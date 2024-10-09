"""Utility functions for timing function execution."""

import time
from collections.abc import Callable
from datetime import timedelta
from functools import wraps
from typing import Any, TypeVar

import structlog

from .config import config

logger = structlog.get_logger(config.name)


def format_timedelta(td: timedelta) -> str:
    """Format a timedelta object as a human-readable string.

    Parameters
    ----------
    td
        The timedelta object to format.

    Returns
    -------
    str
        The formatted timedelta.
    """
    total_seconds = td.total_seconds()
    if total_seconds < 0.001:
        return f"{total_seconds*1000000:.2f} µs"
    elif total_seconds < 1:
        return f"{total_seconds*1000:.2f} ms"
    elif total_seconds < 60:
        return f"{total_seconds:.2f} s"
    elif total_seconds < 3600:
        minutes, seconds = divmod(total_seconds, 60)
        return f"{int(minutes)}m {seconds:.2f}s"
    else:
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}h {int(minutes)}m {seconds:.2f}s"


T = TypeVar("T")


def timer(func: Callable[..., T]) -> Callable[..., T]:
    """Wrap a method and log its execution duration."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        """Log the duration of a function execution."""
        start_time = time.monotonic()
        result = func(*args, **kwargs)
        end_time = time.monotonic()
        duration = timedelta(seconds=end_time - start_time)
        formatted_time = format_timedelta(duration)
        logger.info(
            f"Function '{func.__name__}' executed", duration=formatted_time
        )
        return result

    return wrapper
