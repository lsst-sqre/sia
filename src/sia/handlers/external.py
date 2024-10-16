"""Handlers for the app's external root, ``/api/sia/``."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from lsst.dax.obscore.siav2 import SIAv2Parameters, siav2_query
from safir.dependencies.logger import logger_dependency
from safir.metadata import get_metadata
from safir.models import ErrorModel
from starlette.responses import Response
from structlog.stdlib import BoundLogger

from ..config import config
from ..dependencies.context import RequestContext, context_dependency
from ..dependencies.data_collections import validate_collection
from ..dependencies.query_params import get_form_params, get_query_params
from ..dependencies.token import optional_auth_delegated_token_dependency
from ..models.data_collections import ButlerDataCollection
from ..models.index import Index
from ..services.availability import AvailabilityService
from ..services.data_collections import DataCollectionService
from ..services.response_handler import ResponseHandlerService

BASE_DIR = Path(__file__).resolve().parent.parent
_TEMPLATES = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))

__all__ = ["get_index", "external_router"]

external_router = APIRouter()
"""FastAPI router for all external handlers."""


@external_router.get(
    "/",
    description=(
        "Document the top-level API here. By default it only returns metadata"
        " about the application."
    ),
    response_model=Index,
    response_model_exclude_none=True,
    summary="Application metadata",
)
async def get_index(
    logger: Annotated[BoundLogger, Depends(logger_dependency)],
) -> Index:
    """GET ``/api/sia/`` (the app's external root).

    Customize this handler to return whatever the top-level resource of your
    application should return. For example, consider listing key API URLs.
    When doing so, also change or customize the response model in
    `sia.models.Index`.

    By convention, the root of the external API includes a field called
    ``metadata`` that provides the same Safir-generated metadata as the
    internal root endpoint.
    """
    # There is no need to log simple requests since uvicorn will do this
    # automatically, but this is included as an example of how to use the
    # logger for more complex logging.
    logger.info("Request for application metadata")

    metadata = get_metadata(
        package_name="sia",
        application_name=config.name,
    )
    return Index(metadata=metadata)


@external_router.get(
    "/{collection_name}/availability",
    description="VOSI-availability resource for the service",
    responses={200: {"content": {"application/xml": {}}}},
    summary="IVOA service availability",
)
async def get_availability(collection_name: str) -> Response:
    # Get the butler data collection
    collection = DataCollectionService(
        config=config
    ).get_data_collection_by_name(name=collection_name)

    # Check if it is available
    availability = await AvailabilityService(
        collection=collection
    ).get_availability()

    xml = availability.to_xml(skip_empty=True)
    return Response(content=xml, media_type="application/xml")


@external_router.get(
    "/{collection_name}/capabilities",
    description="VOSI-capabilities resource for the SIA service.",
    responses={200: {"content": {"application/xml": {}}}},
    summary="IVOA service capabilities",
)
async def get_capabilities(
    collection_name: str,
    request: Request,
) -> Response:
    return _TEMPLATES.TemplateResponse(
        request,
        "capabilities.xml",
        {
            "request": request,
            "availability_url": request.url_for(
                "get_availability", collection_name=collection_name
            ),
            "capabilities_url": request.url_for(
                "get_capabilities", collection_name=collection_name
            ),
            "query_url": request.url_for(
                "query_get", collection_name=collection_name
            ),
        },
        media_type="application/xml",
    )


@external_router.get(
    "/{collection_name}/query",
    description="Query endpoint for the SIA service.",
    responses={
        200: {"content": {"application/xml": {}}},
        400: {
            "description": "Invalid query parameters",
            "model": ErrorModel,
        },
    },
    summary="IVOA SIA service query",
)
def query_get(
    *,
    context: Annotated[RequestContext, Depends(context_dependency)],
    collection: Annotated[ButlerDataCollection, Depends(validate_collection)],
    params: Annotated[SIAv2Parameters, Depends(get_query_params)],
    delegated_token: Annotated[
        str | None, Depends(optional_auth_delegated_token_dependency)
    ],
) -> Response:
    return ResponseHandlerService.process_query(
        factory=context.factory,
        params=params,
        token=delegated_token,
        sia_query=siav2_query,
        collection=collection,
        request=context.request,
    )


@external_router.post(
    "/{collection_name}/query",
    description="Query endpoint for the SIA service (POST method).",
    responses={
        200: {"content": {"application/xml": {}}},
        400: {
            "description": "Invalid query parameters",
            "model": ErrorModel,
        },
    },
    summary="IVOA SIA (v2) service query (POST)",
)
def query_post(
    *,
    context: Annotated[RequestContext, Depends(context_dependency)],
    collection: Annotated[ButlerDataCollection, Depends(validate_collection)],
    params: Annotated[SIAv2Parameters, Depends(get_form_params)],
    delegated_token: Annotated[
        str | None, Depends(optional_auth_delegated_token_dependency)
    ],
) -> Response:
    return ResponseHandlerService.process_query(
        factory=context.factory,
        params=params,
        token=delegated_token,
        sia_query=siav2_query,
        collection=collection,
        request=context.request,
    )
