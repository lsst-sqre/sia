"""Configuration definition."""

from typing import Annotated, Self

from pydantic import Field, HttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from safir.logging import LogLevel, Profile
from safir.metrics import MetricsConfiguration, metrics_configuration_factory

__all__ = ["Config", "config"]


class Config(BaseSettings):
    """Configuration for sia."""

    model_config = SettingsConfigDict(env_prefix="SIA_", case_sensitive=False)

    datasets: Annotated[
        list[str],
        Field(
            title="Supported datasets",
            description=(
                "Only queries against the listed datasets are supported"
            ),
            min_length=1,
        ),
    ]

    log_level: LogLevel = Field(
        LogLevel.INFO, title="Log level of the application's logger"
    )

    log_profile: Profile = Field(
        Profile.production, title="Application logging profile"
    )

    metrics: MetricsConfiguration = Field(
        default_factory=metrics_configuration_factory,
        title="Metrics configuration",
        description="Configuration for reporting metrics to Kafka",
    )

    name: str = Field("sia", title="Name of application")

    obscore_config: Annotated[
        dict[str, HttpUrl],
        Field(
            title="ObsCore confiugration",
            description="Mapping of dataset label to ObsCore configuration",
        ),
    ]

    path_prefix: str = Field("/api/sia", title="URL prefix for application")

    slack_webhook: Annotated[
        HttpUrl | None, Field(title="Slack webhook for exception reporting")
    ] = None

    @model_validator(mode="after")
    def _validate_obscore_config(self) -> Self:
        """Every dataset must have an ObsCore configuration."""
        for dataset in self.datasets:
            if not self.obscore_config.get(dataset):
                msg = f"No ObsCore configuration for dataset {dataset}"
                raise ValueError(msg)
        return self


config = Config()
"""Configuration instance for sia."""
