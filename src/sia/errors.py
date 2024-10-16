"""VOTable exception handler to format an error into a valid
VOTAble.
"""

import functools
from collections.abc import Callable
from pathlib import Path
from typing import ParamSpec, TypeVar

import structlog
from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates

from .config import config
from .exceptions import DefaultFaultError, UsageFaultError, VOTableError

_TEMPLATES = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent / "templates")
)

logger = structlog.get_logger(config.name)


async def votable_exception_handler(
    request: Request, exc: Exception
) -> Response:
    """Handle exceptions that should be returned as VOTable errors.
    Produces a VOTable error as a TemplateResponse with the error message.

    Parameters
    ----------
    request
        The incoming request.
    exc
        The exception to handle.

    Returns
    -------
    Response
        The VOTAble error response.
    """
    logger.error(
        "Error during query processing",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path,
        method=request.method,
    )

    if isinstance(exc, RequestValidationError):
        error_message = str(exc)
        exc = UsageFaultError(detail=error_message)
    elif not isinstance(exc, VOTableError):
        exc = DefaultFaultError(detail=str(exc))

    response = _TEMPLATES.TemplateResponse(
        request,
        "votable_error.xml",
        {
            "request": request,
            "error_message": str(exc),
        },
        media_type="application/xml",
    )
    response.status_code = 400
    return response


R = TypeVar("R")  # Return type
P = ParamSpec("P")  # Parameters


def handle_exceptions(func: Callable[P, R]) -> Callable[P, R]:
    """Handle exceptions in the decorated function by logging
    and then formatting as a VOTable.

    Parameters
    ----------
    func
        The function to decorate.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """Wrap function to handle its exceptions."""
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            logger.exception("An exception occurred during query processing")
            if isinstance(exc, VOTableError):
                raise exc from exc
            if isinstance(exc, RequestValidationError):
                raise UsageFaultError(detail=str(exc)) from exc
            raise exc from exc

    return wrapper
