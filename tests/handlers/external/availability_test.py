"""Test the availability's endpoint.

This test checks that the availability endpoint returns the expected XML
response, read from the :file:`templates/availability.xml` file.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.templating import Jinja2Templates
from httpx import AsyncClient

from sia.config import Config, config
from sia.services.availability import AvailabilityService
from sia.services.data_collections import DataCollectionService

from ...support.data import SiaData


@pytest.mark.asyncio
async def test_availability(
    data: SiaData, client: AsyncClient, mock_async_client: AsyncMock
) -> None:
    """Test the availability endpoint."""
    templates = Jinja2Templates(data.path("templates"))

    r = await client.get(f"{config.path_prefix}/dp02/availability")
    assert r.status_code == 200
    expected = templates.get_template("availability.xml").render()
    assert r.text.strip() == expected.strip()


@pytest.mark.asyncio
async def test_remote_butler_availability_success(
    test_config: Config,
) -> None:
    """Test the availability of the remote Butler ."""
    collection = DataCollectionService(
        config=test_config
    ).get_data_collection_by_name(name="dp02")

    checker = AvailabilityService(collection)
    with patch("sia.services.availability.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value = (
            mock_response
        )
        availability = await checker.get_availability()
    assert availability.available is True


@pytest.mark.asyncio
async def test_remote_butler_availability_failure(
    test_config: Config,
) -> None:
    """Test the availability of the remote Butler  when
    it is not available.
    """
    collection = DataCollectionService(
        config=test_config
    ).get_data_collection_by_name(name="dp02")

    checker = AvailabilityService(collection)
    with patch("sia.services.availability.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_client.return_value.__aenter__.return_value.get.return_value = (
            mock_response
        )

        availability = await checker.get_availability()
    assert availability.available is False
