"""Service for checking the availability of the system."""

from httpx import AsyncClient, HTTPError
from vo_models.vosi.availability import Availability

from ..dependencies.butler import butler_factory_dependency
from ..models.data_collections import ButlerDataCollection


class AvailabilityService:
    """Service for checking the availability of the system."""

    def __init__(self, collection: ButlerDataCollection) -> None:
        self._collection = collection

    async def get_availability(self) -> Availability:
        """Check the availability of the system.

        Returns
        -------
        Availability
            The availability of the service.
        """
        name = self._collection.name
        butler_url = await butler_factory_dependency.get_butler_url(name)
        if not butler_url:
            note = f"Unknown collection {self._collection.name}"
            return Availability(note=[note], available=False)

        async with AsyncClient() as client:
            try:
                r = await client.get(butler_url)
                r.raise_for_status()
                return Availability(available=True)
            except HTTPError as exc:
                return Availability(note=[str(exc)], available=False)
