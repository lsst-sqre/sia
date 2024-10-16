"""Test the Config model."""

import json

import pytest
from pydantic_settings import SettingsError

from sia.config import Config
from sia.exceptions import FatalFaultError
from sia.models.data_collections import ButlerDataCollection


@pytest.mark.asyncio
async def test_empty_config(
    test_config_remote: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that an empty Config raises a FatalFaultError."""
    monkeypatch.setenv("SIA_BUTLER_DATA_COLLECTIONS", "")

    with pytest.raises(
        SettingsError,
        match='error parsing value for field "butler_data_collections" '
        'from source "EnvSettingsSource"',
    ):
        Config()


@pytest.mark.asyncio
async def test_config_no_butler_type(
    test_config_remote: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that a Config with no default collection raises a
    FatalFaultError.
    """
    sample_collection: list[ButlerDataCollection] = []

    monkeypatch.setenv(
        "SIA_BUTLER_DATA_COLLECTIONS", json.dumps(sample_collection)
    )

    with pytest.raises(
        FatalFaultError,
        match="FatalFault: No Data Collections configured. "
        "Please configure at least one Data collection.",
    ):
        Config()
