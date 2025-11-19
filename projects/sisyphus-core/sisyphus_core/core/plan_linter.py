"""YAML work plan linter for schema validation."""

# ruff: noqa: ANN401
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from sisyphus_core.core.graph.dependencies import build_plan_graph, detect_cycles
from sisyphus_core.core.plans.models import PlanDocument, RetrievalType, TodoStatus
from sisyphus_core.core.plans.references import ReferenceResolver
from sisyphus_core.core.plans.registry import load_registry, resolve_registry_plan


@dataclass
class LintError:
    """Lint error information.

    Note: All error messages are in English for LLM workflow compatibility
    (Pydantic ValidationError also uses English).
    """

    location: str  # e.g., "todos[0].status", "metadata.created_at"
    message: str  # e.g., "Missing required field"
    expected: str | None = None  # e.g., "string", "one of [pending, in_progress, completed]"
    actual: str | None = None  # e.g., "null", "invalid"
    suggestion: str | None = None  # e.g., "Add field 'created_at'"
    category: str = "schema"  # "schema" | "dependency" | "cycle" | "reference"


class PlanLinter:
    """YAML work plan linter."""

    def __init__(self, schema_doc: dict[str, Any]) -> None:
        """Initialize with plan schema definition.

        Args:
            schema_doc: Schema정보 (나중에 확장용, 현재는 Pydantic 모델 기반)
        """
        self.errors: list[LintError] = []

    def lint(self, yaml_data: dict[str, Any]) -> list[LintError]:
        """Lint YAML data and return all errors (v3.0 PlanDocument).

        Args:
            yaml_data: Parsed YAML dictionary

        Returns:
            List of lint errors (empty if valid)
        """
        self.errors = []
        self._validate_root_fields(yaml_data)  # v3.0 PlanDocument validation
        self._validate_metadata(yaml_data)
        # work_plans validation is handled in _validate_root_fields
        return self.errors

    def _validate_root_fields(self, data: dict[str, Any]) -> None:
        """Validate PlanDocument root fields (v3.0).

        v3.0 structure: PlanDocument contains version, metadata, and work_plans list.
        Each work_plan in the list is validated separately.
        """
        allowed_root = {"version", "metadata", "work_plans"}
        self._check_extra_fields(data, "", allowed_root)

        required_fields = ["version", "metadata", "work_plans"]
        for field in required_fields:
            if field not in data:
                self.errors.append(
                    LintError(
                        location=field,
                        message="Missing required field",
                        expected="field must exist",
                        suggestion=f"Add '{field}' section to YAML",
                    )
                )

        if "version" in data:
            self._check_type(data["version"], "version", "string")
            if isinstance(data["version"], str) and data["version"] != "3.0":
                self.errors.append(
                    LintError(
                        location="version",
                        message="Unsupported version",
                        expected="3.0",
                        actual=data["version"],
                        suggestion="Change version to '3.0'",
                    )
                )

        if "work_plans" in data:
            self._check_type(data["work_plans"], "work_plans", "list")
            if isinstance(data["work_plans"], list):
                for i, plan in enumerate(data["work_plans"]):
                    self._validate_work_plan(plan, f"work_plans[{i}]")

    def _validate_work_plan(self, plan: dict[str, Any], path: str) -> None:
        """Validate individual WorkPlan fields (v3.0).

        Validates a single work plan from the work_plans list.
        Reuses existing validation methods for nested structures.
        """
        if not isinstance(plan, dict):
            self._check_type(plan, path, "dict")
            return

        allowed_fields = {
            "id",
            "name",
            "depends_on",
            "user_request",
            "objectives",
            "background",
            "required_background",
            "workflow",
            "success_vision",
            "final_verification",
            "todos",
            "references",
            "execution",
            "work_mode",
            "current_work_ids",
            "acceptance_criteria_for_verification_agent",
            "fully_done_evidence",
        }
        self._check_extra_fields(plan, path, allowed_fields)

        required_fields = [
            "id",
            "name",
            "user_request",
            "objectives",
            "background",
            "required_background",
            "workflow",
            "success_vision",
            "final_verification",
            "todos",
        ]
        for field in required_fields:
            if field not in plan:
                self.errors.append(
                    LintError(
                        location=f"{path}.{field}",
                        message="Missing required field",
                        expected="field must exist",
                        suggestion=f"Add '{field}' to {path}",
                    )
                )

        if "id" in plan:
            self._check_type(plan["id"], f"{path}.id", "string")
        if "name" in plan:
            self._check_type(plan["name"], f"{path}.name", "string")
        if "depends_on" in plan:
            self._check_type(plan["depends_on"], f"{path}.depends_on", "list")

        if "user_request" in plan:
            self._validate_user_request_in_plan(plan["user_request"], f"{path}.user_request")
        if "objectives" in plan:
            self._validate_objectives_in_plan(plan["objectives"], f"{path}.objectives")
        if "background" in plan:
            self._validate_background_in_plan(plan["background"], f"{path}.background")
        if "required_background" in plan:
            self._validate_required_background_in_plan(plan["required_background"], f"{path}.required_background")
        if "workflow" in plan:
            self._validate_workflow_in_plan(plan["workflow"], f"{path}.workflow")
        if "success_vision" in plan:
            self._validate_success_vision_in_plan(plan["success_vision"], f"{path}.success_vision")
        if "final_verification" in plan:
            self._validate_final_verification_in_plan(plan["final_verification"], f"{path}.final_verification")
        if "todos" in plan:
            self._validate_todos_in_plan(plan["todos"], f"{path}.todos")

        if "execution" in plan:
            self._validate_execution_in_plan(plan["execution"], f"{path}.execution")
        if "work_mode" in plan:
            self._validate_work_mode_in_plan(plan["work_mode"], f"{path}.work_mode")
        if "current_work_ids" in plan:
            self._check_type(plan["current_work_ids"], f"{path}.current_work_ids", "list")

    def _validate_user_request_in_plan(self, user_req: Any, path: str) -> None:
        """Validate user_request within a work plan."""
        if not isinstance(user_req, dict):
            self._check_type(user_req, path, "dict")
            return

        allowed_fields = {"original", "created_at", "additional", "expected_outcome", "forbidden_outcome"}
        self._check_extra_fields(user_req, path, allowed_fields)
        self._validate_nested_required(user_req, path, ["original", "created_at"])

        if "original" in user_req:
            self._check_type(user_req["original"], f"{path}.original", "string")
        if "created_at" in user_req:
            self._check_type(user_req["created_at"], f"{path}.created_at", "string")
        if "additional" in user_req:
            self._check_type(user_req["additional"], f"{path}.additional", "list")
        if "expected_outcome" in user_req and user_req["expected_outcome"] is not None:
            self._check_type(user_req["expected_outcome"], f"{path}.expected_outcome", "string")
        if "forbidden_outcome" in user_req and user_req["forbidden_outcome"] is not None:
            self._check_type(user_req["forbidden_outcome"], f"{path}.forbidden_outcome", "string")

    def _validate_objectives_in_plan(self, objectives: Any, path: str) -> None:
        """Validate objectives within a work plan."""
        if not isinstance(objectives, dict):
            self._check_type(objectives, path, "dict")
            return

        allowed_fields = {"core", "detailed"}
        self._check_extra_fields(objectives, path, allowed_fields)
        self._validate_nested_required(objectives, path, ["core"])

        if "core" in objectives:
            self._check_type(objectives["core"], f"{path}.core", "string")
        if "detailed" in objectives:
            self._check_type(objectives["detailed"], f"{path}.detailed", "list")
            if isinstance(objectives["detailed"], list):
                for i, detail in enumerate(objectives["detailed"]):
                    detail_path = f"{path}.detailed[{i}]"
                    if not isinstance(detail, dict):
                        self._check_type(detail, detail_path, "dict")
                        continue
                    allowed_detail_fields = {"goal", "measurable"}
                    self._check_extra_fields(detail, detail_path, allowed_detail_fields)
                    self._validate_nested_required(detail, detail_path, ["goal", "measurable"])
                    if "goal" in detail:
                        self._check_type(detail["goal"], f"{detail_path}.goal", "string")
                    if "measurable" in detail:
                        self._check_type(detail["measurable"], f"{detail_path}.measurable", "string")

    def _validate_background_in_plan(self, background: Any, path: str) -> None:
        """Validate background within a work plan."""
        if not isinstance(background, dict):
            self._check_type(background, path, "dict")
            return

        allowed_fields = {"current_situation", "reason_for_change", "changes_to_make"}
        self._check_extra_fields(background, path, allowed_fields)
        self._validate_nested_required(background, path, ["current_situation", "reason_for_change", "changes_to_make"])

        if "current_situation" in background:
            self._check_type(background["current_situation"], f"{path}.current_situation", "string")
        if "reason_for_change" in background:
            self._check_type(background["reason_for_change"], f"{path}.reason_for_change", "string")
        if "changes_to_make" in background:
            self._check_type(background["changes_to_make"], f"{path}.changes_to_make", "string")

    def _validate_required_background_in_plan(self, req_bg: Any, path: str) -> None:
        """Validate required_background within a work plan."""
        if not isinstance(req_bg, dict):
            self._check_type(req_bg, path, "dict")
            return

        allowed_fields = {"description", "file_structure", "references"}
        self._check_extra_fields(req_bg, path, allowed_fields)
        self._validate_nested_required(req_bg, path, ["description"])

        if "description" in req_bg:
            self._check_type(req_bg["description"], f"{path}.description", "string")
        if "file_structure" in req_bg and req_bg["file_structure"] is not None:
            self._check_type(req_bg["file_structure"], f"{path}.file_structure", "string")
        if "references" in req_bg:
            self._check_type(req_bg["references"], f"{path}.references", "list")

    def _validate_workflow_in_plan(self, workflow: Any, path: str) -> None:
        """Validate workflow within a work plan."""
        if not isinstance(workflow, dict):
            self._check_type(workflow, path, "dict")
            return

        allowed_fields = {"dependency_diagram", "critical_path"}
        self._check_extra_fields(workflow, path, allowed_fields)
        self._validate_nested_required(workflow, path, ["dependency_diagram"])

        if "dependency_diagram" in workflow:
            self._check_type(workflow["dependency_diagram"], f"{path}.dependency_diagram", "string")
        if "critical_path" in workflow:
            self._check_type(workflow["critical_path"], f"{path}.critical_path", "list")

    def _validate_success_vision_in_plan(self, success_vision: Any, path: str) -> None:
        """Validate success_vision within a work plan."""
        if not isinstance(success_vision, dict):
            self._check_type(success_vision, path, "dict")
            return

        allowed_fields = {"user_perspective", "business_perspective", "technical_criteria"}
        self._check_extra_fields(success_vision, path, allowed_fields)

        if "user_perspective" in success_vision:
            self._check_type(success_vision["user_perspective"], f"{path}.user_perspective", "list")
            if isinstance(success_vision["user_perspective"], list):
                for i, scenario in enumerate(success_vision["user_perspective"]):
                    scenario_path = f"{path}.user_perspective[{i}]"
                    if not isinstance(scenario, dict):
                        self._check_type(scenario, scenario_path, "dict")
                        continue
                    allowed_scenario_fields = {"scenario", "experience"}
                    self._check_extra_fields(scenario, scenario_path, allowed_scenario_fields)
                    self._validate_nested_required(scenario, scenario_path, ["scenario", "experience"])
                    if "scenario" in scenario:
                        self._check_type(scenario["scenario"], f"{scenario_path}.scenario", "string")
                    if "experience" in scenario:
                        self._check_type(scenario["experience"], f"{scenario_path}.experience", "string")

        if "business_perspective" in success_vision:
            self._check_type(success_vision["business_perspective"], f"{path}.business_perspective", "list")
            if isinstance(success_vision["business_perspective"], list):
                for i, metric in enumerate(success_vision["business_perspective"]):
                    metric_path = f"{path}.business_perspective[{i}]"
                    if not isinstance(metric, dict):
                        self._check_type(metric, metric_path, "dict")
                        continue
                    allowed_metric_fields = {"metric", "target"}
                    self._check_extra_fields(metric, metric_path, allowed_metric_fields)
                    self._validate_nested_required(metric, metric_path, ["metric", "target"])
                    if "metric" in metric:
                        self._check_type(metric["metric"], f"{metric_path}.metric", "string")
                    if "target" in metric:
                        self._check_type(metric["target"], f"{metric_path}.target", "string")

        if "technical_criteria" in success_vision:
            self._check_type(success_vision["technical_criteria"], f"{path}.technical_criteria", "list")
            if isinstance(success_vision["technical_criteria"], list):
                for i, criterion in enumerate(success_vision["technical_criteria"]):
                    criterion_path = f"{path}.technical_criteria[{i}]"
                    if not isinstance(criterion, dict):
                        self._check_type(criterion, criterion_path, "dict")
                        continue
                    allowed_criterion_fields = {"category", "criteria", "command", "expected"}
                    self._check_extra_fields(criterion, criterion_path, allowed_criterion_fields)
                    self._validate_nested_required(criterion, criterion_path, ["category", "criteria", "expected"])
                    if "category" in criterion:
                        self._check_type(criterion["category"], f"{criterion_path}.category", "string")
                    if "criteria" in criterion:
                        self._check_type(criterion["criteria"], f"{criterion_path}.criteria", "string")
                    if "command" in criterion and criterion["command"] is not None:
                        self._check_type(criterion["command"], f"{criterion_path}.command", "string")
                    if "expected" in criterion:
                        self._check_type(criterion["expected"], f"{criterion_path}.expected", "string")

    def _validate_final_verification_in_plan(self, final_verification: Any, path: str) -> None:
        """Validate final_verification within a work plan."""
        if not isinstance(final_verification, list):
            self._check_type(final_verification, path, "list")
            return

        for i, item in enumerate(final_verification):
            item_path = f"{path}[{i}]"
            if not isinstance(item, dict):
                self._check_type(item, item_path, "dict")
                continue

            allowed_item_fields = {
                "id",
                "title",
                "category",
                "description",
                "verified",
                "verified_at",
                "verification_evidence",
                "orchestrator_manually_verified",
                "manual_verification_evidence",
                "bash",
                "llm_judge",
            }
            self._check_extra_fields(item, item_path, allowed_item_fields)
            self._validate_nested_required(
                item,
                item_path,
                [
                    "id",
                    "title",
                    "category",
                    "description",
                    "orchestrator_manually_verified",
                    "manual_verification_evidence",
                ],
            )

            if "id" in item:
                self._check_type(item["id"], f"{item_path}.id", "string")
            if "title" in item:
                self._check_type(item["title"], f"{item_path}.title", "string")
            if "category" in item:
                self._check_type(item["category"], f"{item_path}.category", "string")
            if "description" in item:
                self._check_type(item["description"], f"{item_path}.description", "string")
            if "verified" in item:
                self._check_type(item["verified"], f"{item_path}.verified", "boolean")
            if "verified_at" in item and item["verified_at"] is not None:
                self._check_type(item["verified_at"], f"{item_path}.verified_at", "string")
            if "verification_evidence" in item and item["verification_evidence"] is not None:
                self._check_type(item["verification_evidence"], f"{item_path}.verification_evidence", "string")
            if "orchestrator_manually_verified" in item:
                self._check_type(
                    item["orchestrator_manually_verified"], f"{item_path}.orchestrator_manually_verified", "boolean"
                )
            if "manual_verification_evidence" in item:
                self._check_type(
                    item["manual_verification_evidence"], f"{item_path}.manual_verification_evidence", "string"
                )

            has_bash = "bash" in item and item["bash"]
            has_llm = "llm_judge" in item and item["llm_judge"]
            if not has_bash and not has_llm:
                self.errors.append(
                    LintError(
                        location=item_path,
                        message="bash or llm_judge is required",
                        expected="at least one of bash or llm_judge",
                        actual="neither present",
                        suggestion="Add 'bash' or 'llm_judge' field",
                    )
                )

            if has_bash:
                self._validate_bash_list(item["bash"], f"{item_path}.bash")
            if has_llm:
                self._validate_llm_judge_list(item["llm_judge"], f"{item_path}.llm_judge")

    def _validate_todos_in_plan(self, todos: Any, path: str) -> None:
        """Validate todos within a work plan."""
        if not isinstance(todos, list):
            self._check_type(todos, path, "list")
            return

        if len(todos) == 0:
            self.errors.append(
                LintError(
                    location=path,
                    message="Empty todos list",
                    expected="at least one todo",
                    actual="empty list",
                    suggestion="Add at least one todo item to the todos list",
                )
            )
            return

        for i, todo in enumerate(todos):
            self._validate_todo(todo, f"{path}[{i}]")

    def _validate_execution_in_plan(self, exec_data: Any, path: str) -> None:
        """Validate execution field within a work plan (v3.0)."""
        if not isinstance(exec_data, dict):
            self._check_type(exec_data, path, "dict")
            return

        allowed_exec_fields = {"started", "completed", "started_at", "completed_at", "fully_done_at"}
        self._check_extra_fields(exec_data, path, allowed_exec_fields)
        self._validate_nested_required(exec_data, path, ["started", "completed"])

        if "started" in exec_data:
            self._check_type(exec_data["started"], f"{path}.started", "boolean")
        if "completed" in exec_data:
            self._check_type(exec_data["completed"], f"{path}.completed", "boolean")
        if "started_at" in exec_data and exec_data["started_at"] is not None:
            self._check_type(exec_data["started_at"], f"{path}.started_at", "string")
        if "completed_at" in exec_data and exec_data["completed_at"] is not None:
            self._check_type(exec_data["completed_at"], f"{path}.completed_at", "string")

    def _validate_work_mode_in_plan(self, work_mode: Any, path: str) -> None:
        """Validate work_mode field within a work plan (v3.0)."""
        if not isinstance(work_mode, dict):
            self._check_type(work_mode, path, "dict")
            return

        allowed_wm_fields = {"parallel_requested", "current_task_id"}
        self._check_extra_fields(work_mode, path, allowed_wm_fields)
        self._validate_nested_required(work_mode, path, ["parallel_requested"])

        if "parallel_requested" in work_mode:
            self._check_type(work_mode["parallel_requested"], f"{path}.parallel_requested", "boolean")
        if "current_task_id" in work_mode and work_mode["current_task_id"] is not None:
            self._check_type(work_mode["current_task_id"], f"{path}.current_task_id", "string")

    def _validate_nested_required(self, data: dict[str, Any], path: str, required_fields: list[str]) -> None:
        """Validate required fields in nested object."""
        for field in required_fields:
            if field not in data:
                location = f"{path}.{field}" if path else field
                self.errors.append(
                    LintError(
                        location=location,
                        message="Missing required field",
                        expected="field must exist",
                        suggestion=f"Add '{field}' to {path or 'root'}",
                    )
                )

    def _check_type(
        self,
        data: Any,
        location: str,
        expected_type: str,  # noqa: ANN401
    ) -> None:
        """Check if data matches expected type."""
        if expected_type == "string" and not isinstance(data, str):
            self.errors.append(
                LintError(
                    location=location,
                    message="Type mismatch",
                    expected="string",
                    actual=type(data).__name__,
                    suggestion="Change value to string",
                )
            )
        elif expected_type == "boolean" and not isinstance(data, bool):
            self.errors.append(
                LintError(
                    location=location,
                    message="Type mismatch",
                    expected="boolean",
                    actual=type(data).__name__,
                    suggestion=f"Use true/false (not {data!r})",
                )
            )
        elif expected_type == "int" and not isinstance(data, int):
            self.errors.append(
                LintError(
                    location=location,
                    message="Type mismatch",
                    expected="int",
                    actual=type(data).__name__,
                    suggestion="Change value to integer",
                )
            )
        elif expected_type == "list" and not isinstance(data, list):
            self.errors.append(
                LintError(
                    location=location,
                    message="Type mismatch",
                    expected="list",
                    actual=type(data).__name__,
                    suggestion="Change value to list (array)",
                )
            )
        elif expected_type == "dict" and not isinstance(data, dict):
            self.errors.append(
                LintError(
                    location=location,
                    message="Type mismatch",
                    expected="dict",
                    actual=type(data).__name__,
                    suggestion="Change value to dictionary (object)",
                )
            )

    def _check_extra_fields(self, data: dict[str, Any], path: str, allowed_fields: set[str]) -> None:
        """Check for undefined extra fields."""
        for key in data.keys():
            if key not in allowed_fields:
                location = f"{path}.{key}" if path else key
                self.errors.append(
                    LintError(
                        location=location,
                        message="Unknown field (not in schema)",
                        expected=f"one of {sorted(allowed_fields)}",
                        actual=key,
                        suggestion=f"Remove '{key}' or check spelling",
                    )
                )

    def _check_enum(
        self,
        value: Any,
        location: str,
        enum_class: type[Enum],  # noqa: ANN401
    ) -> None:
        """Check if value is valid enum member."""
        valid_values = [e.value for e in enum_class]
        if value not in valid_values:
            self.errors.append(
                LintError(
                    location=location,
                    message="Invalid enum value",
                    expected=f"one of {valid_values}",
                    actual=str(value),
                    suggestion=f"Change to one of: {', '.join(valid_values)}",
                )
            )

    def _check_pattern(self, value: str, location: str, pattern: str, description: str) -> None:
        """Check if value matches regex pattern."""
        if not re.match(pattern, value):
            self.errors.append(
                LintError(
                    location=location,
                    message="Pattern mismatch",
                    expected=description,
                    actual=value,
                    suggestion=f"Value must match pattern: {pattern}",
                )
            )

    def _validate_discriminated_union_type(self, data: dict[str, Any], location: str, valid_types: list[str]) -> bool:
        """Validate type field for discriminated unions (ReferenceSpec, RetrievalSpec).

        Returns: True if type is valid, False if invalid (caller should skip further validation)
        """
        if "type" not in data:
            self.errors.append(
                LintError(
                    location=f"{location}.type",
                    message="Missing required field",
                    expected="type field must exist for discriminated union",
                    suggestion=f"Add 'type' field with one of: {', '.join(valid_types)}",
                )
            )
            return False

        if data["type"] not in valid_types:
            # This will be caught by literal validation later
            pass

        return True

    def _validate_metadata(self, data: dict[str, Any]) -> None:
        """Validate metadata section (PlanDocument.metadata)."""
        if "metadata" not in data:
            return
        metadata = data["metadata"]

        if not isinstance(metadata, dict):
            self._check_type(metadata, "metadata", "dict")
            return

        allowed_fields = {"created_at", "updated_at"}
        self._check_extra_fields(metadata, "metadata", allowed_fields)

        self._validate_nested_required(metadata, "metadata", ["created_at"])

        if "created_at" in metadata:
            self._check_type(metadata["created_at"], "metadata.created_at", "string")
        if "updated_at" in metadata and metadata["updated_at"] is not None:
            self._check_type(metadata["updated_at"], "metadata.updated_at", "string")

    def _validate_user_request(self, data: dict[str, Any]) -> None:
        """Validate user_request section."""
        if "user_request" not in data:
            return
        user_req = data["user_request"]

        if not isinstance(user_req, dict):
            self._check_type(user_req, "user_request", "dict")
            return

        allowed_fields = {"original", "created_at", "additional"}
        self._check_extra_fields(user_req, "user_request", allowed_fields)

        self._validate_nested_required(user_req, "user_request", ["original", "created_at"])

        if "original" in user_req:
            self._check_type(user_req["original"], "user_request.original", "string")
        if "created_at" in user_req:
            self._check_type(user_req["created_at"], "user_request.created_at", "string")
        if "additional" in user_req:
            self._check_type(user_req["additional"], "user_request.additional", "list")

    def _validate_objectives(self, data: dict[str, Any]) -> None:
        """Validate objectives section."""
        if "objectives" not in data:
            return
        objectives = data["objectives"]

        if not isinstance(objectives, dict):
            self._check_type(objectives, "objectives", "dict")
            return

        allowed_fields = {"core", "detailed"}
        self._check_extra_fields(objectives, "objectives", allowed_fields)

        self._validate_nested_required(objectives, "objectives", ["core"])

        if "core" in objectives:
            self._check_type(objectives["core"], "objectives.core", "string")
        if "detailed" in objectives:
            self._check_type(objectives["detailed"], "objectives.detailed", "list")
            if isinstance(objectives["detailed"], list):
                for i, detail in enumerate(objectives["detailed"]):
                    detail_path = f"objectives.detailed[{i}]"
                    if not isinstance(detail, dict):
                        self._check_type(detail, detail_path, "dict")
                        continue
                    allowed_detail_fields = {"goal", "measurable"}
                    self._check_extra_fields(detail, detail_path, allowed_detail_fields)
                    self._validate_nested_required(detail, detail_path, ["goal", "measurable"])
                    if "goal" in detail:
                        self._check_type(detail["goal"], f"{detail_path}.goal", "string")
                    if "measurable" in detail:
                        self._check_type(detail["measurable"], f"{detail_path}.measurable", "string")

    def _validate_background(self, data: dict[str, Any]) -> None:
        """Validate background section."""
        if "background" not in data:
            return
        background = data["background"]

        if not isinstance(background, dict):
            self._check_type(background, "background", "dict")
            return

        allowed_fields = {"current_situation", "reason_for_change", "changes_to_make"}
        self._check_extra_fields(background, "background", allowed_fields)

        self._validate_nested_required(
            background, "background", ["current_situation", "reason_for_change", "changes_to_make"]
        )

        if "current_situation" in background:
            self._check_type(background["current_situation"], "background.current_situation", "string")
        if "reason_for_change" in background:
            self._check_type(background["reason_for_change"], "background.reason_for_change", "string")
        if "changes_to_make" in background:
            self._check_type(background["changes_to_make"], "background.changes_to_make", "string")

    def _validate_required_background(self, data: dict[str, Any]) -> None:
        """Validate required_background section."""
        if "required_background" not in data:
            return
        req_bg = data["required_background"]

        if not isinstance(req_bg, dict):
            self._check_type(req_bg, "required_background", "dict")
            return

        allowed_fields = {"description", "file_structure", "references"}
        self._check_extra_fields(req_bg, "required_background", allowed_fields)

        self._validate_nested_required(req_bg, "required_background", ["description"])

        if "description" in req_bg:
            self._check_type(req_bg["description"], "required_background.description", "string")
        if "file_structure" in req_bg and req_bg["file_structure"] is not None:
            self._check_type(req_bg["file_structure"], "required_background.file_structure", "string")
        if "references" in req_bg:
            self._check_type(req_bg["references"], "required_background.references", "list")

    def _validate_retrieval_spec(self, retrieval: Any, path: str) -> None:
        """Validate RetrievalSpec (discriminated union)."""
        if not isinstance(retrieval, dict):
            self._check_type(retrieval, path, "dict")
            return

        valid_types = ["keywords", "prompt"]
        if not self._validate_discriminated_union_type(retrieval, path, valid_types):
            return

        retrieval_type = retrieval.get("type")
        if retrieval_type == "keywords":
            allowed_fields = {"type", "keywords", "line_range"}
            self._check_extra_fields(retrieval, path, allowed_fields)
            self._validate_nested_required(retrieval, path, ["keywords"])
            if "keywords" in retrieval:
                self._check_type(retrieval["keywords"], f"{path}.keywords", "list")
        elif retrieval_type == "prompt":
            allowed_fields = {"type", "prompt"}
            self._check_extra_fields(retrieval, path, allowed_fields)
            self._validate_nested_required(retrieval, path, ["prompt"])
            if "prompt" in retrieval:
                self._check_type(retrieval["prompt"], f"{path}.prompt", "string")

        # Validate type enum
        if retrieval_type:
            self._check_enum(retrieval_type, f"{path}.type", RetrievalType)

    def _validate_status(self, data: dict[str, Any]) -> None:
        """Validate status section."""
        if "status" not in data:
            return
        status = data["status"]

        if not isinstance(status, dict):
            self._check_type(status, "status", "dict")
            return

        allowed_fields = {"execution", "work_mode", "current_work"}
        self._check_extra_fields(status, "status", allowed_fields)

        self._validate_nested_required(status, "status", ["execution", "work_mode", "current_work"])

        # Validate execution
        if "execution" in status:
            exec_data = status["execution"]
            if not isinstance(exec_data, dict):
                self._check_type(exec_data, "status.execution", "dict")
            else:
                allowed_exec_fields = {"started", "completed", "started_at", "completed_at", "fully_done_at"}
                self._check_extra_fields(exec_data, "status.execution", allowed_exec_fields)
                self._validate_nested_required(exec_data, "status.execution", ["started", "completed"])
                if "started" in exec_data:
                    self._check_type(exec_data["started"], "status.execution.started", "boolean")
                if "completed" in exec_data:
                    self._check_type(exec_data["completed"], "status.execution.completed", "boolean")
                if "started_at" in exec_data and exec_data["started_at"] is not None:
                    self._check_type(exec_data["started_at"], "status.execution.started_at", "string")
                if "completed_at" in exec_data and exec_data["completed_at"] is not None:
                    self._check_type(exec_data["completed_at"], "status.execution.completed_at", "string")

        # Validate work_mode
        if "work_mode" in status:
            work_mode = status["work_mode"]
            if not isinstance(work_mode, dict):
                self._check_type(work_mode, "status.work_mode", "dict")
            else:
                allowed_wm_fields = {"parallel_requested", "current_task_id"}
                self._check_extra_fields(work_mode, "status.work_mode", allowed_wm_fields)
                self._validate_nested_required(work_mode, "status.work_mode", ["parallel_requested"])
                if "parallel_requested" in work_mode:
                    self._check_type(work_mode["parallel_requested"], "status.work_mode.parallel_requested", "boolean")
                if "current_task_id" in work_mode and work_mode["current_task_id"] is not None:
                    self._check_type(work_mode["current_task_id"], "status.work_mode.current_task_id", "string")

        # Validate current_work
        if "current_work" in status:
            self._check_type(status["current_work"], "status.current_work", "string")

    def _validate_workflow(self, data: dict[str, Any]) -> None:
        """Validate workflow section."""
        if "workflow" not in data:
            return
        workflow = data["workflow"]

        if not isinstance(workflow, dict):
            self._check_type(workflow, "workflow", "dict")
            return

        allowed_fields = {"dependency_diagram", "critical_path"}
        self._check_extra_fields(workflow, "workflow", allowed_fields)

        self._validate_nested_required(workflow, "workflow", ["dependency_diagram"])

        if "dependency_diagram" in workflow:
            self._check_type(workflow["dependency_diagram"], "workflow.dependency_diagram", "string")
        if "critical_path" in workflow:
            self._check_type(workflow["critical_path"], "workflow.critical_path", "list")

    def _validate_todos(self, data: dict[str, Any]) -> None:
        """Validate todos section (recursive)."""
        if "todos" not in data:
            return
        todos = data["todos"]

        if not isinstance(todos, list):
            self._check_type(todos, "todos", "list")
            return

        if len(todos) == 0:
            self.errors.append(
                LintError(
                    location="todos",
                    message="Empty todos list",
                    expected="at least one todo",
                    actual="empty list",
                    suggestion="Add at least one todo item to the todos list",
                )
            )
            return

        for i, todo in enumerate(todos):
            self._validate_todo(todo, f"todos[{i}]")

    def _validate_todo(self, todo: Any, path: str) -> None:
        """Validate single todo item (v3.0)."""
        if not isinstance(todo, dict):
            self._check_type(todo, path, "dict")
            return

        allowed_fields = {
            "id",
            "title",
            "description",
            "status",
            "children",
            "references",
            "verification_spec",
            "parallel",
            "parallelable_and_safe_evidence",
            "acceptance_criteria",
        }
        self._check_extra_fields(todo, path, allowed_fields)

        self._validate_nested_required(todo, path, ["id", "title", "status"])

        if "id" in todo:
            self._check_type(todo["id"], f"{path}.id", "string")

        if "title" in todo:
            self._check_type(todo["title"], f"{path}.title", "string")

        if "description" in todo and todo["description"] is not None:
            self._check_type(todo["description"], f"{path}.description", "string")

        if "status" in todo:
            self._check_enum(todo["status"], f"{path}.status", TodoStatus)

        if "references" in todo:
            self._check_type(todo["references"], f"{path}.references", "list")

        if "verification_spec" in todo:
            self._check_type(todo["verification_spec"], f"{path}.verification_spec", "list")
            if isinstance(todo["verification_spec"], list):
                for i, spec in enumerate(todo["verification_spec"]):
                    self._validate_verification_item(spec, f"{path}.verification_spec[{i}]")

        if "parallel" in todo:
            self._check_type(todo["parallel"], f"{path}.parallel", "boolean")

        if "parallelable_and_safe_evidence" in todo:
            if todo["parallelable_and_safe_evidence"] is not None:
                self._check_type(
                    todo["parallelable_and_safe_evidence"],
                    f"{path}.parallelable_and_safe_evidence",
                    "string",
                )

        if "acceptance_criteria" in todo:
            self._check_type(todo["acceptance_criteria"], f"{path}.acceptance_criteria", "list")
            if isinstance(todo["acceptance_criteria"], list):
                for i, criteria in enumerate(todo["acceptance_criteria"]):
                    self._validate_acceptance_criteria_item(criteria, f"{path}.acceptance_criteria[{i}]")

        if "children" in todo:
            self._check_type(todo["children"], f"{path}.children", "list")
            if isinstance(todo["children"], list):
                for i, child in enumerate(todo["children"]):
                    self._validate_todo(child, f"{path}.children[{i}]")

    def _validate_verification_item(self, item: Any, path: str) -> None:
        """Validate VerificationItem - v2.1."""
        if not isinstance(item, dict):
            self._check_type(item, path, "dict")
            return

        allowed_fields = {
            "id",
            "title",
            "description",
            "verified",
            "verified_at",
            "verification_evidence",
            "orchestrator_manually_verified",
            "manual_verification_evidence",
            "bash",
            "llm_judge",
            "deterministic_bash",
            "orchestrator_judge",
        }
        self._check_extra_fields(item, path, allowed_fields)

        self._validate_nested_required(
            item,
            path,
            ["id", "title", "description", "orchestrator_manually_verified", "manual_verification_evidence"],
        )

        # Type validation
        if "id" in item:
            self._check_type(item["id"], f"{path}.id", "string")
        if "title" in item:
            self._check_type(item["title"], f"{path}.title", "string")
        if "description" in item:
            self._check_type(item["description"], f"{path}.description", "string")
        if "verified" in item:
            self._check_type(item["verified"], f"{path}.verified", "boolean")
        if "verified_at" in item and item["verified_at"] is not None:
            self._check_type(item["verified_at"], f"{path}.verified_at", "string")
        if "verification_evidence" in item and item["verification_evidence"] is not None:
            self._check_type(item["verification_evidence"], f"{path}.verification_evidence", "string")
        if "orchestrator_manually_verified" in item:
            self._check_type(
                item["orchestrator_manually_verified"], f"{path}.orchestrator_manually_verified", "boolean"
            )
        if "manual_verification_evidence" in item:
            self._check_type(item["manual_verification_evidence"], f"{path}.manual_verification_evidence", "string")

        # Validate at least one of bash or llm_judge exists
        has_bash = "bash" in item and item["bash"]
        has_llm = "llm_judge" in item and item["llm_judge"]
        if not has_bash and not has_llm:
            self.errors.append(
                LintError(
                    location=path,
                    message="bash or llm_judge is required",
                    expected="at least one of bash or llm_judge",
                    actual="neither present",
                    suggestion="Add 'bash' or 'llm_judge' field",
                )
            )

        # Validate bash list
        if has_bash:
            self._validate_bash_list(item["bash"], f"{path}.bash")

        # Validate llm_judge list
        if has_llm:
            self._validate_llm_judge_list(item["llm_judge"], f"{path}.llm_judge")

        # Validate deterministic_bash list
        if "deterministic_bash" in item:
            self._check_type(item["deterministic_bash"], f"{path}.deterministic_bash", "list")
            if isinstance(item["deterministic_bash"], list):
                for i, det_bash in enumerate(item["deterministic_bash"]):
                    self._validate_deterministic_bash_item(det_bash, f"{path}.deterministic_bash[{i}]")

        # Validate orchestrator_judge list
        if "orchestrator_judge" in item:
            self._check_type(item["orchestrator_judge"], f"{path}.orchestrator_judge", "list")
            if isinstance(item["orchestrator_judge"], list):
                for i, orch_judge in enumerate(item["orchestrator_judge"]):
                    self._validate_orchestrator_judge_item(orch_judge, f"{path}.orchestrator_judge[{i}]")

    def _validate_bash_list(self, bash_list: Any, path: str) -> None:
        """Validate list of BashVerification."""
        if not isinstance(bash_list, list):
            self._check_type(bash_list, path, "list")
            return

        for i, bash in enumerate(bash_list):
            bash_path = f"{path}[{i}]"
            if not isinstance(bash, dict):
                self._check_type(bash, bash_path, "dict")
                continue

            allowed_fields = {"execute", "expected_stdout", "expected_stderr", "expected_exit_code", "notes"}
            self._check_extra_fields(bash, bash_path, allowed_fields)
            self._validate_nested_required(bash, bash_path, ["execute"])

            if "execute" in bash:
                self._check_type(bash["execute"], f"{bash_path}.execute", "string")
            if "expected_stdout" in bash and bash["expected_stdout"] is not None:
                self._check_type(bash["expected_stdout"], f"{bash_path}.expected_stdout", "string")
            if "expected_stderr" in bash and bash["expected_stderr"] is not None:
                self._check_type(bash["expected_stderr"], f"{bash_path}.expected_stderr", "string")
            if "expected_exit_code" in bash:
                self._check_type(bash["expected_exit_code"], f"{bash_path}.expected_exit_code", "int")
            if "notes" in bash and bash["notes"] is not None:
                self._check_type(bash["notes"], f"{bash_path}.notes", "string")

    def _validate_llm_judge_list(self, llm_list: Any, path: str) -> None:
        """Validate list of LLMJudgeVerification."""
        if not isinstance(llm_list, list):
            self._check_type(llm_list, path, "list")
            return

        for i, llm in enumerate(llm_list):
            llm_path = f"{path}[{i}]"
            if not isinstance(llm, dict):
                self._check_type(llm, llm_path, "dict")
                continue

            allowed_fields = {"by", "context_commands", "instruction"}
            self._check_extra_fields(llm, llm_path, allowed_fields)
            self._validate_nested_required(llm, llm_path, ["instruction"])

            # Validate by field (literal check)
            if "by" in llm:
                valid_by_values = ["orchestrator-agent", "external-agent"]
                if llm["by"] not in valid_by_values:
                    self.errors.append(
                        LintError(
                            location=f"{llm_path}.by",
                            message="Invalid value",
                            expected=f"one of {valid_by_values}",
                            actual=str(llm["by"]),
                            suggestion="Use 'orchestrator-agent' or 'external-agent'",
                        )
                    )

            if "context_commands" in llm:
                self._check_type(llm["context_commands"], f"{llm_path}.context_commands", "list")
                if isinstance(llm["context_commands"], list):
                    for j, cmd in enumerate(llm["context_commands"]):
                        self._check_type(cmd, f"{llm_path}.context_commands[{j}]", "string")

            if "instruction" in llm:
                self._check_type(llm["instruction"], f"{llm_path}.instruction", "string")

    def _validate_acceptance_criteria_item(self, item: Any, path: str) -> None:
        """Validate AcceptanceCriteriaItem."""
        if not isinstance(item, dict):
            self._check_type(item, path, "dict")
            return

        allowed_fields = {"id", "condition", "verified_at", "verification_evidence"}
        self._check_extra_fields(item, path, allowed_fields)
        self._validate_nested_required(item, path, ["id", "condition"])

        if "id" in item:
            self._check_type(item["id"], f"{path}.id", "string")
        if "condition" in item:
            self._check_type(item["condition"], f"{path}.condition", "string")
        if "verified_at" in item and item["verified_at"] is not None:
            self._check_type(item["verified_at"], f"{path}.verified_at", "string")
        if "verification_evidence" in item and item["verification_evidence"] is not None:
            self._check_type(item["verification_evidence"], f"{path}.verification_evidence", "string")

    def _validate_deterministic_bash_item(self, item: Any, path: str) -> None:
        """Validate DeterministicBashVerification."""
        if not isinstance(item, dict):
            self._check_type(item, path, "dict")
            return

        allowed_fields = {
            "description",
            "reason_why_it_is_deterministic_and_reliable",
            "execute",
            "expected_stdout",
            "expected_stderr",
            "expected_exit_code",
            "verified_at",
        }
        self._check_extra_fields(item, path, allowed_fields)
        self._validate_nested_required(
            item, path, ["description", "reason_why_it_is_deterministic_and_reliable", "execute"]
        )

        if "description" in item:
            self._check_type(item["description"], f"{path}.description", "string")
        if "reason_why_it_is_deterministic_and_reliable" in item:
            self._check_type(
                item["reason_why_it_is_deterministic_and_reliable"],
                f"{path}.reason_why_it_is_deterministic_and_reliable",
                "string",
            )
        if "execute" in item:
            self._check_type(item["execute"], f"{path}.execute", "string")
        if "expected_stdout" in item and item["expected_stdout"] is not None:
            self._check_type(item["expected_stdout"], f"{path}.expected_stdout", "string")
        if "expected_stderr" in item and item["expected_stderr"] is not None:
            self._check_type(item["expected_stderr"], f"{path}.expected_stderr", "string")
        if "expected_exit_code" in item:
            self._check_type(item["expected_exit_code"], f"{path}.expected_exit_code", "int")
        if "verified_at" in item and item["verified_at"] is not None:
            self._check_type(item["verified_at"], f"{path}.verified_at", "string")

    def _validate_orchestrator_judge_item(self, item: Any, path: str) -> None:
        """Validate OrchestratorJudgeVerification."""
        if not isinstance(item, dict):
            self._check_type(item, path, "dict")
            return

        allowed_fields = {"prompt", "verified_at", "verification_evidence"}
        self._check_extra_fields(item, path, allowed_fields)
        self._validate_nested_required(item, path, ["prompt"])

        if "prompt" in item:
            self._check_type(item["prompt"], f"{path}.prompt", "string")
        if "verified_at" in item and item["verified_at"] is not None:
            self._check_type(item["verified_at"], f"{path}.verified_at", "string")
        if "verification_evidence" in item and item["verification_evidence"] is not None:
            self._check_type(item["verification_evidence"], f"{path}.verification_evidence", "string")

    def _validate_success_vision(self, data: dict[str, Any]) -> None:
        """Validate success_vision section."""
        if "success_vision" not in data:
            return
        success_vision = data["success_vision"]

        if not isinstance(success_vision, dict):
            self._check_type(success_vision, "success_vision", "dict")
            return

        allowed_fields = {"user_perspective", "business_perspective", "technical_criteria"}
        self._check_extra_fields(success_vision, "success_vision", allowed_fields)

        # All fields are optional with defaults=[]
        if "user_perspective" in success_vision:
            self._check_type(success_vision["user_perspective"], "success_vision.user_perspective", "list")
            if isinstance(success_vision["user_perspective"], list):
                for i, scenario in enumerate(success_vision["user_perspective"]):
                    scenario_path = f"success_vision.user_perspective[{i}]"
                    if not isinstance(scenario, dict):
                        self._check_type(scenario, scenario_path, "dict")
                        continue
                    allowed_scenario_fields = {"scenario", "experience"}
                    self._check_extra_fields(scenario, scenario_path, allowed_scenario_fields)
                    self._validate_nested_required(scenario, scenario_path, ["scenario", "experience"])
                    if "scenario" in scenario:
                        self._check_type(scenario["scenario"], f"{scenario_path}.scenario", "string")
                    if "experience" in scenario:
                        self._check_type(scenario["experience"], f"{scenario_path}.experience", "string")

        if "business_perspective" in success_vision:
            self._check_type(success_vision["business_perspective"], "success_vision.business_perspective", "list")
            if isinstance(success_vision["business_perspective"], list):
                for i, metric in enumerate(success_vision["business_perspective"]):
                    metric_path = f"success_vision.business_perspective[{i}]"
                    if not isinstance(metric, dict):
                        self._check_type(metric, metric_path, "dict")
                        continue
                    allowed_metric_fields = {"metric", "target"}
                    self._check_extra_fields(metric, metric_path, allowed_metric_fields)
                    self._validate_nested_required(metric, metric_path, ["metric", "target"])
                    if "metric" in metric:
                        self._check_type(metric["metric"], f"{metric_path}.metric", "string")
                    if "target" in metric:
                        self._check_type(metric["target"], f"{metric_path}.target", "string")

        if "technical_criteria" in success_vision:
            self._check_type(success_vision["technical_criteria"], "success_vision.technical_criteria", "list")
            if isinstance(success_vision["technical_criteria"], list):
                for i, criterion in enumerate(success_vision["technical_criteria"]):
                    criterion_path = f"success_vision.technical_criteria[{i}]"
                    if not isinstance(criterion, dict):
                        self._check_type(criterion, criterion_path, "dict")
                        continue
                    allowed_criterion_fields = {"category", "criteria", "command", "expected"}
                    self._check_extra_fields(criterion, criterion_path, allowed_criterion_fields)
                    self._validate_nested_required(criterion, criterion_path, ["category", "criteria", "expected"])
                    if "category" in criterion:
                        self._check_type(criterion["category"], f"{criterion_path}.category", "string")
                    if "criteria" in criterion:
                        self._check_type(criterion["criteria"], f"{criterion_path}.criteria", "string")
                    if "command" in criterion and criterion["command"] is not None:
                        self._check_type(criterion["command"], f"{criterion_path}.command", "string")
                    if "expected" in criterion:
                        self._check_type(criterion["expected"], f"{criterion_path}.expected", "string")

    def _validate_final_verification(self, data: dict[str, Any]) -> None:
        """Validate final_verification section - v2.1 (flattened structure)."""
        if "final_verification" not in data:
            return
        final_verification = data["final_verification"]

        if not isinstance(final_verification, list):
            self._check_type(final_verification, "final_verification", "list")
            return

        # v2.1: flat list of FinalVerificationItem (each has category field)
        for i, item in enumerate(final_verification):
            item_path = f"final_verification[{i}]"
            if not isinstance(item, dict):
                self._check_type(item, item_path, "dict")
                continue

            allowed_item_fields = {
                "id",
                "title",
                "category",
                "description",
                "verified",
                "verified_at",
                "verification_evidence",
                "orchestrator_manually_verified",
                "manual_verification_evidence",
                "bash",
                "llm_judge",
            }
            self._check_extra_fields(item, item_path, allowed_item_fields)

            self._validate_nested_required(
                item,
                item_path,
                [
                    "id",
                    "title",
                    "category",
                    "description",
                    "orchestrator_manually_verified",
                    "manual_verification_evidence",
                ],
            )

            # Type validation
            if "id" in item:
                self._check_type(item["id"], f"{item_path}.id", "string")
            if "title" in item:
                self._check_type(item["title"], f"{item_path}.title", "string")
            if "category" in item:
                self._check_type(item["category"], f"{item_path}.category", "string")
            if "description" in item:
                self._check_type(item["description"], f"{item_path}.description", "string")
            if "verified" in item:
                self._check_type(item["verified"], f"{item_path}.verified", "boolean")
            if "verified_at" in item and item["verified_at"] is not None:
                self._check_type(item["verified_at"], f"{item_path}.verified_at", "string")
            if "verification_evidence" in item and item["verification_evidence"] is not None:
                self._check_type(item["verification_evidence"], f"{item_path}.verification_evidence", "string")
            if "orchestrator_manually_verified" in item:
                self._check_type(
                    item["orchestrator_manually_verified"], f"{item_path}.orchestrator_manually_verified", "boolean"
                )
            if "manual_verification_evidence" in item:
                self._check_type(
                    item["manual_verification_evidence"], f"{item_path}.manual_verification_evidence", "string"
                )

            # Validate at least one of bash or llm_judge exists
            has_bash = "bash" in item and item["bash"]
            has_llm = "llm_judge" in item and item["llm_judge"]
            if not has_bash and not has_llm:
                self.errors.append(
                    LintError(
                        location=item_path,
                        message="bash or llm_judge is required",
                        expected="at least one of bash or llm_judge",
                        actual="neither present",
                        suggestion="Add 'bash' or 'llm_judge' field",
                    )
                )

            # Validate bash list
            if has_bash:
                self._validate_bash_list(item["bash"], f"{item_path}.bash")

            # Validate llm_judge list
            if has_llm:
                self._validate_llm_judge_list(item["llm_judge"], f"{item_path}.llm_judge")

    def format_error(self, error: LintError) -> str:
        """Format error as string."""
        parts = [f"Error: {error.location} - {error.message}"]
        if error.expected:
            parts.append(f"Expected: {error.expected}")
        if error.actual:
            parts.append(f"Actual: {error.actual}")
        if error.suggestion:
            parts.append(f"Suggestion: {error.suggestion}")
        return ". ".join(parts)

    def validate_all(self, plan_document: PlanDocument, plan_path: Path) -> list[LintError]:
        """Validate all aspects of a plan document (structure, dependencies, references).

        Args:
            plan_document: v3.0 PlanDocument instance
            plan_path: Path to the plan file being validated

        Returns:
            List of lint errors categorized by type (empty if valid)
        """
        errors: list[LintError] = []

        dep_errors = self.validate_depends_on(plan_document, plan_path)
        errors.extend(
            [
                LintError(
                    location="depends_on",
                    message=err,
                    category="dependency",
                )
                for err in dep_errors
            ]
        )

        ref_errors = self.validate_references(plan_document)
        errors.extend(
            [
                LintError(
                    location="references",
                    message=err,
                    category="reference",
                )
                for err in ref_errors
            ]
        )

        return errors

    def _load_plan_sync(self, path: Path) -> PlanDocument:
        """Load plan file synchronously (for linter usage).

        Args:
            path: Path to YAML plan file

        Returns:
            PlanDocument instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid or version is not 3.0
        """
        if not path.exists():
            raise FileNotFoundError(f"Plan file not found: {path}")

        with open(path) as f:
            content = f.read()

        yaml = YAML()
        data = yaml.load(content)

        version = data.get("version")
        if not version:
            raise ValueError(f"Plan file {path} missing 'version' field")

        if version != "3.0":
            raise ValueError(f"Unsupported version: {version}. Only v3.0 supported.")

        return PlanDocument(**data)

    def _validate_external_dependency(
        self,
        dep_ref: str,
        source_plan_id: str,
        source_path: Path,
    ) -> str | None:
        """Validate external file dependency.

        Args:
            dep_ref: Dependency reference in 'file:backend.yaml#backend-api' format
            source_plan_id: ID of the plan that has this dependency
            source_path: Path to the source plan file

        Returns:
            Error message string if validation fails, None if successful
        """
        if not dep_ref.startswith("file:"):
            return f"External dependency '{dep_ref}' must start with 'file:' prefix"

        dep_ref_content = dep_ref[5:]

        if "#" not in dep_ref_content:
            return f"External dependency '{dep_ref}' is malformed. Expected format: 'file:path/to/plan.yaml#plan-id'"

        file_path_str, plan_id = dep_ref_content.split("#", 1)

        if not file_path_str:
            return f"External dependency '{dep_ref}' has empty file path"

        if not plan_id:
            return f"External dependency '{dep_ref}' has empty plan ID"

        external_file_path = Path(file_path_str)
        if not external_file_path.is_absolute():
            external_file_path = source_path.parent / external_file_path

        if not external_file_path.exists():
            return (
                f"Plan '{source_plan_id}' depends on external file '{external_file_path}' that does not exist. "
                f"Fix: Create the file or correct the path in depends_on"
            )

        try:
            external_plan_doc = self._load_plan_sync(external_file_path)
        except Exception as e:
            return (
                f"Plan '{source_plan_id}' depends on external file '{external_file_path}' "
                f"that could not be loaded: {e}"
            )

        external_plan_ids = {plan.id for plan in external_plan_doc.work_plans}
        if plan_id not in external_plan_ids:
            available = ", ".join(f"'{p}'" for p in external_plan_ids)
            return (
                f"Plan '{source_plan_id}' depends on plan '{plan_id}' in file '{external_file_path}' "
                f"that does not exist. Fix: Either create a plan with id '{plan_id}' in that file, "
                f"or change the dependency to one of: {available}"
            )

        return None

    def _validate_registry_dependency(
        self,
        plan_id: str,
        source_plan_id: str,
        plan_path: Path,
    ) -> str | None:
        """Validate registry-based dependency.

        Args:
            plan_id: Plan ID referenced (without 'registry:' prefix)
            source_plan_id: ID of the plan that has this dependency
            plan_path: Path to the source plan file

        Returns:
            Error message string if validation fails, None if successful
        """
        sisyphus_dir = self._find_sisyphus_dir(plan_path)
        if sisyphus_dir is None:
            return (
                f"Plan '{source_plan_id}' uses registry reference but .sisyphus directory not found. "
                f"Fix: Create .sisyphus/registry.yaml or use 'file:' reference instead"
            )

        registry_path = sisyphus_dir / "registry.yaml"
        if not registry_path.exists():
            return (
                f"Plan '{source_plan_id}' depends on 'registry:{plan_id}' "
                f"but registry file not found at {registry_path}. "
                f"Fix: Create registry.yaml file or use 'file:' reference instead"
            )

        try:
            registry = load_registry(registry_path)
            external_file_path, resolved_plan_id = resolve_registry_plan(plan_id, registry, sisyphus_dir.parent)
        except ValueError:
            available_plans = []
            try:
                registry = load_registry(registry_path)
                for entry in registry.plans:
                    available_plans.extend(entry.plans)
            except Exception:
                pass

            available_str = ", ".join(f"'{p}'" for p in available_plans) if available_plans else "none"
            return (
                f"Plan '{source_plan_id}' depends on 'registry:{plan_id}' that does not exist in registry. "
                f"Available plans: {available_str}. Fix: Add plan to registry.yaml or correct the dependency"
            )
        except Exception as e:
            return f"Plan '{source_plan_id}' depends on 'registry:{plan_id}' but registry could not be loaded: {e}"

        if not external_file_path.exists():
            return (
                f"Plan '{source_plan_id}' depends on 'registry:{plan_id}' "
                f"but referenced file {external_file_path} does not exist. "
                f"Fix: Create the file or update registry.yaml"
            )

        try:
            external_plan_doc = self._load_plan_sync(external_file_path)
        except Exception as e:
            return (
                f"Plan '{source_plan_id}' depends on 'registry:{plan_id}' "
                f"but file {external_file_path} could not be loaded: {e}"
            )

        external_plan_ids = {plan.id for plan in external_plan_doc.work_plans}
        if resolved_plan_id not in external_plan_ids:
            available = ", ".join(f"'{p}'" for p in external_plan_ids)
            return (
                f"Plan '{source_plan_id}' depends on 'registry:{plan_id}' "
                f"but plan '{resolved_plan_id}' does not exist in file {external_file_path}. "
                f"Available plans: {available}. Fix: Create the plan or update registry.yaml"
            )

        return None

    def _find_sisyphus_dir(self, plan_path: Path) -> Path | None:
        """Find .sisyphus directory by searching upward from plan_path.

        Args:
            plan_path: Path to the plan file

        Returns:
            Path to .sisyphus directory, or None if not found
        """
        current = plan_path.parent
        while current != current.parent:
            sisyphus_dir = current / ".sisyphus"
            if sisyphus_dir.exists() and sisyphus_dir.is_dir():
                return sisyphus_dir
            current = current.parent
        return None

    def _search_plan_in_sibling_files(self, plan_id: str, source_path: Path) -> bool:
        """Search for plan_id in sibling YAML files in .sisyphus/tasks directory.

        Args:
            plan_id: Plan ID to search for
            source_path: Path to the source plan file

        Returns:
            True if plan_id found in any sibling file, False otherwise
        """
        tasks_dir = source_path.parent
        if not tasks_dir.exists():
            return False

        for yaml_file in tasks_dir.glob("**/*.y*ml"):
            if yaml_file == source_path:
                continue

            try:
                plan_doc = self._load_plan_sync(yaml_file)
                plan_ids = {plan.id for plan in plan_doc.work_plans}
                if plan_id in plan_ids:
                    return True
            except Exception:
                continue

        return False

    @staticmethod
    def resolve_depends_on_path(depends_on: str, current_plan_path: Path) -> Path:
        """Resolve depends_on value to actual file path.

        Args:
            depends_on: depends_on value (filename, relative path, or absolute path)
            current_plan_path: Path to the current plan file

        Returns:
            Resolved absolute path

        Raises:
            ValueError: If path resolution fails
        """
        # 1. Absolute path (starts with /) → use as-is
        if depends_on.startswith("/"):
            return Path(depends_on)

        # 2. Relative path (./ or ../) → resolve from current plan file's parent
        if depends_on.startswith("./") or depends_on.startswith("../"):
            return (current_plan_path.parent / depends_on).resolve()

        # 3. Filename only (foobar.yml) → search in .sisyphus/tasks/ directory
        # Check if current_plan_path.parent is already .sisyphus/tasks/ directory
        if current_plan_path.parent.name == "tasks" and current_plan_path.parent.parent.name == ".sisyphus":
            # Already in .sisyphus/tasks/, just return parent / filename
            return (current_plan_path.parent / depends_on).resolve()
        else:
            # Not in .sisyphus/tasks/, need to add the path
            return (current_plan_path.parent / ".sisyphus/tasks" / depends_on).resolve()

    def _validate_file_path_depends_on(
        self, depends_on: str, plan_id: str, current_plan_path: Path, visited: set[Path] | None = None
    ) -> str | None:
        """Validate file path format depends_on.

        Args:
            depends_on: depends_on value to validate
            plan_id: ID of the plan that depends on this file
            current_plan_path: Path to the current plan file
            visited: Set of visited file paths (for cycle detection)

        Returns:
            Error message if validation fails, None if valid
        """
        if visited is None:
            visited = set()

        if depends_on.startswith("file:"):
            return None

        if depends_on.startswith("registry:"):
            return None

        if "/" not in depends_on and not depends_on.endswith((".yml", ".yaml")):
            return None

        try:
            resolved_path = self.resolve_depends_on_path(depends_on, current_plan_path)
        except Exception as error:
            return f"Plan '{plan_id}' depends on file path '{depends_on}': failed to resolve path - {error}"

        if not resolved_path.exists():
            return (
                f"Plan '{plan_id}' depends on file path '{depends_on}' which resolves to "
                f"'{resolved_path}': file does not exist"
            )

        if resolved_path in visited:
            cycle_path = " → ".join(str(p) for p in visited) + f" → {resolved_path}"
            return f"Circular file dependency detected: {cycle_path}"

        visited = visited | {resolved_path}

        try:
            referenced_plan_doc = self._load_plan_sync(resolved_path)
        except Exception as error:
            return f"Plan '{plan_id}' depends on file '{depends_on}': failed to load referenced file - {error}"

        for ref_plan in referenced_plan_doc.work_plans:
            for ref_dep in ref_plan.depends_on:
                error = self._validate_file_path_depends_on(ref_dep, ref_plan.id, resolved_path, visited)
                if error:
                    return error

        return None

    def validate_depends_on(self, plan_document: PlanDocument, plan_path: Path) -> list[str]:
        """Validate depends_on field for all work plans.

        Args:
            plan_document: v3.0 PlanDocument instance
            plan_path: Path to the plan file being validated

        Returns:
            List of error messages (empty if valid)
        """
        errors: list[str] = []

        plans = {plan.id: plan for plan in plan_document.work_plans}

        for plan in plan_document.work_plans:
            for dep_id in plan.depends_on:
                if dep_id.startswith("file:"):
                    error = self._validate_external_dependency(dep_id, plan.id, plan_path)
                    if error:
                        errors.append(error)
                elif dep_id.startswith("registry:"):
                    plan_id = dep_id[9:]
                    error = self._validate_registry_dependency(plan_id, plan.id, plan_path)
                    if error:
                        errors.append(error)
                elif dep_id not in plans:
                    found_in_file = self._search_plan_in_sibling_files(dep_id, plan_path)
                    if found_in_file:
                        continue

                    available = ", ".join(f"'{p}'" for p in plans.keys())
                    errors.append(
                        f"Plan '{plan.id}' depends on plan '{dep_id}' that does not exist. "
                        f"Fix: Either create a plan with id '{dep_id}', or change the dependency to one of: "
                        f"{available}"
                    )

                # File path validation
                file_error = self._validate_file_path_depends_on(dep_id, plan.id, plan_path)
                if file_error:
                    errors.append(file_error)
        graph = build_plan_graph(plans)

        cycles = detect_cycles(graph)
        for cycle in cycles:
            cycle_path = " → ".join(cycle + [cycle[0]])
            suggestion = (
                f"To fix: Remove '{cycle[-1]}' from the depends_on list of plan '{cycle[0]}', "
                f"or remove '{cycle[0]}' from the depends_on list of plan '{cycle[-1]}'"
            )
            errors.append(f"Circular dependency detected: {cycle_path}. {suggestion}")

        return errors

    def validate_references(self, plan_document: PlanDocument) -> list[str]:
        """Validate all references in v3.0 plan document.

        Args:
            plan_document: v3.0 PlanDocument instance

        Returns:
            List of error messages (empty if valid)
        """
        errors: list[str] = []

        for work_plan in plan_document.work_plans:
            ref_errors = ReferenceResolver.validate_references(work_plan)
            errors.extend(ref_errors)

        return errors
