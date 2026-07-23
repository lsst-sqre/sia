"""Generate the self-description of the SIA service."""

import asyncio

from lsst.daf.butler import Butler
from lsst.dax.obscore import ExporterConfig

from ..constants import BASE_RESOURCE_IDENTIFIER
from ..models.description import SelfDescription
from ..models.sia_query_params import BandInfo

__all__ = ["SelfDescriptionService"]


class SelfDescriptionService:
    """Generate the self-description of the SIA service.

    The self-description is returned for ``MAXREC=0`` query responses and
    contains metadata about the service. It is specific to a Butler data
    collection (called a dataset in service discovery).

    Parameters
    ----------
    butler
        Butler instance for this collection.
    obscore_config
        ObsCore exporter configuration for this collection.
    """

    def __init__(self, butler: Butler, obscore_config: ExporterConfig) -> None:
        self._butler = butler
        self._obscore_config = obscore_config

    async def get_description(self) -> SelfDescription:
        """Return self-description metadata for the SIAv2 service.

        Returns
        -------
        SelfDescription
            Self-description metadata suitable for producing a templated
            response.
        """
        instruments = await asyncio.to_thread(
            self._butler.query_dimension_records, "instrument"
        )

        label = self._obscore_config.obs_collection
        bands = [
            BandInfo(label=f"Rubin band {n}", low=low, high=high)
            for n, (low, high) in self._obscore_config.spectral_ranges.items()
            if low is not None and high is not None
        ]
        subtypes = {
            c.dataproduct_subtype
            for c in self._obscore_config.dataset_types.values()
            if c.dataproduct_subtype is not None
        }

        return SelfDescription(
            instruments=[i.name for i in instruments],
            collections=[label] if label else [],
            resource_identifier=f"{BASE_RESOURCE_IDENTIFIER}/{label}",
            facility_name=self._obscore_config.facility_name.strip(),
            bands=bands,
            dataproduct_subtypes=list(subtypes),
        )
