"""Test the capabilities endpoint.

This test checks that the capabilities endpoint returns the expected XML
response.
"""

import pytest
from httpx import AsyncClient

from sia.config import config

from ...support.data import SiaData


@pytest.mark.asyncio
async def test_capabilities(data: SiaData, client: AsyncClient) -> None:
    """Test the capabilities endpoint."""
    r = await client.get(f"{config.path_prefix}/dp02/capabilities")
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/xml"
    data.assert_text_matches(r.text, "responses/capabilities.xml")
