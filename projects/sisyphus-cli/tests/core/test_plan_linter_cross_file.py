from __future__ import annotations

from pathlib import Path

import pytest
from ruamel.yaml import YAML

from sisyphus.core.plan_linter import PlanLinter
from sisyphus.core.plans.models import (
    Background,
    Metadata,
    Objectives,
    PlanDocument,
    RequiredBackground,
    SuccessVision,
    UserRequest,
    Workflow,
    WorkPlan,
)

pytestmark = [pytest.mark.anyio]


def test_validate_external_dependency__if_valid_reference__returns_none(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})

    external_plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-09T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="backend-api",
                name="Backend API",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[],
                todos=[],
            )
        ],
    )

    external_file_path = tmp_path / "backend.yaml"
    yaml = YAML()
    with open(external_file_path, "w") as f:
        yaml.dump(external_plan_doc.model_dump(mode="json"), f)

    source_path = tmp_path / "frontend.yaml"
    dep_ref = f"file:{external_file_path}#backend-api"

    # when
    result = linter._validate_external_dependency(dep_ref, "frontend-app", source_path)

    # then
    assert result is None


def test_validate_external_dependency__if_file_not_exist__returns_error(
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})
    source_path = tmp_path / "frontend.yaml"
    dep_ref = f"file:{tmp_path / 'nonexistent.yaml'}#backend-api"

    # when
    result = linter._validate_external_dependency(dep_ref, "frontend-app", source_path)

    # then
    assert result is not None
    assert "does not exist" in result
    assert "frontend-app" in result
    assert "Fix:" in result


def test_validate_external_dependency__if_plan_not_exist__returns_error(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})

    external_plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-09T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="backend-auth",
                name="Backend Auth",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[],
                todos=[],
            )
        ],
    )

    external_file_path = tmp_path / "backend.yaml"
    yaml = YAML()
    with open(external_file_path, "w") as f:
        yaml.dump(external_plan_doc.model_dump(mode="json"), f)

    source_path = tmp_path / "frontend.yaml"
    dep_ref = f"file:{external_file_path}#backend-api"

    # when
    result = linter._validate_external_dependency(dep_ref, "frontend-app", source_path)

    # then
    assert result is not None
    assert "does not exist" in result
    assert "backend-api" in result
    assert "'backend-auth'" in result
    assert "Fix:" in result


def test_validate_external_dependency__if_malformed_format__returns_error(
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})
    source_path = tmp_path / "frontend.yaml"
    dep_ref = "file:backend.yaml"

    # when
    result = linter._validate_external_dependency(dep_ref, "frontend-app", source_path)

    # then
    assert result is not None
    assert "malformed" in result
    assert "file:path/to/plan.yaml#plan-id" in result


def test_validate_external_dependency__if_empty_file_path__returns_error(
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})
    source_path = tmp_path / "frontend.yaml"
    dep_ref = "file:#backend-api"

    # when
    result = linter._validate_external_dependency(dep_ref, "frontend-app", source_path)

    # then
    assert result is not None
    assert "empty file path" in result


def test_validate_external_dependency__if_empty_plan_id__returns_error(
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})
    source_path = tmp_path / "frontend.yaml"
    dep_ref = "file:backend.yaml#"

    # when
    result = linter._validate_external_dependency(dep_ref, "frontend-app", source_path)

    # then
    assert result is not None
    assert "empty plan ID" in result


def test_validate_external_dependency__if_relative_path__resolves_correctly(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})

    external_plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-09T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="backend-api",
                name="Backend API",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[],
                todos=[],
            )
        ],
    )

    external_file_path = tmp_path / "backend.yaml"
    yaml = YAML()
    with open(external_file_path, "w") as f:
        yaml.dump(external_plan_doc.model_dump(mode="json"), f)

    source_path = tmp_path / "frontend.yaml"
    dep_ref = "file:backend.yaml#backend-api"

    # when
    result = linter._validate_external_dependency(dep_ref, "frontend-app", source_path)

    # then
    assert result is None


