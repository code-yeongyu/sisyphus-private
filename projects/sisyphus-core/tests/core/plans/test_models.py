from sisyphus_core.core.plans.models import (
    AcceptanceCriteriaChecklist,
    AcceptanceCriteriaForVerificationAgent,
    AcceptanceCriteriaItem,
    Background,
    BashVerification,
    DeterministicBashVerification,
    ExecutionStatus,
    Objectives,
    OrchestratorJudgeVerification,
    RequiredBackground,
    SuccessVision,
    Todo,
    TodoStatus,
    UserRequest,
    VerificationItem,
    Workflow,
    WorkPlan,
)


def test_user_request__with_expected_outcome__stores_correctly() -> None:
    # Given
    original = "User wants feature X"
    expected_outcome = "Feature X is implemented and working"
    forbidden_outcome = "Feature X breaks existing functionality"

    # When
    user_request = UserRequest(
        original=original,
        created_at="2025-11-16T10:00:00Z",
        expected_outcome=expected_outcome,
        forbidden_outcome=forbidden_outcome,
    )

    # Then
    assert user_request.original == original
    assert user_request.expected_outcome == expected_outcome
    assert user_request.forbidden_outcome == forbidden_outcome


def test_user_request__without_expected_outcome__defaults_to_none() -> None:
    # Given
    original = "User wants feature Y"

    # When
    user_request = UserRequest(
        original=original,
        created_at="2025-11-16T10:00:00Z",
    )

    # Then
    assert user_request.original == original
    assert user_request.expected_outcome is None
    assert user_request.forbidden_outcome is None


def test_user_request__with_additional_notes__stores_list() -> None:
    # Given
    original = "Feature request"
    additional = ["Note 1", "Note 2", "Note 3"]

    # When
    user_request = UserRequest(
        original=original,
        created_at="2025-11-16T10:00:00Z",
        additional=additional,
    )

    # Then
    assert user_request.additional == additional
    assert len(user_request.additional) == 3


def test_deterministic_bash_verification__with_all_fields__creates_correctly() -> None:
    # Given
    description = "Build command test"
    reason = "Command is deterministic and always returns same output"
    execute = "npm run build"
    expected_stdout = "Build successful"
    expected_exit_code = 0

    # When
    bash_verif = DeterministicBashVerification(
        description=description,
        reason_why_it_is_deterministic_and_reliable=reason,
        execute=execute,
        expected_stdout=expected_stdout,
        expected_exit_code=expected_exit_code,
    )

    # Then
    assert bash_verif.description == description
    assert bash_verif.reason_why_it_is_deterministic_and_reliable == reason
    assert bash_verif.execute == execute
    assert bash_verif.expected_stdout == expected_stdout
    assert bash_verif.expected_exit_code == expected_exit_code
    assert bash_verif.verified_at is None


def test_deterministic_bash_verification__with_verification_timestamp__stores_correctly() -> None:
    # Given
    description = "Test verification"
    reason = "Safe to run multiple times"
    execute = "pytest tests/"
    verified_at = "2025-11-16T11:30:00Z"

    # When
    bash_verif = DeterministicBashVerification(
        description=description,
        reason_why_it_is_deterministic_and_reliable=reason,
        execute=execute,
        verified_at=verified_at,
    )

    # Then
    assert bash_verif.verified_at == verified_at


def test_orchestrator_judge_verification__with_all_fields__creates_correctly() -> None:
    # Given
    prompt = "Is the implementation correct?"
    verified_at = "2025-11-16T12:00:00Z"
    evidence = "Orchestrator approved the implementation"

    # When
    judge_verif = OrchestratorJudgeVerification(
        prompt=prompt,
        verified_at=verified_at,
        verification_evidence=evidence,
    )

    # Then
    assert judge_verif.prompt == prompt
    assert judge_verif.verified_at == verified_at
    assert judge_verif.verification_evidence == evidence


