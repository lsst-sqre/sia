"""Dependency for the availability service."""

from vo_models.vosi.availability import Availability

from ..config import config
from ..services.availability import AvailabilityService


async def get_availability_dependency() -> Availability:
    """Return the availability of the service.

    Returns
    -------
    Availability
        The availability of the service.
    """
    return await AvailabilityService(config=config).get_availability()
