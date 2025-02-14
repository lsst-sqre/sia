"""Sentry integration helpers."""

from __future__ import annotations

import re
from collections.abc import Callable, Generator
from contextlib import contextmanager
from re import Pattern
from typing import Any

import sentry_sdk
from safir.sentry import before_send_handler
from sentry_sdk.tracing import Span

from .config import config

__all__ = ["capturing_start_span", "enable_sentry", "make_traces_sampler"]


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


@contextmanager
def capturing_start_span(op: str, **kwargs: Any) -> Generator[Span]:
    """Start a span, set the op/start time in the context, and capture errors.

    Setting the op and start time in the context will propagate it to any error
    events that get sent to Sentry, event if the trace does not get sent.

    Explicitly capturing errors in the span will tie the Sentry events to this
    specific span, rather than tying them to the span/transaction where they
    would be handled otherwise.
    """
    with sentry_sdk.start_span(op=op, **kwargs) as span:
        sentry_sdk.get_isolation_scope().set_context(
            "phase", {"phase": op, "started_at": span.start_timestamp}
        )
        sentry_sdk.get_isolation_scope().set_tag("phase", op)

        # You can't see the time a span started in the Sentry UI, only the time
        # the entire transaction started
        span.set_tag("started_at", span.start_timestamp)

        try:
            yield span
        except Exception as e:
            # Even though we're capturing exceptions at the business level,
            # Sentry knows not to send them twice.
            sentry_sdk.capture_exception(e)
            raise
        finally:
            sentry_sdk.get_isolation_scope().remove_context("phase")
            sentry_sdk.get_isolation_scope().remove_tag("phase")
