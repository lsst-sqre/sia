"""Data collection dependencies."""

from typing import Annotated

from fastapi import Depends
from rubin.repertoire import DiscoveryClient, discovery_dependency

from ..exceptions import UsageFaultError
from ..models.data_collections import ButlerDataCollection
from .butler import butler_factory_dependency


async def validate_collection(
    collection_name: str,
    *,
    discovery: Annotated[DiscoveryClient, Depends(discovery_dependency)],
    butler_url: Annotated[str, Depends(butler_factory_dependency.butler_url)],
) -> ButlerDataCollection:
    """Validate the collection name and return the Butler data collection.

    Parameters
    ----------
    collection_name
        Name of the collection.
    discovery
        Service discovery client.
    butler_url
        URL to the Butler configuration. This is not used; it is present as
        a dependency to ensure that the collection is supported by Butler,
        since a 404 should be returned if it is not.

    Returns
    -------
    ButlerDataCollection
        Metadata for the Butler data collection.

    Raises
    ------
    UsageFaultError
        Raised if the collection is not found.
    """
    obscore_config = await discovery.obscore_config_for(collection_name)
    if not obscore_config:
        raise UsageFaultError(f"Collection '{collection_name}' not found", 404)
    return ButlerDataCollection(config=obscore_config, name=collection_name)
