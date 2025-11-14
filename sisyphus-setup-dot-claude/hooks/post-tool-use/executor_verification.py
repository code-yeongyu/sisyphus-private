#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pydantic>=2.0", "anyio>=4.0", "ruamel.yaml>=0.18"]
# ///
# pyright: reportMissingImports=false

import json
import sys
from enum import Enum
from pathlib import Path
from typing import Any

import anyio
from pydantic import BaseModel
from ruamel.yaml import YAML

EXECUTOR_AGENT_NAME = "sisyphus-executor"


# Pydantic models (standalone - copied from sisyphus.core.plans.models)
class LLMJudgeBy(str, Enum):
    ORCHESTRATOR = "orchestrator-agent"
    EXTERNAL = "external-agent"


class BashVerification(BaseModel):
    execute: str
    expected_stdout: str | None = None
    expected_stderr: str | None = None
    expected_exit_code: int = 0
    notes: str | None = None


class LLMJudgeVerification(BaseModel):
    by: LLMJudgeBy = LLMJudgeBy.ORCHESTRATOR
    context_commands: list[str] = []
    instruction: str


class VerificationItem(BaseModel):
    id: str
    title: str
    description: str
    verified: bool = False
    verified_at: str | None = None
    verification_evidence: str | None = None
    orchestrator_manually_verified: bool
    manual_verification_evidence: str
    bash: list[BashVerification] = []
    llm_judge: list[LLMJudgeVerification] = []


class Todo(BaseModel):
    id: str
    title: str
    status: str
    verification_spec: list[VerificationItem] = []
    children: list["Todo"] | None = None


class WorkMode(BaseModel):
    current_task_id: str | None = None


class WorkPlan(BaseModel):
    id: str
    todos: list[Todo]
    work_mode: WorkMode


class PlanDocument(BaseModel):
    work_plans: list[WorkPlan]


async def load_plan_standalone(plan_path: Path) -> PlanDocument:
    """Load YAML plan without sisyphus imports."""
    yaml = YAML()
    yaml.preserve_quotes = True

    try:
        async with await anyio.open_file(plan_path, "r") as f:
            content = await f.read()
        data = yaml.load(content)
        return PlanDocument(**data)
    except Exception as e:
        raise RuntimeError(f"Failed to load YAML: {e}")


def find_todo_by_id_standalone(todos: list[Todo], target_id: str) -> Todo | None:
    """Find todo by ID (recursively search children)."""
    for todo in todos:
        if todo.id == target_id:
            return todo
        if todo.children:
            found = find_todo_by_id_standalone(todo.children, target_id)
            if found:
                return found
    return None


def find_next_unverified(verifications: list[VerificationItem]) -> VerificationItem | None:
    """Find first unverified item in list order."""
    for v in verifications:
        if not v.verified:
            return v
    return None


def determine_verification_type(verify_item: VerificationItem) -> tuple[str, VerificationItem]:
    """Determine verification type: bash, llm_orchestrator, or llm_external.

    Returns:
        ("bash", verify_item) or
        ("llm_orchestrator", verify_item) or
        ("llm_external", verify_item)
    """
    if verify_item.bash:
        return ("bash", verify_item)
    elif verify_item.llm_judge:
        llm_item = verify_item.llm_judge[0]
        if llm_item.by == LLMJudgeBy.ORCHESTRATOR:
            return ("llm_orchestrator", verify_item)
        else:  # LLMJudgeBy.EXTERNAL
            return ("llm_external", verify_item)
    else:
        raise ValueError(f"VerificationItem {verify_item.id} has neither bash nor llm_judge")


def format_common_header() -> str:
    """Generate common header for executor completion."""
    return """
========================================
🎯 EXECUTOR TASK COMPLETION DETECTED
========================================

[CRITICAL NOTICE]
The @agent-sisyphus-executor has just FINISHED execution.
Even if executor provided NO response, this means execution has TERMINATED.
You are NOT waiting for work completion - the work phase is ALREADY DONE.

YOUR MANDATORY DUTIES AS ORCHESTRATOR:
1. INSPECT the actual code changes - verify they match requirements
2. REVIEW the work output - ensure it's complete and correct
3. VERIFY through testing - run verification commands below
4. CHECK conventions - ensure code follows project standards

VERIFICATION IS MANDATORY. YOU CANNOT SKIP THIS.
"""


def format_bash_message(verify_item: VerificationItem) -> str:
    """Generate bash verification message."""
    bash_commands = "\n".join(f"  - {b.execute}" for b in verify_item.bash)

    return f"""
[BASH VERIFICATION REQUIRED]
Next verification: {verify_item.title}
Description: {verify_item.description}

AUTOMATED VERIFICATION AVAILABLE:
Run: sisyphus-speckit task verify bash

This will execute:
{bash_commands}

Expected: All commands exit with code 0
On success: verified=True is set automatically
On failure: Fix issues and retry

YOU MUST RUN THIS COMMAND BEFORE PROCEEDING.
"""


