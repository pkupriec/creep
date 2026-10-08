"""Atomic draft revisions and immutable publications, without inference."""

import asyncio
import json
import os

import pytest
from test_validator import make_graph

from app.contracts.config import MAX_GRAPH_BYTES
from app.contracts.errors import CGError, ErrorCode
from app.contracts.graph import Graph
from app.graphs.repository import FileGraphRepository
from app.graphs.validator import GraphValidator


@pytest.fixture
def repository(tmp_path):
    return FileGraphRepository(tmp_path, GraphValidator())


@pytest.mark.asyncio
async def test_create_save_publish_and_retained_snapshot_after_restart(repository, tmp_path):
    graph = Graph.model_validate(make_graph())
    await repository.create(graph)
    first = await repository.publish(graph.id, 1)
    assert (tmp_path / "published/test/1.json").exists()
    graph.name = "New draft"
    saved = await repository.save(graph, 1)
    assert saved.revision == 2
    assert graph.revision == 1
    second = await repository.publish(graph.id, 2)
    restarted = FileGraphRepository(tmp_path, GraphValidator())
    assert (await restarted.load_snapshot(graph.id, 1)).graph_hash == first.graph_hash
    assert (
        await restarted.load_snapshot(graph.id, published_only=True)
    ).graph_hash == second.graph_hash
    assert first.graph().name == "Test"
    assert (await restarted.list_graphs())[0].published_revision == 2
    assert len(await restarted.list_published()) == 1
    await restarted.save(saved, 2)
    assert (await restarted.load_snapshot(graph.id)).revision == 3


@pytest.mark.asyncio
async def test_publication_does_not_expose_drafts_and_is_idempotent(repository):
    await repository.create(Graph.model_validate(make_graph()))
    assert await repository.list_published() == ()
    published = await repository.publish("test", 1)
    assert await repository.publish("test", 1) == published


@pytest.mark.asyncio
async def test_conflicts_leave_original_bytes_unchanged(repository, tmp_path):
    graph = await repository.create(Graph.model_validate(make_graph()))
    path = tmp_path / "graphs/test.json"
    original = path.read_bytes()
    for operation in (
        repository.create(graph),
        repository.save(graph, 2),
        repository.publish("test", 2),
    ):
        with pytest.raises(CGError) as exc:
            await operation
        assert exc.value.code == ErrorCode.REVISION_CONFLICT
        assert path.read_bytes() == original


@pytest.mark.asyncio
async def test_overwritten_unpublished_revision_conflicts(repository):
    graph = await repository.create(Graph.model_validate(make_graph()))
    await repository.save(graph, 1)
    with pytest.raises(CGError) as exc:
        await repository.load_snapshot("test", 1)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_concurrent_saves_one_winner_across_repository_instances(repository, tmp_path):
    graph = await repository.create(Graph.model_validate(make_graph()))
    other = FileGraphRepository(tmp_path, GraphValidator())
    results = await asyncio.gather(
        repository.save(graph, 1), other.save(graph, 1), return_exceptions=True
    )
    assert sum(isinstance(result, Graph) for result in results) == 1
    assert sum(isinstance(result, CGError) and result.status_code == 409 for result in results) == 1
    assert (await repository.get("test")).revision == 2


@pytest.mark.asyncio
async def test_invalid_draft_can_be_edited_but_never_published_or_run(repository):
    value = make_graph()
    value["edges"] = []
    await repository.create(Graph.model_validate(value))
    for operation in (repository.publish("test", 1), repository.load_snapshot("test")):
        with pytest.raises(CGError) as exc:
            await operation
        assert exc.value.code == ErrorCode.GRAPH_VALIDATION_FAILED


@pytest.mark.asyncio
@pytest.mark.parametrize("graph_id", ["../other", "a/b", "a\\b", "/absolute", "..", "CON"])
async def test_safe_identifiers_reject_paths(repository, graph_id):
    with pytest.raises(CGError) as exc:
        await repository.get(graph_id)
    assert exc.value.status_code == 400
    assert graph_id not in exc.value.message


@pytest.mark.asyncio
async def test_corrupt_highest_publication_is_not_silently_rolled_back(repository, tmp_path):
    graph = await repository.create(Graph.model_validate(make_graph()))
    await repository.publish("test", 1)
    saved = await repository.save(graph, 1)
    await repository.publish("test", saved.revision)
    (tmp_path / "published/test/2.json").write_text("not json")
    for operation in (
        repository.list_published(),
        repository.load_snapshot("test", published_only=True),
        repository.list_graphs(),
    ):
        with pytest.raises(CGError) as exc:
            await operation
        assert exc.value.code == ErrorCode.STORAGE_ERROR


