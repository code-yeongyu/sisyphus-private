"""Tests for TaskValidator."""

from __future__ import annotations

from pathlib import Path

import pytest

from sisyphus.core.tasks import TaskValidator

pytestmark = [pytest.mark.anyio]


async def test_read_content_success(tmp_path: Path) -> None:
    # given
    todolist = tmp_path / "ai-todolist.md"
    content = "# Test\nis_all_goals_accomplished = TRUE"
    todolist.write_text(content, encoding="utf-8")
    validator = TaskValidator(todolist)

    # when
    result = validator.read_content()

    # then
    assert result == content


async def test_read_content_file_not_found(tmp_path: Path) -> None:
    # given
    todolist = tmp_path / "nonexistent.md"
    validator = TaskValidator(todolist)

    # when
    result = validator.read_content()

    # then
    assert result == ""


async def test_check_all_goals_accomplished_true() -> None:
    # given
    content = """
# Task List
is_all_goals_accomplished = TRUE
- [x] Task 1
"""
    validator = TaskValidator()

    # when
    result = validator.check_all_goals_accomplished(content)

    # then
    assert result is True


async def test_check_all_goals_accomplished_false() -> None:
    # given
    content = """
# Task List
is_all_goals_accomplished = FALSE
- [ ] Task 1
"""
    validator = TaskValidator()

    # when
    result = validator.check_all_goals_accomplished(content)

    # then
    assert result is False


async def test_check_all_goals_accomplished_missing() -> None:
    # given
    content = """
# Task List
- [ ] Task 1
"""
    validator = TaskValidator()

    # when
    result = validator.check_all_goals_accomplished(content)

    # then
    assert result is False


async def test_check_all_goals_accomplished_case_insensitive() -> None:
    # given
    content = "is_all_goals_accomplished = true"
    validator = TaskValidator()

    # when
    result = validator.check_all_goals_accomplished(content)

    # then
    assert result is True


async def test_check_all_goals_accomplished_whitespace_variations() -> None:
    # given
    content = "is_all_goals_accomplished=TRUE"
    validator = TaskValidator()

    # when
    result = validator.check_all_goals_accomplished(content)

    # then
    assert result is True


async def test_check_execution_started_true() -> None:
    # given
    content = """
# Task List
is_execution_started = TRUE
"""
    validator = TaskValidator()

    # when
    result = validator.check_execution_started(content)

    # then
    assert result is True


async def test_check_execution_started_false() -> None:
    # given
    content = """
# Task List
is_execution_started = FALSE
"""
    validator = TaskValidator()

    # when
    result = validator.check_execution_started(content)

    # then
    assert result is False


async def test_check_execution_started_missing() -> None:
    # given
    content = "# Task List"
    validator = TaskValidator()

    # when
    result = validator.check_execution_started(content)

    # then
    assert result is False


async def test_check_execution_started_case_insensitive() -> None:
    # given
    content = "is_execution_started = True"
    validator = TaskValidator()

    # when
    result = validator.check_execution_started(content)

    # then
    assert result is True


async def test_check_all_checkboxes_completed_all_done() -> None:
    # given
    content = """
- [x] Task 1
- [x] Task 2
- [x] Task 3
"""
    validator = TaskValidator()

    # when
    result = validator.check_all_checkboxes_completed(content)

    # then
    assert result is True


async def test_check_all_checkboxes_completed_some_incomplete() -> None:
    # given
    content = """
- [x] Task 1
- [ ] Task 2
- [x] Task 3
"""
    validator = TaskValidator()

    # when
    result = validator.check_all_checkboxes_completed(content)

    # then
    assert result is False


async def test_check_all_checkboxes_completed_all_incomplete() -> None:
    # given
    content = """
- [ ] Task 1
- [ ] Task 2
"""
    validator = TaskValidator()

    # when
    result = validator.check_all_checkboxes_completed(content)

    # then
    assert result is False


async def test_check_all_checkboxes_completed_empty() -> None:
    # given
    content = "# No checkboxes"
    validator = TaskValidator()

    # when
    result = validator.check_all_checkboxes_completed(content)

    # then
    assert result is False


async def test_check_all_checkboxes_completed_case_insensitive() -> None:
    # given
    content = """
- [X] Task 1
- [x] Task 2
"""
    validator = TaskValidator()

    # when
    result = validator.check_all_checkboxes_completed(content)

    # then
    assert result is True


async def test_check_all_checkboxes_completed_with_whitespace() -> None:
    # given
    content = """
  - [x] Task 1
    - [x] Task 2
"""
    validator = TaskValidator()

    # when
    result = validator.check_all_checkboxes_completed(content)

    # then
    assert result is True


async def test_extract_uncompleted_checkboxes_simple() -> None:
    # given
    content = """
- [ ] Task 1
- [x] Task 2
- [ ] Task 3
"""
    validator = TaskValidator()

    # when
    result = validator.extract_uncompleted_checkboxes(content)

    # then
    assert result == ["Task 1", "Task 3"]


async def test_extract_uncompleted_checkboxes_empty() -> None:
    # given
    content = """
- [x] Task 1
- [x] Task 2
"""
    validator = TaskValidator()

    # when
    result = validator.extract_uncompleted_checkboxes(content)

    # then
    assert result == []


