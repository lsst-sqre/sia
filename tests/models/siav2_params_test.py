"""Tests for cutout parameter models."""

from __future__ import annotations

import pytest

from vosiav2.models.common import CaseInsensitiveEnum
from vosiav2.models.siav2_query_params import (
    CalibLevel,
    DPType,
    Polarization,
    Shape,
    SIAv2QueryParams,
)


@pytest.mark.asyncio
async def test_case_insensitive_enum() -> None:
    class TestEnum(CaseInsensitiveEnum):
        A = "a"
        B = "b"

    assert TestEnum("a") == TestEnum.A
    assert TestEnum("A") == TestEnum.A
    assert TestEnum("b") == TestEnum.B
    assert TestEnum("B") == TestEnum.B

    with pytest.raises(ValueError, match="'c' is not a valid TestEnum"):
        TestEnum("c")


@pytest.mark.asyncio
async def test_shape_enum() -> None:
    assert Shape("circle") == Shape.CIRCLE
    assert Shape("RANGE") == Shape.RANGE
    assert Shape("Polygon") == Shape.POLYGON

    with pytest.raises(ValueError, match="'square' is not a valid Shape"):
        Shape("square")


@pytest.mark.asyncio
async def test_dptype_enum() -> None:
    assert DPType("image") == DPType.IMAGE
    assert DPType("CUBE") == DPType.CUBE

    with pytest.raises(ValueError, match="'video' is not a valid DPType"):
        DPType("video")


@pytest.mark.asyncio
async def test_polarization_enum() -> None:
    assert Polarization("i") == Polarization.I
    assert Polarization("RR") == Polarization.RR
    assert Polarization("xy") == Polarization.XY

    with pytest.raises(ValueError, match="'Z' is not a valid Polarization"):
        Polarization("Z")


@pytest.mark.asyncio
async def test_siav2params_initialization() -> None:
    params = SIAv2QueryParams(
        pos=["CIRCLE 0 1 1"],
        q_format=["application/fits"],
        time=["55 55"],
        band=["0.1 10.0"],
        pol=[Polarization("I"), Polarization("Q")],
        fov=["1.0 2.0"],
        spatres=["0.1 0.2"],
        exptime=["-Inf 60"],
        timeres=["-Inf 1.0"],
        specrp=["1000 2000"],
        q_id=["obs_id_1"],
        dptype=[DPType("image")],
        calib=[CalibLevel(0), CalibLevel(1), CalibLevel(2)],
        target=["M31"],
        collection=["HST"],
        facility=["HST"],
        instrument=["ACS"],
        maxrec=10,
        responseformat="application/x-votable+xml",
    )

    assert params.pos == ["CIRCLE 0 1 1"]
    assert params.q_format == ["application/fits"]
    assert params.time == ["55 55"]
    assert params.band == ["0.1 10.0"]
    assert params.pol == [Polarization("I"), Polarization("Q")]
    assert params.fov == ["1.0 2.0"]
    assert params.spatres == ["0.1 0.2"]
    assert params.exptime == ["-Inf 60"]
    assert params.timeres == ["-Inf 1.0"]
    assert params.specrp == ["1000 2000"]
    assert params.q_id == ["obs_id_1"]
    assert params.dptype == [DPType("image")]
    assert params.calib == [0, 1, 2]
    assert params.target == ["M31"]
    assert params.collection == ["HST"]
    assert params.facility == ["HST"]
    assert params.instrument == ["ACS"]
    assert params.maxrec == 10
    assert params.responseformat == "application/x-votable+xml"


@pytest.mark.asyncio
async def test_siav2params_default_values() -> None:
    params = SIAv2QueryParams()

    assert params.pos is None
    assert params.q_format is None
    assert params.time is None
    assert params.band is None
    assert params.pol is None
    assert params.fov is None
    assert params.spatres is None
    assert params.exptime is None
    assert params.timeres is None
    assert params.specrp is None
    assert params.q_id is None
    assert params.dptype is None
    assert params.calib is None
    assert params.target is None
    assert params.collection is None
    assert params.facility is None
    assert params.instrument is None
    assert params.maxrec is None
    assert params.responseformat is None


@pytest.fixture
def sample_siav2params() -> SIAv2QueryParams:
    return SIAv2QueryParams(
        pos=["CIRCLE 0 1 1 1"],
        q_format=["application/fits"],
        time=["55"],
        band=["0.1 10.0"],
        pol=[Polarization("I"), Polarization("Q")],
        fov=["1.0 2.0"],
        spatres=["0.1 0.2"],
        exptime=["-Inf 60"],
        timeres=["-Inf 1.0"],
        specrp=["1000 2000"],
        q_id=["obs_id_1"],
        dptype=[DPType("image")],
        calib=[CalibLevel(0), CalibLevel(1), CalibLevel(2)],
        target=["M31"],
        collection=["HST"],
        facility=["HST"],
        instrument=["ACS"],
        maxrec=10,
        responseformat="application/x-votable+xml",
    )
