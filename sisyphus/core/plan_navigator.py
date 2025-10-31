from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sisyphus.utils.plan_types import Todo, TodoStatus, VerificationItem, WorkPlan


@dataclass
class CompletionReport:
    task_id: str | int
    task_status: TodoStatus
    all_children_completed: bool
    children_summary: dict[str, int]
    all_verifications_completed: bool
    verification_summary: dict[str, int]
    can_complete: bool


class PlanNavigator:
    """Navigate work plan tasks using DFS (Depth-First Search) algorithm.

    Business rules:
    - DFS order: children → sibling → parent's sibling (backtrack)
    - in_progress task: check children first, then siblings
    - completed task: check next sibling, then backtrack to parent's sibling
    - parallel_group: return first pending in group (parallel execution controlled by CLI)
    """

    def __init__(self, plan: WorkPlan) -> None:
        self.plan = plan

    def get_current_task(self) -> Todo | None:
        """Get currently in-progress task from current_task_id."""
        current_id = self.plan.status.work_mode.current_task_id
        if current_id is None:
            return None
        return self.find_todo_by_id(current_id)

    def get_next_task(self, current_id: str | None = None) -> Todo | None:
        """Get next pending task using DFS algorithm.

        DFS traversal order:
        1. current_id=None → return first pending
        2. in_progress → children first, then siblings
        3. completed → next sibling, then backtrack to parent's sibling
        """
        if current_id is None:
            current_id = self.plan.status.work_mode.current_task_id

        if current_id is None:
            return self._find_first_pending(self.plan.todos)

        current = self.find_todo_by_id(current_id)
        if current is None:
            raise ValueError(f"작업 ID를 찾을 수 없습니다: {current_id}")

        match current.status:
            case TodoStatus.in_progress:
                if current.children:
                    first_child_pending = self._find_first_pending(current.children)
                    if first_child_pending:
                        return first_child_pending

                next_sibling = self._find_next_sibling(current_id)
                if next_sibling and next_sibling.status == TodoStatus.pending:
                    return next_sibling

            case TodoStatus.completed:
                next_sibling = self._find_next_sibling(current_id)
                if next_sibling and next_sibling.status == TodoStatus.pending:
                    return next_sibling

                parent = self._find_parent(current_id)
                if parent:
                    parent_next = self._find_next_sibling(parent.id)
                    if parent_next and parent_next.status == TodoStatus.pending:
                        return parent_next

        return None

    def find_todo_by_id(self, target_id: str | int) -> Todo | None:
        """Find todo by ID (e.g. "1", "1.1", "1.1.2")."""
        return self._find_in_list(self.plan.todos, target_id)

    def _find_in_list(self, todos: list[Todo], target_id: str | int) -> Todo | None:
        for todo in todos:
            if todo.id == target_id:
                return todo
            if todo.children:
                found = self._find_in_list(todo.children, target_id)
                if found:
                    return found
        return None

    def _find_first_pending(self, todos: list[Todo]) -> Todo | None:
        for todo in todos:
            if todo.status == TodoStatus.pending:
                return todo
            if todo.children:
                child = self._find_first_pending(todo.children)
                if child:
                    return child
        return None

    def _find_next_sibling(self, current_id: str | int) -> Todo | None:
        siblings = self._get_siblings(current_id)
        if siblings is None:
            return None

        for i, sibling in enumerate(siblings):
            if sibling.id == current_id and i + 1 < len(siblings):
                return siblings[i + 1]
        return None

    def _get_siblings(self, target_id: str | int) -> list[Todo] | None:
        for todo in self.plan.todos:
            if todo.id == target_id:
                return self.plan.todos

        parent = self._find_parent(target_id)
        if parent:
            return parent.children
        return None

    def _find_parent(self, target_id: str | int) -> Todo | None:
        return self._find_parent_in_list(self.plan.todos, target_id)

    def _find_parent_in_list(self, todos: list[Todo], target_id: str | int) -> Todo | None:
        for todo in todos:
            for child in todo.children:
                if child.id == target_id:
                    return todo

            if todo.children:
                parent = self._find_parent_in_list(todo.children, target_id)
                if parent:
                    return parent
        return None

    def get_task_references(self, task_id: str | int) -> list[Any]:
        """Get references for a specific task."""
        task = self.find_todo_by_id(task_id)
        if task is None:
            raise ValueError(f"작업 ID를 찾을 수 없습니다: {task_id}")
        return task.references

    def get_task_children(self, task_id: str | int) -> list[Todo]:
        """Get direct children of a task."""
        task = self.find_todo_by_id(task_id)
        if task is None:
            raise ValueError(f"작업 ID를 찾을 수 없습니다: {task_id}")
        return task.children

    def get_all_descendants(self, task_id: str | int) -> list[Todo]:
        """Get all descendants (children recursively) of a task."""
        task = self.find_todo_by_id(task_id)
        if task is None:
            raise ValueError(f"작업 ID를 찾을 수 없습니다: {task_id}")

        descendants: list[Todo] = []

        def collect(todos: list[Todo]) -> None:
            for todo in todos:
                descendants.append(todo)
                if todo.children:
                    collect(todo.children)

        if task.children:
            collect(task.children)
        return descendants

    def get_task_verification(self, task_id: str | int) -> list[VerificationItem]:
        """Get verification spec for a task."""
        task = self.find_todo_by_id(task_id)
        if task is None:
            raise ValueError(f"작업 ID를 찾을 수 없습니다: {task_id}")
        return task.verification_spec

    def check_task_completion(self, task_id: str | int) -> CompletionReport:
        """Check if task can be marked as completed.

        Business rule: Task can complete when:
        - All children are completed
        - All verification items are completed

        Args:
            task_id: Task ID to check

        Returns:
            CompletionReport with completion status

        Raises:
            ValueError: If task ID is not found
        """
        task = self.find_todo_by_id(task_id)
        if task is None:
            raise ValueError(f"작업 ID를 찾을 수 없습니다: {task_id}")

        # 1. Children 체크
        descendants = self.get_all_descendants(task_id)
        children_summary = {
            "completed": sum(1 for d in descendants if d.status == TodoStatus.completed),
            "in_progress": sum(1 for d in descendants if d.status == TodoStatus.in_progress),
            "pending": sum(1 for d in descendants if d.status == TodoStatus.pending),
        }
        all_children_completed = len(descendants) == 0 or children_summary["completed"] == len(descendants)

        # 2. Verification 체크
        verifications = task.verification_spec
        verification_summary = {
            "completed": sum(1 for v in verifications if v.verified),
            "total": len(verifications),
        }
        all_verifications_completed = len(verifications) == 0 or verification_summary["completed"] == len(
            verifications
        )

        # 3. 완료 가능 여부
        can_complete = all_children_completed and all_verifications_completed

        return CompletionReport(
            task_id=task_id,
            task_status=task.status,
            all_children_completed=all_children_completed,
            children_summary=children_summary,
            all_verifications_completed=all_verifications_completed,
            verification_summary=verification_summary,
            can_complete=can_complete,
        )
