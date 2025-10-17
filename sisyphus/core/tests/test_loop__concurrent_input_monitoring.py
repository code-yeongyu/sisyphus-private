"""Tests for ExecutionLoop concurrent input monitoring feature.

Tests Task 3.1 and 3.2 from ai-todolist.md:
- 3.1: Message transmission during Agent response
- 3.2: ESC key interrupt/resume multiple times
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import anyio
import pytest

from sisyphus.core.loop import ExecutionLoop
from sisyphus.utils.types import AgentMessage

if TYPE_CHECKING:
    pass

pytestmark = [pytest.mark.anyio]


class MockLoggerFactory:
    """Mock logger factory for testing."""

    @staticmethod
    def create_logger(agent_type: str, session_id: str | None = None, log_dir: Path = Path("./logs")) -> MagicMock:
        logger = MagicMock()
        logger.info = MagicMock()
        logger.debug = MagicMock()
        logger.warning = MagicMock()
        return logger


async def test_execute_phase__if_user_sends_message_during_agent_response__message_forwarded_immediately() -> None:
    """Test 3.1.1: User message input during Agent response → Immediately forwarded to Agent."""

    # given
    class MockAgent:
        def __init__(self) -> None:
            self.supports_interactive = False
            self.session_id: str | None = None
            self.sent_messages: list[str] = []
            self.stream_started = False

        async def initialize(self) -> None:
            pass

        async def start_session(self, session_id: str | None = None) -> str:
            self.session_id = session_id or "test-session"
            return self.session_id

        async def send(self, message: str) -> None:
            self.sent_messages.append(message)

        def stream(self) -> AsyncIterator[AgentMessage]:
            async def _generator() -> AsyncIterator[AgentMessage]:
                self.stream_started = True
                # Simulate Agent generating 3 messages
                for i in range(3):
                    await anyio.sleep(0.01)
                    yield AgentMessage(role="assistant", content=f"Response {i + 1}")

            return _generator()

        async def close(self) -> None:
            pass

    class MockUI:
        def __init__(self) -> None:
            self.messages: list[tuple[AgentMessage, str]] = []
            self.input_queue: list[str] = []
            self.input_index = 0

        async def initialize(self) -> None:
            pass

        async def show_message(self, message: AgentMessage, source: str) -> None:
            self.messages.append((message, source))
            # Simulate user sending message after first Agent response
            if len(self.messages) == 1:
                self.input_queue.append("User message during response")

        async def show_status(self, status: str) -> None:
            pass

        async def get_input(self) -> str | None:
            if self.input_index < len(self.input_queue):
                msg = self.input_queue[self.input_index]
                self.input_index += 1
                return msg
            await anyio.sleep(0.01)
            return None

    class MockSessionStore:
        async def get_session(self, agent_type: str) -> str | None:
            return None

        async def save_session(self, agent_type: str, session_id: str) -> None:
            pass

    class MockPromptResolver:
        async def resolve(self, prompt: str, extra: str | None = None) -> str:
            return prompt

    execute_agent = MockAgent()
    verify_agent = MockAgent()
    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        ui=ui,
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
    )

    # when
    await loop.run(execute_prompt="Test prompt", verify_prompt="Verify")

    # then
    # Both initial prompt and user message should be forwarded
    assert len(execute_agent.sent_messages) == 2
    assert execute_agent.sent_messages[0] == "Test prompt"
    assert execute_agent.sent_messages[1] == "User message during response"


async def test_execute_phase__if_multiple_user_messages_sent__all_forwarded_in_order() -> None:
    """Test 3.1.2: Multiple messages sent consecutively → All forwarded in order."""

    # given
    class MockAgent:
        def __init__(self) -> None:
            self.supports_interactive = False
            self.session_id: str | None = None
            self.sent_messages: list[str] = []

        async def initialize(self) -> None:
            pass

        async def start_session(self, session_id: str | None = None) -> str:
            self.session_id = session_id or "test-session"
            return self.session_id

        async def send(self, message: str) -> None:
            self.sent_messages.append(message)

        def stream(self) -> AsyncIterator[AgentMessage]:
            async def _generator() -> AsyncIterator[AgentMessage]:
                for i in range(5):
                    await anyio.sleep(0.01)
                    yield AgentMessage(role="assistant", content=f"Response {i + 1}")

            return _generator()

        async def close(self) -> None:
            pass

    class MockUI:
        def __init__(self) -> None:
            self.messages: list[tuple[AgentMessage, str]] = []
            self.input_queue: list[str] = ["First", "Second", "Third"]
            self.input_index = 0

        async def initialize(self) -> None:
            pass

        async def show_message(self, message: AgentMessage, source: str) -> None:
            self.messages.append((message, source))

        async def show_status(self, status: str) -> None:
            pass

        async def get_input(self) -> str | None:
            if self.input_index < len(self.input_queue):
                msg = self.input_queue[self.input_index]
                self.input_index += 1
                await anyio.sleep(0.005)  # Small delay to simulate user typing
                return msg
            await anyio.sleep(0.01)
            return None

    class MockSessionStore:
        async def get_session(self, agent_type: str) -> str | None:
            return None

        async def save_session(self, agent_type: str, session_id: str) -> None:
            pass

    class MockPromptResolver:
        async def resolve(self, prompt: str, extra: str | None = None) -> str:
            return prompt

    execute_agent = MockAgent()
    verify_agent = MockAgent()
    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        ui=ui,
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
    )

    # when
    await loop.run(execute_prompt="Initial", verify_prompt="Verify")

    # then
    assert len(execute_agent.sent_messages) == 4
    assert execute_agent.sent_messages[0] == "Initial"
    assert execute_agent.sent_messages[1] == "First"
    assert execute_agent.sent_messages[2] == "Second"
    assert execute_agent.sent_messages[3] == "Third"
