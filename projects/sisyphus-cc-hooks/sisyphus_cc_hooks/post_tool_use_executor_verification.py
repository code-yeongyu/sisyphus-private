#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["anyio>=4.0"]
# ///
# pyright: reportMissingImports=false

import json
import sys
from pathlib import Path
from typing import NotRequired, TypedDict

import anyio

EXECUTOR_AGENT_NAME = "sisyphus-executor"


class ToolInput(TypedDict):
    subagent_type: NotRequired[str]


class HookInput(TypedDict):
    tool_input: NotRequired[ToolInput]
    cwd: NotRequired[str]


def run_verify_status(cwd: str) -> str:
    try:
        result = anyio.run(
            anyio.run_process,
            ["sisyphus", "task", "verify", "status", "--cwd", cwd],
        )
        if result.returncode == 0:
            return result.stdout.decode("utf-8", errors="replace")
        else:
            return "[Verification status unavailable]"
    except Exception:
        return "[Verification status unavailable]"


def format_verification_guide() -> str:
    return """
VERIFICATION WORKFLOW
Follow this sequence to complete all verifications:

1. BASH AUTOMATED VERIFICATION
    Run automated bash tests:
    ```sh
    sisyphus task verify bash
    ```

  This command:
  - Executes all bash verification commands automatically
  - Sets verified=True if all exit codes are 0
  - Shows detailed output on failure

  On failure:
  - Review error messages
  - Fix issues
  - Re-run 'sisyphus task verify bash'
  - Or request sisyphus-executor to fix

2. LLM VERIFICATION (Orchestrator)
  Get your next LLM verification instructions:
    sisyphus task verify llm

  This shows:
  - Verification instruction
  - Context collection commands
  - Required evidence format

  Mark your verification as complete with detailed evidence:
    ```sh
    sisyphus task verify llm-mark <verify-id> --evidence "<detailed findings>"
    ```

  Evidence MUST include:
  - Specific items verified (functions, files, metrics)
  - How verification was done (tools used, commands run)
  - Results obtained (pass/fail, exact numbers)
  - Any unexpected findings

  Good evidence example:
    "All functions have type hints (ruff check passed),
     try-except blocks in 5 locations properly handle errors,
     pytest --cov shows 87% coverage (target: 80%),
     All 8 public functions have complete docstrings"

  Bad evidence examples:
    "Code looks good"
    "Tests passed"
    "Everything is fine"

3. MANUAL VERIFICATION
  Check manual verification requirements:
  ```sh
   sisyphus task verify manual
   ```

  Mark as complete:
    sisyphus task verify manual-mark <verify-id> --evidence "<very detailed evidence>"

  CRITICAL WARNING:
  DO NOT use "LLM judge passed" or "previous verification completed" as evidence.
  Manual verification requires INDEPENDENT, DIRECT observation and testing.

  Evidence MUST include:
  1. WHAT you verified (specific UI elements, pages, features)
  2. HOW you verified (browser version, environment, tools)
  3. WHAT the results were (exact behavior observed)
  4. ANY unexpected findings (screenshots, logs)

  Good evidence example:
    "Chrome 120.0 / macOS 14.2 environment:
     - Login page: Email/password fields render correctly at /login
     - Submit click: POST /api/auth/login request (DevTools Network tab)
     - Success: JWT token in LocalStorage 'auth_token' key
     - Error handling: Wrong password -> 'Authentication failed' in red
     - Redirect: Success -> /dashboard (verified URL change)
     - Token expiry: Auto-logout after 15 minutes (timed test)"

  Bad evidence examples:
    "UI test done"
    "Checked in browser"
    "Works fine"
    "LLM verification passed so this is good"

CHECK STATUS ANYTIME
View all verification status:
  sisyphus task verify status

Shows:
- Total progress (completed/total)
- Each verification item status
- Task breakdown

AFTER ALL VERIFICATIONS
Once all verifications show complete:
  sisyphus task continue

This will:
- Mark current task as completed
- Move to next pending task
- Start sisyphus-executor on next task

YOU MUST RUN 'sisyphus task continue' TO PROCEED.

[MANDATORY REPORTING FORMAT]
After completing EACH verification, report to user in this format:

```
- Verification Report: [bash/llm/manual] verification completed
- Verification Type: [automated bash/LLM judge/manual inspection]
- Commands Executed:
  - [exact commands you ran, e.g., sisyphus task verify bash]
  - [exact commands you ran, e.g., pytest projects/sisyphus-cli/]
  - [exact commands you ran, e.g., ruff check .]
- Evidence Collected:
  - What verified: [specific items: functions, files, test results, metrics]
  - How verified: [tools used, manual inspection steps, browser tests]
  - Results obtained: [pass/fail, exact numbers, error messages if any]
  - Unexpected findings: [any issues discovered, edge cases found]
- Acceptance Criteria: [which criteria from todo were verified and how]
- Status: [PASS/FAIL] - [brief reason]
```

After ALL verifications complete, report:
```
- Final Status: All verifications completed
- Task Status: Ready to continue (will run sisyphus task continue)
- Next Action: Moving to next task
```

[CRITICAL RULES - DO NOT VIOLATE]
1. NEVER skip verification steps - all must be completed
2. NEVER accept "looks good" or "seems fine" as evidence
3. NEVER trust executor's claims without independent verification
4. NEVER move forward with failing tests or lint errors
5. ALWAYS provide concrete evidence (command outputs, file contents, test results)
6. ALWAYS run 'sisyphus task continue' after all verifications pass

[IMPORTANT - NO SKIPPING]
The concept of "skipping verification" does NOT exist.
If verification fails, summon sisyphus-executor again to fix the issues.
Repeat until all verifications pass.
Again: The concept of "skipping verification" does NOT exist.

[CRITICAL - REMEMBER YOUR IDENTITY]
YOU ARE THE ORCHESTRATOR, NOT THE EXECUTOR.
Your role is to VERIFY and DELEGATE, NOT to implement or fix code yourself.

NEVER do direct work:
- DO NOT write code yourself
- DO NOT fix bugs yourself
- DO NOT implement features yourself
- DO NOT modify files yourself

ALWAYS delegate to sisyphus-executor:
- If verification fails: Summon sisyphus-executor to fix
- If tests fail: Summon sisyphus-executor to fix
- If lint errors: Summon sisyphus-executor to fix
- If anything incomplete: Summon sisyphus-executor to fix

Your ONLY job:
1. VERIFY executor's work thoroughly
2. DELEGATE fixes to executor when needed
3. REPEAT until all verifications pass

DO NOT FORGET: You are the orchestrator. Delegate, don't implement.
"""


