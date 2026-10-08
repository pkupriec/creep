"""Atomic local graph files; one shared per-path lock owns every graph transition.

Drafts may be incomplete topologically so they remain editable. Publication and
run snapshots require full validation. Publications are retained and immutable;
the highest stored revision is authoritative and corruption never rolls it back.
"""

import asyncio
import errno
import os
import re
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from pydantic import ValidationError

from app.contracts.api import GraphSummary
from app.contracts.config import MAX_GRAPH_BYTES
from app.contracts.errors import CGError, ErrorCode
from app.contracts.graph import Graph
from app.contracts.interfaces import GraphSnapshot, Validator

T = TypeVar("T")
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
WINDOWS_DEVICES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


class FileGraphRepository:
    """Implement GraphRepository for a single local backend process.

    Locks are shared across repository instances for the same absolute graph
    path. Filesystem work executes off the event loop; no lock spans inference
    or a database transaction. Multiple backend processes are unsupported.
    """

    _locks: dict[str, threading.RLock] = {}
    _locks_guard = threading.Lock()

    def __init__(self, data_dir: Path, validator: Validator):
        self.data_dir = data_dir.absolute()
        self.validator = validator

    @staticmethod
    def _safe_id(graph_id: str) -> None:
        if (
            not isinstance(graph_id, str)
            or not SAFE_ID.fullmatch(graph_id)
            or graph_id.upper() in WINDOWS_DEVICES
        ):
            raise CGError(ErrorCode.INVALID_PARAMETER, "Invalid graph identifier.")

    @staticmethod
    def _revision(revision: int) -> None:
        if type(revision) is not int or revision < 1:
            raise CGError(ErrorCode.INVALID_PARAMETER, "Invalid graph revision.")

    def _lock(self, graph_id: str) -> threading.RLock:
        self._safe_id(graph_id)
        key = os.path.normcase(str(self.data_dir / "graphs" / f"{graph_id}.json"))
        with self._locks_guard:
            return self._locks.setdefault(key, threading.RLock())

    def _check_path(self, path: Path) -> None:
        try:
            path.relative_to(self.data_dir)
        except ValueError as exc:
            raise CGError(ErrorCode.INVALID_PARAMETER, "Unsafe graph storage path.") from exc
        if self.data_dir.resolve() != self.data_dir:
            raise CGError(ErrorCode.INVALID_PARAMETER, "Linked graph storage is not allowed.")
        current = self.data_dir
        for part in path.relative_to(self.data_dir).parts:
            current /= part
            if current.is_symlink() or current.resolve() != current:
                raise CGError(ErrorCode.INVALID_PARAMETER, "Linked graph storage is not allowed.")

    def _directory(self, path: Path) -> None:
        self._check_path(path)
        missing = []
        current = path
        while not current.exists():
            missing.append(current)
            current = current.parent
        path.mkdir(parents=True, exist_ok=True)
        self._check_path(path)
        for created in reversed(missing):
            self._sync_directory(created.parent)

    @staticmethod
    def _sync_directory(path: Path) -> None:
        if os.name == "nt":
            return  # Windows does not support POSIX directory fsync descriptors.
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            try:
                os.fsync(descriptor)
            except OSError as exc:
                if exc.errno not in {errno.EINVAL, errno.ENOTSUP}:
                    raise
        finally:
            os.close(descriptor)

    def _write(self, path: Path, payload: bytes) -> None:
        self._directory(path.parent)
        self._check_path(path)
        descriptor, filename = tempfile.mkstemp(prefix=".cg-", suffix=".tmp", dir=path.parent)
        temporary = Path(filename)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            self._check_path(path)
            os.replace(temporary, path)
            self._sync_directory(path.parent)
        finally:
            temporary.unlink(missing_ok=True)

    def _read(self, path: Path, graph_id: str, revision: int | None = None) -> Graph:
        self._check_path(path)
        if not path.exists():
            raise CGError(ErrorCode.GRAPH_NOT_FOUND, "Graph not found.")
        if not path.is_file() or path.stat().st_size > MAX_GRAPH_BYTES:
            raise CGError(ErrorCode.STORAGE_ERROR, "Stored graph is invalid.")
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as stream:
            payload = stream.read(MAX_GRAPH_BYTES + 1)
        if len(payload) > MAX_GRAPH_BYTES:
            raise CGError(ErrorCode.STORAGE_ERROR, "Stored graph is invalid.")
        graph = Graph.model_validate_json(payload)
        if graph.id != graph_id or (revision is not None and graph.revision != revision):
            raise CGError(ErrorCode.STORAGE_ERROR, "Stored graph identity is invalid.")
        return graph

    @staticmethod
    def _snapshot(graph: Graph) -> GraphSnapshot:
        snapshot = GraphSnapshot.from_graph(graph)
        if len(snapshot.graph_json.encode("utf-8")) > MAX_GRAPH_BYTES:
            raise CGError(ErrorCode.REQUEST_TOO_LARGE, "Graph exceeds the size limit.")
        return snapshot

    def _draft_path(self, graph_id: str) -> Path:
        return self.data_dir / "graphs" / f"{graph_id}.json"

    def _publication_path(self, graph_id: str, revision: int) -> Path:
        return self.data_dir / "published" / graph_id / f"{revision}.json"

    def _highest(self, graph_id: str) -> int | None:
        directory = self.data_dir / "published" / graph_id
        self._check_path(directory)
        if not directory.exists():
            return None
        revisions = []
        for path in directory.glob("*.json"):
            self._check_path(path)
            if not re.fullmatch(r"[1-9][0-9]*", path.stem):
                raise CGError(ErrorCode.STORAGE_ERROR, "Stored publication revision is invalid.")
            revisions.append(int(path.stem))
        return max(revisions, default=None)

    def _published(self, graph_id: str, revision: int) -> GraphSnapshot:
        graph = self._read(self._publication_path(graph_id, revision), graph_id, revision)
        snapshot = self._snapshot(graph)
        try:
            self.validator.compile(snapshot)
        except CGError as exc:
            raise CGError(ErrorCode.STORAGE_ERROR, "Stored publication is invalid.") from exc
        return snapshot

    async def _run(self, function: Callable[..., T], *arguments: object) -> T:
        try:
            return await asyncio.to_thread(function, *arguments)
        except CGError:
            raise
        except (OSError, ValueError, ValidationError, RecursionError) as exc:
            raise CGError(ErrorCode.STORAGE_ERROR, "Graph storage operation failed.") from exc

    async def create(self, graph: Graph) -> Graph:
        snapshot = self._snapshot(graph)
        if graph.revision != 1:
            raise CGError(ErrorCode.INVALID_PARAMETER, "New graphs require revision one.")

        def operation():
            with self._lock(snapshot.graph_id):
                path = self._draft_path(snapshot.graph_id)
                self._check_path(path)
                if path.exists() or self._highest(snapshot.graph_id) is not None:
                    raise CGError(ErrorCode.REVISION_CONFLICT, "Graph identifier already exists.")
                self._write(path, snapshot.graph_json.encode("utf-8"))
                return snapshot.graph()

        return await self._run(operation)

    async def get(self, graph_id: str) -> Graph:
        def operation():
            with self._lock(graph_id):
                return self._read(self._draft_path(graph_id), graph_id)

        return await self._run(operation)

    async def save(self, graph: Graph, expected_revision: int) -> Graph:
        self._revision(expected_revision)
        original = self._snapshot(graph)
        if original.revision != expected_revision:
            raise CGError(
                ErrorCode.REVISION_CONFLICT, "Graph revision does not match expected revision."
            )

        def operation():
            with self._lock(original.graph_id):
                path = self._draft_path(original.graph_id)
                current = self._read(path, original.graph_id)
                if current.revision != expected_revision:
                    raise CGError(ErrorCode.REVISION_CONFLICT, "Graph revision has changed.")
                saved = original.graph()
                saved.revision = expected_revision + 1
                snapshot = self._snapshot(saved)
                self._write(path, snapshot.graph_json.encode("utf-8"))
                return snapshot.graph()

        return await self._run(operation)

    async def publish(self, graph_id: str, expected_revision: int) -> GraphSnapshot:
        self._revision(expected_revision)

        def operation():
            with self._lock(graph_id):
                graph = self._read(self._draft_path(graph_id), graph_id)
                if graph.revision != expected_revision:
                    raise CGError(ErrorCode.REVISION_CONFLICT, "Graph revision has changed.")
                snapshot = self._snapshot(graph)
                self.validator.compile(snapshot)
                highest = self._highest(graph_id)
                if highest is not None:
                    self._published(graph_id, highest)  # Never hide a corrupt current publication.
                path = self._publication_path(graph_id, graph.revision)
                self._check_path(path)
                if path.exists():
                    existing = self._published(graph_id, graph.revision)
                    if existing.graph_hash != snapshot.graph_hash:
                        raise CGError(
                            ErrorCode.REVISION_CONFLICT, "Published revisions are immutable."
                        )
                    return existing
                self._write(path, snapshot.graph_json.encode("utf-8"))
                return snapshot

        return await self._run(operation)

    async def load_snapshot(
        self, graph_id: str, revision: int | None = None, published_only: bool = False
    ) -> GraphSnapshot:
        if revision is not None:
            self._revision(revision)

        def operation():
            with self._lock(graph_id):
                if published_only:
                    selected = revision if revision is not None else self._highest(graph_id)
                    if selected is None:
                        raise CGError(ErrorCode.GRAPH_NOT_FOUND, "Published graph not found.")
                    return self._published(graph_id, selected)
                draft = self._read(self._draft_path(graph_id), graph_id)
                if revision is None or revision == draft.revision:
                    snapshot = self._snapshot(draft)
                    self.validator.compile(snapshot)
                    return snapshot
                path = self._publication_path(graph_id, revision)
                self._check_path(path)
                if path.exists():
                    return self._published(graph_id, revision)
                raise CGError(
                    ErrorCode.REVISION_CONFLICT, "Requested graph revision is unavailable."
                )

        return await self._run(operation)

    async def list_graphs(self) -> tuple[GraphSummary, ...]:
        def operation():
            directory = self.data_dir / "graphs"
            self._check_path(directory)
            result = []
            for path in sorted(directory.glob("*.json")):
                with self._lock(path.stem):
                    graph = self._read(path, path.stem)
                    highest = self._highest(graph.id)
                    if highest is not None:
                        self._published(graph.id, highest)
                    result.append(
                        GraphSummary(
                            id=graph.id,
                            name=graph.name,
                            revision=graph.revision,
                            published_revision=highest,
                        )
                    )
            return tuple(result)

        return await self._run(operation)

    async def list_published(self) -> tuple[GraphSnapshot, ...]:
        def operation():
            directory = self.data_dir / "published"
            self._check_path(directory)
            result = []
            if directory.exists():
                for path in sorted(directory.iterdir()):
                    with self._lock(path.name):
                        self._check_path(path)
                        if not path.is_dir():
                            raise CGError(
                                ErrorCode.STORAGE_ERROR, "Publication directory is invalid."
                            )
                        highest = self._highest(path.name)
                        if highest is not None:
                            result.append(self._published(path.name, highest))
            return tuple(result)

        return await self._run(operation)
