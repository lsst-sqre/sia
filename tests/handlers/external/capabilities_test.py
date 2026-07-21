"""Test the capabilities' endpoint.
This test checks that the capabilities endpoint returns the
expected XML response, read from the templates/capabilities.xml file.
"""

import pytest
from fastapi.templating import Jinja2Templates
from httpx import AsyncClient

from sia.config import config

from ...support.data import SiaData


@pytest.mark.asyncio
async def test_capabilities(data: SiaData, client: AsyncClient) -> None:
    """Test the capabilities endpoint."""
    templates = Jinja2Templates(data.path("templates"))

    context = {
        "capabilities_url": (
            f"https://example.com{config.path_prefix}/dp02/capabilities"
        ),
        "availability_url": (
            f"https://example.com{config.path_prefix}/dp02/availability"
        ),
        "query_url": f"https://example.com{config.path_prefix}/dp02/query",
    }
    expected = templates.get_template("capabilities.xml").render(context)

    r = await client.get(f"{config.path_prefix}/dp02/capabilities")
    assert r.status_code == 200
    assert r.text.strip() == expected.strip()
