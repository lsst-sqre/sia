"""Test the capabilities endpoint.

This test checks that the capabilities endpoint returns the expected XML
response.
"""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from sia.config import config

from ...support.constants import TEST_BASE_URL
from ...support.data import SiaData


@pytest.mark.asyncio
async def test_capabilities(data: SiaData, client: AsyncClient) -> None:
    """Test the capabilities endpoint."""
    r = await client.get(f"{config.path_prefix}/dp02/capabilities")
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/xml"
    data.assert_text_matches(r.text, "responses/capabilities.xml")


@pytest.mark.asyncio
async def test_availability_anonymous(data: SiaData, app: FastAPI) -> None:
    """Test the capabilities endpoint without authentication."""
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url=TEST_BASE_URL)

    r = await client.get(f"{config.path_prefix}/dp02/capabilities")
    assert r.status_code == 200
    data.assert_text_matches(r.text, "responses/capabilities.xml")


@pytest.mark.asyncio
async def test_capabilities_unknown(client: AsyncClient) -> None:
    r = await client.get(f"{config.path_prefix}/dp1/capabilities")
    assert r.status_code == 404
