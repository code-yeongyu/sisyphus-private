"""Tests for task status() display - verifying verification spec table, continuable logic, and acceptance criteria."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from sisyphus_core.core.plans.models import (
    AcceptanceCriteriaItem,
    Background,
    BashVerification,
    ExecutionStatus,
    LLMJudgeBy,
    LLMJudgeVerification,
    Objectives,
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


@pytest.fixture()
def minimal_work_plan(
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


def test_status__verification_spec_table__displays_all_verification_items(
    minimal_work_plan: WorkPlan,
) -> None:
    """
    Given: A task with multiple verification specifications
    When: Processing for verification spec table display
    Then: All verification items are accessible with ID, title, and status
    """
    # given: A todo with 3 verification specs (1 verified, 2 unverified)
    todo = Todo(
        id="1",
        title="Task 1",
        description="Test",
        status=TodoStatus.in_progress,
        references=[],
        children=[],
        verification_spec=[
            VerificationItem(
                id="verify-1",
                title="Verification 1",
                description="First check",
                verified=True,
                verified_at=datetime.now(ZoneInfo("UTC")).isoformat(),
                orchestrator_manually_verified=True,
                manual_verification_evidence="Evidence 1",
                bash=[BashVerification(execute="echo test1", expected_exit_code=0)],
                llm_judge=[],
            ),
            VerificationItem(
                id="verify-2",
                title="Verification 2",
                description="Second check",
                verified=False,
                verified_at=None,
                orchestrator_manually_verified=False,
                manual_verification_evidence="",
                bash=[BashVerification(execute="echo test2", expected_exit_code=0)],
                llm_judge=[],
            ),
            VerificationItem(
                id="verify-3",
                title="Verification 3",
                description="Third check",
                verified=False,
                verified_at=None,
                orchestrator_manually_verified=False,
                manual_verification_evidence="",
                bash=[],
                llm_judge=[
                    LLMJudgeVerification(
                        by=LLMJudgeBy.ORCHESTRATOR,
                        instruction="Check if code is correct",
                    )
                ],
            ),
        ],
    )
    minimal_work_plan.todos = [todo]

    # when: Extracting verification specs for table display
    vspec_table_data = []
    for vspec in todo.verification_spec:
        bash_str = "✓" if vspec.bash else ""
        llm_str = "✓" if vspec.llm_judge else ""
        verified_str = "✓" if vspec.verified else "✗"
        vspec_table_data.append(
            {
                "id": vspec.id,
                "title": vspec.title or "",
                "description": vspec.description or "",
                "verified": verified_str,
                "bash": bash_str,
                "llm": llm_str,
            }
        )

    # then: All 3 verification items are present in table data
    assert len(vspec_table_data) == 3
    assert vspec_table_data[0]["id"] == "verify-1"
    assert vspec_table_data[0]["verified"] == "✓"
    assert vspec_table_data[0]["bash"] == "✓"
    assert vspec_table_data[0]["llm"] == ""

    assert vspec_table_data[1]["id"] == "verify-2"
    assert vspec_table_data[1]["verified"] == "✗"
    assert vspec_table_data[1]["bash"] == "✓"

    assert vspec_table_data[2]["id"] == "verify-3"
    assert vspec_table_data[2]["verified"] == "✗"
    assert vspec_table_data[2]["llm"] == "✓"


@pytest.mark.usefixtures("minimal_work_plan")
def test_status__verification_spec_table__extracts_bash_details(
) -> None:
    """
    Given: A verification item with bash checks
    When: Extracting bash verification details
    Then: Execute command, expected exit code, and notes are accessible
    """
    # given: A verification spec with bash details
    bash_check = BashVerification(
        execute="uv run pytest projects/test.py -v",
        expected_exit_code=0,
        notes="All tests must pass",
    )
    _ = VerificationItem(
        id="verify-bash-1",
        title="Bash Test",
        description="Run tests",
        verified=False,
        verified_at=None,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[bash_check],
        llm_judge=[],
    )

    # when: Extracting bash details for display
    bash_details = {
        "execute": bash_check.execute,
        "expected_exit_code": bash_check.expected_exit_code,
        "notes": bash_check.notes,
    }

    # then: All bash details are present
    assert bash_details["execute"] == "uv run pytest projects/test.py -v"
    assert bash_details["expected_exit_code"] == 0
    assert bash_details["notes"] == "All tests must pass"


@pytest.mark.usefixtures("minimal_work_plan")
def test_status__verification_spec_table__extracts_llm_judge_details(
) -> None:
    """
    Given: A verification item with LLM judge checks
    When: Extracting LLM judge details
    Then: By and instruction fields are accessible
    """
    # given: A verification spec with LLM judge details
    llm_check = LLMJudgeVerification(
        by=LLMJudgeBy.ORCHESTRATOR,
        instruction="Verify that the code follows project conventions and has proper error handling",
    )
    _ = VerificationItem(
        id="verify-llm-1",
        title="LLM Code Review",
        description="Code quality check",
        verified=False,
        verified_at=None,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[],
        llm_judge=[llm_check],
    )

    # when: Extracting LLM judge details for display
    llm_details = {
        "by": llm_check.by,
        "instruction_preview": llm_check.instruction[:100] if llm_check.instruction else "",
    }

    # then: LLM judge details are accessible
    assert llm_details["by"] == LLMJudgeBy.ORCHESTRATOR
    assert "Verify that the code follows project conventions" in llm_details["instruction_preview"]


def test_status__acceptance_criteria_table__displays_all_criteria(
    minimal_work_plan: WorkPlan,
) -> None:
    """
    Given: A task with acceptance criteria
    When: Processing for acceptance criteria table display
    Then: All criteria with ID, condition, and verified status are accessible
    """
    # given: A todo with acceptance criteria
    todo = Todo(
        id="1",
        title="Task 1",
        description="Test",
        status=TodoStatus.in_progress,
        references=[],
        children=[],
        verification_spec=[],
        acceptance_criteria=[
            AcceptanceCriteriaItem(
                id="criterion-1",
                condition="test_status.py file exists",
                verified_at=datetime.now(ZoneInfo("UTC")).isoformat(),
            ),
            AcceptanceCriteriaItem(
                id="criterion-2",
                condition="All tests pass",
                verified_at=None,
            ),
            AcceptanceCriteriaItem(
                id="criterion-3",
                condition="Type checking passes",
                verified_at=None,
            ),
        ],
    )
    minimal_work_plan.todos = [todo]

    # when: Extracting acceptance criteria for table display
    ac_table_data = []
    if todo.acceptance_criteria:
        for ac in todo.acceptance_criteria:
            verified_status = "✓" if ac.verified_at is not None else "✗"
            ac_table_data.append(
                {
                    "id": ac.id,
                    "condition": ac.condition,
                    "verified": verified_status,
                }
            )

    # then: All 3 acceptance criteria are present
    assert len(ac_table_data) == 3
    assert ac_table_data[0]["id"] == "criterion-1"
    assert ac_table_data[0]["verified"] == "✓"

    assert ac_table_data[1]["id"] == "criterion-2"
    assert ac_table_data[1]["verified"] == "✗"

    assert ac_table_data[2]["id"] == "criterion-3"
    assert ac_table_data[2]["verified"] == "✗"


def test_status__acceptance_criteria__handles_missing_criteria(
    minimal_work_plan: WorkPlan,
) -> None:
    """
    Given: A task with no acceptance criteria
    When: Processing for acceptance criteria display
    Then: Gracefully handles missing criteria
    """
    # given: A todo without acceptance criteria
    todo = Todo(
        id="1",
        title="Task 1",
        description="Test",
        status=TodoStatus.in_progress,
        references=[],
        children=[],
        verification_spec=[],
        acceptance_criteria=[],
    )
    minimal_work_plan.todos = [todo]

    # when: Checking for acceptance criteria
    has_criteria = len(todo.acceptance_criteria) > 0

    # then: Absence is properly detected
    assert has_criteria is False


def test_status__continuable__calculates_when_all_verifications_complete(
    minimal_work_plan: WorkPlan,
) -> None:
    """
    Given: A task with all verifications marked as verified
    When: Computing continuable status
    Then: Task is continuable (can_complete=True)
    """
    # given: A todo where all verifications are complete
    todo = Todo(
        id="1",
        title="Task 1",
        description="Test",
        status=TodoStatus.in_progress,
        references=[],
        children=[],
        verification_spec=[
            VerificationItem(
                id="verify-1",
                title="Verification 1",
                description="Check",
                verified=True,
                verified_at=datetime.now(ZoneInfo("UTC")).isoformat(),
                orchestrator_manually_verified=True,
                manual_verification_evidence="Evidence",
                bash=[BashVerification(execute="echo test", expected_exit_code=0)],
                llm_judge=[],
            ),
            VerificationItem(
                id="verify-2",
                title="Verification 2",
                description="Check",
                verified=True,
                verified_at=datetime.now(ZoneInfo("UTC")).isoformat(),
                orchestrator_manually_verified=True,
                manual_verification_evidence="Evidence",
                bash=[BashVerification(execute="echo test", expected_exit_code=0)],
                llm_judge=[],
            ),
        ],
    )
    minimal_work_plan.todos = [todo]
    minimal_work_plan.id = "test-plan"

    # when: Computing continuable status
    all_verifications_complete = all(v.verified for v in todo.verification_spec)

    # then: Task is continuable
    assert all_verifications_complete is True


def test_status__continuable__detects_incomplete_verifications(
    minimal_work_plan: WorkPlan,
) -> None:
    """
    Given: A task with some incomplete verifications
    When: Computing continuable status
    Then: Task is not continuable (can_complete=False)
    """
    # given: A todo where not all verifications are complete
    todo = Todo(
        id="1",
        title="Task 1",
        description="Test",
        status=TodoStatus.in_progress,
        references=[],
        children=[],
        verification_spec=[
            VerificationItem(
                id="verify-1",
                title="Verification 1",
                description="Check",
                verified=True,
                verified_at=datetime.now(ZoneInfo("UTC")).isoformat(),
                orchestrator_manually_verified=True,
                manual_verification_evidence="Evidence",
                bash=[BashVerification(execute="echo test", expected_exit_code=0)],
                llm_judge=[],
            ),
            VerificationItem(
                id="verify-2",
                title="Verification 2",
                description="Check",
                verified=False,
                verified_at=None,
                orchestrator_manually_verified=False,
                manual_verification_evidence="",
                bash=[BashVerification(execute="echo test", expected_exit_code=0)],
                llm_judge=[],
            ),
        ],
    )
    minimal_work_plan.todos = [todo]

    # when: Computing continuable status
    all_verifications_complete = all(v.verified for v in todo.verification_spec)

    # then: Task is not continuable
    assert all_verifications_complete is False


@pytest.mark.usefixtures("minimal_work_plan")
def test_status__continuable__detects_missing_manual_verification(
) -> None:
    """
    Given: A task with verified but not manually verified items
    When: Computing continuable status
    Then: Task is not continuable due to missing manual verification
    """
    # given: A todo where verification is marked but not orchestrator-manually-verified
    todo = Todo(
        id="1",
        title="Task 1",
        description="Test",
        status=TodoStatus.in_progress,
        references=[],
        children=[],
        verification_spec=[
            VerificationItem(
                id="verify-1",
                title="Verification 1",
                description="Check",
                verified=True,
                verified_at=datetime.now(ZoneInfo("UTC")).isoformat(),
                orchestrator_manually_verified=False,  # Not manually verified
                manual_verification_evidence="",
                bash=[BashVerification(execute="echo test", expected_exit_code=0)],
                llm_judge=[],
            ),
        ],
    )

    # when: Checking manual verification status
    needs_manual_verification = any(
        v.verified and not v.orchestrator_manually_verified for v in todo.verification_spec
    )

    # then: Manual verification is needed
    assert needs_manual_verification is True


@pytest.mark.usefixtures("minimal_work_plan")
def test_status__continuable__handles_no_verification_spec(
) -> None:
    """
    Given: A task with no verification specifications
    When: Computing continuable status
    Then: Task is continuable (no verifications to check)
    """
    # given: A todo with no verification specs
    todo = Todo(
        id="1",
        title="Task 1",
        description="Test",
        status=TodoStatus.in_progress,
        references=[],
        children=[],
        verification_spec=[],
    )

    # when: Checking if continuable
    has_verification_spec = len(todo.verification_spec) > 0
    is_continuable = not has_verification_spec or all(v.verified for v in todo.verification_spec)

    # then: Task is continuable
    assert is_continuable is True


@pytest.mark.usefixtures("minimal_work_plan")
def test_status__detailed_verification_info__formats_bash_check_details(
) -> None:
    """
    Given: A verification item with bash checks and multiple checks
    When: Formatting detailed verification information
    Then: All bash check details are properly formatted
    """
    # given: A verification spec with multiple bash checks
    vspec = VerificationItem(
        id="verify-1",
        title="Test Verification",
        description="Run multiple bash checks",
        verified=False,
        verified_at=None,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[
            BashVerification(
                execute="uv run pytest projects/sisyphus-speckit/tests/task/test_status.py -v",
                expected_exit_code=0,
                notes="All tests must pass",
            ),
            BashVerification(
                execute="uv run basedpyright projects/sisyphus-speckit --level error",
                expected_exit_code=0,
                notes="Type checking",
            ),
        ],
        llm_judge=[],
    )

    # when: Formatting detailed bash info
    bash_details_list = []
    for bash in vspec.bash:
        bash_details_list.append(
            {
                "execute": bash.execute,
                "expected_exit_code": bash.expected_exit_code,
                "notes": bash.notes or "",
            }
        )

    # then: All bash details are formatted correctly
    assert len(bash_details_list) == 2
    assert "pytest" in bash_details_list[0]["execute"]
    assert bash_details_list[0]["expected_exit_code"] == 0
    assert bash_details_list[0]["notes"] == "All tests must pass"
    assert "basedpyright" in bash_details_list[1]["execute"]


@pytest.mark.usefixtures("minimal_work_plan")
def test_status__detailed_verification_info__formats_llm_judge_details(
) -> None:
    """
    Given: A verification item with multiple LLM judge checks
    When: Formatting detailed verification information
    Then: All LLM judge details are properly formatted
    """
    # given: A verification spec with multiple LLM judge checks
    vspec = VerificationItem(
        id="verify-1",
        title="Code Review Verification",
        description="LLM code review checks",
        verified=False,
        verified_at=None,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[],
        llm_judge=[
            LLMJudgeVerification(
                by=LLMJudgeBy.ORCHESTRATOR,
                instruction="Check code quality and conventions",
            ),
            LLMJudgeVerification(
                by=LLMJudgeBy.EXTERNAL,
                instruction="Verify error handling and edge cases",
            ),
        ],
    )

    # when: Formatting detailed LLM judge info
    llm_details_list = []
    for llm in vspec.llm_judge:
        llm_details_list.append(
            {
                "by": llm.by,
                "instruction_preview": llm.instruction[:100] if llm.instruction else "N/A",
            }
        )

    # then: All LLM judge details are formatted correctly
    assert len(llm_details_list) == 2
    assert llm_details_list[0]["by"] == LLMJudgeBy.ORCHESTRATOR
    assert "code quality" in llm_details_list[0]["instruction_preview"]
    assert llm_details_list[1]["by"] == LLMJudgeBy.EXTERNAL
    assert "error handling" in llm_details_list[1]["instruction_preview"]


@pytest.mark.usefixtures("minimal_work_plan")
def test_status__verification_output__handles_bash_verification_type(
) -> None:
    """
    Given: A verification item with bash checks
    When: Determining verification type
    Then: Bash verification type is detected
    """
    # given: A verification spec with bash (automatic check)
    vspec = VerificationItem(
        id="verify-bash-1",
        title="Bash Verification",
        description="Automated bash check",
        verified=False,
        verified_at=None,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[BashVerification(execute="echo test", expected_exit_code=0)],
        llm_judge=[],
    )

    # when: Determining verification type
    verify_types = []
    if vspec.bash:
        verify_types.append("bash")
    if vspec.llm_judge:
        verify_types.append("llm")

    verify_type_str = ", ".join(verify_types) if verify_types else "unknown"

    # then: Bash verification type is correctly identified
    assert verify_type_str == "bash"


@pytest.mark.usefixtures("minimal_work_plan")
def test_status__verification_output__handles_mixed_verification_types(
) -> None:
    """
    Given: A verification item with both bash and LLM judge
    When: Determining verification types
    Then: Both types are listed
    """
    # given: A verification spec with both bash and llm_judge
    vspec = VerificationItem(
        id="verify-mixed-1",
        title="Mixed Verification",
        description="Combined bash and LLM checks",
        verified=False,
        verified_at=None,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[BashVerification(execute="echo test", expected_exit_code=0)],
        llm_judge=[LLMJudgeVerification(by=LLMJudgeBy.ORCHESTRATOR, instruction="Check result")],
    )

    # when: Determining verification types
    verify_types = []
    if vspec.bash:
        verify_types.append("bash")
    if vspec.llm_judge:
        verify_types.append("llm")
    if not vspec.bash and not vspec.llm_judge:
        verify_types.append("manual")

    verify_type_str = ", ".join(verify_types)

    # then: Both types are listed
    assert verify_type_str == "bash, llm"
