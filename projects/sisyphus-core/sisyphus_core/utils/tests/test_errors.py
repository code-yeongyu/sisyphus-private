"""Tests for sisyphus.utils.errors module."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sisyphus_core.utils.errors import PromptTooLongError, RetryRequiredError, SessionLimitError, SisyphusError

pytestmark = [pytest.mark.anyio]


async def test_retry_required_error__is_sisyphus_error() -> None:
    """Test that RetryRequiredError is a SisyphusError."""
    # given
    error = RetryRequiredError("Retry needed")

    # when
    is_sisyphus_error = isinstance(error, SisyphusError)

    # then
    assert is_sisyphus_error is True


async def test_session_limit_error__is_retry_required_error() -> None:
    """Test that SessionLimitError is a RetryRequiredError (backward compatibility)."""
    # given
    error = SessionLimitError("Session limit reached")

    # when
    is_retry_required = isinstance(error, RetryRequiredError)

    # then
    assert is_retry_required is True


async def test_prompt_too_long_error__is_retry_required_error() -> None:
    """Test that PromptTooLongError is a RetryRequiredError."""
    # given
    error = PromptTooLongError("Prompt is too long")

    # when
    is_retry_required = isinstance(error, RetryRequiredError)

    # then
    assert is_retry_required is True


async def test_session_limit_error__preserves_reset_time() -> None:
    """Test that SessionLimitError preserves reset_time attribute."""
    # given
    reset_time = datetime(2025, 10, 21, 15, 30, 0, tzinfo=UTC)
    error = SessionLimitError("Session limit reached", reset_time=reset_time)

    # when
    retrieved_reset_time = error.reset_time

    # then
    assert retrieved_reset_time == reset_time
    assert retrieved_reset_time is reset_time
