"""Module for the Query Processor service."""

import asyncio
import time
import uuid
from collections.abc import Callable
from pathlib import Path

import astropy
import structlog
from fastapi import Request
from fastapi.templating import Jinja2Templates
from lsst.daf.butler import Butler
from lsst.dax.obscore import ExporterConfig
from safir.sentry import duration
from starlette.responses import Response

from ..constants import BASE_RESOURCE_IDENTIFIER
from ..constants import RESULT_NAME as RESULT
from ..events import Events, SIAQueryFailed, SIAQuerySucceeded
from ..factory import Factory
from ..models.data_collections import ButlerDataCollection
from ..models.sia_query_params import BandInfo, SIAQueryParams
from ..sentry import capturing_start_span
from ..services.votable import VotableConverterService

logger = structlog.get_logger(__name__)

SIAv2QueryType = Callable[..., astropy.io.votable.tree.VOTableFile]

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
    def _get_dataproduct_subtypes(
        obscore_config: ExporterConfig,
    ) -> list[str]:
        """Extract unique dataproduct subtypes from dataset types.

        Parameters
        ----------
        obscore_config
            The ExporterConfig object containing dataset types.

        Returns
        -------
        list[str]
            The list of unique dataproduct subtypes.
        """
        subtypes = {
            config.dataproduct_subtype
            for config in obscore_config.dataset_types.values()
            if config.dataproduct_subtype is not None
        }
        return list(subtypes)

    @staticmethod
    async def self_description_response(
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

        dataproduct_subtypes = (
            ResponseHandlerService._get_dataproduct_subtypes(obscore_config)
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
                "dataproduct_subtypes": dataproduct_subtypes,
            },
            headers={
                "content-disposition": f"attachment; filename={RESULT}.xml",
                "Content-Type": "application/x-votable+xml",
            },
            media_type="application/x-votable+xml",
        )

    @staticmethod
    async def process_query(
        *,
        factory: Factory,
        raw_params: SIAQueryParams,
        sia_query: SIAv2QueryType,
        request: Request,
        collection: ButlerDataCollection,
        events: Events,
        user: str,
        token: str | None,
    ) -> Response:
        """Process the SIAv2 query and generate a Response.

        Parameters
        ----------
        factory
            The Factory instance.
        raw_params
            The parameters for the SIAv2 query.
        sia_query
            The SIA query method to use
        request
            The request object.
        collection
            The Butler data collection
        events
            Object with attributes for all metrics event publishers.
        user
            The username.
        token
            The token to use for the Butler (Optional).

        Returns
        -------
        Response
            The response containing the query results.
        """
        start_time = time.time()
        query_id = str(uuid.uuid4())[:8]

        query_string = raw_params.to_query_description()
        params = raw_params.to_butler_parameters()

        logger.info(
            "SIA query started with params:",
            params=params,
            method=request.method,
        )

        loop = asyncio.get_running_loop()

        # Run Butler creation in a thread pool
        butler = await loop.run_in_executor(
            None,
            lambda: factory.create_butler(
                butler_collection=collection,
                token=token,
            ),
        )
        obscore_config = factory.create_obscore_config(collection.label)

        if params.maxrec == 0:
            logger.info(
                "Returning self-description response (maxrec=0)",
                user=user,
                query_id=query_id,
            )
            return await ResponseHandlerService.self_description_response(
                request=request,
                butler=butler,
                obscore_config=obscore_config,
                butler_collection=collection,
            )

        with capturing_start_span("sia_query") as span:
            span.set_data("query", params)
            span.set_data("query_id", query_id)
            span.set_data("user", user)

            try:
                query_start_time = time.time()
                logger.info(
                    "Starting SIA query execution",
                    user=user,
                    query_id=query_id,
                )

                query_url = str(request.url)

                # Execute the query
                table_as_votable = await loop.run_in_executor(
                    None,
                    lambda: sia_query(
                        butler,
                        obscore_config,
                        params,
                        query_url=query_url,
                        query_string=query_string,
                    ),
                )

                query_duration = time.time() - query_start_time
                logger.info(
                    "SIA query execution completed",
                    query_duration_seconds=round(query_duration, 3),
                    user=user,
                    query_id=query_id,
                )

                # Publish success event
                await events.sia_query_succeeded.publish(
                    SIAQuerySucceeded(duration=duration(span), username=user)
                )
            except Exception as e:
                query_duration = time.time() - query_start_time
                logger.info(
                    "SIA query execution failed",
                    error=str(e),
                    query_duration_seconds=round(query_duration, 3),
                    user=user,
                    query_id=query_id,
                )
                # Publish failed event
                await events.sia_query_failed.publish(
                    SIAQueryFailed(
                        error=str(e),
                        duration=duration(span),
                        username=user,
                    )
                )
                raise

            conversion_start_time = time.time()
            # Convert the result to a string
            result = await loop.run_in_executor(
                None,
                lambda: VotableConverterService(table_as_votable).to_bytes(),
            )

            conversion_duration = time.time() - conversion_start_time

        total_duration = time.time() - start_time
        logger.info(
            "SIA query processing completed successfully",
            total_duration_seconds=round(total_duration, 3),
            query_duration_seconds=round(query_duration, 3),
            conversion_duration_seconds=round(conversion_duration, 3),
            user=user,
            query_id=query_id,
        )

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
