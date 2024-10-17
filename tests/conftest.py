"""Test fixtures for sia tests."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from pydantic import HttpUrl

from sia import main
from sia.config import Config, config
from sia.models.butler_type import ButlerType
from sia.models.data_collections import ButlerDataCollection

from .support.butler import (
    MockButler,
    MockButlerQueryService,
    patch_butler,
    patch_siav2_query,
)

BASE_PATH = Path(__file__).parent


@pytest_asyncio.fixture
async def app(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[FastAPI]:
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

    data_config = BASE_PATH / "data" / "config" / "dp02.yaml"

    butler_collections = [
        ButlerDataCollection(
            config=data_config,
            label="LSST.DP02",
            name="dp02",
            butler_type=ButlerType.REMOTE,
            repository=HttpUrl("https://example/repo/dp02/butler.yaml"),
            default_instrument="LSSTCam-imSim",
        ),
    ]
    monkeypatch.setattr(config, "path_prefix", "/api/sia")
    monkeypatch.setattr(config, "butler_data_collections", butler_collections)

    async with LifespanManager(main.app):
        yield main.app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Return an ``httpx.AsyncClient`` configured to talk to the test app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="https://example.com/",
        headers={"X-Auth-Request-Token": "sometoken"},
    ) as client:
        yield client


@pytest_asyncio.fixture
async def app_direct(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[FastAPI]:
    """Return a configured test application.

    Wraps the application in a lifespan manager so that startup and shutdown
    events are sent during test execution.
    """
    repo_path = BASE_PATH / "data" / "repo"
    config_file = BASE_PATH / "data" / "config" / "ci_hsc_gen3.yaml"

    butler_collections = [
        ButlerDataCollection(
            config=config_file,
            repository=repo_path,
            butler_type=ButlerType.DIRECT,
            label="ci_hsc_gen3",
            name="hsc",
            default_instrument="HSC",
        ),
    ]

    monkeypatch.setattr(config, "path_prefix", "/api/sia")
    monkeypatch.setattr(config, "butler_data_collections", butler_collections)

    async with LifespanManager(main.app):
        yield main.app


@pytest_asyncio.fixture
async def client_direct(app_direct: FastAPI) -> AsyncIterator[AsyncClient]:
    """Return an ``httpx.AsyncClient`` configured to talk to the test app."""
    async with AsyncClient(
        transport=ASGITransport(app=app_direct),
        base_url="https://example.com/",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def expected_votable() -> str:
    """Return the expected VOTable content as a string."""
    xml_file_path = BASE_PATH / "templates" / "expected_votable.xml"
    with xml_file_path.open("r", encoding="utf-8") as file:
        return file.read()


@pytest_asyncio.fixture
async def test_config_remote() -> Config:
    """Return a test configuration for a remote Butler.

    Returns
    -------
    Config
        The test configuration
    """
    config = BASE_PATH / "data" / "config" / "dp02.yaml"

    butler_collections = [
        ButlerDataCollection(
            config=config,
            label="LSST.DP02",
            name="dp02",
            repository=HttpUrl(
                "https://example.com/api/butler/repo/dp02/butler" ".yaml"
            ),
            butler_type=ButlerType.REMOTE,
            default_instrument="LSSTCam-imSim",
        ),
    ]
    return Config(
        path_prefix="/api/sia",
        butler_data_collections=butler_collections,
    )


@pytest_asyncio.fixture
async def test_config_direct() -> Config:
    """Return a test configuration for a direct Butler.

    Returns
    -------
    Config
        The test configuration
    """
    base_path = Path(__file__).parent
    repo_path = base_path / "data" / "repo"
    config_file = base_path / "data" / "config" / "ci_hsc_gen3.yaml"

    butler_collections = [
        ButlerDataCollection(
            config=config_file,
            repository=repo_path,
            butler_type=ButlerType.DIRECT,
            label="ci_hsc_gen3",
            name="hsc",
            default_instrument="LSSTCam-imSim",
        ),
    ]

    return Config(
        butler_data_collections=butler_collections,
    )


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
