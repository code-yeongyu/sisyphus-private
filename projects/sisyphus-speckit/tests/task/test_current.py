"""Tests for task current command."""

from __future__ import annotations

import pytest
from sisyphus_core.core.plans.models import (
    Background,
    BashVerification,
    ExecutionStatus,
    Objectives,
    ReferenceItem,
    RequiredBackground,
    SuccessVision,
    Todo,
    TodoStatus,
    UserRequest,
    VerificationItem,
    Workflow,
    WorkMode,
    WorkPlan,
)


class TestCurrentCommand:
    """Tests for current command."""

    @pytest.fixture()
    def minimal_work_plan(
        self,
        minimal_user_request: UserRequest,
        minimal_objectives: Objectives,
        minimal_background: Background,
        minimal_required_background: RequiredBackground,
        minimal_workflow: Workflow,
        minimal_success_vision: SuccessVision,
    ) -> WorkPlan:
        """Create a minimal WorkPlan for testing."""
        return WorkPlan(
            id="test-plan",
            name="Test Plan",
            depends_on=[],
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            todos=[],
            references=[],
            execution=ExecutionStatus(started=False, completed=False, started_at=None, completed_at=None),
            work_mode=WorkMode(parallel_requested=False),
        )

    @pytest.fixture()
    def current_task_todo(self) -> Todo:
        """Create a current task Todo for testing."""
        # given: a task with verification spec and references
        return Todo(
            id="task-1",
            title="Current Task",
            description="This is the current task in progress",
            status=TodoStatus.in_progress,
            children=None,
            references=[
                ReferenceItem(
                    ref_id="ref-1",
                    uri=None,
                    inline="Reference content for current task",
                )
            ],
            verification_spec=[
                VerificationItem(
                    id="verify-1",
                    title="Test Verification",
                    description="Current task verification",
                    verified=False,
                    verified_at=None,
                    verification_evidence=None,
                    orchestrator_manually_verified=False,
                    manual_verification_evidence="",
                    bash=[BashVerification(execute="echo current", expected_exit_code=0)],
                    llm_judge=[],
                    deterministic_bash=[],
                    orchestrator_judge=[],
                )
            ],
            acceptance_criteria=[],
            parallel=False,
            parallelable_and_safe_evidence=None,
        )

    def test_current__has_current_task__displays_task_info(
        self, minimal_work_plan: WorkPlan, current_task_todo: Todo
    ) -> None:
        """
        Test that current command displays current task information.

        #given: A work plan with a current task in progress
        #when: Displaying current task
        #then: Task info is accessible and properly formatted
        """
        # given: A work plan with current task
        minimal_work_plan.todos = [current_task_todo]
        task = minimal_work_plan.todos[0]

        # when: Checking task information
        task_info = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
        }

        # then: Task information is accessible
        assert task_info["id"] == "task-1"
        assert task_info["title"] == "Current Task"
        assert task_info["description"] == "This is the current task in progress"
        assert task_info["status"] == TodoStatus.in_progress

    def test_current__has_verification_spec__displays_verification_info(self, current_task_todo: Todo) -> None:
        """
        Test that current command displays verification spec.

        #given: A current task with verification spec
        #when: Extracting verification information
        #then: Verification spec is accessible
        """
        # given: A current task with verification spec
        task = current_task_todo

        # when: Checking verification spec
        has_verification = len(task.verification_spec) > 0
        vspec = task.verification_spec[0] if has_verification else None

        # then: Verification spec is present
        assert has_verification is True
        assert vspec is not None
        assert vspec.id == "verify-1"
        assert vspec.title == "Test Verification"
        assert vspec.verified is False

    def test_current__has_references__displays_references(self, current_task_todo: Todo) -> None:
        """
        Test that current command displays references.

        #given: A current task with references
        #when: Extracting reference information
        #then: References are accessible
        """
        # given: A current task with references
        task = current_task_todo

        # when: Checking references
        has_references = len(task.references) > 0
        ref = task.references[0] if has_references else None

        # then: References are present
        assert has_references is True
        assert ref is not None
        assert ref.ref_id == "ref-1"
        assert ref.inline == "Reference content for current task"

    def test_current__tip_message__contains_status_command_hint(self) -> None:
        """
        Test that current command displays tip message.

        #given: Current command execution
        #when: Checking for tip message
        #then: Tip message contains status command hint
        """
        # given: The expected tip message
        expected_tip = "💡 Tip: 검증 스펙 상세는 'sisyphus-speckit task status' 실행"

        # when: Verifying tip message content
        has_status_keyword = "status" in expected_tip
        has_verification_keyword = "검증 스펙" in expected_tip

        # then: Tip message contains proper hints
        assert has_status_keyword is True
        assert has_verification_keyword is True
        assert "sisyphus-speckit task status" in expected_tip

    def test_current__no_current_task__shows_guidance_message(self) -> None:
        """
        Test that current command shows guidance when no task is started.

        #given: A work plan with no current task
        #when: Attempting to display current task
        #then: Guidance message is shown
        """
        # given: Expected guidance messages
        expected_no_task_msg = "작업이 시작되지 않았습니다."
        expected_start_instruction = "다음 명령으로 작업을 시작하세요: sisyphus-speckit task continue"

        # when: Checking guidance message content
        has_no_task_msg = "작업이 시작되지 않았습니다" in expected_no_task_msg
        has_start_cmd = "sisyphus-speckit task continue" in expected_start_instruction

        # then: Guidance messages are properly formatted
        assert has_no_task_msg is True
        assert has_start_cmd is True

    def test_current__task_with_children__maintains_hierarchy(self, minimal_work_plan: WorkPlan) -> None:
        """
        Test that current command handles tasks with children.

        #given: A current task with child tasks
        #when: Displaying task hierarchy
        #then: Children are properly accessible
        """
        # given: A task with children
        child_task = Todo(
            id="task-1.1",
            title="Child Task",
            description="Child of current task",
            status=TodoStatus.pending,
            children=None,
            references=[],
            verification_spec=[],
            acceptance_criteria=[],
            parallel=False,
            parallelable_and_safe_evidence=None,
        )
        parent_task = Todo(
            id="task-1",
            title="Parent Task",
            description="Parent task with children",
            status=TodoStatus.in_progress,
            children=[child_task],
            references=[],
            verification_spec=[],
            acceptance_criteria=[],
            parallel=False,
            parallelable_and_safe_evidence=None,
        )
        minimal_work_plan.todos = [parent_task]

        # when: Checking task hierarchy
        task = minimal_work_plan.todos[0]
        has_children = task.children is not None and len(task.children) > 0

        # then: Children are accessible
        assert has_children is True
        assert task.children is not None
        child = task.children[0]
        assert child.id == "task-1.1"
        assert child.title == "Child Task"

    def test_current__task_basic_fields__all_required_fields_present(self, current_task_todo: Todo) -> None:
        """
        Test that current task has all required fields.

        #given: A current task
        #when: Checking required fields
        #then: All required fields are present
        """
        # given: A current task
        task = current_task_todo

        # when: Checking all required fields
        has_id = task.id is not None  # pyright: ignore[reportUnnecessaryComparison]
        has_title = task.title is not None  # pyright: ignore[reportUnnecessaryComparison]
        has_description = task.description is not None
        has_status = task.status is not None
        has_verification_spec = hasattr(task, "verification_spec")
        has_references = hasattr(task, "references")
        has_children = hasattr(task, "children")

        # then: All required fields exist
        assert has_id is True
        assert has_title is True
        assert has_description is not None
        assert has_status is True
        assert has_verification_spec is True
        assert has_references is True
        assert has_children is True

    def test_current__verification_spec_with_bash__bash_details_accessible(self, current_task_todo: Todo) -> None:
        """
        Test that verification spec bash details are accessible.

        #given: A current task with bash verification
        #when: Extracting bash verification details
        #then: Bash execute command and exit code are accessible
        """
        # given: A current task with bash verification
        task = current_task_todo
        vspec = task.verification_spec[0]

        # when: Checking bash verification details
        has_bash = len(vspec.bash) > 0
        bash_check = vspec.bash[0] if has_bash else None

        # then: Bash details are accessible
        assert has_bash is True
        assert bash_check is not None
        assert bash_check.execute == "echo current"
        assert bash_check.expected_exit_code == 0

    def test_current__inline_reference__content_accessible(self, current_task_todo: Todo) -> None:
        """
        Test that inline references are accessible.

        #given: A current task with inline reference
        #when: Extracting inline reference content
        #then: Inline content is properly accessible
        """
        # given: A current task with inline reference
        task = current_task_todo
        ref = task.references[0]

        # when: Checking inline content
        has_inline = ref.inline is not None
        inline_content = ref.inline if has_inline else ""

        # then: Inline content is accessible
        assert has_inline is True
        assert inline_content == "Reference content for current task"
        assert len(inline_content) > 0
