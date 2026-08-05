"""Test fixtures for sia tests."""

from collections.abc import AsyncGenerator, Iterator
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
import respx
from asgi_lifespan import LifespanManager
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from rubin.repertoire import Discovery, register_mock_discovery

from sia import main
from sia.config import Config, config

from .support.butler import (
    MockButler,
    MockButlerQueryService,
    patch_butler,
    patch_siav2_query,
)
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


@pytest.fixture
def mock_async_client(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[AsyncMock, AsyncMock]:
    """Return a mock AsyncClient and a mock response object.

    Parameters
    ----------
    monkeypatch
        The pytest monkeypatch fixture

    Returns
    -------
    tuple[AsyncMock, AsyncMock]
        The mock AsyncClient and mock response objects
    """
    mock_response = AsyncMock()
    mock_response.status_code = 200

    mock_client = AsyncMock(spec=AsyncClient)
    mock_client.__aenter__.return_value.get.return_value = mock_response

    monkeypatch.setattr(
        "sia.services.availability.AsyncClient", lambda: mock_client
    )

    return mock_client, mock_response


@pytest.fixture(autouse=True)
def mock_discovery(
    data: SiaData, respx_mock: respx.Router, monkeypatch: pytest.MonkeyPatch
) -> Discovery:
    monkeypatch.setenv("REPERTOIRE_BASE_URL", "https://example.com/repertoire")
    path = data.path("discovery.json")
    return register_mock_discovery(respx_mock, path)


@pytest.fixture
def mock_exporter_config(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Return a mock ExporterConfig instance."""
    mock = Mock()
    monkeypatch.setattr(
        "sia.factories.butler_type_factory.ExporterConfig", mock
    )
    return mock


@pytest.fixture
def mock_labeled_butler_factory(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Return a mock LabeledButlerFactory instance."""
    mock = Mock()
    monkeypatch.setattr(
        "sia.factories.butler_type_factory.LabeledButlerFactory", mock
    )
    return mock


@pytest.fixture
def mock_butler_config(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Return a mock ButlerConfig instance."""
    mock = Mock()
    monkeypatch.setattr("sia.factories.butler_type_factory.ButlerConfig", mock)
    return mock


@pytest.fixture
def mock_siav2_query() -> Iterator[MockButlerQueryService]:
    """Mock Butler for testing."""
    yield from patch_siav2_query()


@pytest.fixture
def mock_butler() -> Iterator[MockButler]:
    """Mock Butler for testing."""
    yield from patch_butler()
