from __future__ import annotations

import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from sisyphus_core.core.loop import ExecutionLoop
from sisyphus_core.core.plans.loader import save_plan
from sisyphus_core.core.plans.models import (
    AcceptanceCriteriaChecklist,
    AcceptanceCriteriaForVerificationAgent,
    Background,
    ExecutionStatus,
    Metadata,
    Objectives,
    PlanDocument,
    RequiredBackground,
    SuccessVision,
    Todo,
    TodoStatus,
    UserRequest,
    Workflow,
    WorkPlan,
)
from sisyphus_core.core.session import SessionStore
from sisyphus_core.core.status.manager import StatusManager
from sisyphus_core.core.task_validator import YamlTaskValidator
from sisyphus_core.utils.types import AgentMessage

pytestmark = [pytest.mark.anyio]


async def test_loop__if_execution_completed_is_true__triggers_verify_phase() -> None:
    """
    #given: execution.completed = True인 WorkPlan
    #when: ExecutionLoop가 실행되면
    #then: Verify phase가 트리거됨
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        plan_path = Path(tmpdir) / "test.yaml"

        work_plan = WorkPlan(
            id="test-plan",
            name="Test Plan",
            depends_on=[],
            user_request=UserRequest(
                original="Test request",
                created_at="2025-01-01T00:00:00+00:00",
                additional=[],
            ),
            objectives=Objectives(core="Test objective", detailed=[]),
            background=Background(
                current_situation="Test",
                reason_for_change="Test",
                changes_to_make="Test",
            ),
            required_background=RequiredBackground(description="Test"),
            workflow=Workflow(dependency_diagram="Test", critical_path=[]),
            success_vision=SuccessVision(
                user_perspective=[],
                business_perspective=[],
                technical_criteria=[],
            ),
            final_verification=[],
            todos=[
                Todo(
                    id="1",
                    title="Test task",
                    description="Test description",
                    status=TodoStatus.completed,
                    references=[],
                    verification_spec=[],
                    parallel=False,
                )
            ],
            acceptance_criteria_for_verification_agent=[
                AcceptanceCriteriaForVerificationAgent(
                    id="test-acceptance-1",
                    title="Test verification criteria 1",
                    checklists=[
                        AcceptanceCriteriaChecklist(
                            id="test-checklist-1-1",
                            title="Test checklist 1-1",
                            content="Test verification content 1-1",
                        ),
                        AcceptanceCriteriaChecklist(
                            id="test-checklist-1-2",
                            title="Test checklist 1-2",
                            content="Test verification content 1-2",
                        ),
                    ],
                ),
                AcceptanceCriteriaForVerificationAgent(
                    id="test-acceptance-2",
                    title="Test verification criteria 2",
                    checklists=[
                        AcceptanceCriteriaChecklist(
                            id="test-checklist-2-1",
                            title="Test checklist 2-1",
                            content="Test verification content 2-1",
                        ),
                        AcceptanceCriteriaChecklist(
                            id="test-checklist-2-2",
                            title="Test checklist 2-2",
                            content="Test verification content 2-2",
                        ),
                    ],
                ),
                AcceptanceCriteriaForVerificationAgent(
                    id="test-acceptance-3",
                    title="Test verification criteria 3",
                    checklists=[
                        AcceptanceCriteriaChecklist(
                            id="test-checklist-3-1",
                            title="Test checklist 3-1",
                            content="Test verification content 3-1",
                        ),
                        AcceptanceCriteriaChecklist(
                            id="test-checklist-3-2",
                            title="Test checklist 3-2",
                            content="Test verification content 3-2",
                        ),
                    ],
                ),
                AcceptanceCriteriaForVerificationAgent(
                    id="test-acceptance-4",
                    title="Test verification criteria 4",
                    checklists=[
                        AcceptanceCriteriaChecklist(
                            id="test-checklist-4-1",
                            title="Test checklist 4-1",
                            content="Test verification content 4-1",
                        ),
                        AcceptanceCriteriaChecklist(
                            id="test-checklist-4-2",
                            title="Test checklist 4-2",
                            content="Test verification content 4-2",
                        ),
                    ],
                ),
            ],
            references=[],
            execution=ExecutionStatus(
                started=True,
                completed=True,
                started_at="2025-01-01T00:00:00+00:00",
                completed_at="2025-01-01T01:00:00+00:00",
                fully_done_at=None,
            ),
        )

        plan_doc = PlanDocument(
            version="3.0",
            metadata=Metadata(
                created_at="2025-01-01T00:00:00+00:00",
                updated_at="2025-01-01T00:00:00+00:00",
            ),
            work_plans=[work_plan],
        )

        await save_plan(plan_path, plan_doc)

        status_path = Path(tmpdir) / "status.json"
        status_manager = StatusManager(status_path=status_path)
        await status_manager.set_current(plan_path=str(plan_path), plan_root=str(tmpdir))

        execute_agent = AsyncMock(
            spec=["supports_interactive", "initialize", "start_session", "send", "stream", "close", "session_id"]
        )
        execute_agent.supports_interactive = False
        execute_agent.session_id = None
        execute_agent.initialize = AsyncMock(return_value=None)
        execute_agent.start_session = AsyncMock(return_value="session-1")
        execute_agent.send = AsyncMock(return_value=None)

        async def execute_stream_generator() -> AsyncIterator[AgentMessage]:
            yield AgentMessage(role="assistant", content="Execute complete")

        execute_agent.stream = MagicMock(return_value=execute_stream_generator())
        execute_agent.close = AsyncMock(return_value=None)

        verify_agent = AsyncMock(
            spec=["supports_interactive", "initialize", "start_session", "send", "stream", "close", "session_id"]
        )
        verify_agent.supports_interactive = False
        verify_agent.session_id = None
        verify_agent.initialize = AsyncMock(return_value=None)
        verify_agent.start_session = AsyncMock(return_value="verify-session-1")
        verify_agent.send = AsyncMock(return_value=None)

        async def verify_stream_generator() -> AsyncIterator[AgentMessage]:
            yield AgentMessage(role="assistant", content="FULLY_DONE = TRUE")

        verify_agent.stream = MagicMock(return_value=verify_stream_generator())
        verify_agent.close = AsyncMock(return_value=None)

        ui = AsyncMock()
        ui.initialize = AsyncMock(return_value=None)
        ui.show_message = AsyncMock(return_value=None)
        ui.show_status = AsyncMock(return_value=None)
        ui.get_input = AsyncMock(return_value=None)

        session_store = SessionStore(base_dir=Path(tmpdir))
        task_validator = YamlTaskValidator(todolist_path=plan_path)

        logger_factory_mock = MagicMock()
        logger_factory_mock.create_logger = MagicMock(return_value=MagicMock())

        loop = ExecutionLoop(
            execute_agent=execute_agent,
            verify_agent=verify_agent,
            ui=ui,
            logger_factory=logger_factory_mock,  # type: ignore[arg-type]
            session_store=session_store,
            status_manager=status_manager,
            task_validator=task_validator,
        )

        await loop.run(
            execute_extra="Execute extra context",
            verify_extra="Verify extra context",
        )

        assert verify_agent.initialize.called
        assert verify_agent.start_session.called
