"""System theme detection utilities."""

from __future__ import annotations

import platform
import subprocess
from typing import Literal

ThemeName = Literal["mocha", "latte"]


def detect_system_theme() -> ThemeName:
    """Detect system theme (macOS only).

    Returns:
        "mocha" for dark mode, "latte" for light mode or on error
    """
    if platform.system() != "Darwin":
        return "latte"

    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            check=False,
            capture_output=True,
            text=True,
            timeout=0.5,
        )
        if result.returncode == 0 and "Dark" in result.stdout:
            return "mocha"
        return "latte"
    except Exception:
        return "latte"
