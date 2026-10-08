import asyncio

import pytest

from app.contracts.errors import CGError
from app.runtime.admission import BoundedAdmissionController


@pytest.mark.asyncio
async def test_capacity_queue_promotion_and_cancel():
    controller = BoundedAdmissionController(1, 1)
    first = await controller.acquire("graph")
    await first.wait()
    queued = await controller.acquire("direct")
    waiter = asyncio.create_task(queued.wait())
    await asyncio.sleep(0)
    assert not waiter.done()
    with pytest.raises(CGError, match="capacity") as failure:
        await controller.acquire("overflow")
    assert failure.value.status_code == 429
    await first.release()
    await asyncio.wait_for(waiter, 1)
    await queued.release()
    await queued.release()
    last = await controller.acquire("last")
    await last.wait()
    await last.release()


@pytest.mark.asyncio
async def test_restore_reserved_waiting_and_queued_jobs():
    controller = BoundedAdmissionController(1, 2)
    await controller.restore(("waiting",), ("queued",))
    waiting = await controller.acquire("waiting")
    queued = await controller.acquire("queued")
    assert queued is await controller.acquire("queued")
    task = asyncio.create_task(queued.wait())
    await asyncio.sleep(0)
    assert not task.done()
    await waiting.release()
    await asyncio.wait_for(task, 1)
    await queued.release()


@pytest.mark.asyncio
async def test_release_queued_lease_does_not_consume_active_slot():
    controller = BoundedAdmissionController(1, 1)
    first = await controller.acquire("first")
    second = await controller.acquire("second")
    await second.release()
    replacement = await controller.acquire("replacement")
    task = asyncio.create_task(replacement.wait())
    await asyncio.sleep(0)
    assert not task.done()
    await first.release()
    await task
    await replacement.release()