def format_llm_orchestrator_message(verify_item: VerificationItem) -> str:
    """Generate LLM orchestrator verification message."""
    llm_item = verify_item.llm_judge[0]
    instruction = llm_item.instruction

    return f"""
[LLM VERIFICATION REQUIRED - YOUR RESPONSIBILITY]
Next verification: {verify_item.title}
Description: {verify_item.description}

Verification by: ORCHESTRATOR (YOU)
Instruction: {instruction}

WHAT YOU MUST DO:
1. Follow the instruction above carefully
2. Perform the verification yourself
3. Mark as verified with evidence:
   sisyphus-speckit task verify llm-mark {verify_item.id} --evidence "<your findings>"

RESPOND IN THIS FORMAT TO CONFIRM YOU COMPLETED VERIFICATION:
```
Verification completed for {verify_item.title}.
Evidence: <detailed description of what you verified>
Command executed: sisyphus-speckit task verify llm-mark {verify_item.id} --evidence "..."
```

YOU CANNOT PROCEED WITHOUT COMPLETING THIS VERIFICATION.
"""


def format_llm_external_message(verify_item: VerificationItem) -> str:
    """Generate LLM external verification message."""
    llm_item = verify_item.llm_judge[0]
    instruction = llm_item.instruction

    return f"""
[LLM VERIFICATION REQUIRED - EXTERNAL AGENT]
Next verification: {verify_item.title}
Description: {verify_item.description}

Verification by: EXTERNAL AGENT (Claude Agent SDK)
Instruction: {instruction}

WHAT YOU MUST DO:
1. Invoke external agent with instruction above
2. Collect verification evidence from agent
3. Ensure agent provides:
   {verify_item.id}_VERIFIED = TRUE
   {verify_item.id}_VERIFICATION_EVIDENCE = "<evidence description>"
4. Mark as verified:
   sisyphus-speckit task verify llm-mark {verify_item.id} --evidence "<agent's evidence>"

YOU CANNOT PROCEED WITHOUT COMPLETING THIS VERIFICATION.
"""


def format_continue_message() -> str:
    """Generate continue work message."""
    return """
[ALL VERIFICATIONS COMPLETED]
✓ All verification items have been marked as verified.

YOU CAN NOW PROCEED TO NEXT TASK:
Run: sisyphus-speckit task continue

RESPOND IN THIS FORMAT AFTER RUNNING THE COMMAND:
```
sisyphus-speckit task continue executed successfully.
Next task information received and task has moved forward.
Now assigning executor agent for next task.
```

YOU MUST RUN 'sisyphus-speckit task continue' TO PROCEED.
WITHOUT EXECUTING THIS COMMAND, YOU CANNOT MOVE TO THE NEXT TASK.
"""


def main() -> int:
    try:
        input_data: dict[str, Any] = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        return 1

    tool_input: dict[str, Any] = input_data.get("tool_input", {})
    subagent_type: str = tool_input.get("subagent_type", "")
    _cwd: str = input_data.get("cwd", ".")
    _session_id: str = input_data.get("session_id", "")

    if subagent_type != EXECUTOR_AGENT_NAME:
        print(f"Skipping hook: Not executor agent (got: {subagent_type})", file=sys.stderr)
        return 0

    status_path = Path(_cwd) / ".sisyphus" / "status.json"
    if not status_path.exists():
        print("Error: No active plan (.sisyphus/status.json not found)", file=sys.stderr)
        return 1

    try:
        status_data: dict[str, Any] = json.loads(status_path.read_text())
        current_plan_data: dict[str, Any] | None = status_data.get("current_plan")
        if not current_plan_data:
            print("Error: No current_plan in status.json", file=sys.stderr)
            return 1

        current_plan_path: str | None = current_plan_data.get("plan_path")
        if not current_plan_path:
            print("Error: No plan_path in current_plan", file=sys.stderr)
            return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid status.json: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: Failed to read status.json: {e}", file=sys.stderr)
        return 1

    plan_path = Path(_cwd) / current_plan_path
    if not plan_path.exists():
        print(f"Error: Plan file not found: {plan_path}", file=sys.stderr)
        return 1

    try:
        plan_doc: PlanDocument = anyio.run(load_plan_standalone, plan_path)
    except Exception as e:
        print(f"Error: Failed to load YAML plan: {e}", file=sys.stderr)
        return 1

    if not plan_doc.work_plans:
        print("Error: No work_plans in YAML", file=sys.stderr)
        return 1

    work_plan: WorkPlan = plan_doc.work_plans[0]
    current_task_id: str | None = work_plan.work_mode.current_task_id

    if not current_task_id:
        print("No task in progress", file=sys.stderr)
        return 0

    current_task: Todo | None = find_todo_by_id_standalone(work_plan.todos, current_task_id)
    if current_task is None:
        print(f"Error: Current task not found: {current_task_id}", file=sys.stderr)
        return 1

    verifications: list[VerificationItem] = current_task.verification_spec
    if not verifications:
        print(format_common_header(), file=sys.stderr)
        print(format_continue_message(), file=sys.stderr)
        return 2

    next_unverified = find_next_unverified(verifications)
    if next_unverified is None:
        print(format_common_header(), file=sys.stderr)
        print(format_continue_message(), file=sys.stderr)
        return 2

    verify_type, verify_item = determine_verification_type(next_unverified)

    print(format_common_header(), file=sys.stderr)

    match verify_type:
        case "bash":
            print(format_bash_message(verify_item), file=sys.stderr)
        case "llm_orchestrator":
            print(format_llm_orchestrator_message(verify_item), file=sys.stderr)
        case "llm_external":
            print(format_llm_external_message(verify_item), file=sys.stderr)
        case _:
            pass

    return 2


if __name__ == "__main__":
    sys.exit(main())
