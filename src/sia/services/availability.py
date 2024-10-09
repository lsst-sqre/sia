"""Service for checking the availability of the system."""

from abc import ABC, abstractmethod

from httpx import AsyncClient
from vo_models.vosi.availability import Availability

from ..config import Config
from ..exceptions import FatalFaultError
from ..models.butler_type import ButlerType
from .data_collections import DataCollectionService


class AvailabilityChecker(ABC):
    """Base class for availability checkers."""

    @abstractmethod
    async def check_availability(self, *, config: Config) -> Availability:
        """Check the availability of the service.

        Parameters
        ----------
        config
            The app configuration

        Returns
        -------
        Availability
            The availability of the service.
        """


class DirectButlerAvailabilityChecker(AvailabilityChecker):
    """Checker for the availability of the direct Butler based service."""

    async def check_availability(self, *, config: Config) -> Availability:
        """Check the availability of the direct Butler based service.
        For now this just returns Available(True). We could improve this by
        checking if we can create a valid Butler with the config provided.

        Parameters
        ----------
        config
            The app configuration

        Returns
        -------
        Availability
            The availability of the service if using direct Butler.
        """
        return Availability(available=True)


class RemoteButlerAvailabilityChecker(AvailabilityChecker):
    """Checker for the availability of a remote Butler based service."""

    async def check_availability(self, *, config: Config) -> Availability:
        """Check the availability of a remote Butler based service.
        This checks if the remote Butler is available by sending a GET request
        to the root URL of the remote Butler.

        Parameters
        ----------
        config
            The app configuration

        Returns
        -------
        Availability
            The availability of the remote Butler based service.
        """
        async with AsyncClient() as client:
            try:
                default_collection = DataCollectionService(
                    config=config
                ).get_default_collection()

                repository = default_collection.repository
                r = await client.get(str(repository)) if repository else None
                if not r:
                    return Availability(available=False)

                return Availability(available=r.status_code == 200)

            except (KeyError, ValueError, FatalFaultError) as exc:
                return Availability(note=[str(exc)], available=False)


class AvailabilityService:
    """Service for checking the availability of the system."""

    def __init__(self, *, config: Config) -> None:
        self.config = config
        self.checkers: dict[ButlerType, AvailabilityChecker] = {
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
        checker = self.checkers.get(self.config.butler_type)
        if checker:
            return await checker.check_availability(config=self.config)
        else:
            return Availability(available=True)
