"""Provides functions to get instances of QueryEngineFactory and
ParamFactory.
"""

from collections import defaultdict

from fastapi import Request

from ..config import config
from ..constants import SINGLE_PARAMS
from ..factories.param_factory import ParamFactory
from ..factories.query_engine_factory import QueryEngineFactory
from ..models import SIAv2QueryParams


def get_query_engine_factory() -> QueryEngineFactory:
    """Return a QueryEngineFactory instance."""
    return QueryEngineFactory(config)


def get_param_factory() -> ParamFactory:
    """Return a ParamFactory instance."""
    return ParamFactory(config)


async def siav2_post_params_dependency(
    request: Request,
) -> SIAv2QueryParams:
    """Dependency to parse the POST parameters for the SIAv2 query.

    Parameters
    ----------
    request
        The request object.

    Returns
    -------
    SIAv2QueryParams
        The parameters for the SIAv2 query.

    Raises
    ------
    ValueError
        If the method is not POST.
    """
    if request.method != "POST":
        raise ValueError(
            "siav2_post_params_dependency used for non-POST route"
        )
    content_type = request.headers.get("Content-Type", "")
    params_dict: dict[str, list[str]] = defaultdict(list)

    # Handle JSON Content-Type
    # This isn't required by the SIAv2 spec, but it may be useful for
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

    return SIAv2QueryParams.from_dict(converted_params_dict)
