import pytest
from sisyphus_core.core.plans.models import AcceptanceCriteriaItem, Todo, TodoStatus


def test_acceptance_criteria_item__basic_creation__creates_successfully() -> None:
    # Given
    item_id = "test-criterion-1"
    condition = "All tests must pass"

    # When
    criterion = AcceptanceCriteriaItem(
        id=item_id,
        condition=condition,
        verified_at=None,
        verification_evidence=None
    )

    # Then
    assert criterion.id == item_id
    assert criterion.condition == condition
    assert criterion.verified_at is None
    assert criterion.verification_evidence is None


def test_acceptance_criteria_item__with_verification_details__stores_correctly() -> None:
    # Given
    item_id = "test-criterion-2"
    condition = "Code coverage > 80%"
    verified_at = "2025-11-16T10:00:00Z"
    evidence = "Coverage report shows 85%"

    # When
    criterion = AcceptanceCriteriaItem(
        id=item_id,
        condition=condition,
        verified_at=verified_at,
        verification_evidence=evidence
    )

    # Then
    assert criterion.id == item_id
    assert criterion.condition == condition
    assert criterion.verified_at == verified_at
    assert criterion.verification_evidence == evidence


def test_todo__with_new_parallel_fields__initializes_correctly() -> None:
    # Given
    todo_id = "task-1"
    title = "Implement feature X"
    status = TodoStatus.pending

    # When
    todo = Todo(
        id=todo_id,
        title=title,
        status=status
    )

    # Then
    assert todo.id == todo_id
    assert todo.title == title
    assert todo.status == status
    assert todo.parallel is False
    assert todo.parallelable_and_safe_evidence is None
    assert todo.acceptance_criteria == []


def test_todo__with_parallel_flag_set__stores_flag_correctly() -> None:
    # Given
    todo_id = "task-2"
    title = "Parallel task"
    status = TodoStatus.in_progress
    evidence = "This task has no shared state dependencies"

    # When
    todo = Todo(
        id=todo_id,
        title=title,
        status=status,
        parallel=True,
        parallelable_and_safe_evidence=evidence
    )

    # Then
    assert todo.parallel is True
    assert todo.parallelable_and_safe_evidence == evidence


def test_todo__with_acceptance_criteria__stores_list_correctly() -> None:
    # Given
    todo_id = "task-3"
    title = "Task with acceptance criteria"
    status = TodoStatus.pending
    criterion1 = AcceptanceCriteriaItem(
        id="criterion-1",
        condition="All unit tests pass"
    )
    criterion2 = AcceptanceCriteriaItem(
        id="criterion-2",
        condition="Code review approved"
    )

    # When
    todo = Todo(
        id=todo_id,
        title=title,
        status=status,
        acceptance_criteria=[criterion1, criterion2]
    )

    # Then
    assert len(todo.acceptance_criteria) == 2
    assert todo.acceptance_criteria[0].id == "criterion-1"
    assert todo.acceptance_criteria[1].id == "criterion-2"
    assert todo.acceptance_criteria[0].condition == "All unit tests pass"


def test_todo__with_all_new_fields__combines_all_features() -> None:
    # Given
    todo_id = "complex-task"
    title = "Complex parallelizable task"
    status = TodoStatus.in_progress
    parallel = True
    evidence = "No race conditions possible"
    criteria = [
        AcceptanceCriteriaItem(
            id="ac-1",
            condition="Performance < 100ms",
            verified_at="2025-11-16T09:30:00Z",
            verification_evidence="Benchmark completed"
        ),
        AcceptanceCriteriaItem(
            id="ac-2",
            condition="No memory leaks"
        )
    ]

    # When
    todo = Todo(
        id=todo_id,
        title=title,
        status=status,
        parallel=parallel,
        parallelable_and_safe_evidence=evidence,
        acceptance_criteria=criteria
    )

    # Then
    assert todo.id == todo_id
    assert todo.parallel is True
    assert todo.parallelable_and_safe_evidence == evidence
    assert len(todo.acceptance_criteria) == 2
    assert todo.acceptance_criteria[0].verified_at == "2025-11-16T09:30:00Z"
    assert todo.acceptance_criteria[1].verification_evidence is None
