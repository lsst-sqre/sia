"""Test the availability's endpoint.
This test checks that the availability endpoint returns the
expected XML response, read from the templates/availability.xml file.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from httpx import AsyncClient

from sia.config import Config, config
from sia.models.butler_type import ButlerType
from sia.services.availability import (
    AvailabilityService,
    DirectButlerAvailabilityChecker,
    RemoteButlerAvailabilityChecker,
)

router = APIRouter()
"""FastAPI router for all external handlers."""


@pytest.mark.asyncio
async def test_availability(
    client: AsyncClient, mock_async_client: AsyncMock
) -> None:
    """Test the availability endpoint."""
    templates_dir = Jinja2Templates(
        directory=str(Path(__file__).parent.parent.parent / "templates")
    )
    mock_client, mock_response = mock_async_client

    r = await client.get(f"{config.path_prefix}/availability")
    assert r.status_code == 200
    template_rendered = templates_dir.get_template("availability.xml").render()
    assert r.text.strip() == template_rendered.strip()


@pytest.mark.asyncio
async def test_direct_butler_availability(test_config_direct: Config) -> None:
    """Test the availability of the direct Butler ."""
    checker = DirectButlerAvailabilityChecker()
    availability = await checker.check_availability(config=test_config_direct)
    assert availability.available is True


@pytest.mark.asyncio
async def test_remote_butler_availability_success(
    test_config_remote: Config,
) -> None:
    """Test the availability of the remote Butler ."""
    checker = RemoteButlerAvailabilityChecker()
    with patch("sia.services.availability.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value = (
            mock_response
        )
        availability = await checker.check_availability(
            config=test_config_remote
        )
    assert availability.available is True


@pytest.mark.asyncio
async def test_remote_butler_availability_failure(
    test_config_remote: Config,
) -> None:
    """Test the availability of the remote Butler  when
    it is not available.
    """
    checker = RemoteButlerAvailabilityChecker()
    with patch("sia.services.availability.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_client.return_value.__aenter__.return_value.get.return_value = (
            mock_response
        )

        availability = await checker.check_availability(
            config=test_config_remote
        )
    assert availability.available is False


@pytest.mark.asyncio
async def test_remote_butler_availability_no_config(
    test_config_remote: Config,
) -> None:
    """Test the availability of the remote Butler
    when there is no configuration.
    """
    checker = RemoteButlerAvailabilityChecker()
    conf = Config()
    conf.butler_data_collections = []
    availability = await checker.check_availability(config=conf)
    assert availability.available is False


@pytest.mark.asyncio
async def test_availability_service(test_config_direct: Config) -> None:
    """Test the availability service."""
    service = AvailabilityService(config=test_config_direct)
    availability = await service.get_availability()
    assert availability.available is True


@pytest.mark.asyncio
async def test_availability_service_unknown_butler_type(
    test_config_remote: Config,
) -> None:
    """Test the availability service with an unknown butler_type."""
    service = AvailabilityService(config=test_config_remote)
    service.checkers.pop(ButlerType.REMOTE)
    availability = await service.get_availability()
    assert availability.available is True
