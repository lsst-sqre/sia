"""VOTable exceptions and exception handler to format an error into a valid
VOTAble.
"""

import functools
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import ParamSpec, TypeVar

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.templating import Jinja2Templates

from .config import config

_TEMPLATES = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent / "templates")
)

logger = structlog.get_logger(config.name)

# Module may be slightly too long, in the future we may want to break it up


class VOTableError(HTTPException):
    """Exception for VOTable errors."""

    def __init__(
        self, detail: str = "Uknown error occured", status_code: int = 400
    ) -> None:
        super().__init__(detail=detail, status_code=status_code)

    def __str__(self) -> str:
        return f"{self.detail}"


class UsageFaultError(VOTableError):
    """Exception for invalid input.

    Attributes
    ----------
    detail : str
        The error message.
    status_code : int
        The status code for the exception
    """

    def __init__(
        self, detail: str = "Invalid input", status_code: int = 400
    ) -> None:
        self.detail = f"UsageFault: {detail}"
        self.status_code = status_code
        super().__init__(detail=self.detail, status_code=self.status_code)


class TransientFaultError(VOTableError):
    """Exception for service temporarily unavailable.

    Attributes
    ----------
    detail : str
        The error message.
    status_code : int
        The status code for the exception
    """

    def __init__(
        self,
        detail: str = "Service is not currently able to function",
        status_code: int = 400,
    ) -> None:
        self.detail = f"TransientFault: {detail}"
        self.status_code = status_code
        super().__init__(detail=self.detail, status_code=self.status_code)


class FatalFaultError(VOTableError):
    """Exception for service cannot perform requested action.

    Attributes
    ----------
    detail : str
        The error message.
    status_code : int
        The status code for the exception
    """

    def __init__(
        self,
        detail: str = "Service cannot perform requested action",
        status_code: int = 400,
    ) -> None:
        self.detail = f"FatalFault: {detail}"
        self.status_code = status_code
        super().__init__(detail=self.detail, status_code=self.status_code)


class DefaultFaultError(VOTableError):
    """General exception for errors not covered above.

    Attributes
    ----------
    detail : str
        The error message.
    status_code : int
        The status code for the exception
    """

    def __init__(
        self, detail: str = "General error", status_code: int = 400
    ) -> None:
        self.detail = f"DefaultFault: {detail}"
        self.status_code = status_code
        super().__init__(detail=self.detail, status_code=self.status_code)


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

    async def _extract_error_message(excpt: RequestValidationError) -> str:
        """Extract the error message from a RequestValidationError.

        Parameters
        ----------
        excpt
            The RequestValidationError to extract the error message from.

        """
        total_messages = []
        for error in excpt.errors():
            try:
                loc = error["loc"][1]
                msg = error.get("msg", "Validation error")
                input_value = error.get("input", None)
                message = f"Validation of '{loc}' failed: {msg}."
                if input_value:
                    message += f" Got: {input_value}."
            except IndexError:
                message = error["msg"]
            total_messages.append(message)
        return " ".join(total_messages)
        # We are returning the messages separated by a space in the INFO
        # element. This is not very readable for a user, but I think the spec
        # only allows a single INFO, so maybe there isn't a better way

    logger.error(
        "Error during query processing",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path,
        method=request.method,
    )

    if isinstance(exc, RequestValidationError):
        error_message = await _extract_error_message(exc)
        exc = UsageFaultError(detail=error_message)
    elif isinstance(exc, ValueError):
        error_message = str(exc)
        exc = UsageFaultError(detail=error_message)
    elif not isinstance(
        exc,
        UsageFaultError
        | TransientFaultError
        | FatalFaultError
        | DefaultFaultError,
    ):
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


def configure_exception_handlers(app: FastAPI) -> None:
    """Configure the exception handlers for the application.
    Handle by formatting as VOTable with the appropriate error message.

    Parameters
    ----------
    app
        The FastAPI application instance.
    """

    @app.exception_handler(VOTableError)
    @app.exception_handler(RequestValidationError)
    @app.exception_handler(Exception)
    async def custom_exception_handler(
        request: Request, exc: Exception
    ) -> Response:
        """Handle exceptions that should be returned as VOTable errors.

        Parameters
        ----------
        request
            The incoming request.
        exc
            The exception to handle.
        """
        return await votable_exception_handler(request, exc)


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
            stack_trace = "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            )
            logger.exception(
                "Error during query processing",
                error_type=type(exc).__name__,
                error_message=str(exc),
                stack_trace=stack_trace,
            )
            if isinstance(
                exc,
                UsageFaultError
                | TransientFaultError
                | FatalFaultError
                | DefaultFaultError,
            ):
                raise exc from exc

            if isinstance(exc, ValueError | RequestValidationError):
                raise UsageFaultError(detail=str(exc)) from exc
            raise DefaultFaultError(detail=str(exc)) from exc

    return wrapper
