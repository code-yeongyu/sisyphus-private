---
name: claude-code-hook-creator
description: Claude Code Hook Creator, as known as 'CC Hook Master'. Expert skill for creating, designing, and implementing Claude Code hooks with comprehensive type safety and real-world patterns. Activate when users request to create hooks for PreToolUse, PostToolUse, UserPromptSubmit, or other Claude Code automation events. Provides TypedDict templates, exit code strategies, and production-ready patterns for blocking operations, validating inputs, running linters, and injecting context.
---

# Claude Code Hook Creator

Expert skill for creating, designing, and implementing Claude Code hooks with comprehensive type safety and real-world patterns.

## When to Activate

This skill activates automatically when users request:
- "Create a hook for..."
- "Make a hook that blocks/validates/checks..."
- "I need a PreToolUse/PostToolUse hook..."
- "Build a hook to enforce..."
- Working with Claude Code automation or validation

## Quick Navigation

### Essential References

1. **[TypedDict Definitions](references/typedicts.md)** - All TypedDict structures for type-safe hooks
2. **[NotRequired Pattern Guide](references/notrequired-pattern-guide.md)** - NotRequired vs str | None (엄밀한 구분)
3. **[Common Patterns](references/common-patterns.md)** - Reusable utilities and code patterns
4. **[PreToolUse Hooks](references/pre-tool-use.md)** - Block operations BEFORE execution
5. **[PostToolUse Hooks](references/post-tool-use.md)** - Validate and inform AFTER execution
6. **[UserPromptSubmit Hooks](references/user-prompt-submit.md)** - Inject context before prompts
7. **[Other Events](references/other-events.md)** - Stop, SubagentStop, SessionStart, SessionEnd, etc.

### Official Documentation

- **[Hooks API Reference](references/hooks-api-reference.md)** - Complete official API documentation
- **[Getting Started Guide](references/get-started-with-claude-code-hooks.md)** - Quick start tutorial

## Hook Event Types Overview

Claude Code hooks execute at specific events to control Claude's behavior:

### PreToolUse - BLOCK Before Execution

**When**: BEFORE a tool executes
**Purpose**: Block dangerous operations, validate inputs, enforce policies
**Exit Code 2**: **BLOCKS the tool** from executing, sends stderr to Claude

**Common Use Cases**:
- Block `grep` → suggest `rg`
- Prevent library misuse (pandas when polars exists)
- Block code with `Any` return types
- Security validation
- Policy enforcement

**Key Pattern**: Validation hooks that **prevent** bad operations

➡️ **[Full PreToolUse Reference](references/pre-tool-use.md)**

### PostToolUse - INFORM After Execution

**When**: AFTER a tool completes successfully
**Purpose**: Validate outputs, run formatters/linters, inject context
**Exit Code 2**: Tool already ran, sends stderr to Claude to **inform** about issues

**Common Use Cases**:
- Run linters (ruff, basedpyright)
- Auto-format code
- Detect code smells (TypedDict total=False)
- Type checking
- Inject knowledge files

**Key Pattern**: Context injection hooks that detect **new issues** and inform Claude

**⚠️ MOST COMMON MISTAKE**: Using exit code 0 when you want Claude to see the message!

Even though the tool succeeded, **ALWAYS use exit code 2** if you want to inform Claude.

➡️ **[Full PostToolUse Reference](references/post-tool-use.md)**

### UserPromptSubmit - INJECT Context

**When**: BEFORE Claude processes user's prompt
**Purpose**: Inject system context, add metadata
**Exit Code 0 + stdout**: stdout becomes context for Claude
**Exit Code 2**: Blocks prompt (rare)

**Common Use Cases**:
- Add git status, Python version
- Inject environment info
- Add timestamps
- User preference reminders

**Key Pattern**: System reminder injection on every prompt

➡️ **[Full UserPromptSubmit Reference](references/user-prompt-submit.md)**

