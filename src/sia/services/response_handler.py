"""Module for the Query Processor service."""

from collections.abc import Callable
from pathlib import Path

import astropy
import structlog
from fastapi import Request
from fastapi.templating import Jinja2Templates
from lsst.daf.butler import Butler
from lsst.dax.obscore import ExporterConfig
from lsst.dax.obscore.siav2 import SIAv2Parameters
from starlette.responses import Response

from ..constants import BASE_RESOURCE_IDENTIFIER
from ..constants import RESULT_NAME as RESULT
from ..factory import Factory
from ..models.data_collections import ButlerDataCollection
from ..models.sia_query_params import BandInfo
from ..services.votable import VotableConverterService

logger = structlog.get_logger(__name__)

SIAv2QueryType = Callable[
    [Butler, ExporterConfig, SIAv2Parameters],
    astropy.io.votable.tree.VOTableFile,
]

BASE_DIR = Path(__file__).resolve().parent.parent
_TEMPLATES = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))


class ResponseHandlerService:
    """Service for handling the SIAv2 query response."""

    @staticmethod
    def _generate_band_info(
        spectral_ranges: dict[str, tuple[float | None, float | None]],
    ) -> list[BandInfo]:
        """Generate band information from spectral ranges dictionary.

        Parameters
        ----------
        spectral_ranges
            The spectral ranges dictionary.

        Returns
        -------
        list[BandInfo]
            The list of BandInfo objects.
        """
        bands = []
        for band_name, (low, high) in spectral_ranges.items():
            if low is not None and high is not None:
                # The Rubin label is hardcoded here, but it could be
                # parameterized if needed in the future.
                bands.append(
                    BandInfo(
                        label=f"Rubin band {band_name}", low=low, high=high
                    )
                )
        return bands

    @staticmethod
    def self_description_response(
        request: Request,
        butler: Butler,
        obscore_config: ExporterConfig,
        butler_collection: ButlerDataCollection,
    ) -> Response:
        """Return a self-description response for the SIAv2 service.
        This should provide metadata about the expected parameters and return
        values for the service.

        Parameters
        ----------
        request
            The request object.
        butler
            The Butler instance.
        obscore_config
            The ObsCore configuration.
        butler_collection
            The Butler data collection.

        Returns
        -------
        Response
            The response containing the self-description.
        """
        bands = ResponseHandlerService._generate_band_info(
            obscore_config.spectral_ranges
        )

        return _TEMPLATES.TemplateResponse(
            request,
            "self_description.xml",
            {
                "request": request,
                "instruments": [
                    rec.name
                    for rec in butler.query_dimension_records("instrument")
                ],
                "collections": [obscore_config.obs_collection],
                # This may need to be updated if we decide to change the
                # dax_obscore config to hold multiple collections
                "resource_identifier": f"{BASE_RESOURCE_IDENTIFIER}/"
                f"{butler_collection.label}",
                "access_url": request.url_for(
                    "query", collection_name=butler_collection.name
                ),
                "facility_name": obscore_config.facility_name.strip(),
                "bands": bands,
            },
            headers={
                "content-disposition": f"attachment; filename={RESULT}.xml",
                "Content-Type": "application/x-votable+xml",
            },
            media_type="application/x-votable+xml",
        )

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
        obscore_config = factory.create_obscore_config(collection.label)

        if params.maxrec == 0:
            return ResponseHandlerService.self_description_response(
                request=request,
                butler=butler,
                obscore_config=obscore_config,
                butler_collection=collection,
            )

        # Execute the query
        table_as_votable = sia_query(
            butler,
            obscore_config,
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
