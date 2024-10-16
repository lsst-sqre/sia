"""Tests for the config_reader module."""

from pathlib import Path

import pytest
from pydantic import HttpUrl

from sia.config import Config
from sia.exceptions import FatalFaultError
from sia.services.data_collections import DataCollectionService

BASE_PATH = Path(__file__).parent


@pytest.mark.asyncio
async def test_get_data_repositories(test_config_remote: Config) -> None:
    """Test get_data_repositories function."""
    expected_repos = {
        "LSST.DP02": "https://example.com/api/butler/repo/dp02/butler.yaml"
    }

    result = DataCollectionService(
        config=test_config_remote
    ).get_data_repositories()

    assert (
        result == expected_repos
    ), f"Expected {expected_repos}, but got {result}"
    assert len(result) == 1, f"Expected 1 repository, but got {len(result)}"
    assert "LSST.DP02" in result, "Expected 'LSST.DP02' to be in the result"
    assert result["LSST.DP02"] == (
        "https://example.com/api/butler/repo/dp02/butler.yaml"
    ), f"Unexpected repository URL for LSST.DP02: {result['LSST.DP02']}"


@pytest.mark.asyncio
async def test_get_data_collection_with_label(
    test_config_remote: Config,
) -> None:
    """Test get_data_collection function with a label."""
    label = "LSST.DP02"
    result = DataCollectionService(
        config=test_config_remote
    ).get_data_collection_by_label(label=label)
    assert result.label == label
    assert result.repository == HttpUrl(
        "https://example.com/api/butler/repo/dp02/butler.yaml"
    )


@pytest.mark.asyncio
async def test_get_data_collection_with_name(
    test_config_remote: Config,
) -> None:
    """Test get_data_collection function with a name."""
    name = "dp02"
    result = DataCollectionService(
        config=test_config_remote
    ).get_data_collection_by_name(name=name)
    assert result.name == name
    assert result.repository == HttpUrl(
        "https://example.com/api/butler/repo/dp02/butler.yaml"
    )


@pytest.mark.asyncio
async def test_get_data_collection_no_label(
    test_config_remote: Config,
) -> None:
    """Test get_data_collection function with no label."""
    with pytest.raises(
        ValueError,
        match="Label is required.",
    ):
        DataCollectionService(
            config=test_config_remote
        ).get_data_collection_by_label(label="")


@pytest.mark.asyncio
async def test_get_data_collection_empty_config() -> None:
    """Test get_data_collection function with an empty configuration."""
    with pytest.raises(
        FatalFaultError,
        match="FatalFault: No Data Collections configured. Please configure "
        "at least one Data collection.",
    ):
        empty_config = Config(
            butler_data_collections=[],
        )
        DataCollectionService(
            config=empty_config
        ).get_data_collection_by_label(label="")


@pytest.mark.asyncio
async def test_get_data_collection_invalid_label(
    test_config_remote: Config,
) -> None:
    """Test get_data_collection function with an invalid label."""
    with pytest.raises(
        KeyError,
        match="Label InvalidLabel not found in Data collections",
    ):
        DataCollectionService(
            config=test_config_remote
        ).get_data_collection_by_label(label="InvalidLabel")
