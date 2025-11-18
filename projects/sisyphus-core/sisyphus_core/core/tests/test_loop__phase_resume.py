# pyright: reportArgumentType=false, reportMissingImports=false, reportImplicitRelativeImport=false
"""Tests for ExecutionLoop phase resume behavior."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import anyio
import pytest

from sisyphus_core.core.loop import ExecutionLoop
from sisyphus_core.core.tests.test_loop import MockAgent, MockStatusManager, MockTaskValidator
from sisyphus_core.utils.types import AgentMessage

if TYPE_CHECKING:
    pass

pytestmark = [pytest.mark.anyio]


async def test_execute_phase__after_resume__continues_phase(
    mock_execute_agent: MockAgentWithResume,
    mock_ui: MockUIWithInput,
    mock_session_store: MockSessionStore,
    mock_logger_factory: MockLoggerFactory,
) -> None:
    mock_execute_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Initial response"),
    ]
    mock_ui.input_queue = ["resumed message"]
    mock_ui.should_interrupt = True

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [AgentMessage(role="assistant", content="FULLY_DONE = TRUE")]
    task_validator = MockTaskValidator(all_complete=True)

    loop = ExecutionLoop(
        execute_agent=mock_execute_agent,  # type: ignore
        verify_agent=verify_agent,  # type: ignore
        ui=mock_ui,  # type: ignore
        session_store=mock_session_store,  # type: ignore
        logger_factory=mock_logger_factory,  # type: ignore
        task_validator=task_validator,  # type: ignore
        status_manager=MockStatusManager(),  # type: ignore
    )

    loop.state.set_plan_id("test-plan")

    async def simulate_interrupt_and_resume() -> None:
        await anyio.sleep(0.05)
        loop.request_interrupt()
        await anyio.sleep(0.05)
        loop.clear_interrupt()

    async with anyio.create_task_group() as tg:
        tg.start_soon(loop.phase_orchestrator.execute_phase, "test prompt", None)
        tg.start_soon(simulate_interrupt_and_resume)

    assert "resumed message" in mock_execute_agent.sent_messages
    assert mock_execute_agent.closed


async def test_execute_phase__normal_completion__ends_phase(
    mock_execute_agent: MockAgentWithResume,
    mock_ui: MockUIWithInput,
    mock_session_store: MockSessionStore,
    mock_logger_factory: MockLoggerFactory,
) -> None:
    mock_execute_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Response 1"),
        AgentMessage(role="assistant", content="Response 2"),
    ]

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [AgentMessage(role="assistant", content="FULLY_DONE = TRUE")]
    task_validator = MockTaskValidator(all_complete=True)

    loop = ExecutionLoop(
        execute_agent=mock_execute_agent,  # type: ignore
        verify_agent=verify_agent,  # type: ignore
        ui=mock_ui,  # type: ignore
        session_store=mock_session_store,  # type: ignore
        logger_factory=mock_logger_factory,  # type: ignore
        task_validator=task_validator,  # type: ignore
        status_manager=MockStatusManager(),  # type: ignore
    )

    loop.state.set_plan_id("test-plan")

    await loop.phase_orchestrator.execute_phase("test prompt", None)

    assert mock_execute_agent.closed
    assert len(mock_ui.messages) == 2


async def test_execute_phase__multiple_resumes__continues_each_time(
    mock_execute_agent: MockAgentWithResume,
    mock_ui: MockUIWithInput,
    mock_session_store: MockSessionStore,
    mock_logger_factory: MockLoggerFactory,
) -> None:
    mock_execute_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Response 1"),
    ]
    mock_ui.input_queue = ["resume 1", "resume 2"]
    mock_ui.interrupt_count = 2

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [AgentMessage(role="assistant", content="FULLY_DONE = TRUE")]
    task_validator = MockTaskValidator(all_complete=True)

    loop = ExecutionLoop(
        execute_agent=mock_execute_agent,  # type: ignore
        verify_agent=verify_agent,  # type: ignore
        ui=mock_ui,  # type: ignore
        session_store=mock_session_store,  # type: ignore
        logger_factory=mock_logger_factory,  # type: ignore
        task_validator=task_validator,  # type: ignore
        status_manager=MockStatusManager(),  # type: ignore
    )

    loop.state.set_plan_id("test-plan")

    async def simulate_multiple_interrupts() -> None:
        await anyio.sleep(0.05)
        loop.request_interrupt()
        await anyio.sleep(0.05)
        loop.clear_interrupt()
        await anyio.sleep(0.05)
        loop.request_interrupt()
        await anyio.sleep(0.05)
        loop.clear_interrupt()

    async with anyio.create_task_group() as tg:
        tg.start_soon(loop.phase_orchestrator.execute_phase, "test prompt", None)
        tg.start_soon(simulate_multiple_interrupts)

    assert "resume 1" in mock_execute_agent.sent_messages
    assert "resume 2" in mock_execute_agent.sent_messages


async def test_verify_phase__after_resume__continues_phase(
    mock_execute_agent: MockAgentWithResume,
    mock_verify_agent: MockAgentWithResume,
    mock_ui: MockUIWithInput,
    mock_session_store: MockSessionStore,
    mock_logger_factory: MockLoggerFactory,
) -> None:
    mock_verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Initial response\nFULLY_DONE = TRUE"),
    ]
    mock_ui.input_queue = ["resumed message"]
    mock_ui.should_interrupt = True

    task_validator = MockTaskValidator(all_complete=True)

    loop = ExecutionLoop(
        execute_agent=mock_execute_agent,  # type: ignore
        verify_agent=mock_verify_agent,  # type: ignore
        ui=mock_ui,  # type: ignore
        session_store=mock_session_store,  # type: ignore
        logger_factory=mock_logger_factory,  # type: ignore
        task_validator=task_validator,  # type: ignore
    )

    loop.state.set_plan_id("test-plan")

    async def simulate_interrupt_and_resume() -> None:
        await anyio.sleep(0.05)
        loop.request_interrupt()
        await anyio.sleep(0.05)
        loop.clear_interrupt()

    async with anyio.create_task_group() as tg:
        tg.start_soon(lambda: loop.phase_orchestrator.verify_phase("test prompt", None))
        tg.start_soon(simulate_interrupt_and_resume)

    assert "resumed message" in mock_verify_agent.sent_messages
    assert mock_verify_agent.closed


async def test_verify_phase__normal_completion__ends_phase(
    mock_execute_agent: MockAgentWithResume,
    mock_verify_agent: MockAgentWithResume,
    mock_ui: MockUIWithInput,
    mock_session_store: MockSessionStore,
    mock_logger_factory: MockLoggerFactory,
) -> None:
    mock_verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Response 1"),
        AgentMessage(role="assistant", content="Response 2\nFULLY_DONE = TRUE"),
    ]

    task_validator = MockTaskValidator(all_complete=True)

    loop = ExecutionLoop(
        execute_agent=mock_execute_agent,  # type: ignore
        verify_agent=mock_verify_agent,  # type: ignore
        ui=mock_ui,  # type: ignore
        session_store=mock_session_store,  # type: ignore
        logger_factory=mock_logger_factory,  # type: ignore
        task_validator=task_validator,  # type: ignore
    )

    loop.state.set_plan_id("test-plan")

    feedback, fully_done = await loop.phase_orchestrator.verify_phase("test prompt", None)

    assert mock_verify_agent.closed
    assert len(mock_ui.messages) == 2
    assert "Response 1" in feedback
    assert "Response 2" in feedback


class MockAgentWithResume:
    def __init__(self) -> None:
        self.supports_interactive = True
        self.initialized = False
        self.session_id: str | None = None
        self.sent_messages: list[str] = []
        self.closed = False
        self.messages_to_return: list[AgentMessage] = []
        self.response_sequence: list[list[AgentMessage]] = []
        self.stream_call_count = 0
        self.session_count = 0

    async def initialize(self) -> None:
        self.initialized = True

    async def start_session(self, session_id: str | None = None) -> str:
        if session_id is not None:
            self.session_id = session_id
        else:
            self.session_id = f"session-{self.session_count}"
            self.session_count += 1
        return self.session_id

    async def send(self, message: str) -> None:
        self.sent_messages.append(message)

    def stream(self) -> AsyncIterator[AgentMessage]:
        async def _generator() -> AsyncIterator[AgentMessage]:
            self.stream_call_count += 1
            if self.response_sequence:
                session_idx = self.session_count - 1
                if 0 <= session_idx < len(self.response_sequence):
                    for msg in self.response_sequence[session_idx]:
                        yield msg
                        await anyio.sleep(0.01)
            else:
                for msg in self.messages_to_return:
                    yield msg
                    await anyio.sleep(0.01)

        return _generator()

    async def close(self) -> None:
        self.closed = True


class MockUIWithInput:
    def __init__(self) -> None:
        self.initialized = False
        self.messages: list[tuple[AgentMessage, str]] = []
        self.statuses: list[str] = []
        self.input_queue: list[str] = []
        self.input_index = 0
        self.should_interrupt = False
        self.interrupt_count = 0

    async def initialize(self) -> None:
        self.initialized = True

    async def show_message(self, message: AgentMessage, source: str) -> None:
        self.messages.append((message, source))

    async def show_status(self, status: str) -> None:
        self.statuses.append(status)

    async def get_input(self) -> str | None:
        if self.input_index < len(self.input_queue):
            result = self.input_queue[self.input_index]
            self.input_index += 1
            return result
        return None


class MockSessionStore:
    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, str]] = {}

    async def get_session(self, agent_type: str, plan_id: str) -> str | None:
        if agent_type not in self.sessions:
            return None
        return self.sessions[agent_type].get(plan_id)

    async def save_session(self, agent_type: str, session_id: str, plan_id: str) -> None:
        if agent_type not in self.sessions:
            self.sessions[agent_type] = {}
        self.sessions[agent_type][plan_id] = session_id

    async def delete_session(self, agent_type: str, plan_id: str | None = None) -> None:
        if plan_id is None:
            if agent_type in self.sessions:
                del self.sessions[agent_type]
        else:
            if agent_type in self.sessions and plan_id in self.sessions[agent_type]:
                del self.sessions[agent_type][plan_id]


class MockLoggerFactory:
    def create_logger(self, name: str, session_id: str | None) -> MagicMock:
        logger = MagicMock()
        logger.info = MagicMock()
        logger.debug = MagicMock()
        logger.warning = MagicMock()
        return logger


@pytest.fixture()
def mock_execute_agent() -> MockAgentWithResume:
    return MockAgentWithResume()


@pytest.fixture()
def mock_ui() -> MockUIWithInput:
    return MockUIWithInput()


@pytest.fixture()
def mock_session_store() -> MockSessionStore:
    return MockSessionStore()


@pytest.fixture()
def mock_logger_factory() -> MockLoggerFactory:
    return MockLoggerFactory()


@pytest.fixture()
def mock_verify_agent() -> MockAgentWithResume:
    return MockAgentWithResume()
