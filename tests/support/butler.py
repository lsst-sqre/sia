"""Support module for mockign a Butler."""

from collections.abc import Iterator
from typing import Any
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import astropy
from lsst.daf.butler import Butler, LabeledButlerFactory
from lsst.resources import ResourcePath

__all__ = ["MockButlerQueryService", "patch_siav2_query"]


class MockButlerQueryService:
    @staticmethod
    def siav2_query() -> astropy.io.votable.tree.VOTableFile:
        """Create a mock ObsCore VOTable.

        Returns
        -------
        astropy.io.votable.tree.VOTableFile
            The mock ObsCore VOTable.
        """
        from astropy.io.votable import from_table
        from astropy.table import Table

        # Create an Astropy Table with Obscore columns
        t = Table(
            names=(
                "dataproduct_type",
                "s_ra",
                "s_dec",
                "s_fov",
                "t_min",
                "t_max",
                "em_min",
                "em_max",
                "o_ucd",
                "access_url",
                "access_format",
                "obs_publisher_did",
            ),
            dtype=(
                "str",
                "float",
                "float",
                "float",
                "str",
                "str",
                "float",
                "float",
                "str",
                "str",
                "str",
                "str",
            ),
        )

        t.add_row(
            (
                "image",
                180.0,
                -30.0,
                0.1,
                "2020-01-01",
                "2020-01-02",
                4.0e-7,
                7.0e-7,
                "phot.flux",
                "http://example.com/image.fits",
                "application/fits",
                "ivo://example/123",
            )
        )

        return from_table(t)


__all__ = ["MockButler", "patch_butler"]


class MockDatasetRef:
    """Mock of a Butler DatasetRef."""

    def __init__(self, uuid: UUID, dataset_type: str) -> None:
        self.uuid = uuid
        self.datasetType = self
        self.name = dataset_type


class MockButler(Mock):
    """Mock of Butler for testing."""

    def __init__(self) -> None:
        super().__init__(spec=Butler)
        self.uuid = uuid4()
        self.is_raw = False
        self.mock_uri: str | None = None

    def _generate_mock_uri(self, ref: MockDatasetRef) -> str:
        if self.mock_uri is None:
            return f"s3://some-bucket/{ref.uuid!s}"
        return self.mock_uri

    def _get_child_mock(self, /, **kwargs: Any) -> Mock:
        return Mock(**kwargs)

    def get_dataset(self, uuid: UUID) -> MockDatasetRef | None:
        dataset_type = "raw" if self.is_raw else "calexp"
        if uuid == self.uuid:
            return MockDatasetRef(uuid, dataset_type)
        else:
            return None

    def getURI(self, ref: MockDatasetRef) -> ResourcePath:  # noqa: N802
        resource_path = ResourcePath(self._generate_mock_uri(ref))
        # 'size' does I/O, so mock it out
        mock = patch.object(resource_path, "size").start()
        mock.return_value = 1234
        return resource_path


def patch_butler() -> Iterator[MockButler]:
    """Mock out Butler for testing."""
    mock_butler = MockButler()
    with patch.object(LabeledButlerFactory, "create_butler") as mock:
        mock.return_value = mock_butler
        yield mock_butler


def patch_siav2_query() -> Iterator[MockButlerQueryService]:
    """Mock out Butler siav2_query for testing."""
    mock_siav2_query = MockButlerQueryService()
    with patch("sia.handlers.external.siav2_query") as mock:
        mock.return_value = mock_siav2_query.siav2_query()
        yield mock_siav2_query
