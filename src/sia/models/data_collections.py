"""Data collection models."""

import contextlib
from dataclasses import dataclass
from pathlib import Path

from lsst.daf.butler import ButlerConfig
from lsst.dax.obscore import ExporterConfig
from pydantic import HttpUrl


@dataclass
class ButlerDataCollection:
    """Model to represent a Remote Butler data collection."""

    config: HttpUrl | Path
    repository: HttpUrl | Path
    label: str
    defaultinstrument: str
    default: bool = False
    datalinkurl: HttpUrl | None = None

    def get_identifier(self) -> str:
        """Get the identifier for the data collection.

        Returns
        -------
        str
            The identifier.
        """
        return f"{self.label}:{self.repository}"

    @property
    def exporter_config(self) -> ExporterConfig:
        """Get the exporter configuration.

        Returns
        -------
        ExporterConfig
            The exporter configuration.
        """
        config_data = ButlerConfig(str(self.config))
        exporter_config = ExporterConfig.model_validate(config_data)
        # Overwrite datalink format if provided
        for name in exporter_config.dataset_types:
            with contextlib.suppress(AttributeError):
                # We normally should find the datalink_url_fmt attribute
                # If it doesn't exist this doesn't seem to be a critical issue
                # so we suppress the AttributeError
                exporter_config.dataset_types[name].datalink_url_fmt = str(
                    self.datalinkurl
                )
        return exporter_config