### Other Events

- **Stop**: Post-response validation
- **SubagentStop**: Subagent result validation
- **SessionStart**: Session initialization
- **SessionEnd**: Cleanup and logging
- **PreCompact**: Pre-compaction preparation
- **Notification**: Custom notification handling

➡️ **[Other Events Reference](references/other-events.md)**

## Exit Code Strategy

Understanding exit codes is **CRITICAL** for hook behavior:

### Exit Code 0 - Success/Allow

**PreToolUse**: Allow tool to execute
**PostToolUse**: Hook succeeded, nothing to say to Claude (SILENT)
**UserPromptSubmit**: Inject stdout as context
**Other**: Normal success

### Exit Code 2 - Block/Inform

**PreToolUse**: **BLOCKS tool** from executing, stderr → Claude
**PostToolUse**: Tool already ran, **INFORMS Claude** via stderr
**UserPromptSubmit**: Blocks prompt, erases it
**Stop/SubagentStop**: Blocks stoppage, stderr → Claude

### Other Exit Codes

Non-blocking error, stderr shown to user (not Claude)

## Common Mistake Patterns

### ❌ MISTAKE 1: PostToolUse exit code confusion (MOST COMMON!)

**WRONG:**
```python
# PostToolUse hook - found violations
if violations:
    message = build_error_message(violations)
    print(message, file=sys.stderr)
    sys.exit(0)  # ❌ WRONG - Claude never sees this!
```

**CORRECT:**
```python
# PostToolUse hook - found violations
if violations:
    message = build_error_message(violations)
    print(message, file=sys.stderr)
    sys.exit(2)  # ✅ CORRECT - Claude sees and can fix!
```

**Why**: PostToolUse developers think "tool succeeded, so return 0". **WRONG!** Exit code 2 means "inform Claude", not "tool failed".

### ❌ MISTAKE 2: Wrong output stream

**PreToolUse/PostToolUse**: Print to `stderr` (not stdout)
**UserPromptSubmit**: Print to `stdout` (not stderr)

### ❌ MISTAKE 3: Not using python-tool-writer

**ALWAYS** use the `python-tool-writer` skill to generate hooks with proper PEP 723 metadata.

➡️ See each reference for more common mistakes

## Workflow: Creating a Hook

When a user requests a hook, follow these steps:

### 1. Understand the Requirement

Ask clarifying questions:
- Which hook event type? (PreToolUse, PostToolUse, etc.)
- What should trigger it? (file types, commands, tools)
- What action? (block, validate, inject, log)
- What should Claude receive as feedback?

### 2. Choose the Hook Type

| Requirement                          | Hook Type                |
| ------------------------------------ | ------------------------ |
| **Prevent** operation from happening | PreToolUse               |
| **Detect issues** in written code    | PostToolUse              |
| **Add context** to every prompt      | UserPromptSubmit         |
| **Validate** Claude's response       | Stop                     |
| **Initialize** session               | SessionStart             |
| **Log** events                       | SessionEnd, Notification |

### 3. Design the Structure

Consult the appropriate reference:
- **[PreToolUse Reference](references/pre-tool-use.md)** - Blocking patterns
- **[PostToolUse Reference](references/post-tool-use.md)** - Context injection patterns
- **[UserPromptSubmit Reference](references/user-prompt-submit.md)** - System reminder patterns

Use **[TypedDict Reference](references/typedicts.md)** for type-safe structures.

Use **[Common Patterns Reference](references/common-patterns.md)** for utilities.

### 4. Generate with python-tool-writer

**CRITICAL**: ALWAYS use the `python-tool-writer` skill to create hooks:

