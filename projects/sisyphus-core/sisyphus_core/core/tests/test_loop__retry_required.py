"""Tests for ExecutionLoop RetryRequiredError handling."""

from __future__ import annotations

import anyio
import pytest

from sisyphus_core.utils.errors import PromptTooLongError, RetryRequiredError

pytestmark = [pytest.mark.anyio]


async def test_except_star_syntax__if_single_retry_required_error__catches_error() -> None:
    """Test that except* catches single RetryRequiredError."""
    # given
    error = RetryRequiredError("Retry needed")

    caught_error = None

    # when
    try:
        raise error
    except* RetryRequiredError as exception_group:
        caught_error = exception_group.exceptions[0]

    # then
    assert caught_error is error


async def test_except_star_syntax__if_retry_required_in_task_group__catches_error() -> None:
    """Test that except* catches RetryRequiredError from TaskGroup."""
    # given
    caught_error = None

    # when
    try:
        async with anyio.create_task_group() as task_group:

            async def raise_error() -> None:
                raise RetryRequiredError("Retry needed")

            task_group.start_soon(raise_error)
    except* RetryRequiredError as exception_group:
        caught_error = exception_group.exceptions[0]

    # then
    assert caught_error is not None
    assert isinstance(caught_error, RetryRequiredError)


async def test_except_star_syntax__if_prompt_too_long_error__catches_as_retry_required() -> None:
    """Test that PromptTooLongError is caught by except* RetryRequiredError."""
    # given
    error = PromptTooLongError("Prompt is too long")

    caught_error = None

    # when
    try:
        raise error
    except* RetryRequiredError as exception_group:
        caught_error = exception_group.exceptions[0]

    # then
    assert caught_error is error
    assert isinstance(caught_error, PromptTooLongError)
    assert isinstance(caught_error, RetryRequiredError)


async def test_except_star_syntax__if_prompt_too_long_in_task_group__catches_error() -> None:
    """Test that PromptTooLongError from TaskGroup is caught."""
    # given
    caught_error = None

    # when
    try:
        async with anyio.create_task_group() as task_group:

            async def raise_error() -> None:
                raise PromptTooLongError("Prompt is too long")

            task_group.start_soon(raise_error)
    except* RetryRequiredError as exception_group:
        caught_error = exception_group.exceptions[0]

    # then
    assert caught_error is not None
    assert isinstance(caught_error, PromptTooLongError)
    assert isinstance(caught_error, RetryRequiredError)
