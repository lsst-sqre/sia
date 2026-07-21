"""Configuration definition."""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, HttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from safir.logging import LogLevel, Profile
from safir.metrics import MetricsConfiguration, metrics_configuration_factory

from .exceptions import FatalFaultError
from .models.data_collections import ButlerDataCollection

__all__ = ["Config", "config"]


class Config(BaseSettings):
    """Configuration for sia."""

    model_config = SettingsConfigDict(env_prefix="SIA_", case_sensitive=False)

    butler_data_collections: Annotated[
        list[ButlerDataCollection],
        Field(title="Data collections"),
    ]

    log_level: LogLevel = Field(
        LogLevel.INFO, title="Log level of the application's logger"
    )

    log_profile: Profile = Field(
        Profile.development, title="Application logging profile"
    )

    metrics: MetricsConfiguration = Field(
        default_factory=metrics_configuration_factory,
        title="Metrics configuration",
        description="Configuration for reporting metrics to Kafka",
    )

    name: str = Field("sia", title="Name of application")

    path_prefix: str = Field("/api/sia", title="URL prefix for application")

    slack_webhook: Annotated[
        HttpUrl | None, Field(title="Slack webhook for exception reporting")
    ] = None

    @model_validator(mode="after")
    def _validate_butler_data_collections(self) -> Self:
        """Validate the Butler data collections."""
        if len(self.butler_data_collections) == 0:
            raise FatalFaultError(
                detail="No Data Collections configured. Please configure "
                "at least one Data collection."
            )

        return self


config = Config()
"""Configuration instance for sia."""
