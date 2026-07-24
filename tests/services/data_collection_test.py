"""Tests for the config_reader module."""

import pytest

from sia.services.data_collections import DataCollectionService

from ..support.data import SiaData


@pytest.mark.asyncio
async def test_get_data_collection_with_name(data: SiaData) -> None:
    """Test get_data_collection function with a name."""
    name = "dp02"
    result = DataCollectionService().get_data_collection_by_name(name=name)
    assert result.name == name
    assert result.config == data.path("config/dp02.yaml")
