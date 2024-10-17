"""Provides functions to get instances of params."""

from collections import defaultdict
from typing import Annotated

from fastapi import Depends, Request
from lsst.dax.obscore.siav2 import SIAv2Parameters

from ..constants import SINGLE_PARAMS
from ..models.sia_query_params import SIAQueryParams


async def get_sia_params_dependency(
    *,
    params: Annotated[SIAQueryParams, Depends(SIAQueryParams)],
    request: Request,
) -> SIAv2Parameters:
    """Parse GET and POST parameters into SIAv2Parameters for SIA query."""
    # For POST requests, use form data
    if request.method == "POST":
        post_params_ddict: dict[str, list[str]] = defaultdict(list)

        for key, value in (await request.form()).multi_items():
            if not isinstance(value, str):
                raise TypeError("File upload not supported")
            post_params_ddict[key].append(value)

        post_params = {
            key: (values[0] if key in SINGLE_PARAMS and values else values)
            for key, values in post_params_ddict.items()
        }
        params = SIAQueryParams.from_dict(post_params)

    return params.to_butler_parameters()
