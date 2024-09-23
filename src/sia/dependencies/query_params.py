"""Provides functions to get instances of ParamFactory."""

from collections import defaultdict

from fastapi import Request

from ..constants import SINGLE_PARAMS
from ..models.sia_query_params import SIAQueryParams


async def sia_post_params_dependency(
    *,
    request: Request,
) -> SIAQueryParams:
    """Dependency to parse the POST parameters for the SIA query.

    Parameters
    ----------
    request
        The request object.

    Returns
    -------
    SIAQueryParams
        The parameters for the SIA query.

    Raises
    ------
    ValueError
        If the method is not POST.
    """
    if request.method != "POST":
        raise ValueError("sia_post_params_dependency used for non-POST route")
    content_type = request.headers.get("Content-Type", "")
    params_dict: dict[str, list[str]] = defaultdict(list)

    # Handle JSON Content-Type
    # This isn't required by the SIA spec, but it may be useful for
    # deugging, for future expansion the spec and for demonstration purposes.
    if "application/json" in content_type:
        json_data = await request.json()
        for key, value in json_data.items():
            lower_key = key.lower()
            if isinstance(value, list):
                params_dict[lower_key].extend(str(v) for v in value)
            else:
                params_dict[lower_key].append(str(value))

    else:  # Assume form data
        form_data = await request.form()
        for key, value in form_data.multi_items():
            if not isinstance(value, str):
                raise TypeError("File upload not supported")
            lower_key = key.lower()
            params_dict[lower_key].append(value)

    converted_params_dict = {}
    for key, value in params_dict.items():
        if key in SINGLE_PARAMS:
            converted_params_dict[key] = value[0]
        else:
            converted_params_dict[key] = value

    return SIAQueryParams.from_dict(converted_params_dict)
