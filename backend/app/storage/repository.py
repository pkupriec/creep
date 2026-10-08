"""One dedicated SQLite thread owns short, fully synchronous state transactions.

The checkpoint is the immutable-record frontier; relational indexes independently
enforce identities and make mappings, claims and committed events recoverable.
No connection or transaction is used by a provider or held across an await.
"""

import asyncio
import sqlite3
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from app.contracts.api import TERMINAL_RUN_STATUSES, RunEvent
from app.contracts.errors import CGError, ErrorCode
from app.contracts.interfaces import (
    ActivationKey,
    ContinuationAcceptance,
    ContinuationRoute,
    PendingTool,
    ReplayClaim,
    ResponseEnvelope,
    RunCheckpoint,
    RunPage,
    RunRecord,
    RunSubmission,
    ToolCheckpoint,
    raw_text_hash,
)


def conflict(message="State changed; reload the durable checkpoint"):
    return CGError(ErrorCode.CONTINUATION_CONFLICT, message)


def append_event(checkpoint: RunCheckpoint, type_: str, now: datetime, payload=None):
    event = RunEvent(
        run_id=checkpoint.run.run_id,
        event_id=len(checkpoint.events_json) + 1,
        type=type_,
        created_at=now.isoformat(),
        payload=payload or {},
    )
    return checkpoint.model_copy(
        update={"events_json": checkpoint.events_json + (event.model_dump_json(),)}
    )


