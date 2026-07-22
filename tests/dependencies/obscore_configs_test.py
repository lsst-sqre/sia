"""Tests for SIA FastAPI dependencies."""

from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from httpx import AsyncClient
from lsst.dax.obscore import ExporterConfig
from rubin.repertoire import Discovery

from sia.constants import DATALINK_VERSION
from sia.dependencies.obscore_configs import obscore_config_dependency


@pytest.mark.asyncio
async def test_obscore_config(
    app: FastAPI, client: AsyncClient, mock_discovery: Discovery
) -> None:
    """Test that the DataLink URL is replaced in the ObsCore config."""
    datalink = mock_discovery.datasets["dp02"].services["datalink"]
    datalink_url = str(datalink.versions[DATALINK_VERSION].url)

    @app.get("/{collection_name}/test-obscore")
    async def obscore(
        obscore_config: Annotated[
            ExporterConfig, Depends(obscore_config_dependency)
        ],
    ) -> ExporterConfig:
        return obscore_config

    r = await client.get("/dp02/test-obscore")
    assert r.status_code == 200
    exporter_config = ExporterConfig.model_validate(r.json())
    for settings in exporter_config.dataset_types.values():
        assert settings.datalink_url_fmt
        assert settings.datalink_url_fmt.startswith(datalink_url + "?")
