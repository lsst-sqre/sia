"""Test the availability endpoint."""

import pytest
import respx
from httpx import AsyncClient, Response
from rubin.repertoire import Discovery

from sia.config import config

from ...support.data import SiaData


@pytest.mark.asyncio
async def test_availability(
    *,
    data: SiaData,
    client: AsyncClient,
    mock_discovery: Discovery,
    respx_mock: respx.Router,
) -> None:
    """Test the availability endpoint."""
    butler_url = mock_discovery.datasets["dp02"].butler_config
    assert butler_url
    respx_mock.get(str(butler_url)).mock(return_value=Response(200))

    r = await client.get(f"{config.path_prefix}/dp02/availability")
    assert r.status_code == 200
    data.assert_text_matches(r.text, "responses/availability-success.xml")


@pytest.mark.asyncio
async def test_availability_failure(
    *,
    data: SiaData,
    client: AsyncClient,
    mock_discovery: Discovery,
    respx_mock: respx.Router,
) -> None:
    """Test the availability of the remote Butler  when
    it is not available.
    """
    butler_url = mock_discovery.datasets["dp02"].butler_config
    assert butler_url
    respx_mock.get(str(butler_url)).mock(return_value=Response(404))

    r = await client.get(f"{config.path_prefix}/dp02/availability")
    assert r.status_code == 200
    data.assert_text_matches(r.text, "responses/availability-404.xml")
