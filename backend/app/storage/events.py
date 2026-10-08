"""Notifications wake catch-up reads; only committed SQLite events are emitted."""

import asyncio

from app.contracts.api import TERMINAL_RUN_STATUSES
from app.contracts.interfaces import RunRepository


class DurableEventBus:
    def __init__(self, repository: RunRepository):
        self.repository = repository
        self.conditions: dict[str, asyncio.Condition] = {}

    async def notify(self, run_id: str) -> None:
        condition = self.conditions.get(run_id)
        if condition is not None:
            async with condition:
                condition.notify_all()

    async def read_after(self, run_id, namespace, after_event_id):
        return await self.repository.read_events(run_id, namespace, after_event_id)

    async def subscribe(self, run_id, namespace, after_event_id):
        condition = self.conditions.setdefault(run_id, asyncio.Condition())
        cursor = after_event_id
        while True:
            # Register before querying so a notification cannot fall between read and wait.
            async with condition:
                events = await self.read_after(run_id, namespace, cursor)
                if not events:
                    run = await self.repository.get_run(run_id, namespace)
                    if run.status in TERMINAL_RUN_STATUSES:
                        # Terminalization can commit between the first event read and
                        # status read. Its final event must still reach this cursor.
                        events = await self.read_after(run_id, namespace, cursor)
                        if not events:
                            return
                    else:
                        try:
                            await asyncio.wait_for(condition.wait(), timeout=1)
                        except TimeoutError:
                            pass
                        continue
            for event in events:
                cursor = event.event_id
                yield event
