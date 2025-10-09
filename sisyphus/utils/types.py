"""Common type definitions for Sisyphus."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentMessage:
    """통합 메시지 형식."""

    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """에이전트 설정."""

    agent_type: str  # 'claude', 'droid', 'opencode'
    model: str | None
    prompt: tuple[str, str | None]  # (base_prompt, extra_prompt)
    binary: Path | None
    sdk_options: dict[str, Any] = field(default_factory=dict)
    opencode_server_url: str | None = None
