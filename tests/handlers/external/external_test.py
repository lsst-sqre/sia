"""Tests for the sia.handlers.external module and routes."""

from __future__ import annotations

import re
from typing import Any

import pytest
from httpx import AsyncClient

from sia.config import config
from sia.constants import RESULT_NAME
from tests.support.butler import MockButler, MockButlerQueryService
from tests.support.constants import EXCEPTION_MESSAGES
from tests.support.validators import validate_votable_error


@pytest.mark.asyncio
async def test_get_index(client: AsyncClient) -> None:
    """Test ``GET /api/sia/``."""
    response = await client.get(f"{config.path_prefix}/")
    assert response.status_code == 200
    data = response.json()
    metadata = data["metadata"]
    assert metadata["name"] == config.name
    assert isinstance(metadata["version"], str)
    assert isinstance(metadata["description"], str)
    assert isinstance(metadata["repository_url"], str)
    assert isinstance(metadata["documentation_url"], str)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "query_params",
        "expected_status",
        "expected_content_type",
        "expected_message",
    ),
    [
        (
            "POS=CIRCLE+320+-0.1+10.7",
            200,
            "application/x-votable+xml",
            None,
        ),
        (
            "POS=CIRCLE+320+-0.1+10.7&TIME=-Inf++Inf",
            200,
            "application/x-votable+xml",
            None,
        ),
        (
            "POS=CIRCLE+320+-0.1+10.7&TIME=-Inf++Inf&DP_TYPE=image",
            200,
            "application/x-votable+xml",
            None,
        ),
        (
            "pos=CIRCLE+320+-0.1+10.7&TIME=-Inf++Inf&DP_TYPE=image",
            200,
            "application/x-votable+xml",
            None,
        ),
        (
            "POS=RANGE+0+360.0+-2.0+2.0&TIME=-Inf++Inf&DP_TYPE=image&dp_type"
            "=cube",
            200,
            "application/x-votable+xml",
            None,
        ),
    ],
)
async def test_query_endpoint_mocker_get(
    client: AsyncClient,
    query_params: str,
    expected_status: int,
    expected_content_type: str,
    expected_message: str | None,
    mock_siav2_query: MockButlerQueryService,
    mock_butler: MockButler,
    expected_votable: str,
) -> None:
    """Test ``GET /api/sia/query`` with valid parameters but use a Mocker
    for the Butler SIAv2 query.
    """
    response = await client.get(
        f"{config.path_prefix}/dp02/query?{query_params}",
    )

    # Remove XML declaration and comments
    cleaned_response = re.sub(
        r"<\?xml.*?\?>\s*", "", response.text, flags=re.DOTALL
    )
    cleaned_response = re.sub(
        r"<!--.*?-->\s*", "", cleaned_response, flags=re.DOTALL
    )

    assert cleaned_response == expected_votable
    assert response.status_code == expected_status
    assert response.headers["content-type"] == expected_content_type
    assert "content-disposition" in response.headers
    assert response.headers["content-disposition"].startswith(
        f"attachment; filename={RESULT_NAME}.xml",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "query_params",
        "expected_status",
        "expected_content_type",
        "expected_message",
    ),
    [
        (
            "POS=SOME_SHAPE+321+0+1&BAND=700e-9&FORMAT=votable",
            400,
            "application/xml",
            EXCEPTION_MESSAGES["invalid_pos"],
        ),
        (
            "POS=CIRCLE+0+0+1&TIME=ABC",
            400,
            "application/xml",
            EXCEPTION_MESSAGES["invalid_time"],
        ),
        (
            "POS=CIRCLE+0+0+1&CALIB=6",
            400,
            "application/xml",
            EXCEPTION_MESSAGES["invalid_calib"],
        ),
        (
            "MAXREC=0",
            200,
            "application/x-votable+xml",
            None,
        ),
    ],
)
async def test_query_endpoint_get(
    client_direct: AsyncClient,
    query_params: str,
    expected_status: int,
    expected_content_type: str,
    expected_message: str | None,
) -> None:
    response = await client_direct.get(
        f"{config.path_prefix}/hsc/query?{query_params}"
    )

    assert response.status_code == expected_status
    assert expected_content_type in response.headers["content-type"]

    if expected_status == 200:
        assert "content-disposition" in response.headers
        assert response.headers["content-disposition"].startswith(
            f"attachment; filename={RESULT_NAME}.xml"
        )
    elif expected_status == 400:
        validate_votable_error(response, expected_message)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "post_data",
        "expected_status",
        "expected_content_type",
        "expected_message",
    ),
    [
        (
            {
                "POS": "SOME_SHAPE 321 0 1",
                "BAND": "700e-9",
                "FORMAT": "votable",
            },
            400,
            "application/xml",
            EXCEPTION_MESSAGES["invalid_pos"],
        ),
        (
            {"pos": "CIRCLE 0 0 1", "TIME": "ABC"},
            400,
            "application/xml",
            EXCEPTION_MESSAGES["invalid_time"],
        ),
        (
            {"POS": "CIRCLE 321 0 1", "BAND": "700e-9", "FORMAT": "votable"},
            200,
            "application/x-votable+xml",
            EXCEPTION_MESSAGES["invalid_time"],
        ),
        (
            {"MAXREC": "0"},
            200,
            "application/x-votable+xml",
            None,
        ),
    ],
)
async def test_query_endpoint_post(
    client_direct: AsyncClient,
    post_data: dict[str, Any],
    expected_status: int,
    expected_content_type: str,
    expected_message: str | None,
    expected_votable: str,
) -> None:
    """Test ``POST /api/sia/query`` with various parameters."""
    response = await client_direct.post(
        f"{config.path_prefix}/hsc/query", data=post_data
    )
    assert response.status_code == expected_status

    if expected_status == 200:
        assert "content-disposition" in response.headers
        assert response.headers["content-disposition"].startswith(
            f"attachment; filename={RESULT_NAME}.xml"
        )
    elif expected_status == 400:
        validate_votable_error(response, expected_message)