def test_validate_registry_dependency__if_valid_reference__returns_none(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})

    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()

    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    backend_plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-09T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="backend-api",
                name="Backend API",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[],
                todos=[],
            )
        ],
    )

    backend_file_path = tmp_path / "backend.yaml"
    yaml = YAML()
    with open(backend_file_path, "w") as f:
        yaml.dump(backend_plan_doc.model_dump(mode="json"), f)

    registry_data = {
        "version": "1.0",
        "plans": [
            {
                "file": "backend.yaml",
                "plans": ["backend-api"],
            }
        ],
    }
    registry_path = sisyphus_dir / "registry.yaml"
    with open(registry_path, "w") as f:
        yaml.dump(registry_data, f)

    plan_path = tasks_dir / "frontend.yaml"

    # when
    result = linter._validate_registry_dependency("backend-api", "frontend-app", plan_path)

    # then
    assert result is None


def test_validate_registry_dependency__if_registry_not_exist__returns_error(
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})

    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()

    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_path = tasks_dir / "frontend.yaml"

    # when
    result = linter._validate_registry_dependency("backend-api", "frontend-app", plan_path)

    # then
    assert result is not None
    assert "registry file not found" in result
    assert "frontend-app" in result
    assert "Fix:" in result


def test_validate_registry_dependency__if_plan_not_in_registry__returns_error(
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})

    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()

    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    registry_data = {
        "version": "1.0",
        "plans": [
            {
                "file": "backend.yaml",
                "plans": ["backend-auth"],
            }
        ],
    }
    registry_path = sisyphus_dir / "registry.yaml"
    yaml = YAML()
    with open(registry_path, "w") as f:
        yaml.dump(registry_data, f)

    plan_path = tasks_dir / "frontend.yaml"

    # when
    result = linter._validate_registry_dependency("backend-api", "frontend-app", plan_path)

    # then
    assert result is not None
    assert "does not exist in registry" in result
    assert "backend-api" in result
    assert "'backend-auth'" in result
    assert "Fix:" in result


def test_validate_registry_dependency__if_no_sisyphus_dir__returns_error(
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})
    plan_path = tmp_path / "frontend.yaml"

    # when
    result = linter._validate_registry_dependency("backend-api", "frontend-app", plan_path)

    # then
    assert result is not None
    assert ".sisyphus directory not found" in result
    assert "frontend-app" in result
    assert "Fix:" in result


def test_validate_depends_on__if_file_reference__validates_external_file(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})

    backend_plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-09T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="backend-api",
                name="Backend API",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[],
                todos=[],
            )
        ],
    )

    backend_file_path = tmp_path / "backend.yaml"
    yaml = YAML()
    with open(backend_file_path, "w") as f:
        yaml.dump(backend_plan_doc.model_dump(mode="json"), f)

    frontend_plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-09T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="frontend-app",
                name="Frontend App",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=["file:backend.yaml#backend-api"],
                todos=[],
            )
        ],
    )

    frontend_file_path = tmp_path / "frontend.yaml"

    # when
    errors = linter.validate_depends_on(frontend_plan_doc, frontend_file_path)

    # then
    assert len(errors) == 0


def test_validate_depends_on__if_registry_reference__validates_via_registry(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})

    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()

    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    backend_plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-09T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="backend-api",
                name="Backend API",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[],
                todos=[],
            )
        ],
    )

    backend_file_path = tmp_path / "backend.yaml"
    yaml = YAML()
    with open(backend_file_path, "w") as f:
        yaml.dump(backend_plan_doc.model_dump(mode="json"), f)

    registry_data = {
        "version": "1.0",
        "plans": [
            {
                "file": "backend.yaml",
                "plans": ["backend-api"],
            }
        ],
    }
    registry_path = sisyphus_dir / "registry.yaml"
    with open(registry_path, "w") as f:
        yaml.dump(registry_data, f)

    frontend_plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-09T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="frontend-app",
                name="Frontend App",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=["registry:backend-api"],
                todos=[],
            )
        ],
    )

    frontend_file_path = tasks_dir / "frontend.yaml"

    # when
    errors = linter.validate_depends_on(frontend_plan_doc, frontend_file_path)

    # then
    assert len(errors) == 0


