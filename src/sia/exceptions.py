"""VOTable exceptions and exception handler to format an error into a valid
VOTAble.
"""

from pathlib import Path

from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates

_TEMPLATES = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent / "templates")
)


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
    detail
        The error message.
    status_code
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
    detail
        The error message.
    status_code
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
    detail
        The error message.
    status_code
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
    detail
        The error message.
    status_code
        The status code for the exception
    """

    def __init__(
        self, detail: str = "General error", status_code: int = 400
    ) -> None:
        self.detail = f"DefaultFault: {detail}"
        self.status_code = status_code
        super().__init__(detail=self.detail, status_code=self.status_code)
