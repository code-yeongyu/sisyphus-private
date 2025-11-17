"""Operations for mutating WorkPlan and Todo objects."""

from __future__ import annotations

from datetime import UTC, datetime

from sisyphus_core.core.plans.models import Todo, WorkPlan


def find_todo_by_id(todos: list[Todo], todo_id: str) -> Todo | None:
    """Find a todo by id, recursively searching through children.

    Args:
        todos: List of todos to search
        todo_id: ID to find

    Returns:
        Todo if found, None otherwise
    """
    for todo in todos:
        if todo.id == todo_id:
            return todo
        if todo.children:
            found = find_todo_by_id(todo.children, todo_id)
            if found:
                return found
    return None


def get_current_task(work_plan: WorkPlan) -> Todo | None:
    """Get the current task from work_plan.work_mode.current_task_id.

    Args:
        work_plan: WorkPlan to search

    Returns:
        Current Todo if found, None otherwise
    """
    current_task_id = work_plan.work_mode.current_task_id
    if current_task_id is None:
        return None
    return find_todo_by_id(work_plan.todos, current_task_id)


def mark_todo_acceptance_criterion(
    todo: Todo,
    criterion_id: str,
    evidence: str,
) -> bool:
    """Mark a specific acceptance criterion as verified for a todo.

    Args:
        todo: Todo containing acceptance_criteria
        criterion_id: ID of the criterion to mark
        evidence: Evidence string to record

    Returns:
        True if criterion was found and marked, False otherwise
    """
    for criterion in todo.acceptance_criteria:
        if criterion.id == criterion_id:
            criterion.verified_at = datetime.now(UTC).isoformat()
            criterion.verification_evidence = evidence
            return True
    return False


def mark_current_task_acceptance_criterion(
    work_plan: WorkPlan,
    criterion_id: str,
    evidence: str,
) -> tuple[bool, str]:
    """Mark acceptance criterion for the current task.

    Args:
        work_plan: WorkPlan containing the current task
        criterion_id: ID of the criterion to mark
        evidence: Evidence string to record

    Returns:
        Tuple of (success, message)
    """
    current_task = get_current_task(work_plan)
    if current_task is None:
        return False, "현재 진행 중인 작업이 없습니다 (work_mode.current_task_id가 설정되지 않음)"

    if not current_task.acceptance_criteria:
        return False, f"현재 작업 '{current_task.id}'에 acceptance_criteria가 정의되지 않았습니다"

    success = mark_todo_acceptance_criterion(current_task, criterion_id, evidence)
    if not success:
        return False, f"Criterion ID '{criterion_id}'를 현재 작업 '{current_task.id}'에서 찾을 수 없습니다"

    return True, f"Task '{current_task.id}' acceptance criterion '{criterion_id}' 검증 완료"


def mark_verification_agent_checklist(
    work_plan: WorkPlan,
    checklist_id: str,
    evidence: str,
) -> tuple[bool, str]:
    """Mark verification agent acceptance criteria checklist as checked.

    Args:
        work_plan: WorkPlan containing acceptance_criteria_for_verification_agent
        checklist_id: ID of the checklist item to mark
        evidence: Evidence string to record

    Returns:
        Tuple of (success, message)
    """
    if not work_plan.acceptance_criteria_for_verification_agent:
        return False, "WorkPlan에 acceptance_criteria_for_verification_agent가 정의되지 않았습니다"

    for criteria in work_plan.acceptance_criteria_for_verification_agent:
        for checklist in criteria.checklists:
            if checklist.id == checklist_id:
                checklist.checked_at = datetime.now(UTC).isoformat()
                checklist.checked_evidence = evidence
                return True, f"Verification agent checklist '{checklist_id}' 검증 완료"

    return False, f"Checklist ID '{checklist_id}'를 acceptance_criteria_for_verification_agent에서 찾을 수 없습니다"


def mark_fully_done(
    work_plan: WorkPlan,
    evidence: str,
) -> tuple[bool, str]:
    """Mark work plan as fully done with evidence.

    Args:
        work_plan: WorkPlan to mark as fully done
        evidence: Evidence string describing completion

    Returns:
        Tuple of (success, message)
    """
    work_plan.execution.fully_done_at = datetime.now(UTC).isoformat()
    work_plan.fully_done_evidence = evidence
    return True, f"WorkPlan '{work_plan.id}' fully done 마킹 완료"
