"""Sentry integration helpers."""

from __future__ import annotations

import re
from collections.abc import Callable
from re import Pattern
from typing import Any

from safir.sentry import before_send_handler

from .config import config

__all__ = ["enable_sentry", "make_traces_sampler"]


def enable_sentry() -> None:
    """Enable Sentry telemetry."""
    try:
        import sentry_sdk
    except ImportError:
        return

    sampler = make_traces_sampler(
        original_rate=config.sentry_traces_sample_rate,
        exclude_patterns=["/", re.compile(r"^/healthcheck(/.*)?$")],
    )

    sentry_sdk.init(
        dsn=config.sentry_dsn,
        environment=config.environment_name,
        before_send=before_send_handler,
        traces_sampler=sampler,
    )


def make_traces_sampler(
    original_rate: float,
    exclude_patterns: list[str | Pattern] | None = None,
) -> Callable[[dict[str, Any]], float]:
    """Create a traces sampler that excludes certain paths from sampling.

    This function creates a sampler that will return 0.0 (no sampling) for
    paths that match any of the provided patterns, and the original sample
    rate for all other paths.

    Parameters
    ----------
    original_rate
        The original sample rate.
    exclude_patterns
        A list of patterns to exclude from sampling. (string or compiled
        regex)

    Returns
    -------
    Callable[[dict[str, Any]], float]
        The traces sampler.

    """
    if exclude_patterns is None:
        exclude_patterns = []

    def traces_sampler(context: dict[str, Any]) -> float:
        """Determine the sample rate for a transaction.

        Parameters
        ----------
        context
            The Sentry context.

        Returns
        -------
        float
            The sample rate.
        """
        asgi_scope = context.get("asgi_scope")
        if not asgi_scope:
            return original_rate

        path = asgi_scope.get("path", "")

        for pattern in exclude_patterns:
            if isinstance(pattern, Pattern):
                if pattern.match(path):
                    return 0.0
            elif path == pattern:
                return 0.0

        return original_rate

    return traces_sampler
