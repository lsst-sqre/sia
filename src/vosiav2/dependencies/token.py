"""FastAPI dependencies for handling tokens."""

from fastapi import Header


async def optional_auth_delegated_token_dependency(
    x_auth_request_token: str | None = Header(
        default=None, include_in_schema=False
    ),
) -> str | None:
    """Make auth_delegated_token_dependency optional.

    Parameters
    ----------
    x_auth_request_token : Optional[str]
        The delegated token.

    Returns
    -------
    Optional[str]
        The delegated token or None if it is not provided.
    """
    if x_auth_request_token is None:
        return None

    from safir.dependencies.gafaelfawr import auth_delegated_token_dependency

    return await auth_delegated_token_dependency(x_auth_request_token)
