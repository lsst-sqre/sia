"""SIA query parameters models."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from enum import Enum
from numbers import Integral
from typing import Annotated, Any, Self, TypeVar, cast

from fastapi import Query
from lsst.dax.obscore.siav2 import SIAv2Parameters

from ..exceptions import UsageFaultError
from ..models.common import CaseInsensitiveEnum

__all__ = [
    "BaseQueryParams",
    "SIAQueryParams",
    "Shape",
    "DPType",
    "Polarization",
    "CalibLevel",
]

T = TypeVar("T", bound=Enum)


class CalibLevel(int, Enum):
    """Enumeration of possible calibration levels."""

    LEVEL0 = 0
    LEVEL1 = 1
    LEVEL2 = 2
    LEVEL3 = 3


class Shape(CaseInsensitiveEnum):
    """Enumeration of possible shapes for the POS parameter."""

    CIRCLE = "CIRCLE"
    RANGE = "RANGE"
    POLYGON = "POLYGON"


class DPType(CaseInsensitiveEnum):
    """Enumeration of possible data product types."""

    IMAGE = "IMAGE"
    CUBE = "CUBE"


class Polarization(CaseInsensitiveEnum):
    """Enumeration of possible polarization states."""

    I = "I"  # noqa: E741
    Q = "Q"
    U = "U"
    V = "V"
    RR = "RR"
    LL = "LL"
    RL = "RL"
    LR = "LR"
    XX = "XX"
    YY = "YY"
    XY = "XY"
    YX = "YX"


class BaseQueryParams(ABC):
    """Base class for query parameters."""

    @abstractmethod
    def to_butler_parameters(self) -> Any:
        """Convert the query parameters  vto the format expected by the
        specific Butler type.
        """


@dataclass
class SIAQueryParams(BaseQueryParams):
    """A class to represent the parameters for an SIA query.

    Attributes
    ----------
    pos
        Positional region(s) to be searched.
    format
        Image format(s).
    time
        Time interval(s) to be searched.
    band
        Band interval(s) to be searched.
    pol
        Polarization state(s) to be searched.
    fov
        Range(s) of field of view.
    spatres
        Range(s) of spatial resolution.
    exptime
        Range(s) of exposure times.
    timeres
        Range(s) of temporal resolution.
    specrp
        Range(s) of spectral resolving power.
    id
        Identifier of dataset(s). (Case insensitive)
    dptype
        Type of data (dataproduct_type).
    calib
        Calibration level of the data.
    target
        Name of the target.
    collection
        Name of the data collection.
    facility
        Name of the facility.
    instrument
        Name of the instrument.
    maxrec
        Maximum number of records in the response.
    responseformat
        Format of the response.

    Notes
    -----
    I have tried using Pydantic here, but as I understand there is currently
    a limitation with how FastAPI handles Pydantic models for query parameters
    with list attributes
    (See: https://github.com/fastapi/fastapi/discussions/10556)
    """

    pos: Annotated[
        list[str] | None,
        Query(
            title="pos",
            description="Positional region(s) to be searched",
            examples=["55.7467 -32.2862 0.05"],
        ),
    ] = None

    format: Annotated[
        list[str] | None,
        Query(
            title="format",
            alias="format",
            description="Response format(s)",
            examples=["application/x-votable+xml"],
        ),
    ] = None

    time: Annotated[
        list[str] | None,
        Query(
            title="time",
            description="Time interval(s) to be searched",
            examples=["60550.31803461111 60550.31838182871"],
        ),
    ] = None

    band: Annotated[
        list[str] | None,
        Query(
            title="band",
            description="Energy interval(s) to be searched",
            examples=["0.1 10.0"],
        ),
    ] = None

    pol: Annotated[
        list[Polarization] | None,
        Query(
            title="pol",
            description="Polarization state(s) to be searched",
            examples=["I", "Q"],
        ),
    ] = None

    fov: Annotated[
        list[str] | None,
        Query(
            title="fov",
            description="Range(s) of field of view",
            examples=["1.0 2.0"],
        ),
    ] = None

    spatres: Annotated[
        list[str] | None,
        Query(
            title="spatres",
            description="Range(s) of spatial resolution",
            examples=["0.1 0.2"],
        ),
    ] = None

    exptime: Annotated[
        list[str] | None,
        Query(
            title="exptime",
            description="Range(s) of exposure times",
            examples=["-Inf 60"],
        ),
    ] = None

    timeres: Annotated[
        list[str] | None,
        Query(
            title="timeres",
            description="Range(s) of temporal resolution",
            examples=["-Inf 1.0"],
        ),
    ] = None

    specrp: Annotated[
        list[str] | None,
        Query(
            title="specrp",
            description="Range(s) of spectral resolving power",
            examples=["1000 2000"],
        ),
    ] = None

    id: Annotated[
        list[str] | None,
        Query(
            title="id",
            alias="id",
            description="Identifier of dataset(s)",
            examples=["obs_id_1"],
        ),
    ] = None

    dptype: Annotated[
        list[DPType] | None,
        Query(title="dptype", description="Type of data", examples=["image"]),
    ] = None

    calib: Annotated[
        list[CalibLevel] | None,
        Query(
            title="calib",
            description="Calibration level of the data",
            examples=[0, 1, 2],
        ),
    ] = None

    target: Annotated[
        list[str] | None,
        Query(
            title="target", description="Name of the target", examples=["M31"]
        ),
    ] = None

    collection: Annotated[
        list[str] | None,
        Query(
            title="collection",
            description="Name of the data collection",
            examples=["HST"],
        ),
    ] = None

    facility: Annotated[
        list[str] | None,
        Query(
            title="facility",
            description="Name of the facility",
            examples=["HST"],
        ),
    ] = None

    instrument: Annotated[
        list[str] | None,
        Query(
            title="instrument",
            description="Name of the instrument",
            examples=["ACS"],
        ),
    ] = None

    maxrec: Annotated[
        int | None,
        Query(
            title="maxrec",
            description="Maximum number of records in the response",
            examples=[10],
        ),
    ] = None

    responseformat: Annotated[
        str | None,
        Query(
            title="reponseformat",
            description="Format of the response",
            examples=["application/x-votable+xml"],
        ),
    ] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create an instance of SIAQueryParams from a dictionary.

        Parameters
        ----------
        data
            The dictionary containing the query parameters.

        Returns
        -------
        SIAQueryParams
            Instance of SIAQueryParams initialized with the provided data.
        """
        return cls(**data)

    def all_params_none(self) -> bool:
        """Check if all params except maxrec and responseformat are None."""
        return all(
            getattr(self, attr) is None
            for attr in self.__annotations__
            if attr not in ["maxrec", "responseformat"]
        )

    def __post_init__(self) -> None:
        """Validate the form parameters."""
        # If no parameters were provided, I don't think we should run a query
        # Instead return the self-description VOTable
        if self.all_params_none():
            self.maxrec = 0

    def to_dict(self) -> dict[str, Any]:
        """Return the query parameters as a dictionary.

        Returns
        -------
        dict
            The query parameters as a dictionary.
        """
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_butler_parameters(self) -> SIAv2Parameters:
        """Convert the query parameters to SIAv2Parameters. Exclude None
        values.

        Returns
        -------
        SIAv2Parameters
            The query parameters as a dictionary.

        Raises
        ------
        UsageFaultError
            If the query parameters are invalid.
        """
        try:
            return SIAv2Parameters.from_siav2(
                instrument=self.instrument or (),
                pos=self.pos or (),
                time=self.time or (),
                band=self.band or (),
                exptime=self.exptime or (),
                calib=self._convert_calib(calib=self.calib),
                maxrec=str(self.maxrec) if self.maxrec is not None else None,
            )
        except ValueError as exc:
            raise UsageFaultError(detail=str(exc)) from exc

    @staticmethod
    def _convert_calib(calib: list[CalibLevel] | None) -> Iterable[Integral]:
        """Convert the calibration levels to integers.

        Parameters
        ----------
        calib
            The calibration levels.

        Returns
        -------
        Iterable
            The calibration levels as integers.
        """
        if calib is None:
            return ()
        return cast(list[Integral], [int(level.value) for level in calib])