def test_orchestrator_judge_verification__without_verification__defaults_none() -> None:
    # Given
    prompt = "Check the code quality"

    # When
    judge_verif = OrchestratorJudgeVerification(prompt=prompt)

    # Then
    assert judge_verif.prompt == prompt
    assert judge_verif.verified_at is None
    assert judge_verif.verification_evidence is None


def test_verification_item__with_deterministic_bash_and_bash__includes_bash_verification() -> None:
    # Given
    verif_id = "verify-1"
    title = "Build test"
    description = "Test that build succeeds"
    bash_verif_classic = BashVerification(
        execute="npm run build",
        expected_exit_code=0,
    )
    bash_verif_deterministic = DeterministicBashVerification(
        description="Build check",
        reason_why_it_is_deterministic_and_reliable="Deterministic build",
        execute="npm run build",
        expected_exit_code=0,
    )

    # When
    verif_item = VerificationItem(
        id=verif_id,
        title=title,
        description=description,
        orchestrator_manually_verified=True,
        manual_verification_evidence="Build verified",
        bash=[bash_verif_classic],
        deterministic_bash=[bash_verif_deterministic],
    )

    # Then
    assert len(verif_item.deterministic_bash) == 1
    assert verif_item.deterministic_bash[0].description == "Build check"
    assert verif_item.deterministic_bash[0].execute == "npm run build"


def test_verification_item__with_deterministic_bash__supports_reason_why_field() -> None:
    # Given
    verif_id = "verify-2"
    title = "Deterministic test"
    bash_verif_deterministic = DeterministicBashVerification(
        description="Deterministic command",
        reason_why_it_is_deterministic_and_reliable="No external state, deterministic output",
        execute="echo 'hello'",
    )

    # When
    verif_item = VerificationItem(
        id=verif_id,
        title=title,
        description="Test deterministic field",
        orchestrator_manually_verified=True,
        manual_verification_evidence="OK",
        bash=[BashVerification(execute="echo test")],
        deterministic_bash=[bash_verif_deterministic],
    )

    # Then
    reason = verif_item.deterministic_bash[0].reason_why_it_is_deterministic_and_reliable
    assert reason == "No external state, deterministic output"


def test_verification_item__with_orchestrator_judge_and_bash__combines_both() -> None:
    # Given
    verif_id = "verify-3"
    title = "Code quality check"
    bash_verif = BashVerification(execute="npm test")
    judge_verif = OrchestratorJudgeVerification(
        prompt="Is the code quality acceptable?",
        verified_at="2025-11-16T13:00:00Z",
        verification_evidence="Code approved",
    )

    # When
    verif_item = VerificationItem(
        id=verif_id,
        title=title,
        description="Combined verification",
        orchestrator_manually_verified=True,
        manual_verification_evidence="Approved",
        bash=[bash_verif],
        orchestrator_judge=[judge_verif],
    )

    # Then
    assert len(verif_item.bash) == 1
    assert len(verif_item.orchestrator_judge) == 1
    assert verif_item.orchestrator_judge[0].prompt == "Is the code quality acceptable?"


def test_acceptance_criteria_checklist__with_all_fields__creates_correctly() -> None:
    # Given
    checklist_id = "check-1"
    title = "Unit tests"
    content = "All unit tests must pass"
    checked_at = "2025-11-16T14:00:00Z"
    evidence = "Test report shows 100% pass"

    # When
    checklist = AcceptanceCriteriaChecklist(
        id=checklist_id,
        title=title,
        content=content,
        checked_at=checked_at,
        checked_evidence=evidence,
    )

    # Then
    assert checklist.id == checklist_id
    assert checklist.title == title
    assert checklist.content == content
    assert checklist.checked_at == checked_at
    assert checklist.checked_evidence == evidence


def test_acceptance_criteria_checklist__unchecked__defaults_none() -> None:
    # Given
    checklist_id = "check-2"
    title = "Integration tests"
    content = "All integration tests pass"

    # When
    checklist = AcceptanceCriteriaChecklist(
        id=checklist_id,
        title=title,
        content=content,
    )

    # Then
    assert checklist.id == checklist_id
    assert checklist.checked_at is None
    assert checklist.checked_evidence is None


