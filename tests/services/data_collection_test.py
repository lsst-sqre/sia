"""Tests for the config_reader module."""

import copy
from pathlib import Path

import pytest
from pydantic import HttpUrl

from sia.config import Config
from sia.exceptions import FatalFaultError, UsageFaultError
from sia.models.butler_type import ButlerType
from sia.models.data_collections import ButlerDataCollection
from sia.services.data_collections import DataCollectionService

BASE_PATH = Path(__file__).parent


@pytest.fixture
def test_config_invalid() -> Config:
    """Return a test configuration with an invalid Data Collection."""
    butler_collections = [
        ButlerDataCollection(
            config=Path("invalid_config.yaml"),
            repository=Path("invalid_repo"),
            default=False,
            label="InvalidLabel",
            defaultinstrument="LSSTCam-imSim",
        ),
    ]
    return Config(
        butler_type=ButlerType.REMOTE,
        butler_data_collections=butler_collections,
    )


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
    ).get_data_collection(label=label)
    assert result.label == label
    assert result.repository == HttpUrl(
        "https://example.com/api/butler/repo/dp02/butler.yaml"
    )


@pytest.mark.asyncio
async def test_get_data_collection_no_label(
    test_config_remote: Config,
) -> None:
    """Test get_data_collection function with no label."""
    result = DataCollectionService(
        config=test_config_remote
    ).get_data_collection(label=None)
    assert result.label == "LSST.DP02"
    assert result.repository == HttpUrl(
        "https://example.com/api/butler/repo/dp02/butler.yaml"
    )


@pytest.mark.asyncio
async def test_get_data_collection_empty_config(empty_config: Config) -> None:
    """Test get_data_collection function with an empty configuration."""
    with pytest.raises(
        FatalFaultError, match="No Data Collections configured"
    ):
        DataCollectionService(config=empty_config).get_data_collection(
            label=None
        )


@pytest.mark.asyncio
async def test_get_data_collection_invalid_label(
    test_config_remote: Config,
) -> None:
    """Test get_data_collection function with an invalid label."""
    with pytest.raises(
        UsageFaultError,
        match="Label InvalidLabel not found in Data collections",
    ):
        DataCollectionService(config=test_config_remote).get_data_collection(
            label="InvalidLabel"
        )


@pytest.mark.asyncio
async def test_get_data_collection_case_sensitive(
    test_config_remote: Config,
) -> None:
    """Test get_data_collection function with a case-sensitive label."""
    with pytest.raises(
        UsageFaultError, match="Label lsst.dp02 not found in Data collections"
    ):
        DataCollectionService(config=test_config_remote).get_data_collection(
            label="lsst.dp02"
        )


@pytest.mark.asyncio
async def test_get_default_collection_multiple_defaults(
    test_config_remote: Config,
) -> None:
    test_config = copy.deepcopy(test_config_remote)

    # Add one more default collection
    config = BASE_PATH / "data" / "config" / "dp02.yaml"

    new_configs = [
        ButlerDataCollection(
            config=config,
            label="New collection",
            repository=HttpUrl(
                "https://example.com/api/butler/repo/dp02/butler.yaml"
            ),
            defaultinstrument="LSSTCam-imSim",
            default=True,
        ),
        ButlerDataCollection(
            config=config,
            label="New collection 2",
            repository=HttpUrl(
                "https://example.com/api/butler/repo/dp02/butler.yaml"
            ),
            defaultinstrument="LSSTCam-imSim",
            default=False,
        ),
    ]

    test_config.butler_data_collections.extend(new_configs)

    expected_label = "LSST.DP02"

    result = DataCollectionService(
        config=test_config_remote
    ).get_default_collection()

    assert (
        result.label == expected_label
    ), f"Expected {expected_label}, but got {result.label}"
