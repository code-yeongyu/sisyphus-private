"""DEPRECATED: v2.1 formatting utilities.

All v2.1 formatting functions have been removed in v3.0.
This module is kept for backward compatibility only.
"""

from __future__ import annotations

from enum import Enum


class OutputFormat(Enum):
    PLAIN = "plain"
    RICH = "rich"