def test_acceptance_criteria_for_verification_agent__with_checklists__combines_correctly() -> None:
    # Given
    criteria_id = "acceptance-1"
    criteria_title = "Feature X acceptance"
    checklist1 = AcceptanceCriteriaChecklist(
        id="check-1",
        title="Functionality",
        content="Feature works correctly",
        checked_at="2025-11-16T15:00:00Z",
        checked_evidence="Tested manually",
    )
    checklist2 = AcceptanceCriteriaChecklist(
        id="check-2",
        title="Performance",
        content="Response time < 100ms",
        checked_at="2025-11-16T15:30:00Z",
        checked_evidence="Benchmark passed",
    )

    # When
    criteria = AcceptanceCriteriaForVerificationAgent(
        id=criteria_id,
        title=criteria_title,
        accepted_at="2025-11-16T16:00:00Z",
        checklists=[checklist1, checklist2],
    )

    # Then
    assert criteria.id == criteria_id
    assert criteria.title == criteria_title
    assert len(criteria.checklists) == 2
    assert criteria.checklists[0].id == "check-1"
    assert criteria.checklists[1].id == "check-2"
    assert criteria.accepted_at == "2025-11-16T16:00:00Z"


def test_acceptance_criteria_for_verification_agent__without_acceptance_timestamp__defaults_none() -> None:
    # Given
    criteria_id = "acceptance-2"
    criteria_title = "Pending acceptance"
    checklist = AcceptanceCriteriaChecklist(
        id="check-1",
        title="Check 1",
        content="Something",
    )

    # When
    criteria = AcceptanceCriteriaForVerificationAgent(
        id=criteria_id,
        title=criteria_title,
        checklists=[checklist],
    )

    # Then
    assert criteria.id == criteria_id
    assert criteria.accepted_at is None
    assert len(criteria.checklists) == 1


def test_execution_status__with_fully_done_at__stores_timestamp() -> None:
    # Given
    started = True
    completed = True
    started_at = "2025-11-16T10:00:00Z"
    completed_at = "2025-11-16T16:00:00Z"
    fully_done_at = "2025-11-16T16:30:00Z"

    # When
    execution = ExecutionStatus(
        started=started,
        completed=completed,
        started_at=started_at,
        completed_at=completed_at,
        fully_done_at=fully_done_at,
    )

    # Then
    assert execution.started is True
    assert execution.completed is True
    assert execution.fully_done_at == fully_done_at


def test_execution_status__without_fully_done_at__defaults_none() -> None:
    # Given
    started = False
    completed = False

    # When
    execution = ExecutionStatus(
        started=started,
        completed=completed,
    )

    # Then
    assert execution.started is False
    assert execution.completed is False
    assert execution.fully_done_at is None
    assert execution.started_at is None
    assert execution.completed_at is None


def test_todo__with_all_new_fields__combines_parallel_and_criteria() -> None:
    # Given
    todo_id = "complex-task"
    title = "Complex task"
    status = TodoStatus.in_progress
    parallel = True
    evidence = "No race conditions"
    criterion1 = AcceptanceCriteriaItem(
        id="crit-1",
        condition="Performance good",
    )
    criterion2 = AcceptanceCriteriaItem(
        id="crit-2",
        condition="Tests pass",
        verified_at="2025-11-16T17:00:00Z",
    )

    # When
    todo = Todo(
        id=todo_id,
        title=title,
        status=status,
        parallel=parallel,
        parallelable_and_safe_evidence=evidence,
        acceptance_criteria=[criterion1, criterion2],
    )

    # Then
    assert todo.id == todo_id
    assert todo.parallel is True
    assert todo.parallelable_and_safe_evidence == evidence
    assert len(todo.acceptance_criteria) == 2
    assert todo.acceptance_criteria[0].id == "crit-1"
    assert todo.acceptance_criteria[1].verified_at == "2025-11-16T17:00:00Z"


