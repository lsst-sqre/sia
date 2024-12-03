"""The main application factory for the sia service.

Notes
-----
Be aware that, following the normal pattern for FastAPI services, the app is
constructed when this module is loaded and is not deferred until a function is
called.
"""

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import metadata, version

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from safir.dependencies.http_client import http_client_dependency
from safir.logging import configure_logging, configure_uvicorn_logging
from safir.middleware.ivoa import CaseInsensitiveQueryMiddleware
from safir.middleware.x_forwarded import XForwardedMiddleware
from safir.slack.webhook import SlackRouteErrorHandler
from structlog import get_logger

from .config import config
from .dependencies.context import context_dependency
from .dependencies.labeled_butler_factory import (
    labeled_butler_factory_dependency,
)
from .dependencies.obscore_configs import obscore_config_dependency
from .errors import votable_exception_handler
from .exceptions import VOTableError
from .handlers.external import external_router
from .handlers.internal import internal_router
from .middleware.ivoa import CaseInsensitiveFormMiddleware
from .telemetry import enable_telemetry

__all__ = ["app"]


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Set up and tear down the application."""
    logger.debug("SIA has started up.")
    await labeled_butler_factory_dependency.initialize(config=config)
    await obscore_config_dependency.initialize(config=config)
    await context_dependency.initialize(config=config)

    yield

    await labeled_butler_factory_dependency.aclose()
    await obscore_config_dependency.aclose()
    await context_dependency.aclose()
    await http_client_dependency.aclose()
    logger.debug("SIA shut down complete.")


configure_logging(
    profile=config.profile,
    log_level=config.log_level,
    name="sia",
)
configure_uvicorn_logging(config.log_level)
enable_telemetry()

app = FastAPI(
    title="sia",
    description=metadata("sia")["Summary"],
    version=version("sia"),
    openapi_url=f"{config.path_prefix}/openapi.json",
    docs_url=f"{config.path_prefix}/docs",
    redoc_url=f"{config.path_prefix}/redoc",
    lifespan=lifespan,
)
"""The main FastAPI application for sia."""


def configure_exception_handlers(app: FastAPI) -> None:
    """Configure the exception handlers for the application.
    Handle by formatting as VOTable with the appropriate error message.

    Parameters
    ----------
    app
        The FastAPI application instance.
    """

    @app.exception_handler(VOTableError)
    @app.exception_handler(RequestValidationError)
    async def custom_exception_handler(
        request: Request, exc: Exception
    ) -> Response:
        """Handle exceptions that should be returned as VOTable errors.

        Parameters
        ----------
        request
            The incoming request.
        exc
            The exception to handle.
        """
        return await votable_exception_handler(request, exc)


# Address case-sensitivity issue with IVOA query parameters
app.add_middleware(CaseInsensitiveFormMiddleware)
app.add_middleware(CaseInsensitiveQueryMiddleware)

# Configure exception handlers.
configure_exception_handlers(app)

# Attach the routers.
app.include_router(internal_router)
app.include_router(external_router, prefix=f"{config.path_prefix}")

# Add middleware.
app.add_middleware(XForwardedMiddleware)


# Configure Slack alerts.
if config.slack_webhook:
    webhook = str(config.slack_webhook)
    SlackRouteErrorHandler.initialize(webhook, config.name, logger)
    logger.debug("Initialized Slack webhook")


def create_openapi() -> str:
    """Create the OpenAPI spec for static documentation."""
    spec = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    return json.dumps(spec)
