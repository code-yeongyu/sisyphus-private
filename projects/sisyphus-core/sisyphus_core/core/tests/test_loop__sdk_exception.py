# pyright: reportArgumentType=false, reportMissingImports=false, reportImplicitRelativeImport=false
from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from sisyphus_core.core.loop import ExecutionLoop
from sisyphus_core.core.tests.test_loop import MockAgent, MockStatusManager
from sisyphus_core.utils.errors import RetryRequiredError
from sisyphus_core.utils.types import AgentMessage

if TYPE_CHECKING:
    pass

pytestmark = [pytest.mark.anyio]


async def test_execute_phase__if_sdk_exception__deletes_session_and_retries() -> None:
    # given
    execute_agent = MockAgentWithSDKError()
    execute_agent.fail_on_first_stream = True

    ui = MockUI()
    session_store = MockSessionStore()
    await session_store.save_session("mockwithsdkerror", "invalid-session-id", "default")
    logger_factory = MockLoggerFactory()

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [AgentMessage(role="assistant", content="FULLY_DONE = TRUE")]
    task_validator = MockTaskValidator(all_complete=True)

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore
        verify_agent=verify_agent,  # type: ignore
        ui=ui,  # type: ignore
        session_store=session_store,  # type: ignore
        logger_factory=logger_factory,  # type: ignore
        task_validator=task_validator,  # type: ignore
        status_manager=MockStatusManager("default"),  # type: ignore
    )

    loop.state.set_plan_id("default")

    # when
    retry_count = 0
    max_retries = 3
    success = False

    while retry_count < max_retries:
        should_retry = False
        try:
            await loop.phase_orchestrator.execute_phase(prompt="Test prompt", extra=None)
            success = True
            break
        except* RetryRequiredError:
            retry_count += 1
            should_retry = True

        if not should_retry:
            break

    # then
    assert success is True
    assert execute_agent.start_session_call_count == 2
    loaded_session = await session_store.get_session("mockwithsdkerror", "default")
    assert loaded_session is not None
    assert loaded_session == "new-session-2"


async def test_execute_phase__if_sdk_exception_3_times__exits_phase() -> None:
    # given
    execute_agent = MockAgentWithSDKError()
    execute_agent.always_fail = True

    ui = MockUI()
    session_store = MockSessionStore()
    await session_store.save_session("mockwithsdkerror", "invalid-session-id", "default")
    logger_factory = MockLoggerFactory()

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [AgentMessage(role="assistant", content="FULLY_DONE = TRUE")]
    task_validator = MockTaskValidator(all_complete=True)

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore
        verify_agent=verify_agent,  # type: ignore
        ui=ui,  # type: ignore
        session_store=session_store,  # type: ignore
        logger_factory=logger_factory,  # type: ignore
        task_validator=task_validator,  # type: ignore
        status_manager=MockStatusManager("default"),  # type: ignore
    )

    loop.state.set_plan_id("default")

    # when
    retry_count = 0
    max_retries = 5
    final_exception_raised = False

    while retry_count < max_retries:
        should_retry = False
        try:
            await loop.phase_orchestrator.execute_phase(prompt="Test prompt", extra=None)
            break
        except* RetryRequiredError:
            retry_count += 1
            should_retry = True

        if loop.state.should_exit_execute_phase():
            final_exception_raised = True
            break

        if not should_retry:
            break

    # then
    assert final_exception_raised is True
    assert execute_agent.stream_call_count == 3
    loaded_session = await session_store.get_session("mockwithsdkerror", "default")
    assert loaded_session is None


async def test_verify_phase__if_sdk_exception__deletes_session_and_retries() -> None:
    # given
    verify_agent = MockAgentWithSDKError()
    verify_agent.fail_on_first_stream = True

    ui = MockUI()
    session_store = MockSessionStore()
    await session_store.save_session("mockwithsdkerror", "invalid-session-id", "default")
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator()

    loop = ExecutionLoop(
        execute_agent=MagicMock(),  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
        status_manager=MockStatusManager("default"),  # type: ignore[arg-type]
    )

    loop.state.set_plan_id("default")

    # when
    retry_count = 0
    max_retries = 3
    success = False

    while retry_count < max_retries:
        should_retry = False
        try:
            _ = await loop.phase_orchestrator.verify_phase(prompt="Test prompt", extra=None)
            success = True
            break
        except* RetryRequiredError:
            retry_count += 1
            should_retry = True

        if not should_retry:
            break

    # then
    assert success is True
    assert verify_agent.start_session_call_count == 2
    loaded_session = await session_store.get_session("mockwithsdkerror", "default")
    assert loaded_session is None


class MockAgentWithSDKError:
    def __init__(self) -> None:
        self.supports_interactive = False
        self.initialized = False
        self.session_id: str | None = None
        self.sent_messages: list[str] = []
        self.closed = False
        self.start_session_call_count = 0
        self.stream_call_count = 0
        self.fail_on_first_stream = False
        self.always_fail = False

    async def initialize(self) -> None:
        self.initialized = True

    async def start_session(self, session_id: str | None = None) -> str:
        self.start_session_call_count += 1
        if session_id is not None:
            self.session_id = session_id
        else:
            self.session_id = f"new-session-{self.start_session_call_count}"
        return self.session_id

    async def send(self, message: str) -> None:
        self.sent_messages.append(message)

    def stream(self) -> AsyncIterator[AgentMessage]:
        async def _generator() -> AsyncIterator[AgentMessage]:
            self.stream_call_count += 1

            if self.always_fail:
                raise Exception("Command failed with exit code 1")

            if self.fail_on_first_stream and self.stream_call_count == 1:
                raise Exception("Command failed with exit code 1")

            yield AgentMessage(role="assistant", content="Success", metadata={})

        return _generator()

    async def close(self) -> None:
        self.closed = True


class MockUI:
    def __init__(self) -> None:
        self.initialized = False
        self.messages: list[tuple[AgentMessage, str]] = []
        self.statuses: list[str] = []
        self.closed = False

    async def initialize(self) -> None:
        self.initialized = True

    async def show_message(self, message: AgentMessage, source: str) -> None:
        self.messages.append((message, source))

    async def show_status(self, status: str) -> None:
        self.statuses.append(status)

    async def get_input(self) -> str | None:
        return None

    async def close(self) -> None:
        self.closed = True


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

    async def delete_session(self, agent_type: str, plan_id: str) -> None:
        if agent_type in self.sessions and plan_id in self.sessions[agent_type]:
            del self.sessions[agent_type][plan_id]

    async def list_sessions(self) -> dict[str, dict[str, dict[str, str]]]:
        return {k: {p: {"session_id": s} for p, s in v.items()} for k, v in self.sessions.items()}


class MockLoggerFactory:
    @staticmethod
    def create_logger(agent_type: str, session_id: str | None = None, _log_dir: Path = Path("./logs")) -> MagicMock:
        logger = MagicMock()
        logger.info = MagicMock()
        logger.debug = MagicMock()
        logger.warning = MagicMock()
        logger.error = MagicMock()
        return logger


class MockTaskValidator:
    def __init__(self, all_complete: bool = False) -> None:
        self._all_complete = all_complete
        self.todolist_path = Path(".sisyphus/tasks/test-plan.yaml")

    def read_content(self) -> str:
        return "mock content"

    async def check_all_goals_accomplished(self, _content: str | None = None) -> bool:
        return self._all_complete

    async def check_all_checkboxes_completed(self, _content: str | None = None) -> bool:
        return self._all_complete
