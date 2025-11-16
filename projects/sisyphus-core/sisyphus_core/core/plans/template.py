from __future__ import annotations

from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path

from ruamel.yaml import YAML

from sisyphus_core.core.plans.models import (
    Background,
    FinalVerificationItem,
    LLMJudgeVerification,
    Metadata,
    Objectives,
    PlanDocument,
    RequiredBackground,
    SuccessVision,
    UserRequest,
    Workflow,
    WorkPlan,
)


class PlanTemplateGenerator:
    """Generate plan templates from Pydantic models (Single Source of Truth)."""

    @staticmethod
    def _get_reference_example() -> Path:
        """Get path to example backend.yaml reference.

        Uses importlib.resources to locate the file within the sisyphus_core package.
        """
        try:
            examples_dir = files("sisyphus_core") / "examples" / "multi-file"
            backend_yaml = examples_dir / "backend.yaml"
            path = Path(str(backend_yaml))
            if path.exists():
                return path
        except Exception:
            pass

        raise FileNotFoundError("Example file not found: sisyphus_core/examples/multi-file/backend.yaml")

    @staticmethod
    def full_example() -> PlanDocument:
        """
        Generate full example template with all fields populated.

        Loads example-work-plan.yaml and updates timestamps.
        This ensures template stays in sync with documentation.
        """
        yaml = YAML()
        yaml.preserve_quotes = True

        example_path = PlanTemplateGenerator._get_reference_example()

        try:
            with example_path.open("r", encoding="utf-8") as f:
                data = yaml.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Example file not found: {example_path}") from e

        # Update timestamps to current time
        now = datetime.now(UTC).isoformat()
        data["metadata"]["created_at"] = now
        data["metadata"]["updated_at"] = now

        for plan in data["work_plans"]:
            plan["user_request"]["created_at"] = now

        # ✅ model_validate 사용 (Pydantic v2 권장)
        return PlanDocument.model_validate(data)

    @staticmethod
    def minimal() -> PlanDocument:
        """
        Generate minimal template with TODO placeholders.

        Uses Pydantic models directly, ensuring type safety.
        """
        now = datetime.now(UTC).isoformat()

        return PlanDocument(
            version="3.0",
            metadata=Metadata(created_at=now, updated_at=now),
            work_plans=[
                WorkPlan(
                    id="new-plan",
                    name="New Plan",
                    depends_on=[],
                    user_request=UserRequest(
                        original="TODO: Describe your work request here",
                        created_at=now,
                        additional=[],
                    ),
                    objectives=Objectives(core="TODO: Write core objective here", detailed=[]),
                    background=Background(
                        current_situation="TODO: Describe current state",
                        reason_for_change="TODO: Why this work is needed",
                        changes_to_make="TODO: What will change",
                    ),
                    required_background=RequiredBackground(
                        description="TODO: Required context and knowledge",
                        file_structure=None,
                        references=[],
                    ),
                    workflow=Workflow(dependency_diagram="TODO: Add task dependency diagram", critical_path=[]),
                    success_vision=SuccessVision(
                        user_perspective=[],
                        business_perspective=[],
                        technical_criteria=[],
                    ),
                    final_verification=[
                        # Example structure for guidance
                        FinalVerificationItem(
                            id="example-final-1",
                            title="TODO: Final verification title",
                            category="TODO: Category (e.g., Functionality, Quality)",
                            description="TODO: What to verify",
                            verified=False,
                            orchestrator_manually_verified=False,
                            manual_verification_evidence="",
                            bash=[],
                            llm_judge=[
                                LLMJudgeVerification(
                                    context_commands=[
                                        "# TODO: Add context gathering commands",
                                        "# Example: cat src/main.py",
                                        "# Example: grep 'pattern' src/",
                                    ],
                                    instruction=(
                                        "TODO: Write verification criteria:\n"
                                        "1. Criterion 1\n"
                                        "2. Criterion 2\n\n"
                                        "Success: All criteria met\n"
                                        "Failure: Any criterion fails"
                                    ),
                                )
                            ],
                        )
                    ],
                    todos=[],
                    references=[],
                )
            ],
        )
