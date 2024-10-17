"""Tests for the IVOA middleware."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_lowercase_form_keys(client: AsyncClient) -> None:
    """Test that the form keys are converted to lowercase."""
    response = await client.post(
        "/test-params", data={"UpperCase": "value", "MixedCase": "another"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "method": "POST",
        "form_data": {"uppercase": "value", "mixedcase": "another"},
    }


@pytest.mark.asyncio
async def test_preserve_value_case(client: AsyncClient) -> None:
    """Test that the form values are preserved."""
    response = await client.post(
        "/test-params", data={"key": "MixedCaseValue"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "method": "POST",
        "form_data": {"key": "MixedCaseValue"},
    }


@pytest.mark.asyncio
async def test_empty_form(client: AsyncClient) -> None:
    """Test that an empty form is handled correctly."""
    response = await client.post("/test-params", data={})
    assert response.status_code == 200
    assert response.json() == {"method": "POST", "form_data": {}}


@pytest.mark.asyncio
async def test_content_type(client: AsyncClient) -> None:
    """Test that the middleware handles different content types."""
    response = await client.post(
        "/test-params",
        data={"UpperCase": "value"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "method": "POST",
        "form_data": {"uppercase": "value"},
    }
