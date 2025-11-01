from pathlib import Path

import pytest

from sisyphus.core.plan_linter import PlanLinter
from sisyphus.core.plans.models import Metadata, PlanDocument, WorkPlan

pytestmark = [pytest.mark.anyio]


async def test_self_reference_in_depends_on__if_plan_depends_on_itself__detects_cycle() -> None:
    # given
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-02T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-self",
                name="Self Referencing Plan",
                depends_on=["plan-self"],
                todos=[],
            ),
        ],
    )
    linter = PlanLinter({})
    plan_path = Path("/fake/self-ref.yaml")

    # when
    errors = linter.validate_depends_on(plan_doc, plan_path)

    # then
    assert len(errors) == 1
    assert "Circular dependency detected" in errors[0]
    assert "plan-self" in errors[0]


async def test_self_reference_with_other_dependencies__if_includes_self__detects_cycle() -> None:
    # given
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-02T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-a",
                name="Plan A",
                depends_on=["plan-b", "plan-a"],
                todos=[],
            ),
            WorkPlan(
                id="plan-b",
                name="Plan B",
                depends_on=[],
                todos=[],
            ),
        ],
    )
    linter = PlanLinter({})
    plan_path = Path("/fake/mixed-self-ref.yaml")

    # when
    errors = linter.validate_depends_on(plan_doc, plan_path)

    # then
    assert len(errors) >= 1
    assert any("Circular dependency detected" in e for e in errors)
    assert any("plan-a" in e for e in errors)


async def test_multiple_self_references__if_multiple_plans_self_reference__detects_all() -> None:
    # given
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-02T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="plan-x",
                name="Plan X",
                depends_on=["plan-x"],
                todos=[],
            ),
            WorkPlan(
                id="plan-y",
                name="Plan Y",
                depends_on=["plan-y"],
                todos=[],
            ),
        ],
    )
    linter = PlanLinter({})
    plan_path = Path("/fake/multiple-self-ref.yaml")

    # when
    errors = linter.validate_depends_on(plan_doc, plan_path)

    # then
    assert len(errors) >= 2
    assert sum("plan-x" in e for e in errors) >= 1
    assert sum("plan-y" in e for e in errors) >= 1
