"""Constants for the SIA service."""

__all__ = ["RESPONSEFORMATS", "RESULT_NAME", "SINGLE_PARAMS"]

RESPONSEFORMATS = {"votable", "application/x-votable"}
"""List of supported response formats for the SIA service."""

RESULT_NAME = "result"
"""The name of the result file."""

SINGLE_PARAMS = {
    "maxrec",
    "responseformat",
}
"""Parameters that should be treated as single values."""
