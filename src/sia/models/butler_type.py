"""Butler Type models."""

from ..models.common import CaseInsensitiveEnum


class ButlerType(str, CaseInsensitiveEnum):
    """Enumeration of possible butler types."""

    __slots__ = ()

    DIRECT = "DIRECT"
    REMOTE = "REMOTE"
