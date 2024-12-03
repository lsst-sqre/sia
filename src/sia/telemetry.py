"""Setup code for Sentry.io trace."""

from typing import Any


def enable_telemetry() -> None:
    """Turn on upload of trace telemetry to Sentry, to allow performance
    debugging of deployed server.
    """
    try:
        import sentry_sdk
    except ImportError:
        return

    # Configuration will be pulled from SENTRY_* environment variables
    # (see https://docs.sentry.io/platforms/python/configuration/options/).
    # If SENTRY_DSN is not present, telemetry is disabled.
    sentry_sdk.init(
        enable_tracing=True, traces_sampler=_decide_whether_to_sample_trace
    )


def _decide_whether_to_sample_trace(context: dict[str, Any]) -> float:
    asgi_scope = context.get("asgi_scope")
    if asgi_scope is not None:
        # Do not log health check endpoint.
        if asgi_scope.get("path") == "/":
            return 0

    return 1
