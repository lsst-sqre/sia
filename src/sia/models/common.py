"""Common models used by in different places in the application."""

from enum import Enum
from typing import TypeVar

T = TypeVar("T", bound="CaseInsensitiveEnum")

__all__ = ["CaseInsensitiveEnum"]


class CaseInsensitiveEnum(Enum):
    """A case-insensitive Enum class.
    This class allows for case-insensitive comparisons of Enum values.
    """

    @classmethod
    def _missing_(cls: type[T], value: object) -> T | None:
        """Return the Enum member that matches the given value.

        Parameters
        ----------
        value
            The value to match.

        Returns
        -------
        Enum
            The Enum member that matches the given value.
        """
        if not isinstance(value, str):
            return None

        for member in cls:
            if member.value.lower() == value.lower():
                return member

        raise ValueError(f"{value!r} is not a valid {cls.__name__}")
