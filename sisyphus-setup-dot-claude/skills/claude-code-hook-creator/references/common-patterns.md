# Common Patterns and Utilities for Claude Code Hooks

This reference contains reusable code patterns and utility functions frequently used in Claude Code hooks.

## Table of Contents

1. [Standard Hook Structure](#standard-hook-structure)
2. [Input Parsing](#input-parsing)
3. [File Operations](#file-operations)
4. [Process Execution](#process-execution)
5. [Path Handling](#path-handling)
6. [Transcript Reading](#transcript-reading)
7. [Project Dependency Checking](#project-dependency-checking)
8. [Error Handling](#error-handling)
9. [Message Building](#message-building)
10. [AST Parsing with ast-grep](#ast-parsing-with-ast-grep)

## Standard Hook Structure

### Minimal Hook Template

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
[Hook Name] for Claude Code.
[Brief description]
"""

from __future__ import annotations

import json
import sys
from typing import NoReturn, TypedDict


class Config:
    """Configuration constants."""
    EXIT_CODE_BLOCK_TOOL: int = 2


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

    result = process_hook_logic(data)
    handle_findings(result)


def parse_input() -> dict:
    """Parse and validate stdin input."""
    input_raw = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(0)

    try:
        return json.loads(input_raw)
    except json.JSONDecodeError:
        sys.exit(0)


def should_process(data: dict) -> bool:
    """Determine if the input should be processed."""
    # Add filtering logic
    return True


def process_hook_logic(data: dict) -> Any:
    """Core hook processing logic."""
    # Implement main logic
    pass


def handle_findings(result: Any) -> NoReturn:
    """Handle results and exit appropriately."""
    if not result:
        sys.exit(0)

    message = build_error_message(result)
    print(message, file=sys.stderr)
    sys.exit(Config.EXIT_CODE_BLOCK_TOOL)


def build_error_message(result: Any) -> str:
    """Build error message for Claude."""
    return "Error message here"


def handle_hook_error() -> NoReturn:
    """Handle errors in hook execution."""
    sys.exit(0)


if __name__ == "__main__":
    main()
```

## Input Parsing

### Safe JSON Parsing

```python
def parse_input() -> dict[str, Any]:
    """Parse and validate stdin input with comprehensive error handling."""
    input_raw = sys.stdin.read()

    if not input_raw:
        print("[hook] Skipping: No input provided", file=sys.stderr)
        sys.exit(0)

    if not input_raw.strip():
        print("[hook] Skipping: Empty input", file=sys.stderr)
        sys.exit(0)

    try:
        parsed_data = json.loads(input_raw)
        return parsed_data
    except json.JSONDecodeError as e:
        print(f"[hook] Skipping: Invalid JSON input - {e}", file=sys.stderr)
        sys.exit(0)
```

### Type-Safe Input Parsing

```python
from typing import TypedDict, cast

class PreToolUseInput(TypedDict):
    session_id: str
    tool_name: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    tool_input: dict[str, Any]


def parse_input() -> PreToolUseInput:
    """Parse and validate stdin input."""
    input_raw = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(0)

    try:
        parsed_data: PreToolUseInput = json.loads(input_raw)
        return parsed_data
    except (json.JSONDecodeError, KeyError, TypeError):
        sys.exit(0)
```

## File Operations

### Safe File Reading

```python
from pathlib import Path

def read_file_content(file_path: str) -> str | None:
    """Read file content with error handling."""
    if not file_path:
        return None

    path = Path(file_path)
    if not path.exists():
        return None

    if not path.is_file():
        return None

    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
```

### Safe File Writing

```python
from pathlib import Path

def write_file_content(file_path: str, content: str) -> bool:
    """Write file content with error handling."""
    if not file_path:
        return False

    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return True
    except (OSError, UnicodeEncodeError):
        return False
```

### File Existence Check

```python
from pathlib import Path

def file_exists(file_path: str) -> bool:
    """Check if file exists safely."""
    if not file_path:
        return False

    try:
        return Path(file_path).exists()
    except (OSError, ValueError):
        return False
```

## Process Execution

### Running Commands with Timeout

```python
import subprocess

def run_command(cmd: list[str], cwd: str = ".", timeout: float = 30.0) -> tuple[str, int]:
    """Run a shell command and return output and exit code."""
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
        return result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "Command timed out", 1
    except (FileNotFoundError, subprocess.SubprocessError) as e:
        return f"Error running command: {e}", 1
```

### Running Commands Silently

```python
import subprocess

def run_command_silent(cmd: list[str], cwd: str = ".") -> bool:
    """Run a command and return True if successful."""
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            cwd=cwd,
            timeout=10.0,
        )
        return result.returncode == 0
    except Exception:
        return False
```

### Async Command Execution

```python
import asyncio

async def run_command_async(cmd: list[str], timeout: float = 10.0) -> tuple[str, str, int]:
    """Run a command asynchronously and return stdout, stderr, and returncode."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            async with asyncio.timeout(timeout):
                stdout, stderr = await proc.communicate()
            return (
                stdout.decode("utf-8") if stdout else "",
                stderr.decode("utf-8") if stderr else "",
                proc.returncode or 0,
            )
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return "", "Timeout", -1

    except Exception as e:
        return "", str(e), -1
```

## Path Handling

### Extract File Path from Tool Input

```python
def extract_file_path(data: dict[str, Any]) -> str:
    """Extract file path from various tool input types."""
    tool_input = data.get("tool_input", {})

    if not isinstance(tool_input, dict):
        return ""

    # Try different field names
    file_path = (
        tool_input.get("file_path") or
        tool_input.get("notebook_path") or
        tool_input.get("target_file") or
        ""
    )

    return str(file_path) if file_path else ""
```

### Get Display Path (Relative to CWD)

```python
from pathlib import Path

def get_display_path(file_path: str, cwd: str | None = None) -> str:
    """Get display-friendly path relative to cwd if possible."""
    if not file_path:
        return ""

    try:
        base_path = Path(cwd) if cwd else Path.cwd()
        file_path_obj = Path(file_path).resolve()

        if file_path_obj.is_relative_to(base_path):
            return str(file_path_obj.relative_to(base_path))

        return file_path
    except (ValueError, OSError):
        return file_path
```

### Path Validation

```python
from pathlib import Path

def is_python_file(file_path: str) -> bool:
    """Check if file is a Python file."""
    if not file_path:
        return False
    return file_path.endswith((".py", ".pyi"))


def is_test_file(file_path: str) -> bool:
    """Check if file is a test file."""
    if not file_path:
        return False

    path = Path(file_path)

    # Check filename
    if path.name.startswith("test_") or path.name.endswith("_test.py"):
        return True

    # Check directory
    parts = path.parts
    return "test" in parts or "tests" in parts


def is_excluded_path(file_path: str, exclusions: list[str] | None = None) -> bool:
    """Check if path should be excluded."""
    if not file_path:
        return True

    default_exclusions = [
        ".venv",
        "venv",
        "node_modules",
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "build",
        "dist",
    ]

    exclusions = exclusions or default_exclusions

    path = Path(file_path)
    for exclusion in exclusions:
        if exclusion in path.parts:
            return True

    return False
```

## Transcript Reading

### Read Transcript Messages

```python
import json
from pathlib import Path
from typing import Any

def read_transcript_messages(transcript_path: str) -> list[dict[str, Any]]:
    """Read all messages from transcript file."""
    transcript_file = Path(transcript_path)
    if not transcript_file.exists():
        return []

    messages: list[dict[str, Any]] = []

    try:
        with transcript_file.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    message = json.loads(line)
                    messages.append(message)
                except json.JSONDecodeError:
                    continue

        return messages

    except OSError:
        return []
```

### Search Transcript for Pattern

```python
import json
from pathlib import Path

def is_pattern_in_transcript(pattern: str, transcript_path: str) -> bool:
    """Check if pattern exists in transcript."""
    transcript_file = Path(transcript_path)
    if not transcript_file.exists():
        return False

    try:
        with transcript_file.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    message = json.loads(line)
                    content = message.get("content", "")

                    if isinstance(content, list):
                        content_str = json.dumps(content)
                    else:
                        content_str = str(content)

                    if pattern in content_str:
                        return True

                except (json.JSONDecodeError, KeyError, TypeError):
                    continue

        return False

    except OSError:
        return False
```

## Project Dependency Checking

### Check pyproject.toml Dependencies

```python
from pathlib import Path

def has_dependency(dependency_name: str, pyproject_path: str = "pyproject.toml") -> bool:
    """Check if project has a specific dependency in pyproject.toml."""
    path = Path(pyproject_path)

    if not path.exists():
        return False

    try:
        import toml

        with open(path) as f:
            config = toml.load(f)

        # Check project dependencies
        if "project" in config and "dependencies" in config["project"]:
            deps = config["project"]["dependencies"]
            for dep in deps:
                if dependency_name.lower() in dep.lower():
                    return True

        # Check tool.uv.dev-dependencies
        if "tool" in config and "uv" in config["tool"]:
            uv_config = config["tool"]["uv"]
            if "dev-dependencies" in uv_config:
                dev_deps = uv_config["dev-dependencies"]
                for dep in dev_deps:
                    if dependency_name.lower() in dep.lower():
                        return True

        return False

    except Exception:
        return False
```

### Check Python Version

```python
import re
import sys
from pathlib import Path

def check_python_version_meets_requirement(min_major: int, min_minor: int) -> bool:
    """Check if Python version meets minimum requirement."""
    # Check runtime version
    if sys.version_info.major > min_major:
        return True
    if sys.version_info.major == min_major and sys.version_info.minor >= min_minor:
        return True

    # Check pyproject.toml
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        try:
            with open(pyproject_path) as f:
                content = f.read()

            # Look for requires-python
            match = re.search(r'requires-python\s*=\s*"[^"]*(\d+)\.(\d+)', content)
            if match:
                major = int(match.group(1))
                minor = int(match.group(2))
                if major > min_major or (major == min_major and minor >= min_minor):
                    return True

        except Exception:
            pass

    return False
```

## Error Handling

### Graceful Error Handler

```python
import sys
import traceback

def handle_hook_error() -> NoReturn:
    """Handle errors in hook execution gracefully."""
    # Don't print traceback in production - just exit
    sys.exit(0)


def handle_hook_error_verbose() -> NoReturn:
    """Handle errors with traceback (for debugging)."""
    print("[Hook Error] Unexpected error occurred:", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(0)
```

### Try-Except Wrapper

```python
from typing import Callable, TypeVar

T = TypeVar('T')

def safe_execute(func: Callable[[], T], default: T) -> T:
    """Execute function safely and return default on error."""
    try:
        return func()
    except Exception:
        return default
```

## Message Building

### Build Structured Error Message

```python
def build_structured_message(
    title: str,
    items: list[dict[str, str]],
    footer: str | None = None,
) -> str:
    """Build a structured error message."""
    lines: list[str] = []

    lines.append(title)
    lines.append("=" * 60)
    lines.append("")

    for i, item in enumerate(items, 1):
        lines.append(f"[{i}] {item.get('title', 'Item')}")
        for key, value in item.items():
            if key != 'title':
                lines.append(f"    {key}: {value}")
        lines.append("")

    if footer:
        lines.append("-" * 60)
        lines.append(footer)

    return "\n".join(lines)
```

### Format Code with Line Numbers

```python
def format_code_with_line_numbers(code: str, start_line: int = 1) -> str:
    """Format code with line numbers."""
    lines = code.split("\n")
    formatted_lines = []

    for i, line in enumerate(lines):
        line_num = start_line + i
        formatted_lines.append(f"{line_num:6} │ {line}")

    return "\n".join(formatted_lines)
```

### Truncate Text

```python
def truncate_text(text: str, max_length: int = 80) -> str:
    """Truncate text to specified length with ellipsis if needed."""
    if len(text) <= max_length:
        return text

    lines = text.split("\n")
    if len(lines) > 1:
        first_line = lines[0]
        if len(first_line) > max_length - 3:
            return first_line[:max_length - 3] + "..."
        return first_line + "..."

    return text[:max_length - 3] + "..."
```

## AST Parsing with ast-grep

### Initialize AST Parser

```python
import ast_grep_py as sg

def parse_python_code(code: str) -> sg.SgNode:
    """Parse Python code into AST."""
    root: sg.SgRoot = sg.SgRoot(code, "python")
    return root.root()
```

### Find Patterns

```python
import ast_grep_py as sg

def find_all_functions(code: str) -> list[sg.SgNode]:
    """Find all function definitions in code."""
    root: sg.SgRoot = sg.SgRoot(code, "python")
    node: sg.SgNode = root.root()

    return node.find_all(pattern="def $FUNC($$$ARGS): $$$BODY")


def find_all_classes(code: str) -> list[sg.SgNode]:
    """Find all class definitions in code."""
    root: sg.SgRoot = sg.SgRoot(code, "python")
    node: sg.SgNode = root.root()

    return node.find_all(pattern="class $NAME($$$BASES): $BODY")
```

### Extract Information from Nodes

```python
import ast_grep_py as sg

def extract_function_name(func_node: sg.SgNode) -> str:
    """Extract function name from function node."""
    name_match = func_node.get_match("FUNC")
    if name_match:
        return name_match.text()

    # Fallback: parse from text
    import re
    func_text = func_node.text()
    match = re.match(r"(?:async\s+)?def\s+(\w+)", func_text)
    if match:
        return match.group(1)

    return "unknown_function"


def extract_class_name(class_node: sg.SgNode) -> str:
    """Extract class name from class node."""
    name_match = class_node.get_match("NAME")
    if name_match:
        return name_match.text()

    name_field = class_node.field("name")
    if name_field:
        return name_field.text()

    # Fallback: parse from text
    import re
    class_text = class_node.text()
    match = re.match(r"class\s+(\w+)", class_text)
    if match:
        return match.group(1)

    return "UnknownClass"
```

### Check Node Hierarchy

```python
import ast_grep_py as sg

def is_method_node(func_node: sg.SgNode) -> bool:
    """Check if a function node is a method (inside a class)."""
    current: sg.SgNode | None = func_node.parent()
    while current:
        if current.kind() == "class_definition":
            return True
        current = current.parent()
    return False


def is_async_function(func_node: sg.SgNode) -> bool:
    """Check if function is async."""
    func_text = func_node.text()
    return func_text.strip().startswith("async ")
```

## Tool Input Validation Patterns

### Validate Bash Command

```python
def should_process_bash(data: dict[str, Any]) -> bool:
    """Check if Bash tool should be processed."""
    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input")

    if tool_name != "Bash":
        return False

    if not isinstance(tool_input, dict):
        return False

    command = tool_input.get("command", "")
    if not command or not command.strip():
        return False

    return True
```

### Validate File Edit

```python
def should_process_file_edit(data: dict[str, Any]) -> bool:
    """Check if file edit tool should be processed."""
    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input")

    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        return False

    if not isinstance(tool_input, dict):
        return False

    file_path = tool_input.get("file_path", "")
    if not file_path:
        return False

    # Check file extension
    if not file_path.endswith(".py"):
        return False

    # Skip excluded paths
    if is_excluded_path(file_path):
        return False

    return True
```

## Best Practices

1. **Always handle errors gracefully** - Exit with code 0 on unexpected errors
2. **Use type hints** - Makes code more maintainable
3. **Validate inputs** - Check types and existence before using
4. **Use Path objects** - More robust than string manipulation
5. **Set timeouts** - Prevent hooks from hanging
6. **Keep functions small** - One responsibility per function
7. **Document edge cases** - Comment unusual behavior
8. **Test with real data** - Run hooks manually to verify behavior
