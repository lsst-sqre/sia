"""Data collection dependencies."""

from ..config import config
from ..exceptions import UsageFaultError
from ..models.data_collections import ButlerDataCollection


def validate_collection(collection_name: str) -> ButlerDataCollection:
    """Validate the collection name and return the Butler data collection.

    Parameters
    ----------
    collection_name
        Name of the collection.

    Returns
    -------
    ButlerDataCollection
        Metadata for the Butler data collection.

    Raises
    ------
    UsageFaultError
        Raised if the collection is not found.
    """
    if collection_name not in config.datasets:
        raise UsageFaultError(f"Collection '{collection_name}' not found", 404)
    obscore_config = config.obscore_config[collection_name]
    return ButlerDataCollection(config=obscore_config, name=collection_name)
