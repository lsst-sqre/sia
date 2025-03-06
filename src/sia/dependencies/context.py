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

from ..config import Config
from ..events import Events
from ..factory import Factory
from .labeled_butler_factory import labeled_butler_factory_dependency
from .obscore_configs import obscore_config_dependency

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

    config: Config
    """SIA's configuration."""

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
        self._config: Config | None = None
        self._events: Events | None = None

    async def __call__(
        self,
        *,
        request: Request,
        logger: Annotated[BoundLogger, Depends(logger_dependency)],
    ) -> RequestContext:
        """Create a per-request context and return it."""
        if not self._config or not self._events:
            raise RuntimeError("ContextDependency not initialized")

        return RequestContext(
            request=request,
            config=self._config,
            logger=logger,
            factory=await self.create_factory(logger=logger),
            events=self._events,
        )

    async def create_factory(self, logger: BoundLogger) -> Factory:
        """Create a factory for use outside a request context."""
        if not self._config:
            raise RuntimeError("ContextDependency not initialized")

        return Factory(
            logger=logger,
            config=self._config,
            labeled_butler_factory=await labeled_butler_factory_dependency(),
            obscore_configs=await obscore_config_dependency(),
        )

    async def aclose(self) -> None:
        """Clean up the per-process configuration."""
        self._config = None

    async def initialize(
        self, config: Config, event_manager: EventManager
    ) -> None:
        """Initialize the process-wide shared context.

        Parameters
        ----------
        config
            SIA configuration.
        event_manager
            Global event manager.
        """
        self._config = config
        self._events = Events()
        await self._events.initialize(event_manager)


context_dependency = ContextDependency()
"""The dependency that will return the per-request context."""
