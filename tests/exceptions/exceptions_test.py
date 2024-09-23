"""Tests for the Exceptions module."""

import pytest
from fastapi import FastAPI

from sia.exceptions import (
    DefaultFaultError,
    FatalFaultError,
    TransientFaultError,
    UsageFaultError,
    votable_exception_handler,
)

app = FastAPI()
app.add_exception_handler(Exception, votable_exception_handler)


@pytest.mark.asyncio
async def test_usage_fault() -> None:
    """Test the UsageFault exception."""
    exc = UsageFaultError("Test usage fault")
    assert str(exc) == "UsageFault: Test usage fault"
    assert exc.status_code == 400


@pytest.mark.asyncio
async def test_transient_fault() -> None:
    """Test the TransientFault exception."""
    exc = TransientFaultError("Test transient fault")
    assert str(exc) == "TransientFault: Test transient fault"
    assert exc.status_code == 400


@pytest.mark.asyncio
async def test_fatal_fault() -> None:
    """Test the FatalFault exception."""
    exc = FatalFaultError("Test fatal fault")
    assert str(exc) == "FatalFault: Test fatal fault"
    assert exc.status_code == 400


@pytest.mark.asyncio
async def test_default_fault() -> None:
    """Test the DefaultFault exception."""
    exc = DefaultFaultError("Test default fault")
    assert str(exc) == "DefaultFault: Test default fault"
    assert exc.status_code == 400
