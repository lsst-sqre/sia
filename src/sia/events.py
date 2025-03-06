"""App metrics events."""

from datetime import timedelta
from typing import override

from safir.dependencies.metrics import EventMaker
from safir.metrics import EventManager, EventPayload


class SIAQuery(EventPayload):
    """Reported when a SIA query is executed."""

    success: bool
    duration: timedelta | None


class Events(EventMaker):
    """Container for app metrics event publishers."""

    @override
    async def initialize(self, manager: EventManager) -> None:
        self.sia_query = await manager.create_publisher("sia_query", SIAQuery)