def test_work_plan__with_current_work_ids__stores_list() -> None:
    # Given
    work_plan_id = "plan-1"
    current_work_ids = ["task-1", "task-2", "task-3"]

    # When
    work_plan = WorkPlan(
        id=work_plan_id,
        name="Test Plan",
        user_request=UserRequest(
            original="Test",
            created_at="2025-11-16T10:00:00Z",
        ),
        objectives=Objectives(
            core="Test core objective",
            detailed=[],
        ),
        background=Background(
            current_situation="Current",
            reason_for_change="Change needed",
            changes_to_make="Make changes",
        ),
        required_background=RequiredBackground(
            description="Background",
            file_structure=None,
            references=[],
        ),
        workflow=Workflow(
            dependency_diagram="A -> B -> C",
            critical_path=[],
        ),
        success_vision=SuccessVision(
            user_perspective=[],
            business_perspective=[],
            technical_criteria=[],
        ),
        final_verification=[],
        todos=[],
        execution=ExecutionStatus(started=False, completed=False),
        current_work_ids=current_work_ids,
    )

    # Then
    assert work_plan.id == work_plan_id
    assert work_plan.current_work_ids == current_work_ids
    assert len(work_plan.current_work_ids) == 3


def test_work_plan__with_acceptance_criteria_for_verification_agent__stores_criteria_list() -> None:
    # Given
    work_plan_id = "plan-2"
    checklist = AcceptanceCriteriaChecklist(
        id="check-1",
        title="Test check",
        content="Test content",
    )
    criteria = AcceptanceCriteriaForVerificationAgent(
        id="criteria-1",
        title="Test criteria",
        checklists=[checklist],
    )

    # When
    work_plan = WorkPlan(
        id=work_plan_id,
        name="Test Plan 2",
        user_request=UserRequest(
            original="Test",
            created_at="2025-11-16T10:00:00Z",
        ),
        objectives=Objectives(
            core="Core",
            detailed=[],
        ),
        background=Background(
            current_situation="Current",
            reason_for_change="Change",
            changes_to_make="Changes",
        ),
        required_background=RequiredBackground(
            description="Background",
            file_structure=None,
            references=[],
        ),
        workflow=Workflow(
            dependency_diagram="Diagram",
            critical_path=[],
        ),
        success_vision=SuccessVision(
            user_perspective=[],
            business_perspective=[],
            technical_criteria=[],
        ),
        final_verification=[],
        todos=[],
        execution=ExecutionStatus(started=False, completed=False),
        acceptance_criteria_for_verification_agent=[criteria],
    )

    # Then
    assert len(work_plan.acceptance_criteria_for_verification_agent) == 1
    assert work_plan.acceptance_criteria_for_verification_agent[0].id == "criteria-1"
    assert len(work_plan.acceptance_criteria_for_verification_agent[0].checklists) == 1


def test_work_plan__with_fully_done_evidence__stores_string() -> None:
    # Given
    work_plan_id = "plan-3"
    fully_done_evidence = "All requirements met, all tests passed, deployment successful"

    # When
    work_plan = WorkPlan(
        id=work_plan_id,
        name="Test Plan 3",
        user_request=UserRequest(
            original="Test",
            created_at="2025-11-16T10:00:00Z",
        ),
        objectives=Objectives(
            core="Core",
            detailed=[],
        ),
        background=Background(
            current_situation="Current",
            reason_for_change="Change",
            changes_to_make="Changes",
        ),
        required_background=RequiredBackground(
            description="Background",
            file_structure=None,
            references=[],
        ),
        workflow=Workflow(
            dependency_diagram="Diagram",
            critical_path=[],
        ),
        success_vision=SuccessVision(
            user_perspective=[],
            business_perspective=[],
            technical_criteria=[],
        ),
        final_verification=[],
        todos=[],
        execution=ExecutionStatus(started=False, completed=False),
        fully_done_evidence=fully_done_evidence,
    )

    # Then
    assert work_plan.fully_done_evidence == fully_done_evidence


