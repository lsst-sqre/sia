"""Dependency class for creating a LabeledButlerFactory singleton."""

from lsst.daf.butler import LabeledButlerFactory

from ..config import Config
from ..services.data_collections import DataCollectionService


class LabeledButlerFactoryDependency:
    """Provides a remote butler factory as a dependency."""

    def __init__(self) -> None:
        self._labeled_butler_factory: LabeledButlerFactory | None = None

    async def initialize(
        self,
        config: Config,
    ) -> None:
        """Initialize the dependency."""
        # Get the data repositories from the config in a format suitable for
        # the LabeledButlerFactory.
        data_repositories = DataCollectionService(
            config=config
        ).get_data_repositories()

        self._labeled_butler_factory = LabeledButlerFactory(
            repositories=data_repositories
        )

    async def __call__(self) -> LabeledButlerFactory:
        """Return the LabeledButlerFactory instance."""
        if self._labeled_butler_factory is None:
            raise RuntimeError(
                "LabeledButlerFactoryDependency is not initialized"
            )
        return self._labeled_butler_factory

    async def aclose(self) -> None:
        """Close in this case has no effect."""
        self._labeled_butler_factory = None


labeled_butler_factory_dependency = LabeledButlerFactoryDependency()
"""The dependency that will return the LabeledButlerFactoryDependency."""
