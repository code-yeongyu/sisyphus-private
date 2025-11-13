from __future__ import annotations

from dataclasses import dataclass

from sisyphus_core.core.plans.models import PlanDocument, ReferenceItem, Todo, TodoStatus, VerificationItem, WorkPlan


@dataclass
class CompletionReport:
    task_id: str
    task_status: TodoStatus
    all_children_completed: bool
    children_summary: dict[str, int]
    all_verifications_completed: bool
    verification_summary: dict[str, int]
    manual_verification_summary: dict[str, int]
    all_manual_verifications_completed: bool
    can_complete: bool


class TaskManager:
    """Navigate v3.0 WorkPlan tasks using DFS (Depth-First Search) algorithm.

    Business rules:
    - DFS order: children → sibling → parent's sibling (backtrack)
    - in_progress task: check children first, then siblings
    - completed task: check next sibling, then backtrack to parent's sibling
    """

    def __init__(self, plan_doc: PlanDocument, plan_id: str) -> None:
        self.plan_doc = plan_doc
        self.plan_id = plan_id
        self.work_plan = self._find_work_plan()

    def _find_work_plan(self) -> WorkPlan:
        """Find WorkPlan by ID, raise ValueError if not found."""
        for work_plan in self.plan_doc.work_plans:
            if work_plan.id == self.plan_id:
                return work_plan
        raise ValueError(f"WorkPlan not found: {self.plan_id}")

    def get_current_task(self) -> Todo | None:
        """Get currently in-progress task from current_task_id."""
        current_id = self.work_plan.work_mode.current_task_id
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
            current_id = self.work_plan.work_mode.current_task_id

        if current_id is None:
            return self._find_first_pending(self.work_plan.todos)

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

    def get_previous_task(self, current_id: str | None = None) -> Todo | None:
        """Get previous task in DFS traversal order (reverse).

        Reverse DFS order:
        1. current=None or first task → return None
        2. Has previous sibling → return last descendant of previous sibling
        3. No previous sibling → return parent

        Example DFS order: 1 → 1.1 → 1.1.1 → 1.1.2 → 1.2 → 2
        - current="1.2" → previous="1.1.2" (last descendant of 1.1)
        - current="1.1" → previous="1" (parent)
        - current="1" → previous=None (first task)
        """
        if current_id is None:
            current_id = self.work_plan.work_mode.current_task_id

        if current_id is None:
            return None

        current = self.find_todo_by_id(current_id)
        if current is None:
            raise ValueError(f"작업 ID를 찾을 수 없습니다: {current_id}")

        siblings = self._get_siblings(current_id)
        if siblings is not None:
            for i, sibling in enumerate(siblings):
                if sibling.id == current_id and i > 0:
                    previous_sibling = siblings[i - 1]
                    return self._get_last_descendant(previous_sibling)

        parent = self._find_parent(current_id)
        return parent

    def find_todo_by_id(self, target_id: str) -> Todo | None:
        """Find todo by ID (e.g. "1", "1.1", "1.1.2")."""
        return self._find_in_list(self.work_plan.todos, target_id)

    def _find_in_list(self, todos: list[Todo], target_id: str) -> Todo | None:
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

    def _find_next_sibling(self, current_id: str) -> Todo | None:
        siblings = self._get_siblings(current_id)
        if siblings is None:
            return None

        for i, sibling in enumerate(siblings):
            if sibling.id == current_id and i + 1 < len(siblings):
                return siblings[i + 1]
        return None

    def _get_siblings(self, target_id: str) -> list[Todo] | None:
        for todo in self.work_plan.todos:
            if todo.id == target_id:
                return self.work_plan.todos

        parent = self._find_parent(target_id)
        if parent:
            return parent.children
        return None

    def _find_parent(self, target_id: str) -> Todo | None:
        return self._find_parent_in_list(self.work_plan.todos, target_id)

    def _find_parent_in_list(self, todos: list[Todo], target_id: str) -> Todo | None:
        for todo in todos:
            if todo.children:
                for child in todo.children:
                    if child.id == target_id:
                        return todo

                parent = self._find_parent_in_list(todo.children, target_id)
                if parent:
                    return parent
        return None

    def _get_last_descendant(self, todo: Todo) -> Todo:
        """Get last descendant (deepest rightmost node) of a todo."""
        current = todo
        while current.children:
            current = current.children[-1]
        return current

    def get_task_references(self, task_id: str) -> list[ReferenceItem]:
        """Get references for a specific task."""
        task = self.find_todo_by_id(task_id)
        if task is None:
            raise ValueError(f"작업 ID를 찾을 수 없습니다: {task_id}")
        return task.references

    def get_task_children(self, task_id: str) -> list[Todo]:
        """Get direct children of a task."""
        task = self.find_todo_by_id(task_id)
        if task is None:
            raise ValueError(f"작업 ID를 찾을 수 없습니다: {task_id}")
        return task.children if task.children else []

    def get_all_descendants(self, task_id: str) -> list[Todo]:
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

    def get_task_verification(self, task_id: str) -> list[VerificationItem]:
        """Get verification spec for a task."""
        task = self.find_todo_by_id(task_id)
        if task is None:
            raise ValueError(f"작업 ID를 찾을 수 없습니다: {task_id}")
        return task.verification_spec

    def check_task_completion(self, task_id: str) -> CompletionReport:
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

        descendants = self.get_all_descendants(task_id)
        children_summary = {
            "completed": sum(1 for d in descendants if d.status == TodoStatus.completed),
            "in_progress": sum(1 for d in descendants if d.status == TodoStatus.in_progress),
            "pending": sum(1 for d in descendants if d.status == TodoStatus.pending),
        }
        all_children_completed = len(descendants) == 0 or children_summary["completed"] == len(descendants)

        verifications = task.verification_spec
        verification_summary = {
            "completed": sum(1 for v in verifications if v.verified),
            "total": len(verifications),
        }
        all_verifications_completed = len(verifications) == 0 or verification_summary["completed"] == len(
            verifications
        )

        manual_verification_summary = {
            "completed": sum(
                1 for v in verifications if v.orchestrator_manually_verified and v.manual_verification_evidence != ""
            ),
            "total": len(verifications),
        }
        all_manual_verifications_completed = len(verifications) == 0 or manual_verification_summary[
            "completed"
        ] == len(verifications)

        can_complete = all_children_completed and all_verifications_completed and all_manual_verifications_completed

        return CompletionReport(
            task_id=task_id,
            task_status=task.status,
            all_children_completed=all_children_completed,
            children_summary=children_summary,
            all_verifications_completed=all_verifications_completed,
            verification_summary=verification_summary,
            manual_verification_summary=manual_verification_summary,
            all_manual_verifications_completed=all_manual_verifications_completed,
            can_complete=can_complete,
        )

    def next_unverified(self) -> tuple[VerificationItem, int, int] | None:
        """Get next unverified verification item across all tasks.

        Returns:
            Tuple of (verification_item, current_index, total_count) or None if all verified
            - current_index: 1-based index (e.g., 1 for first item)
            - total_count: total number of verification items
        """
        all_verifications: list[tuple[VerificationItem, Todo]] = []

        def collect_verifications(todos: list[Todo]) -> None:
            for todo in todos:
                for verify_item in todo.verification_spec:
                    all_verifications.append((verify_item, todo))
                if todo.children:
                    collect_verifications(todo.children)

        collect_verifications(self.work_plan.todos)

        if not all_verifications:
            return None

        for idx, (verify_item, _) in enumerate(all_verifications):
            if not verify_item.verified:
                return (verify_item, idx + 1, len(all_verifications))

        return None
