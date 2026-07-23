"""Models used to populate the service self-description."""

from dataclasses import dataclass, fields

from .sia_query_params import BandInfo

__all__ = ["SelfDescription"]


@dataclass
class SelfDescription:
    """Parameters for the SIA service self-description.

    The self-description is returned for ``MAXREC=0`` query responses and
    contains metadata about the service. This model holds the parameters for
    that response and is passed as context variables for the
    :file:`templates/self-description.xml` template.

    This metadata is specific to a Butler data collection (called a dataset in
    service discovery).
    """

    instruments: list[str]
    """Known instruments."""

    collections: list[str]
    """Known collection names."""

    resource_identifier: str
    """Identifier of the resource."""

    facility_name: str
    """Name of the facility."""

    bands: list[BandInfo]
    """Spectral band information."""

    dataproduct_subtypes: list[str]
    """Data product subtypes available in this collection."""

    def to_dict(self) -> dict[str, str | list[BandInfo] | list[str]]:
        """Convert to a dictionary suitable for use as template parameters."""
        return {f.name: getattr(self, f.name) for f in fields(self)}
