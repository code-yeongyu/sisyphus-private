# PostToolUse Hook Reference

PostToolUse hooks execute **AFTER** a tool completes successfully, allowing you to validate outputs, inject context, run formatters/linters, and provide feedback to Claude.

## Table of Contents

1. [When to Use PostToolUse](#when-to-use-posttooluse)
2. [How PostToolUse Works](#how-posttooluse-works)
3. [Input Structure](#input-structure)
4. [Exit Code Behavior](#exit-code-behavior)
5. [Common Use Cases](#common-use-cases)
6. [Complete Examples](#complete-examples)
7. [Common Mistakes](#common-mistakes)
8. [Best Practices](#best-practices)

## When to Use PostToolUse

Use PostToolUse hooks when you need to:

✅ **Validate outputs** - Check if tool produced correct results
✅ **Run linters/formatters** - Auto-format code after edits (ruff, black, prettier)
✅ **Inject context** - Add knowledge files or system information to Claude's context
✅ **Type checking** - Run type checkers (basedpyright, mypy) after code changes
✅ **Detect code smells** - Find patterns that need fixing (TypedDict total=False, Any types)
✅ **Log operations** - Track what tools were used

**Key characteristic**: PostToolUse runs **AFTER** the tool executes, so it **CANNOT PREVENT** the tool from running. It can only **INFORM** Claude about issues.

## How PostToolUse Works

```
User Request → Claude Creates Tool Call → Tool Executes Successfully
                                              ↓
                                      PostToolUse Hook Runs
                                              ↓
                                         Exit Code?
                                        /          \
                                   Code 0          Code 2
                                      ↓               ↓
                              Hook Success    stderr → Claude
                             (silent pass)    (inform about issues)
```

**CRITICAL Understanding:**

- **Exit Code 0**: Hook succeeded, no issues found, continue silently
- **Exit Code 2**: Hook found issues, send stderr to Claude as context
- **Tool already executed** - You CANNOT block the tool, only inform Claude

**⚠️ MOST COMMON MISTAKE**: Using exit code 0 when you want to inform Claude about issues!

## Input Structure

### PostToolUseInput TypedDict

```python
from typing import Any, TypedDict

class PostToolUseInput(TypedDict):
    session_id: str          # Unique session identifier
    tool_name: str           # Name of tool that executed (e.g., "Write", "Bash")
    transcript_path: str     # Path to transcript file
    cwd: str                 # Current working directory
    hook_event_name: str     # Always "PostToolUse"
    tool_input: dict[str, Any]      # Tool-specific input parameters
    tool_response: dict[str, Any]   # Tool's response/output
```

### Key Differences from PreToolUse

1. **tool_response field** - Contains the result of tool execution
2. **Tool already ran** - File is already written, command already executed
3. **Cannot block** - Can only inform Claude about what happened

### Input Example

```json
{
  "session_id": "abc123",
  "tool_name": "Write",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project",
  "hook_event_name": "PostToolUse",
  "tool_input": {
    "file_path": "/path/to/file.py",
    "content": "class MyDict(TypedDict, total=False):\n    name: str"
  },
  "tool_response": {
    "success": true,
    "type": "create",
    "filePath": "/path/to/file.py"
  }
}
```

### Accessing Tool Input and Response

```python
def process_hook_logic(data: PostToolUseInput) -> list[Issue]:
    """Process tool input and response."""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    tool_response = data.get("tool_response", {})

    # Check if tool succeeded
    success = tool_response.get("success")
    if success is None:
        # Fallback: check type field
        type_field = tool_response.get("type")
        success = type_field in ["create", "edit", "update"]

    if not success:
        return []  # Don't process failed tools

    # Type guard
    if not isinstance(tool_input, dict):
        return []

    # Extract file path
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return []

    # Read the file that was just written
    content = read_file_content(file_path)
    if not content:
        return []

    # Detect violations in the written content
    violations = detect_violations(content)

    return violations
```

## Exit Code Behavior

### Exit Code 0 - Success, No Issues

```python
def handle_findings(violations: list[Issue]) -> NoReturn:
    """Handle findings and exit."""
    if not violations:
        # No issues found - exit successfully
        print("[hook] Success: No issues found", file=sys.stderr)
        sys.exit(0)

    # ... handle violations
```

**Effect**: Hook succeeded silently, no message to Claude.

### Exit Code 2 - Inform Claude About Issues

```python
def handle_findings(violations: list[Issue]) -> NoReturn:
    """Handle findings and exit."""
    if violations:
        message = build_error_message(violations)
        print(message, file=sys.stderr)  # MUST use stderr
        sys.exit(2)  # Inform Claude (tool already ran)

    sys.exit(0)
```

**Effect**:
- Tool already executed successfully
- Message from stderr is sent to Claude as system-reminder
- Claude receives feedback and can fix issues in next action

**⚠️ CRITICAL MISTAKE TO AVOID**:

Many developers think "the operation succeeded (file was written), so I should exit with code 0". **THIS IS WRONG!**

If you want Claude to see your message and fix issues, **ALWAYS use exit code 2**, even though the tool succeeded.

## Common Use Cases

### 1. Context Injection Pattern (check_typeddict_total_false.py pattern)

This is the most common PostToolUse pattern: **detect issues in newly written code and inform Claude**.

```python
def process_tool_input(data: PostToolUseInput) -> list[Issue]:
    """Process and detect NEW violations only."""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    file_path = extract_file_path(data)
    if not file_path:
        return []

    # Get existing violations BEFORE this edit
    existing_violations = get_existing_violations(file_path, tool_name, tool_input)

    # Read current file content (AFTER edit)
    content = read_file_content(file_path)
    if not content:
        return []

    # Detect all violations in current content
    all_violations = detect_violations(content)

    # Filter to only NEW violations
    new_violations = []
    for violation in all_violations:
        violation_key = create_violation_key(violation)
        if violation_key not in existing_violations:
            new_violations.append(violation)

    return new_violations


def get_existing_violations(
    file_path: str,
    tool_name: str,
    tool_input: dict[str, Any],
) -> set[str]:
    """Get existing violations from old content to avoid duplicate warnings."""
    existing = set()

    if tool_name == "Edit":
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")

        if old_string and new_string:
            # Read current content
            current_content = read_file_content(file_path)
            if current_content and new_string in current_content:
                # Reconstruct pre-edit content
                pre_edit_content = current_content.replace(new_string, old_string, 1)

                # Detect violations in old content
                old_violations = detect_violations(pre_edit_content)
                for v in old_violations:
                    existing.add(create_violation_key(v))

    return existing
```

**Why this pattern is important:**

- Prevents duplicate warnings for existing issues
- Only notifies Claude about **new** problems introduced by this edit
- Allows gradual improvement of codebase without nagging about old issues

### 2. Run Linters/Formatters

```python
import subprocess

def run_ruff_check_and_format(file_path: str) -> tuple[str, int]:
    """Run ruff linter and formatter."""
    # Run lint check
    lint_result = subprocess.run(
        ["ruff", "check", "--fix", "--unsafe-fixes", file_path],
        capture_output=True,
        text=True,
        timeout=30.0,
    )

    # Run format
    format_result = subprocess.run(
        ["ruff", "format", file_path],
        capture_output=True,
        text=True,
        timeout=30.0,
    )

    output = lint_result.stdout + lint_result.stderr
    exit_code = lint_result.returncode or format_result.returncode

    return output, exit_code


def handle_findings(file_path: str) -> NoReturn:
    """Run linter and inform Claude if issues found."""
    output, exit_code = run_ruff_check_and_format(file_path)

    if exit_code == 0:
        print("[ruff] Success: No issues found", file=sys.stderr)
        sys.exit(0)

    # Issues found or file reformatted
    message = f"""RUFF LINTER/FORMATTER RESULTS

{output}

File has been auto-fixed and formatted.
REQUIRED ACTION: Use Read() to get the latest file content before any Edit() operations.
"""

    print(message, file=sys.stderr)
    sys.exit(2)  # Inform Claude
```

### 3. Inject Knowledge Files

```python
import hashlib
from pathlib import Path

def inject_knowledge_files(file_path: str, cwd: str, transcript_path: str) -> str | None:
    """Find and inject relevant knowledge files."""
    knowledge_files = find_knowledge_files(file_path, cwd)

    if not knowledge_files:
        return None

    messages = []

    for kf in knowledge_files:
        # Check if already in transcript
        identifier = f"[knowledge:{kf['path']}:{kf['hash']}]"
        if is_in_transcript(identifier, transcript_path):
            continue

        # Read and inject
        full_path = Path(cwd) / kf['path']
        content = full_path.read_text(encoding="utf-8")

        messages.append(f"{identifier}\n{content}")

    if messages:
        return "\n\n".join(messages)

    return None


def handle_findings(message: str | None) -> NoReturn:
    """Inject knowledge if found."""
    if not message:
        print("[knowledge] No new knowledge files to inject", file=sys.stderr)
        sys.exit(0)

    # Inject knowledge to Claude's context
    print(message, file=sys.stderr)
    sys.exit(2)  # Send to Claude
```

### 4. Type Checking

```python
import subprocess

def run_type_checker(file_path: str) -> tuple[str, int]:
    """Run basedpyright type checker."""
    result = subprocess.run(
        ["basedpyright", file_path],
        capture_output=True,
        text=True,
        timeout=30.0,
    )

    return result.stdout + result.stderr, result.returncode


def handle_findings(file_path: str) -> NoReturn:
    """Run type checker and inform Claude if issues found."""
    output, exit_code = run_type_checker(file_path)

    if exit_code == 0:
        print("[type-check] Success: No type errors", file=sys.stderr)
        sys.exit(0)

    # Type errors found
    message = f"""TYPE CHECKING ERRORS

{output}

Please fix the type errors above.
"""

    print(message, file=sys.stderr)
    sys.exit(2)  # Inform Claude
```

## Complete Examples

### Example 1: TypedDict total=False Detector (Real-world pattern)

This is based on the actual `check_typeddict_total_false.py` hook pattern.

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "ast-grep-py>=0.24.1",
# ]
# ///
"""
TypedDict total=False detector hook for Claude Code (PostToolUse).
Detects NEW TypedDict declarations with total=False and suggests using NotRequired.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Literal, NoReturn, TypedDict

import ast_grep_py as sg


class Config:
    """Configuration constants."""
    EXIT_CODE_INFORM_CLAUDE: int = 2  # NOT 0!


class TotalFalseIssue(TypedDict):
    type: Literal["class_definition", "function_call"]
    issue_description: str
    suggestion: str
    line: int
    class_name: str
    text: str


class WriteToolInput(TypedDict):
    file_path: str
    content: str


class EditToolInput(TypedDict):
    file_path: str
    old_string: str
    new_string: str


class PostToolUseInput(TypedDict):
    session_id: str
    tool_name: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    tool_input: WriteToolInput | EditToolInput | dict[str, Any]
    tool_response: dict[str, Any]


def main() -> None:
    """Main entry point."""
    hook_filename = Path(__file__).stem.replace("_", "-")
    print(f"\n[{hook_filename}]", file=sys.stderr)

    try:
        execute_hook_pipeline()
    except Exception:
        handle_hook_error()


def execute_hook_pipeline() -> None:
    """Execute the main hook logic pipeline."""
    data = parse_input()

    if not should_process(data):
        print("[hook] Skipping: Not applicable", file=sys.stderr)
        sys.exit(0)

    violations = process_tool_input(data)
    file_path = extract_file_path(data)

    handle_findings(violations, file_path)


def parse_input() -> PostToolUseInput:
    """Parse and validate stdin input."""
    input_raw = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(0)

    try:
        return json.loads(input_raw)
    except json.JSONDecodeError:
        sys.exit(0)


def should_process(data: PostToolUseInput) -> bool:
    """Determine if the input should be processed."""
    tool_input = data.get("tool_input", {})
    tool_response = data.get("tool_response", {})

    if not isinstance(tool_input, dict):
        return False

    # Check if tool succeeded
    success = tool_response.get("success")
    if success is None:
        type_field = tool_response.get("type")
        success = type_field in ["create", "edit", "update"]

    if not success:
        return False

    # Check file path
    file_path = tool_input.get("file_path", "")
    if not file_path or not file_path.endswith(".py"):
        return False

    # Check Python version
    if not check_python_version_311_or_higher():
        return False

    return True


def process_tool_input(data: PostToolUseInput) -> list[TotalFalseIssue]:
    """Process tool input and detect NEW violations only."""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if not isinstance(tool_input, dict):
        return []

    file_path = tool_input.get("file_path", "")

    # Get existing violations (before this edit)
    existing_violations = get_existing_violations(file_path, tool_name, tool_input)

    # Read current content (after edit)
    content = read_file_content(file_path)
    if not content:
        return []

    # Detect all violations
    all_violations = detect_total_false_violations(content)

    # Filter to NEW violations only
    new_violations = []
    for violation in all_violations:
        violation_key = create_violation_key(violation)
        if violation_key not in existing_violations:
            new_violations.append(violation)

    return new_violations


def detect_total_false_violations(code: str) -> list[TotalFalseIssue]:
    """Detect TypedDict total=False violations."""
    root = sg.SgRoot(code, "python")
    node = root.root()

    violations: list[TotalFalseIssue] = []

    # Find class definitions with total=False
    class_nodes = node.find_all(pattern="class $NAME($$$BASES): $BODY")

    for class_node in class_nodes:
        class_text = class_node.text()

        if "TypedDict" in class_text and "total=False" in class_text:
            class_name = extract_class_name(class_node)
            start = class_node.range().start

            violations.append(TotalFalseIssue(
                type="class_definition",
                issue_description=f"TypedDict '{class_name}' uses total=False",
                suggestion="Remove total=False and use NotRequired for optional fields",
                line=start.line + 1,
                class_name=class_name,
                text=class_text,
            ))

    return violations


def get_existing_violations(
    file_path: str,
    tool_name: str,
    tool_input: dict[str, Any],
) -> set[str]:
    """Get existing violations to avoid duplicate warnings."""
    existing = set()

    if tool_name == "Edit":
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")

        if old_string and new_string:
            current_content = read_file_content(file_path)
            if current_content and new_string in current_content:
                # Reconstruct pre-edit content
                pre_edit_content = current_content.replace(new_string, old_string, 1)
                old_violations = detect_total_false_violations(pre_edit_content)

                for v in old_violations:
                    existing.add(create_violation_key(v))

    return existing


def create_violation_key(violation: TotalFalseIssue) -> str:
    """Create unique key for violation."""
    return f"{violation['class_name']}:{violation['line']}:{violation['type']}"


def handle_findings(violations: list[TotalFalseIssue], file_path: str) -> NoReturn:
    """Handle detected violations."""
    if not violations:
        print("[hook] Success: No TypedDict total=False violations found", file=sys.stderr)
        sys.exit(0)

    message = build_error_message(violations, file_path)
    print(message, file=sys.stderr)  # stderr, NOT stdout!
    sys.exit(Config.EXIT_CODE_INFORM_CLAUDE)  # Exit 2, NOT 0!


def build_error_message(violations: list[TotalFalseIssue], file_path: str) -> str:
    """Build error message."""
    msg_parts = [
        "TYPEDDICT total=False DETECTED - MODERNIZATION OPPORTUNITY",
        "",
        f"File: {file_path}",
        f"Found {len(violations)} TypedDict declaration(s) using total=False.",
        "",
        "Python 3.11+ introduces NotRequired, which provides a cleaner way",
        "to mark individual fields as optional in TypedDict.",
        "",
        "Using NotRequired is preferred because:",
        "- It makes the intent clearer at the field level",
        "- It follows modern Python typing best practices",
        "- It provides better IDE support and type checking",
        "",
        "Detected violations:",
    ]

    for i, v in enumerate(violations, 1):
        msg_parts.append(f"\n[{i}] Line {v['line']}: {v['issue_description']}")
        msg_parts.append(f"    Suggestion: {v['suggestion']}")

    msg_parts.append("\nFIX IMMEDIATELY: Convert TypedDict declarations to use NotRequired.")
    msg_parts.append("This is the modern Python way for Python 3.11+.")

    return "\n".join(msg_parts)


def extract_class_name(class_node: sg.SgNode) -> str:
    """Extract class name from class node."""
    name_match = class_node.get_match("NAME")
    if name_match:
        return name_match.text()

    class_text = class_node.text()
    match = re.match(r"class\s+(\w+)", class_text)
    if match:
        return match.group(1)

    return "UnknownClass"


def extract_file_path(data: PostToolUseInput) -> str:
    """Extract file path from input."""
    tool_input = data.get("tool_input", {})
    if isinstance(tool_input, dict):
        return tool_input.get("file_path", "")
    return ""


def read_file_content(file_path: str) -> str | None:
    """Read file content safely."""
    if not file_path or not Path(file_path).exists():
        return None

    try:
        return Path(file_path).read_text(encoding="utf-8")
    except Exception:
        return None


def check_python_version_311_or_higher() -> bool:
    """Check if Python 3.11+ is being used."""
    import sys as sys_module

    if sys_module.version_info >= (3, 11):
        return True

    # Check pyproject.toml
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        try:
            content = pyproject_path.read_text()
            match = re.search(r'requires-python\s*=\s*"[^"]*3\.(\d+)', content)
            if match and int(match.group(1)) >= 11:
                return True
        except Exception:
            pass

    return False


def handle_hook_error() -> NoReturn:
    """Handle errors gracefully."""
    print("[hook] Skipping: Unexpected error occurred", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
```

### Example 2: Ruff Linter and Formatter

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Ruff linter and formatter hook for Claude Code (PostToolUse).
Runs ruff check and format on Python files after edits.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn, TypedDict


class Config:
    """Configuration constants."""
    EXIT_CODE_INFORM_CLAUDE: int = 2
    VENV_RUFF_PATHS: list[Path] = [Path(".venv/bin/ruff"), Path("venv/bin/ruff")]


class PostToolUseInput(TypedDict):
    session_id: str
    tool_name: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    tool_input: dict[str, Any]
    tool_response: dict[str, Any]


@dataclass
class RuffResults:
    lint_output: str
    lint_exit_code: int
    format_output: str
    format_exit_code: int


def main() -> None:
    """Main entry point."""
    hook_filename = Path(__file__).stem.replace("_", "-")
    print(f"\n[{hook_filename}]", file=sys.stderr)

    input_data = sys.stdin.read()
    file_path = get_target_file_path(input_data)

    if not file_path:
        print("[ruff] Skipping: No valid Python file", file=sys.stderr)
        sys.exit(0)

    ruff_path = find_ruff_executable()
    if not ruff_path:
        print("[ruff] Skipping: ruff not found", file=sys.stderr)
        sys.exit(0)

    results = execute_ruff_operations(ruff_path, file_path)
    handle_results_and_exit(results)


def get_target_file_path(input_data: str) -> str | None:
    """Extract Python file path from input."""
    if not input_data:
        return None

    try:
        data: PostToolUseInput = json.loads(input_data)
        tool_input = data["tool_input"]
    except Exception:
        return None

    file_path = tool_input.get("file_path", "")
    if not file_path or not file_path.endswith(".py"):
        return None

    return file_path if Path(file_path).exists() else None


def find_ruff_executable() -> str | None:
    """Find ruff in venv or system PATH."""
    for venv_path in Config.VENV_RUFF_PATHS:
        if venv_path.exists():
            return str(venv_path.absolute())

    return shutil.which("ruff")


def execute_ruff_operations(ruff_path: str, file_path: str) -> RuffResults:
    """Run ruff lint and format."""
    lint_result = subprocess.run(
        [ruff_path, "check", "--fix", "--unsafe-fixes", file_path],
        capture_output=True,
        text=True,
        timeout=30.0,
    )

    format_result = subprocess.run(
        [ruff_path, "format", file_path],
        capture_output=True,
        text=True,
        timeout=30.0,
    )

    return RuffResults(
        lint_output=lint_result.stdout + lint_result.stderr,
        lint_exit_code=lint_result.returncode,
        format_output=format_result.stdout + format_result.stderr,
        format_exit_code=format_result.returncode,
    )


def handle_results_and_exit(results: RuffResults) -> NoReturn:
    """Handle ruff results and exit."""
    if results.lint_exit_code == 0 and results.format_exit_code == 0:
        print("[ruff] Success: No issues found", file=sys.stderr)
        sys.exit(0)

    message_parts = []

    if results.lint_exit_code != 0 and results.lint_output:
        message_parts.append("\n<ruff-lint>\n")
        message_parts.append(results.lint_output)
        message_parts.append("\n</ruff-lint>\n")

    if results.format_exit_code != 0:
        message_parts.append("\nFile has been auto-formatted by ruff.\n")
        message_parts.append("REQUIRED ACTION: Use Read() to get the latest file content before any Edit() operations.\n")

    if message_parts:
        print("".join(message_parts), file=sys.stderr)
        sys.exit(Config.EXIT_CODE_INFORM_CLAUDE)  # Exit 2 to inform Claude

    sys.exit(0)


if __name__ == "__main__":
    main()
```

## Common Mistakes

### ❌ MISTAKE 1: Using exit code 0 when you want to inform Claude (MOST COMMON!)

**WRONG:**
```python
def handle_findings(violations: list[Issue]) -> NoReturn:
    """Handle violations."""
    if violations:
        # Found violations - tool already succeeded, so exit 0... RIGHT?
        message = build_error_message(violations)
        print(message, file=sys.stderr)
        sys.exit(0)  # ❌ WRONG - Claude will NEVER see this message!

    sys.exit(0)
```

**WHY THIS IS WRONG:**

PostToolUse developers often think: "The tool succeeded (file was written), so I should return success (exit 0)."

**THIS IS INCORRECT LOGIC!**

- Exit code 0 = "Hook has nothing to say to Claude"
- Exit code 2 = "Hook wants to inform Claude" (even if tool succeeded)

**CORRECT:**
```python
def handle_findings(violations: list[Issue]) -> NoReturn:
    """Handle violations."""
    if violations:
        # Found violations - INFORM CLAUDE
        message = build_error_message(violations)
        print(message, file=sys.stderr)
        sys.exit(2)  # ✅ CORRECT - Claude will see this message and can fix it

    sys.exit(0)  # No violations - silent success
```

### ❌ MISTAKE 2: Thinking PostToolUse can block the tool

**WRONG MINDSET:**
```python
def handle_findings(violations: list[Issue]) -> NoReturn:
    """Handle violations."""
    if violations:
        # Block the tool from executing!
        sys.exit(2)  # ❌ WRONG - Tool already executed!
```

**CORRECT MINDSET:**
```python
def handle_findings(violations: list[Issue]) -> NoReturn:
    """Handle violations."""
    if violations:
        # Tool already executed. Inform Claude so it can fix the issue.
        message = build_error_message(violations)
        print(message, file=sys.stderr)
        sys.exit(2)  # ✅ CORRECT - Informs Claude to fix in next action
```

**Remember**: PostToolUse runs **AFTER** the tool. You cannot prevent the tool from running. You can only inform Claude about what happened.

### ❌ MISTAKE 3: Not filtering out existing violations

**WRONG:**
```python
def process_tool_input(data: PostToolUseInput) -> list[Issue]:
    """Process tool input."""
    file_path = extract_file_path(data)
    content = read_file_content(file_path)

    # Detect ALL violations (including pre-existing ones)
    return detect_violations(content)  # ❌ WRONG - Will nag about old issues
```

**CORRECT:**
```python
def process_tool_input(data: PostToolUseInput) -> list[Issue]:
    """Process tool input."""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    file_path = extract_file_path(data)

    # Get existing violations BEFORE this edit
    existing = get_existing_violations(file_path, tool_name, tool_input)

    # Get current violations AFTER this edit
    content = read_file_content(file_path)
    all_violations = detect_violations(content)

    # Return only NEW violations
    new_violations = []
    for v in all_violations:
        if create_violation_key(v) not in existing:
            new_violations.append(v)

    return new_violations  # ✅ CORRECT - Only new issues
```

### ❌ MISTAKE 4: Printing to stdout instead of stderr

**WRONG:**
```python
def handle_findings(violations: list[Issue]) -> NoReturn:
    """Handle violations."""
    if violations:
        message = build_error_message(violations)
        print(message)  # ❌ WRONG - Goes to stdout
        sys.exit(2)
```

**CORRECT:**
```python
def handle_findings(violations: list[Issue]) -> NoReturn:
    """Handle violations."""
    if violations:
        message = build_error_message(violations)
        print(message, file=sys.stderr)  # ✅ CORRECT - Goes to stderr
        sys.exit(2)
```

### ❌ MISTAKE 5: Not checking if tool succeeded

**WRONG:**
```python
def should_process(data: PostToolUseInput) -> bool:
    """Check if should process."""
    # Assuming tool always succeeded
    return True  # ❌ WRONG - Should check tool_response
```

**CORRECT:**
```python
def should_process(data: PostToolUseInput) -> bool:
    """Check if should process."""
    tool_response = data.get("tool_response", {})

    # Check success field
    success = tool_response.get("success")

    # Fallback: check type field
    if success is None:
        type_field = tool_response.get("type")
        success = type_field in ["create", "edit", "update"]

    return success  # ✅ CORRECT - Only process if tool succeeded
```

## Best Practices

1. **ALWAYS use exit code 2 to inform Claude** - Exit code 0 means "nothing to say"
2. **ALWAYS print to stderr** - Messages must go to stderr, not stdout
3. **Filter out existing violations** - Only report NEW issues introduced by this edit
4. **Check tool_response for success** - Don't process failed tools
5. **Validate tool_input is a dict** - Use isinstance() before accessing
6. **Handle errors gracefully** - Exit with code 0 on unexpected errors
7. **Be specific in messages** - Tell Claude exactly what's wrong and how to fix
8. **Keep hooks fast** - Should complete in <1 second
9. **Use python-tool-writer** - Always generate hooks with proper PEP 723 metadata
10. **Print hook name** - Help users debug which hook ran

## Integration with python-tool-writer

**ALWAYS** use the `python-tool-writer` skill when creating PostToolUse hooks:

```
Use python-tool-writer to create a PostToolUse hook script named "detect_total_false.py" that:

Purpose: Detect TypedDict declarations with total=False in Python files

Behavior:
1. Triggers on Write/Edit tools for .py files
2. Checks if tool succeeded via tool_response
3. Reads the file that was just written/edited
4. Detects TypedDict with total=False using ast-grep-py
5. Filters out existing violations (only report NEW ones)
6. If NEW violations found: print message to stderr and exit code 2
7. If no violations: exit code 0

TypedDicts:
- PostToolUseInput (session_id, tool_name, tool_input, tool_response, etc.)
- WriteToolInput (file_path, content)
- EditToolInput (file_path, old_string, new_string)
- TotalFalseIssue (class_name, line, suggestion)

Dependencies:
- ast-grep-py>=0.24.1

CRITICAL: Exit code 2 to INFORM Claude (not exit 0), even though tool succeeded.
Print to stderr, not stdout.
```

## Summary

PostToolUse hooks run **AFTER** tools execute to validate and inform Claude:

✅ Exit code 2 = INFORM Claude (most common case)
✅ Exit code 0 = Silent success, nothing to say
✅ Print to stderr, not stdout
✅ Tool already ran - cannot block, only inform
✅ Filter to NEW violations only
✅ Use python-tool-writer skill
✅ Check tool_response for success

**MOST CRITICAL POINT**: Don't confuse "tool succeeded" with "hook succeeded". Even if the tool succeeded, use exit code 2 if you want Claude to see your message!

**Remember**: PostToolUse is your chance to **inform** Claude about issues after operations complete. Use exit code 2 liberally when you have something to say!
