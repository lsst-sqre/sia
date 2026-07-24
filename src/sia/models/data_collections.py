"""Data collection models."""

import contextlib
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from lsst.daf.butler import ButlerConfig
from lsst.dax.obscore import ExporterConfig
from pydantic import Field, HttpUrl


@dataclass
class ButlerDataCollection:
    """Model to represent a Remote Butler data collection."""

    config: Annotated[
        HttpUrl | Path,
        Field(
            title="ObsCore configuration",
            description="Config path or URL to obscore config for collection",
            examples=[
                "https://example.com/butler-repo/path/to/local/dp02.yaml",
                "/path/to/local/butler/dp02.yaml",
            ],
        ),
    ]

    name: Annotated[
        str,
        Field(
            title="Name of Butler collection",
            description=(
                "The name for this Butler collection. This value is used to"
                " identify the collection in API URLs. For example, a name of"
                " 'dp02' would be used in the URL '/api/sia/dp02/query'."
            ),
            examples=["dp02"],
        ),
    ]

    datalink_url: Annotated[
        HttpUrl | None,
        Field(
            default=None,
            title="DataLink URL",
            description=(
                "An optional datalink URL to use instead of the one in the"
                " config. This will overwrite the value in the obscore"
                " configuration for the collection"
            ),
        ),
    ] = None

    def get_exporter_config(self) -> ExporterConfig:
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
                    self.datalink_url
                )
        return exporter_config