class SQLiteRunRepository:
    def __init__(self, database_path: Path):
        self.database_path = Path(database_path)
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cg-sqlite")
        self.connection: sqlite3.Connection | None = None
        self.closed = False

    async def _call(self, operation):
        if self.closed:
            raise CGError(ErrorCode.STORAGE_ERROR, "Storage is closed")
        return await asyncio.get_running_loop().run_in_executor(self.executor, operation)

    async def initialize(self) -> None:
        def initialize():
            if self.connection is not None:
                return
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(self.database_path, isolation_level=None)
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA foreign_keys=ON")
            self.connection.execute("PRAGMA synchronous=FULL")
            self.connection.execute("PRAGMA busy_timeout=5000")
            version = self.connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                self.connection.close()
                self.connection = None
                raise CGError(ErrorCode.STORAGE_ERROR, "Unsupported SQLite schema version")
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS runs(
                  run_id TEXT PRIMARY KEY, namespace TEXT NOT NULL, graph_id TEXT NOT NULL,
                  status TEXT NOT NULL, version INTEGER NOT NULL, created TEXT NOT NULL,
                  ended TEXT, checkpoint TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS activations(
                  activation_id TEXT PRIMARY KEY,
                  run_id TEXT NOT NULL REFERENCES runs ON DELETE CASCADE,
                  scope_key TEXT NOT NULL, iteration INTEGER NOT NULL, node_id TEXT NOT NULL,
                  record TEXT NOT NULL, UNIQUE(run_id,scope_key,iteration,node_id));
                CREATE TABLE IF NOT EXISTS pending_tools(
                  external_id TEXT PRIMARY KEY,
                  run_id TEXT NOT NULL REFERENCES runs ON DELETE CASCADE,
                  activation_id TEXT NOT NULL REFERENCES activations ON DELETE CASCADE,
                  provider_round INTEGER NOT NULL,
                  call_ordinal INTEGER NOT NULL, record TEXT NOT NULL,
                  UNIQUE(activation_id,provider_round,call_ordinal));
                CREATE TABLE IF NOT EXISTS batches(
                  batch_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs ON DELETE CASCADE,
                  sequence INTEGER NOT NULL, status TEXT NOT NULL, record TEXT NOT NULL,
                  UNIQUE(run_id,sequence));
                CREATE UNIQUE INDEX IF NOT EXISTS one_open_batch
                  ON batches(run_id) WHERE status='open';
                CREATE TABLE IF NOT EXISTS responses(
                  run_id TEXT NOT NULL REFERENCES runs ON DELETE CASCADE,
                  sequence INTEGER NOT NULL, record TEXT NOT NULL, PRIMARY KEY(run_id,sequence));
                CREATE TABLE IF NOT EXISTS response_cache(
                  claim_id TEXT PRIMARY KEY, namespace TEXT NOT NULL,
                  run_id TEXT NOT NULL REFERENCES runs ON DELETE CASCADE,
                  batch_id TEXT NOT NULL REFERENCES batches ON DELETE CASCADE,
                  request_hash TEXT NOT NULL, route_json TEXT NOT NULL, record TEXT NOT NULL,
                  UNIQUE(namespace,run_id,batch_id,request_hash));
                CREATE TABLE IF NOT EXISTS events(
                  run_id TEXT NOT NULL REFERENCES runs ON DELETE CASCADE,
                  event_id INTEGER NOT NULL, record TEXT NOT NULL, PRIMARY KEY(run_id,event_id));
                PRAGMA user_version=1;
            """)

        await self._call(initialize)

    async def close(self) -> None:
        if self.closed:
            return
        await self._call(lambda: self.connection.close() if self.connection else None)
        self.closed = True
        self.executor.shutdown(wait=True)

    def _transaction(self, operation):
        connection = self.connection
        if connection is None:
            raise CGError(ErrorCode.STORAGE_ERROR, "Storage is not initialized")
        connection.execute("BEGIN IMMEDIATE")
        try:
            result = operation()
            connection.execute("COMMIT")
            return result
        except sqlite3.Error as error:
            connection.execute("ROLLBACK")
            if isinstance(error, sqlite3.IntegrityError):
                raise conflict("Durable identity or uniqueness conflict") from None
            raise CGError(ErrorCode.STORAGE_ERROR, "SQLite state transaction failed") from None
        except BaseException:
            connection.execute("ROLLBACK")
            raise

    def _load(self, run_id: str, namespace: str | None = None) -> RunCheckpoint:
        row = self.connection.execute(
            "SELECT namespace,checkpoint FROM runs WHERE run_id=?", (run_id,)
        ).fetchone()
        if row is None or namespace is not None and row[0] != namespace:
            raise CGError(ErrorCode.RUN_NOT_FOUND, "Run not found")
        return RunCheckpoint.model_validate_json(row[1])

    def _verify(self, proposed: RunCheckpoint, current: RunCheckpoint, expected_version: int):
        if current.run.status in TERMINAL_RUN_STATUSES:
            raise CGError(ErrorCode.RUN_TERMINAL, "Run already has a terminal outcome")
        if (
            current.run.state_version != expected_version
            or proposed.run.state_version != expected_version
        ):
            raise conflict()
        for field in ("run_id", "snapshot", "context", "inputs_json", "policy", "created_at"):
            if getattr(proposed.run, field) != getattr(current.run, field):
                raise conflict("Immutable run data cannot change")
        for field in (
            "node_executions",
            "upstream_attempts",
            "tool_rounds",
            "active_elapsed_seconds",
            "queue_elapsed_seconds",
        ):
            if getattr(proposed.run, field) < getattr(current.run, field):
                raise conflict("Run counters cannot decrease")
        if proposed.responses[: len(current.responses)] != current.responses:
            raise conflict("Committed responses cannot change")
        if proposed.events_json[: len(current.events_json)] != current.events_json:
            raise conflict("Committed events cannot change")
        old_tools = {tool.external_id: tool for tool in current.pending_tools}
        new_tools = {tool.external_id: tool for tool in proposed.pending_tools}
        if not old_tools.keys() <= new_tools.keys():
            raise conflict("Tool mappings cannot disappear")
        for id_, old in old_tools.items():
            new = new_tools[id_]
            for field in type(old).model_fields:
                if field in {"status", "batch_id", "result", "result_hash"}:
                    continue
                if getattr(old, field) != getattr(new, field):
                    raise conflict("Tool identity cannot change")
            if old.status == "accepted" and new != old:
                raise conflict("Accepted tool results cannot change")
            if old.batch_id is not None and new.batch_id != old.batch_id:
                raise conflict("Delivered mappings cannot move between batches")
            if old.result is not None and new.result != old.result:
                raise conflict("Accepted tool results cannot change")
            if new.result != old.result or new.result_hash != old.result_hash:
                raise conflict("Only accept_results may commit external results")
        old_activations = {item.activation_id: item for item in current.activations}
        new_activations = {item.activation_id: item for item in proposed.activations}
        if not old_activations.keys() <= new_activations.keys():
            raise conflict("Activation history cannot disappear")
        for id_, old in old_activations.items():
            new = new_activations[id_]
            if new.key != old.key:
                raise conflict("Activation identity cannot change")
            if old.status == "completed" and new != old:
                raise conflict("Completed activation cannot change")
            if old.status == "running" and new.attempt_id != old.attempt_id:
                raise conflict("Stale provider attempt cannot route an outcome")
        old_batches = {batch.batch_id: batch for batch in current.batches}
        new_batches = {batch.batch_id: batch for batch in proposed.batches}
        if not old_batches.keys() <= new_batches.keys():
            raise conflict("Batch history cannot disappear")
        for id_, old in old_batches.items():
            new = new_batches[id_]
            if old.model_copy(update={"status": new.status}) != new:
                raise conflict("Batch deadline, IDs and response cannot change")
            if old.status != "open" and new != old:
                raise conflict("Closed batches cannot reopen")

    def _persist(self, checkpoint: RunCheckpoint, current: RunCheckpoint | None = None):
        checkpoint = RunCheckpoint.model_validate_json(checkpoint.model_dump_json())
        run = checkpoint.run.model_copy(
            update={"state_version": 0 if current is None else current.run.state_version + 1}
        )
        checkpoint = checkpoint.model_copy(update={"run": run})
        if len({item.activation_id for item in checkpoint.activations}) != len(
            checkpoint.activations
        ):
            raise conflict("Duplicate activation IDs")
        if len({item.external_id for item in checkpoint.pending_tools}) != len(
            checkpoint.pending_tools
        ):
            raise conflict("Duplicate external tool IDs")
        if tuple(item.response_sequence for item in checkpoint.responses) != tuple(
            range(1, len(checkpoint.responses) + 1)
        ):
            raise conflict("Responses must have contiguous immutable sequences")
        if tuple(
            RunEvent.model_validate_json(raw).event_id for raw in checkpoint.events_json
        ) != tuple(range(1, len(checkpoint.events_json) + 1)):
            raise conflict("Events must have contiguous immutable sequences")
        for table, field, items in (
            ("activations", "activation_id", checkpoint.activations),
            ("pending_tools", "external_id", checkpoint.pending_tools),
            ("batches", "batch_id", checkpoint.batches),
        ):
            for item in items:
                existing = self.connection.execute(
                    f"SELECT run_id FROM {table} WHERE {field}=?", (getattr(item, field),)
                ).fetchone()
                if existing is not None and existing[0] != run.run_id:
                    raise conflict("Globally unique identity already belongs to another run")
        values = (
            run.run_id,
            run.context.namespace,
            run.snapshot.graph_id,
            run.status,
            run.state_version,
            run.created_at.isoformat(),
            run.ended_at.isoformat() if run.ended_at else None,
            checkpoint.model_dump_json(),
        )
        if current is None:
            self.connection.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?,?)", values)
        else:
            cursor = self.connection.execute(
                "UPDATE runs SET namespace=?,graph_id=?,status=?,version=?,created=?,"
                "ended=?,checkpoint=? "
                "WHERE run_id=? AND version=?",
                values[1:] + (run.run_id, current.run.state_version),
            )
            if cursor.rowcount != 1:
                raise conflict()
        for activation in checkpoint.activations:
            key = activation.key
            if key.run_id != run.run_id:
                raise conflict("Activation belongs to another run")
            self.connection.execute(
                "INSERT INTO activations VALUES(?,?,?,?,?,?) ON CONFLICT(activation_id) "
                "DO UPDATE SET record=excluded.record",
                (
                    activation.activation_id,
                    run.run_id,
                    key.scope_key,
                    key.iteration,
                    key.node_id,
                    activation.model_dump_json(),
                ),
            )
        for tool in checkpoint.pending_tools:
            if tool.run_id != run.run_id:
                raise conflict("Tool mapping belongs to another run")
            owner = next(
                (
                    item
                    for item in checkpoint.activations
                    if item.activation_id == tool.activation_id
                ),
                None,
            )
            if owner is None or owner.key.node_id != tool.node_id:
                raise conflict("Tool mapping must belong to its activation and node")
            self.connection.execute(
                "INSERT INTO pending_tools VALUES(?,?,?,?,?,?) ON CONFLICT(external_id) "
                "DO UPDATE SET record=excluded.record",
                (
                    tool.external_id,
                    run.run_id,
                    tool.activation_id,
                    tool.provider_round,
                    tool.call_ordinal,
                    tool.model_dump_json(),
                ),
            )
        for batch in checkpoint.batches:
            self.connection.execute(
                "INSERT INTO batches VALUES(?,?,?,?,?) ON CONFLICT(batch_id) "
                "DO UPDATE SET status=excluded.status,record=excluded.record",
                (batch.batch_id, run.run_id, batch.sequence, batch.status, batch.model_dump_json()),
            )
        for response in checkpoint.responses:
            self.connection.execute(
                "INSERT OR IGNORE INTO responses VALUES(?,?,?)",
                (run.run_id, response.response_sequence, response.model_dump_json()),
            )
        for raw in checkpoint.events_json:
            event = RunEvent.model_validate_json(raw)
            if event.run_id != run.run_id:
                raise conflict("Event belongs to another run")
            self.connection.execute(
                "INSERT OR IGNORE INTO events VALUES(?,?,?)", (run.run_id, event.event_id, raw)
            )
        return run

    async def create_run(self, submission: RunSubmission, run_id: str, now: datetime) -> RunRecord:
        run = RunRecord(
            run_id=run_id,
            snapshot=submission.plan.snapshot,
            context=submission.context,
            inputs_json=submission.inputs_json,
            policy=submission.policy,
            status="queued",
            state_version=0,
            created_at=now,
        )
        checkpoint = RunCheckpoint(
            run=run,
            activations=(),
            loops=(),
            pending_tools=(),
            batches=(),
            responses=(),
            events_json=(),
        )
        checkpoint = append_event(checkpoint, "run.queued", now)
        return await self._call(lambda: self._transaction(lambda: self._persist(checkpoint)))

    async def get_run(self, run_id: str, namespace: str) -> RunRecord:
        return (await self.load_checkpoint(run_id, namespace)).run

    async def load_checkpoint(self, run_id: str, namespace: str) -> RunCheckpoint:
        return await self._call(lambda: self._load(run_id, namespace))

    async def list_runs(self, namespace, *, graph_id, status, limit, offset) -> RunPage:
        if not 1 <= limit <= 100 or offset < 0:
            raise CGError(ErrorCode.INVALID_PARAMETER, "Invalid run pagination")

        def query():
            clauses, values = ["namespace=?"], [namespace]
            for name, value in (("graph_id", graph_id), ("status", status)):
                if value is not None:
                    clauses.append(name + "=?")
                    values.append(value)
            where = " AND ".join(clauses)
            total = self.connection.execute(
                "SELECT count(*) FROM runs WHERE " + where, values
            ).fetchone()[0]
            rows = self.connection.execute(
                "SELECT checkpoint FROM runs WHERE "
                + where
                + " ORDER BY created DESC,run_id DESC LIMIT ? OFFSET ?",
                [*values, limit, offset],
            ).fetchall()
            return RunPage(
                runs=tuple(RunCheckpoint.model_validate_json(row[0]).run for row in rows),
                total=total,
            )

        return await self._call(query)

    async def save_checkpoint(self, checkpoint: RunCheckpoint, expected_version: int) -> RunRecord:
        def save():
            current = self._load(checkpoint.run.run_id, checkpoint.run.context.namespace)
            self._verify(checkpoint, current, expected_version)
            if checkpoint.run.status in TERMINAL_RUN_STATUSES:
                raise conflict("Use an atomic terminal transition")
            return self._persist(checkpoint, current)

        return await self._call(lambda: self._transaction(save))

    async def claim_activation(self, key: ActivationKey, attempt_id: str, now: datetime):
        def claim():
            current = self._load(key.run_id)
            if current.run.status != "running":
                return None
            if current.run.active_elapsed_seconds >= current.run.policy.active_timeout_seconds:
                raise CGError(ErrorCode.RUN_TIMEOUT, "Active run budget exhausted")
            activation = next((item for item in current.activations if item.key == key), None)
            if activation is None or activation.status != "ready":
                return None
            new_execution = activation.started_at is None
            if (
                new_execution
                and current.run.node_executions >= current.run.policy.max_node_executions
            ):
                raise CGError(ErrorCode.BUDGET_EXCEEDED, "Node execution budget exhausted")
            activation = activation.model_copy(
                update={
                    "status": "running",
                    "attempt_id": attempt_id,
                    "started_at": activation.started_at or now,
                }
            )
            checkpoint = current.model_copy(
                update={
                    "run": current.run.model_copy(
                        update={
                            "node_executions": current.run.node_executions + int(new_execution),
                            "upstream_attempts": current.run.upstream_attempts + 1,
                        }
                    ),
                    "activations": tuple(
                        activation if item.key == key else item for item in current.activations
                    ),
                }
            )
            checkpoint = append_event(
                checkpoint,
                "activation.running",
                now,
                {"activation_id": activation.activation_id, "attempt_id": attempt_id},
            )
            self._persist(checkpoint, current)
            return activation

        return await self._call(lambda: self._transaction(claim))

    def _seal_claims(self, run_id: str, response: ResponseEnvelope):
        rows = self.connection.execute(
            "SELECT claim_id,record FROM response_cache WHERE run_id=?", (run_id,)
        ).fetchall()
        for id_, raw in rows:
            claim = ReplayClaim.model_validate_json(raw)
            if (
                claim.status == "pending"
                and claim.after_response_sequence < response.response_sequence
            ):
                earlier = self.connection.execute(
                    "SELECT record FROM responses WHERE run_id=? AND sequence>? "
                    "ORDER BY sequence LIMIT 1",
                    (run_id, claim.after_response_sequence),
                ).fetchone()
                envelope = ResponseEnvelope.model_validate_json(earlier[0]) if earlier else response
                claim = claim.model_copy(update={"status": "completed", "envelope": envelope})
                self.connection.execute(
                    "UPDATE response_cache SET record=? WHERE claim_id=?",
                    (claim.model_dump_json(), id_),
                )

    async def checkpoint_batch(
        self, checkpoint: ToolCheckpoint, expected_version: int
    ) -> RunRecord:
        def expose():
            proposed = checkpoint.checkpoint
            current = self._load(proposed.run.run_id, proposed.run.context.namespace)
            self._verify(proposed, current, expected_version)
            if any(item.status == "running" for item in current.activations):
                raise conflict("Tool checkpoint has uncertain running attempts")
            if any(batch.status == "open" for batch in current.batches):
                raise conflict("An external batch is already open")
            mappings = {tool.external_id: tool for tool in current.pending_tools}
            if any(
                id_ not in mappings or mappings[id_].status != "unexposed"
                for id_ in checkpoint.batch.external_ids
            ):
                raise conflict("Exposure must use already durable unexposed mappings")
            if current.run.tool_rounds >= current.run.policy.max_tool_rounds:
                raise CGError(ErrorCode.BUDGET_EXCEEDED, "Tool batch budget exhausted")
            if checkpoint.batch.sequence != len(current.responses) + 1:
                raise conflict("Response sequence is not the next committed boundary")
            proposed = proposed.model_copy(
                update={
                    "run": proposed.run.model_copy(
                        update={
                            "tool_rounds": current.run.tool_rounds + 1,
                        }
                    )
                }
            )
            proposed = append_event(
                proposed,
                "run.waiting_tools",
                checkpoint.batch.prepared_at,
                {"batch_id": checkpoint.batch.batch_id},
            )
            run = self._persist(proposed, current)
            self._seal_claims(run.run_id, checkpoint.batch.envelope)
            return run

        return await self._call(lambda: self._transaction(expose))

    async def complete_run(self, checkpoint, envelope, expected_version):
        def complete():
            current = self._load(checkpoint.run.run_id, checkpoint.run.context.namespace)
            self._verify(checkpoint, current, expected_version)
            if envelope.run_id != current.run.run_id or envelope.batch_id is not None:
                raise conflict("Final envelope identity mismatch")
            if envelope.response_sequence != len(current.responses) + 1:
                raise conflict("Final response sequence mismatch")
            if any(batch.status == "open" for batch in checkpoint.batches):
                raise conflict("Cannot complete with outstanding external tools")
            if any(item.status == "running" for item in checkpoint.activations):
                raise conflict("Cannot complete with uncertain provider attempts")
            if any(item.status != "completed" for item in checkpoint.activations):
                raise conflict("Cannot complete an unfinished required frontier")
            output = next(
                (
                    item
                    for item in checkpoint.activations
                    if item.key.node_id == current.run.snapshot.graph().output_node_id
                ),
                None,
            )
            if output is None or output.payload_json != checkpoint.run.output_json:
                raise conflict("Completion requires the declared output payload")
            if checkpoint.run.status != "completed" or checkpoint.run.ended_at is None:
                raise conflict("Completion requires a terminal frontier and end time")
            if checkpoint.responses != current.responses + (envelope,):
                raise conflict("Completion must append exactly one final response")
            proposed = append_event(checkpoint, "run.completed", checkpoint.run.ended_at)
            run = self._persist(proposed, current)
            self._seal_claims(run.run_id, envelope)
            return run

        return await self._call(lambda: self._transaction(complete))

    async def lookup_tools(self, external_ids: tuple[str, ...]):
        def lookup():
            result = []
            for id_ in external_ids:
                row = self.connection.execute(
                    "SELECT record FROM pending_tools WHERE external_id=?", (id_,)
                ).fetchone()
                if row:
                    result.append(PendingTool.model_validate_json(row[0]))
            return tuple(result)

        return await self._call(lookup)

    async def get_claim(self, claim_id: str):
        def get():
            row = self.connection.execute(
                "SELECT record FROM response_cache WHERE claim_id=?", (claim_id,)
            ).fetchone()
            if row is None:
                raise conflict("Continuation claim not found")
            return ReplayClaim.model_validate_json(row[0])

        return await self._call(get)

    async def accept_results(self, route: ContinuationRoute, request_hash: str, now: datetime):
        def accept():
            current = self._load(route.run_id, route.namespace)
            if route.model != "cg/" + current.run.snapshot.graph_id:
                raise conflict("Continuation model does not match the saved run")
            if current.run.status in {"failed", "cancelled", "interrupted"}:
                raise CGError(ErrorCode.RUN_TERMINAL, "Run has a terminal failure outcome")
            batch = next(
                (item for item in current.batches if item.batch_id == route.batch_id), None
            )
            if batch is None:
                raise conflict("Continuation batch not found")
            mappings = {item.external_id: item for item in current.pending_tools}
            ids = [item.tool_call_id for item in route.results]
            if not ids or len(ids) != len(set(ids)) or not set(ids) <= set(batch.external_ids):
                raise CGError(ErrorCode.UNKNOWN_TOOL_CALL, "Results must belong to the same batch")
            for result in route.results:
                old = mappings[result.tool_call_id]
                if old.result is not None and old.result != result.content:
                    raise conflict("Accepted tool result differs")
            row = self.connection.execute(
                "SELECT record,route_json FROM response_cache WHERE namespace=? AND run_id=? "
                "AND batch_id=? AND request_hash=?",
                (route.namespace, route.run_id, route.batch_id, request_hash),
            ).fetchone()
            missing = tuple(id_ for id_ in batch.external_ids if mappings[id_].status != "accepted")
            if row:
                if row[1] != route.model_dump_json():
                    raise conflict("Replay hash does not identify an identical continuation")
                claim = ReplayClaim.model_validate_json(row[0])
                if claim.status == "completed":
                    return ContinuationAcceptance(
                        kind="replay", claim=claim, accepted_ids=tuple(ids), missing_ids=()
                    )
                if claim.status == "terminal":
                    raise CGError(ErrorCode.RUN_TERMINAL, "Continuation has a terminal outcome")
                if current.run.status in TERMINAL_RUN_STATUSES:
                    raise CGError(ErrorCode.RUN_TERMINAL, "Run has a terminal outcome")
                if now >= batch.expires_at and batch.status == "open":
                    error = CGError(
                        ErrorCode.TOOL_WAIT_TIMEOUT, "External tool result deadline expired"
                    )
                    self._terminal(current, "failed", error.payload().error, now)
                    return error
                return ContinuationAcceptance(
                    kind="joined", claim=claim, accepted_ids=tuple(ids), missing_ids=missing
                )
            if current.run.status in TERMINAL_RUN_STATUSES:
                raise CGError(ErrorCode.RUN_TERMINAL, "Run has a terminal outcome")
            if batch.status != "open":
                raise conflict("Closed batch requires an exact existing replay claim")
            if now >= batch.expires_at:
                error = CGError(
                    ErrorCode.TOOL_WAIT_TIMEOUT, "External tool result deadline expired"
                )
                self._terminal(current, "failed", error.payload().error, now)
                return error
            for result in route.results:
                mappings[result.tool_call_id] = mappings[result.tool_call_id].model_copy(
                    update={
                        "status": "accepted",
                        "result": result.content,
                        "result_hash": raw_text_hash(result.content),
                    }
                )
            missing = tuple(id_ for id_ in batch.external_ids if mappings[id_].status != "accepted")
            closed = batch.model_copy(update={"status": "open" if missing else "closed"})
            checkpoint = current.model_copy(
                update={
                    "pending_tools": tuple(
                        mappings[item.external_id] for item in current.pending_tools
                    ),
                    "batches": tuple(
                        closed if item.batch_id == batch.batch_id else item
                        for item in current.batches
                    ),
                }
            )
            checkpoint = append_event(
                checkpoint,
                "tools.accepted",
                now,
                {"accepted_ids": ids, "missing_ids": list(missing)},
            )
            self._persist(checkpoint, current)
            claim = ReplayClaim(
                claim_id=uuid.uuid4().hex,
                namespace=route.namespace,
                run_id=route.run_id,
                batch_id=route.batch_id,
                request_hash=request_hash,
                after_response_sequence=batch.sequence,
                status="pending",
            )
            self.connection.execute(
                "INSERT INTO response_cache VALUES(?,?,?,?,?,?,?)",
                (
                    claim.claim_id,
                    route.namespace,
                    route.run_id,
                    route.batch_id,
                    request_hash,
                    route.model_dump_json(),
                    claim.model_dump_json(),
                ),
            )
            return ContinuationAcceptance(
                kind="partial" if missing else "ready",
                claim=claim,
                accepted_ids=tuple(ids),
                missing_ids=missing,
            )

        result = await self._call(lambda: self._transaction(accept))
        if isinstance(result, CGError):
            raise result
        return result

    def _terminal(self, current, status, error, now):
        if current.run.status in TERMINAL_RUN_STATUSES:
            return current.run
        code = {
            "failed": ErrorCode.UPSTREAM_ERROR,
            "cancelled": ErrorCode.CANCELLED,
            "interrupted": ErrorCode.INTERRUPTED,
        }[status]
        error = error or CGError(code, "Run " + status).payload().error
        checkpoint = current.model_copy(
            update={
                "run": current.run.model_copy(
                    update={
                        "status": status,
                        "ended_at": now,
                        "error_json": error.model_dump_json(),
                    }
                ),
                "activations": tuple(
                    item
                    if item.status == "completed"
                    else item.model_copy(
                        update={
                            "status": "cancelled" if status == "cancelled" else "failed",
                            "ended_at": now,
                            "error_json": error.model_dump_json(),
                        }
                    )
                    for item in current.activations
                ),
                "pending_tools": tuple(
                    item
                    if item.status == "accepted"
                    else item.model_copy(update={"status": "terminal"})
                    for item in current.pending_tools
                ),
                "batches": tuple(
                    item.model_copy(update={"status": "terminal"})
                    if item.status == "open"
                    else item
                    for item in current.batches
                ),
            }
        )
        checkpoint = append_event(checkpoint, "run." + status, now)
        run = self._persist(checkpoint, current)
        for claim_id, raw in self.connection.execute(
            "SELECT claim_id,record FROM response_cache WHERE run_id=?", (run.run_id,)
        ).fetchall():
            claim = ReplayClaim.model_validate_json(raw)
            if claim.status == "pending":
                claim = claim.model_copy(
                    update={"status": "terminal", "error_json": error.model_dump_json()}
                )
                self.connection.execute(
                    "UPDATE response_cache SET record=? WHERE claim_id=?",
                    (claim.model_dump_json(), claim_id),
                )
        return run

    async def terminalize(self, run_id, status, error, now):
        if status not in {"failed", "cancelled", "interrupted"}:
            raise ValueError("Success requires complete_run")

        def transition():
            current = self._load(run_id)
            if error is not None and error.code == ErrorCode.TOOL_WAIT_TIMEOUT.value:
                batch = next((item for item in current.batches if item.status == "open"), None)
                # Acceptance and expiry share this serialized transaction boundary.
                # A stale deadline cannot fail a fully accepted batch.
                if batch is None or now < batch.expires_at:
                    return current.run
            return self._terminal(current, status, error, now)

        return await self._call(lambda: self._transaction(transition))

    async def cancel_if_unexposed(self, run_id, namespace, now):
        def cancel():
            current = self._load(run_id, namespace)
            if current.responses or current.run.status in TERMINAL_RUN_STATUSES:
                return current.run
            return self._terminal(current, "cancelled", None, now)

        return await self._call(lambda: self._transaction(cancel))

    async def recover(self, now: datetime):
        def recover():
            rows = self.connection.execute(
                "SELECT run_id FROM runs ORDER BY created,run_id"
            ).fetchall()
            safe = []
            for (run_id,) in rows:
                current = self._load(run_id)
                if current.run.status in TERMINAL_RUN_STATUSES:
                    continue
                batch = next((item for item in current.batches if item.status == "open"), None)
                if batch and now >= batch.expires_at:
                    error = CGError(
                        ErrorCode.TOOL_WAIT_TIMEOUT, "External tool result deadline expired"
                    )
                    self._terminal(current, "failed", error.payload().error, now)
                elif current.run.status == "waiting_tools" and not any(
                    item.status == "running" for item in current.activations
                ):
                    safe.append(current.run)
                elif (
                    current.run.status == "running"
                    and any(batch.status == "closed" for batch in current.batches)
                    and not any(item.status == "running" for item in current.activations)
                ):
                    # Acceptance may win before restart but its reducer may have only
                    # marked the run active, without claiming the next provider attempt.
                    # Preserve that proven quiescent frontier; old closed TTLs are over.
                    checkpoint = current.model_copy(
                        update={"run": current.run.model_copy(update={"status": "waiting_tools"})}
                    )
                    safe.append(self._persist(checkpoint, current))
                elif current.run.status == "queued":
                    safe.append(current.run)
                else:
                    self._terminal(current, "interrupted", None, now)
            return tuple(safe)

        return await self._call(lambda: self._transaction(recover))

    async def read_events(self, run_id, namespace, after_event_id, limit=1000):
        def read():
            self._load(run_id, namespace)
            rows = self.connection.execute(
                "SELECT record FROM events WHERE run_id=? AND event_id>? ORDER BY event_id LIMIT ?",
                (run_id, after_event_id, limit),
            ).fetchall()
            return tuple(RunEvent.model_validate_json(row[0]) for row in rows)

        return await self._call(read)

    async def cleanup_history(self, before: datetime):
        def cleanup():
            return self.connection.execute(
                "DELETE FROM runs WHERE status IN ('completed','failed','cancelled','interrupted') "
                "AND ended<?",
                (before.isoformat(),),
            ).rowcount

        return await self._call(lambda: self._transaction(cleanup))
