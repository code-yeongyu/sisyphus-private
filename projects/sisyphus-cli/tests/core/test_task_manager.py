from __future__ import annotations

import pytest

from sisyphus_core.core.plans.models import (
    Background,
    BashVerification,
    LLMJudgeBy,
    LLMJudgeVerification,
    Metadata,
    Objectives,
    PlanDocument,
    RequiredBackground,
    SuccessVision,
    Todo,
    TodoStatus,
    UserRequest,
    VerificationItem,
    Workflow,
    WorkPlan,
)
from sisyphus_core.core.task_manager import TaskManager

pytestmark = [pytest.mark.anyio]


async def test_task_manager__if_work_plan_exists__finds_it(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[],
            )
        ],
    )

    manager = TaskManager(plan_doc, "test-plan")

    assert manager.work_plan.id == "test-plan"


async def test_task_manager__if_work_plan_missing__raises_error(
    _minimal_user_request: UserRequest,
    _minimal_objectives: Objectives,
    _minimal_background: Background,
    _minimal_required_background: RequiredBackground,
    _minimal_workflow: Workflow,
    _minimal_success_vision: SuccessVision,
) -> None:
    plan_doc = PlanDocument(version="3.0", metadata=Metadata(created_at="2025-11-06T00:00:00Z"), work_plans=[])

    with pytest.raises(ValueError, match="WorkPlan not found"):
        _ = TaskManager(plan_doc, "missing-plan")


