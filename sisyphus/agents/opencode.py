"""OpenCodeAgent implementation with server auto-start and SSE streaming."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import anyio
import httpx

from sisyphus.utils.errors import AgentNotFoundError, HealthCheckError, ServerStartError
from sisyphus.utils.process import ProcessManager
from sisyphus.utils.types import AgentMessage

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class OpenCodeAgent:
    """OpenCode agent with server auto-start and SSE streaming."""

    supports_interactive: bool = True

    def __init__(
        self,
        binary: Path | None = None,
        server_url: str | None = None,
    ) -> None:
        """Initialize OpenCodeAgent.

        Args:
            binary: Optional path to opencode binary
            server_url: Optional external server URL (skips auto-start if provided)
        """
        self._binary = binary
        self._server_url = server_url
        self._binary_path: Path | None = None
        self._process: anyio.abc.Process | None = None
        self._session_id: str | None = None
        self._auto_port: int | None = None
        self._client: httpx.AsyncClient | None = None

    @property
    def session_id(self) -> str | None:
        """Get current session ID.

        Returns:
            Current session ID or None if not yet received
        """
        return self._session_id

    async def initialize(self) -> None:
        """Initialize the OpenCode agent.

        If server_url is provided, skips binary search and server start.
        Otherwise, finds binary and starts server with health check.

        Raises:
            AgentNotFoundError: If opencode binary is not found
            ServerStartError: If server fails to start
            HealthCheckError: If health check fails after retries
        """
        if self._server_url:
            self._client = httpx.AsyncClient(base_url=self._server_url, timeout=30.0)
            await self._health_check()
            return

        await self._find_binary()
        self._auto_port = await self._find_available_port()
        await self._start_server()

        self._client = httpx.AsyncClient(
            base_url=f"http://127.0.0.1:{self._auto_port}",
            timeout=30.0,
        )

        await self._health_check()

    async def _find_binary(self) -> None:
        """Find opencode binary with priority order.

        Priority:
        1. Constructor binary parameter
        2. PATH search (shutil.which)
        3. Environment variable OPENCODE_BINARY

        Raises:
            AgentNotFoundError: If binary is not found
        """
        if self._binary:
            if self._binary.exists():
                self._binary_path = self._binary
                return
            raise AgentNotFoundError(f"OpenCode binary not found at: {self._binary}")

        binary_str = shutil.which("opencode")
        if binary_str:
            self._binary_path = Path(binary_str)
            return

        env_binary = os.getenv("OPENCODE_BINARY")
        if env_binary:
            env_path = Path(env_binary)
            if env_path.exists():
                self._binary_path = env_path
                return
            raise AgentNotFoundError(f"OpenCode binary not found at OPENCODE_BINARY: {env_binary}")

        raise AgentNotFoundError(
            "OpenCode binary not found. Please install opencode or set OPENCODE_BINARY environment variable."
        )

    async def _find_available_port(self) -> int:
        """Find an available port by binding to port 0.

        Returns:
            Available port number
        """
        async with await anyio.create_tcp_listener(local_host="127.0.0.1", local_port=0) as listener:
            return listener.extra(anyio.abc.SocketAttribute.local_port)

    async def _start_server(self) -> None:
        """Start OpenCode server in background.

        Raises:
            ServerStartError: If server fails to start
        """
        if self._binary_path is None or self._auto_port is None:
            raise RuntimeError("Binary or port not initialized")

        cmd = [
            str(self._binary_path),
            "serve",
            "--host",
            "127.0.0.1",
            "--port",
            str(self._auto_port),
        ]

        try:
            self._process = await ProcessManager.run_with_timeout(cmd, timeout_seconds=10.0)
        except Exception as e:
            raise ServerStartError(f"Failed to start OpenCode server: {e}") from e

    async def _health_check(self) -> None:
        """Perform health check with retries.

        Checks GET /app endpoint 5 times with 2 second intervals.

        Raises:
            HealthCheckError: If all health check attempts fail
        """
        if self._client is None:
            raise RuntimeError("HTTP client not initialized")

        max_retries = 5
        retry_interval = 2.0

        for attempt in range(max_retries):
            try:
                response = await self._client.get("/app")
                if response.status_code == 200:
                    return
            except (httpx.RequestError, httpx.HTTPStatusError):
                if attempt < max_retries - 1:
                    await anyio.sleep(retry_interval)
                    continue

        raise HealthCheckError(f"Health check failed after {max_retries} attempts")

    async def start_session(self, session_id: str | None = None) -> str:
        """Start a new session or resume an existing one.

        Args:
            session_id: Optional session ID to use as appId

        Returns:
            The actual session ID (ses_xxx format from server)

        Raises:
            RuntimeError: If client not initialized
        """
        if self._client is None:
            raise RuntimeError("HTTP client not initialized. Call initialize() first.")

        app_id = session_id or "default"

        response = await self._client.post("/session", json={"appId": app_id})
        response.raise_for_status()

        session_data = response.json()
        self._session_id = session_data.get("id", app_id)

        if self._session_id is None:
            raise RuntimeError("Server did not return session ID")

        return self._session_id

    async def send(self, message: str) -> None:
        """Send a message to OpenCode.

        Args:
            message: The message to send

        Raises:
            RuntimeError: If session not started
        """
        if self._client is None or self._session_id is None:
            raise RuntimeError("Session not started. Call start_session() first.")

        await self._client.post(
            "/app",
            json={"session": self._session_id, "message": message},
        )

    async def stream(self) -> AsyncIterator[AgentMessage]:
        """Stream responses from OpenCode via SSE.

        Yields:
            AgentMessage objects containing the response

        Raises:
            RuntimeError: If session not started
        """
        if self._client is None or self._session_id is None:
            raise RuntimeError("Session not started. Call start_session() first.")

        url = f"/event?session={self._session_id}"
        headers = {"Accept": "text/event-stream"}

        async with self._client.stream("GET", url, headers=headers) as response:
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue

                data_str = line[6:].strip()

                if not data_str:
                    continue

                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                event_type = data.get("event", "message.chunk")
                role = "assistant"
                content = ""
                metadata: dict[str, object] = {"event": event_type}

                match event_type:
                    case "message.chunk":
                        content = data.get("content", "")
                        metadata["id"] = data.get("id")
                        metadata["index"] = data.get("index")
                    case "message.start":
                        content = f"[Message started: {data.get('id')}]"
                        metadata.update(data)
                    case "message.end":
                        content = f"[Message completed: {data.get('tokens')} tokens]"
                        metadata.update(data)
                    case "tool.start":
                        content = f"[Tool: {data.get('name')}]"
                        metadata.update(data)
                    case "tool.result":
                        content = f"[Tool result: {data.get('success')}]"
                        metadata.update(data)
                    case "error":
                        role = "system"
                        content = f"[Error: {data.get('message')}]"
                        metadata.update(data)
                    case _:
                        content = str(data)

                yield AgentMessage(
                    role=role,
                    content=content,
                    metadata=metadata,
                )

    async def close(self) -> None:
        """Close the OpenCode agent and terminate server if auto-started."""
        if self._client:
            with anyio.move_on_after(5.0):
                await self._client.aclose()
            self._client = None

        if self._process:
            await ProcessManager.terminate_gracefully(self._process, timeout_seconds=5.0)
            self._process = None