```
Use python-tool-writer to create a [PreToolUse|PostToolUse|UserPromptSubmit] hook script named "[name].py" that:

Purpose: [Clear description of what the hook does]

Behavior:
1. [Step-by-step logic]
2. [Trigger conditions]
3. [Exit code strategy]
4. [Output format]

TypedDicts:
- [List all TypedDict structures needed]
- [See references/typedicts.md for complete definitions]

Dependencies:
- [List any required packages, e.g., "ast-grep-py>=0.24.1"]

Special Notes:
- [Any specific patterns or edge cases]
- [Exit code clarification if needed]
```

**Why python-tool-writer?**
- Ensures proper PEP 723 inline script metadata
- Adds correct shebang and dependencies
- Creates portable, executable scripts
- Follows uv standards

### 5. Test the Hook

After generation, test manually:

```bash
# Create test input JSON
echo '{
  "session_id": "test",
  "tool_name": "Write",
  ...
}' | uv run your_hook.py

# Check exit code
echo $?
# Should be 2 if blocking/informing, 0 if passing
```

## Real-World Hook Patterns

### Pattern 1: Command Substitution (PreToolUse)

Block deprecated commands and suggest alternatives:

```python
# Block grep → suggest rg
# Block pandas import → suggest polars (when polars in deps)
# Block asyncio → suggest anyio (when anyio exists)
```

➡️ See **[PreToolUse Reference](references/pre-tool-use.md)** for complete examples

### Pattern 2: Code Quality Gates (PreToolUse)

Block code that violates standards:

```python
# Block functions with Any return type
# Block TypedDict with total=False (Python 3.11+)
# Block mutable default arguments
```

➡️ See **[PreToolUse Reference](references/pre-tool-use.md)** for complete examples

### Pattern 3: New Violation Detection (PostToolUse)

**CRITICAL PATTERN**: Only warn about **NEW** violations, not existing ones.

This is the pattern used in `check_typeddict_total_false.py`:

1. Get existing violations (before this edit)
2. Detect all violations (after this edit)
3. Filter to NEW violations only
4. If new violations: inform Claude with exit code 2
5. If no new violations: exit code 0

➡️ See **[PostToolUse Reference](references/post-tool-use.md)** for complete implementation

### Pattern 4: Linter/Formatter Integration (PostToolUse)

Run external tools and inform Claude of results:

```python
# Run ruff check + format
# Run basedpyright type checker
# Run black formatter
# Run prettier for JS/TS
```

➡️ See **[PostToolUse Reference](references/post-tool-use.md)** for complete examples

### Pattern 5: Context Injection (PostToolUse)

Inject knowledge files or system information:

```python
# Inject CLAUDE.md, AGENTS.md when editing nearby files
# Check if already in transcript (avoid duplicates)
# Use file hash to track versions
```

➡️ See **[PostToolUse Reference](references/post-tool-use.md)** for complete examples

### Pattern 6: System Reminder (UserPromptSubmit)

Add system context to every prompt:

```python
# Git status (branch, commit, unstaged count)
# Python version and venv status
# Current timestamp
# Use asyncio for concurrent I/O (keep fast!)
```

➡️ See **[UserPromptSubmit Reference](references/user-prompt-submit.md)** for complete examples

## MCP Tool Integration

When creating hooks for MCP tools (e.g., `mcp__terminalcp__terminalcp`), follow this enhanced workflow:

### MCP Tool Naming Pattern

MCP tools use: `mcp__<server>__<tool>`

Examples:
- `mcp__terminalcp__terminalcp`
- `mcp__zen__chat`
- `mcp__memory__create_entities`

### MCP Hook Workflow

1. **Investigate the MCP tool** - Check tool parameters and capabilities
2. **Ask clarifying questions** - When should it trigger? What info to show?
3. **Design MCP TypedDict** - MCP tools use `args` dict for parameters
4. **Implement tool invocation** - Call MCP tools via subprocess if needed
5. **Generate with python-tool-writer**

➡️ See **[PreToolUse Reference](references/pre-tool-use.md)** and **[PostToolUse Reference](references/post-tool-use.md)** for MCP integration examples

## Standard Hook Structure

