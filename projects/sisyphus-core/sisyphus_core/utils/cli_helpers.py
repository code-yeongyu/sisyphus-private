"""CLI helper utilities for agent creation and configuration."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, cast
from urllib.parse import urlparse

import typer

from sisyphus_core.agents.claude import ClaudeAgent
from sisyphus_core.agents.opencode import OpenCodeAgent
from sisyphus_core.utils.theme import ThemeName, detect_system_theme

if TYPE_CHECKING:
    from sisyphus_core.agents.base import Agent


class ThemeOption(str, Enum):
    """TUI theme options."""

    SYSTEM = "system"
    MOCHA = "mocha"
    LATTE = "latte"


def validate_url(url: str) -> str:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        Validated URL

    Raises:
        typer.BadParameter: If URL format is invalid
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise typer.BadParameter(f"Invalid URL: {url}")
    return url


def resolve_theme(option: ThemeOption) -> ThemeName:
    """Convert ThemeOption to actual theme name.

    Args:
        option: Theme option from CLI

    Returns:
        "mocha" or "latte"
    """
    match option:
        case ThemeOption.SYSTEM:
            return detect_system_theme()
        case ThemeOption.MOCHA:
            return "mocha"
        case _:
            return "latte"


def resolve_binary(common: Path | None, specific: Path | None) -> Path | None:
    """Resolve binary path (specific > common > None).

    Args:
        common: Common binary path
        specific: Specific binary path

    Returns:
        Resolved binary path (specific takes priority, fallback to common)
    """
    return specific if specific is not None else common


def create_agent(
    agent_spec: str,
    sdk_options_json: str | None,
    binary_path: Path | None,
    opencode_url: str | None,
    cwd: Path | None = None,
    system_prompt: str | None = None,
) -> Agent:
    """Create agent from agent spec.

    Args:
        agent_spec: "claude" | "claude:sonnet" | "opencode"
        sdk_options_json: JSON string (SDK options)
        binary_path: Binary path (auto-detect if None)
        opencode_url: OpenCode server URL (auto-start if None)
        cwd: Working directory for Claude Agent SDK (auto-detect if None)
        system_prompt: Optional system prompt for Claude agent

    Returns:
        Agent instance

    Raises:
        typer.BadParameter: If agent type is unknown or JSON is invalid
    """
    if ":" in agent_spec:
        agent_type, model = agent_spec.split(":", 1)
    else:
        agent_type, model = agent_spec, None

    try:
        sdk_options: dict[str, object] = json.loads(sdk_options_json) if sdk_options_json else {}
    except json.JSONDecodeError as e:
        raise typer.BadParameter(f"Invalid JSON in SDK options: {e}") from e

    if model:
        sdk_options["model"] = model

    match agent_type:
        case "claude":
            working_dir = str(cwd) if cwd else str(Path.cwd())
            return cast(
                "Agent",
                ClaudeAgent(model=model, sdk_options=sdk_options, cwd=working_dir, system_prompt=system_prompt),
            )
        case "opencode":
            working_dir = str(cwd) if cwd else str(Path.cwd())
            return cast("Agent", OpenCodeAgent(binary=binary_path, server_url=opencode_url, cwd=working_dir))
        case _:
            raise typer.BadParameter(f"Unknown agent type: {agent_type}")
