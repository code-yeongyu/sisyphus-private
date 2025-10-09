"""DroidAgent implementation using Droid CLI with stream-json mode."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import anyio

from sisyphus.utils.errors import AgentNotFoundError
from sisyphus.utils.process import ProcessManager
from sisyphus.utils.types import AgentMessage

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class DroidAgent:
    """Droid CLI agent using subprocess with stream-json mode."""

    supports_interactive: bool = False

    def __init__(
        self,
        binary: Path | None = None,
        model: str | None = None,
    ) -> None:
        """Initialize DroidAgent.

        Args:
            binary: Optional path to droid binary
            model: Optional model override (e.g., "claude-opus-4-1-20250805")
        """
        self._binary = binary
        self._model = model
        self._binary_path: Path | None = None
        self._process: anyio.abc.Process | None = None
        self._session_id: str | None = None

    async def initialize(self) -> None:
        """Initialize the Droid agent by finding the binary.

        Binary search priority:
        1. Constructor binary parameter
        2. PATH search (shutil.which)
        3. Environment variable DROID_BINARY

        Raises:
            AgentNotFoundError: If droid binary is not found
        """
        if self._binary:
            if self._binary.exists():
                self._binary_path = self._binary
                return
            raise AgentNotFoundError(f"Droid binary not found at: {self._binary}")

        binary_str = shutil.which("droid")
        if binary_str:
            self._binary_path = Path(binary_str)
            return

        env_binary = os.getenv("DROID_BINARY")
        if env_binary:
            env_path = Path(env_binary)
            if env_path.exists():
                self._binary_path = env_path
                return
            raise AgentNotFoundError(f"Droid binary not found at DROID_BINARY: {env_binary}")

        raise AgentNotFoundError(
            "Droid binary not found. Please install droid or set DROID_BINARY environment variable."
        )

    async def start_session(self, session_id: str | None = None) -> str:
        """Start a new session or resume an existing one.

        Args:
            session_id: Optional session ID to resume (UUID format)

        Returns:
            The actual session ID being used

        Raises:
            RuntimeError: If binary not initialized
        """
        if self._binary_path is None:
            raise RuntimeError("Binary not initialized. Call initialize() first.")

        if session_id:
            self._session_id = session_id
        else:
            self._session_id = str(uuid.uuid4())

        cmd = [
            str(self._binary_path),
            "exec",
            "--input-format",
            "stream-json",
            "--output-format",
            "stream-json",
            "--session",
            self._session_id,
            "--skip-permissions-unsafe",
        ]

        if self._model:
            cmd.extend(["--model", self._model])

        self._process = await ProcessManager.run_with_timeout(cmd, timeout_seconds=30.0)

        return self._session_id

    async def send(self, message: str) -> None:
        """Send a message to Droid via stdin.

        Args:
            message: The message to send
        """
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("Process not started. Call start_session() first.")

        json_msg = json.dumps({"role": "user", "content": message})
        json_bytes = json_msg.encode("utf-8") + b"\n"

        await self._process.stdin.send(json_bytes)

    async def stream(self) -> AsyncIterator[AgentMessage]:
        """Stream responses from Droid via stdout.

        Yields:
            AgentMessage objects containing the response
        """
        if self._process is None or self._process.stdout is None:
            raise RuntimeError("Process not started. Call start_session() first.")

        async for json_obj in ProcessManager.parse_jsonl_stream(self._process.stdout):
            role = json_obj.get("role", "assistant")
            content = json_obj.get("content", "")
            metadata = {k: v for k, v in json_obj.items() if k not in ("role", "content")}

            yield AgentMessage(
                role=role,
                content=content,
                metadata=metadata,
            )

    async def close(self) -> None:
        """Close the Droid process gracefully."""
        if self._process:
            await ProcessManager.terminate_gracefully(self._process, timeout_seconds=5.0)
            self._process = None
