"""Butler Type models."""

from ..models.common import CaseInsensitiveEnum


class ButlerType(CaseInsensitiveEnum):
    """Enumeration of possible butler types."""

    DIRECT = "DIRECT"
    REMOTE = "REMOTE"
