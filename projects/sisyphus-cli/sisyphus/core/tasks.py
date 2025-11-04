"""TaskValidator for ai-todolist.md validation."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from ruamel.yaml import YAML

from sisyphus.core.plans.models import PlanDocument, TodoStatus

if TYPE_CHECKING:
    from sisyphus.core.plans.models import PlanDocument


class TaskValidator:
    """ai-todolist.md validation tool."""

    def __init__(self, todolist_path: Path = Path("./ai-todolist.md")) -> None:
        """Initialize TaskValidator.

        Args:
            todolist_path: Path to ai-todolist.md file
        """
        self.todolist_path = todolist_path
        self._last_valid_doc: PlanDocument | None = None
        self._last_mtime: float | None = None

    def read_content(self) -> str:
        """Read todolist content.

        Returns:
            Content of the todolist file, or empty string if file not found
        """
        try:
            return self.todolist_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    def check_all_goals_accomplished(self, content: str | None = None) -> bool:
        """Check if is_all_goals_accomplished = TRUE (Markdown or YAML).

        Args:
            content: Content to check. If None, reads from file.

        Returns:
            True if flag is set to TRUE, False otherwise
        """
        if self.todolist_path.suffix.lower() in (".yaml", ".yml"):
            return self._check_yaml_accomplished()

        if content is None:
            content = self.read_content()

        pattern = r"is_all_goals_accomplished\s*=\s*TRUE"
        return bool(re.search(pattern, content, re.IGNORECASE))

    def check_execution_started(self, content: str | None = None) -> bool:
        """Check if is_execution_started = TRUE.

        Args:
            content: Content to check. If None, reads from file.

        Returns:
            True if flag is set to TRUE, False otherwise
        """
        if content is None:
            content = self.read_content()

        pattern = r"is_execution_started\s*=\s*TRUE"
        return bool(re.search(pattern, content, re.IGNORECASE))

    def check_all_checkboxes_completed(self, content: str | None = None) -> bool:
        """Check if all checkboxes are [x] (Markdown or YAML).

        Args:
            content: Content to check. If None, reads from file.

        Returns:
            True if no uncompleted checkboxes exist and at least one completed checkbox exists
        """
        # YAML: Markdown 체크박스 로직 우회 (ExecutionLoop AND 조건 통과용)
        if self.todolist_path.suffix.lower() in (".yaml", ".yml"):
            return True

        if content is None:
            content = self.read_content()

        unchecked = re.findall(r"^\s*-\s*\[\s*\]", content, re.MULTILINE)
        if unchecked:
            return False

        checked = re.findall(r"^\s*-\s*\[x\]", content, re.MULTILINE | re.IGNORECASE)
        return len(checked) > 0

    def extract_uncompleted_checkboxes(self, content: str | None = None) -> list[str]:
        """Extract uncompleted checkbox items.

        Args:
            content: Content to check. If None, reads from file.

        Returns:
            List of item texts (without "- [ ]" prefix)
        """
        if content is None:
            content = self.read_content()

        uncompleted_items: list[str] = []
        lines = content.split("\n")

        for line in lines:
            match = re.match(r"^\s*-\s*\[\s*\]\s*(.+)", line)
            if match:
                item_text = match.group(1).strip()
                uncompleted_items.append(item_text)

        return uncompleted_items

    def count_total_checkboxes(self, content: str | None = None) -> int:
        """Count total checkboxes (Markdown or YAML todos).

        Args:
            content: Content to check. If None, reads from file.

        Returns:
            Total number of checkboxes
        """
        if self.todolist_path.suffix.lower() in (".yaml", ".yml"):
            doc = self._load_yaml_with_cache()
            if not doc.work_plans:
                return 0
            return len(doc.work_plans[0].todos)

        if content is None:
            content = self.read_content()

        unchecked = re.findall(r"^\s*-\s*\[\s*\]", content, re.MULTILINE)
        checked = re.findall(r"^\s*-\s*\[x\]", content, re.MULTILINE | re.IGNORECASE)
        return len(unchecked) + len(checked)

    def count_completed_checkboxes(self, content: str | None = None) -> int:
        """Count completed checkboxes (Markdown or YAML todos).

        Args:
            content: Content to check. If None, reads from file.

        Returns:
            Number of completed checkboxes
        """
        if self.todolist_path.suffix.lower() in (".yaml", ".yml"):
            doc = self._load_yaml_with_cache()
            if not doc.work_plans:
                return 0
            work_plan = doc.work_plans[0]
            return sum(1 for t in work_plan.todos if t.status == TodoStatus.completed)

        if content is None:
            content = self.read_content()

        checked = re.findall(r"^\s*-\s*\[x\]", content, re.MULTILINE | re.IGNORECASE)
        return len(checked)

    def _load_yaml_with_cache(self) -> PlanDocument:
        """Load YAML with mtime-based caching and detailed error messages.

        Returns:
            PlanDocument

        Raises:
            PermissionError: If file is not readable
            ValueError: If YAML parse error, version missing, or version not 3.0
            FileNotFoundError: If file doesn't exist
        """
        # 파일 존재 확인
        if not self.todolist_path.exists():
            raise FileNotFoundError(f"Plan file not found: {self.todolist_path}")

        # mtime 캐시 체크 (권한 에러 세분화)
        try:
            current_mtime = self.todolist_path.stat().st_mtime
        except PermissionError as e:
            raise PermissionError(f"Cannot access file: {self.todolist_path}") from e

        if self._last_mtime == current_mtime and self._last_valid_doc:
            return self._last_valid_doc

        # YAML 파싱 (에러 세분화)
        try:
            yaml = YAML(typ="safe", pure=True)
            try:
                content = self.todolist_path.read_text(encoding="utf-8")
            except PermissionError as e:
                raise PermissionError(f"Cannot read file: {self.todolist_path}") from e

            raw = yaml.load(content)
        except PermissionError:
            raise  # Re-raise PermissionError as-is
        except Exception as e:
            raise ValueError(f"YAML parse error in {self.todolist_path}: {e}") from e

        # 버전 체크 (누락/불일치)
        version = raw.get("version")
        if not version:
            raise ValueError(
                f"Missing 'version' field in {self.todolist_path}. v3.0 YAML requires 'version: \"3.0\"' at root."
            )
        if version != "3.0":
            raise ValueError(
                f"Unsupported version '{version}' in {self.todolist_path}. work command requires version 3.0."
            )

        # PlanDocument 생성
        doc = PlanDocument(**raw)

        # 캐시 갱신
        self._last_valid_doc = doc
        self._last_mtime = current_mtime

        return doc

    def _check_yaml_accomplished(self) -> bool:
        """Check v3.0 YAML completion with detailed feedback.

        Custom spec (work command):
        - Flat structure (no children)
        - 3 states only (pending/in_progress/completed)

        Returns:
            True if all completed and custom spec valid
        """

        logger = logging.getLogger(__name__)

        doc = self._load_yaml_with_cache()

        # 빈 work_plans 체크
        if not doc.work_plans:
            logger.warning(f"YAML has no work_plans: {self.todolist_path}. Cannot determine completion status.")
            return False

        if not doc.work_plans[0].todos:
            logger.warning(f"Work plan '{doc.work_plans[0].id}' has no todos. Cannot determine completion status.")
            return False

        work_plan = doc.work_plans[0]
        violations = []  # 커스텀 스펙 위반 수집

        for todo in work_plan.todos:
            # 커스텀 스펙 검증
            # NOTE: children is not None (빈 리스트도 금지, 필드 존재 자체를 금지)
            if todo.children is not None:
                violations.append(
                    f"Todo '{todo.id}' ('{todo.title}') has children field. "
                    "work command requires flat structure (children field must be None)."
                )
            if todo.status == TodoStatus.blocked:
                violations.append(
                    f"Todo '{todo.id}' ('{todo.title}') has 'blocked' status. "
                    "work command allows only: pending, in_progress, completed."
                )
            if todo.status != TodoStatus.completed:
                # 미완료 (스펙은 통과했지만 작업 진행 중)
                pass

        # 커스텀 스펙 위반 발견 시 Hard Fail (work 명령 커스텀 스펙은 강제 요구사항)
        if violations:
            error_msg = (
                f"Custom spec violations in {self.todolist_path}:\n"
                + "\n".join(f"  - {v}" for v in violations)
                + "\n\n"
                "work command requires:\n"
                "  - Flat structure (no children field)\n"
                "  - 3 states only (pending, in_progress, completed)\n\n"
                "Tip: Use 'sisyphus task continue' for full v3.0 support (blocked state, children)."
            )
            logger.error(error_msg)
            raise ValueError(f"Custom spec violated: {len(violations)} error(s)")

        # 모든 todos completed 확인
        return all(t.status == TodoStatus.completed for t in work_plan.todos)
