"""Test data handling for SIA."""

import re

from safir.testing.data import Data

__all__ = ["SiaData"]


class SiaData(Data):
    """Test data handling for SIA."""

    def assert_votable_matches(self, seen: str, path: str) -> None:
        """Check that a VOTable matches expected output.

        This cleans the VOTable output against which the saved test data is
        matched to remove elements that may change or distract from the
        important portion of the comparison.

        Parameters
        ----------
        seen
            VOTable output to check.
        path
            Path relative to :file:`tests/data` of the expected output.

        Raises
        ------
        AssertionError
            Raised if the data doesn't match.
        """
        for regex in (r"<\?xml.*?\?>\s*", r"<!--.*?-->\s*"):
            seen = re.sub(regex, "", seen, flags=re.DOTALL)
        self.assert_text_matches(seen, path)
