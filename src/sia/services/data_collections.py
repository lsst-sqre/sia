"""Data collection helper service."""

from dataclasses import dataclass

from ..config import Config
from ..models.data_collections import ButlerDataCollection


@dataclass
class DataCollectionService:
    """Data Collection service class."""

    config: Config
    """The configuration object for the data collection."""

    def _get_data_collection(
        self,
        *,
        key: str,
        value: str,
        attribute: str,
    ) -> ButlerDataCollection:
        """Return the Data collection for the given attribute and value.

        Parameters
        ----------
        key
            The name of the attribute being searched (for error messages).
        value
            The value to search for.
        attribute
            The attribute of ButlerDataCollection to match against.

        Returns
        -------
        ButlerDataCollection
            The Butler Data collection.

        Raises
        ------
        ValueError
            If the value is empty.
        KeyError
            If the value is not found in the Data collections.
        """
        if not value:
            raise ValueError(f"{key.capitalize()} is required.")

        for collection in self.config.butler_data_collections:
            if getattr(collection, attribute).upper() == value.upper():
                return collection

        raise KeyError(
            f"{key.capitalize()} {value} not found in Data collections."
        )

    def get_data_collection_by_label(
        self,
        *,
        label: str,
    ) -> ButlerDataCollection:
        """Return the Data collection URL for the given label.

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
        ValueError
            No label was provided
        KeyError
            If the label is not found in the Data collections.
        """
        return self._get_data_collection(
            key="label", value=label, attribute="label"
        )

    def get_data_collection_by_name(
        self,
        *,
        name: str,
    ) -> ButlerDataCollection:
        """Return the Data collection URL for the given name.

        Parameters
        ----------
        name
            The name of the data collection.

        Returns
        -------
        ButlerDataCollection
            The Butler Data collection.

        Raises
        ------
        KeyError
            If the label is not found in the Data collections.

        UsageFaultError
            If the label is not found in the Data collections.
        """
        return self._get_data_collection(
            key="name", value=name, attribute="name"
        )

    def get_data_repositories(self) -> dict[str, str]:
        """Read the Data repositories from config and return a dictionary
        mapping labels to repository URLs.
        This is used to populate the LabeledButlerFactory.

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
