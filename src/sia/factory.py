"""Component factory and process-wide status for mobu."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from lsst.daf.butler.registry import RegistryDefaults
from structlog.stdlib import BoundLogger

from .config import Config, config

__all__ = ["Factory", "ProcessContext"]

import structlog
from lsst.daf.butler import Butler, LabeledButlerFactory

from .dependencies.labeled_butler_factory import (
    labeled_butler_factory_dependency,
)
from .exceptions import FatalFaultError
from .models.butler_type import ButlerType
from .models.data_collections import ButlerDataCollection
from .services.data_collections import DataCollectionService


@dataclass(frozen=True, slots=True)
class ProcessContext:
    """Per-process application context.

    This object caches all of the per-process singletons that can be reused
    for every request.
    """

    config: Config
    """SIA's configuration."""

    labeled_butler_factory: LabeledButlerFactory | None
    """The Labeled Butler factory."""

    @classmethod
    async def create(cls) -> Self:
        labeled_butler_factory = (
            await labeled_butler_factory_dependency()
            if config.butler_type is ButlerType.REMOTE
            else None
        )
        return cls(
            config=config, labeled_butler_factory=labeled_butler_factory
        )

    async def aclose(self) -> None:
        """Close any resources held by the context."""


class Factory:
    """Component factory for sia.

    Uses the contents of a `ProcessContext` to construct the components of an
    application on demand.

    Parameters
    ----------
    process_context
        Shared process context.
    """

    def __init__(
        self,
        process_context: ProcessContext,
        logger: BoundLogger | None = None,
    ) -> None:
        self._process_context = process_context
        self._logger = logger if logger else structlog.get_logger("mobu")

    def create_butler(
        self,
        config_path: str,
        butler_collection: ButlerDataCollection,
        token: str | None = None,
    ) -> Butler:
        """Create a Butler instance.

        Parameters
        ----------
        config_path
            The path to the Butler configuration.
        butler_collection
            The Butler data collection.
        token
            The token to use for the Butler instance.

        Returns
        -------
        Butler
            The Butler instance.
        """
        app_config = self._process_context.config
        if not config_path:
            raise ValueError(
                "No Butler configuration file configured <butler_config>"
            )

        if app_config.butler_type is ButlerType.DIRECT:
            if not butler_collection.repository:
                raise ValueError(
                    "No Butler repository configured <butler_repo>"
                )

            butler = Butler.from_config(
                str(butler_collection.repository), writeable=False
            )
        else:
            if not butler_collection.label:
                raise FatalFaultError(
                    detail="No Butler label configured <label>"
                )
            if not token:
                raise FatalFaultError(
                    detail="Token is required for RemoteButlerQueryEngine"
                )

            if not self._process_context.labeled_butler_factory:
                raise FatalFaultError(
                    detail="No LabeledButlerFactory configured"
                )

            butler = (
                self._process_context.labeled_butler_factory.create_butler(
                    label=butler_collection.label, access_token=token
                )
            )

            # TODO (stvoutsin): Temporary workaround for DP02
            butler.registry.defaults = RegistryDefaults(
                instrument=butler_collection.defaultinstrument
            )

        return butler

    def create_data_collection_service(self) -> DataCollectionService:
        """Create a data collection service.

        Returns
        -------
        DataCollectionService
            The data collection service.
        """
        return DataCollectionService(
            config=self._process_context.config,
        )

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
