"""Request context dependency for FastAPI.

This dependency gathers a variety of information into a single object for the
convenience of writing request handlers.  It also provides a place to store a
`structlog.BoundLogger` that can gather additional context during processing,
including from dependencies.
"""

from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, Request
from safir.dependencies.logger import logger_dependency
from safir.metrics import EventManager
from structlog.stdlib import BoundLogger

from ..events import Events
from ..factory import Factory
from .labeled_butler_factory import labeled_butler_factory_dependency

__all__ = [
    "ContextDependency",
    "RequestContext",
    "context_dependency",
]


@dataclass(slots=True)
class RequestContext:
    """Holds the incoming request and its surrounding context.

    The primary reason for the existence of this class is to allow the
    functions involved in request processing to repeated rebind the request
    logger to include more information, without having to pass both the
    request and the logger separately to every function.
    """

    request: Request
    """The incoming request."""

    logger: BoundLogger
    """The request logger, rebound with discovered context."""

    factory: Factory
    """The component factory."""

    events: Events
    """Events publisher."""

    def rebind_logger(self, **values: Any) -> None:
        """Add the given values to the logging context.

        Parameters
        ----------
        **values
            Additional values that should be added to the logging context.
        """
        self.logger = self.logger.bind(**values)
        self.factory.set_logger(self.logger)


class ContextDependency:
    """Provide a per-request context as a FastAPI dependency.

    Each request gets a `RequestContext`.  To save overhead, the portions of
    the context that are shared by all requests are collected into the single
    process-global `~sia.factory.ProcessContext` and reused with each
    request.
    """

    def __init__(self) -> None:
        self._events: Events | None = None

    async def __call__(
        self,
        *,
        request: Request,
        logger: Annotated[BoundLogger, Depends(logger_dependency)],
    ) -> RequestContext:
        """Create a per-request context and return it."""
        if not self._events:
            raise RuntimeError("ContextDependency not initialized")
        factory = Factory(
            logger=logger,
            labeled_butler_factory=await labeled_butler_factory_dependency(),
        )
        return RequestContext(
            request=request,
            logger=logger,
            factory=factory,
            events=self._events,
        )

    async def initialize(self, event_manager: EventManager) -> None:
        """Initialize the process-wide shared context.

        Parameters
        ----------
        event_manager
            Global event manager.
        """
        self._events = Events()
        await self._events.initialize(event_manager)


context_dependency = ContextDependency()
"""The dependency that will return the per-request context."""
