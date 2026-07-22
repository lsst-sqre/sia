"""Constants for the SIA service."""

__all__ = [
    "BASE_RESOURCE_IDENTIFIER",
    "DATALINK_VERSION",
    "RESPONSEFORMATS",
    "RESULT_NAME",
    "SINGLE_PARAMS",
]

BASE_RESOURCE_IDENTIFIER = "ivo://rubin/"
"""The base resource identifier for any rubin SIA service."""

DATALINK_VERSION = "datalink-links-1.1"
"""Version of the DataLink links service to request from service discovery."""

RESPONSEFORMATS = {"votable", "application/x-votable"}
"""Set of supported response formats for the SIA service."""

RESULT_NAME = "result"
"""Name of the result file."""

SINGLE_PARAMS = {"maxrec", "responseformat"}
"""Parameters that should be treated as single values."""
