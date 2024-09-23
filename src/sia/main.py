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

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from safir.dependencies.http_client import http_client_dependency
from safir.logging import configure_logging, configure_uvicorn_logging
from safir.middleware.x_forwarded import XForwardedMiddleware
from safir.slack.webhook import SlackRouteErrorHandler
from structlog import get_logger

from .config import config
from .dependencies.context import context_dependency
from .dependencies.labeled_butler_factory import (
    labeled_butler_factory_dependency,
)
from .exceptions import configure_exception_handlers
from .handlers.external import external_router
from .handlers.internal import internal_router
from .middleware.ivoa import CaseInsensitiveQueryAndBodyMiddleware
from .models.butler_type import ButlerType

__all__ = ["app"]


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Set up and tear down the application."""
    logger.debug("SIA has started up.")
    if config.butler_type is ButlerType.REMOTE:
        await labeled_butler_factory_dependency.initialize(config=config)
    await context_dependency.initialize(config=config)

    yield

    if config.butler_type is ButlerType.REMOTE:
        await labeled_butler_factory_dependency.close()

    await context_dependency.aclose()
    logger.debug("SIA shut down complete.")
    await http_client_dependency.aclose()


configure_logging(
    profile=config.profile,
    log_level=config.log_level,
    name="sia",
)
configure_uvicorn_logging(config.log_level)

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

# Address case-sensitivity issue with IVOA query parameters
app.add_middleware(CaseInsensitiveQueryAndBodyMiddleware)

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
