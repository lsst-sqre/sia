"""Test the Config model."""

import json
import re

import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsError

from sia.config import Config


@pytest.mark.asyncio
async def test_empty_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIA_DATASETS", "")
    with pytest.raises(SettingsError):
        Config()


@pytest.mark.asyncio
async def test_config_no_butler_type(monkeypatch: pytest.MonkeyPatch) -> None:
    obscore_config = {"dp2": "https://example.com/dp2.yaml"}
    monkeypatch.setenv("SIA_OBSCORE_CONFIG", json.dumps(obscore_config))

    expected = "No ObsCore configuration for dataset dp02"
    with pytest.raises(ValidationError, match=re.escape(expected)):
        Config()
