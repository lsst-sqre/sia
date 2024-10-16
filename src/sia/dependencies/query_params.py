"""Provides functions to get instances of params."""

from typing import Annotated

from fastapi import Depends
from lsst.dax.obscore.siav2 import SIAv2Parameters

from ..models.sia_query_params import SIAFormParams, SIAQueryParams


def get_query_params(
    params: Annotated[SIAQueryParams, Depends(SIAQueryParams)],
) -> SIAv2Parameters:
    """Get the SIAv2Parameters from the query parameters.

    Parameters
    ----------
    params
        The query parameters.

    Returns
    -------
    SIAv2Parameters
        The SIAv2Parameters instance.
    """
    return params.to_butler_parameters()


def get_form_params(
    params: Annotated[SIAFormParams, Depends(SIAFormParams)],
) -> SIAv2Parameters:
    """Get the SIAv2Parameters from the form parameters.

    Parameters
    ----------
    params
        The form parameters.

    Returns
    -------
    SIAv2Parameters
        The SIAv2Parameters instance.
    """
    return params.to_butler_parameters()
