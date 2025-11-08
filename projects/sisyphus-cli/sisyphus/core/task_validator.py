"""v3.0 YAML-based task validator for ExecutionLoop."""

from __future__ import annotations

from pathlib import Path

from sisyphus.core.plans.loader import load_plan
from sisyphus.core.plans.models import Todo, TodoStatus


class YamlTaskValidator:
    """Task validator for v3.0 YAML work plans.

    Implements TaskValidatorProtocol for ExecutionLoop feedback loop.
    Checks if all todos in the work plan are completed.
    """

    def __init__(self, todolist_path: Path) -> None:
        """Initialize validator with YAML plan path.

        Args:
            todolist_path: Path to v3.0 YAML work plan file
        """
        self.todolist_path = todolist_path

    def read_content(self) -> str:
        """Read YAML content from file.

        Returns:
            YAML file content as string
        """
        return self.todolist_path.read_text(encoding="utf-8")

    async def check_all_goals_accomplished(self, content: str | None = None) -> bool:
        """Check if FULLY_DONE goal is accomplished in execution metadata.

        Args:
            content: Optional YAML content (unused, file is reloaded)

        Returns:
            True if execution.completed is True, False otherwise
        """
        try:
            plan_doc = await load_plan(self.todolist_path)

            if not plan_doc.work_plans:
                return False

            work_plan = plan_doc.work_plans[0]
            return work_plan.execution.completed
        except Exception:
            return False

    async def check_all_checkboxes_completed(self, content: str | None = None) -> bool:
        """Check if all todos are completed.

        Args:
            content: Optional YAML content (unused, file is reloaded)

        Returns:
            True if all todos have status=completed, False otherwise
        """
        try:
            plan_doc = await load_plan(self.todolist_path)

            if not plan_doc.work_plans:
                return False

            work_plan = plan_doc.work_plans[0]

            def all_todos_completed(todos: list[Todo]) -> bool:
                for todo in todos:
                    if todo.status != TodoStatus.completed:
                        return False
                    if todo.children and not all_todos_completed(todo.children):
                        return False
                return True

            return all_todos_completed(work_plan.todos)
        except Exception:
            return False
