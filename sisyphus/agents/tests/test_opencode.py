"""Tests for OpenCodeAgent."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import anyio
import httpx
import pytest

from sisyphus.agents.base import Agent
from sisyphus.agents.opencode import OpenCodeAgent
from sisyphus.utils.errors import AgentNotFoundError, HealthCheckError, ServerStartError

pytestmark = [pytest.mark.anyio]


async def test_opencode_supports_interactive() -> None:
    """OpenCodeAgent should support interactive mode."""
    # given
    agent = OpenCodeAgent()

    # when / then
    assert agent.supports_interactive is True


async def test_opencode_protocol_compliance() -> None:
    """OpenCodeAgent should satisfy Agent Protocol."""
    # given
    agent = OpenCodeAgent()

    # when / then
    assert isinstance(agent, Agent)


async def test_binary_discovery_from_path() -> None:
    """Should find binary from PATH."""
    # given
    with patch("shutil.which", return_value="/usr/bin/opencode"):
        agent = OpenCodeAgent()

        # when / then
        await agent._find_binary()
        assert agent._binary_path == Path("/usr/bin/opencode")


async def test_binary_discovery_from_constructor() -> None:
    """Should prioritize constructor binary parameter."""
    # given
    binary_path = Path("/custom/opencode")
    with patch.object(Path, "exists", return_value=True):
        agent = OpenCodeAgent(binary=binary_path)

        # when
        await agent._find_binary()

        # then
        assert agent._binary_path == binary_path


async def test_binary_discovery_from_env() -> None:
    """Should fall back to environment variable."""
    # given
    with (
        patch("shutil.which", return_value=None),
        patch("os.getenv", return_value="/env/opencode"),
        patch.object(Path, "exists", return_value=True),
    ):
        agent = OpenCodeAgent()

        # when
        await agent._find_binary()

        # then
        assert agent._binary_path == Path("/env/opencode")


async def test_binary_not_found() -> None:
    """Should raise AgentNotFoundError when binary not found."""
    # given
    with (
        patch("shutil.which", return_value=None),
        patch("os.getenv", return_value=None),
    ):
        agent = OpenCodeAgent()

        # when / then
        with pytest.raises(AgentNotFoundError, match="OpenCode binary not found"):
            await agent._find_binary()


async def test_find_available_port() -> None:
    """Should find available port."""
    # given
    agent = OpenCodeAgent()

    # when
    port = await agent._find_available_port()

    # then
    assert isinstance(port, int)
    assert port > 0


async def test_server_auto_start() -> None:
    """Should start server with auto-discovered port."""
    # given
    agent = OpenCodeAgent()
    agent._binary_path = Path("/usr/bin/opencode")
    agent._auto_port = 4096

    mock_process = Mock(spec=anyio.abc.Process)

    with patch(
        "sisyphus.agents.opencode.ProcessManager.run_with_timeout",
        return_value=mock_process,
    ) as mock_run:
        # when
        await agent._start_server()

        # then
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "/usr/bin/opencode"
        assert call_args[1] == "serve"
        assert "4096" in call_args
        assert agent._process == mock_process


async def test_server_start_failure() -> None:
    """Should raise ServerStartError on failure."""
    # given
    agent = OpenCodeAgent()
    agent._binary_path = Path("/usr/bin/opencode")
    agent._auto_port = 4096

    with patch(
        "sisyphus.agents.opencode.ProcessManager.run_with_timeout",
        side_effect=Exception("Connection refused"),
    ):
        # when / then
        with pytest.raises(ServerStartError, match="Failed to start OpenCode server"):
            await agent._start_server()


async def test_health_check_success() -> None:
    """Should pass health check on first attempt."""
    # given
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(return_value=mock_response)

    agent = OpenCodeAgent()
    agent._client = mock_client

    # when
    await agent._health_check()

    # then
    mock_client.get.assert_called_once_with("/app")


async def test_health_check_retry() -> None:
    """Should retry health check on failure."""
    # given
    mock_response_fail = Mock(spec=httpx.Response)
    mock_response_fail.status_code = 500

    mock_response_success = Mock(spec=httpx.Response)
    mock_response_success.status_code = 200

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(
        side_effect=[
            httpx.RequestError("Connection refused"),
            mock_response_success,
        ]
    )

    agent = OpenCodeAgent()
    agent._client = mock_client

    with patch("anyio.sleep"):
        # when
        await agent._health_check()

        # then
        assert mock_client.get.call_count == 2


async def test_health_check_failure() -> None:
    """Should raise HealthCheckError after max retries."""
    # given
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection refused"))

    agent = OpenCodeAgent()
    agent._client = mock_client

    with patch("anyio.sleep"):
        # when / then
        with pytest.raises(HealthCheckError, match="Health check failed after 5 attempts"):
            await agent._health_check()


async def test_external_server_url() -> None:
    """Should skip auto-start when external server URL provided."""
    # given
    agent = OpenCodeAgent(server_url="http://localhost:9999")

    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200

    with (
        patch("httpx.AsyncClient") as mock_client_cls,
        patch.object(agent, "_health_check") as mock_health,
    ):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        # when
        await agent.initialize()

        # then
        mock_client_cls.assert_called_once_with(base_url="http://localhost:9999", timeout=30.0)
        mock_health.assert_called_once()
        assert agent._process is None


async def test_session_creation() -> None:
    """Should create session with POST /session."""
    # given
    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = {"id": "ses_123"}
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_response)

    agent = OpenCodeAgent()
    agent._client = mock_client

    # when
    session_id = await agent.start_session("my-app")

    # then
    assert session_id == "ses_123"
    mock_client.post.assert_called_once_with("/session", json={"appId": "my-app"})


async def test_session_creation_default() -> None:
    """Should use default appId when session_id not provided."""
    # given
    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = {"id": "ses_456"}
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_response)

    agent = OpenCodeAgent()
    agent._client = mock_client

    # when
    session_id = await agent.start_session()

    # then
    assert session_id == "ses_456"
    mock_client.post.assert_called_once_with("/session", json={"appId": "default"})


async def test_send_message() -> None:
    """Should send message via POST /app."""
    # given
    mock_response = Mock(spec=httpx.Response)
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_response)

    agent = OpenCodeAgent()
    agent._client = mock_client
    agent._session_id = "ses_123"

    # when
    await agent.send("Hello, OpenCode!")

    # then
    mock_client.post.assert_called_once_with(
        "/app",
        json={"session": "ses_123", "message": "Hello, OpenCode!"},
    )


async def test_sse_streaming_message_chunk() -> None:
    """Should parse SSE message.chunk events."""
    # given
    sse_data = [
        'data: {"event": "message.chunk", "content": "Hello", "id": "msg-1", "index": 0}',
        'data: {"event": "message.chunk", "content": " World", "id": "msg-1", "index": 1}',
    ]

    async def mock_aiter_lines() -> AsyncIterator[str]:
        for line in sse_data:
            yield line

    mock_response = Mock()
    mock_response.aiter_lines = mock_aiter_lines

    mock_stream_ctx = AsyncMock()
    mock_stream_ctx.__aenter__.return_value = mock_response
    mock_stream_ctx.__aexit__.return_value = None

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.stream.return_value = mock_stream_ctx

    agent = OpenCodeAgent()
    agent._client = mock_client
    agent._session_id = "ses_123"

    # when
    messages = []
    async for msg in agent.stream():
        messages.append(msg)

    # then
    assert len(messages) == 2
    assert messages[0].content == "Hello"
    assert messages[0].metadata["id"] == "msg-1"
    assert messages[1].content == " World"


async def test_sse_streaming_tool_events() -> None:
    """Should parse SSE tool events."""
    # given
    sse_data = [
        'data: {"event": "tool.start", "name": "read_file", "id": "tool-1"}',
        'data: {"event": "tool.result", "success": true, "id": "tool-1"}',
    ]

    async def mock_aiter_lines() -> AsyncIterator[str]:
        for line in sse_data:
            yield line

    mock_response = Mock()
    mock_response.aiter_lines = mock_aiter_lines

    mock_stream_ctx = AsyncMock()
    mock_stream_ctx.__aenter__.return_value = mock_response
    mock_stream_ctx.__aexit__.return_value = None

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.stream.return_value = mock_stream_ctx

    agent = OpenCodeAgent()
    agent._client = mock_client
    agent._session_id = "ses_123"

    # when
    messages = []
    async for msg in agent.stream():
        messages.append(msg)

    # then
    assert len(messages) == 2
    assert "[Tool: read_file]" in messages[0].content
    assert "[Tool result:" in messages[1].content


async def test_sse_streaming_error_event() -> None:
    """Should parse SSE error events."""
    # given
    sse_data = [
        'data: {"event": "error", "message": "Rate limit exceeded", "code": "RATE_LIMIT"}',
    ]

    async def mock_aiter_lines() -> AsyncIterator[str]:
        for line in sse_data:
            yield line

    mock_response = Mock()
    mock_response.aiter_lines = mock_aiter_lines

    mock_stream_ctx = AsyncMock()
    mock_stream_ctx.__aenter__.return_value = mock_response
    mock_stream_ctx.__aexit__.return_value = None

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.stream.return_value = mock_stream_ctx

    agent = OpenCodeAgent()
    agent._client = mock_client
    agent._session_id = "ses_123"

    # when
    messages = []
    async for msg in agent.stream():
        messages.append(msg)

    # then
    assert len(messages) == 1
    assert messages[0].role == "system"
    assert "Rate limit exceeded" in messages[0].content


async def test_sse_streaming_skip_invalid_lines() -> None:
    """Should skip lines without 'data:' prefix."""
    # given
    sse_data = [
        "event: message.start",
        'data: {"event": "message.chunk", "content": "Valid"}',
        "",
        ": comment line",
    ]

    async def mock_aiter_lines() -> AsyncIterator[str]:
        for line in sse_data:
            yield line

    mock_response = Mock()
    mock_response.aiter_lines = mock_aiter_lines

    mock_stream_ctx = AsyncMock()
    mock_stream_ctx.__aenter__.return_value = mock_response
    mock_stream_ctx.__aexit__.return_value = None

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.stream.return_value = mock_stream_ctx

    agent = OpenCodeAgent()
    agent._client = mock_client
    agent._session_id = "ses_123"

    # when
    messages = []
    async for msg in agent.stream():
        messages.append(msg)

    # then
    assert len(messages) == 1
    assert messages[0].content == "Valid"


async def test_sse_streaming_malformed_json() -> None:
    """Should skip malformed JSON without crashing."""
    # given
    sse_data = [
        "data: {invalid json}",
        'data: {"event": "message.chunk", "content": "Valid"}',
        "data: {incomplete",
    ]

    async def mock_aiter_lines() -> AsyncIterator[str]:
        for line in sse_data:
            yield line

    mock_response = Mock()
    mock_response.aiter_lines = mock_aiter_lines

    mock_stream_ctx = AsyncMock()
    mock_stream_ctx.__aenter__.return_value = mock_response
    mock_stream_ctx.__aexit__.return_value = None

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.stream.return_value = mock_stream_ctx

    agent = OpenCodeAgent()
    agent._client = mock_client
    agent._session_id = "ses_123"

    # when
    messages = []
    async for msg in agent.stream():
        messages.append(msg)

    # then
    assert len(messages) == 1
    assert messages[0].content == "Valid"


async def test_sse_streaming_empty_data_field() -> None:
    """Should skip empty data fields."""
    # given
    sse_data = [
        "data: ",
        "data:    ",
        'data: {"event": "message.chunk", "content": "Valid"}',
    ]

    async def mock_aiter_lines() -> AsyncIterator[str]:
        for line in sse_data:
            yield line

    mock_response = Mock()
    mock_response.aiter_lines = mock_aiter_lines

    mock_stream_ctx = AsyncMock()
    mock_stream_ctx.__aenter__.return_value = mock_response
    mock_stream_ctx.__aexit__.return_value = None

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.stream.return_value = mock_stream_ctx

    agent = OpenCodeAgent()
    agent._client = mock_client
    agent._session_id = "ses_123"

    # when
    messages = []
    async for msg in agent.stream():
        messages.append(msg)

    # then
    assert len(messages) == 1
    assert messages[0].content == "Valid"


async def test_close_cleanup() -> None:
    """Should cleanup resources on close."""
    # given
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_process = Mock(spec=anyio.abc.Process)

    agent = OpenCodeAgent()
    agent._client = mock_client
    agent._process = mock_process

    with patch("sisyphus.agents.opencode.ProcessManager.terminate_gracefully") as mock_terminate:
        # when
        await agent.close()

        # then
        mock_client.aclose.assert_called_once()
        mock_terminate.assert_called_once_with(mock_process, timeout_seconds=5.0)
        assert agent._client is None
        assert agent._process is None


async def test_close_without_process() -> None:
    """Should handle close when no process started (external server)."""
    # given
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    agent = OpenCodeAgent()
    agent._client = mock_client
    agent._process = None

    # when
    await agent.close()

    # then
    mock_client.aclose.assert_called_once()
    assert agent._client is None
