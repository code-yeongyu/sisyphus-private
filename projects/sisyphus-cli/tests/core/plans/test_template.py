"""Tests for PlanTemplateGenerator."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from sisyphus.core.plans.models import PlanDocument
from sisyphus.core.plans.template import PlanTemplateGenerator

pytestmark = [pytest.mark.anyio]


# ============================================================================
# 4.2 minimal() Method Tests
# ============================================================================


async def test_minimal__when_called__returns_plan_document() -> None:
    """minimal() returns a valid PlanDocument instance."""
    # given - no setup needed

    # when
    result = PlanTemplateGenerator.minimal()

    # then
    assert isinstance(result, PlanDocument)
    assert result.version == "3.0"
    assert len(result.work_plans) == 1


async def test_minimal__when_called__includes_todo_placeholders() -> None:
    """minimal() includes TODO placeholders in all required fields."""
    # given - no setup needed

    # when
    result = PlanTemplateGenerator.minimal()

    # then
    work_plan = result.work_plans[0]
    assert "TODO" in work_plan.user_request.original
    assert "TODO" in work_plan.objectives.core
    assert "TODO" in work_plan.background.current_situation
    assert "TODO" in work_plan.required_background.description
    assert "TODO" in work_plan.workflow.dependency_diagram


async def test_minimal__when_called__includes_final_verification_example() -> None:
    """minimal() includes a final_verification example with LLM judge."""
    # given - no setup needed

    # when
    result = PlanTemplateGenerator.minimal()

    # then
    work_plan = result.work_plans[0]
    assert len(work_plan.final_verification) == 1
    verification = work_plan.final_verification[0]
    assert verification.id == "example-final-1"
    assert "TODO" in verification.title
    assert len(verification.llm_judge) == 1
    assert "TODO" in verification.llm_judge[0].instruction


async def test_minimal__when_called__has_current_timestamp() -> None:
    """minimal() uses current UTC timestamp for created_at fields."""
    # given

    before = datetime.now(UTC).isoformat()

    # when
    result = PlanTemplateGenerator.minimal()

    # then
    after = datetime.now(UTC).isoformat()
    assert before <= result.metadata.created_at <= after
    assert before <= result.work_plans[0].user_request.created_at <= after


# ============================================================================
# 4.3 full_example() Method Tests
# ============================================================================


async def test_full_example__when_file_exists__returns_plan_document() -> None:
    """full_example() loads example-work-plan.yaml and returns PlanDocument."""
    # given - example file exists (verified by method)

    # when
    result = PlanTemplateGenerator.full_example()

    # then
    assert isinstance(result, PlanDocument)
    assert result.version == "3.0"
    assert len(result.work_plans) > 0


async def test_full_example__when_called__updates_timestamps() -> None:
    """full_example() updates metadata and user_request timestamps to current time."""
    # given

    before = datetime.now(UTC).isoformat()

    # when
    result = PlanTemplateGenerator.full_example()

    # then
    after = datetime.now(UTC).isoformat()
    assert before <= result.metadata.created_at <= after
    assert result.metadata.updated_at is not None
    assert before <= result.metadata.updated_at <= after
    for plan in result.work_plans:
        assert before <= plan.user_request.created_at <= after


async def test_full_example__when_file_missing__raises_file_not_found() -> None:
    """full_example() raises FileNotFoundError when example file is missing."""
    # given
    with patch.object(
        PlanTemplateGenerator,
        "_get_reference_example",
        return_value=Path("/nonexistent/path/example.yaml"),
    ):
        # when/then
        with pytest.raises(FileNotFoundError, match="Example file not found"):
            PlanTemplateGenerator.full_example()
