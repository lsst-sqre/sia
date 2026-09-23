"""Configuration definition."""

from typing import Annotated
from urllib.parse import urlsplit

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from safir.logging import LogLevel, Profile
from safir.metrics import MetricsConfiguration, metrics_configuration_factory

__all__ = ["Config", "config"]


class Config(BaseSettings):
    """Configuration for sia."""

    model_config = SettingsConfigDict(env_prefix="SIA_", case_sensitive=False)

    ivoid_format: str = Field(
        ...,
        title="Format for service IVOID",
        description=(
            "A Python format string used to generate the IVOID returned in"
            " the service self-description. This format string must have"
            " one variable, dataset, which will be replaced with the short"
            " label of the dataset."
        ),
    )

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

    path_prefix: str = Field("/api/sia", title="URL prefix for application")

    slack_webhook: Annotated[
        HttpUrl | None, Field(title="Slack webhook for exception reporting")
    ] = None

    @field_validator("ivoid_format")
    @classmethod
    def _validate_ivoid_format(cls, v: str) -> str:
        try:
            uri = v.format(dataset="dataset")
        except Exception as e:
            msg = f"Invalid ivoid_format: {type(e).__name__}: {e!s}"
            raise ValueError(msg) from e
        parsed_uri = urlsplit(uri)
        if parsed_uri.scheme != "ivo":
            msg = f"ivoid_format scheme must be ivo, not {parsed_uri.scheme}"
            raise ValueError(msg)
        return v


config = Config()
"""Configuration instance for sia."""
