"""Module for the Query Processor service."""

from collections.abc import Callable

import astropy
import structlog
from fastapi import Request
from lsst.daf.butler import Butler
from lsst.dax.obscore import ExporterConfig
from lsst.dax.obscore.siav2 import SIAv2Parameters
from starlette.responses import Response

from ..constants import RESULT_NAME as RESULT
from ..factory import Factory
from ..models.data_collections import ButlerDataCollection
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
        params: SIAv2Parameters,
        sia_query: SIAv2QueryType,
        request: Request,
        collection: ButlerDataCollection,
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
        collection
            The Butler data collection
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
        )

        butler = factory.create_butler(
            butler_collection=collection,
            token=token,
        )

        # Execute the query
        table_as_votable = sia_query(
            butler,
            collection.get_exporter_config(),
            params,
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