Every hook follows this template:

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   # List dependencies here
# ]
# ///
"""
[Hook Name] for Claude Code ([Hook Event Type]).
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


def process_hook_logic(data: dict):
    """Core hook processing logic."""
    # Implement main logic
    pass


def handle_findings(result) -> NoReturn:
    """Handle results and exit appropriately."""
    if not result:
        sys.exit(0)

    message = build_error_message(result)
    print(message, file=sys.stderr)
    sys.exit(Config.EXIT_CODE_BLOCK_TOOL)


def build_error_message(result) -> str:
    """Build error message for Claude."""
    return "Error message here"


def handle_hook_error() -> NoReturn:
    """Handle errors in hook execution."""
    sys.exit(0)


if __name__ == "__main__":
    main()
```

➡️ See **[Common Patterns Reference](references/common-patterns.md)** for more templates and utilities

## Settings.json Integration

After creating a hook, add it to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "uv run ~/.claude/hooks/pre-tool-use/your_hook.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "uv run ~/.claude/hooks/post-tool-use/your_hook.py"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/user-prompt-submit/your_hook.py"
          }
        ]
      }
    ]
  }
}
```

## Best Practices Summary

1. **Always use python-tool-writer skill** - Ensures proper PEP 723 metadata
2. **Use TypedDict for type safety** - See [TypedDict Reference](references/typedicts.md)
3. **Exit code 2 = block (Pre) or inform (Post)** - NOT "tool failed"
4. **Print to stderr (except UserPromptSubmit)** - UserPromptSubmit uses stdout
5. **Handle errors gracefully** - Exit 0 on unexpected errors
6. **Keep hooks fast** - <1 second for most, <500ms for UserPromptSubmit
7. **Filter to NEW violations** - Don't nag about existing issues (PostToolUse pattern)
8. **Be specific in messages** - Tell Claude exactly what's wrong and how to fix
9. **Test manually** - Use echo + pipe to test with real JSON
10. **Validate tool_input** - Use isinstance() before accessing dict fields

## Quick Reference Table

| Hook Event           | When            | Exit 0         | Exit 2            | Output Stream |
| -------------------- | --------------- | -------------- | ----------------- | ------------- |
| **PreToolUse**       | Before tool     | Allow tool     | **BLOCK** tool    | stderr        |
| **PostToolUse**      | After tool      | Silent         | **INFORM** Claude | stderr        |
| **UserPromptSubmit** | Before prompt   | Inject context | Block prompt      | **stdout**    |
| **Stop**             | After response  | Allow          | Block stoppage    | stderr        |
| **SubagentStop**     | After subagent  | Allow          | Block stoppage    | stderr        |
| **SessionStart**     | Session starts  | Inject context | Block (rare)      | stdout        |
| **SessionEnd**       | Session ends    | Success        | N/A               | N/A           |
| **PreCompact**       | Before compact  | Allow          | Block (rare)      | stderr        |
| **Notification**     | On notification | Allow          | Custom            | stderr        |

## Summary

This skill helps you create production-ready Claude Code hooks:

✅ **Comprehensive references** for all hook types and patterns
✅ **TypedDict templates** for complete type safety
✅ **Real-world examples** from actual hooks
✅ **Common mistake warnings** to avoid pitfalls
✅ **python-tool-writer integration** for proper metadata
✅ **Exit code strategies** for each hook type

**Most Important Takeaways**:

1. **PreToolUse exit 2 = BLOCKS** the tool from running
2. **PostToolUse exit 2 = INFORMS** Claude (tool already ran)
3. **ALWAYS use python-tool-writer** skill for hook generation
4. **PostToolUse exit code 0 when you have issues = Claude never sees them!**

**Remember**: Hooks are powerful automation tools. Design them carefully, test thoroughly, and always provide helpful feedback to Claude when issues are detected.

For detailed information on any hook type, consult the appropriate reference document linked throughout this guide.