def test_validate_depends_on__if_mixed_references__validates_all_types(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})

    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()

    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    backend_plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-09T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="backend-api",
                name="Backend API",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[],
                todos=[],
            )
        ],
    )

    backend_file_path = tmp_path / "backend.yaml"
    yaml = YAML()
    with open(backend_file_path, "w") as f:
        yaml.dump(backend_plan_doc.model_dump(mode="json"), f)

    auth_plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-09T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="auth-service",
                name="Auth Service",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[],
                todos=[],
            )
        ],
    )

    auth_file_path = tmp_path / "auth.yaml"
    with open(auth_file_path, "w") as f:
        yaml.dump(auth_plan_doc.model_dump(mode="json"), f)

    registry_data = {
        "version": "1.0",
        "plans": [
            {
                "file": "backend.yaml",
                "plans": ["backend-api"],
            }
        ],
    }
    registry_path = sisyphus_dir / "registry.yaml"
    with open(registry_path, "w") as f:
        yaml.dump(registry_data, f)

    frontend_plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-09T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="local-plan",
                name="Local Plan",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[],
                todos=[],
            ),
            WorkPlan(
                id="frontend-app",
                name="Frontend App",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[
                    "local-plan",
                    "registry:backend-api",
                    f"file:{auth_file_path}#auth-service",
                ],
                todos=[],
            ),
        ],
    )

    frontend_file_path = tasks_dir / "frontend.yaml"

    # when
    errors = linter.validate_depends_on(frontend_plan_doc, frontend_file_path)

    # then
    assert len(errors) == 0


def test_validate_depends_on__if_auto_cross_file_search__finds_plan_in_sibling(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})

    tasks_dir = tmp_path
    tasks_dir.mkdir(exist_ok=True)

    backend_plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-09T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-1-foundation",
                name="Foundation",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=[],
                todos=[],
            )
        ],
    )

    backend_file_path = tasks_dir / "plan-1-foundation.yaml"
    yaml = YAML()
    with open(backend_file_path, "w") as f:
        yaml.dump(backend_plan_doc.model_dump(mode="json"), f)

    frontend_plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-09T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-2-rendering-engine",
                name="Rendering Engine",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=["plan-1-foundation"],
                todos=[],
            )
        ],
    )

    frontend_file_path = tasks_dir / "plan-2-rendering-engine.yaml"

    # when
    errors = linter.validate_depends_on(frontend_plan_doc, frontend_file_path)

    # then
    assert len(errors) == 0


def test_validate_depends_on__if_auto_cross_file_search__plan_not_found__returns_error(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
    tmp_path: Path,
) -> None:
    # given
    linter = PlanLinter({})

    tasks_dir = tmp_path
    tasks_dir.mkdir(exist_ok=True)

    frontend_plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-09T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-2-rendering-engine",
                name="Rendering Engine",
                user_request=minimal_user_request,
                objectives=minimal_objectives,
                background=minimal_background,
                required_background=minimal_required_background,
                workflow=minimal_workflow,
                success_vision=minimal_success_vision,
                final_verification=[],
                depends_on=["plan-1-foundation"],
                todos=[],
            )
        ],
    )

    frontend_file_path = tasks_dir / "plan-2-rendering-engine.yaml"

    # when
    errors = linter.validate_depends_on(frontend_plan_doc, frontend_file_path)

    # then
    assert len(errors) == 1
    assert "plan-1-foundation" in errors[0]
    assert "does not exist" in errors[0]
