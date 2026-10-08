"""Single per-run frontier reducers, independent of HTTP request lifetime.

Provider tasks return outcomes to their reducer. Only that reducer constructs
frontiers; concurrent tool acceptance is rebased through optimistic storage CAS.
External calls are exposed only after every started sibling inference settles.
"""

import asyncio
import json
import uuid
from datetime import timedelta
from urllib.parse import unquote

from jsonschema.exceptions import SchemaError
from jsonschema.exceptions import ValidationError as SchemaValidationError
from jsonschema.validators import validator_for
from pydantic import ValidationError
from referencing import Registry
from referencing.exceptions import NoSuchResource, Unresolvable

from app.contracts.api import TERMINAL_RUN_STATUSES, ChatCompletionResponse
from app.contracts.config import Settings
from app.contracts.errors import CGError, ErrorCode
from app.contracts.graph import ControllerOutput, InputNode, LLMNode, controller_schema
from app.contracts.interfaces import (
    ActivationKey,
    ActivationRecord,
    AdmissionController,
    Clock,
    ContinuationAcceptance,
    EventBus,
    LoopState,
    OllamaAdapter,
    PortValue,
    ProviderRequest,
    ResponseEnvelope,
    RunRepository,
    RunSubmission,
    ToolBridge,
    Validator,
    canonical_json,
    raw_text_hash,
)
from app.storage.repository import append_event


