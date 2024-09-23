"""The main application factory for the vo-siav2 service.

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

import structlog
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from safir.dependencies.http_client import http_client_dependency
from safir.logging import configure_logging, configure_uvicorn_logging
from safir.middleware.x_forwarded import XForwardedMiddleware
from safir.slack.webhook import SlackRouteErrorHandler

from .config import config
from .exceptions import configure_exception_handlers
from .handlers.external import external_router
from .handlers.internal import internal_router
from .middleware.ivoa import CaseInsensitiveQueryMiddleware

__all__ = ["app"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Set up and tear down the application."""
    # Any code here will be run when the application starts up.

    yield

    # Any code here will be run when the application shuts down.
    await http_client_dependency.aclose()


configure_logging(
    profile=config.profile,
    log_level=config.log_level,
    name="vosiav2",
)
configure_uvicorn_logging(config.log_level)

app = FastAPI(
    title="vo-siav2",
    description=metadata("vo-siav2")["Summary"],
    version=version("vo-siav2"),
    openapi_url=f"{config.path_prefix}/openapi.json",
    docs_url=f"{config.path_prefix}/docs",
    redoc_url=f"{config.path_prefix}/redoc",
    lifespan=lifespan,
)
"""The main FastAPI application for vo-siav2."""

# Address case-sensitivity issue with IVOA query parameters
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
    logger = structlog.get_logger(__name__)
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
