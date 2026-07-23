"""Handlers for the app's external root, ``/api/sia/``."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.templating import Jinja2Templates
from lsst.daf.butler import Butler
from lsst.dax.obscore import ExporterConfig
from lsst.dax.obscore.siav2 import siav2_query
from safir.dependencies.gafaelfawr import auth_dependency
from safir.dependencies.logger import logger_dependency
from safir.metadata import get_metadata
from safir.models import ErrorModel
from structlog.stdlib import BoundLogger
from vo_models.vosi.availability import Availability
from vo_models.vosi.capabilities.models import VOSICapabilities

from ..config import config
from ..dependencies.butler import butler_dependency
from ..dependencies.context import RequestContext, context_dependency
from ..dependencies.data_collections import validate_collection
from ..dependencies.obscore_configs import obscore_config_dependency
from ..dependencies.query_params import get_sia_params_dependency
from ..models.data_collections import ButlerDataCollection
from ..models.index import Index
from ..models.sia_query_params import SIAQueryParams
from ..services.availability import AvailabilityService
from ..services.response_handler import ResponseHandlerService

BASE_DIR = Path(__file__).resolve().parent.parent
_TEMPLATES = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))

__all__ = ["external_router", "get_index"]

external_router = APIRouter()
"""FastAPI router for all external handlers."""


@external_router.get(
    "/",
    description=(
        "Document the top-level API here. By default it only returns metadata"
        " about the application."
    ),
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
    response_model=Availability,
    description="VOSI-availability resource for the service",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/xml": {
                    "example": """<?xml version="1.0" encoding="UTF-8"?>
<availability xmlns="http://www.ivoa.net/xml/VOSIAvailability/v1.0">
    <available>true</available>
</availability>""",
                    "schema": Availability.model_json_schema(),
                },
                "application/json": None,
            },
        }
    },
    summary="IVOA service availability",
)
async def get_availability(
    collection: Annotated[ButlerDataCollection, Depends(validate_collection)],
) -> Response:
    availability = await AvailabilityService(
        collection=collection
    ).get_availability()
    xml = availability.to_xml(skip_empty=True)
    return Response(content=xml, media_type="application/xml")


@external_router.get(
    "/{collection_name}/capabilities",
    description="VOSI-capabilities resource for the SIA service.",
    response_model=VOSICapabilities,
    responses={
        200: {
            "content": {
                "application/xml": {
                    "example": """<?xml version="1.0"?>
    <capabilities
        xmlns="http://www.ivoa.net/xml/VOSICapabilities/v1.0"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:vod="http://www.ivoa.net/xml/VODataService/v1.1">
       <capability standardID="ivo://ivoa.net/std/SIA#query-2.0">
         <interface xsi:type="vod:ParamHTTP" role="std" version="2.0">
             <accessURL>https://example.com/query</accessURL>
         </interface>
       </capability>
    </capabilities>""",
                    "schema": VOSICapabilities.model_json_schema(),
                }
            }
        }
    },
    summary="IVOA service capabilities",
)
async def get_capabilities(
    collection: Annotated[ButlerDataCollection, Depends(validate_collection)],
    request: Request,
) -> Response:
    return _TEMPLATES.TemplateResponse(
        request,
        "capabilities.xml",
        {
            "request": request,
            "availability_url": request.url_for(
                "get_availability", collection_name=collection.name
            ),
            "capabilities_url": request.url_for(
                "get_capabilities", collection_name=collection.name
            ),
            "query_url": request.url_for(
                "query", collection_name=collection.name
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
async def query(
    *,
    context: Annotated[RequestContext, Depends(context_dependency)],
    butler: Annotated[Butler, Depends(butler_dependency)],
    obscore_config: Annotated[
        ExporterConfig, Depends(obscore_config_dependency)
    ],
    collection: Annotated[ButlerDataCollection, Depends(validate_collection)],
    raw_params: Annotated[SIAQueryParams, Depends(get_sia_params_dependency)],
    user: Annotated[str, Depends(auth_dependency)],
) -> Response:
    return await ResponseHandlerService.process_query(
        butler=butler,
        raw_params=raw_params,
        sia_query=siav2_query,
        collection=collection,
        events=context.events,
        user=user,
        request=context.request,
        obscore_config=obscore_config,
    )
