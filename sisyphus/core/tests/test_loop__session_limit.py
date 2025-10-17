"""Tests for ExecutionLoop SessionLimitError handling with ExceptionGroup."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import anyio
import pytest

from sisyphus.utils.errors import SessionLimitError

pytestmark = [pytest.mark.anyio]


async def test_except_star_syntax__if_single_session_limit_error__catches_error() -> None:
    # given
    reset_time = datetime.now(UTC) + timedelta(hours=1)
    error = SessionLimitError("Session limit reached", reset_time=reset_time)

    caught_error = None

    # when
    try:
        raise error
    except* SessionLimitError as exception_group:
        caught_error = exception_group.exceptions[0]

    # then
    assert caught_error is error
    assert caught_error.reset_time == reset_time


async def test_except_star_syntax__if_session_limit_in_task_group__catches_error() -> None:
    # given
    reset_time = datetime.now(UTC) + timedelta(hours=1)

    caught_error = None

    # when
    try:
        async with anyio.create_task_group() as task_group:

            async def raise_error() -> None:
                raise SessionLimitError("Session limit", reset_time=reset_time)

            task_group.start_soon(raise_error)
    except* SessionLimitError as exception_group:
        caught_error = exception_group.exceptions[0]

    # then
    assert caught_error is not None
    assert isinstance(caught_error, SessionLimitError)
    assert caught_error.reset_time == reset_time


async def test_except_star_syntax__if_no_reset_time__catches_error_without_reset() -> None:
    # given
    error = SessionLimitError("Session limit reached", reset_time=None)

    caught_error = None

    # when
    try:
        raise error
    except* SessionLimitError as exception_group:
        caught_error = exception_group.exceptions[0]

    # then
    assert caught_error is error
    assert caught_error.reset_time is None
