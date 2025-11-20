"""Session limit handling utilities."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import anyio

if TYPE_CHECKING:
    from sisyphus_core.ui.base import UIProtocol


async def sleep_until_reset(
    reset_time: datetime,
    ui: UIProtocol | None = None,
) -> None:
    """Sleep until session reset time with periodic UI updates.

    Args:
        reset_time: The datetime to sleep until
        ui: Optional UI protocol for status updates
    """
    now = datetime.now().astimezone()
    if reset_time <= now:
        if ui:
            await ui.show_status("Reset time has already passed, continuing...")
        return

    total_seconds = (reset_time - now).total_seconds()

    if ui:
        reset_str = reset_time.strftime("%Y-%m-%d %H:%M:%S")
        await ui.show_status(f"⚠️  Session limit reached. Sleeping until {reset_str} ({int(total_seconds)}s)")

    remaining = total_seconds
    while remaining > 0:
        sleep_chunk = min(remaining, 60)
        await anyio.sleep(sleep_chunk)
        remaining -= sleep_chunk

        if remaining > 0 and ui:
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            seconds = int(remaining % 60)

            if hours > 0:
                time_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                time_str = f"{minutes}m {seconds}s"
            else:
                time_str = f"{seconds}s"

            await ui.show_status(f"Waiting for session reset... {time_str} remaining")

    if ui:
        await ui.show_status("✅ Session limit reset time reached, continuing...")


async def sleep_until_next_hour(
    ui: UIProtocol | None = None,
) -> None:
    """Sleep until the next hour (top of the hour) with periodic UI updates.

    Args:
        ui: Optional UI protocol for status updates
    """
    now = datetime.now().astimezone()
    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    total_seconds = (next_hour - now).total_seconds()

    if ui:
        reset_str = next_hour.strftime("%Y-%m-%d %H:%M:%S")
        await ui.show_status(f"⚠️  Session limit reached. Sleeping until next hour {reset_str} ({int(total_seconds)}s)")

    remaining = total_seconds
    while remaining > 0:
        sleep_chunk = min(remaining, 60)
        await anyio.sleep(sleep_chunk)
        remaining -= sleep_chunk

        if remaining > 0 and ui:
            minutes = int((remaining % 3600) // 60)
            seconds = int(remaining % 60)

            if minutes > 0:
                time_str = f"{minutes}m {seconds}s"
            else:
                time_str = f"{seconds}s"

            await ui.show_status(f"Waiting for next hour... {time_str} remaining")

    if ui:
        await ui.show_status("✅ Next hour reached, continuing...")
