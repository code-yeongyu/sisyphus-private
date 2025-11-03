# UserPromptSubmit Hook Reference

UserPromptSubmit hooks execute **BEFORE** Claude processes a user's prompt, allowing you to inject system context, add metadata, or block prompts.

## When to Use UserPromptSubmit

Use UserPromptSubmit hooks when you need to:

✅ **Inject system information** - Add git status, Python version, timestamps
✅ **Add environment context** - Virtual env status, project info
✅ **Inject user preferences** - Reminders, language settings
✅ **Block prompts** - Filter or prevent specific user inputs (rare)
✅ **Session initialization** - Add startup context

## How UserPromptSubmit Works

```
User Types Prompt → UserPromptSubmit Hook Runs → Claude Processes
                           ↓
                      Exit Code?
                     /          \
                Code 0          Code 2
                   ↓               ↓
            stdout → Claude   Prompt BLOCKED
           (inject context)   (prompt erased)
```

**Critical Understanding:**

- **Exit Code 0 + stdout**: stdout becomes context for Claude
- **Exit Code 2**: Prompt is BLOCKED and erased
- Hook runs on **EVERY** user prompt submission

## Input Structure

```python
from typing import TypedDict

class UserPromptSubmitInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str  # Always "UserPromptSubmit"
    user_prompt: str      # The prompt the user submitted
```

## Exit Code Behavior

### Exit Code 0 + stdout - Inject Context

```python
def main() -> None:
    """Main entry point."""
    try:
        data = json.loads(sys.stdin.read())

        # Generate system context
        system_info = generate_system_reminder()

        # stdout becomes context for Claude
        print(system_info)
        sys.exit(0)

    except Exception:
        sys.exit(0)
```

**Effect**: stdout content is injected as system-reminder context for Claude.

### Exit Code 2 - Block Prompt

```python
def main() -> None:
    """Main entry point."""
    try:
        data = json.loads(sys.stdin.read())
        user_prompt = data.get("user_prompt", "")

        if should_block_prompt(user_prompt):
            print("Prompt blocked: contains prohibited content", file=sys.stderr)
            sys.exit(2)  # Blocks and erases prompt

        sys.exit(0)

    except Exception:
        sys.exit(0)
```

**Effect**: Prompt is blocked and erased, stderr shown to Claude.

## Complete Example: System Reminder Injector

```python
#!/usr/bin/env python3
"""
UserPromptSubmit hook that injects system information.
Uses asyncio for concurrent subprocess execution.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import TypedDict


class UserPromptSubmitInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    user_prompt: str


def main() -> None:
    """Entry point that runs the async main function."""
    asyncio.run(async_main())


async def async_main() -> None:
    """Async main function that handles the hook logic."""
    try:
        json.load(sys.stdin)  # Parse input

        # Generate system reminder
        system_info = await generate_system_reminder()

        # stdout becomes context for Claude
        print(system_info)
        sys.exit(0)

    except Exception:
        sys.exit(0)


async def run_command(cmd: list[str], timeout: float = 1.0) -> tuple[str, int]:
    """Run a command asynchronously."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            async with asyncio.timeout(timeout):
                stdout, _ = await proc.communicate()
            return stdout.decode("utf-8").strip(), proc.returncode or 0
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return "", -1

    except Exception:
        return "", -1


async def get_git_info() -> dict[str, str | int]:
    """Get git repository information."""
    git_check = await run_command(["git", "rev-parse", "--git-dir"])
    if git_check[1] != 0:
        return {}

    # Run git commands concurrently
    async with asyncio.TaskGroup() as tg:
        branch_task = tg.create_task(run_command(["git", "branch", "--show-current"]))
        commit_task = tg.create_task(run_command(["git", "rev-parse", "--short", "HEAD"]))
        status_task = tg.create_task(run_command(["git", "status", "--porcelain"]))

    git_info = {}

    branch_stdout = branch_task.result()[0]
    git_info["branch"] = branch_stdout or "detached"

    commit_stdout = commit_task.result()[0]
    if commit_stdout:
        git_info["commit_hash"] = commit_stdout

    status_lines = status_task.result()[0].splitlines()
    unstaged_count = len([line for line in status_lines if line.strip()])
    if unstaged_count > 0:
        git_info["unstaged"] = unstaged_count

    return git_info


async def get_python_info() -> tuple[str | None, str | None]:
    """Get Python version and environment information."""
    result = await run_command(["python", "--version"])

    if result[1] != 0:
        return None, None

    python_version = result[0].replace("Python ", "")

    virtual_env = os.environ.get("VIRTUAL_ENV")
    if virtual_env:
        venv_name = os.path.basename(virtual_env)
        return python_version, f"venv: {venv_name}"
    else:
        return python_version, "global"


async def generate_system_reminder() -> str:
    """Generate the full system reminder text asynchronously."""
    lines: list[str] = []

    current_time = datetime.now().astimezone().isoformat()

    lines.extend([
        "",
        "[system-reminder]",
        f"CURRENT SYSTEM TIME: {current_time}",
    ])

    # Run git and Python info concurrently
    async with asyncio.TaskGroup() as tg:
        git_task = tg.create_task(get_git_info())
        python_task = tg.create_task(get_python_info())

    git_info = git_task.result()
    if git_info:
        if "branch" in git_info:
            lines.append(f"Git branch: {git_info['branch']}")

        if "commit_hash" in git_info:
            lines.append(f"Git commit: {git_info['commit_hash']}")

        if "unstaged" in git_info:
            lines.append(f"Git unstaged: {git_info['unstaged']} files")

    python_version, env_type = python_task.result()
    if python_version:
        lines.append(f"Python: {python_version} ({env_type})")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
```

