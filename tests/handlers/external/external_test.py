"""Tests for the sia.handlers.external module and routes."""

from typing import Any

import pytest
import respx
from httpx import AsyncClient
from rubin.repertoire import register_mock_discovery
from safir.dependencies.http_client import http_client_dependency
from safir.testing.logging import parse_log_tuples

from sia.config import config
from sia.constants import RESULT_NAME
from tests.support.constants import EXCEPTION_MESSAGES
from tests.support.validators import validate_votable_error

from ...support.data import SiaData


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
    *,
    data: SiaData,
    client: AsyncClient,
    query_params: str,
    expected_status: int,
    expected_content_type: str,
    expected_message: str | None,
) -> None:
    """Test ``GET /api/sia/query`` with valid parameters but use a Mocker
    for the Butler SIAv2 query.
    """
    response = await client.get(
        f"{config.path_prefix}/dp02/query?{query_params}",
    )
    data.assert_votable_matches(response.text, "responses/votable.xml")
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
    *,
    client: AsyncClient,
    query_params: str,
    expected_status: int,
    expected_content_type: str,
    expected_message: str | None,
) -> None:
    response = await client.get(
        f"{config.path_prefix}/dp02/query?{query_params}"
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
    *,
    client: AsyncClient,
    post_data: dict[str, Any],
    expected_status: int,
    expected_content_type: str,
    expected_message: str | None,
) -> None:
    """Test ``POST /api/sia/query`` with various parameters."""
    response = await client.post(
        f"{config.path_prefix}/dp02/query", data=post_data
    )
    assert response.status_code == expected_status

    if expected_status == 200:
        assert "content-disposition" in response.headers
        assert response.headers["content-disposition"].startswith(
            f"attachment; filename={RESULT_NAME}.xml"
        )
    elif expected_status == 400:
        validate_votable_error(response, expected_message)


@pytest.mark.asyncio
async def test_query_maxrec_zero(
    data: SiaData,
    client: AsyncClient,
) -> None:
    r = await client.get(
        f"{config.path_prefix}/dp02/query", params={"MAXREC": 0}
    )
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/x-votable+xml"
    data.assert_text_matches(r.text, "responses/self-description.xml")


@pytest.mark.asyncio
async def test_query_unknown(client: AsyncClient) -> None:
    r = await client.get(
        f"{config.path_prefix}/dp1/query", params={"MAXREC": 0}
    )
    assert r.status_code == 404

    r = await client.post(
        f"{config.path_prefix}/dp1/query", data={"MAXREC": 0}
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_bad_discovery(
    *,
    data: SiaData,
    client: AsyncClient,
    respx_mock: respx.Router,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test having service discovery drop a dataset SIA is serving."""
    caplog.clear()
    r = await client.get(
        f"{config.path_prefix}/dp02/query",
        params={"POS": "CIRCLE 320 -0.1 10.7"},
    )
    assert r.status_code == 200
    data.assert_votable_matches(r.text, "responses/votable.xml")
    seen_log_messages = [
        m
        for m in parse_log_tuples("sia", caplog.record_tuples)
        if m["severity"] not in ("info", "debug")
    ]
    assert seen_log_messages == []

    # Now, replace service discovery information with empty information, which
    # is missing any configuration for dp02.
    path = data.path("discovery/empty.json")
    register_mock_discovery(respx_mock, path)

    # Clear the service discovery cache by changing the underlying HTTP
    # client, which forces recreation of the Repertoire client. This is a hack
    # that should be replaced with a proper way to clear the cache in
    # rubin.repertoire.
    await http_client_dependency.aclose()

    # The query should still succeed, since cached Butler information should
    # be used even though the service discovery information has been updated.
    caplog.clear()
    r = await client.get(
        f"{config.path_prefix}/dp02/query",
        params={"POS": "CIRCLE 320 -0.1 10.7"},
    )
    assert r.status_code == 200
    data.assert_votable_matches(r.text, "responses/votable.xml")

    # An error and a warning should have been logged.
    seen_log_messages = [
        m
        for m in parse_log_tuples("sia", caplog.record_tuples)
        if m["severity"] not in ("info", "debug")
    ]
    data.assert_json_matches(seen_log_messages, "logs/bad-discovery")
