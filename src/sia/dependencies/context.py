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
from structlog.stdlib import BoundLogger

from ..config import Config
from ..factory import Factory, ProcessContext

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
        self._process_context: ProcessContext | None = None

    async def __call__(
        self,
        *,
        request: Request,
        logger: Annotated[BoundLogger, Depends(logger_dependency)],
    ) -> RequestContext:
        """Create a per-request context and return it."""
        if not self._config or not self._process_context:
            raise RuntimeError("ContextDependency not initialized")

        return RequestContext(
            request=request,
            config=self._config,
            logger=logger,
            factory=Factory(
                process_context=self._process_context, logger=logger
            ),
        )

    @property
    def process_context(self) -> ProcessContext:
        """The underlying process context, primarily for use in tests."""
        if not self._process_context:
            raise RuntimeError("ContextDependency not initialized")
        return self._process_context

    def create_factory(self, logger: BoundLogger) -> Factory:
        """Create a factory for use outside a request context."""
        return Factory(
            logger=logger,
            process_context=self.process_context,
        )

    async def aclose(self) -> None:
        """Clean up the per-process configuration."""
        if self._process_context:
            await self._process_context.aclose()
        self._config = None
        self._process_context = None

    async def initialize(
        self,
        config: Config,
    ) -> None:
        """Initialize the process-wide shared context.

        Parameters
        ----------
        config
            SIA configuration.
        """
        if self._process_context:
            await self._process_context.aclose()
        self._config = config
        self._process_context = await ProcessContext.create()


context_dependency = ContextDependency()
"""The dependency that will return the per-request context."""
