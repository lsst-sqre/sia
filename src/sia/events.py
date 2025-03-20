"""App metrics events."""

from datetime import timedelta
from typing import override

from safir.dependencies.metrics import EventMaker
from safir.metrics import EventManager, EventPayload


class SIAQuerySucceeded(EventPayload):
    """Reported when a SIA query is successfully executed."""

    duration: timedelta


class SIAQueryFailed(EventPayload):
    """Reported when a SIA query fails."""

    duration: timedelta | None
    error: str | None = None


class Events(EventMaker):
    """Container for app metrics event publishers."""

    @override
    async def initialize(self, manager: EventManager) -> None:
        self.sia_query_succeeded = await manager.create_publisher(
            "sia_query_succeeded", SIAQuerySucceeded
        )
        self.sia_query_failed = await manager.create_publisher(
            "sia_query_failed", SIAQueryFailed
        )
