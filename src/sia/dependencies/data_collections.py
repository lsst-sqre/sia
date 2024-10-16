"""Data collection dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException

from ..dependencies.context import RequestContext, context_dependency
from ..models.data_collections import ButlerDataCollection


def validate_collection(
    collection_name: str,
    context: Annotated[RequestContext, Depends(context_dependency)],
) -> ButlerDataCollection:
    """Validate the collection name and return the Butler data collection.

    Parameters
    ----------
    collection_name
        The name of the collection.
    context
        The request context.

    Returns
    -------
    ButlerDataCollection
        The Butler data collection.

    Raises
    ------
    HTTPException
        If the collection is not found.
    """
    try:
        data_collection_service = (
            context.factory.create_data_collection_service()
        )
        return data_collection_service.get_data_collection_by_name(
            name=collection_name
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=f"Collection '{collection_name}' not found"
        ) from exc
