"""Component factory and process-wide status for sia."""

import structlog
from lsst.daf.butler import Butler, LabeledButlerFactory
from lsst.dax.obscore import ExporterConfig
from structlog.stdlib import BoundLogger

from .config import config
from .models.data_collections import ButlerDataCollection
from .services.data_collections import DataCollectionService

__all__ = ["Factory"]


class Factory:
    """Component factory for sia.

    Uses the contents of a `ProcessContext` to construct the components of an
    application on demand.

    Parameters
    ----------
    labeled_butler_factory
        The LabeledButlerFactory singleton
    obscore_configs
        The Obscore configurations
    logger
        The logger instance
    """

    def __init__(
        self,
        labeled_butler_factory: LabeledButlerFactory,
        obscore_configs: dict[str, ExporterConfig],
        logger: BoundLogger | None = None,
    ) -> None:
        self._labeled_butler_factory = labeled_butler_factory
        self._obscore_configs = obscore_configs
        self._logger = logger or structlog.get_logger(config.name)

    def create_butler(
        self,
        butler_collection: ButlerDataCollection,
        token: str,
    ) -> Butler:
        """Create a Butler instance.

        Parameters
        ----------
        butler_collection
            The Butler data collection.
        token
            The token to use for the Butler instance.

        Returns
        -------
        Butler
            The Butler instance.
        """
        return self._labeled_butler_factory.create_butler(
            label=butler_collection.label, access_token=token
        )

    def create_obscore_config(self, label: str) -> ExporterConfig:
        """Create an Obscore config object for a given label.

        Parameters
        ----------
        label
            The label for the Obscore config.

        Returns
        -------
        ExporterConfig
            The Obscore config.
        """
        return self._obscore_configs[label]

    def create_data_collection_service(self) -> DataCollectionService:
        """Create a data collection service.

        Returns
        -------
        DataCollectionService
            The data collection service.
        """
        return DataCollectionService()

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