class AsyncGraphRuntime:
    def __init__(
        self,
        settings: Settings,
        repository: RunRepository,
        validator: Validator,
        provider: OllamaAdapter,
        bridge: ToolBridge,
        events: EventBus,
        admission: AdmissionController,
        clock: Clock,
    ):
        self.settings = settings
        self.repository = repository
        self.validator = validator
        self.provider = provider
        self.bridge = bridge
        self.events = events
        self.admission = admission
        self.clock = clock
        self.tasks: dict[str, asyncio.Task] = {}
        self.leases = {}
        self.wakes: dict[str, asyncio.Event] = {}
        self.active_since: dict[str, float] = {}
        self.stopping = False

    async def submit(self, submission: RunSubmission):
        if self.stopping:
            raise CGError(ErrorCode.INTERRUPTED, "Runtime is shutting down")
        graph = submission.plan.snapshot.graph()
        prepared = self.validator.prepare_inputs(graph, submission.inputs_json)
        if prepared != submission.inputs_json:
            submission = submission.model_copy(update={"inputs_json": prepared})
        client = json.loads(submission.policy.client_request_json)
        choice = client.get("tool_choice")
        if (
            isinstance(choice, dict)
            and sum(isinstance(node, LLMNode) and node.tools_enabled for node in graph.nodes) != 1
        ):
            raise CGError(
                ErrorCode.UNSUPPORTED_TOOL_CHOICE,
                "A forced tool requires exactly one tool-capable node",
            )
        if (isinstance(choice, dict) or choice == "required") and (
            not json.loads(submission.context.tools_json)
            or not any(isinstance(node, LLMNode) and node.tools_enabled for node in graph.nodes)
        ):
            raise CGError(
                ErrorCode.UNSUPPORTED_TOOL_CHOICE,
                "Required tool choice needs exposed tools and a tool-capable node",
            )
        run_id = uuid.uuid4().hex
        lease = await self.admission.acquire(run_id)
        creation = asyncio.create_task(
            self.repository.create_run(submission, run_id, self.clock.now())
        )
        try:
            run = await asyncio.shield(creation)
        except BaseException:
            # The dedicated DB thread may finish insertion after cancellation. Join
            # it before releasing the reservation so no undispatched orphan is left.
            outcomes = await asyncio.gather(creation, return_exceptions=True)
            if not isinstance(outcomes[0], BaseException):
                await self.repository.terminalize(run_id, "cancelled", None, self.clock.now())
            await lease.release()
            raise
        self.leases[run_id] = lease
        self.wakes[run_id] = asyncio.Event()
        self.tasks[run_id] = asyncio.create_task(
            self._run(run_id, run.context.namespace), name="cg-run-" + run_id
        )
        await self.events.notify(run_id)
        return run

    async def resume(self, acceptance: ContinuationAcceptance) -> None:
        if acceptance.kind != "ready" or self.stopping:
            return
        run_id = acceptance.claim.run_id
        # Duplicate ready notifications join the one reducer; durable activation claims
        # still guard every upstream call, including after reconstructed recovery.
        wake = self.wakes.get(run_id)
        if wake is not None:
            wake.set()
        await self.events.notify(run_id)

    async def await_response(self, run_id, namespace, after_response_sequence=0):
        while True:
            checkpoint = await self.repository.load_checkpoint(run_id, namespace)
            if checkpoint.run.status in {"failed", "cancelled", "interrupted"}:
                self._raise_terminal(checkpoint)
            for response in checkpoint.responses:
                if response.response_sequence > after_response_sequence:
                    return response
            if checkpoint.run.status in TERMINAL_RUN_STATUSES:
                self._raise_terminal(checkpoint)
            await self.clock.sleep(0.02)

    @staticmethod
    def _raise_terminal(checkpoint):
        if checkpoint.run.error_json:
            error = json.loads(checkpoint.run.error_json)
            raise CGError(ErrorCode(error["code"]), error["message"])
        raise CGError(ErrorCode.RUN_TERMINAL, "Run ended without another response")

    async def cancel(self, run_id, namespace):
        await self.repository.get_run(run_id, namespace)
        await self._account_active(run_id, namespace)
        run = await self.repository.terminalize(run_id, "cancelled", None, self.clock.now())
        await self._stop_terminal(run_id, run)
        return run

    async def detach_initial(self, run_id, namespace):
        await self._account_active(run_id, namespace)
        run = await self.repository.cancel_if_unexposed(run_id, namespace, self.clock.now())
        await self._stop_terminal(run_id, run)
        return run

    async def _stop_terminal(self, run_id, run):
        if run.status in TERMINAL_RUN_STATUSES:
            task = self.tasks.get(run_id)
            if task is not None and task is not asyncio.current_task():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
                self.tasks.pop(run_id, None)
                self.wakes.pop(run_id, None)
            lease = self.leases.pop(run_id, None)
            if lease is not None:
                await lease.release()
        await self.events.notify(run_id)

    async def _account_active(self, run_id, namespace):
        run = await self.repository.get_run(run_id, namespace)
        if run.status != "running" or run_id not in self.active_since:
            return
        try:
            await self._update(run_id, namespace, lambda checkpoint: checkpoint)
        except CGError:
            latest = await self.repository.get_run(run_id, namespace)
            if latest.status not in TERMINAL_RUN_STATUSES:
                raise

    async def recover(self) -> None:
        records = await self.repository.recover(self.clock.now())
        await self.admission.restore(
            tuple(run.run_id for run in records if run.status == "waiting_tools"),
            tuple(run.run_id for run in records if run.status == "queued"),
        )
        for run in records:
            self.validator.compile(run.snapshot)
            self.leases[run.run_id] = await self.admission.acquire(run.run_id)
            self.wakes[run.run_id] = asyncio.Event()
            self.tasks[run.run_id] = asyncio.create_task(
                self._run(run.run_id, run.context.namespace), name="cg-recover-" + run.run_id
            )
        await self.repository.cleanup_history(
            self.clock.now() - timedelta(days=self.settings.history_retention_days)
        )

    async def shutdown(self) -> None:
        self.stopping = True
        tasks = tuple(self.tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for run_id, lease in tuple(self.leases.items()):
            await lease.release()
            self.leases.pop(run_id, None)
        self.tasks.clear()
        self.wakes.clear()
        self.active_since.clear()

    async def _update(self, run_id, namespace, transform):
        while True:
            current = await self.repository.load_checkpoint(run_id, namespace)
            if current.run.status in TERMINAL_RUN_STATUSES:
                self._raise_terminal(current)
            proposed = transform(current)
            now_mono = self.clock.monotonic()
            baseline = self.active_since.get(run_id)
            if baseline is not None and current.run.status == "running":
                proposed = proposed.model_copy(
                    update={
                        "run": proposed.run.model_copy(
                            update={
                                "active_elapsed_seconds": current.run.active_elapsed_seconds
                                + max(0.0, now_mono - baseline),
                            }
                        )
                    }
                )
            try:
                await self.repository.save_checkpoint(proposed, current.run.state_version)
            except CGError as error:
                if error.code == ErrorCode.CONTINUATION_CONFLICT:
                    latest = await self.repository.get_run(run_id, namespace)
                    if latest.state_version != current.run.state_version:
                        continue
                raise
            if proposed.run.status == "running":
                self.active_since[run_id] = now_mono
            else:
                self.active_since.pop(run_id, None)
            await self.events.notify(run_id)
            return await self.repository.load_checkpoint(run_id, namespace)

    def _new_activation(self, run_id, scope, iteration, node_id):
        return ActivationRecord(
            activation_id=uuid.uuid4().hex,
            key=ActivationKey(run_id=run_id, scope_key=scope, iteration=iteration, node_id=node_id),
            status="pending",
            inputs=(),
            messages_json="[]",
        )

    def _advance(self, checkpoint, plan):
        graph = plan.snapshot.graph()
        nodes = {node.id: node for node in graph.nodes}
        scope = {member: loop.id for loop in graph.loops for member in loop.node_ids}
        port_plans = {port.node_id: port.ordered_ports for port in plan.ports}
        if not checkpoint.activations:
            checkpoint = checkpoint.model_copy(
                update={
                    "activations": tuple(
                        self._new_activation(
                            checkpoint.run.run_id, scope.get(node.id, ""), 0, node.id
                        )
                        for node in graph.nodes
                    ),
                    "loops": tuple(
                        LoopState(
                            loop_id=loop.id,
                            iteration=0,
                            status="waiting",
                            external_inputs=(),
                            next_feedback=(),
                        )
                        for loop in graph.loops
                    ),
                }
            )
        activations = list(checkpoint.activations)
        loops = {loop.loop_id: loop for loop in checkpoint.loops}
        changed = True
        while changed:
            changed = False
            indexed = {
                (item.key.scope_key, item.key.iteration, item.key.node_id): item
                for item in activations
            }
            for loop in graph.loops:
                state = loops[loop.id]
                controller = indexed[(loop.id, state.iteration, loop.controller_node_id)]
                if state.status == "completed" or controller.status != "completed":
                    continue
                if controller.control_decision == loop.exit_value:
                    loops[loop.id] = state.model_copy(update={"status": "completed"})
                    checkpoint = append_event(
                        checkpoint,
                        "loop.stopped",
                        self.clock.now(),
                        {"loop_id": loop.id, "iteration": state.iteration},
                    )
                elif controller.control_decision == loop.continue_value:
                    next_iteration = state.iteration + 1
                    feedback = []
                    for edge in graph.edges:
                        if edge.kind != "feedback" or edge.loop_id != loop.id:
                            continue
                        source = indexed[(loop.id, state.iteration, edge.source)]
                        if source.status != "completed":
                            raise CGError(
                                ErrorCode.GRAPH_VALIDATION_FAILED, "Feedback source is not complete"
                            )
                        feedback.append(
                            PortValue(
                                target=ActivationKey(
                                    run_id=checkpoint.run.run_id,
                                    scope_key=loop.id,
                                    iteration=next_iteration,
                                    node_id=edge.target,
                                ),
                                target_port=edge.target_port,
                                source_node_id=edge.source,
                                source_iteration=state.iteration,
                                value_json=source.payload_json,
                            )
                        )
                    loops[loop.id] = state.model_copy(
                        update={
                            "iteration": next_iteration,
                            "status": "running",
                            "next_feedback": tuple(feedback),
                        }
                    )
                    activations.extend(
                        self._new_activation(checkpoint.run.run_id, loop.id, next_iteration, member)
                        for member in loop.node_ids
                    )
                    checkpoint = append_event(
                        checkpoint,
                        "loop.continued",
                        self.clock.now(),
                        {"loop_id": loop.id, "iteration": next_iteration},
                    )
                else:
                    raise CGError(
                        ErrorCode.GRAPH_VALIDATION_FAILED, "Controller decision is invalid"
                    )
                changed = True
            if changed:
                continue
            for index, activation in enumerate(activations):
                node = nodes[activation.key.node_id]
                if activation.status != "pending":
                    continue
                if (
                    activation.key.scope_key
                    and loops[activation.key.scope_key].iteration != activation.key.iteration
                ):
                    continue
                if isinstance(node, InputNode):
                    value = json.loads(checkpoint.run.inputs_json)[node.input_id]
                    activations[index] = activation.model_copy(
                        update={
                            "status": "completed",
                            "payload_json": canonical_json(value),
                            "ended_at": self.clock.now(),
                        }
                    )
                    checkpoint = append_event(
                        checkpoint,
                        "activation.completed",
                        self.clock.now(),
                        {"activation_id": activation.activation_id},
                    )
                    changed = True
                    continue
                values = {}
                for edge in graph.edges:
                    if edge.target != node.id:
                        continue
                    if edge.kind == "feedback":
                        state = loops[edge.loop_id]
                        if activation.key.iteration == 0:
                            values[edge.target_port] = PortValue(
                                target=activation.key,
                                target_port=edge.target_port,
                                source_node_id=edge.source,
                                source_iteration=0,
                                value_json=canonical_json(edge.initial_value),
                            )
                        else:
                            token = next(
                                (
                                    token
                                    for token in state.next_feedback
                                    if token.target == activation.key
                                    and token.target_port == edge.target_port
                                ),
                                None,
                            )
                            if token is not None:
                                values[edge.target_port] = token
                        continue
                    source_scope = scope.get(edge.source, "")
                    target_scope = activation.key.scope_key
                    if target_scope and source_scope != target_scope:
                        state = loops[target_scope]
                        latched = next(
                            (
                                token
                                for token in state.external_inputs
                                if token.target.node_id == node.id
                                and token.target_port == edge.target_port
                            ),
                            None,
                        )
                        if latched is not None:
                            values[edge.target_port] = latched.model_copy(
                                update={"target": activation.key}
                            )
                            continue
                    source_iteration = 0
                    if source_scope:
                        state = loops[source_scope]
                        if source_scope != target_scope and state.status != "completed":
                            continue
                        source_iteration = (
                            activation.key.iteration
                            if source_scope == target_scope
                            else state.iteration
                        )
                    source = indexed.get((source_scope, source_iteration, edge.source))
                    if source is None or source.status != "completed":
                        continue
                    token = PortValue(
                        target=activation.key,
                        target_port=edge.target_port,
                        source_node_id=edge.source,
                        source_iteration=source_iteration,
                        value_json=source.payload_json,
                    )
                    values[edge.target_port] = token
                    if target_scope and source_scope != target_scope:
                        state = loops[target_scope]
                        loops[target_scope] = state.model_copy(
                            update={"external_inputs": state.external_inputs + (token,)}
                        )
                expected = port_plans[node.id]
                if set(values) != set(expected):
                    continue
                inputs = tuple(values[port] for port in expected)
                if isinstance(node, LLMNode):
                    activations[index] = activation.model_copy(
                        update={"status": "ready", "inputs": inputs}
                    )
                    checkpoint = append_event(
                        checkpoint,
                        "activation.ready",
                        self.clock.now(),
                        {"activation_id": activation.activation_id},
                    )
                else:
                    activations[index] = activation.model_copy(
                        update={
                            "status": "completed",
                            "inputs": inputs,
                            "payload_json": inputs[0].value_json,
                            "ended_at": self.clock.now(),
                        }
                    )
                    checkpoint = append_event(
                        checkpoint,
                        "activation.completed",
                        self.clock.now(),
                        {"activation_id": activation.activation_id},
                    )
                if activation.key.scope_key:
                    state = loops[activation.key.scope_key]
                    if state.status == "waiting":
                        loops[activation.key.scope_key] = state.model_copy(
                            update={"status": "running"}
                        )
                changed = True
        return checkpoint.model_copy(
            update={"activations": tuple(activations), "loops": tuple(loops.values())}
        )

    def _resume_owners(self, checkpoint):
        activations = []
        for activation in checkpoint.activations:
            if activation.status != "waiting_tools":
                activations.append(activation)
                continue
            calls = sorted(
                (
                    tool
                    for tool in checkpoint.pending_tools
                    if tool.activation_id == activation.activation_id
                    and tool.provider_round == activation.provider_round
                ),
                key=lambda tool: tool.call_ordinal,
            )
            if not calls or any(tool.status != "accepted" for tool in calls):
                activations.append(activation)
                continue
            history = json.loads(activation.messages_json)
            history.extend(
                {"role": "tool", "tool_call_id": tool.internal_id, "content": tool.result}
                for tool in calls
            )
            activations.append(
                activation.model_copy(
                    update={"status": "ready", "messages_json": canonical_json(history)}
                )
            )
        return checkpoint.model_copy(update={"activations": tuple(activations)})

    def _request(self, checkpoint, activation, plan):
        graph = plan.snapshot.graph()
        node = next(node for node in graph.nodes if node.id == activation.key.node_id)
        client = json.loads(checkpoint.run.policy.client_request_json)
        messages = json.loads(checkpoint.run.context.messages_json)
        messages.append({"role": "system", "content": node.system_prompt})
        messages.append(
            {
                "role": "user",
                "content": canonical_json(
                    {
                        "inputs": [
                            {
                                "node_id": token.source_node_id,
                                "port": token.target_port,
                                "value": json.loads(token.value_json),
                            }
                            for token in activation.inputs
                        ]
                    }
                ),
            }
        )
        messages.extend(json.loads(activation.messages_json))
        fields = node.generation.model_dump(mode="json", exclude_none=True)
        if node.id == plan.final_llm_node_id:
            fields.update(
                {
                    key: client[key]
                    for key in ("temperature", "top_p", "max_tokens", "stop", "response_format")
                    if client.get(key) is not None
                }
            )
        loop = next((loop for loop in graph.loops if loop.controller_node_id == node.id), None)
        if loop is not None:
            schema = controller_schema(loop)
            requested_format = (
                client.get("response_format") if node.id == plan.final_llm_node_id else None
            )
            if requested_format and requested_format["type"] == "json_object":
                schema["properties"]["payload"] = {"type": "object"}
            elif requested_format and requested_format["type"] == "json_schema":
                payload_schema = json.loads(
                    canonical_json(requested_format["json_schema"]["schema"])
                )
                self._embed_payload_references(payload_schema)
                schema["properties"]["payload"] = payload_schema
                if isinstance(payload_schema.get("$schema"), str):
                    schema["$schema"] = payload_schema["$schema"]
                    if schema["$schema"].rstrip("#").endswith("draft-03/schema"):
                        # Draft 3 expresses presence on each property schema.
                        for shape in (schema, schema["$defs"]["Control"]):
                            for required in shape.pop("required", []):
                                shape["properties"][required]["required"] = True
            fields["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "control_" + loop.id,
                    "strict": True,
                    "schema": schema,
                },
            }
        tools = (
            json.loads(checkpoint.run.context.tools_json)
            if node.tools_enabled and client.get("tool_choice") != "none"
            else []
        )
        if tools:
            fields["tools"] = tools
            choice = client.get("tool_choice") or "auto"
            # Required/forced is satisfied by the first durable owner tool round.
            # Its result resume can then answer; each new loop activation starts at zero.
            fields["tool_choice"] = "auto" if activation.provider_round > 0 else choice
        elif client.get("tool_choice") == "none":
            fields["tool_choice"] = "none"
        fields["parallel_tool_calls"] = client.get("parallel_tool_calls", True)
        return ProviderRequest.model_validate_json(
            canonical_json({"model": graph.base_model, "messages": messages, **fields})
        )

    @staticmethod
    def _embed_payload_references(schema):
        # Work on the detached provider copy. Resource isolation keeps references
        # and literal data intact; declared legacy dialects retain their ID semantics.
        if not isinstance(schema, dict):
            return
        legacy_dialects = {
            "http://json-schema.org/draft-03/schema",
            "https://json-schema.org/draft-03/schema",
            "http://json-schema.org/draft-04/schema",
            "https://json-schema.org/draft-04/schema",
            "http://json-schema.org/draft-06/schema",
            "https://json-schema.org/draft-06/schema",
            "http://json-schema.org/draft-07/schema",
            "https://json-schema.org/draft-07/schema",
        }

        def dialect_of(current, inherited):
            return str(current.get("$schema", inherited)).rstrip("#")

        def id_keyword(dialect):
            return "id" if dialect.endswith(("draft-03/schema", "draft-04/schema")) else "$id"

        dialect = dialect_of(schema, "https://json-schema.org/draft/2020-12/schema")
        root_keyword = id_keyword(dialect)
        identifier = schema.get(root_keyword)
        rebase = dialect in legacy_dialects and (
            "$ref" in schema
            or (isinstance(identifier, str) and identifier.startswith("#") and identifier != "#")
        )
        locations = []

        def collect(current, inherited, root=False):
            if not isinstance(current, dict):
                return
            current_dialect = dialect_of(current, inherited)
            keyword = id_keyword(current_dialect)
            current_id = current.get(keyword)
            ignored_id = current_dialect in legacy_dialects and "$ref" in current
            if not root and not ignored_id and current_id in ("", "#"):
                # These IDs denote the containing resource. Leaving them in a
                # detached resource can register the child under its parent's URI.
                del current[keyword]
            if (
                rebase
                and not root
                and not ignored_id
                and isinstance(current_id, str)
                and current_id.split("#", 1)[0]
            ):
                return
            locations.append(current)
            if current_dialect.endswith("draft-03/schema"):
                # Draft 3 permits schemas alongside named type alternatives and
                # accepts either a single schema or an array under extends.
                for keyword in ("extends", "type", "disallow"):
                    value = current.get(keyword)
                    if isinstance(value, list):
                        for child in value:
                            collect(child, current_dialect)
                    elif keyword == "extends":
                        collect(value, current_dialect)
            for keyword in (
                "additionalProperties",
                "unevaluatedProperties",
                "propertyNames",
                "contains",
                "unevaluatedItems",
                "additionalItems",
                "not",
                "if",
                "then",
                "else",
                "contentSchema",
            ):
                collect(current.get(keyword), current_dialect)
            for keyword in ("allOf", "anyOf", "oneOf", "prefixItems", "items"):
                value = current.get(keyword)
                if isinstance(value, list):
                    for child in value:
                        collect(child, current_dialect)
                elif keyword == "items":
                    collect(value, current_dialect)
            for keyword in (
                "$defs",
                "definitions",
                "properties",
                "patternProperties",
                "dependentSchemas",
                "dependencies",
            ):
                value = current.get(keyword)
                if isinstance(value, dict):
                    for child in value.values():
                        collect(child, current_dialect)

        collect(schema, dialect, root=True)
        if not rebase:
            if identifier in (None, "", "#"):
                schema[root_keyword] = (
                    "https://cognitive-graph.invalid/schema/"
                    + raw_text_hash(canonical_json(schema))
                    + "/"
                )
            return
        known_locations = {id(location) for location in locations}
        copied_targets = {}
        target_names = {}
        private_key = "cg_refs_" + raw_text_hash(canonical_json(schema))
        for location in locations:
            for keyword in ("$ref", "$dynamicRef"):
                reference = location.get(keyword)
                if reference == "#":
                    location[keyword] = "#/properties/payload"
                elif isinstance(reference, str) and reference.startswith("#/"):
                    pointer = tuple(
                        part.replace("~1", "/").replace("~0", "~")
                        for part in unquote(reference[2:]).split("/")
                    )
                    target = schema
                    try:
                        for part in pointer:
                            target = target[int(part)] if isinstance(target, list) else target[part]
                    except (KeyError, IndexError, TypeError, ValueError):
                        target = None
                    if isinstance(target, dict) and id(target) not in known_locations:
                        # A reference can activate annotation/literal data as a schema.
                        # Rewrite a detached context, never its original literal value.
                        if pointer not in target_names:
                            name = "target" + str(len(target_names))
                            target_names[pointer] = name
                            copied_targets[name] = json.loads(canonical_json(target))
                            collect(copied_targets[name], dialect)
                        name = target_names[pointer]
                        location[keyword] = (
                            f"#/properties/payload/definitions/{private_key}/definitions/{name}"
                        )
                    else:
                        location[keyword] = "#/properties/payload/" + reference[2:]
        if copied_targets:
            schema.setdefault("definitions", {})[private_key] = {"definitions": copied_targets}

    async def _provider_call(self, request):
        task = asyncio.create_task(self.provider.complete(request))
        timer = asyncio.create_task(self.clock.sleep(self.settings.llm_timeout_seconds))
        try:
            done, _ = await asyncio.wait((task, timer), return_when=asyncio.FIRST_COMPLETED)
            if task in done:
                return task.result()
            raise CGError(ErrorCode.LLM_TIMEOUT, "Upstream inference deadline expired")
        finally:
            task.cancel()
            timer.cancel()
            await asyncio.gather(task, timer, return_exceptions=True)

    def _apply_outcome(self, checkpoint, activation_id, attempt_id, response, plan):
        activation = next(
            item for item in checkpoint.activations if item.activation_id == activation_id
        )
        if activation.status != "running" or activation.attempt_id != attempt_id:
            raise CGError(
                ErrorCode.CONTINUATION_CONFLICT, "Provider outcome belongs to a stale attempt"
            )
        message = response.choices[0].message
        node = next(
            node for node in plan.snapshot.graph().nodes if node.id == activation.key.node_id
        )
        client = json.loads(checkpoint.run.policy.client_request_json)
        choice = client.get("tool_choice")
        if (
            node.tools_enabled
            and activation.provider_round == 0
            and (isinstance(choice, dict) or choice == "required")
            and not message.tool_calls
        ):
            raise CGError(ErrorCode.UPSTREAM_ERROR, "Provider did not satisfy required tool choice")
        history = json.loads(activation.messages_json)
        history.append(message.model_dump(mode="json", exclude_none=True))
        updates = {
            "messages_json": canonical_json(history),
            "usage_json": response.usage.model_dump_json() if response.usage is not None else None,
            "finish_reason": response.choices[0].finish_reason,
        }
        mappings = ()
        if message.tool_calls:
            tools = json.loads(checkpoint.run.context.tools_json)
            names = {tool["function"]["name"] for tool in tools}
            if (
                not node.tools_enabled
                or client.get("tool_choice") == "none"
                or any(call.function.name not in names for call in message.tool_calls)
            ):
                raise CGError(ErrorCode.UPSTREAM_ERROR, "Provider requested an unavailable tool")
            if (
                activation.provider_round == 0
                and isinstance(choice, dict)
                and any(
                    call.function.name != choice["function"]["name"] for call in message.tool_calls
                )
            ):
                raise CGError(ErrorCode.UPSTREAM_ERROR, "Provider did not satisfy the forced tool")
            mappings = self.bridge.map_calls(activation, response)
            updates.update(status="waiting_tools", provider_round=activation.provider_round + 1)
            event = "activation.waiting_tools"
        else:
            content = message.content
            if isinstance(content, list):
                content = "".join(part.text for part in content)
            loop = next(
                (
                    loop
                    for loop in plan.snapshot.graph().loops
                    if loop.controller_node_id == activation.key.node_id
                ),
                None,
            )
            payload = content
            if loop is not None:
                try:
                    control = ControllerOutput.model_validate_json(content or "")
                except (ValidationError, ValueError):
                    raise CGError(
                        ErrorCode.GRAPH_VALIDATION_FAILED,
                        "Controller response is not strict control JSON",
                    ) from None
                if control.control.decision not in {loop.continue_value, loop.exit_value}:
                    raise CGError(
                        ErrorCode.GRAPH_VALIDATION_FAILED, "Controller decision is outside its enum"
                    )
                payload = control.payload
                updates["control_decision"] = control.control.decision
            updates.update(
                status="completed", payload_json=canonical_json(payload), ended_at=self.clock.now()
            )
            event = "activation.completed"
        activation = activation.model_copy(update=updates)
        checkpoint = checkpoint.model_copy(
            update={
                "activations": tuple(
                    activation if item.activation_id == activation_id else item
                    for item in checkpoint.activations
                ),
                "pending_tools": checkpoint.pending_tools + mappings,
            }
        )
        return append_event(checkpoint, event, self.clock.now(), {"activation_id": activation_id})

    async def _wait_tools(self, checkpoint, namespace):
        run_id = checkpoint.run.run_id
        wake = self.wakes[run_id]
        # Clearing followed by authoritative reload avoids losing a ready signal.
        wake.clear()
        current = await self.repository.load_checkpoint(run_id, namespace)
        batch = next((item for item in current.batches if item.status == "open"), None)
        if batch is None:
            return
        remaining = (batch.expires_at - self.clock.now()).total_seconds()
        if remaining <= 0:
            error = CGError(ErrorCode.TOOL_WAIT_TIMEOUT, "External tool result deadline expired")
            run = await self.repository.terminalize(
                run_id, "failed", error.payload().error, self.clock.now()
            )
            await self.events.notify(run_id)
            if run.status in TERMINAL_RUN_STATUSES:
                raise error
            return
        waiter = asyncio.create_task(wake.wait())
        timer = asyncio.create_task(self.clock.sleep(remaining))
        try:
            await asyncio.wait((waiter, timer), return_when=asyncio.FIRST_COMPLETED)
        finally:
            waiter.cancel()
            timer.cancel()
            await asyncio.gather(waiter, timer, return_exceptions=True)

    async def _finalize(self, checkpoint, output):
        run_id = checkpoint.run.run_id
        payload = json.loads(output.payload_json)
        content = payload if isinstance(payload, str) else canonical_json(payload)
        graph = checkpoint.run.snapshot.graph()
        final_activation = next(
            (
                item
                for item in reversed(checkpoint.activations)
                if item.key.node_id
                == self.validator.compile(checkpoint.run.snapshot).final_llm_node_id
            ),
            None,
        )
        client = json.loads(checkpoint.run.policy.client_request_json)
        requested_format = client.get("response_format") or {}
        native_payload = final_activation is None or final_activation.control_decision is not None
        if requested_format.get("type") in {"json_object", "json_schema"}:
            error_code = (
                ErrorCode.INVALID_PARAMETER
                if final_activation is None
                else ErrorCode.UPSTREAM_ERROR
            )

            def deny_remote(uri):
                raise NoSuchResource(ref=uri)

            def reject_nonfinite(value):
                raise ValueError("Invalid JSON constant")

            try:
                value = (
                    payload
                    if native_payload
                    else json.loads(payload, parse_constant=reject_nonfinite)
                )
                if requested_format["type"] == "json_object":
                    if not isinstance(value, dict):
                        raise ValueError("Expected JSON object")
                else:
                    requested_schema = requested_format["json_schema"]["schema"]
                    validator = (
                        validator_for(requested_schema, default=None)
                        if "$schema" in requested_schema
                        else validator_for(requested_schema)
                    )
                    if validator is None:
                        raise SchemaError("Unknown JSON schema dialect")
                    validator.check_schema(requested_schema)
                    validator(requested_schema, registry=Registry(retrieve=deny_remote)).validate(
                        value
                    )
            except (
                SchemaError,
                SchemaValidationError,
                Unresolvable,
                ValueError,
                TypeError,
                KeyError,
                RecursionError,
            ):
                raise CGError(
                    error_code, "Final graph output does not satisfy requested response format"
                ) from None
            if native_payload:
                content = canonical_json(payload)
        finish = "stop"
        if final_activation is not None:
            # Preserve length for ordinary final text; validated controller payload exits
            # use stop because internal control JSON is not an external completion.
            finish = (
                "stop"
                if final_activation.control_decision is not None
                else (final_activation.finish_reason or "stop")
            )
        completion = ChatCompletionResponse.model_validate(
            {
                "id": "chatcmpl-" + uuid.uuid4().hex,
                "created": int(self.clock.now().timestamp()),
                "model": "cg/" + graph.id,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": finish,
                    }
                ],
                **(
                    {"usage": json.loads(final_activation.usage_json)}
                    if final_activation is not None and final_activation.usage_json is not None
                    else {}
                ),
            }
        )
        envelope = ResponseEnvelope(
            run_id=run_id,
            batch_id=None,
            response_sequence=len(checkpoint.responses) + 1,
            completion_json=completion.model_dump_json(),
        )
        proposed = checkpoint.model_copy(
            update={
                "run": checkpoint.run.model_copy(
                    update={
                        "status": "completed",
                        "ended_at": self.clock.now(),
                        "output_json": output.payload_json,
                    }
                ),
                "responses": checkpoint.responses + (envelope,),
            }
        )
        await self.repository.complete_run(proposed, envelope, checkpoint.run.state_version)
        self.active_since.pop(run_id, None)
        await self.events.notify(run_id)

    async def _run(self, run_id, namespace):
        pending: dict[asyncio.Task, tuple[str, str]] = {}
        try:
            await self.leases[run_id].wait()
            checkpoint = await self.repository.load_checkpoint(run_id, namespace)
            plan = self.validator.compile(checkpoint.run.snapshot)
            while not self.stopping:
                checkpoint = await self.repository.load_checkpoint(run_id, namespace)
                if checkpoint.run.status in TERMINAL_RUN_STATUSES:
                    return
                if any(batch.status == "open" for batch in checkpoint.batches):
                    await self._wait_tools(checkpoint, namespace)
                    continue
                if checkpoint.run.status != "running":

                    def start(current):
                        run = current.run.model_copy(
                            update={
                                "status": "running",
                                "started_at": current.run.started_at or self.clock.now(),
                                "queue_elapsed_seconds": max(
                                    0.0, (self.clock.now() - current.run.created_at).total_seconds()
                                )
                                if current.run.status == "queued"
                                else current.run.queue_elapsed_seconds,
                            }
                        )
                        return append_event(
                            current.model_copy(update={"run": run}), "run.running", self.clock.now()
                        )

                    checkpoint = await self._update(run_id, namespace, start)
                checkpoint = await self._update(
                    run_id,
                    namespace,
                    lambda current: self._advance(self._resume_owners(current), plan),
                )
                if (
                    checkpoint.run.active_elapsed_seconds
                    >= checkpoint.run.policy.active_timeout_seconds
                ):
                    raise CGError(ErrorCode.RUN_TIMEOUT, "Active run deadline expired")
                output = next(
                    (
                        item
                        for item in checkpoint.activations
                        if item.key.node_id == plan.output_node_id and item.status == "completed"
                    ),
                    None,
                )
                if output is not None:
                    await self._finalize(checkpoint, output)
                    return
                unexposed = any(tool.status == "unexposed" for tool in checkpoint.pending_tools)
                if unexposed and not pending:
                    await self._update(
                        run_id,
                        namespace,
                        lambda current: current.model_copy(
                            update={
                                "run": current.run.model_copy(update={"status": "waiting_tools"})
                            }
                        ),
                    )
                    await self.bridge.prepare_batch(run_id, namespace)
                    await self.events.notify(run_id)
                    continue
                if not unexposed:
                    for activation in checkpoint.activations:
                        if activation.status != "ready":
                            continue
                        attempt_id = uuid.uuid4().hex
                        claimed = await self.repository.claim_activation(
                            activation.key, attempt_id, self.clock.now()
                        )
                        if claimed is None:
                            continue
                        latest = await self.repository.load_checkpoint(run_id, namespace)
                        task = asyncio.create_task(
                            self._provider_call(self._request(latest, claimed, plan))
                        )
                        pending[task] = (claimed.activation_id, attempt_id)
                if not pending:
                    raise CGError(
                        ErrorCode.GRAPH_VALIDATION_FAILED,
                        "Graph has no ready work or valid tool wait",
                    )
                latest = await self.repository.get_run(run_id, namespace)
                remaining = latest.policy.active_timeout_seconds - latest.active_elapsed_seconds
                baseline = self.active_since.get(run_id, self.clock.monotonic())
                remaining -= max(0.0, self.clock.monotonic() - baseline)
                timer = asyncio.create_task(self.clock.sleep(max(0.0, remaining)))
                try:
                    done, _ = await asyncio.wait(
                        (*pending, timer), return_when=asyncio.FIRST_COMPLETED
                    )
                    if timer in done and not any(task in done for task in pending):
                        raise CGError(ErrorCode.RUN_TIMEOUT, "Active run deadline expired")
                finally:
                    timer.cancel()
                    await asyncio.gather(timer, return_exceptions=True)
                for task in tuple(pending):
                    if task not in done:
                        continue
                    activation_id, attempt_id = pending.pop(task)
                    response = task.result()
                    await self._update(
                        run_id,
                        namespace,
                        lambda current, id_=activation_id, attempt=attempt_id, result=response: (
                            self._apply_outcome(current, id_, attempt, result, plan)
                        ),
                    )
        except asyncio.CancelledError:
            await self._account_active(run_id, namespace)
            checkpoint = await self.repository.load_checkpoint(run_id, namespace)
            if checkpoint.run.status == "running":
                if any(batch.status == "closed" for batch in checkpoint.batches) and not any(
                    activation.status == "running" for activation in checkpoint.activations
                ):
                    await self._update(
                        run_id,
                        namespace,
                        lambda current: current.model_copy(
                            update={
                                "run": current.run.model_copy(update={"status": "waiting_tools"})
                            }
                        ),
                    )
                else:
                    await self.repository.terminalize(run_id, "interrupted", None, self.clock.now())
            raise
        except CGError as error:
            await self._account_active(run_id, namespace)
            await self.repository.terminalize(
                run_id, "failed", error.payload().error, self.clock.now()
            )
        except Exception:
            await self._account_active(run_id, namespace)
            error = CGError(ErrorCode.UPSTREAM_ERROR, "Graph execution failed")
            await self.repository.terminalize(
                run_id, "failed", error.payload().error, self.clock.now()
            )
        finally:
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            await self.events.notify(run_id)
            run = await self.repository.get_run(run_id, namespace)
            if run.status in TERMINAL_RUN_STATUSES:
                lease = self.leases.pop(run_id, None)
                if lease is not None:
                    await lease.release()
                await self.repository.cleanup_history(
                    self.clock.now() - timedelta(days=self.settings.history_retention_days)
                )
            self.active_since.pop(run_id, None)
            self.tasks.pop(run_id, None)
            self.wakes.pop(run_id, None)
