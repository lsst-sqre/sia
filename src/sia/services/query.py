"""Run an SIA query and return the results as a VOTable."""

import asyncio
import time
import uuid
from collections.abc import Callable

import astropy
from lsst.daf.butler import Butler
from lsst.dax.obscore import ExporterConfig
from safir.sentry import duration
from structlog.stdlib import BoundLogger

from ..events import Events, SIAQueryFailed, SIAQuerySucceeded
from ..models.sia_query_params import SIAQueryParams
from ..sentry import capturing_start_span
from ..services.votable import VotableConverterService

SIAv2QueryType = Callable[..., astropy.io.votable.tree.VOTableFile]

__all__ = ["QueryService"]


class QueryService:
    """Run an SIA query and return the results as a VOTable.

    Parameters
    ----------
    butler
        Butler for this data collection.
    obscore_config
        ObsCore exporter configuration for this data collection.
    events
        Metrics events publishers.
    logger
        Logger to use.
    """

    def __init__(
        self,
        *,
        butler: Butler,
        obscore_config: ExporterConfig,
        events: Events,
        logger: BoundLogger,
    ) -> None:
        self._butler = butler
        self._obscore_config = obscore_config
        self._events = events
        self._logger = logger

    async def run_query(
        self,
        *,
        raw_params: SIAQueryParams,
        sia_query: SIAv2QueryType,
        query_url: str,
        user: str,
    ) -> bytes:
        """Process the SIAv2 query and generate a Response.

        Parameters
        ----------
        raw_params
            Parameters for the SIAv2 query.
        sia_query
            The SIA query method to use.
        query_url
            URL the user sent the query to, which has to be reflected in the
            VOTable output.
        user
            Authenticated username for metrics events.

        Returns
        -------
        bytes
            Resulting VOTable.
        """
        start_time = time.time()
        query_id = str(uuid.uuid4())[:8]

        query_string = raw_params.to_query_description()
        params = raw_params.to_butler_parameters()

        logger = self._logger.bind(query_id=query_id, user=user)
        logger.info("SIA query started", params=params)

        loop = asyncio.get_running_loop()

        with capturing_start_span("sia_query") as span:
            span.set_data("query", params)
            span.set_data("query_id", query_id)
            span.set_data("user", user)

            try:
                query_start_time = time.time()
                logger.info("Starting SIA query execution")

                # Execute the query
                table_as_votable = await loop.run_in_executor(
                    None,
                    lambda: sia_query(
                        self._butler,
                        self._obscore_config,
                        params,
                        query_url=query_url,
                        query_string=query_string,
                    ),
                )

                query_duration = time.time() - query_start_time
                logger.info(
                    "SIA query execution completed",
                    query_duration_seconds=round(query_duration, 3),
                )

                # Publish success event
                await self._events.sia_query_succeeded.publish(
                    SIAQuerySucceeded(duration=duration(span), username=user)
                )
            except Exception as e:
                query_duration = time.time() - query_start_time
                logger.info(
                    "SIA query execution failed",
                    error=str(e),
                    query_duration_seconds=round(query_duration, 3),
                )
                # Publish failed event
                await self._events.sia_query_failed.publish(
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
        )
        return result
