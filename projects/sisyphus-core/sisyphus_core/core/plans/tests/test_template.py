from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from sisyphus.core.plans.models import PlanDocument
from sisyphus.core.plans.template import PlanTemplateGenerator

pytestmark = [pytest.mark.anyio]


class TestPlanTemplateGenerator:
    async def test_minimal__creates_valid_plan_document(self) -> None:
        # given
        # PlanTemplateGenerator class exists

        # when
        doc = PlanTemplateGenerator.minimal()

        # then
        assert isinstance(doc, PlanDocument)
        assert doc.version == "3.0"
        assert len(doc.work_plans) == 1

        plan = doc.work_plans[0]
        assert plan.id == "new-plan"
        assert plan.name == "New Plan"
        assert plan.user_request.original.startswith("TODO:")
        assert plan.objectives.core.startswith("TODO:")

    async def test_minimal__includes_final_verification_example(self) -> None:
        # given
        # PlanTemplateGenerator class exists

        # when
        doc = PlanTemplateGenerator.minimal()

        # then
        plan = doc.work_plans[0]
        assert len(plan.final_verification) >= 1

        verification = plan.final_verification[0]
        assert verification.id == "example-final-1"
        assert len(verification.llm_judge) >= 1

        judge = verification.llm_judge[0]
        assert len(judge.context_commands) > 0
        assert "TODO:" in judge.instruction

    async def test_minimal__timestamps_are_current(self) -> None:
        # given
        # PlanTemplateGenerator class exists

        # when
        before = datetime.now(UTC)
        doc = PlanTemplateGenerator.minimal()
        after = datetime.now(UTC)

        # then
        created_at = datetime.fromisoformat(doc.metadata.created_at.replace("Z", "+00:00"))
        assert before <= created_at <= after

    async def test_minimal__todos_is_empty_list(self) -> None:
        # given
        # PlanTemplateGenerator class exists

        # when
        doc = PlanTemplateGenerator.minimal()

        # then
        assert doc.work_plans[0].todos == []

    async def test_full_example__loads_reference_yaml(self) -> None:
        # given
        # example-work-plan.yaml exists

        # when
        doc = PlanTemplateGenerator.full_example()

        # then
        assert isinstance(doc, PlanDocument)
        assert doc.version == "3.0"
        assert len(doc.work_plans) >= 1

        plan = doc.work_plans[0]
        assert len(plan.todos) > 0
        assert len(plan.final_verification) > 0

    async def test_full_example__updates_timestamps(self) -> None:
        # given
        # example-work-plan.yaml with old timestamps

        # when
        before = datetime.now(UTC)
        doc = PlanTemplateGenerator.full_example()
        after = datetime.now(UTC)

        # then
        created_at = datetime.fromisoformat(doc.metadata.created_at.replace("Z", "+00:00"))
        assert before <= created_at <= after

        updated_at = datetime.fromisoformat(doc.metadata.updated_at.replace("Z", "+00:00"))
        assert before <= updated_at <= after

    async def test_full_example__file_not_found__raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # given
        monkeypatch.setattr(
            PlanTemplateGenerator,
            "_get_reference_example",
            lambda: Path("/nonexistent/example.yaml"),
        )

        # when/then
        with pytest.raises(FileNotFoundError, match="Example file not found"):
            PlanTemplateGenerator.full_example()
