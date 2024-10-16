"""Service for checking the availability of the system."""

from abc import ABC, abstractmethod

from httpx import AsyncClient
from vo_models.vosi.availability import Availability

from ..exceptions import FatalFaultError
from ..models.butler_type import ButlerType
from ..models.data_collections import ButlerDataCollection


class AvailabilityChecker(ABC):
    """Base class for availability checkers."""

    @abstractmethod
    async def check_availability(
        self, *, collection: ButlerDataCollection
    ) -> Availability:
        """Check the availability of the service.

        Parameters
        ----------
        collection
            The ButlerDataCollection instance

        Returns
        -------
        Availability
            The availability of the service.
        """


class DirectButlerAvailabilityChecker(AvailabilityChecker):
    """Checker for the availability of the direct Butler based service."""

    async def check_availability(
        self, *, collection: ButlerDataCollection
    ) -> Availability:
        """Check the availability of the direct Butler based service.
        For now this just returns Available(True). We could improve this by
        checking if we can create a valid Butler with the config provided.

        Parameters
        ----------
        collection
            The ButlerDataCollection instance

        Returns
        -------
        Availability
            The availability of the service if using direct Butler.
        """
        return Availability(available=True)


class RemoteButlerAvailabilityChecker(AvailabilityChecker):
    """Checker for the availability of a remote Butler based service."""

    async def check_availability(
        self, *, collection: ButlerDataCollection
    ) -> Availability:
        """Check the availability of a remote Butler based service.
        This checks if the remote Butler is available by sending a GET request
        to the root URL of the remote Butler.

        Parameters
        ----------
        collection
            The ButlerDataCollection instance

        Returns
        -------
        Availability
            The availability of the remote Butler based service.
        """
        async with AsyncClient() as client:
            try:
                repository = collection.repository
                r = await client.get(str(repository)) if repository else None
                if not r:
                    return Availability(available=False)

                return Availability(available=r.status_code == 200)

            except (KeyError, ValueError, FatalFaultError) as exc:
                return Availability(note=[str(exc)], available=False)


class AvailabilityService:
    """Service for checking the availability of the system."""

    def __init__(self, *, collection: ButlerDataCollection) -> None:
        self._collection = collection
        self._checkers: dict[ButlerType, AvailabilityChecker] = {
            ButlerType.DIRECT: DirectButlerAvailabilityChecker(),
            ButlerType.REMOTE: RemoteButlerAvailabilityChecker(),
        }

    async def get_availability(self) -> Availability:
        """Check the availability of the system.

        Returns
        -------
        Availability
            The availability of the service.
        """
        butler_type = self._collection.butler_type
        checker = self._checkers.get(butler_type)
        if checker:
            return await checker.check_availability(
                collection=self._collection
            )
        else:
            return Availability(note=["Unknown Butler type"], available=False)
