"""Module for the Query Processor service."""

import asyncio
import time
import uuid
from collections.abc import Callable

import astropy
import structlog
from fastapi import Request, Response
from lsst.daf.butler import Butler
from lsst.dax.obscore import ExporterConfig
from safir.sentry import duration

from ..constants import RESULT_NAME as RESULT
from ..events import Events, SIAQueryFailed, SIAQuerySucceeded
from ..models.sia_query_params import SIAQueryParams
from ..sentry import capturing_start_span
from ..services.votable import VotableConverterService

logger = structlog.get_logger(__name__)

SIAv2QueryType = Callable[..., astropy.io.votable.tree.VOTableFile]


class ResponseHandlerService:
    """Service for handling the SIAv2 query response."""

    @staticmethod
    async def process_query(
        *,
        butler: Butler,
        raw_params: SIAQueryParams,
        sia_query: SIAv2QueryType,
        request: Request,
        events: Events,
        user: str,
        obscore_config: ExporterConfig,
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
        events
            Object with attributes for all metrics event publishers.
        user
            The username.
        obscore_config
            The ObsCore configuration.

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
