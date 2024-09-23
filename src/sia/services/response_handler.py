"""Module for the Query Processor service."""

from collections.abc import Callable
from datetime import UTC, datetime

import astropy
import structlog
from fastapi import Request
from lsst.daf.butler import Butler
from lsst.dax.obscore import ExporterConfig
from lsst.dax.obscore.siav2 import SIAv2Parameters
from starlette.responses import Response

from ..constants import RESULT_NAME as RESULT
from ..factory import Factory
from ..models.sia_query_params import SIAQueryParams
from ..services.votable import VotableConverterService

logger = structlog.get_logger(__name__)

SIAv2QueryType = Callable[
    [Butler, ExporterConfig, SIAv2Parameters],
    astropy.io.votable.tree.VOTableFile,
]


class ResponseHandlerService:
    """Service for handling the SIAv2 query response."""

    @staticmethod
    def process_query(
        *,
        factory: Factory,
        params: SIAQueryParams,
        sia_query: SIAv2QueryType,
        request: Request,
        token: str | None,
    ) -> Response:
        """Process the SIAv2 query and generate a Response.

        Parameters
        ----------
        factory
            The Factory instance.
        params
            The parameters for the SIAv2 query.
        sia_query
            The SIA query method to use
        request
            The request object.
        token
            The token to use for the Butler (Optional).

        Returns
        -------
        Response
            The response containing the query results.
        """
        logger.info(
            "SIA query started with params:",
            params=params,
            method=request.method,
            time=datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
        )
        data_collection_service = factory.create_data_collection_service()

        # Get the Butler collection configuration.
        # If many collections are provided, for now just look for the
        # default one. This needs to be updated to handle multiple collections.
        collection = (
            data_collection_service.get_data_collection(
                label=params.collection[0],
            )
            if params.collection is not None and len(params.collection) > 0
            else data_collection_service.get_default_collection()
        )

        butler = factory.create_butler(
            butler_collection=collection,
            token=token,
            config_path=str(collection.config),
        )

        # Execute the query
        table_as_votable = sia_query(
            butler,
            collection.exporter_config,
            params.to_butler_parameters(),
        )

        # Convert the result to a string
        result = VotableConverterService(table_as_votable).to_string()

        # For the moment only VOTable is supported, so we can hardcode the
        # media_type and the file extension.
        return Response(
            headers={
                "content-disposition": f"attachment; filename={RESULT}.xml",
                "Content-Type": "application/x-votable+xml",
            },
            content=result,
            media_type="application/x-votable+xml",
        )
