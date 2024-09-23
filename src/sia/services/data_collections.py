"""Data collection helper service."""

from dataclasses import dataclass

from ..config import Config
from ..exceptions import FatalFaultError, UsageFaultError
from ..models.data_collections import ButlerDataCollection


@dataclass
class DataCollectionService:
    """Data Collection service class."""

    config: Config

    def get_default_collection(
        self,
    ) -> ButlerDataCollection:
        """Return the default Data collection.


        Returns
        -------
        ButlerDataCollection
            The default Butler Data collection.

        Raises
        ------
        FatalFaultError
            If no default Data collection is found.
        """
        for collection in self.config.butler_data_collections:
            if collection.default:
                return collection

        raise FatalFaultError(
            detail="No default Collection found. Please configure a default."
        )

    def get_data_collection(
        self,
        *,
        label: str | None,
    ) -> ButlerDataCollection:
        """Return the Data collection URL for the given label.
        If no label is provided, return the default data collection.

        Parameters
        ----------
        label
            The label of the data collection.


        Returns
        -------
        ButlerDataCollection
            The Butler Data collection.

        Raises
        ------
        KeyError
            If the label is not found in the Data collections.
        FatalFaultError
            If no Data collections are configured.
        UsageFaultError
            If the label is not found in the Data collections.
        """
        if not label:
            if len(self.config.butler_data_collections) == 0:
                raise FatalFaultError(
                    detail="No Data Collections configured. Please configure "
                    "at least one Data collection."
                )
            # Return the first one if no label is provided
            return self.config.butler_data_collections[0]

        # Find the Data collection with the given label
        # Do a case-sensitive search
        for collection in self.config.butler_data_collections:
            if collection.label == label:
                return collection

        raise UsageFaultError(
            detail=f"Label {label} not found in Data collections."
        )

    def get_data_repositories(self) -> dict[str, str]:
        """Read the Data repositories from config and return a dictionary
        mapping labels to repository URLs.

        Returns
        -------
        dict
            A dictionary mapping labels to repository URLs.
        """
        butler_repos = {}

        for collection in self.config.butler_data_collections:
            label = collection.label
            repository = collection.repository

            if label and repository:
                butler_repos[label] = str(repository)

        return butler_repos
