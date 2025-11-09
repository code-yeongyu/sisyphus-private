from __future__ import annotations

from pathlib import Path

import pytest

from sisyphus.cli.work import _is_dependency_satisfied, _is_plan_executable

pytestmark = [pytest.mark.anyio]


def create_minimal_plan_yaml(
    plan_id: str,
    plan_name: str,
    description: str,
    depends_on: list[str],
    todo_status: str,
    execution_completed: bool,
) -> str:
    depends_on_yaml = "[" + ", ".join(depends_on) + "]" if depends_on else "[]"
    return f"""version: "3.0"
metadata:
  created_at: "2025-11-09T00:00:00Z"
  updated_at: "2025-11-09T00:00:00Z"
work_plans:
  - id: {plan_id}
    name: {plan_name}
    description: {description}
    depends_on: {depends_on_yaml}
    user_request:
      original: Test request
      created_at: "2025-11-09T00:00:00Z"
      additional: []
    objectives:
      core: Test objective
      detailed: []
    background:
      current_situation: Test
      reason_for_change: Test
      changes_to_make: Test
    required_background:
      description: Test
      references: []
    workflow:
      dependency_diagram: Test
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    todos:
      - id: "1"
        title: Task 1
        status: {todo_status}
        references: []
        verification_spec: []
    final_verification: []
    execution:
      started: {str(execution_completed).lower()}
      completed: {str(execution_completed).lower()}
"""


async def test_is_plan_executable__if_no_dependencies__returns_true(tmp_path: Path) -> None:
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    plan_file = tasks_dir / "standalone.yaml"
    plan_content = create_minimal_plan_yaml(
        plan_id="standalone-plan",
        plan_name="Standalone Plan",
        description="Plan with no dependencies",
        depends_on=[],
        todo_status="pending",
        execution_completed=False,
    )
    plan_file.write_text(plan_content)

    result = await _is_plan_executable(plan_file, tasks_dir)

    assert result is True


async def test_is_plan_executable__if_dependency_completed__returns_true(tmp_path: Path) -> None:
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    dep_plan_file = tasks_dir / "foundation.yaml"
    dep_content = create_minimal_plan_yaml(
        plan_id="foundation",
        plan_name="Foundation",
        description="Base plan",
        depends_on=[],
        todo_status="completed",
        execution_completed=True,
    )
    dep_plan_file.write_text(dep_content)

    dependent_file = tasks_dir / "app.yaml"
    dependent_content = create_minimal_plan_yaml(
        plan_id="app",
        plan_name="App",
        description="App depends on foundation",
        depends_on=["foundation"],
        todo_status="pending",
        execution_completed=False,
    )
    dependent_file.write_text(dependent_content)

    result = await _is_plan_executable(dependent_file, tasks_dir)

    assert result is True


async def test_is_plan_executable__if_dependency_not_completed__returns_false(tmp_path: Path) -> None:
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    dep_plan_file = tasks_dir / "foundation.yaml"
    dep_content = create_minimal_plan_yaml(
        plan_id="foundation",
        plan_name="Foundation",
        description="Base plan",
        depends_on=[],
        todo_status="pending",
        execution_completed=False,
    )
    dep_plan_file.write_text(dep_content)

    dependent_file = tasks_dir / "app.yaml"
    dependent_content = create_minimal_plan_yaml(
        plan_id="app",
        plan_name="App",
        description="App depends on foundation",
        depends_on=["foundation"],
        todo_status="pending",
        execution_completed=False,
    )
    dependent_file.write_text(dependent_content)

    result = await _is_plan_executable(dependent_file, tasks_dir)

    assert result is False


async def test_is_dependency_satisfied__if_file_reference_completed__returns_true(tmp_path: Path) -> None:
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    dep_plan_file = tasks_dir / "backend.yaml"
    dep_content = create_minimal_plan_yaml(
        plan_id="backend-api",
        plan_name="Backend API",
        description="Backend API plan",
        depends_on=[],
        todo_status="completed",
        execution_completed=True,
    )
    dep_plan_file.write_text(dep_content)

    result = await _is_dependency_satisfied("file:backend.yaml#backend-api", tasks_dir)

    assert result is True


async def test_is_dependency_satisfied__if_file_reference_not_completed__returns_false(tmp_path: Path) -> None:
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    dep_plan_file = tasks_dir / "backend.yaml"
    dep_content = create_minimal_plan_yaml(
        plan_id="backend-api",
        plan_name="Backend API",
        description="Backend API plan",
        depends_on=[],
        todo_status="pending",
        execution_completed=False,
    )
    dep_plan_file.write_text(dep_content)

    result = await _is_dependency_satisfied("file:backend.yaml#backend-api", tasks_dir)

    assert result is False


