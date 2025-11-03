# Other Hook Events Reference

This reference covers less commonly used hook events: Stop, SubagentStop, SessionStart, SessionEnd, PreCompact, and Notification.

## Table of Contents

1. [Stop](#stop)
2. [SubagentStop](#subagent-stop)
3. [SessionStart](#session-start)
4. [SessionEnd](#session-end)
5. [PreCompact](#precompact)
6. [Notification](#notification)

## Stop

**When**: Claude Code finishes responding to the user.

**Purpose**: Post-response actions, logging, validation.

### Input Structure

```python
from typing import TypedDict

class StopInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str  # Always "Stop"
```

### Exit Code Behavior

- **Exit Code 0**: Hook succeeded, continue normally
- **Exit Code 2**: Blocks stoppage, sends stderr to Claude

### Example: Response Validator

```python
#!/usr/bin/env python3
"""
Stop hook that validates Claude's response before finishing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import NoReturn, TypedDict


class StopInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str


def main() -> None:
    """Main entry point."""
    try:
        data: StopInput = json.loads(sys.stdin.read())

        # Read last response from transcript
        last_response = read_last_claude_response(data["transcript_path"])

        # Validate response
        if not validate_response(last_response):
            print("Response validation failed. Please address the issues.", file=sys.stderr)
            sys.exit(2)  # Block stoppage

        sys.exit(0)  # Allow stoppage

    except Exception:
        sys.exit(0)


def read_last_claude_response(transcript_path: str) -> str:
    """Read the last Claude response from transcript."""
    transcript_file = Path(transcript_path)
    if not transcript_file.exists():
        return ""

    try:
        with transcript_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        # Find last assistant message
        for line in reversed(lines):
            try:
                message = json.loads(line.strip())
                if message.get("role") == "assistant":
                    content = message.get("content", "")
                    if isinstance(content, str):
                        return content
            except json.JSONDecodeError:
                continue

        return ""

    except Exception:
        return ""


def validate_response(response: str) -> bool:
    """Validate response content."""
    # Example: Check if response is not too short
    if len(response.strip()) < 10:
        return False

    return True


if __name__ == "__main__":
    main()
```

### Use Cases

- Validate response completeness
- Log response metadata
- Check for required information
- Enforce response patterns

## SubagentStop

**When**: A subagent (Task tool) completes execution.

**Purpose**: Validate subagent results before continuing.

### Input Structure

```python
from typing import TypedDict

class SubagentStopInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str  # Always "SubagentStop"
    subagent_id: str      # Identifier for the subagent
```

### Exit Code Behavior

- **Exit Code 0**: Subagent results accepted
- **Exit Code 2**: Blocks stoppage, sends stderr to Claude for review

### Example: Subagent Result Validator

```python
#!/usr/bin/env python3
"""
SubagentStop hook that validates subagent results.
"""

from __future__ import annotations

import json
import sys
from typing import NoReturn, TypedDict


class SubagentStopInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    subagent_id: str


def main() -> None:
    """Main entry point."""
    try:
        data: SubagentStopInput = json.loads(sys.stdin.read())

        subagent_id = data.get("subagent_id", "")

        # Validate subagent results
        if not validate_subagent_results(subagent_id, data["transcript_path"]):
            print(f"Subagent {subagent_id} results need review.", file=sys.stderr)
            sys.exit(2)  # Block stoppage for review

        sys.exit(0)  # Accept results

    except Exception:
        sys.exit(0)


def validate_subagent_results(subagent_id: str, transcript_path: str) -> bool:
    """Validate subagent results."""
    # Example validation logic
    return True


if __name__ == "__main__":
    main()
```

### Use Cases

- Validate subagent outputs
- Check if subagent completed required tasks
- Enforce quality standards
- Log subagent performance

## SessionStart

**When**: Session begins or resumes.

**Purpose**: Initialize session context, inject startup information.

### Input Structure

```python
from typing import TypedDict

class SessionStartInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str  # Always "SessionStart"
```

### Exit Code Behavior

- **Exit Code 0 + stdout**: stdout becomes context for Claude
- **Exit Code 2**: Unlikely to use, would block session start

### Example: Session Initializer

```python
#!/usr/bin/env python3
"""
SessionStart hook that injects welcome message and project info.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    """Main entry point."""
    try:
        data = json.loads(sys.stdin.read())

        cwd = data.get("cwd", "")

        # Generate welcome message with project info
        welcome_message = generate_welcome_message(cwd)

        # stdout becomes context for Claude
        print(welcome_message)
        sys.exit(0)

    except Exception:
        sys.exit(0)


def generate_welcome_message(cwd: str) -> str:
    """Generate welcome message with project information."""
    lines = ["", "[session-start]", "Session initialized.", ""]

    # Add project info
    pyproject_path = Path(cwd) / "pyproject.toml"
    if pyproject_path.exists():
        lines.append("Python project detected (pyproject.toml found)")

    package_json = Path(cwd) / "package.json"
    if package_json.exists():
        lines.append("Node.js project detected (package.json found)")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
```

### Use Cases

- Welcome messages
- Project initialization
- Inject project conventions
- Setup reminders

## SessionEnd

**When**: Session terminates.

**Purpose**: Cleanup, logging, saving state.

### Input Structure

```python
from typing import TypedDict

class SessionEndInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str  # Always "SessionEnd"
```

### Exit Code Behavior

- **Exit Code 0**: Hook succeeded
- No blocking behavior (session is ending anyway)

### Example: Session Logger

```python
#!/usr/bin/env python3
"""
SessionEnd hook that logs session statistics.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


def main() -> None:
    """Main entry point."""
    try:
        data = json.loads(sys.stdin.read())

        session_id = data.get("session_id", "")
        transcript_path = data.get("transcript_path", "")

        # Log session statistics
        log_session_stats(session_id, transcript_path)

        sys.exit(0)

    except Exception:
        sys.exit(0)


def log_session_stats(session_id: str, transcript_path: str) -> None:
    """Log session statistics to a file."""
    transcript_file = Path(transcript_path)
    if not transcript_file.exists():
        return

    try:
        # Count messages
        with transcript_file.open("r", encoding="utf-8") as f:
            message_count = sum(1 for line in f if line.strip())

        # Write log
        log_file = Path.home() / ".claude" / "session-logs.txt"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with log_file.open("a", encoding="utf-8") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{timestamp} | Session {session_id} | {message_count} messages\n")

    except Exception:
        pass


if __name__ == "__main__":
    main()
```

### Use Cases

- Log session metrics
- Save conversation summaries
- Cleanup temporary files
- Export session data

## PreCompact

**When**: Before compaction operations (context window management).

**Purpose**: Pre-compaction validation or preparation.

### Input Structure

```python
from typing import TypedDict

class PreCompactInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str  # Always "PreCompact"
```

### Exit Code Behavior

- **Exit Code 0**: Allow compaction
- **Exit Code 2**: Block compaction (rare)

### Example: Compaction Logger

```python
#!/usr/bin/env python3
"""
PreCompact hook that logs when compaction occurs.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


def main() -> None:
    """Main entry point."""
    try:
        data = json.loads(sys.stdin.read())

        # Log compaction event
        log_compaction_event(data.get("session_id", ""))

        sys.exit(0)  # Allow compaction

    except Exception:
        sys.exit(0)


def log_compaction_event(session_id: str) -> None:
    """Log that compaction occurred."""
    log_file = Path.home() / ".claude" / "compaction-log.txt"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with log_file.open("a", encoding="utf-8") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{timestamp} | Session {session_id} | Compaction triggered\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
```

### Use Cases

- Log compaction events
- Save important context before compaction
- Validate compaction timing
- Prepare for context reduction

## Notification

**When**: Claude sends notifications (permission requests, idle waiting, etc.).

**Purpose**: Custom notification handling.

### Input Structure

```python
from typing import Any, TypedDict

class NotificationInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str          # Always "Notification"
    notification_type: str         # Type of notification
    notification_data: dict[str, Any]  # Additional data
```

### Notification Types

- `permission_request` - Claude requests permission for an action
- `idle_waiting` - Claude is waiting for user input
- `tool_pending` - Tool execution is pending
- (Other types as defined by Claude Code)

### Exit Code Behavior

- **Exit Code 0**: Notification handled
- **Exit Code 2**: Custom notification response

### Example: Notification Logger

```python
#!/usr/bin/env python3
"""
Notification hook that logs all notifications.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict


class NotificationInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    notification_type: str
    notification_data: dict[str, Any]


def main() -> None:
    """Main entry point."""
    try:
        data: NotificationInput = json.loads(sys.stdin.read())

        notification_type = data.get("notification_type", "")
        notification_data = data.get("notification_data", {})

        # Log notification
        log_notification(notification_type, notification_data)

        sys.exit(0)

    except Exception:
        sys.exit(0)


def log_notification(notification_type: str, notification_data: dict[str, Any]) -> None:
    """Log notification to file."""
    log_file = Path.home() / ".claude" / "notification-log.txt"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with log_file.open("a", encoding="utf-8") as f:
            timestamp = datetime.now().isoformat()
            data_str = json.dumps(notification_data)
            f.write(f"{timestamp} | {notification_type} | {data_str}\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
```

### Use Cases

- Log notification events
- Custom notification handling
- Auto-approve certain permissions
- Monitor Claude's state

## Summary

These less common hook events provide additional control points:

| Event | Purpose | Common Use |
|-------|---------|------------|
| **Stop** | Post-response validation | Validate completeness |
| **SubagentStop** | Subagent validation | Quality checks |
| **SessionStart** | Session initialization | Welcome messages |
| **SessionEnd** | Session cleanup | Logging, cleanup |
| **PreCompact** | Pre-compaction prep | Save context |
| **Notification** | Notification handling | Custom responses |

**Note**: These events are used less frequently than PreToolUse, PostToolUse, and UserPromptSubmit. Implement them only when you have specific requirements for these control points.

## Integration with python-tool-writer

When creating hooks for these events, **ALWAYS** use the `python-tool-writer` skill:

```
Use python-tool-writer to create a SessionStart hook script named "session_welcome.py" that:

Purpose: Inject welcome message and project info at session start

Behavior:
1. Reads pyproject.toml and package.json to detect project type
2. Generates welcome message with project information
3. Prints to stdout (becomes context for Claude)
4. Exits with code 0

TypedDicts:
- SessionStartInput (session_id, transcript_path, cwd, hook_event_name)

Dependencies: []

Print to stdout (NOT stderr) for context injection.
```