## Common Mistakes

### ❌ MISTAKE 1: Printing context to stderr instead of stdout

**WRONG:**
```python
def main() -> None:
    system_info = generate_system_reminder()
    print(system_info, file=sys.stderr)  # ❌ WRONG - Goes to stderr
    sys.exit(0)
```

**CORRECT:**
```python
def main() -> None:
    system_info = generate_system_reminder()
    print(system_info)  # ✅ CORRECT - Goes to stdout
    sys.exit(0)
```

**Note**: UserPromptSubmit is the ONLY hook type where you print to stdout for normal operation!

### ❌ MISTAKE 2: Making hook too slow

**WRONG:**
```python
def generate_system_reminder() -> str:
    # Slow synchronous operations
    git_status = subprocess.run(["git", "status"], ...).stdout
    git_diff = subprocess.run(["git", "diff"], ...).stdout  # Sequential!
    git_log = subprocess.run(["git", "log"], ...).stdout    # Sequential!
    # Takes 3+ seconds...
```

**CORRECT:**
```python
async def generate_system_reminder() -> str:
    # Fast concurrent operations
    async with asyncio.TaskGroup() as tg:
        status_task = tg.create_task(run_command(["git", "status"]))
        diff_task = tg.create_task(run_command(["git", "diff"]))
        log_task = tg.create_task(run_command(["git", "log"]))
    # All run in parallel - much faster!
```

### ❌ MISTAKE 3: Not handling errors gracefully

**WRONG:**
```python
def main() -> None:
    data = json.loads(sys.stdin.read())  # ❌ Can crash
    system_info = generate_system_reminder()  # ❌ Can crash
    print(system_info)
    sys.exit(0)
```

**CORRECT:**
```python
def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
        system_info = generate_system_reminder()
        print(system_info)
        sys.exit(0)
    except Exception:
        # Exit gracefully - don't crash the prompt submission
        sys.exit(0)
```

## Best Practices

1. **Print to stdout, not stderr** - For normal context injection
2. **Keep it fast** - Use asyncio for I/O operations, complete in <500ms
3. **Handle errors gracefully** - Don't crash, exit 0 on errors
4. **Set timeouts** - Commands should timeout quickly (1-2 seconds max)
5. **Cache when possible** - Don't re-compute static info
6. **Be concise** - Don't inject too much context (increases token usage)
7. **Test performance** - Measure hook execution time

## Summary

UserPromptSubmit hooks inject context before Claude processes prompts:

✅ Exit code 0 + stdout = Inject context
✅ Exit code 2 = Block prompt (rare)
✅ Print to stdout (NOT stderr)
✅ Keep fast (<500ms)
✅ Use asyncio for I/O
✅ Runs on EVERY prompt

**Remember**: This hook runs on every user message, so keep it fast and lightweight!
