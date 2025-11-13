"""Tests for Agent Protocol."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from sisyphus.agents.base import Agent
from sisyphus.utils.types import AgentMessage

pytestmark = [pytest.mark.anyio]


class MockAgent:
    """Mock agent that implements Agent Protocol."""

    supports_interactive = True

    @property
    def session_id(self) -> str | None:
        return "test-session-id"

    async def initialize(self) -> None:
        pass

    async def start_session(self, session_id: str | None = None) -> str:
        return "test-session-id"

    async def send(self, message: str) -> None:
        pass

    async def stream(self) -> AsyncIterator[AgentMessage]:
        yield AgentMessage(role="assistant", content="test")

    async def close(self) -> None:
        pass


class IncompleteMockAgent:
    """Mock agent that does NOT implement Agent Protocol (missing methods)."""

    supports_interactive = True

    async def initialize(self) -> None:
        pass


async def test_protocol_validation_complete() -> None:
    # Given
    agent = MockAgent()

    # When/Then
    assert isinstance(agent, Agent)


async def test_protocol_validation_incomplete() -> None:
    # Given
    agent = IncompleteMockAgent()

    # When/Then
    assert not isinstance(agent, Agent)


async def test_protocol_supports_interactive_attribute() -> None:
    # Given
    agent = MockAgent()

    # When/Then
    assert hasattr(agent, "supports_interactive")
    assert isinstance(agent.supports_interactive, bool)


async def test_mock_agent_initialize() -> None:
    # Given
    agent = MockAgent()

    # When
    await agent.initialize()

    # Then - should not raise


async def test_mock_agent_start_session() -> None:
    # Given
    agent = MockAgent()

    # When
    session_id = await agent.start_session()

    # Then
    assert session_id == "test-session-id"


async def test_mock_agent_send() -> None:
    # Given
    agent = MockAgent()

    # When
    await agent.send("test message")

    # Then - should not raise


async def test_mock_agent_stream() -> None:
    # Given
    agent = MockAgent()

    # When
    messages = []
    async for msg in agent.stream():
        messages.append(msg)

    # Then
    assert len(messages) == 1
    assert messages[0].role == "assistant"
    assert messages[0].content == "test"


async def test_mock_agent_close() -> None:
    # Given
    agent = MockAgent()

    # When
    await agent.close()

    # Then - should not raise