@pytest.mark.asyncio
async def test_oversized_graph_is_not_written(repository, tmp_path):
    graph = Graph.model_validate(make_graph())
    graph.nodes[1].system_prompt = "x" * MAX_GRAPH_BYTES
    with pytest.raises(CGError) as exc:
        await repository.create(graph)
    assert exc.value.status_code == 413
    assert not (tmp_path / "graphs/test.json").exists()


@pytest.mark.asyncio
async def test_atomic_replace_failure_keeps_old_graph_and_cleans_temp(
    repository, tmp_path, monkeypatch
):
    import app.graphs.repository as module

    graph = await repository.create(Graph.model_validate(make_graph()))
    path = tmp_path / "graphs/test.json"
    before = path.read_bytes()

    def fail_replace(*args):
        raise OSError("sensitive raw path/token must not leak")

    monkeypatch.setattr(module.os, "replace", fail_replace)
    with pytest.raises(CGError) as exc:
        await repository.save(graph, 1)
    assert exc.value.code == ErrorCode.STORAGE_ERROR
    assert "sensitive" not in exc.value.message
    assert path.read_bytes() == before
    assert list(path.parent.iterdir()) == [path]


@pytest.mark.asyncio
async def test_symlink_graph_and_directory_escape_rejected(repository, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "secret.json"
    target.write_text(json.dumps(make_graph()))
    graphs = tmp_path / "graphs"
    graphs.mkdir()
    link = graphs / "test.json"
    try:
        link.symlink_to(target)
    except OSError as exc:
        if os.name != "nt" or exc.winerror != 1314:
            raise
    else:
        with pytest.raises(CGError):
            await repository.get("test")
        link.unlink()
    graphs.rmdir()
    if os.name == "nt":
        import _winapi

        # NTFS junctions exercise a real directory reparse-point escape without
        # requiring Windows' separate symbolic-link creation privilege.
        _winapi.CreateJunction(str(outside), str(graphs))
    else:
        graphs.symlink_to(outside, target_is_directory=True)
    with pytest.raises(CGError):
        await repository.create(Graph.model_validate(make_graph()))
    assert target.exists()


@pytest.mark.asyncio
async def test_published_bytes_cannot_be_replaced_by_mutated_same_revision(repository, tmp_path):
    graph = await repository.create(Graph.model_validate(make_graph()))
    snapshot = await repository.publish("test", 1)
    publication = tmp_path / "published/test/1.json"
    original = publication.read_bytes()
    graph.name = "Tampered outside normal save"
    (tmp_path / "graphs/test.json").write_text(graph.model_dump_json())
    with pytest.raises(CGError) as exc:
        await repository.publish("test", 1)
    assert exc.value.status_code == 409
    assert publication.read_bytes() == original
    assert (
        await repository.load_snapshot("test", published_only=True)
    ).graph_hash == snapshot.graph_hash


@pytest.mark.asyncio
async def test_publication_save_snapshot_race_observes_complete_revision(repository):
    graph = await repository.create(Graph.model_validate(make_graph()))
    await repository.publish("test", 1)
    graph.name = "Second revision"
    saved, captured = await asyncio.gather(
        repository.save(graph, 1), repository.load_snapshot("test")
    )
    assert saved.revision == 2
    assert (captured.revision, captured.graph().name) in {(1, "Test"), (2, "Second revision")}
    await repository.publish("test", 2)
    assert (await repository.load_snapshot("test", 1)).graph().name == "Test"


@pytest.mark.asyncio
async def test_file_fsync_failure_keeps_prior_draft(repository, tmp_path, monkeypatch):
    import app.graphs.repository as module

    graph = await repository.create(Graph.model_validate(make_graph()))
    path = tmp_path / "graphs/test.json"
    original = path.read_bytes()

    def fail_sync(descriptor):
        raise OSError("private data")

    monkeypatch.setattr(module.os, "fsync", fail_sync)
    with pytest.raises(CGError) as exc:
        await repository.save(graph, 1)
    assert exc.value.code == ErrorCode.STORAGE_ERROR
    assert path.read_bytes() == original
    assert list(path.parent.iterdir()) == [path]


@pytest.mark.asyncio
async def test_stored_identity_corruption_is_a_sanitized_storage_error(repository, tmp_path):
    graph = await repository.create(Graph.model_validate(make_graph()))
    graph.id = "wrong"
    (tmp_path / "graphs/test.json").write_text(graph.model_dump_json())
    with pytest.raises(CGError) as exc:
        await repository.get("test")
    assert exc.value.code == ErrorCode.STORAGE_ERROR
    assert "wrong" not in exc.value.message