async def test_is_dependency_satisfied__if_file_not_exists__returns_false(tmp_path: Path) -> None:
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    result = await _is_dependency_satisfied("file:nonexistent.yaml#plan-id", tasks_dir)

    assert result is False


async def test_is_dependency_satisfied__if_file_reference_without_plan_id__returns_first_plan_status(
    tmp_path: Path,
) -> None:
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    dep_plan_file = tasks_dir / "backend.yaml"
    dep_content = create_minimal_plan_yaml(
        plan_id="backend-api",
        plan_name="Backend API",
        description="Backend API plan",
        depends_on=[],
        todo_status="completed",
        execution_completed=True,
    )
    dep_plan_file.write_text(dep_content)

    result = await _is_dependency_satisfied("file:backend.yaml", tasks_dir)

    assert result is True


async def test_is_dependency_satisfied__if_registry_reference__returns_false(tmp_path: Path) -> None:
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    result = await _is_dependency_satisfied("registry:some-plan", tasks_dir)

    assert result is False


async def test_is_dependency_satisfied__if_plain_id_completed__returns_true(tmp_path: Path) -> None:
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    dep_plan_file = tasks_dir / "database.yaml"
    dep_content = create_minimal_plan_yaml(
        plan_id="database-setup",
        plan_name="Database Setup",
        description="Database setup plan",
        depends_on=[],
        todo_status="completed",
        execution_completed=True,
    )
    dep_plan_file.write_text(dep_content)

    result = await _is_dependency_satisfied("database-setup", tasks_dir)

    assert result is True


async def test_is_dependency_satisfied__if_plain_id_not_found__returns_false(tmp_path: Path) -> None:
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    result = await _is_dependency_satisfied("nonexistent-plan", tasks_dir)

    assert result is False


async def test_is_plan_executable__if_malformed_yaml__returns_false(tmp_path: Path) -> None:
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    plan_file = tasks_dir / "malformed.yaml"
    plan_file.write_text("invalid: yaml: content: [")

    result = await _is_plan_executable(plan_file, tasks_dir)

    assert result is False


async def test_is_plan_executable__if_multiple_dependencies_all_completed__returns_true(tmp_path: Path) -> None:
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    backend_file = tasks_dir / "backend.yaml"
    backend_content = create_minimal_plan_yaml(
        plan_id="backend",
        plan_name="Backend",
        description="Backend",
        depends_on=[],
        todo_status="completed",
        execution_completed=True,
    )
    backend_file.write_text(backend_content)

    frontend_file = tasks_dir / "frontend.yaml"
    frontend_content = create_minimal_plan_yaml(
        plan_id="frontend",
        plan_name="Frontend",
        description="Frontend",
        depends_on=[],
        todo_status="completed",
        execution_completed=True,
    )
    frontend_file.write_text(frontend_content)

    integration_file = tasks_dir / "integration.yaml"
    integration_content = create_minimal_plan_yaml(
        plan_id="integration",
        plan_name="Integration",
        description="Integration depends on backend and frontend",
        depends_on=["backend", "frontend"],
        todo_status="pending",
        execution_completed=False,
    )
    integration_file.write_text(integration_content)

    result = await _is_plan_executable(integration_file, tasks_dir)

    assert result is True


async def test_is_plan_executable__if_multiple_dependencies_one_incomplete__returns_false(tmp_path: Path) -> None:
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    backend_file = tasks_dir / "backend.yaml"
    backend_content = create_minimal_plan_yaml(
        plan_id="backend",
        plan_name="Backend",
        description="Backend",
        depends_on=[],
        todo_status="completed",
        execution_completed=True,
    )
    backend_file.write_text(backend_content)

    frontend_file = tasks_dir / "frontend.yaml"
    frontend_content = create_minimal_plan_yaml(
        plan_id="frontend",
        plan_name="Frontend",
        description="Frontend",
        depends_on=[],
        todo_status="pending",
        execution_completed=False,
    )
    frontend_file.write_text(frontend_content)

    integration_file = tasks_dir / "integration.yaml"
    integration_content = create_minimal_plan_yaml(
        plan_id="integration",
        plan_name="Integration",
        description="Integration depends on backend and frontend",
        depends_on=["backend", "frontend"],
        todo_status="pending",
        execution_completed=False,
    )
    integration_file.write_text(integration_content)

    result = await _is_plan_executable(integration_file, tasks_dir)

    assert result is False