def test_work_plan__without_new_fields__defaults_empty() -> None:
    # Given
    work_plan_id = "plan-4"

    # When
    work_plan = WorkPlan(
        id=work_plan_id,
        name="Test Plan 4",
        user_request=UserRequest(
            original="Test",
            created_at="2025-11-16T10:00:00Z",
        ),
        objectives=Objectives(
            core="Core",
            detailed=[],
        ),
        background=Background(
            current_situation="Current",
            reason_for_change="Change",
            changes_to_make="Changes",
        ),
        required_background=RequiredBackground(
            description="Background",
            file_structure=None,
            references=[],
        ),
        workflow=Workflow(
            dependency_diagram="Diagram",
            critical_path=[],
        ),
        success_vision=SuccessVision(
            user_perspective=[],
            business_perspective=[],
            technical_criteria=[],
        ),
        final_verification=[],
        todos=[],
        execution=ExecutionStatus(started=False, completed=False),
    )

    # Then
    assert work_plan.current_work_ids == []
    assert work_plan.acceptance_criteria_for_verification_agent == []
    assert work_plan.fully_done_evidence is None


def test_work_plan__has_no_current_work_field() -> None:
    # Given: WorkPlan model class
    # When: checking for current_work field in model_fields
    # Then: current_work should not exist (removed in favor of current_work_ids)
    assert "current_work" not in WorkPlan.model_fields


def test_work_plan__has_current_work_ids_field() -> None:
    # Given: WorkPlan model class
    # When: checking for current_work_ids field
    # Then: current_work_ids should exist as a list field
    assert "current_work_ids" in WorkPlan.model_fields
    field_info = WorkPlan.model_fields["current_work_ids"]
    assert field_info.annotation == list[str]


def test_work_plan__current_work_ids_defaults_to_empty_list() -> None:
    # Given: WorkPlan with minimal required fields
    # When: creating WorkPlan without specifying current_work_ids
    work_plan = WorkPlan(
        id="test-plan",
        name="Test Plan",
        user_request=UserRequest(
            original="Test",
            created_at="2025-11-19T10:00:00Z",
        ),
        objectives=Objectives(core="Test objective"),
        background=Background(
            current_situation="Current",
            reason_for_change="Change",
            changes_to_make="Changes",
        ),
        required_background=RequiredBackground(description="Background"),
        workflow=Workflow(dependency_diagram="Diagram"),
        success_vision=SuccessVision(),
        final_verification=[],
        todos=[],
    )

    # Then: current_work_ids should default to empty list
    assert work_plan.current_work_ids == []
    assert isinstance(work_plan.current_work_ids, list)


def test_work_plan__current_work_ids_accepts_multiple_items() -> None:
    # Given: WorkPlan with multiple current work items
    work_ids = ["task-1", "task-2", "task-3"]

    # When: creating WorkPlan with multiple current_work_ids
    work_plan = WorkPlan(
        id="test-plan-multi",
        name="Test Plan Multi",
        user_request=UserRequest(
            original="Test",
            created_at="2025-11-19T10:00:00Z",
        ),
        objectives=Objectives(core="Test objective"),
        background=Background(
            current_situation="Current",
            reason_for_change="Change",
            changes_to_make="Changes",
        ),
        required_background=RequiredBackground(description="Background"),
        workflow=Workflow(dependency_diagram="Diagram"),
        success_vision=SuccessVision(),
        final_verification=[],
        todos=[],
        current_work_ids=work_ids,
    )

    # Then: current_work_ids should contain all items in order
    assert work_plan.current_work_ids == work_ids
    assert len(work_plan.current_work_ids) == 3
    assert work_plan.current_work_ids[0] == "task-1"
    assert work_plan.current_work_ids[1] == "task-2"
    assert work_plan.current_work_ids[2] == "task-3"
