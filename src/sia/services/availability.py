"""Service for checking the availability of the system."""

from httpx import AsyncClient, HTTPError
from vo_models.vosi.availability import Availability

__all__ = ["AvailabilityService"]


class AvailabilityService:
    """Service for checking the availability of the system.

    Parameters
    ----------
    http_client
        HTTP client to use for health checks.
    """

    def __init__(self, http_client: AsyncClient) -> None:
        self._client = http_client

    async def get_availability(self, butler_url: str) -> Availability:
        """Check the availability of the system.

        Parameters
        ----------
        butler_url
            URL to check the health of the underlying Butler server.

        Returns
        -------
        Availability
            The availability of the service.
        """
        try:
            r = await self._client.get(butler_url)
            r.raise_for_status()
            return Availability(available=True)
        except HTTPError as exc:
            return Availability(note=[str(exc)], available=False)
