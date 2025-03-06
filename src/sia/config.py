"""Configuration definition."""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, HttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from safir.logging import LogLevel, Profile
from safir.metrics import MetricsConfiguration, metrics_configuration_factory

from .models.data_collections import ButlerDataCollection

__all__ = ["Config", "config"]


class Config(BaseSettings):
    """Configuration for sia."""

    name: str = Field("sia", title="Name of application")
    """Name of application."""

    path_prefix: str = Field("/api/sia", title="URL prefix for application")
    """URL prefix for application."""

    profile: Profile = Field(
        Profile.development, title="Application logging profile"
    )
    """Application logging profile."""

    log_level: LogLevel = Field(
        LogLevel.INFO, title="Log level of the application's logger"
    )
    """Log level of the application's logger."""

    metrics: MetricsConfiguration = Field(
        default_factory=metrics_configuration_factory,
        title="Metrics configuration",
        description="Configuration for reporting metrics to Kafka",
    )
    """Configuration for reporting metrics to Kafka."""

    model_config = SettingsConfigDict(env_prefix="SIA_", case_sensitive=False)
    """Configuration for the model settings."""

    butler_data_collections: Annotated[
        list[ButlerDataCollection],
        Field(title="Data collections"),
    ]
    """Configuration for the data collections."""

    environment_name: Annotated[
        str,
        Field(
            alias="SIA_ENVIRONMENT_NAME",
            description=(
                "The Phalanx name of the Rubin Science Platform environment."
            ),
        ),
    ]
    """The environment name in Phalanx."""

    slack_webhook: Annotated[
        HttpUrl | None, Field(title="Slack webhook for exception reporting")
    ] = None
    """Slack webhook for exception reporting."""

    sentry_dsn: Annotated[
        str | None,
        Field(
            alias="SIA_SENTRY_DSN",
            description="DSN for sending events to Sentry.",
        ),
    ] = None
    """DSN for sending events to Sentry."""

    sentry_traces_sample_rate: Annotated[
        float,
        Field(
            alias="SIA_SENTRY_TRACES_SAMPLE_RATE",
            description=(
                "The percentage of transactions to send to Sentry, expressed "
                "as a float between 0 and 1. 0 means send no traces, 1 means "
                "send every trace."
            ),
            ge=0,
            le=1,
        ),
    ] = 0
    """The percentage of transactions to send to Sentry."""

    @model_validator(mode="after")
    def _validate_butler_data_collections(self) -> Self:
        """Validate the Butler data collections."""
        from .exceptions import FatalFaultError

        if len(self.butler_data_collections) == 0:
            raise FatalFaultError(
                detail="No Data Collections configured. Please configure "
                "at least one Data collection."
            )

        return self


config = Config()
"""Configuration instance for sia."""
