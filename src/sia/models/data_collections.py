"""Data collection models."""

import contextlib
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from lsst.daf.butler import ButlerConfig
from lsst.dax.obscore import ExporterConfig
from pydantic import Field, HttpUrl

from ..models.butler_type import ButlerType


@dataclass
class ButlerDataCollection:
    """Model to represent a Remote Butler data collection."""

    config: Annotated[
        HttpUrl | Path,
        Field(
            description="Config Path or URL to obscore config for collection",
            examples=[
                "https://example.com/butler-repo/path/to/local/dp02.yaml",
                "/path/to/local/butler/dp02.yaml",
            ],
        ),
    ]
    """The obscore configuration file for this data collection."""

    repository: Annotated[
        HttpUrl | Path,
        Field(
            description="Butler Repository Path or URL",
            examples=[
                "https://example.com/butler-repo/path/to/local/repository",
                "/path/to/local/butler/repository",
            ],
        ),
    ]
    """Butler Repository Path or URL"""

    label: Annotated[
        str,
        Field(
            description="The label for this Butler collection. Used to "
            "identify the collection in the case where we are "
            "using a Remote Butler",
            examples=["LSST.DP02"],
        ),
    ]
    """The label for this Butler collection"""

    name: Annotated[
        str,
        Field(
            description="The name for this Butler collection. This value is "
            "used to identify the collection in API URLs. "
            "For example, a name of 'dp02' would be used in the URL "
            "'/api/sia/dp02/query'.",
            examples=["dp02"],
        ),
    ]
    """The name for this Butler collection."""

    butler_type: Annotated[
        ButlerType,
        Field(
            description="The Butler type for this data collection.",
            examples=["REMOTE", "DIRECT"],
        ),
    ]
    """The Butler type for this data collection."""

    default_instrument: Annotated[
        str,
        Field(
            default=None,
            description="The default instrument for the data collection",
        ),
    ]
    """The default instrument for the data collection"""

    datalink_url: Annotated[
        HttpUrl | None,
        Field(
            default=None,
            description="An optional datalink URL to use instead of the one "
            "in the config. This will overwrite the value in the obscore "
            "configuration for the collection",
        ),
    ] = None
    """An optional datalink URL to use instead of the one in the config"""

    @property
    def identifier(self) -> str:
        """Get the identifier for the data collection.

        Returns
        -------
        str
            The identifier.
        """
        return f"{self.label}:{self.repository}"

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