def format_header() -> str:
    return """
EXECUTOR TASK COMPLETION DETECTED

[CRITICAL NOTICE]
The sisyphus-executor has just FINISHED execution.
This message appearing means the executor has REPORTED task completion.
Even if executor provided NO response, this means execution has TERMINATED.

[IMPORTANT - NO WAITING CONCEPT]
The concept of "waiting for executor to finish work" does NOT exist.
If this message is displayed, it means the executor has already reported completion.
The work phase is ALREADY DONE - you are NOT waiting for anything.
Proceed immediately to verification.
Again: There is NO concept of "waiting for executor completion".

YOUR MANDATORY DUTIES AS ORCHESTRATOR:
1. INSPECT the actual code changes - verify they match requirements
2. REVIEW the work output - ensure it's complete and correct
3. VERIFY through testing - run verification commands below
4. CHECK conventions - ensure code follows project standards

VERIFICATION IS MANDATORY. YOU CANNOT SKIP THIS.

[CRITICAL MINDSET: EXECUTOR AGENTS ARE LAZY AND UNRELIABLE]
- Executors WILL claim tasks complete when they are NOT
- Executors WILL say tests pass when they FAIL or weren't run
- Executors WILL report success to avoid more work
- NEVER TRUST executor reports at face value
- YOU must verify EVERYTHING independently
"""


def main() -> int:
    try:
        input_data: HookInput = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        return 1

    tool_input = input_data.get("tool_input", {})
    subagent_type = tool_input.get("subagent_type", "")
    cwd = input_data.get("cwd", ".")

    if subagent_type != EXECUTOR_AGENT_NAME:
        print(f"Skipping hook: Not executor agent (got: {subagent_type})", file=sys.stderr)
        return 0

    status_path = Path(cwd) / ".sisyphus" / "status.json"
    if not status_path.exists():
        print("No active plan found", file=sys.stderr)
        return 0

    verify_status_output = run_verify_status(cwd)

    message = format_header()
    message += "\n[CURRENT VERIFICATION STATUS]\n"
    message += verify_status_output
    message += "\n"
    message += format_verification_guide()

    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
