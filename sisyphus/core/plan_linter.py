"""YAML work plan linter for schema validation."""

# ruff: noqa: ANN401
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from sisyphus.core.graph.dependencies import build_plan_graph, detect_cycles
from sisyphus.core.plans.models import PlanDocument
from sisyphus.core.plans.references import ReferenceResolver
from sisyphus.utils.plan_types import (
    RetrievalType,
    TodoStatus,
)


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


class PlanLinter:
    """YAML work plan linter."""

    def __init__(self, schema_doc: dict[str, Any]) -> None:
        """Initialize with plan schema definition.

        Args:
            schema_doc: Schema정보 (나중에 확장용, 현재는 Pydantic 모델 기반)
        """
        self.errors: list[LintError] = []

    def lint(self, yaml_data: dict[str, Any]) -> list[LintError]:
        """Lint YAML data and return all errors.

        Args:
            yaml_data: Parsed YAML dictionary

        Returns:
            List of lint errors (empty if valid)
        """
        self.errors = []
        self._validate_root_fields(yaml_data)
        self._validate_metadata(yaml_data)
        self._validate_user_request(yaml_data)
        self._validate_objectives(yaml_data)
        self._validate_background(yaml_data)
        self._validate_required_background(yaml_data)
        self._validate_status(yaml_data)
        self._validate_workflow(yaml_data)
        self._validate_todos(yaml_data)
        self._validate_success_vision(yaml_data)
        self._validate_final_verification(yaml_data)
        self._validate_reference_integrity(yaml_data)
        return self.errors

    def _validate_root_fields(self, data: dict[str, Any]) -> None:
        """Validate WorkPlan root required fields.

        Note: WorkPlan root allows extra fields (model_config extra='allow' in plan_types.py:293)
        for Pydantic compatibility, but nested objects (Metadata, Status, etc.) are strict.
        PlanLinter is independent of Pydantic → validates strictly at all levels for LLM usage.
        """
        allowed_root = {
            "metadata",
            "user_request",
            "objectives",
            "background",
            "required_background",
            "status",
            "workflow",
            "todos",
            "success_vision",
            "final_verification",
        }
        # DECISION: Linter validates strictly even at root level
        # (WorkPlan's extra='allow' is for Pydantic tolerance, not YAML lint tolerance)
        self._check_extra_fields(data, "", allowed_root)

        required_fields = [
            "metadata",
            "user_request",
            "objectives",
            "background",
            "required_background",
            "status",
            "workflow",
            "todos",
            "success_vision",
            "final_verification",
        ]
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
        """Validate metadata section."""
        if "metadata" not in data:
            return  # Already caught by root validation
        metadata = data["metadata"]

        if not isinstance(metadata, dict):
            self._check_type(metadata, "metadata", "dict")
            return

        allowed_fields = {"created_at", "updated_at", "format_version"}
        self._check_extra_fields(metadata, "metadata", allowed_fields)

        self._validate_nested_required(metadata, "metadata", ["created_at", "updated_at"])

        if "created_at" in metadata:
            self._check_type(metadata["created_at"], "metadata.created_at", "string")
        if "updated_at" in metadata:
            self._check_type(metadata["updated_at"], "metadata.updated_at", "string")
        if "format_version" in metadata:
            self._check_type(metadata["format_version"], "metadata.format_version", "string")

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
            if isinstance(req_bg["references"], list):
                for i, ref in enumerate(req_bg["references"]):
                    self._validate_reference_spec(ref, f"required_background.references[{i}]")

    def _validate_reference_spec(self, ref: Any, path: str) -> None:
        """Validate ReferenceItem (discriminated union) - v2.1."""
        if not isinstance(ref, dict):
            self._check_type(ref, path, "dict")
            return

        # Validate discriminated union type field (v2.1: pointer, file, url, markdown)
        valid_types = ["pointer", "file", "url", "markdown"]
        if not self._validate_discriminated_union_type(ref, path, valid_types):
            return

        ref_type = ref.get("type")
        if ref_type == "pointer":
            allowed_fields = {"type", "ref_id", "notes"}
            self._check_extra_fields(ref, path, allowed_fields)
            self._validate_nested_required(ref, path, ["ref_id"])
            if "ref_id" in ref:
                self._check_type(ref["ref_id"], f"{path}.ref_id", "string")
            if "notes" in ref and ref["notes"] is not None:
                self._check_type(ref["notes"], f"{path}.notes", "string")
        elif ref_type == "file":
            allowed_fields = {"type", "path", "description", "retrieval", "notes", "id"}
            self._check_extra_fields(ref, path, allowed_fields)
            self._validate_nested_required(ref, path, ["path", "description"])
            if "path" in ref:
                self._check_type(ref["path"], f"{path}.path", "string")
            if "description" in ref:
                self._check_type(ref["description"], f"{path}.description", "string")
            if "notes" in ref and ref["notes"] is not None:
                self._check_type(ref["notes"], f"{path}.notes", "string")
        elif ref_type == "url":
            allowed_fields = {"type", "url", "description", "retrieval", "notes", "id"}
            self._check_extra_fields(ref, path, allowed_fields)
            self._validate_nested_required(ref, path, ["url", "description"])
            if "url" in ref:
                self._check_type(ref["url"], f"{path}.url", "string")
            if "description" in ref:
                self._check_type(ref["description"], f"{path}.description", "string")
            if "notes" in ref and ref["notes"] is not None:
                self._check_type(ref["notes"], f"{path}.notes", "string")
        elif ref_type == "markdown":
            allowed_fields = {"type", "description", "content", "id"}
            self._check_extra_fields(ref, path, allowed_fields)
            self._validate_nested_required(ref, path, ["description", "content"])
            if "description" in ref:
                self._check_type(ref["description"], f"{path}.description", "string")
            if "content" in ref:
                self._check_type(ref["content"], f"{path}.content", "string")

        # Validate type literal (no enum in v2.1, just check valid_types)
        if ref_type and ref_type not in valid_types:
            self.errors.append(
                LintError(
                    location=f"{path}.type",
                    message="Invalid type value",
                    expected=f"one of {valid_types}",
                    actual=str(ref_type),
                    suggestion=f"Change to one of: {', '.join(valid_types)}",
                )
            )

        # Validate retrieval if present
        if "retrieval" in ref and ref["retrieval"] is not None:
            self._validate_retrieval_spec(ref["retrieval"], f"{path}.retrieval")

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

        allowed_fields = {"execution", "work_mode", "progress", "current_work"}
        self._check_extra_fields(status, "status", allowed_fields)

        self._validate_nested_required(status, "status", ["execution", "work_mode", "progress", "current_work"])

        # Validate execution
        if "execution" in status:
            exec_data = status["execution"]
            if not isinstance(exec_data, dict):
                self._check_type(exec_data, "status.execution", "dict")
            else:
                allowed_exec_fields = {"started", "completed", "started_at", "completed_at"}
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

        # Validate progress
        if "progress" in status:
            progress = status["progress"]
            if not isinstance(progress, dict):
                self._check_type(progress, "status.progress", "dict")
            else:
                allowed_prog_fields = {"total_tasks", "completed", "in_progress", "pending"}
                self._check_extra_fields(progress, "status.progress", allowed_prog_fields)
                self._validate_nested_required(
                    progress, "status.progress", ["total_tasks", "completed", "in_progress", "pending"]
                )
                if "total_tasks" in progress:
                    self._check_type(progress["total_tasks"], "status.progress.total_tasks", "int")
                if "completed" in progress:
                    self._check_type(progress["completed"], "status.progress.completed", "int")
                if "in_progress" in progress:
                    self._check_type(progress["in_progress"], "status.progress.in_progress", "int")
                if "pending" in progress:
                    self._check_type(progress["pending"], "status.progress.pending", "int")

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

        for i, todo in enumerate(todos):
            self._validate_todo(todo, f"todos[{i}]")

    def _validate_todo(self, todo: Any, path: str) -> None:
        """Validate single todo item (recursive)."""
        if not isinstance(todo, dict):
            self._check_type(todo, path, "dict")
            return

        allowed_fields = {
            "id",
            "title",
            "status",
            "parallel_group",
            "created_at",
            "updated_at",
            "status_changed_at",
            "references",
            "details",
            "verification_spec",
            "children",
            "parallel_note",
        }
        self._check_extra_fields(todo, path, allowed_fields)

        self._validate_nested_required(todo, path, ["id", "title", "status", "created_at", "updated_at"])

        # Validate id (accepts both string and int, pattern validation)
        if "id" in todo:
            todo_id = str(todo["id"])
            pattern = r"^\d+(\.\d+)*$"
            self._check_pattern(
                todo_id,
                f"{path}.id",
                pattern,
                "numeric ID with optional dots (e.g., '1', '1.1', '1.1.1')",
            )

        # Validate title
        if "title" in todo:
            self._check_type(todo["title"], f"{path}.title", "string")

        # Validate status (TodoStatus enum)
        if "status" in todo:
            self._check_enum(todo["status"], f"{path}.status", TodoStatus)

        # Validate parallel_group
        if "parallel_group" in todo and todo["parallel_group"] is not None:
            self._check_type(todo["parallel_group"], f"{path}.parallel_group", "int")

        # Validate timestamps
        if "created_at" in todo:
            self._check_type(todo["created_at"], f"{path}.created_at", "string")
        if "updated_at" in todo:
            self._check_type(todo["updated_at"], f"{path}.updated_at", "string")
        if "status_changed_at" in todo and todo["status_changed_at"] is not None:
            self._check_type(todo["status_changed_at"], f"{path}.status_changed_at", "string")

        # Validate references (v2.1: all references are ReferenceItem with type field)
        if "references" in todo:
            self._check_type(todo["references"], f"{path}.references", "list")
            if isinstance(todo["references"], list):
                for i, ref in enumerate(todo["references"]):
                    ref_path = f"{path}.references[{i}]"
                    # All references are ReferenceItem (discriminated union with type field)
                    self._validate_reference_spec(ref, ref_path)

        # Validate details
        if "details" in todo:
            self._check_type(todo["details"], f"{path}.details", "dict")

        # Validate verification_spec
        if "verification_spec" in todo:
            self._check_type(todo["verification_spec"], f"{path}.verification_spec", "list")
            if isinstance(todo["verification_spec"], list):
                for i, spec in enumerate(todo["verification_spec"]):
                    self._validate_verification_item(spec, f"{path}.verification_spec[{i}]")

        # Validate children (recursive)
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

    def _collect_reference_ids(self, data: dict[str, Any]) -> set[str]:
        """Collect all reference IDs from required_background.references."""
        ref_ids = set()
        if "required_background" in data:
            bg = data["required_background"]
            if isinstance(bg, dict) and "references" in bg:
                if isinstance(bg["references"], list):
                    for ref in bg["references"]:
                        if isinstance(ref, dict) and "id" in ref:
                            ref_ids.add(ref["id"])
        return ref_ids

    def _validate_reference_integrity(self, data: dict[str, Any]) -> None:
        """Validate all ReferencePointer.ref_id exist in required_background - v2.1."""
        # 1. Collect all defined reference IDs
        valid_ref_ids = self._collect_reference_ids(data)

        # 2. Check all todos for ReferencePointer
        if "todos" in data and isinstance(data["todos"], list):
            self._check_todos_ref_integrity(data["todos"], "todos", valid_ref_ids)

    def _check_todos_ref_integrity(self, todos: list[Any], path: str, valid_ref_ids: set[str]) -> None:
        """Recursively check todos for invalid ref_id - v2.1."""
        for i, todo in enumerate(todos):
            if not isinstance(todo, dict):
                continue

            todo_path = f"{path}[{i}]"

            # Check references
            if "references" in todo and isinstance(todo["references"], list):
                for j, ref in enumerate(todo["references"]):
                    if not isinstance(ref, dict):
                        continue

                    ref_path = f"{todo_path}.references[{j}]"
                    # v2.1: ReferencePointer has type="pointer" and ref_id
                    if ref.get("type") == "pointer" and "ref_id" in ref:
                        ref_id = ref["ref_id"]
                        if isinstance(ref_id, str) and ref_id not in valid_ref_ids:
                            expected_msg = (
                                f"one of {sorted(valid_ref_ids)}" if valid_ref_ids else "no references defined"
                            )
                            suggestion_msg = (
                                f"Add reference with id='{ref_id}' to required_background.references or fix typo"
                            )
                            self.errors.append(
                                LintError(
                                    location=f"{ref_path}.ref_id",
                                    message="Reference ID not found",
                                    expected=expected_msg,
                                    actual=ref_id,
                                    suggestion=suggestion_msg,
                                )
                            )

            # Recursive children check
            if "children" in todo and isinstance(todo["children"], list):
                self._check_todos_ref_integrity(todo["children"], f"{todo_path}.children", valid_ref_ids)

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
                if dep_id not in plans:
                    errors.append(f"Plan '{plan.id}' depends on '{dep_id}' which does not exist in this document")

        graph = build_plan_graph(plans)

        cycles = detect_cycles(graph)
        for cycle in cycles:
            cycle_path = " → ".join(cycle)
            errors.append(f"Circular dependency detected: {cycle_path}")

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

            for ref_item in work_plan.references:
                if ref_item.inline and len(ref_item.inline) > 500:
                    errors.append(
                        f"WorkPlan '{work_plan.name}': inline reference too long "
                        f"({len(ref_item.inline)} chars, recommend < 500)"
                    )

        return errors
