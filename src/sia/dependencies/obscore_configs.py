"""Dependency class for loading the Obscore configs."""

from lsst.dax.obscore import ExporterConfig

from ..config import Config


class ObscoreConfigDependency:
    """Provides a mapping of label names to Obscore (Exporter) Configs as a
    dependency.
    """

    def __init__(self) -> None:
        self._config_mapping: dict[str, ExporterConfig] | None = None

    async def initialize(self, config: Config) -> None:
        """Initialize the dependency by processing the Butler Collections."""
        self._config_mapping = {}
        for collection in config.butler_data_collections:
            exporter_config = collection.get_exporter_config()
            self._config_mapping[collection.label] = exporter_config

    async def __call__(self) -> dict[str, ExporterConfig]:
        """Return the mapping of label names to ExporterConfigs."""
        if self._config_mapping is None:
            raise RuntimeError("ExporterConfigDependency is not initialized")
        return self._config_mapping

    async def aclose(self) -> None:
        """Clear the config mapping."""
        self._config_mapping = None


obscore_config_dependency = ObscoreConfigDependency()
"""The dependency that will return the mapping of label names to
Obscore Configs."""
