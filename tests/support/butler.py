"""Support module for mockign a Butler."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, override
from unittest.mock import Mock, patch

import astropy
from astropy.io.votable import from_table
from astropy.table import Table
from lsst.daf.butler import Butler, LabeledButlerFactory
from lsst.dax.obscore import siav2

__all__ = [
    "MockButler",
    "patch_butler",
    "patch_siav2_query",
]


def mock_siav2_query() -> astropy.io.votable.tree.VOTableFile:
    """Create a mock ObsCore VOTable.

    Returns
    -------
    astropy.io.votable.tree.VOTableFile
        The mock ObsCore VOTable.
    """
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


class MockButler(Mock):
    """Mock of Butler for testing."""

    def __init__(self) -> None:
        super().__init__(spec=Butler)

    @override
    def _get_child_mock(self, /, **kwargs: Any) -> Mock:
        return Mock(**kwargs)

    def query_dimension_records(self, query: str) -> list[str]:
        record = Mock()
        record.name = "HSC"
        return [record]


@contextmanager
def patch_butler() -> Iterator[MockButler]:
    """Mock out Butler for testing."""
    mock_butler = MockButler()
    with patch.object(LabeledButlerFactory, "create_butler") as mock:
        mock.return_value = mock_butler
        yield mock_butler


@contextmanager
def patch_siav2_query() -> Iterator[None]:
    """Mock out Butler siav2_query for testing."""
    mock_votable = mock_siav2_query()
    with patch.object(siav2, "siav2_query") as mock:
        mock.return_value = mock_votable
        yield
