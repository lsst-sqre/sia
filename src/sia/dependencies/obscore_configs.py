"""Dependency class for loading the Obscore configs."""

import contextlib
from typing import Annotated
from urllib.parse import urlparse, urlunparse

from fastapi import Depends
from lsst.daf.butler import ButlerConfig
from lsst.dax.obscore import ExporterConfig
from rubin.repertoire import DiscoveryClient, discovery_dependency

from ..constants import DATALINK_VERSION
from ..models.data_collections import ButlerDataCollection
from .data_collections import validate_collection

__all__ = [
    "ObscoreConfigDependency",
    "datalink_url_dependency",
    "obscore_config_dependency",
]


async def datalink_url_dependency(
    collection: Annotated[ButlerDataCollection, Depends(validate_collection)],
    discovery: Annotated[DiscoveryClient, Depends(discovery_dependency)],
) -> str | None:
    """Determine the DataLink links URL for a collection.

    This is a separate dependency from `ObsCoreConfigDependency` because the
    latter cannot run async since it makes HTTP requests with a sync
    underlying library.
    """
    return await discovery.url_for_data(
        "datalink", collection.name, version=DATALINK_VERSION
    )


class ObscoreConfigDependency:
    """Retrieve ObsCore exporter configuration for a collection."""

    def __init__(self) -> None:
        self._cache: dict[str, ExporterConfig] = {}
        self._datalink_urls: dict[str, str | None] = {}

    def __call__(
        self,
        datalink_url: Annotated[str | None, Depends(datalink_url_dependency)],
        collection: Annotated[
            ButlerDataCollection, Depends(validate_collection)
        ],
    ) -> ExporterConfig:
        """Get the ObsCore exporter configuration for a collection."""
        name = collection.name
        exporter_config = self._cache.get(name)
        if exporter_config and self._datalink_urls.get(name) == datalink_url:
            return exporter_config

        # Fetch the ObsCore configuration and create the appropriate model.
        config_data = ButlerConfig(str(collection.config))
        exporter_config = ExporterConfig.model_validate(config_data)

        # We normally should find the datalink_url_fmt attribute for each
        # dataset type. If it doesn't exist this doesn't seem to be a critical
        # issue so we suppress the AttributeError. Otherwise, preserve its
        # query arguments, but replace the rest of the URL with the URL from
        # service discovery.
        if datalink_url:
            new_url = urlparse(datalink_url)
            new_netloc = new_url.hostname or ""
            if new_url.port:
                new_netloc = f"{new_netloc}:{new_url.port}"
            for settings in exporter_config.dataset_types.values():
                with contextlib.suppress(AttributeError):
                    old_url = urlparse(str(settings.datalink_url_fmt))
                    merged_url = old_url._replace(
                        scheme=new_url.scheme,
                        netloc=new_netloc,
                        path=new_url.path,
                    )
                    settings.datalink_url_fmt = urlunparse(merged_url)

        # Update the cache and return the results.
        self._cache[name] = exporter_config
        self._datalink_urls[name] = datalink_url
        return exporter_config


obscore_config_dependency = ObscoreConfigDependency()
"""Return the ObsCore exporter config for a given collection."""
