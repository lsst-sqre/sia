"""Service for checking the availability of the system."""

from httpx import AsyncClient
from vo_models.vosi.availability import Availability

from ..exceptions import FatalFaultError
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
        async with AsyncClient() as client:
            try:
                repository = self._collection.repository
                r = await client.get(str(repository)) if repository else None
                if not r:
                    return Availability(available=False)

                return Availability(available=r.status_code == 200)

            except (KeyError, ValueError, FatalFaultError) as exc:
                return Availability(note=[str(exc)], available=False)
