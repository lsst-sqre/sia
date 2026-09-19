"""Data collection models."""

from dataclasses import dataclass
from typing import Annotated

from pydantic import Field


@dataclass
class ButlerDataCollection:
    """Model to represent a Remote Butler data collection."""

    config: Annotated[
        str,
        Field(
            title="ObsCore configuration",
            description="Config path or URL to obscore config for collection",
            examples=[
                "https://example.com/butler-repo/path/to/local/dp02.yaml",
                "/path/to/local/butler/dp02.yaml",
            ],
        ),
    ]

    name: Annotated[
        str,
        Field(
            title="Name of Butler collection",
            description=(
                "The name for this Butler collection. This value is used to"
                " identify the collection in API URLs. For example, a name of"
                " 'dp02' would be used in the URL '/api/sia/dp02/query'."
            ),
            examples=["dp02"],
        ),
    ]
