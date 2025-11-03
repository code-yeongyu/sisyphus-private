# NotRequired vs str | None: 엄밀한 타입 패턴 가이드

TypedDict에서 선택적 필드를 다루는 두 가지 패턴의 **엄밀한 차이**를 이해하는 것은 타입 안전성에 매우 중요합니다.

## Table of Contents

1. [핵심 차이점](#핵심-차이점)
2. [NotRequired[T] - 키가 없을 수 있음](#notrequiredt---키가-없을-수-있음)
3. [T | None - 키는 있지만 값이 None](#t--none---키는-있지만-값이-none)
4. [NotRequired[T | None] - 조합 패턴](#notrequiredt--none---조합-패턴)
5. [실전 적용: Hook Input 타입 정의](#실전-적용-hook-input-타입-정의)
6. [잘못된 패턴과 올바른 패턴](#잘못된-패턴과-올바른-패턴)
7. [타입 가드 패턴](#타입-가드-패턴)

## 핵심 차이점

### 세 가지 패턴의 엄밀한 정의

```python
from typing import TypedDict, NotRequired

class Example(TypedDict):
    # 패턴 1: 필수 필드
    required_field: str

    # 패턴 2: 키가 없을 수 있음
    optional_field: NotRequired[str]

    # 패턴 3: 키는 있지만 값이 None일 수 있음
    nullable_field: str | None

    # 패턴 4: 키가 없을 수도 있고, 있어도 None일 수 있음
    optional_nullable_field: NotRequired[str | None]
```

### 동작 차이

```python
# 패턴 1: required_field - 반드시 존재해야 함
data1: Example = {
    "required_field": "value",
    "nullable_field": None,
}  # ✅ OK

data2: Example = {
    "nullable_field": None,
}  # ❌ ERROR: required_field 누락


# 패턴 2: NotRequired[str] - 키가 아예 없어도 됨
data3: Example = {
    "required_field": "value",
    "nullable_field": None,
    # optional_field가 아예 없음
}  # ✅ OK

data4: Example = {
    "required_field": "value",
    "nullable_field": None,
    "optional_field": "value",  # 있어도 됨
}  # ✅ OK

data5: Example = {
    "required_field": "value",
    "nullable_field": None,
    "optional_field": None,  # ❌ ERROR: NotRequired[str]이므로 None 불가
}


# 패턴 3: str | None - 키는 반드시 있어야 하고, 값은 str 또는 None
data6: Example = {
    "required_field": "value",
    # nullable_field가 없음
}  # ❌ ERROR: nullable_field 키가 반드시 있어야 함

data7: Example = {
    "required_field": "value",
    "nullable_field": None,  # 값이 None이어도 OK
}  # ✅ OK

data8: Example = {
    "required_field": "value",
    "nullable_field": "value",  # 값이 str이어도 OK
}  # ✅ OK


# 패턴 4: NotRequired[str | None] - 키가 없어도 되고, 있어도 None 가능
data9: Example = {
    "required_field": "value",
    "nullable_field": None,
    # optional_nullable_field가 아예 없음
}  # ✅ OK

data10: Example = {
    "required_field": "value",
    "nullable_field": None,
    "optional_nullable_field": None,  # 있어도 되고 None도 OK
}  # ✅ OK

data11: Example = {
    "required_field": "value",
    "nullable_field": None,
    "optional_nullable_field": "value",  # 있어도 되고 str도 OK
}  # ✅ OK
```

## NotRequired[T] - 키가 없을 수 있음

### 의미

**딕셔너리에 해당 키 자체가 존재하지 않을 수 있음**

### 사용 시기

1. API 요청에서 **선택적 파라미터**
2. 설정 파일에서 **선택적 설정값**
3. Hook input에서 **일부 도구만 가지는 파라미터**

### 예시: BashToolInput

```python
class BashToolInput(TypedDict):
    command: str                         # 필수 - 항상 있음
    description: NotRequired[str]        # 선택 - 키가 없을 수 있음
    timeout: NotRequired[int]            # 선택 - 키가 없을 수 있음
    run_in_background: NotRequired[bool] # 선택 - 키가 없을 수 있음
```

**왜 NotRequired인가?**

Claude Code가 Bash 도구를 호출할 때:
- `command`는 **항상** 전달됨
- `description`, `timeout`, `run_in_background`는 **경우에 따라** 전달 안 될 수 있음

```python
# 경우 1: 최소한의 입력
input1 = {
    "command": "ls -la"
}  # ✅ OK - 선택 필드들이 아예 없음

# 경우 2: 일부 선택 필드 포함
input2 = {
    "command": "ls -la",
    "timeout": 5000
}  # ✅ OK - description과 run_in_background가 없음

# 경우 3: 모든 필드 포함
input3 = {
    "command": "ls -la",
    "description": "List files",
    "timeout": 5000,
    "run_in_background": False
}  # ✅ OK - 모든 선택 필드 있음
```

### 접근 패턴

```python
def process_bash_input(tool_input: BashToolInput) -> None:
    # 필수 필드 - 바로 접근
    command = tool_input["command"]  # ✅ 타입: str

    # NotRequired 필드 - .get() 사용
    description = tool_input.get("description")  # ✅ 타입: str | None
    timeout = tool_input.get("timeout", 30000)   # ✅ 타입: int (기본값 제공)

    # ❌ 잘못된 접근
    # description = tool_input["description"]  # KeyError 발생 가능!
```

## T | None - 키는 있지만 값이 None

### 의미

**딕셔너리에 키는 반드시 존재하지만, 값이 None일 수 있음**

### 사용 시기

1. **명시적으로 "값이 없음"을 표현**해야 할 때
2. **nullable한 데이터베이스 필드**를 표현할 때
3. **API 응답에서 null을 반환**할 수 있는 필드

### 예시: API Response

```python
class UserResponse(TypedDict):
    id: str                    # 항상 있고 항상 str
    name: str                  # 항상 있고 항상 str
    email: str | None          # 키는 있지만 값이 None일 수 있음
    phone: str | None          # 키는 있지만 값이 None일 수 있음
```

**왜 str | None인가?**

API가 항상 `email`, `phone` 키를 반환하지만:
- 사용자가 이메일을 등록하지 않았으면 → `"email": None`
- 사용자가 이메일을 등록했으면 → `"email": "user@example.com"`

```python
# 경우 1: 이메일 없음
response1 = {
    "id": "123",
    "name": "John",
    "email": None,      # 키는 있지만 값이 None
    "phone": None       # 키는 있지만 값이 None
}  # ✅ OK

# 경우 2: 이메일 있음
response2 = {
    "id": "123",
    "name": "John",
    "email": "john@example.com",  # 값이 str
    "phone": None                 # 키는 있지만 값이 None
}  # ✅ OK

# 경우 3: 키 누락
response3 = {
    "id": "123",
    "name": "John"
    # email, phone 키가 없음
}  # ❌ ERROR - 키가 반드시 있어야 함
```

### 접근 패턴

```python
def process_user_response(response: UserResponse) -> None:
    # 필수 필드 - 바로 접근
    user_id = response["id"]    # ✅ 타입: str
    name = response["name"]     # ✅ 타입: str

    # str | None 필드 - 바로 접근 가능 (키는 항상 있음)
    email = response["email"]   # ✅ 타입: str | None
    phone = response["phone"]   # ✅ 타입: str | None

    # None 체크 후 사용
    if email is not None:
        print(f"Email: {email}")  # 타입: str

    # ❌ 잘못된 패턴
    # email = response.get("email")  # 불필요 - 키는 항상 있음
```

## NotRequired[T | None] - 조합 패턴

### 의미

**키가 없을 수도 있고, 있어도 None일 수 있음**

### 사용 시기

1. **매우 선택적인** 필드 (있을 수도, 없을 수도, None일 수도)
2. **부분 업데이트 API**에서 업데이트하지 않는 필드

### 예시: Partial Update

```python
class UserUpdateInput(TypedDict):
    # 업데이트하고 싶은 필드만 전달
    name: NotRequired[str]              # 업데이트 안 할 수도
    email: NotRequired[str | None]      # 업데이트 안 할 수도, None으로 설정할 수도
    phone: NotRequired[str | None]      # 업데이트 안 할 수도, None으로 설정할 수도
```

**왜 NotRequired[str | None]인가?**

3가지 경우가 가능:
1. **키가 없음** → 해당 필드는 업데이트하지 않음
2. **키가 있고 값이 str** → 해당 필드를 str 값으로 업데이트
3. **키가 있고 값이 None** → 해당 필드를 None(비움)으로 업데이트

```python
# 경우 1: 이름만 업데이트
update1 = {
    "name": "New Name"
    # email, phone 키가 없음 → 업데이트 안 함
}  # ✅ OK

# 경우 2: 이메일을 None으로 설정 (비움)
update2 = {
    "name": "New Name",
    "email": None  # 키는 있고 값이 None → 이메일을 비움
}  # ✅ OK

# 경우 3: 이메일을 새 값으로 업데이트
update3 = {
    "name": "New Name",
    "email": "new@example.com"  # 키는 있고 값이 str → 이메일 업데이트
}  # ✅ OK
```

### 접근 패턴

```python
def process_user_update(update: UserUpdateInput) -> None:
    # NotRequired[T] - .get() 사용
    name = update.get("name")  # 타입: str | None

    # NotRequired[str | None] - .get() 사용
    email = update.get("email")  # 타입: str | None | None = str | None

    # 3가지 케이스 구분
    if "email" in update:
        # 키가 있음
        email_value = update["email"]  # 타입: str | None
        if email_value is None:
            print("이메일을 비웁니다")
        else:
            print(f"이메일을 {email_value}로 업데이트합니다")
    else:
        # 키가 없음
        print("이메일은 업데이트하지 않습니다")
```

## 실전 적용: Hook Input 타입 정의

### Claude Code가 보내는 실제 Input 구조

Claude Code는 **항상 일관된 구조**로 input을 보냅니다:

#### PreToolUseInput - 엄밀한 정의

```python
from typing import Any, TypedDict

class PreToolUseInput(TypedDict):
    # 필수 필드 - 항상 존재
    session_id: str
    tool_name: str
    transcript_path: str
    cwd: str
    hook_event_name: str  # 항상 "PreToolUse"

    # tool_input도 항상 존재하지만, 타입이 다양함
    tool_input: dict[str, Any]  # 또는 구체적인 Union 타입
```

**왜 모두 필수인가?**

Claude Code는 **항상** 이 필드들을 포함해서 보냅니다. 키가 누락되는 경우는 없습니다.

#### PostToolUseInput - 엄밀한 정의

```python
from typing import Any, TypedDict

class PostToolUseInput(TypedDict):
    # 필수 필드 - 항상 존재
    session_id: str
    tool_name: str
    transcript_path: str
    cwd: str
    hook_event_name: str  # 항상 "PostToolUse"
    tool_input: dict[str, Any]
    tool_response: dict[str, Any]  # PostToolUse는 tool_response도 항상 있음
```

#### Tool-Specific Input - 엄밀한 정의

```python
from typing import NotRequired, TypedDict

# Write 도구 - 모든 필드 필수
class WriteToolInput(TypedDict):
    file_path: str  # 필수
    content: str    # 필수

# Edit 도구 - 모든 필드 필수
class EditToolInput(TypedDict):
    file_path: str   # 필수
    old_string: str  # 필수
    new_string: str  # 필수

# Bash 도구 - command만 필수, 나머지는 선택
class BashToolInput(TypedDict):
    command: str                         # 필수
    description: NotRequired[str]        # 선택 - 키가 없을 수 있음
    timeout: NotRequired[int]            # 선택 - 키가 없을 수 있음
    run_in_background: NotRequired[bool] # 선택 - 키가 없을 수 있음

# Task 도구 - 모든 필드 필수
class TaskToolInput(TypedDict):
    description: str   # 필수
    prompt: str        # 필수
    subagent_type: str # 필수

# Read 도구 - file_path만 필수, 나머지는 선택
class ReadToolInput(TypedDict):
    file_path: str            # 필수
    offset: NotRequired[int]  # 선택 - 키가 없을 수 있음
    limit: NotRequired[int]   # 선택 - 키가 없을 수 있음
```

### Union 타입으로 조합

```python
from typing import TypedDict

# 정확한 타입 정의
ToolInput = (
    WriteToolInput |
    EditToolInput |
    MultiEditToolInput |
    BashToolInput |
    TaskToolInput |
    ReadToolInput |
    dict[str, Any]  # MCP 도구나 알려지지 않은 도구용 fallback
)

class PreToolUseInput(TypedDict):
    session_id: str
    tool_name: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    tool_input: ToolInput  # 정확한 Union 타입
```

## 잘못된 패턴과 올바른 패턴

### ❌ 잘못된 패턴 1: 필수 필드를 NotRequired로

```python
# ❌ WRONG
class PreToolUseInput(TypedDict):
    session_id: NotRequired[str]      # 잘못됨 - 항상 있음
    tool_name: NotRequired[str]       # 잘못됨 - 항상 있음
    transcript_path: NotRequired[str] # 잘못됨 - 항상 있음
    cwd: NotRequired[str]             # 잘못됨 - 항상 있음
    hook_event_name: NotRequired[str] # 잘못됨 - 항상 있음
    tool_input: NotRequired[dict[str, Any]]  # 잘못됨 - 항상 있음
```

**문제점**: Claude Code가 **항상** 보내는 필드를 NotRequired로 표시하면:
- 타입 체커가 None 체크를 강제함 (불필요)
- 코드가 복잡해짐
- 실제 동작과 타입 정의가 불일치

### ✅ 올바른 패턴 1: 필수 필드는 필수로

```python
# ✅ CORRECT
class PreToolUseInput(TypedDict):
    session_id: str      # 항상 있음
    tool_name: str       # 항상 있음
    transcript_path: str # 항상 있음
    cwd: str             # 항상 있음
    hook_event_name: str # 항상 있음
    tool_input: dict[str, Any]  # 항상 있음
```

### ❌ 잘못된 패턴 2: NotRequired와 | None 혼동

```python
# ❌ WRONG - 의도와 맞지 않는 타입
class BashToolInput(TypedDict):
    command: str
    description: str | None  # 잘못됨 - 키가 항상 있어야 함
    timeout: int | None      # 잘못됨 - 키가 항상 있어야 함
```

**문제점**: 이렇게 정의하면 Claude Code가 **항상** `description` 키를 보내야 함:
```python
# 이렇게 보내야 함 (불필요하게 복잡)
{"command": "ls", "description": None, "timeout": None}

# 이렇게 보낼 수 없음 (하지만 실제로는 이렇게 보냄)
{"command": "ls"}  # ERROR - description, timeout 키 누락
```

### ✅ 올바른 패턴 2: 선택 필드는 NotRequired

```python
# ✅ CORRECT - Claude Code의 실제 동작과 일치
class BashToolInput(TypedDict):
    command: str
    description: NotRequired[str]  # 키가 없을 수 있음
    timeout: NotRequired[int]      # 키가 없을 수 있음
```

```python
# 이렇게 보낼 수 있음 (실제 동작)
{"command": "ls"}  # ✅ OK

# 이렇게도 보낼 수 있음
{"command": "ls", "timeout": 5000}  # ✅ OK
```

### ❌ 잘못된 패턴 3: .get()으로 필수 필드 접근

```python
# ❌ WRONG
def process_input(data: PreToolUseInput) -> None:
    # 필수 필드를 .get()으로 접근 (불필요)
    session_id = data.get("session_id")  # 타입: str | None (잘못됨)
    if session_id is None:  # 불필요한 None 체크
        return

    # session_id를 str로 사용
    print(session_id)
```

### ✅ 올바른 패턴 3: 필수 필드는 직접 접근

```python
# ✅ CORRECT
def process_input(data: PreToolUseInput) -> None:
    # 필수 필드를 직접 접근
    session_id = data["session_id"]  # 타입: str (정확함)

    # 바로 사용 가능
    print(session_id)
```

### ❌ 잘못된 패턴 4: NotRequired 필드를 직접 접근

```python
# ❌ WRONG
def process_bash_input(tool_input: BashToolInput) -> None:
    command = tool_input["command"]  # ✅ OK - 필수 필드

    # NotRequired 필드를 직접 접근 - KeyError 발생 가능!
    description = tool_input["description"]  # ❌ KeyError!
```

### ✅ 올바른 패턴 4: NotRequired 필드는 .get() 사용

```python
# ✅ CORRECT
def process_bash_input(tool_input: BashToolInput) -> None:
    command = tool_input["command"]  # ✅ OK - 필수 필드

    # NotRequired 필드는 .get() 사용
    description = tool_input.get("description")  # ✅ 타입: str | None
    timeout = tool_input.get("timeout", 30000)   # ✅ 기본값 제공
```

## 타입 가드 패턴

### 패턴 1: NotRequired 필드 체크

```python
def process_bash_input(tool_input: BashToolInput) -> None:
    command = tool_input["command"]

    # 방법 1: .get() + None 체크
    description = tool_input.get("description")
    if description is not None:
        print(f"Description: {description}")  # 타입: str

    # 방법 2: in 연산자 + 직접 접근
    if "timeout" in tool_input:
        timeout = tool_input["timeout"]  # 타입: int
        print(f"Timeout: {timeout}")
```

### 패턴 2: Union 타입 좁히기

```python
def process_tool_input(data: PreToolUseInput) -> None:
    tool_name = data["tool_name"]
    tool_input = data["tool_input"]

    # 타입 좁히기
    if tool_name == "Write":
        # 타입 가드: tool_input이 WriteToolInput임을 확인
        if isinstance(tool_input, dict) and "file_path" in tool_input and "content" in tool_input:
            file_path = tool_input["file_path"]  # 타입: str
            content = tool_input["content"]      # 타입: str
            # 처리...

    elif tool_name == "Bash":
        if isinstance(tool_input, dict) and "command" in tool_input:
            command = tool_input["command"]  # 타입: str
            # 처리...
```

### 패턴 3: TypedDict 타입 가드 함수

```python
from typing import TypeGuard

def is_write_tool_input(tool_input: dict[str, Any]) -> TypeGuard[WriteToolInput]:
    """Check if tool_input is WriteToolInput."""
    return (
        isinstance(tool_input, dict) and
        "file_path" in tool_input and
        "content" in tool_input and
        isinstance(tool_input["file_path"], str) and
        isinstance(tool_input["content"], str)
    )

def process_tool_input(data: PreToolUseInput) -> None:
    tool_input = data["tool_input"]

    if is_write_tool_input(tool_input):
        # 타입: WriteToolInput
        file_path = tool_input["file_path"]  # 타입: str
        content = tool_input["content"]      # 타입: str
```

## 요약: 의사결정 트리

```
필드를 정의할 때:

1. "이 필드가 항상 존재하는가?"
   YES → 필수 필드
   NO  → 2번으로

2. "이 필드의 값이 None일 수 있는가?"
   YES → T | None
   NO  → NotRequired[T]

3. "키가 없을 수도 있고, 있어도 None일 수 있는가?"
   YES → NotRequired[T | None]
```

### 빠른 참조표

| 상황 | 패턴 | 예시 |
|------|------|------|
| 항상 존재, 항상 값 있음 | `field: T` | `session_id: str` |
| 항상 존재, 값이 None 가능 | `field: T \| None` | `email: str \| None` |
| 키가 없을 수 있음, 있으면 값 있음 | `field: NotRequired[T]` | `timeout: NotRequired[int]` |
| 키가 없을 수 있음, 있어도 None 가능 | `field: NotRequired[T \| None]` | `email: NotRequired[str \| None]` |

### 접근 패턴 요약

| 패턴 | 접근 방법 | 타입 |
|------|----------|------|
| `field: T` | `data["field"]` | `T` |
| `field: T \| None` | `data["field"]` | `T \| None` |
| `field: NotRequired[T]` | `data.get("field")` | `T \| None` |
| `field: NotRequired[T \| None]` | `data.get("field")` | `T \| None` |

## Best Practices

1. **실제 API 동작에 맞춰 정의** - 추측하지 말고 실제 데이터 구조 확인
2. **NotRequired는 신중하게** - 정말로 키가 없을 수 있을 때만 사용
3. **필수 필드는 직접 접근** - `.get()` 사용 불필요
4. **선택 필드는 .get()** - KeyError 방지
5. **타입 가드 활용** - isinstance() + in 연산자로 타입 좁히기
6. **명확한 의도 표현** - NotRequired[T]와 T | None을 정확히 구분

이 가이드를 따르면 **타입 안전성이 높고 유지보수하기 쉬운** hook 코드를 작성할 수 있습니다.
