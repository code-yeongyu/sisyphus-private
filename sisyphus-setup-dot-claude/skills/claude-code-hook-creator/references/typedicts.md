# TypedDict 정의: Claude Code Hooks

Claude Code hooks의 **엄밀한 타입 안전성**을 위한 완전한 TypedDict 정의 모음입니다.

## 중요: NotRequired vs str | None

TypedDict를 정의하기 전에 **반드시** 이해해야 할 패턴:

- **`field: T`** - 필수 필드, 항상 존재
- **`field: NotRequired[T]`** - 선택 필드, **키가 없을 수 있음**
- **`field: T | None`** - 필수 필드, **키는 있지만 값이 None 가능**
- **`field: NotRequired[T | None]`** - 선택 필드, 키가 없거나 None

➡️ **[NotRequired 패턴 완전 가이드](notrequired-pattern-guide.md)** 참조

## Table of Contents

1. [Hook Event Input Types](#hook-event-input-types)
2. [Tool Input Types](#tool-input-types)
3. [Tool Response Types](#tool-response-types)
4. [Utility Types](#utility-types)
5. [Type Guards](#type-guards)

## Hook Event Input Types

### PreToolUseInput

**도구가 실행되기 BEFORE에 전달되는 input**

```python
from typing import Any, TypedDict

class PreToolUseInput(TypedDict):
    """PreToolUse hook input structure.

    All fields are REQUIRED - Claude Code always sends them.
    """
    session_id: str          # 세션 고유 ID (항상 존재)
    tool_name: str           # 실행될 도구 이름 (항상 존재)
    transcript_path: str     # Transcript 파일 경로 (항상 존재)
    cwd: str                 # 현재 작업 디렉토리 (항상 존재)
    hook_event_name: str     # 항상 "PreToolUse" (항상 존재)
    tool_input: dict[str, Any]  # 도구별 input (항상 존재, 타입은 다양)
```

**핵심 포인트:**
- ✅ **모든 필드가 필수** - Claude Code가 항상 보냄
- ❌ NotRequired 사용 금지 - 불필요하고 타입 체커를 혼란시킴
- `tool_input`은 항상 존재하지만 **내용은 도구마다 다름**

**접근 패턴:**
```python
def process_pre_tool_use(data: PreToolUseInput) -> None:
    # 모든 필드를 직접 접근 가능 - .get() 불필요
    session_id = data["session_id"]      # ✅ 타입: str
    tool_name = data["tool_name"]        # ✅ 타입: str
    tool_input = data["tool_input"]      # ✅ 타입: dict[str, Any]

    # ❌ 잘못된 패턴
    # session_id = data.get("session_id")  # 불필요 - 항상 있음
```

### PostToolUseInput

**도구가 실행된 AFTER에 전달되는 input**

```python
from typing import Any, TypedDict

class PostToolUseInput(TypedDict):
    """PostToolUse hook input structure.

    All fields are REQUIRED - Claude Code always sends them.
    """
    session_id: str          # 세션 고유 ID (항상 존재)
    tool_name: str           # 실행된 도구 이름 (항상 존재)
    transcript_path: str     # Transcript 파일 경로 (항상 존재)
    cwd: str                 # 현재 작업 디렉토리 (항상 존재)
    hook_event_name: str     # 항상 "PostToolUse" (항상 존재)
    tool_input: dict[str, Any]      # 도구에 전달된 input (항상 존재)
    tool_response: dict[str, Any]   # 도구의 실행 결과 (항상 존재)
```

**PreToolUse와의 차이:**
- `tool_response` 필드가 **추가**됨 (도구 실행 후이므로)

**접근 패턴:**
```python
def process_post_tool_use(data: PostToolUseInput) -> None:
    # 모든 필드를 직접 접근
    tool_response = data["tool_response"]  # ✅ 타입: dict[str, Any]

    # tool_response 내부는 도구마다 다름
    success = tool_response.get("success")  # 타입: Any
```

### UserPromptSubmitInput

**사용자가 프롬프트를 제출할 때 전달되는 input**

```python
from typing import TypedDict

class UserPromptSubmitInput(TypedDict):
    """UserPromptSubmit hook input structure.

    All fields are REQUIRED - Claude Code always sends them.
    """
    session_id: str       # 세션 고유 ID (항상 존재)
    transcript_path: str  # Transcript 파일 경로 (항상 존재)
    cwd: str              # 현재 작업 디렉토리 (항상 존재)
    hook_event_name: str  # 항상 "UserPromptSubmit" (항상 존재)
    user_prompt: str      # 사용자가 입력한 프롬프트 (항상 존재)
```

### StopInput

**Claude가 응답을 마칠 때 전달되는 input**

```python
from typing import TypedDict

class StopInput(TypedDict):
    """Stop hook input structure."""
    session_id: str       # 세션 고유 ID (항상 존재)
    transcript_path: str  # Transcript 파일 경로 (항상 존재)
    cwd: str              # 현재 작업 디렉토리 (항상 존재)
    hook_event_name: str  # 항상 "Stop" (항상 존재)
```

### SubagentStopInput

**Subagent가 완료될 때 전달되는 input**

```python
from typing import TypedDict

class SubagentStopInput(TypedDict):
    """SubagentStop hook input structure."""
    session_id: str       # 세션 고유 ID (항상 존재)
    transcript_path: str  # Transcript 파일 경로 (항상 존재)
    cwd: str              # 현재 작업 디렉토리 (항상 존재)
    hook_event_name: str  # 항상 "SubagentStop" (항상 존재)
    subagent_id: str      # Subagent 고유 ID (항상 존재)
```

### SessionStartInput / SessionEndInput

```python
from typing import TypedDict

class SessionStartInput(TypedDict):
    """SessionStart hook input structure."""
    session_id: str       # 세션 고유 ID (항상 존재)
    transcript_path: str  # Transcript 파일 경로 (항상 존재)
    cwd: str              # 현재 작업 디렉토리 (항상 존재)
    hook_event_name: str  # 항상 "SessionStart" (항상 존재)

class SessionEndInput(TypedDict):
    """SessionEnd hook input structure."""
    session_id: str       # 세션 고유 ID (항상 존재)
    transcript_path: str  # Transcript 파일 경로 (항상 존재)
    cwd: str              # 현재 작업 디렉토리 (항상 존재)
    hook_event_name: str  # 항상 "SessionEnd" (항상 존재)
```

### PreCompactInput

```python
from typing import TypedDict

class PreCompactInput(TypedDict):
    """PreCompact hook input structure."""
    session_id: str       # 세션 고유 ID (항상 존재)
    transcript_path: str  # Transcript 파일 경로 (항상 존재)
    cwd: str              # 현재 작업 디렉토리 (항상 존재)
    hook_event_name: str  # 항상 "PreCompact" (항상 존재)
```

### NotificationInput

```python
from typing import Any, TypedDict

class NotificationInput(TypedDict):
    """Notification hook input structure."""
    session_id: str                    # 세션 고유 ID (항상 존재)
    transcript_path: str               # Transcript 파일 경로 (항상 존재)
    cwd: str                           # 현재 작업 디렉토리 (항상 존재)
    hook_event_name: str               # 항상 "Notification" (항상 존재)
    notification_type: str             # 알림 타입 (항상 존재)
    notification_data: dict[str, Any]  # 알림 데이터 (항상 존재)
```

## Tool Input Types

### BashToolInput

**Bash 도구의 input - command만 필수, 나머지는 선택**

```python
from typing import NotRequired, TypedDict

class BashToolInput(TypedDict):
    """Bash tool input structure.

    Only 'command' is REQUIRED.
    Other fields are OPTIONAL - key may not exist.
    """
    command: str                         # 필수 - 실행할 명령어 (항상 존재)
    description: NotRequired[str]        # 선택 - 명령어 설명 (키가 없을 수 있음)
    timeout: NotRequired[int]            # 선택 - 타임아웃 (밀리초) (키가 없을 수 있음)
    run_in_background: NotRequired[bool] # 선택 - 백그라운드 실행 여부 (키가 없을 수 있음)
```

**핵심 포인트:**
- ✅ `command`는 필수 - 항상 존재
- ✅ 나머지는 `NotRequired` - 키가 없을 수 있음
- ❌ `description: str | None` 사용 금지 - 키가 없을 수 있으므로

**접근 패턴:**
```python
def process_bash_input(tool_input: BashToolInput) -> None:
    # 필수 필드 - 직접 접근
    command = tool_input["command"]  # ✅ 타입: str

    # NotRequired 필드 - .get() 사용
    description = tool_input.get("description")  # ✅ 타입: str | None
    timeout = tool_input.get("timeout", 30000)   # ✅ 타입: int (기본값 제공)

    # in 연산자로 존재 확인
    if "run_in_background" in tool_input:
        run_bg = tool_input["run_in_background"]  # ✅ 타입: bool
```

### WriteToolInput

**Write 도구의 input - 모든 필드 필수**

```python
from typing import TypedDict

class WriteToolInput(TypedDict):
    """Write tool input structure.

    All fields are REQUIRED.
    """
    file_path: str  # 필수 - 작성할 파일 경로 (항상 존재)
    content: str    # 필수 - 파일에 작성할 내용 (항상 존재)
```

**접근 패턴:**
```python
def process_write_input(tool_input: WriteToolInput) -> None:
    # 모든 필드를 직접 접근
    file_path = tool_input["file_path"]  # ✅ 타입: str
    content = tool_input["content"]      # ✅ 타입: str
```

### EditToolInput

**Edit 도구의 input - 모든 필드 필수**

```python
from typing import TypedDict

class EditToolInput(TypedDict):
    """Edit tool input structure.

    All fields are REQUIRED.
    """
    file_path: str   # 필수 - 편집할 파일 경로 (항상 존재)
    old_string: str  # 필수 - 교체할 문자열 (항상 존재)
    new_string: str  # 필수 - 새 문자열 (항상 존재)
```

### EditOperation

**MultiEdit 도구의 단일 편집 작업**

```python
from typing import TypedDict

class EditOperation(TypedDict):
    """Single edit operation for MultiEdit tool.

    All fields are REQUIRED.
    """
    old_string: str  # 필수 - 교체할 문자열 (항상 존재)
    new_string: str  # 필수 - 새 문자열 (항상 존재)
```

### MultiEditToolInput

**MultiEdit 도구의 input - 모든 필드 필수**

```python
from typing import TypedDict

class MultiEditToolInput(TypedDict):
    """MultiEdit tool input structure.

    All fields are REQUIRED.
    """
    file_path: str              # 필수 - 편집할 파일 경로 (항상 존재)
    edits: list[EditOperation]  # 필수 - 편집 작업 목록 (항상 존재)
```

### NotebookEditToolInput

**NotebookEdit 도구의 input - 모든 필드 필수**

```python
from typing import TypedDict

class NotebookEditToolInput(TypedDict):
    """NotebookEdit tool input structure.

    All fields are REQUIRED.
    """
    notebook_path: str  # 필수 - Jupyter 노트북 경로 (항상 존재)
    new_source: str     # 필수 - 새 소스 코드 (항상 존재)
```

### TaskToolInput

**Task 도구의 input - 모든 필드 필수**

```python
from typing import TypedDict

class TaskToolInput(TypedDict):
    """Task tool input structure.

    All fields are REQUIRED.
    """
    description: str   # 필수 - 작업 설명 (3-5 단어) (항상 존재)
    prompt: str        # 필수 - Subagent에게 전달할 프롬프트 (항상 존재)
    subagent_type: str # 필수 - Subagent 타입 (항상 존재)
```

### ReadToolInput

**Read 도구의 input - file_path만 필수, 나머지는 선택**

```python
from typing import NotRequired, TypedDict

class ReadToolInput(TypedDict):
    """Read tool input structure.

    Only 'file_path' is REQUIRED.
    Other fields are OPTIONAL - key may not exist.
    """
    file_path: str            # 필수 - 읽을 파일 경로 (항상 존재)
    offset: NotRequired[int]  # 선택 - 시작 라인 번호 (키가 없을 수 있음)
    limit: NotRequired[int]   # 선택 - 읽을 라인 수 (키가 없을 수 있음)
```

### GrepToolInput

**Grep 도구의 input - pattern만 필수, 나머지는 선택**

```python
from typing import Literal, NotRequired, TypedDict

class GrepToolInput(TypedDict):
    """Grep tool input structure.

    Only 'pattern' is REQUIRED.
    Other fields are OPTIONAL - key may not exist.
    """
    pattern: str  # 필수 - 검색 패턴 (정규식) (항상 존재)

    # 선택 필드들 - 키가 없을 수 있음
    path: NotRequired[str]
    output_mode: NotRequired[Literal["content", "files_with_matches", "count"]]
    glob: NotRequired[str]
    type: NotRequired[str]
    multiline: NotRequired[bool]
```

### GlobToolInput

**Glob 도구의 input - pattern만 필수, path는 선택**

```python
from typing import NotRequired, TypedDict

class GlobToolInput(TypedDict):
    """Glob tool input structure.

    Only 'pattern' is REQUIRED.
    """
    pattern: str             # 필수 - Glob 패턴 (항상 존재)
    path: NotRequired[str]   # 선택 - 검색 디렉토리 (키가 없을 수 있음)
```

### Union Type: ToolInput

**모든 tool input의 Union 타입**

```python
from typing import Any

# 정확한 타입 정의
ToolInput = (
    BashToolInput |
    WriteToolInput |
    EditToolInput |
    MultiEditToolInput |
    NotebookEditToolInput |
    TaskToolInput |
    ReadToolInput |
    GrepToolInput |
    GlobToolInput |
    dict[str, Any]  # MCP 도구나 알려지지 않은 도구용 fallback
)

# PreToolUseInput에 적용
class PreToolUseInput(TypedDict):
    session_id: str
    tool_name: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    tool_input: ToolInput  # Union 타입 사용
```

## Tool Response Types

### Generic ToolResponse

**대부분의 도구가 반환하는 기본 구조**

```python
from typing import Any, NotRequired, TypedDict

class ToolResponse(TypedDict):
    """Generic tool response structure.

    Fields may or may not exist depending on the tool.
    """
    success: NotRequired[bool]                        # 선택 - 성공 여부
    type: NotRequired[str]                            # 선택 - 작업 타입 ("create", "edit" 등)
    filePath: NotRequired[str]                        # 선택 - 영향받은 파일 경로
    structuredPatch: NotRequired[dict[str, Any]]      # 선택 - 구조화된 diff 정보
    error: NotRequired[str]                           # 선택 - 에러 메시지
```

**핵심 포인트:**
- ⚠️ **모든 필드가 NotRequired** - 도구마다 반환 구조가 다름
- 항상 `.get()`으로 접근해야 함

### BashToolResponse

**Bash 도구의 응답 구조**

```python
from typing import NotRequired, TypedDict

class BashToolResponse(TypedDict):
    """Bash tool response structure."""
    stdout: str                  # 표준 출력 (대부분 있음)
    stderr: str                  # 표준 에러 (대부분 있음)
    exit_code: int               # 종료 코드 (대부분 있음)
    shell_id: NotRequired[str]   # 선택 - 백그라운드 실행 시 shell ID
```

## Utility Types

### 공통 패턴 TypedDict

```python
from typing import Literal, TypedDict

# 코드 이슈 정의
class CodeIssue(TypedDict):
    """Generic code issue structure."""
    type: str                # 이슈 타입
    issue_description: str   # 이슈 설명
    suggestion: str          # 수정 제안
    line: int                # 라인 번호
    column: int              # 컬럼 번호
    end_line: int            # 종료 라인
    end_column: int          # 종료 컬럼
    text: str                # 이슈가 있는 코드 텍스트

# 설정 상수 클래스
class Config:
    """Configuration constants for hooks."""
    EXIT_CODE_BLOCK_TOOL: int = 2
    DEFAULT_TEXT_TRUNCATION: int = 80
    LONG_TEXT_TRUNCATION: int = 120
```

## Type Guards

### Union 타입 좁히기

```python
from typing import TypeGuard

def is_write_tool_input(tool_input: dict[str, Any]) -> TypeGuard[WriteToolInput]:
    """Type guard for WriteToolInput."""
    return (
        isinstance(tool_input, dict) and
        "file_path" in tool_input and
        "content" in tool_input and
        isinstance(tool_input["file_path"], str) and
        isinstance(tool_input["content"], str)
    )

def is_bash_tool_input(tool_input: dict[str, Any]) -> TypeGuard[BashToolInput]:
    """Type guard for BashToolInput."""
    return (
        isinstance(tool_input, dict) and
        "command" in tool_input and
        isinstance(tool_input["command"], str)
    )

# 사용 예시
def process_tool_input(data: PreToolUseInput) -> None:
    tool_input = data["tool_input"]

    if is_write_tool_input(tool_input):
        # 타입: WriteToolInput
        file_path = tool_input["file_path"]  # ✅ 타입 안전
        content = tool_input["content"]
    elif is_bash_tool_input(tool_input):
        # 타입: BashToolInput
        command = tool_input["command"]  # ✅ 타입 안전
```

## 실전 예시: 완전한 Hook 구조

### PreToolUse Hook

```python
from __future__ import annotations

import json
import sys
from typing import Any, NoReturn, NotRequired, TypedDict


# Tool Input 정의
class BashToolInput(TypedDict):
    command: str
    description: NotRequired[str]
    timeout: NotRequired[int]
    run_in_background: NotRequired[bool]


class WriteToolInput(TypedDict):
    file_path: str
    content: str


# Hook Input 정의
class PreToolUseInput(TypedDict):
    session_id: str
    tool_name: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    tool_input: BashToolInput | WriteToolInput | dict[str, Any]


def main() -> None:
    """Main entry point."""
    try:
        execute_hook_pipeline()
    except Exception:
        sys.exit(0)


def execute_hook_pipeline() -> None:
    """Execute hook logic."""
    data = parse_input()

    if not should_process(data):
        sys.exit(0)

    # Process...
    sys.exit(0)


def parse_input() -> PreToolUseInput:
    """Parse stdin input."""
    input_raw = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(0)

    try:
        # 모든 필드가 필수이므로 직접 반환
        return json.loads(input_raw)
    except json.JSONDecodeError:
        sys.exit(0)


def should_process(data: PreToolUseInput) -> bool:
    """Check if should process."""
    # 필수 필드는 직접 접근
    tool_name = data["tool_name"]  # ✅ 타입: str
    tool_input = data["tool_input"]  # ✅ 타입: dict

    if tool_name == "Bash":
        # Bash 도구 체크
        if isinstance(tool_input, dict) and "command" in tool_input:
            command = tool_input["command"]  # ✅ 타입: str
            return bool(command)

    return False


if __name__ == "__main__":
    main()
```

## Best Practices

### 1. 필수 vs 선택 구분

```python
# ✅ CORRECT - Claude Code가 항상 보내는 필드
class PreToolUseInput(TypedDict):
    session_id: str  # NotRequired 사용 금지
    tool_name: str   # NotRequired 사용 금지

# ✅ CORRECT - 도구가 선택적으로 보내는 필드
class BashToolInput(TypedDict):
    command: str                 # 필수
    timeout: NotRequired[int]    # 선택 - 키가 없을 수 있음
```

### 2. 접근 패턴

```python
# ✅ CORRECT - 필수 필드는 직접 접근
session_id = data["session_id"]  # 타입: str

# ✅ CORRECT - NotRequired 필드는 .get() 사용
timeout = tool_input.get("timeout", 30000)  # 타입: int

# ❌ WRONG - 필수 필드에 .get() 사용 (불필요)
session_id = data.get("session_id")  # 타입: str | None (잘못됨)
```

### 3. NotRequired vs str | None

```python
# ✅ CORRECT - 키가 없을 수 있음
class BashToolInput(TypedDict):
    timeout: NotRequired[int]  # 키 자체가 없을 수 있음

# ❌ WRONG - 키는 있지만 값이 None (의미가 다름)
class BashToolInput(TypedDict):
    timeout: int | None  # 키는 항상 있어야 함
```

### 4. Union 타입 좁히기

```python
# ✅ CORRECT - 타입 가드 사용
if isinstance(tool_input, dict) and "command" in tool_input:
    command = tool_input["command"]  # 안전

# ✅ CORRECT - tool_name으로 구분
if tool_name == "Write":
    if isinstance(tool_input, dict):
        file_path = tool_input.get("file_path", "")
```

## 요약

1. **Hook Event Input은 모두 필수** - NotRequired 사용 금지
2. **Tool Input은 도구별로 다름** - 문서 확인 필수
3. **NotRequired는 "키가 없음"** - str | None과 다름
4. **필수 필드는 직접 접근** - .get() 불필요
5. **선택 필드는 .get()** - KeyError 방지
6. **타입 가드 활용** - Union 타입 좁히기

➡️ **[NotRequired 패턴 완전 가이드](notrequired-pattern-guide.md)** 참조
