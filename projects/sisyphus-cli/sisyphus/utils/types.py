"""Common type definitions for Sisyphus."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentMessage:
    """Unified message format."""

    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """Agent configuration."""

    agent_type: str  # 'claude', 'opencode'
    model: str | None
    prompt: tuple[str, str | None]  # (base_prompt, extra_prompt)
    binary: Path | None
    sdk_options: dict[str, Any] = field(default_factory=dict)
    opencode_server_url: str | None = None
