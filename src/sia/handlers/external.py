"""Handlers for the app's external root, ``/api/sia/``."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from lsst.dax.obscore.siav2 import siav2_query
from safir.dependencies.logger import logger_dependency
from safir.metadata import get_metadata
from safir.models import ErrorModel
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response
from structlog.stdlib import BoundLogger
from vo_models.vosi.availability import Availability

from ..config import config
from ..dependencies.availability import get_availability_dependency
from ..dependencies.context import RequestContext, context_dependency
from ..dependencies.query_params import sia_post_params_dependency
from ..dependencies.token import optional_auth_delegated_token_dependency
from ..exceptions import handle_exceptions
from ..models.index import Index
from ..models.sia_query_params import SIAQueryParams
from ..services.response_handler import ResponseHandlerService
from ..timer import timer

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
    "/availability",
    description="VOSI-availability resource for the service",
    responses={200: {"content": {"application/xml": {}}}},
    summary="IVOA service availability",
)
async def get_availability(
    availability: Annotated[
        Availability, Depends(get_availability_dependency)
    ],
) -> Response:
    """Endpoint which provides the VOSI-availability resource, which indicates
    whether the service is currently available, returned as an XML document.

    Parameters
    ----------
    availability
        The system availability as dependency

    Returns
    -------
    Response
        The response containing the VOSI-availability XML document.

    ## GET /api/sia/availability

    **Example XML Response**:
    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <availability xmlns="http://www.ivoa.net/xml/VOSIAvailability/v1.0">
        <available>true</available>
    </availability>
    ```
    """
    xml = availability.to_xml(skip_empty=True)
    return Response(content=xml, media_type="application/xml")


@external_router.get(
    "/capabilities",
    description="VOSI-capabilities resource for the SIA service.",
    responses={200: {"content": {"application/xml": {}}}},
    summary="IVOA service capabilities",
)
async def get_capabilities(
    request: Request,
) -> Response:
    """Endpoint which provides the VOSI-capabilities resource, which lists the
    capabilities of the SIA service, as an XML document (VOSI-capabilities).

    Parameters
    ----------
    request
        The request object.
    logger
        The logger instance.

    Returns
    -------
    Response
        The response containing the VOSI-capabilities XML document.

    ## GET /api/sia/capabilities

    **Example XML Response**:
    ```xml
    <?xml version="1.0"?>
    <capabilities
        xmlns:vosi="http://www.ivoa.net/xml/VOSICapabilities/v1.0"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:vod="http://www.ivoa.net/xml/VODataService/v1.1">
       <capability standardID="ivo://ivoa.net/std/SIA#query-2.0">
         <interface xsi:type="vod:ParamHTTP" role="std" version="2.0">
             <accessURL>{{ query_url }}</accessURL>
         </interface>
       </capability>
    </capabilities>
    ```
    """
    return _TEMPLATES.TemplateResponse(
        request,
        "capabilities.xml",
        {
            "request": request,
            "availability_url": request.url_for("get_availability"),
            "capabilities_url": request.url_for("get_capabilities"),
            "query_url": request.url_for("query_get"),
        },
        media_type="application/xml",
    )


@external_router.get(
    "/query",
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
@timer
@handle_exceptions
def query_get(
    context: Annotated[RequestContext, Depends(context_dependency)],
    params: Annotated[SIAQueryParams, Depends()],
    delegated_token: Annotated[
        str | None, Depends(optional_auth_delegated_token_dependency)
    ],
) -> Response:
    """Endpoint used to query the SIA service using various
    parameters defined in the SIA spec via a GET request.
    The response is an XML VOTable file that adheres the Obscore model.

    Parameters
    ----------
    context
        The RequestContext object
    delegated_token
        The delegated token. (Optional)
    params
        The parameters for the SIA query.

    Returns
    -------
    Response
        The response containing the query results.

    Examples
    --------
    ### GET /api/sia/query
    ```
    /api/sia/query?POS=CIRCLE+321+0+1&BAND=700e-9&FORMAT=votable
    ```

    Notes
    -----
    We don't include any parameter validation here because the siav2_query
    from the dax_obscore already does this so we didn't want to duplicate.
    The siav2_query will raise a ValueError if the parameters are invalid.

    See Also
    --------
    SIA Specification: http://www.ivoa.net/documents/SIA/
    ObsCore Data Model: http://www.ivoa.net/documents/ObsCore/
    """
    return ResponseHandlerService.process_query(
        factory=context.factory,
        params=params,
        token=delegated_token,
        sia_query=siav2_query,
        request=context.request,
    )


@handle_exceptions
@external_router.post(
    "/query",
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
async def query_post(
    *,
    context: Annotated[RequestContext, Depends(context_dependency)],
    params: Annotated[SIAQueryParams, Depends(sia_post_params_dependency)],
    delegated_token: Annotated[
        str | None, Depends(optional_auth_delegated_token_dependency)
    ],
) -> Response:
    """Endpoint used to query the SIA service using various
    parameters defined in the SIA spec via a POST request.
    The response is an XML VOTable file that adheres the Obscore model.

    Parameters
    ----------
    context
        The RequestContext object
    delegated_token
        The delegated token. (Optional)
    params
        The parameters for the SIA query.


    Returns
    -------
    Response
        The response containing the query results.

    Examples
    --------
    ### POST /api/sia/query
    ```
    POST /api/sia/query
    Content-Type: application/json

    {
        "POS": "CIRCLE 321 0 1",
        "BAND": "700e-9",
        "FORMAT": "votable"
    }
    ```

    See Also
    --------
    SIA Specification: http://www.ivoa.net/documents/SIA/
    ObsCore Data Model: http://www.ivoa.net/documents/ObsCore/
    """
    return await run_in_threadpool(
        ResponseHandlerService.process_query,
        params=params,
        factory=context.factory,
        token=delegated_token,
        sia_query=siav2_query,
        request=context.request,
    )
