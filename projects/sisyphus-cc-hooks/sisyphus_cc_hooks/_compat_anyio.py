"""Type-safe wrapper for anyio.to_thread.run_sync."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    R = TypeVar("R")

    async def run_sync[R](_func: Callable[[], R]) -> R: ...
else:
    from anyio.to_thread import run_sync as _run_sync

    run_sync = _run_sync
