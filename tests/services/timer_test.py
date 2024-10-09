"""Tests for the timer module."""

import logging
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pytest

from sia.timer import format_timedelta, timer


def test_format_timedelta_microseconds() -> None:
    """Test formatting a timedelta object with microseconds."""
    td = timedelta(microseconds=500)
    assert format_timedelta(td) == "500.00 µs"


def test_format_timedelta_minutes() -> None:
    """Test formatting a timedelta object with minutes."""
    td = timedelta(minutes=2, seconds=30)
    assert format_timedelta(td) == "2m 30.00s"


@timer
def sample_function() -> str:
    """Test the timer decorator.

    Returns
    -------
    str
        The string "Success".
    """
    return "Success"


@pytest.mark.asyncio
async def test_timer_decorator() -> None:
    """Test the timer decorator."""
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    with patch("time.monotonic", side_effect=[1.0, 3.0]):
        result = sample_function()

    assert result == "Success"
    log_output = log_capture.getvalue()
    assert "2.00 s" in log_output

    logger.removeHandler(handler)
