"""Dependency class for creating Butler instances."""

from typing import Annotated

from fastapi import Depends
from lsst.daf.butler import LabeledButlerFactory
from rubin.repertoire import DiscoveryClient, discovery_dependency
from safir.dependencies.gafaelfawr import auth_logger_dependency
from safir.dependencies.http_client import http_client_dependency
from safir.dependencies.logger import logger_dependency
from structlog.stdlib import BoundLogger

from ..exceptions import UsageFaultError

__all__ = [
    "ButlerFactoryDependency",
    "butler_factory_dependency",
]


class ButlerFactoryDependency:
    """Provides a labeled Butler factory as a dependency.

    This factory will be configured with the labels that SIA knows about. It
    is normally used via `butler_factory_dependency`.
    """

    def __init__(self) -> None:
        self._repositories: dict[str, str] = {}
        self._butler_factory: LabeledButlerFactory | None = None

    async def __call__(
        self,
        discovery: Annotated[DiscoveryClient, Depends(discovery_dependency)],
        logger: Annotated[BoundLogger, Depends(auth_logger_dependency)],
    ) -> LabeledButlerFactory:
        return await self._build_butler_factory(discovery, logger)

    async def butler_url(
        self,
        collection_name: str,
        discovery: Annotated[DiscoveryClient, Depends(discovery_dependency)],
        logger: Annotated[BoundLogger, Depends(logger_dependency)],
    ) -> str:
        """Return the Butler URL for a given collection name.

        This is used by the availability checker as a FastAPI dependency to
        get a Butler URL that can be probed to see if the Butler server is
        running. Availability is accessible to unauthenticated users, so this
        method and its dependencies must not require Gafaelfawr
        authentication.

        Parameters
        ----------
        collection_name
            Name of the collection.
        discovery
            Service discovery client.

        Returns
        -------
        str
            URL of the Butler configuration for that collection.

        Raises
        ------
        UsageFaultError
            Raised if the collection was not found in service discovery.
        """
        await self._build_butler_factory(discovery, logger)
        if collection_name not in self._repositories:
            msg = f"Collection '{collection_name}' not found"
            raise UsageFaultError(msg, 404)
        return self._repositories[collection_name]

    async def initialize(self, logger: BoundLogger) -> None:
        """Pre-cache a labeled Butler factory.

        Called during application startup so that basic problems with
        mismatches between Butler discovery information and the local
        configuration will be caught early.

        Parameters
        ----------
        logger
            Logger to use.
        """
        http_client = await http_client_dependency()
        discovery = await discovery_dependency(http_client)
        await self._build_butler_factory(discovery, logger)

    async def _build_butler_factory(
        self, discovery: DiscoveryClient, logger: BoundLogger
    ) -> LabeledButlerFactory:
        """Get a labeled Butler factory.

        Returns the cached Butler factory if it exists and service discovery
        information has not changed. Otherwise, recreates the labeled Butler
        factory with current discovery information.
        """
        repositories = await discovery.butler_repositories()
        if self._butler_factory and repositories == self._repositories:
            return self._butler_factory
        self._butler_factory = LabeledButlerFactory(repositories)
        self._repositories = repositories
        return self._butler_factory


butler_factory_dependency = ButlerFactoryDependency()
"""Dependency that returns a Butler factory that knows about dataset labels."""
