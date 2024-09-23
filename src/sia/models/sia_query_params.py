"""SIA query parameters models."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from enum import Enum
from numbers import Integral
from typing import Annotated, Any, TypeVar, cast

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
        """Convert the query parameters to the format expected by the
        specific Butler type.
        """


@dataclass
class SIAQueryParams(BaseQueryParams):
    """A class to represent the parameters for an SIA query.

    Attributes
    ----------
    pos : Optional[list[str]]
        Positional region(s) to be searched.
    q_format : Optional[list[str]]
        Image format(s).
    time : Optional[list[str]]
        Time interval(s) to be searched.
    band : Optional[list[str]]
        Band interval(s) to be searched.
    pol : Optional[list[Polarization]]
        Polarization state(s) to be searched.
    fov : Optional[list[str]]
        Range(s) of field of view.
    spatres : Optional[list[str]]
        Range(s) of spatial resolution.
    exptime : Optional[list[str]]
        Range(s) of exposure times.
    timeres : Optional[list[str]]
        Range(s) of temporal resolution.
    specrp : Optional[list[str]]
        Range(s) of spectral resolving power.
    q_id : Optional[list[str]]
        Identifier of dataset(s). (Case insensitive)
    dptype : Optional[list[DPType]]
        Type of data (dataproduct_type).
    calib : Optional[list[CalibLevel]]
        Calibration level of the data.
    target : Optional[list[str]]
        Name of the target.
    collection : Optional[list[str]]
        Name of the data collection.
    facility : Optional[list[str]]
        Name of the facility.
    instrument : Optional[list[str]]
        Name of the instrument.
    maxrec : Optional[int]
        Maximum number of records in the response.
    responseformat : Optional[str]
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
            examples=["320 -0.1 10"],
        ),
    ] = None

    q_format: Annotated[
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
            examples=["2021-01-01T00:00:00Z 2021-01-02T00:00:00Z"],
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

    q_id: Annotated[
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
    def from_dict(cls, data: dict[str, Any]) -> "SIAQueryParams":
        """Create an instance of SIAQueryParams from a dictionary.

        This method handles renaming 'id' to 'q_id' and 'format' to 'q_format'.

        Parameters
        ----------
        data
            The dictionary containing the query parameters.

        Returns
        -------
        SIAQueryParams
            Instance of SIAQueryParams initialized with the provided data.
        """
        if "id" in data:
            data["q_id"] = data.pop("id")

        if "format" in data:
            data["q_format"] = data.pop("format")

        return cls(**data)

    @classmethod
    def validate_enum_list(
        cls,
        value: str | int | T | list[str | int | T] | list[T] | None,
        enum_class: type[T],
        field_name: str,
    ) -> list[T] | None:
        """Validate a list of enum values.

        Parameters
        ----------
        value
            The value to validate.
        enum_class
            The enumeration class.
        field_name
            The field name

        Returns
        -------
        list
            The validated list of enum values.

        Raises
        ------
        ValueError
            If the value is not a list.
        """
        if value is None:
            return None
        if not isinstance(value, list):
            value = [value]

        try:
            return [
                enum_class(item) if isinstance(item, str | int) else item
                for item in value
            ]
        except ValueError as exc:
            raise UsageFaultError(
                detail=f"Validation of '{field_name}' failed"
            ) from exc

    def __post_init__(self) -> None:
        """Validate the query parameters."""
        self.pol = self.validate_enum_list(
            value=self.pol, enum_class=Polarization, field_name="pol"
        )
        self.dptype = self.validate_enum_list(
            value=self.dptype, enum_class=DPType, field_name="dptype"
        )
        self.calib = self.validate_enum_list(
            value=self.calib, enum_class=CalibLevel, field_name="calib"
        )

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
        dict
            The query parameters as a dictionary.
        """
        return SIAv2Parameters.from_siav2(
            instrument=self.instrument or (),
            pos=self.pos or (),
            time=self.time or (),
            band=self.band or (),
            exptime=self.exptime or (),
            calib=self._convert_calib(calib=self.calib),
            maxrec=str(self.maxrec) if self.maxrec is not None else None,
        )

    @staticmethod
    def _convert_calib(calib: list[CalibLevel] | None) -> Iterable[Integral]:
        if calib is None:
            return ()
        return cast(list[Integral], [int(level.value) for level in calib])
