"""Sentry integration helpers."""

import re
from collections.abc import Callable, Generator
from contextlib import contextmanager
from re import Pattern
from typing import Any

import sentry_sdk
from safir.sentry import (
    SentryConfig,
    before_send_handler,
    should_enable_sentry,
)
from sentry_sdk.tracing import Span
from sentry_sdk.types import Event

__all__ = ["capturing_start_span", "enable_sentry"]


def _before_send_filter(event: Event, hint: dict[str, Any]) -> Event | None:
    """Filter out ValueError errors from Sentry events."""
    if "exc_info" in hint:
        exc_type, _, _ = hint["exc_info"]
        if exc_type is ValueError or exc_type.__name__ == "UsageFaultError":
            return None

    if event.get("level") == "error":
        extra_data = event.get("extra", {})
        if extra_data.get("error_type") == "UsageFaultError":
            return None

        logentry = event.get("logentry")
        if logentry is not None:
            message = logentry.get("message", "")
            if isinstance(message, str) and "UsageFaultError" in message:
                return None

    return before_send_handler(event, hint)


def _make_traces_sampler(
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
    typing.Callable
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


def enable_sentry(release: str) -> None:
    """Enable Sentry telemetry.

    Ideally this would use `safir.sentry.initialize_sentry` directly, but it
    doesn't currently have support for overriding the ``before_send``
    parameter or excluding routes from trace samplers.

    Parameters
    ----------
    release
        The version of this application that should be sent with every Sentry
        event. For most Safir applications, you should pass the value in
        ``<package>.__version__``.
    """
    if not should_enable_sentry():
        return

    config = SentryConfig()
    sampler = _make_traces_sampler(
        original_rate=config.traces_sample_rate,
        exclude_patterns=["/", re.compile(r"^/healthcheck(/.*)?$")],
    )
    sentry_sdk.init(
        dsn=config.dsn,
        environment=config.environment,
        before_send=_before_send_filter,
        traces_sampler=sampler,
    )


@contextmanager
def capturing_start_span(op: str, **kwargs: Any) -> Generator[Span]:
    """Start a span, set the start time in the context and capture errors."""
    with sentry_sdk.start_span(op=op, **kwargs) as span:
        context = {"phase": op, "started_at": span.start_timestamp}
        sentry_sdk.get_isolation_scope().set_context("phase", context)
        sentry_sdk.get_isolation_scope().set_tag("phase", op)

        span.set_tag("started_at", span.start_timestamp)

        try:
            yield span
        except ValueError:
            # Don't capture ValueError exceptions - just re-raise them
            raise
        except Exception as e:
            if type(e).__name__ == "UsageFaultError":
                raise
            sentry_sdk.capture_exception(e)
            raise
        finally:
            sentry_sdk.get_isolation_scope().remove_context("phase")
            sentry_sdk.get_isolation_scope().remove_tag("phase")
