"""Component factory and process-wide status for sia."""

import structlog
from structlog.stdlib import BoundLogger

from .config import config

__all__ = ["Factory"]


class Factory:
    """Component factory for sia.

    Uses the contents of a `ProcessContext` to construct the components of an
    application on demand.

    Parameters
    ----------
    logger
        The logger instance
    """

    def __init__(self, logger: BoundLogger | None = None) -> None:
        self._logger = logger or structlog.get_logger(config.name)

    def set_logger(self, logger: BoundLogger) -> None:
        """Replace the internal logger.

        Used by the context dependency to update the logger for all
        newly-created components when it's rebound with additional context.

        Parameters
        ----------
        logger
            New logger.
        """
        self._logger = logger
