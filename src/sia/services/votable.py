"""Module with relevant class needed to convert a VOTableFile object to a
string.
"""

import io

from astropy.io.votable.tree import VOTableFile

__all__ = ["VotableConverterService"]


class VotableConverterService:
    """A class to convert a VOTableFile object to a string.

    Attributes
    ----------
    votable : VOTableFile
        The VOTableFile object to convert.
    """

    def __init__(self, votable: VOTableFile) -> None:
        self.votable = votable

    def to_string(self) -> str:
        """Convert the VOTableFile object to a string.

        Returns
        -------
        str
            The VOTableFile object as a string.

        """
        with io.BytesIO() as output:
            self.votable.to_xml(output)
            return output.getvalue().decode("utf-8")
