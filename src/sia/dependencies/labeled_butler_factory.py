"""Dependency class for creating a LabeledButlerFactory singleton."""

from lsst.daf.butler import LabeledButlerFactory
from rubin.repertoire import DiscoveryClient

from ..config import config
from ..exceptions import FatalFaultError


class LabeledButlerFactoryDependency:
    """Provides a remote butler factory as a dependency."""

    def __init__(self) -> None:
        self._discovery = DiscoveryClient()
        self._repositories: dict[str, str] = {}
        self._butler_factory: LabeledButlerFactory | None = None

    async def __call__(self) -> LabeledButlerFactory:
        return await self._build_butler_factory()

    async def get_butler_url(self, name: str) -> str | None:
        """Return the Butler URL for a given collection name.

        This is used by the availability checker to get a Butler URL that can
        be probed to see if the Butler server is running.

        Parameters
        ----------
        name
            Name of the collection.

        Returns
        -------
        str or None
            URL of the Butler configuration for that collection or `None` if
            the collection is unknown.
        """
        await self._build_butler_factory()
        return self._repositories.get(name)

    async def _build_butler_factory(self) -> LabeledButlerFactory:
        """Get a labeled Butler factory.

        Returns the cached Butler factory if it exists and service discovery
        information has not changed. Otherwise, recreates the labeled Butler
        factory with current discovery information.
        """
        repositories = await self._discovery.butler_repositories()
        if self._butler_factory and repositories == self._repositories:
            return self._butler_factory
        for collection in config.butler_data_collections:
            if collection.name not in repositories:
                msg = f"No Butler configuration found for {collection.name}"
                raise FatalFaultError(msg)
        self._butler_factory = LabeledButlerFactory(repositories)
        self._repositories = repositories
        return self._butler_factory


labeled_butler_factory_dependency = LabeledButlerFactoryDependency()
"""The dependency that will return the LabeledButlerFactoryDependency."""
