"""Constants for the tests."""

__all__ = [
    "EXCEPTION_MESSAGES",
    "TEST_BASE_URL",
]

EXCEPTION_MESSAGES = {
    "invalid_pos": "UsageFault: Unrecognized shape in POS string",
    "invalid_calib": "UsageFault: [{'type': 'enum', 'loc': "
    "('query', 'calib', 0), 'msg': 'Input should be 0, 1, 2 or 3', "
    "'input': '6', 'ctx': {'expected': '0, 1, 2 or 3'}}]",
    "invalid_time": "UsageFault: could not convert string to float:",
}

TEST_BASE_URL = "https://example.com/"
"""Base URL on which the SIA application under test is mounted."""
