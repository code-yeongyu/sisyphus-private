"""ClaudeAgent implementation using Claude Agent SDK."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
)

from sisyphus.utils.errors import SessionLimitError, SessionResumeError
from sisyphus.utils.session_limit import parse_reset_time
from sisyphus.utils.types import AgentMessage

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class ClaudeAgent:
    """Claude Agent using Claude Agent SDK with session management."""

    supports_interactive: bool = True

    def __init__(
        self,
        model: str | None = None,
        sdk_options: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ClaudeAgent.

        Args:
            model: Optional model override (e.g., "claude-sonnet-4-5-20250929")
            sdk_options: Optional SDK options to override defaults
        """
        self._model = model
        self._sdk_options = sdk_options or {}
        self._client: ClaudeSDKClient | None = None
        self._options: ClaudeAgentOptions | None = None
        self._session_id: str | None = None
        self._connected: bool = False

    @property
    def session_id(self) -> str | None:
        """Get current session ID (available after stream() receives init message).

        Returns:
            Current session ID or None if not yet received
        """
        return self._session_id

    async def initialize(self) -> None:
        """Initialize the Claude Agent SDK client."""
        base_options: dict[str, Any] = {
            "permission_mode": "bypassPermissions",
            "include_partial_messages": True,
            "setting_sources": ["user", "project", "local"],
        }

        final_options = {**base_options, **self._sdk_options}

        if self._model:
            final_options["model"] = self._model

        self._options = ClaudeAgentOptions(**final_options)
        self._client = ClaudeSDKClient(self._options)

    async def start_session(self, session_id: str | None = None) -> str:
        """Start a new session or resume an existing one.

        Args:
            session_id: Optional session ID to resume

        Returns:
            The actual session ID being used

        Raises:
            SessionResumeError: If session resume fails
        """
        if session_id:
            resume_options: dict[str, Any] = {
                "permission_mode": "bypassPermissions",
                "include_partial_messages": True,
                "setting_sources": ["user", "project", "local"],
            }

            resume_options = {**resume_options, **self._sdk_options}

            if self._model:
                resume_options["model"] = self._model

            resume_options["resume"] = session_id

            self._options = ClaudeAgentOptions(**resume_options)
            self._client = ClaudeSDKClient(self._options)

            try:
                await self._client.connect()
                self._connected = True
                self._session_id = session_id
                return session_id
            except Exception as e:
                error_str = str(e).lower()
                if "session" in error_str or "resume" in error_str:
                    raise SessionResumeError(f"Failed to resume session {session_id}: {e}") from e
                raise
        else:
            if self._client is None:
                raise RuntimeError("Client not initialized. Call initialize() first.")
            await self._client.connect()
            self._connected = True
            return ""

    async def send(self, message: str) -> None:
        """Send a message to Claude.

        Args:
            message: The message to send
        """
        if not self._connected or self._client is None:
            raise RuntimeError("Client not connected. Call start_session() first.")

        await self._client.query(message)

    async def stream(self) -> AsyncIterator[AgentMessage]:
        """Stream responses from Claude.

        Yields:
            AgentMessage objects containing the response

        Raises:
            SessionLimitError: When session limit is reached
        """
        if not self._connected or self._client is None:
            raise RuntimeError("Client not connected. Call start_session() first.")

        async for message in self._client.receive_response():
            if isinstance(message, SystemMessage) and message.subtype == "init":
                session_id = message.data.get("session_id")
                if session_id:
                    self._session_id = session_id

            match message:
                case AssistantMessage():
                    content = ""
                    for block in message.content:
                        match block:
                            case TextBlock():
                                content += block.text
                            case ToolUseBlock():
                                tool_header = f"[TOOL_USE: {block.name}]"
                                if block.input:
                                    tool_input_json = json.dumps(block.input, indent=2, ensure_ascii=False)
                                    json_block = f"```json\n{tool_input_json}\n```"
                                    indented_json = "\n".join(f"    {line}" for line in json_block.split("\n"))
                                    content += f"{tool_header}\n{indented_json}"
                                else:
                                    content += tool_header
                            case ThinkingBlock():
                                thinking_header = "[THINKING]"
                                if block.thinking:
                                    # Follow existing ToolUse pattern: wrap in code block
                                    thinking_block = f"```\n{block.thinking}\n```"
                                    indented_block = "\n".join(f"    {line}" for line in thinking_block.split("\n"))
                                    content += f"{thinking_header}\n{indented_block}"
                                else:
                                    content += thinking_header

                    yield AgentMessage(
                        role="assistant",
                        content=content,
                        metadata={"model": message.model},
                    )

                case SystemMessage():
                    yield AgentMessage(
                        role="system",
                        content=f"[{message.subtype}] {json.dumps(message.data)}",
                        metadata={"subtype": message.subtype},
                    )

                case ResultMessage():
                    if message.is_error and message.result:
                        result_str = str(message.result).lower()
                        if "session limit" in result_str or "limit reached" in result_str:
                            reset_time = parse_reset_time(str(message.result))
                            raise SessionLimitError(
                                f"Claude API session limit reached: {message.result}",
                                reset_time=reset_time,
                            )

                    yield AgentMessage(
                        role="system",
                        content=f"Session complete: {message.session_id}",
                        metadata={
                            "session_id": message.session_id,
                            "duration_ms": message.duration_ms,
                            "num_turns": message.num_turns,
                            "is_error": message.is_error,
                            "result": str(message.result) if message.result else None,
                        },
                    )
                    return

    async def close(self) -> None:
        """Close the Claude Agent SDK client."""
        if self._client and self._connected:
            try:
                await self._client.disconnect()
            except Exception:
                pass
            finally:
                self._connected = False
