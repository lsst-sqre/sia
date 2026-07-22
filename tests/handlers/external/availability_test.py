"""Test the availability endpoint.

This test checks that the availability endpoint returns the expected XML
response.
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from sia.config import config
from sia.services.availability import AvailabilityService
from sia.services.data_collections import DataCollectionService

from ...support.data import SiaData


@pytest.mark.asyncio
async def test_availability(
    data: SiaData, client: AsyncClient, mock_async_client: AsyncMock
) -> None:
    """Test the availability endpoint."""
    r = await client.get(f"{config.path_prefix}/dp02/availability")
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/xml"
    data.assert_text_matches(r.text, "responses/availability.xml")


@pytest.mark.asyncio
async def test_remote_butler_availability_success() -> None:
    """Test the availability of the remote Butler ."""
    collection = DataCollectionService().get_data_collection_by_name(
        name="dp02"
    )

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
async def test_remote_butler_availability_failure() -> None:
    """Test the availability of the remote Butler  when
    it is not available.
    """
    collection = DataCollectionService().get_data_collection_by_name(
        name="dp02"
    )

    checker = AvailabilityService(collection)
    with patch("sia.services.availability.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_client.return_value.__aenter__.return_value.get.return_value = (
            mock_response
        )

        availability = await checker.get_availability()
    assert availability.available is False
