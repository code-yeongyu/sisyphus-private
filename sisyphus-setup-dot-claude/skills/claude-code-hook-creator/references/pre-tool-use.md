# PreToolUse Hook Reference

PreToolUse hooks execute **BEFORE** a tool runs, allowing you to validate inputs, enforce policies, and **BLOCK** dangerous operations.

## Table of Contents

1. [When to Use PreToolUse](#when-to-use-pretooluse)
2. [How PreToolUse Works](#how-pretooluse-works)
3. [Input Structure](#input-structure)
4. [Exit Code Behavior](#exit-code-behavior)
5. [Common Use Cases](#common-use-cases)
6. [Complete Examples](#complete-examples)
7. [Common Mistakes](#common-mistakes)
8. [Best Practices](#best-practices)

## When to Use PreToolUse

Use PreToolUse hooks when you need to:

✅ **Block dangerous operations** - Prevent risky commands before execution
✅ **Validate tool inputs** - Check parameters before tool runs
✅ **Enforce coding policies** - Block code that violates standards
✅ **Command substitution** - Suggest better alternatives (grep → rg)
✅ **Security checks** - Prevent unsafe file operations
✅ **Library enforcement** - Block deprecated libraries

**Key characteristic**: PreToolUse can **PREVENT** the tool from executing.

## How PreToolUse Works

```
User Request → Claude Creates Tool Call → PreToolUse Hook Runs
                                              ↓
                                         Exit Code?
                                        /          \
                                   Code 0          Code 2
                                      ↓               ↓
                              Tool Executes     TOOL BLOCKED
                                                stderr → Claude
```

**Critical Understanding:**

- **Exit Code 0**: Tool proceeds normally
- **Exit Code 2**: Tool is **BLOCKED**, stderr message sent to Claude
- **Other codes**: Non-blocking error, stderr shown to user

## Input Structure

### PreToolUseInput TypedDict

```python
from typing import Any, TypedDict

class PreToolUseInput(TypedDict):
    session_id: str          # Unique session identifier
    tool_name: str           # Name of tool about to execute (e.g., "Write", "Bash")
    transcript_path: str     # Path to transcript file
    cwd: str                 # Current working directory
    hook_event_name: str     # Always "PreToolUse"
    tool_input: dict[str, Any]  # Tool-specific input parameters
```

### Input Example

```json
{
  "session_id": "abc123",
  "tool_name": "Write",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project",
  "hook_event_name": "PreToolUse",
  "tool_input": {
    "file_path": "/path/to/file.py",
    "content": "def foo() -> Any:\n    pass"
  }
}
```

### Accessing Tool Input

```python
def process_hook_logic(data: PreToolUseInput) -> list[Issue]:
    """Process tool input based on tool type."""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Type guard
    if not isinstance(tool_input, dict):
        return []

    # Tool-specific processing
    if tool_name == "Write":
        file_path = tool_input.get("file_path", "")
        content = tool_input.get("content", "")
        # Validate content...

    elif tool_name == "Edit":
        file_path = tool_input.get("file_path", "")
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        # Validate new_string...

    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        # Validate command...

    return violations
```

## Exit Code Behavior

### Exit Code 0 - Allow Tool Execution

```python
def handle_findings(violations: list[Issue]) -> NoReturn:
    """Handle findings and exit."""
    if not violations:
        # No issues found - allow tool to proceed
        sys.exit(0)

    # ... handle violations
```

**Effect**: Tool executes normally, hook succeeded silently.

### Exit Code 2 - Block Tool Execution

```python
def handle_findings(violations: list[Issue]) -> NoReturn:
    """Handle findings and exit."""
    if violations:
        message = build_error_message(violations)
        print(message, file=sys.stderr)  # MUST use stderr
        sys.exit(2)  # BLOCKS the tool

    sys.exit(0)
```

**Effect**:
- Tool is **BLOCKED** and will **NOT execute**
- Message from stderr is sent to Claude as system-reminder
- Claude receives feedback and can adjust

**⚠️ CRITICAL**: Always print to `stderr`, never `stdout`!

## Common Use Cases

### 1. Block Specific Commands

Block deprecated or dangerous commands:

```python
import re

def should_block_command(command: str) -> bool:
    """Check if command should be blocked."""
    # Block grep, suggest rg
    if re.search(r"\bgrep\b", command):
        return True

    # Block rm -rf
    if "rm" in command and "-rf" in command:
        return True

    return False
```

### 2. Validate Code Quality

Block code with quality issues:

```python
import ast_grep_py as sg

def detect_any_return_type(code: str) -> list[Issue]:
    """Detect functions returning Any."""
    root = sg.SgRoot(code, "python")
    node = root.root()

    violations = []

    # Find all functions with -> Any
    func_nodes = node.find_all(pattern="def $FUNC($$$ARGS) -> $RETURN: $$$BODY")

    for func_node in func_nodes:
        return_match = func_node.get_match("RETURN")
        if return_match and "Any" in return_match.text():
            violations.append({
                "function": func_node.get_match("FUNC").text(),
                "issue": "Returns Any type"
            })

    return violations
```

### 3. Enforce Library Usage

Block deprecated libraries when better alternatives exist:

```python
def has_better_library(old_lib: str, new_lib: str) -> bool:
    """Check if project uses the better library."""
    # Check pyproject.toml
    if has_dependency(new_lib):
        return True
    return False


def detect_deprecated_import(content: str, old_lib: str) -> bool:
    """Detect import of deprecated library."""
    import_patterns = [
        f"import {old_lib}",
        f"from {old_lib} import",
    ]

    for pattern in import_patterns:
        if pattern in content:
            return True

    return False
```

### 4. Validate File Paths

Block writes to dangerous locations:

```python
from pathlib import Path

DANGEROUS_PATHS = [
    "/etc",
    "/usr",
    "/bin",
    "/sbin",
    "/System",
]

def is_dangerous_path(file_path: str) -> bool:
    """Check if path is dangerous to write to."""
    try:
        path = Path(file_path).resolve()

        for dangerous in DANGEROUS_PATHS:
            if str(path).startswith(dangerous):
                return True

        return False
    except Exception:
        return True  # Err on side of caution
```

## Complete Examples

### Example 1: Block grep Command

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Grep blocker hook for Claude Code (PreToolUse).
Blocks Bash commands using grep and suggests ripgrep (rg).
"""

from __future__ import annotations

import json
import re
import sys
from typing import NoReturn, NotRequired, TypedDict


class Config:
    """Configuration constants."""
    EXIT_CODE_BLOCK_TOOL: int = 2
    GREP_PATTERN: re.Pattern[str] = re.compile(
        r"\b(?:grep|egrep|fgrep)\b",
        re.IGNORECASE,
    )


class BashToolInput(TypedDict):
    command: str
    description: NotRequired[str]
    timeout: NotRequired[int]
    run_in_background: NotRequired[bool]


class PreToolUseInput(TypedDict):
    session_id: str
    tool_name: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    tool_input: BashToolInput | dict[str, str]


def main() -> None:
    """Main entry point."""
    try:
        execute_hook_pipeline()
    except Exception:
        handle_hook_error()


def execute_hook_pipeline() -> None:
    """Execute the main hook logic pipeline."""
    data = parse_input()

    if not should_process(data):
        sys.exit(0)

    command = extract_command(data)
    has_grep = bool(command) and detect_grep_usage(command)

    handle_findings(has_grep)


def parse_input() -> PreToolUseInput:
    """Parse and validate stdin input."""
    input_raw = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(0)

    try:
        parsed_data: PreToolUseInput = json.loads(input_raw)
        return parsed_data
    except json.JSONDecodeError:
        sys.exit(0)


def should_process(data: PreToolUseInput) -> bool:
    """Determine if the input should be processed."""
    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input")

    return (
        tool_name == "Bash" and
        isinstance(tool_input, dict) and
        bool(tool_input.get("command"))
    )


def extract_command(data: PreToolUseInput) -> str:
    """Extract command from input data."""
    tool_input = data.get("tool_input", {})
    if isinstance(tool_input, dict):
        return tool_input.get("command", "")
    return ""


def detect_grep_usage(command: str) -> bool:
    """Detect if the command contains grep."""
    return bool(Config.GREP_PATTERN.search(command))


def handle_findings(has_grep: bool) -> NoReturn:
    """Handle detected grep usage and exit appropriately."""
    if not has_grep:
        sys.exit(0)

    message = """GREP BLOCKED

Great choice using grep! However, please use rg (ripgrep) instead.
Continue with what you were doing, but use rg instead of grep.

Note: ripgrep uses extended regex by default, so:
- Use `|` for OR (not `\\|` like in basic grep)
- No need to escape special characters like grep -E
- Example: `rg "pattern1|pattern2"` instead of `grep "pattern1\\|pattern2"`"""

    print(message, file=sys.stderr)
    sys.exit(Config.EXIT_CODE_BLOCK_TOOL)


def handle_hook_error() -> NoReturn:
    """Handle errors in hook execution."""
    sys.exit(0)


if __name__ == "__main__":
    main()
```

### Example 2: Block TypedDict total=False (from @hooks/post-tool-use/check_typeddict_total_false.py pattern)

**⚠️ IMPORTANT**: This is a **PreToolUse** pattern for validation hooks that block operations based on code content.

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "ast-grep-py>=0.24.1",
# ]
# ///
"""
TypedDict total=False blocker hook for Claude Code (PreToolUse).
Blocks Write/Edit operations that introduce TypedDict with total=False.
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
    EXIT_CODE_BLOCK_TOOL: int = 2


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


class PreToolUseInput(TypedDict):
    session_id: str
    tool_name: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    tool_input: WriteToolInput | EditToolInput | dict[str, Any]


def main() -> None:
    """Main entry point."""
    try:
        execute_hook_pipeline()
    except Exception:
        handle_hook_error()


def execute_hook_pipeline() -> None:
    """Execute the main hook logic pipeline."""
    data = parse_input()

    if not should_process(data):
        sys.exit(0)

    violations = process_tool_input(data)
    file_path = extract_file_path(data)

    handle_findings(violations, file_path)


def parse_input() -> PreToolUseInput:
    """Parse and validate stdin input."""
    input_raw = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(0)

    try:
        return json.loads(input_raw)
    except json.JSONDecodeError:
        sys.exit(0)


def should_process(data: PreToolUseInput) -> bool:
    """Determine if the input should be processed."""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name not in ["Write", "Edit"]:
        return False

    if not isinstance(tool_input, dict):
        return False

    file_path = tool_input.get("file_path", "")
    if not file_path or not file_path.endswith(".py"):
        return False

    # Check Python 3.11+
    if not check_python_version_311_or_higher():
        return False

    return True


def process_tool_input(data: PreToolUseInput) -> list[TotalFalseIssue]:
    """Process tool input and detect violations."""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if not isinstance(tool_input, dict):
        return []

    content = ""

    if tool_name == "Write":
        content = tool_input.get("content", "")
    elif tool_name == "Edit":
        content = tool_input.get("new_string", "")

    if not content:
        return []

    return detect_total_false_violations(content)


def detect_total_false_violations(code: str) -> list[TotalFalseIssue]:
    """Detect TypedDict total=False violations."""
    root = sg.SgRoot(code, "python")
    node = root.root()

    violations: list[TotalFalseIssue] = []

    # Pattern 1: class MyDict(TypedDict, total=False)
    class_nodes = node.find_all(pattern="class $NAME($$$BASES): $BODY")

    for class_node in class_nodes:
        class_text = class_node.text()

        if "TypedDict" in class_text and "total=False" in class_text:
            class_name = extract_class_name(class_node)
            start = class_node.range().start

            violations.append(TotalFalseIssue(
                type="class_definition",
                issue_description=f"TypedDict '{class_name}' uses total=False",
                suggestion=f"Remove total=False and use NotRequired for optional fields",
                line=start.line + 1,
                class_name=class_name,
                text=class_text,
            ))

    return violations


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


def handle_findings(violations: list[TotalFalseIssue], file_path: str) -> NoReturn:
    """Handle detected violations."""
    if not violations:
        sys.exit(0)

    message = build_error_message(violations, file_path)
    print(message, file=sys.stderr)  # stderr, NOT stdout!
    sys.exit(Config.EXIT_CODE_BLOCK_TOOL)  # Exit 2, NOT 0!


def build_error_message(violations: list[TotalFalseIssue], file_path: str) -> str:
    """Build error message."""
    msg_parts = [
        "TYPEDDICT total=False DETECTED - OPERATION BLOCKED",
        "=" * 60,
        f"\nFile: {file_path}",
        f"Found {len(violations)} violation(s).\n",
    ]

    for i, v in enumerate(violations, 1):
        msg_parts.append(f"\n[{i}] Line {v['line']}: {v['issue_description']}")
        msg_parts.append(f"    Suggestion: {v['suggestion']}\n")

    msg_parts.append("\nFIX REQUIRED: Convert TypedDict declarations to use NotRequired.")
    msg_parts.append("This follows Python 3.11+ best practices.")

    return "\n".join(msg_parts)


def extract_file_path(data: PreToolUseInput) -> str:
    """Extract file path from input."""
    tool_input = data.get("tool_input", {})
    if isinstance(tool_input, dict):
        return tool_input.get("file_path", "")
    return ""


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
    sys.exit(0)


if __name__ == "__main__":
    main()
```

## Common Mistakes

### ❌ MISTAKE 1: Using exit code 0 when you want to block

**WRONG:**
```python
def handle_findings(violations: list[Issue]) -> NoReturn:
    """Handle violations."""
    if violations:
        # Found violations, but exiting with 0
        message = build_error_message(violations)
        print(message, file=sys.stderr)
        sys.exit(0)  # ❌ WRONG - Tool will execute anyway!

    sys.exit(0)
```

**CORRECT:**
```python
def handle_findings(violations: list[Issue]) -> NoReturn:
    """Handle violations."""
    if violations:
        # Found violations - BLOCK the tool
        message = build_error_message(violations)
        print(message, file=sys.stderr)
        sys.exit(2)  # ✅ CORRECT - Blocks tool execution

    sys.exit(0)  # No violations - allow tool
```

### ❌ MISTAKE 2: Printing to stdout instead of stderr

**WRONG:**
```python
def handle_findings(violations: list[Issue]) -> NoReturn:
    """Handle violations."""
    if violations:
        message = build_error_message(violations)
        print(message)  # ❌ WRONG - Goes to stdout
        sys.exit(2)

    sys.exit(0)
```

**CORRECT:**
```python
def handle_findings(violations: list[Issue]) -> NoReturn:
    """Handle violations."""
    if violations:
        message = build_error_message(violations)
        print(message, file=sys.stderr)  # ✅ CORRECT - Goes to stderr
        sys.exit(2)

    sys.exit(0)
```

### ❌ MISTAKE 3: Not validating tool_input type

**WRONG:**
```python
def extract_command(data: PreToolUseInput) -> str:
    """Extract command."""
    tool_input = data.get("tool_input", {})
    return tool_input.get("command", "")  # ❌ May crash if not dict
```

**CORRECT:**
```python
def extract_command(data: PreToolUseInput) -> str:
    """Extract command."""
    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return ""
    return tool_input.get("command", "")  # ✅ Safe
```

### ❌ MISTAKE 4: Crashing on invalid input

**WRONG:**
```python
def parse_input() -> PreToolUseInput:
    """Parse input."""
    return json.loads(sys.stdin.read())  # ❌ Crashes on invalid JSON
```

**CORRECT:**
```python
def parse_input() -> PreToolUseInput:
    """Parse input."""
    input_raw = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(0)  # ✅ Exit gracefully

    try:
        return json.loads(input_raw)
    except json.JSONDecodeError:
        sys.exit(0)  # ✅ Exit gracefully
```

### ❌ MISTAKE 5: Forgetting to use python-tool-writer

**WRONG:**
```python
# Manually writing hook without PEP 723 metadata
# Missing proper shebang, dependencies, etc.
```

**CORRECT:**

Always invoke the `python-tool-writer` skill:

```
Use python-tool-writer to create a PreToolUse hook that:
1. Blocks pandas imports when polars exists in pyproject.toml
2. Uses TypedDicts from the hook templates
3. Includes ast-grep-py dependency
4. Follows the standard PreToolUse pattern with exit code 2 for blocking
```

## Best Practices

1. **Always use exit code 2 to block** - Exit code 0 means "allow"
2. **Always print to stderr** - Messages must go to stderr, not stdout
3. **Validate tool_input is a dict** - Use isinstance() before accessing
4. **Handle errors gracefully** - Exit with code 0 on unexpected errors
5. **Be specific in messages** - Tell Claude exactly what's wrong and how to fix
6. **Keep hooks fast** - Should complete in <1 second
7. **Test with real data** - Run hook manually with actual JSON input
8. **Use python-tool-writer** - Always generate hooks with proper PEP 723 metadata
9. **Type everything** - Use TypedDict for all data structures
10. **Document why** - Explain in docstring why this validation exists

## Integration with python-tool-writer

**ALWAYS** use the `python-tool-writer` skill when creating PreToolUse hooks:

```
Use python-tool-writer to create a PreToolUse hook script named "block_any_return_type.py" that:

Purpose: Block functions with Any return type in Python files

Behavior:
1. Triggers on Write/Edit tools for .py files
2. Uses ast-grep-py to detect "def func() -> Any" patterns
3. Blocks operation with exit code 2 if violations found
4. Prints helpful message to stderr with suggestions
5. Exits with code 0 if no violations

TypedDicts:
- PreToolUseInput (session_id, tool_name, tool_input, etc.)
- WriteToolInput (file_path, content)
- EditToolInput (file_path, old_string, new_string)
- AnyReturnIssue (function_name, line, suggestion)

Dependencies:
- ast-grep-py>=0.24.1

Follow the standard PreToolUse pattern with proper error handling.
```

## Testing Your Hook

### Manual Testing

```bash
# Create test input
echo '{
  "session_id": "test",
  "tool_name": "Write",
  "transcript_path": "/tmp/transcript.jsonl",
  "cwd": "/tmp",
  "hook_event_name": "PreToolUse",
  "tool_input": {
    "file_path": "/tmp/test.py",
    "content": "def foo() -> Any:\n    pass"
  }
}' | uv run your_hook.py

# Check exit code
echo $?
# Should be 2 if violation detected, 0 if clean
```

### Verify Behavior

1. **Test blocking case** - Hook should exit 2 and print to stderr
2. **Test passing case** - Hook should exit 0 silently
3. **Test error handling** - Invalid input should exit 0
4. **Test performance** - Should complete in <1 second

## Summary

PreToolUse hooks are powerful tools for **blocking** operations before they execute:

✅ Exit code 2 = BLOCK tool
✅ Print to stderr, not stdout
✅ Validate inputs with isinstance()
✅ Handle errors gracefully (exit 0)
✅ Use python-tool-writer skill
✅ Keep fast (<1 second)

**Remember**: PreToolUse is your chance to **stop** bad operations before they happen. Use it wisely!