async def test_extract_uncompleted_checkboxes_with_whitespace() -> None:
    # given
    content = """
  - [ ] Indented task
    - [ ] More indented task
"""
    validator = TaskValidator()

    # when
    result = validator.extract_uncompleted_checkboxes(content)

    # then
    assert result == ["Indented task", "More indented task"]


async def test_extract_uncompleted_checkboxes_multiline_description() -> None:
    # given
    content = """
- [ ] Task with description
- [x] Completed task
- [ ] Another task (with details)
"""
    validator = TaskValidator()

    # when
    result = validator.extract_uncompleted_checkboxes(content)

    # then
    assert result == ["Task with description", "Another task (with details)"]


async def test_extract_uncompleted_checkboxes_special_characters() -> None:
    # given
    content = """
- [ ] Task with @mentions
- [ ] Task with #tags
- [ ] Task with [links](url)
"""
    validator = TaskValidator()

    # when
    result = validator.extract_uncompleted_checkboxes(content)

    # then
    assert result == ["Task with @mentions", "Task with #tags", "Task with [links](url)"]


async def test_extract_uncompleted_checkboxes_numbered_tasks() -> None:
    # given
    content = """
- [ ] 1. First task
- [x] 2. Second task
- [ ] 3. Third task
"""
    validator = TaskValidator()

    # when
    result = validator.extract_uncompleted_checkboxes(content)

    # then
    assert result == ["1. First task", "3. Third task"]


async def test_count_total_checkboxes_mixed() -> None:
    # given
    content = """
- [ ] Task 1
- [x] Task 2
- [ ] Task 3
- [x] Task 4
"""
    validator = TaskValidator()

    # when
    result = validator.count_total_checkboxes(content)

    # then
    assert result == 4


async def test_count_total_checkboxes_empty() -> None:
    # given
    content = "# No checkboxes here"
    validator = TaskValidator()

    # when
    result = validator.count_total_checkboxes(content)

    # then
    assert result == 0


async def test_count_total_checkboxes_case_insensitive() -> None:
    # given
    content = """
- [ ] Task 1
- [X] Task 2
- [x] Task 3
"""
    validator = TaskValidator()

    # when
    result = validator.count_total_checkboxes(content)

    # then
    assert result == 3


async def test_count_completed_checkboxes_mixed() -> None:
    # given
    content = """
- [ ] Task 1
- [x] Task 2
- [ ] Task 3
- [x] Task 4
"""
    validator = TaskValidator()

    # when
    result = validator.count_completed_checkboxes(content)

    # then
    assert result == 2


async def test_count_completed_checkboxes_none() -> None:
    # given
    content = """
- [ ] Task 1
- [ ] Task 2
"""
    validator = TaskValidator()

    # when
    result = validator.count_completed_checkboxes(content)

    # then
    assert result == 0


async def test_count_completed_checkboxes_all() -> None:
    # given
    content = """
- [x] Task 1
- [x] Task 2
"""
    validator = TaskValidator()

    # when
    result = validator.count_completed_checkboxes(content)

    # then
    assert result == 2


async def test_count_completed_checkboxes_case_insensitive() -> None:
    # given
    content = """
- [X] Task 1
- [x] Task 2
"""
    validator = TaskValidator()

    # when
    result = validator.count_completed_checkboxes(content)

    # then
    assert result == 2


async def test_validator_with_actual_todolist_sample() -> None:
    # given
    content = """
# Project Todo List

is_execution_started = TRUE
is_all_goals_accomplished = FALSE

# Tasks

- [x] 1. Setup project structure
  - [x] 1.1 Add dependencies
  - [x] 1.2 Create directories
- [ ] 2. Implement core features
  - [x] 2.1 Add Agent Protocol
  - [ ] 2.2 Add UI Protocol
- [ ] 3. Write tests
"""
    validator = TaskValidator()

    # when
    execution_started = validator.check_execution_started(content)
    goals_accomplished = validator.check_all_goals_accomplished(content)
    all_complete = validator.check_all_checkboxes_completed(content)
    uncompleted = validator.extract_uncompleted_checkboxes(content)
    total = validator.count_total_checkboxes(content)
    completed = validator.count_completed_checkboxes(content)

    # then
    assert execution_started is True
    assert goals_accomplished is False
    assert all_complete is False
    assert len(uncompleted) == 3
    assert "2. Implement core features" in uncompleted
    assert "2.2 Add UI Protocol" in uncompleted
    assert "3. Write tests" in uncompleted
    assert total == 7
    assert completed == 4


async def test_validator_reads_from_file_when_content_none(tmp_path: Path) -> None:
    # given
    todolist = tmp_path / "ai-todolist.md"
    content = """
is_execution_started = TRUE
- [x] Task 1
- [ ] Task 2
"""
    todolist.write_text(content, encoding="utf-8")
    validator = TaskValidator(todolist)

    # when
    execution_started = validator.check_execution_started()
    uncompleted = validator.extract_uncompleted_checkboxes()

    # then
    assert execution_started is True
    assert uncompleted == ["Task 2"]


async def test_validator_regex_whitespace_between_brackets() -> None:
    # given
    content = """
- [  ] Task with extra space in brackets
- [ x ] Task with space around x
"""
    validator = TaskValidator()

    # when
    uncompleted = validator.extract_uncompleted_checkboxes(content)
    total = validator.count_total_checkboxes(content)
    completed = validator.count_completed_checkboxes(content)

    # then
    assert "Task with extra space in brackets" in uncompleted
    assert total == 1
    assert completed == 0