async def test_find_todo_by_id__if_root_todo__returns_it(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[Todo(id="1", title="Task 1", status=TodoStatus.pending, references=[])],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    todo = manager.find_todo_by_id("1")

    assert todo is not None
    assert todo.id == "1"


async def test_find_todo_by_id__if_child_todo__returns_it(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[
                    Todo(
                        id="1",
                        title="Parent",
                        status=TodoStatus.pending,
                        references=[],
                        children=[Todo(id="1.1", title="Child", status=TodoStatus.pending, references=[])],
                    )
                ],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    todo = manager.find_todo_by_id("1.1")

    assert todo is not None
    assert todo.id == "1.1"


async def test_get_current_task__if_current_task_id_set__returns_task(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[Todo(id="1", title="Task 1", status=TodoStatus.in_progress, references=[])],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")
    manager.work_plan.work_mode.current_task_id = "1"

    current = manager.get_current_task()

    assert current is not None
    assert current.id == "1"


async def test_get_current_task__if_current_task_id_none__returns_none(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[Todo(id="1", title="Task 1", status=TodoStatus.pending, references=[])],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    current = manager.get_current_task()

    assert current is None


async def test_get_next_task__if_no_current__returns_first_pending(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[
                    Todo(id="1", title="Task 1", status=TodoStatus.completed, references=[]),
                    Todo(id="2", title="Task 2", status=TodoStatus.pending, references=[]),
                ],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    next_task = manager.get_next_task()

    assert next_task is not None
    assert next_task.id == "2"


async def test_get_next_task__if_in_progress_has_children__returns_first_child_pending(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[
                    Todo(
                        id="1",
                        title="Parent",
                        status=TodoStatus.in_progress,
                        references=[],
                        children=[
                            Todo(id="1.1", title="Child 1", status=TodoStatus.pending, references=[]),
                            Todo(id="1.2", title="Child 2", status=TodoStatus.pending, references=[]),
                        ],
                    )
                ],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    next_task = manager.get_next_task("1")

    assert next_task is not None
    assert next_task.id == "1.1"


async def test_get_previous_task__if_first_task__returns_none(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[
                    Todo(id="1", title="Task 1", status=TodoStatus.in_progress, references=[]),
                    Todo(id="2", title="Task 2", status=TodoStatus.pending, references=[]),
                ],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    previous = manager.get_previous_task("1")

    assert previous is None


async def test_get_previous_task__if_has_previous_sibling__returns_last_descendant(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[
                    Todo(
                        id="1",
                        title="Task 1",
                        status=TodoStatus.completed,
                        references=[],
                        children=[
                            Todo(id="1.1", title="Child 1.1", status=TodoStatus.completed, references=[]),
                            Todo(id="1.2", title="Child 1.2", status=TodoStatus.completed, references=[]),
                        ],
                    ),
                    Todo(id="2", title="Task 2", status=TodoStatus.in_progress, references=[]),
                ],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    previous = manager.get_previous_task("2")

    assert previous is not None
    assert previous.id == "1.2"


async def test_get_task_children__if_has_children__returns_children(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[
                    Todo(
                        id="1",
                        title="Parent",
                        status=TodoStatus.pending,
                        references=[],
                        children=[
                            Todo(id="1.1", title="Child 1", status=TodoStatus.pending, references=[]),
                            Todo(id="1.2", title="Child 2", status=TodoStatus.pending, references=[]),
                        ],
                    )
                ],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    children = manager.get_task_children("1")

    assert len(children) == 2
    assert children[0].id == "1.1"
    assert children[1].id == "1.2"


async def test_get_all_descendants__if_nested_children__returns_all(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[
                    Todo(
                        id="1",
                        title="Parent",
                        status=TodoStatus.pending,
                        references=[],
                        children=[
                            Todo(
                                id="1.1",
                                title="Child 1",
                                status=TodoStatus.pending,
                                references=[],
                                children=[
                                    Todo(id="1.1.1", title="Grandchild", status=TodoStatus.pending, references=[])
                                ],
                            ),
                            Todo(id="1.2", title="Child 2", status=TodoStatus.pending, references=[]),
                        ],
                    )
                ],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    descendants = manager.get_all_descendants("1")

    assert len(descendants) == 3
    assert descendants[0].id == "1.1"
    assert descendants[1].id == "1.1.1"
    assert descendants[2].id == "1.2"


async def test_check_task_completion__if_all_children_completed__can_complete(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[
                    Todo(
                        id="1",
                        title="Parent",
                        status=TodoStatus.in_progress,
                        references=[],
                        children=[
                            Todo(id="1.1", title="Child 1", status=TodoStatus.completed, references=[]),
                            Todo(id="1.2", title="Child 2", status=TodoStatus.completed, references=[]),
                        ],
                    )
                ],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    report = manager.check_task_completion("1")

    assert report.all_children_completed is True
    assert report.all_verifications_completed is True
    assert report.can_complete is True


async def test_check_task_completion__if_children_pending__cannot_complete(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[
                    Todo(
                        id="1",
                        title="Parent",
                        status=TodoStatus.in_progress,
                        references=[],
                        children=[
                            Todo(id="1.1", title="Child 1", status=TodoStatus.completed, references=[]),
                            Todo(id="1.2", title="Child 2", status=TodoStatus.pending, references=[]),
                        ],
                    )
                ],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    report = manager.check_task_completion("1")

    assert report.all_children_completed is False
    assert report.can_complete is False


async def test_check_task_completion__if_manual_verification_incomplete__cannot_complete(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given: task with manual verification that has verified=True but orchestrator_manually_verified=False

    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[
                    Todo(
                        id="1",
                        title="Task with incomplete manual verification",
                        status=TodoStatus.in_progress,
                        references=[],
                        verification_spec=[
                            VerificationItem(
                                id="v1",
                                title="Manual verification",
                                description="Manual check without bash",
                                verified=True,
                                orchestrator_manually_verified=False,
                                manual_verification_evidence="",
                                llm_judge=[
                                    LLMJudgeVerification(
                                        by=LLMJudgeBy.ORCHESTRATOR, instruction="Manual check instruction"
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    # when
    report = manager.check_task_completion("1")

    # then
    assert report.all_verifications_completed is True
    assert report.all_manual_verifications_completed is False
    assert report.manual_verification_summary["completed"] == 0
    assert report.manual_verification_summary["total"] == 1
    assert report.can_complete is False


async def test_check_task_completion__if_manual_verification_missing_evidence__cannot_complete(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given: manual verification with verified=True and orchestrator_manually_verified=True but no evidence

    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[
                    Todo(
                        id="1",
                        title="Task with missing evidence",
                        status=TodoStatus.in_progress,
                        references=[],
                        verification_spec=[
                            VerificationItem(
                                id="v1",
                                title="Manual verification",
                                description="Manual check without bash",
                                verified=True,
                                orchestrator_manually_verified=True,
                                manual_verification_evidence="",
                                llm_judge=[
                                    LLMJudgeVerification(
                                        by=LLMJudgeBy.ORCHESTRATOR, instruction="Manual check instruction"
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    # when
    report = manager.check_task_completion("1")

    # then
    assert report.all_verifications_completed is True
    assert report.all_manual_verifications_completed is False
    assert report.manual_verification_summary["completed"] == 0
    assert report.manual_verification_summary["total"] == 1
    assert report.can_complete is False


async def test_check_task_completion__if_all_manual_verification_complete__can_complete(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given: task with all three manual verification conditions met

    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[
                    Todo(
                        id="1",
                        title="Task with complete manual verification",
                        status=TodoStatus.in_progress,
                        references=[],
                        verification_spec=[
                            VerificationItem(
                                id="v1",
                                title="Manual verification",
                                description="Manual check without bash",
                                verified=True,
                                orchestrator_manually_verified=True,
                                manual_verification_evidence=(
                                    "Complete evidence with more than 100 characters to satisfy "
                                    "the validation requirements for manual verification evidence."
                                ),
                                llm_judge=[
                                    LLMJudgeVerification(
                                        by=LLMJudgeBy.ORCHESTRATOR, instruction="Manual check instruction"
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    # when
    report = manager.check_task_completion("1")

    # then
    assert report.all_verifications_completed is True
    assert report.all_manual_verifications_completed is True
    assert report.manual_verification_summary["completed"] == 1
    assert report.manual_verification_summary["total"] == 1
    assert report.can_complete is True


async def test_check_task_completion__if_mixed_verification_types_with_manual_incomplete__cannot_complete(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given: task with bash verification complete (verified=True only) and manual verification incomplete

    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[
                    Todo(
                        id="1",
                        title="Task with mixed verification types",
                        status=TodoStatus.in_progress,
                        references=[],
                        verification_spec=[
                            VerificationItem(
                                id="v1",
                                title="Bash verification",
                                description="Automated bash check",
                                verified=True,
                                orchestrator_manually_verified=False,
                                manual_verification_evidence="",
                                bash=[BashVerification(execute="echo test", expected_exit_code=0)],
                            ),
                            VerificationItem(
                                id="v2",
                                title="Manual verification",
                                description="Manual check without bash",
                                verified=True,
                                orchestrator_manually_verified=False,
                                manual_verification_evidence="",
                                llm_judge=[
                                    LLMJudgeVerification(
                                        by=LLMJudgeBy.ORCHESTRATOR, instruction="Manual check instruction"
                                    )
                                ],
                            ),
                        ],
                    )
                ],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    # when
    report = manager.check_task_completion("1")

    # then
    assert report.all_verifications_completed is True
    assert report.all_manual_verifications_completed is False
    assert report.manual_verification_summary["completed"] == 0
    assert report.manual_verification_summary["total"] == 2
    assert report.can_complete is False


async def test_check_task_completion__if_no_verifications__can_complete(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given: task with empty verification_spec list
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-plan",
                name="Test Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                todos=[
                    Todo(
                        id="1",
                        title="Task with no verifications",
                        status=TodoStatus.in_progress,
                        references=[],
                        verification_spec=[],
                    )
                ],
            )
        ],
    )
    manager = TaskManager(plan_doc, "test-plan")

    # when
    report = manager.check_task_completion("1")

    # then
    assert report.all_verifications_completed is True
    assert report.all_manual_verifications_completed is True
    assert report.manual_verification_summary["completed"] == 0
    assert report.manual_verification_summary["total"] == 0
    assert report.can_complete is True
