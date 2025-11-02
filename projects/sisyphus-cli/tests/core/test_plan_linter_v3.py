from pathlib import Path

import pytest

from sisyphus.core.plan_linter import PlanLinter
from sisyphus.core.plans.models import Metadata, PlanDocument, WorkPlan

pytestmark = [pytest.mark.anyio]


def test_validate_depends_on__if_circular_dependency__detects_cycle() -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(id="plan-a", name="Plan A", depends_on=["plan-b"], todos=[]),
            WorkPlan(id="plan-b", name="Plan B", depends_on=["plan-a"], todos=[]),
        ],
    )
    linter = PlanLinter({})
    plan_path = Path("/fake/path.yaml")

    errors = linter.validate_depends_on(plan_doc, plan_path)

    assert len(errors) == 1
    assert "Circular dependency detected" in errors[0]
    assert "plan-a" in errors[0]
    assert "plan-b" in errors[0]


def test_validate_depends_on__if_missing_dependency__reports_error() -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(id="plan-a", name="Plan A", depends_on=["nonexistent"], todos=[]),
        ],
    )
    linter = PlanLinter({})
    plan_path = Path("/fake/path.yaml")

    errors = linter.validate_depends_on(plan_doc, plan_path)

    assert len(errors) == 1
    assert "plan-a" in errors[0]
    assert "nonexistent" in errors[0]
    assert "does not exist" in errors[0]


def test_validate_depends_on__if_valid_dependency__returns_empty() -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(id="plan-a", name="Plan A", depends_on=[], todos=[]),
            WorkPlan(id="plan-b", name="Plan B", depends_on=["plan-a"], todos=[]),
        ],
    )
    linter = PlanLinter({})
    plan_path = Path("/fake/path.yaml")

    errors = linter.validate_depends_on(plan_doc, plan_path)

    assert len(errors) == 0


def test_validate_depends_on__if_empty_depends_on__returns_empty() -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(id="plan-a", name="Plan A", depends_on=[], todos=[]),
        ],
    )
    linter = PlanLinter({})
    plan_path = Path("/fake/path.yaml")

    errors = linter.validate_depends_on(plan_doc, plan_path)

    assert len(errors) == 0


def test_validate_depends_on__if_self_reference__detects_cycle() -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(id="plan-a", name="Plan A", depends_on=["plan-a"], todos=[]),
        ],
    )
    linter = PlanLinter({})
    plan_path = Path("/fake/path.yaml")

    errors = linter.validate_depends_on(plan_doc, plan_path)

    assert len(errors) == 1
    assert "Circular dependency detected" in errors[0]
    assert "plan-a" in errors[0]


def test_validate_depends_on__if_complex_cycle__detects_all_nodes() -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(id="plan-a", name="Plan A", depends_on=["plan-b"], todos=[]),
            WorkPlan(id="plan-b", name="Plan B", depends_on=["plan-c"], todos=[]),
            WorkPlan(id="plan-c", name="Plan C", depends_on=["plan-a"], todos=[]),
        ],
    )
    linter = PlanLinter({})
    plan_path = Path("/fake/path.yaml")

    errors = linter.validate_depends_on(plan_doc, plan_path)

    assert len(errors) == 1
    assert "Circular dependency detected" in errors[0]
    assert "plan-a" in errors[0]
    assert "plan-b" in errors[0]
    assert "plan-c" in errors[0]


def test_validate_depends_on__if_multiple_missing__reports_all() -> None:
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-01T00:00:00Z"),
        work_plans=[
            WorkPlan(id="plan-a", name="Plan A", depends_on=["missing-1", "missing-2"], todos=[]),
        ],
    )
    linter = PlanLinter({})
    plan_path = Path("/fake/path.yaml")

    errors = linter.validate_depends_on(plan_doc, plan_path)

    assert len(errors) == 2
    assert any("missing-1" in e for e in errors)
    assert any("missing-2" in e for e in errors)
