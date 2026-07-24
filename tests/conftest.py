"""Test fixtures for sia tests."""

from collections.abc import AsyncGenerator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
import respx
from asgi_lifespan import LifespanManager
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from rubin.repertoire import Discovery, register_mock_discovery

from sia import main
from sia.config import Config, config

from .support.butler import MockButler, patch_butler, patch_siav2_query
from .support.data import SiaData


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-test-data",
        action="store_true",
        default=False,
        help="Overwrite expected test output with current results",
    )


@pytest.fixture(autouse=True)
def _config(data: SiaData, monkeypatch: pytest.MonkeyPatch) -> Config:
    """Override ObsCore configuration to use test data."""
    obscore_config = {"dp02": str(data.path("config/dp02.yaml"))}
    monkeypatch.setattr(config, "obscore_config", obscore_config)
    return config


@pytest.fixture(autouse=True)
def _mock_butler() -> Iterator[MockButler]:
    """Mock Butler for testing."""
    with patch_butler() as butler:
        yield butler


@pytest.fixture(autouse=True)
def _mock_siav2_query() -> Iterator[None]:
    """Mock ObsCore SIAv2 implementation for testing."""
    with patch_siav2_query():
        yield


@pytest_asyncio.fixture
async def app() -> AsyncGenerator[FastAPI]:
    """Return a configured test application.

    Wraps the application in a lifespan manager so that startup and shutdown
    events are sent during test execution.
    """

    @main.app.post("/test-params")
    async def test_params_endpoint(
        request: Request,
    ) -> dict:
        """Test endpoint for the middleware.

        Parameters
        ----------
        request
            The incoming request

        Returns
        -------
        dict[str, dict[str, str]]
            The response data
        """
        form_data = await request.form()
        return {"method": "POST", "form_data": dict(form_data)}

    async with LifespanManager(main.app):
        yield main.app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    """Return an ``httpx.AsyncClient`` configured to talk to the test app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="https://example.com/",
        headers={
            "X-Auth-Request-Token": "sometoken",
            "X-Auth-Request-User": "user",
        },
    ) as client:
        yield client


@pytest.fixture
def data(request: pytest.FixtureRequest) -> SiaData:
    update = request.config.getoption("--update-test-data")
    return SiaData(Path(__file__).parent / "data", update_test_data=update)


@pytest.fixture(autouse=True)
def mock_discovery(
    data: SiaData, respx_mock: respx.Router, monkeypatch: pytest.MonkeyPatch
) -> Discovery:
    monkeypatch.setenv("REPERTOIRE_BASE_URL", "https://example.com/repertoire")
    path = data.path("discovery.json")
    return register_mock_discovery(respx_mock, path)
