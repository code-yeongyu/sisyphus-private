"""TaskValidator for ai-todolist.md validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class TaskValidator:
    """ai-todolist.md validation tool."""

    def __init__(self, todolist_path: Path = Path("./ai-todolist.md")) -> None:
        """Initialize TaskValidator.

        Args:
            todolist_path: Path to ai-todolist.md file
        """
        self.todolist_path = todolist_path

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
        """Check if is_all_goals_accomplished = TRUE.

        Args:
            content: Content to check. If None, reads from file.

        Returns:
            True if flag is set to TRUE, False otherwise
        """
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
        """Check if all checkboxes are [x].

        Args:
            content: Content to check. If None, reads from file.

        Returns:
            True if no uncompleted checkboxes exist and at least one completed checkbox exists
        """
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
        """Count total checkboxes.

        Args:
            content: Content to check. If None, reads from file.

        Returns:
            Total number of checkboxes
        """
        if content is None:
            content = self.read_content()

        unchecked = re.findall(r"^\s*-\s*\[\s*\]", content, re.MULTILINE)
        checked = re.findall(r"^\s*-\s*\[x\]", content, re.MULTILINE | re.IGNORECASE)
        return len(unchecked) + len(checked)

    def count_completed_checkboxes(self, content: str | None = None) -> int:
        """Count completed checkboxes.

        Args:
            content: Content to check. If None, reads from file.

        Returns:
            Number of completed checkboxes
        """
        if content is None:
            content = self.read_content()

        checked = re.findall(r"^\s*-\s*\[x\]", content, re.MULTILINE | re.IGNORECASE)
        return len(checked)
