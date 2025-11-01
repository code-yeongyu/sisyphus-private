#!/usr/bin/env python3

import json
import sys
from pathlib import Path


def find_ai_todolist(cwd: str) -> Path | None:
    cwd_path = Path(cwd)
    if not cwd_path.is_dir():
        return None

    todolist = cwd_path / "ai-todolist.md"
    if todolist.is_file():
        return todolist

    for todolist in cwd_path.rglob("ai-todolist.md"):
        if todolist.is_file():
            return todolist

    return None


def is_execution_started(todolist_path: Path) -> bool:
    try:
        content = todolist_path.read_text()
        return "is_execution_started" in content.lower() and "true" in content.lower()
    except Exception:
        return False


def find_uncompleted_todos(cwd: str) -> list[str]:
    cwd_path = Path(cwd)
    uncompleted = []

    for todolist in cwd_path.rglob("ai-todolist.md"):
        if not todolist.is_file():
            continue

        try:
            lines = todolist.read_text().splitlines()
            for line in lines:
                if line.strip().startswith("- [ ]"):
                    uncompleted.append(line)
        except Exception:
            continue

    return uncompleted


def main() -> int:
    EXECUTOR = "executor"

    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print("Error: Invalid JSON input", file=sys.stderr)
        return 1

    subagent_type = input_data.get("tool_input", {}).get("subagent_type", "")

    if subagent_type == EXECUTOR:
        print("Skipping orchestrator hook: This is an executor agent", file=sys.stderr)
        return 0

    cwd = input_data.get("cwd", ".")
    todolist_path = find_ai_todolist(cwd)

    if not todolist_path:
        return 0

    if not is_execution_started(todolist_path):
        return 0

    uncompleted_todos = find_uncompleted_todos(cwd)

    print(
        f"""
{"=" * 40}
🎯 ORCHESTRATOR MODE ACTIVATED
{"=" * 40}

[ORCHESTRATION REMINDER]
After @agent-{EXECUTOR} returns, remember to:

**CRITICAL MINDSET: EXECUTOR AGENTS ARE LAZY, UNRELIABLE, AND DISHONEST**
- Executors WILL claim tasks are complete when they are NOT
- Executors WILL say tests pass when they FAIL or weren't even run
- Executors WILL report success to avoid doing more work
- NEVER TRUST executor reports at face value

YOUR VERIFICATION DUTIES (DO NOT SKIP ANY):
- Inspect: Read the ACTUAL code changes and confirm they FULLY meet requirements
- Review: MANUALLY verify their work matches the goal - assume they cut corners
- Verify: Verify test code: Naive test cases, redundant test cases, duplicated test cases.
  (Make sure test code should reflect the spec and also clear.)
  Run global tests (ex: pytest .) and lint(ex: ruff check .) and typecheck
  (ex: basedpyright .), consider executor as a liar. Use playwright mcp, tmux cli, python
- Check notepad.md: Verify executor documented work with REAL findings, not placeholders
- Commit: After verification, ensure all changes committed. Check git commit and status

And say to user in following format:
```
- Report: Completed X/Y tasks
- Report: Just finished: [task description]
- Report: Next up: [next task] or 'All tasks complete!'
- Report: Review status: [passed/failed] - Code review and verification completed
- Report: Validation status: [passed/failed with details]
  - What was verified: [specific commands run: pytest X, ruff check Y, basedpyright Z]
  - Evidence found: [actual test outputs, file changes confirmed, functionality tested]
  - Why confident: [concrete reasons why task is truly complete]
  - Acceptance criteria: [which criteria from todo were verified and how]
- Report: Cleanup status: [completed/not completed]
  - CRITICAL: All playwright browser sessions MUST be closed (use mcp__browser_close)
  - CRITICAL: All tmux sessions YOU CREATED MUST be terminated
  - Verify: Confirm all verification resources have been properly cleaned up
- Action: If tests/lint/work fail, mark as not success and summon new executor
```
""",
        file=sys.stderr,
    )

    print(
        f"""
[DELEGATION REMINDER]
DO NOT work directly - delegate tasks to @agent-{EXECUTOR} agent
Use: Task tool with subagent_type='{EXECUTOR}'
Follow /execute command pattern for systematic completion
Even if verification fails, summon executor again to fix the issues
Again, Use @agent-{EXECUTOR} to resolve any failed tests, lint errors, or incomplete work
Again, Use @agent-{EXECUTOR} to resolve any failed tests, lint errors, or incomplete work
IMPORTANT: Delegate ONE major task at a time to @agent-{EXECUTOR} - avoid overwhelming
Focus on completing one significant work item fully before moving to the next

사용자가 제시한, 그리고 계획서 속의 요구사항과 지시사항을 어떠한 게으름도 없이 정직하게 이행하세요.
작업해야 할 내용을 TODO 로 코드 내에 남기는것, 테스트가 온전하고 완전하게 통과하지 않았는데
넘어가는것은 엄격히 금지됩니다.
어떠한 경우에서도 작업 계획서 속 내용을 모두 구현해야하고, 테스트가 모두 통과해야 합니다 -
어떠한 이유도 허용되지 않습니다.
(일시적인 세팅 오류라도 넘어가서는 안되고 성공하는것을 명시적으로 확인하여야 합니다.)
""",
        file=sys.stderr,
    )

    if not uncompleted_todos:
        print("✅ All tasks in ai-todolist.md are completed!", file=sys.stderr)
        print("", file=sys.stderr)
        return 0
    print(
        f"""
{"=" * 40}
⚠️  UNCOMPLETED TASKS DETECTED
{"=" * 40}

[ERROR] Uncompleted TODO items found:
""",
        file=sys.stderr,
    )
    for todo in uncompleted_todos:
        print(todo, file=sys.stderr)
    print(
        """
[CRITICAL ERROR - INCOMPLETE TASKS]
This is an obvious error! All TODO items above are in incomplete state!
There should be no '- [ ]'. You must complete these TODOs perfectly and mark them as '- [x]'!
All tasks must be successfully completed and checked to resolve this error!
""",
        file=sys.stderr,
    )

    print(
        f"""
[IMPORTANT - CHECKBOX UPDATE]
If the executor agent has completed tasks but checkboxes remain unchecked:
YOU (the orchestrator) MUST manually update the checkboxes in ai-todolist.md
Use TodoWrite or Edit tools to mark completed tasks as [x]
Do NOT leave completed tasks unchecked - this blocks progress tracking

[CRITICAL - NEVER STOP]
TASKS ARE NOT COMPLETE IN @ai-todolist.md
YOU MUST CONTINUE WORKING UNTIL:
1. ALL checkboxes in ai-todolist.md are marked as [x]
2. AND you have RESPONSIBLY verified that ALL work is TRULY complete
3. AND the user's ENTIRE request has been fulfilled
DO NOT STOP - DO NOT GIVE UP - COMPLETE ALL TASKS WITH FULL RESPONSIBILITY
Keep delegating to @agent-{EXECUTOR} until EVERYTHING is done, not just checkboxes
Take OWNERSHIP - ensure REAL completion, not just checkbox completion
NEVEREVER STOP: NOW VERIFY A DELEGATE TASK TO @agent-{EXECUTOR}
""",
        file=sys.stderr,
    )

    return 2


if __name__ == "__main__":
    sys.exit(main())
