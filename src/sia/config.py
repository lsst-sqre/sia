"""Configuration definition."""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, HttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from safir.logging import LogLevel, Profile

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

    model_config = SettingsConfigDict(env_prefix="SIA_", case_sensitive=False)
    """Configuration for the model settings."""

    butler_data_collections: Annotated[
        list[ButlerDataCollection],
        Field(title="Data collections"),
    ]
    """Configuration for the data collections."""

    slack_webhook: Annotated[
        HttpUrl | None, Field(title="Slack webhook for exception reporting")
    ] = None
    """Slack webhook for exception reporting."""

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
