"""One bounded admission pool shared by graphs and ephemeral direct calls."""

import asyncio
from collections import OrderedDict

from app.contracts.errors import CGError, ErrorCode


class _Lease:
    def __init__(self, controller, job_id: str, active: bool):
        self.controller = controller
        self.job_id = job_id
        self.admitted = asyncio.Event()
        self.released = False
        if active:
            self.admitted.set()

    async def wait(self) -> None:
        await self.admitted.wait()
        if self.released:
            raise CGError(ErrorCode.CANCELLED, "Admission reservation was released")

    async def release(self) -> None:
        async with self.controller.lock:
            if self.released:
                return
            self.released = True
            self.admitted.set()
            self.controller.active.pop(self.job_id, None)
            self.controller.queued.pop(self.job_id, None)
            self.controller.leases.pop(self.job_id, None)
            while (
                self.controller.queued and len(self.controller.active) < self.controller.max_active
            ):
                job_id, lease = self.controller.queued.popitem(last=False)
                self.controller.active[job_id] = lease
                lease.admitted.set()


class BoundedAdmissionController:
    def __init__(self, max_active: int, max_queued: int):
        if max_active < 1 or max_queued < 0:
            raise ValueError("Admission limits must be positive active and nonnegative queued")
        self.max_active = max_active
        self.max_queued = max_queued
        self.lock = asyncio.Lock()
        self.active: dict[str, _Lease] = {}
        self.queued: OrderedDict[str, _Lease] = OrderedDict()
        self.leases: dict[str, _Lease] = {}

    async def acquire(self, job_id: str) -> _Lease:
        async with self.lock:
            if job_id in self.leases:
                return self.leases[job_id]
            active = len(self.active) < self.max_active
            if not active and len(self.queued) >= self.max_queued:
                raise CGError(ErrorCode.QUEUE_FULL, "Active and queued capacity is full")
            lease = _Lease(self, job_id, active)
            self.leases[job_id] = lease
            if active:
                self.active[job_id] = lease
            else:
                self.queued[job_id] = lease
            return lease

    async def restore(
        self, active_job_ids: tuple[str, ...], queued_job_ids: tuple[str, ...]
    ) -> None:
        async with self.lock:
            ids = active_job_ids + queued_job_ids
            if self.leases or len(ids) != len(set(ids)):
                raise CGError(ErrorCode.STORAGE_ERROR, "Invalid admission recovery state")
            if len(active_job_ids) > self.max_active or len(queued_job_ids) > self.max_queued:
                raise CGError(ErrorCode.QUEUE_FULL, "Recovered runs exceed configured capacity")
            for job_id in active_job_ids:
                lease = _Lease(self, job_id, True)
                self.leases[job_id] = self.active[job_id] = lease
            for job_id in queued_job_ids:
                lease = _Lease(self, job_id, False)
                self.leases[job_id] = lease
                self.queued[job_id] = lease
            while self.queued and len(self.active) < self.max_active:
                job_id, lease = self.queued.popitem(last=False)
                self.active[job_id] = lease
                lease.admitted.set()
