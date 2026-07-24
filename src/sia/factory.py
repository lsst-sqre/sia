"""Component factory for SIA."""

from lsst.daf.butler import Butler
from lsst.dax.obscore import ExporterConfig
from structlog.stdlib import BoundLogger

from .events import Events
from .services.description import SelfDescriptionService
from .services.query import QueryService

__all__ = ["Factory"]


class Factory:
    """Component factory for SIA.

    This factory is specific to a particular Butler data collection. The label
    of that collection is determined from the path parameters to an SIA
    handler and used to build an appropriate factory in the SIA FastAPI
    context dependency.

    Parameters
    ----------
    butler
        Remote Butler client for the relevant collection.
    obscore_config
        ObsCore exporter configuration for the relevant collection.
    events
        Events publishers.
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

    def create_query_service(self) -> QueryService:
        """Create the service that executes SIA queries.

        Returns
        -------
        QueryService
            Newly-created service.
        """
        return QueryService(
            butler=self._butler,
            obscore_config=self._obscore_config,
            events=self._events,
            logger=self._logger,
        )

    def create_self_description_service(self) -> SelfDescriptionService:
        """Create the service to generate SIA self-descriptions.

        Returns
        -------
        SelfDescriptionService
            Newly-created service.
        """
        return SelfDescriptionService(self._butler, self._obscore_config)

    def set_logger(self, logger: BoundLogger) -> None:
        """Replace the internal logger.

        Used by the context dependency to update the logger for all
        newly-created components when it's rebound with additional context.

        Parameters
        ----------
        logger
            New logger.
        """
        self._logger = logger
