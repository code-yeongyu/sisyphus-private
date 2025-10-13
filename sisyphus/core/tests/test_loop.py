"""Tests for ExecutionLoop."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from sisyphus.core.loop import ExecutionLoop
from sisyphus.utils.types import AgentMessage

if TYPE_CHECKING:
    pass

pytestmark = [pytest.mark.anyio]


class MockAgent:
    """Mock agent for testing."""

    def __init__(self) -> None:
        self.supports_interactive = False
        self.initialized = False
        self.session_id: str | None = None
        self.sent_messages: list[str] = []
        self.closed = False
        self.messages_to_return: list[AgentMessage] = []

    async def initialize(self) -> None:
        self.initialized = True

    async def start_session(self, session_id: str | None = None) -> str:
        if session_id is not None:
            self.session_id = session_id
        else:
            self.session_id = "new-session-123"
        return self.session_id

    async def send(self, message: str) -> None:
        self.sent_messages.append(message)

    def stream(self) -> AsyncIterator[AgentMessage]:
        async def _generator() -> AsyncIterator[AgentMessage]:
            for msg in self.messages_to_return:
                yield msg

        return _generator()

    async def close(self) -> None:
        self.closed = True


class MockUI:
    """Mock UI for testing."""

    def __init__(self) -> None:
        self.initialized = False
        self.messages: list[tuple[AgentMessage, str]] = []
        self.statuses: list[str] = []

    async def initialize(self) -> None:
        self.initialized = True

    async def show_message(self, message: AgentMessage, source: str) -> None:
        self.messages.append((message, source))

    async def show_status(self, status: str) -> None:
        self.statuses.append(status)

    async def get_input(self) -> str | None:
        return None


class MockSessionStore:
    """Mock session store for testing."""

    def __init__(self) -> None:
        self.sessions: dict[str, str] = {}

    async def get_session(self, agent_type: str) -> str | None:
        return self.sessions.get(agent_type)

    async def save_session(self, agent_type: str, session_id: str) -> None:
        self.sessions[agent_type] = session_id

    async def delete_session(self, agent_type: str) -> None:
        if agent_type in self.sessions:
            del self.sessions[agent_type]

    async def list_sessions(self) -> dict[str, dict[str, str]]:
        return {k: {"session_id": v} for k, v in self.sessions.items()}


class MockPromptResolver:
    """Mock prompt resolver for testing."""

    async def resolve(self, prompt: str, extra: str | None = None) -> str:
        if extra:
            return f"{prompt}\n\n{extra}"
        return prompt


class MockLoggerFactory:
    """Mock logger factory for testing."""

    @staticmethod
    def create_logger(agent_type: str, session_id: str | None = None, log_dir: Path = Path("./logs")) -> MagicMock:
        logger = MagicMock()
        logger.info = MagicMock()
        logger.debug = MagicMock()
        return logger


class MockTaskValidator:
    """Mock task validator for testing."""

    def __init__(self, all_complete: bool = False) -> None:
        self._all_complete = all_complete
        self.read_count = 0

    def read_content(self) -> str:
        self.read_count += 1
        return "mock content"

    def check_all_goals_accomplished(self, content: str | None = None) -> bool:
        return self._all_complete

    def check_all_checkboxes_completed(self, content: str | None = None) -> bool:
        return self._all_complete

    def extract_uncompleted_checkboxes(self, content: str | None = None) -> list[str]:
        if self._all_complete:
            return []
        return ["Task 1", "Task 2"]

    def count_total_checkboxes(self, content: str | None = None) -> int:
        return 10

    def count_completed_checkboxes(self, content: str | None = None) -> int:
        return 8 if not self._all_complete else 10


async def test_execution_loop_execute_only() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Hello from execute", metadata={}),
    ]
    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
    )

    # when
    await loop.run(execute_prompt="Execute task")

    # then
    assert execute_agent.initialized
    assert execute_agent.session_id == "new-session-123"
    assert "Execute task" in execute_agent.sent_messages
    assert execute_agent.closed
    assert ui.initialized
    # UI remains initialized after ExecutionLoop completes (no longer closes automatically)
    assert len(ui.messages) == 1
    assert ui.messages[0][0].content == "Hello from execute"
    assert ui.messages[0][1] == "execute"


async def test_execution_loop_execute_and_verify() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Execute done", metadata={}),
    ]

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Verify done\n\nFULLY_DONE = TRUE", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator(all_complete=True)

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
    )

    # when
    await loop.run(execute_prompt="Execute task", verify_prompt="Verify task")

    # then
    assert execute_agent.initialized
    assert verify_agent.initialized
    assert execute_agent.closed
    assert verify_agent.closed
    assert len(ui.messages) == 2
    assert ui.messages[0][1] == "execute"
    assert ui.messages[1][1] == "verify"


async def test_execution_loop_verify_always_new_session() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = []

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Verify complete\n\nFULLY_DONE = TRUE", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    await session_store.save_session("mockagent", "old-session-456")

    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator(all_complete=True)

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
    )

    # when
    await loop.run(execute_prompt="Execute", verify_prompt="Verify")

    # then
    assert verify_agent.session_id == "new-session-123"


async def test_execution_loop_session_resume() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = []

    ui = MockUI()
    session_store = MockSessionStore()
    await session_store.save_session("mock", "existing-session-789")

    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
    )

    # when
    await loop.run(execute_prompt="Resume task")

    # then
    assert execute_agent.session_id == "existing-session-789"


async def test_execution_loop_with_task_validator_complete() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = []

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator(all_complete=True)

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
    )

    # when
    await loop.run(execute_prompt="Execute")

    # then
    assert task_validator.read_count == 1
    assert any("All tasks completed" in s for s in ui.statuses)


async def test_execution_loop_with_task_validator_incomplete() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = []

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()

    validator = MockTaskValidator(all_complete=False)

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        task_validator=validator,  # type: ignore[arg-type]
    )

    iteration_count = 0

    original_run = loop._execute_phase

    async def patched_execute_phase(prompt: str, extra: str | None = None) -> None:
        nonlocal iteration_count
        iteration_count += 1
        if iteration_count >= 2:
            validator._all_complete = True
        await original_run(prompt, extra)

    loop._execute_phase = patched_execute_phase  # type: ignore[method-assign]

    # when
    await loop.run(execute_prompt="Execute")

    # then
    assert iteration_count == 2
    assert validator.read_count == 2


async def test_execution_loop_prompt_with_extra() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = []

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
    )

    # when
    await loop.run(execute_prompt="Main prompt", execute_extra="Extra info")

    # then
    assert "Main prompt\n\nExtra info" in execute_agent.sent_messages


async def test_execution_loop_ui_status_updates() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = []

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
    )

    # when
    await loop.run(execute_prompt="Task")

    # then
    assert any("Execute phase" in s for s in ui.statuses)
    assert any("complete" in s for s in ui.statuses)


async def test_execution_loop_session_saved() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = []

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
    )

    # when
    await loop.run(execute_prompt="Task")

    # then
    sessions = await session_store.list_sessions()
    assert "mock" in sessions
    assert sessions["mock"]["session_id"] == "new-session-123"
