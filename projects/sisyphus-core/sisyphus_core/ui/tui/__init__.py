# pyright: reportImportCycles=false
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sisyphus_core.ui.tui.app import TUI

__all__ = ["TUI"]


def __getattr__(name: str) -> type[TUI]:
    """Lazy import to avoid circular dependency."""
    if name == "TUI":
        from sisyphus_core.ui.tui.app import TUI as _TUI
        return _TUI
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
