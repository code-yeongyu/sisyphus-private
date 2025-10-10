# 사용자의 최초 요청 (기록용)

TUI 모드에서 채팅 입력 부분(InputBar)의 메시지 전송이 작동하지 않는 문제를 분석하고 해결해야 합니다. 현재는 Enter를 눌러도 메시지가 실제로 전송되지 않고 입력창만 비워집니다.

## 사용자가 이후에 추가 요청한 내용들 (기록용)

- 메시지 큐잉과 supports_interactive를 지원하지 않는 droid agent와 같은 경우도 고려
- 전체 시스템의 메시지 전송 흐름 이해 필요
- UP 키로 현재 큐잉된 메시지를 편집하는 기능 추가
- 큐잉된 메시지를 화면에 렌더링하는 기능 추가
- Enter를 여러 번 누르면 메시지가 "\n"으로 구분되어 누적되어야 함
- Ctrl+S가 아니라 Agent가 available할 때 자동으로 전송되어야 함
- UP 키 동작 수정: 큐가 있으면 큐를 로드, 없으면 마지막 전송 메시지(_last_sent) 로드

# 작업 목표

- InputBar에서 Enter 키로 입력한 메시지가 ExecutionLoop으로 전달되도록 구현
- InputReadyEvent를 정의하고 TUI 앱에 핸들러 추가
- InputBar에 메시지 큐 기능 구현 (누적, 렌더링, UP 키 편집)
- ExecutionLoop이 interactive agent를 위해 InputBar 큐를 직접 읽도록 수정
- supports_interactive 플래그에 따라 다른 동작 방식 구현 (interactive vs non-interactive)

# 작업 배경

현재 TUI 구현은 다음과 같은 문제가 있습니다:

1. **InputBar**: Enter 키를 누르면 메시지를 strip()하고 입력창을 비우지만, 실제로 메시지를 어디로도 전송하지 않습니다 (TODO 주석으로 남아있음)
2. **TUI 앱**: `_send_stream`과 `_receive_stream`은 생성되지만 실제로 사용되지 않습니다 (제거 예정)
3. **ExecutionLoop**: 초기 프롬프트만 전송하고 사용자 입력을 받는 로직이 없습니다
4. **Agent 타입**: DroidAgent는 `supports_interactive = False`로 대화형 미지원, ClaudeAgent/OpenCodeAgent는 `supports_interactive = True`로 지원

이로 인해 사용자가 InputBar에 메시지를 입력하고 Enter를 눌러도 아무 일도 일어나지 않습니다.

# 작업 시작 여부
is_execution_started = TRUE

# 모든 목표 달성 여부
is_all_goals_accomplished = FALSE

# 병렬 실행 여부
parallel_requested = FALSE

# 현재 진행 중인 작업
- 4. 통합 테스트 및 검증

# 작업 계획

## 디테일 레벨
detail_level: balanced

## 핵심 설계 변경사항

### 기존 설계 (제거 예정)
```python
# app.py
self._send_stream: MemoryObjectSendStream[str] | None = None
self._receive_stream: MemoryObjectReceiveStream[str] | None = None

# UserMessageEvent로 메시지를 _send_stream에 전송
# get_input()이 _receive_stream에서 메시지를 수신
```

**문제점:**
- Enter 즉시 버퍼로 전송하면 UP 키로 편집 불가능
- 메시지가 버퍼에 들어가면 꺼낼 수 없음

### 새로운 설계
```python
# InputBar에 큐 저장
self._queued_message: str = ""  # 누적된 메시지
self._last_sent: str = ""       # 마지막 전송 메시지

# Enter → 큐에만 저장, InputReadyEvent 발생
# get_input() → InputBar.get_and_clear_queue() 직접 호출
# UP 키 → 큐 있으면 큐 로드, 없으면 _last_sent 로드
```

**장점:**
- ✅ UP 키로 큐 편집 가능
- ✅ `_send_stream` / `_receive_stream` 불필요
- ✅ Agent available = `get_input()` 대기 = 큐 자동 전송

## 메시지 큐잉 UX 정의

### 선택된 동작 방식: 메시지 누적 + 자동 전송
사용자 경험:
1. 사용자가 메시지 입력 후 **Enter** → 메시지가 `_queued_message`에 **누적 저장**
2. 큐잉된 메시지는 **InputBar 상단에 표시** (시각적 피드백)
3. **다시 Enter** → 기존 큐에 "\n"으로 구분하여 **추가 누적**
4. **Agent가 `ui.get_input()` 호출하면** → InputBar 큐를 직접 읽어가서 전송
5. **UP 키** → 큐가 있으면 큐를 입력창에 로드, 없으면 마지막 전송 메시지(_last_sent) 로드
6. 편집 후 **Enter** → 편집된 내용이 큐에 저장

**동작 예시**:
```
1. "Hello" 입력 → Enter → _queued_message = "Hello", 화면에 표시
2. "World" 입력 → Enter → _queued_message = "Hello\nWorld", 화면에 표시
3. Agent가 get_input() 호출 → "Hello\nWorld" 반환, _last_sent에 저장, 큐 비움
4. UP 키 → 큐 비어있으므로 _last_sent에서 "Hello\nWorld" 로드
5. "Hello\nWorld!" 로 수정 → Enter → _queued_message = "Hello\nWorld!", 화면에 표시
6. Agent가 get_input() 호출 → "Hello\nWorld!" 반환
```

**큐잉 표시 예시**:
```
┌─ Queued Message (will send when ready) ───┐
│ Hello                                      │
│ World                                      │
└────────────────────────────────────────────┘
[Press UP to edit queued message]
```

## 필요한 사전 지식

### Textual Message System
- Textual은 위젯 간 통신을 위해 Message 시스템 사용
- `Message` 클래스를 상속하여 커스텀 메시지 정의
- `self.post_message()`로 메시지 전송
- `on_{message_class_name}()`으로 핸들러 정의

### anyio Event
- `anyio.Event()`로 이벤트 생성
- `await event.wait()`: 이벤트가 set될 때까지 대기
- `event.set()`: 대기 중인 코루틴 깨우기
- Thread-safe한 비동기 신호 전달 메커니즘

### Agent Interactive Support
- `supports_interactive` 속성으로 대화형 지원 여부 표시
- DroidAgent: `False` (초기 프롬프트만 전송)
- ClaudeAgent/OpenCodeAgent: `True` (계속 입력 받음)

## 파일 구조 및 역할

```
sisyphus/
├── sisyphus/
│   ├── ui/
│   │   └── tui/
│   │       ├── app.py              # TUI 앱 (InputReadyEvent 핸들러)
│   │       └── components/
│   │           └── input_bar.py    # 입력창 위젯 (메시지 큐 관리)
│   ├── core/
│   │   └── loop.py                 # ExecutionLoop (수정 필요)
│   └── agents/
│       ├── base.py                 # Agent Protocol
│       ├── claude.py               # supports_interactive = True
│       ├── opencode.py             # supports_interactive = True
│       └── droid.py                # supports_interactive = False
```

## 맥락 이해를 위해 참고해야 할 파일들

### 1. sisyphus/ui/tui/components/input_bar.py (전체)
- **역할**: 사용자 메시지 입력 위젯
- **참고할 부분**: `on_input_submitted()` 메서드 (line 25-40)
- **현재 상태**:
  ```python
  def on_input_submitted(self, event: Input.Submitted) -> None:
      message = event.value.strip()
      if message:
          # TODO: UserMessageEvent 정의 후 활성화
          # self.app.post_message(UserMessageEvent(message))

          self.value = ""
          self._unsent_message = ""
  ```
- **문제점**: TODO 주석으로 메시지 전송 코드가 비활성화됨

### 2. sisyphus/ui/tui/app.py (line 20-51, 90-91, 103-106, 195-203)
- **역할**: TUI 앱 (UIProtocol 구현)
- **참고할 부분**:
  - Custom Message 정의 (line 20-51)
  - 메시지 스트림 생성 (line 90-91, 103-106) - **제거 예정**
  - `get_input()` 메서드 (line 195-203)
- **현재 상태**:
  ```python
  # line 90-91 (제거 예정)
  self._send_stream: MemoryObjectSendStream[str] | None = None
  self._receive_stream: MemoryObjectReceiveStream[str] | None = None

  # line 103-106 (제거 예정)
  (
      self._send_stream,
      self._receive_stream,
  ) = anyio.create_memory_object_stream(max_buffer_size=100)

  # line 195-203 (수정 필요)
  async def get_input(self) -> str | None:
      if self._receive_stream:
          return await self._receive_stream.receive()
      return None
  ```
- **변경 예정**: `_send_stream` / `_receive_stream` 제거, `get_input()`이 InputBar 큐를 직접 읽도록 수정

### 3. sisyphus/core/loop.py (전체)
- **역할**: Execute/Verify phase orchestration
- **참고할 부분**: `run()` 메서드 (line 54-110)
- **현재 상태**: 초기 프롬프트만 전송하고 사용자 입력을 받지 않음
- **주의사항**: `ui.get_input()` 호출 로직이 없음

### 4. sisyphus/agents/*.py
- **역할**: Agent implementations
- **참고할 부분**: `supports_interactive` 속성
  - droid.py line 25: `supports_interactive: bool = False`
  - claude.py line 29: `supports_interactive: bool = True`
  - opencode.py line 25: `supports_interactive: bool = True`

### 5. sisyphus/ui/tui/layouts/main.py (line 12-26)
- **역할**: TUI 레이아웃 구성
- **참고할 부분**: `compose_main_layout()` 함수
- **현재 상태**:
  ```python
  def compose_main_layout() -> ComposeResult:
      """메인 레이아웃 구성."""
      yield Header()
      yield Container(
          VerticalScroll(ChatLog(), id="chat-scroll"),
          Container(StatusPanel(), id="status-container"),
          InputBar(),  # line 24
      )
      yield Footer()
  ```
- **확인 사항**: InputBar를 단순히 위젯으로 yield하고 있으므로, Vertical 컨테이너로 변경해도 호환됨

## 구현 세부사항

### 구현 전략

1. **InputReadyEvent 정의** (app.py)
   - 기존 Custom Message들과 같은 패턴으로 정의
   - InputBar에서 Enter를 눌렀을 때 발생

2. **InputReadyEvent 핸들러 추가** (app.py)
   - `on_input_ready_event()` 메서드 구현
   - `_input_ready_event.set()`로 대기 중인 `get_input()` 깨우기

3. **InputBar 큐 기능 구현** (input_bar.py)
   - `_queued_message`: 누적된 메시지
   - `_last_sent`: 마지막 전송 메시지
   - `get_and_clear_queue()`: 큐를 읽고 비우는 메서드
   - `_update_queue_display()`: 큐 렌더링
   - UP 키: 큐 또는 _last_sent 로드

4. **get_input() 수정** (app.py)
   - InputBar 큐를 직접 읽도록 변경
   - 큐가 비어있으면 `_input_ready_event.wait()` 대기

5. **ExecutionLoop 수정** (loop.py)
   - `supports_interactive` 체크 추가
   - Interactive agent인 경우 사용자 입력 대기 루프 구현
   - Non-interactive agent인 경우 기존 방식 유지

### 주의사항

- ExecutionLoop의 기존 동작을 깨뜨리지 않도록 `supports_interactive` 체크 필수
- Thread-safe한 메시지 전송 유지 (기존 패턴 따르기)
- DroidAgent 같은 non-interactive agent는 여전히 초기 프롬프트만 받도록
- `_send_stream` / `_receive_stream` 제거 시 관련 코드 모두 정리

## 프로젝트 커밋 메시지 스타일

Recent commits:
```
de2acb2 now tui works
212fa0e fix: handle OSError when checking if prompt string is a file path
1526138 feat: embed default prompts as Python constants to avoid path dependency
599fc51 test: verify TUI and CLI modes work correctly - all goals accomplished
d16cd89 docs: update Phase 2 checkboxes - all tasks completed
```

패턴: `<type>: <subject>` (feat, fix, test, docs)
- feat: 새로운 기능 추가
- fix: 버그 수정
- test: 테스트 관련
- docs: 문서 관련
- refactor: 리팩토링

# TODOs

- [x] 1. InputReadyEvent 정의 및 TUI 앱 수정 (sisyphus/ui/tui/app.py)
  - [x] 1.1 구현: InputReadyEvent 클래스 정의
    ```python
    # app.py 상단, 다른 Message 클래스들과 함께 (line 20-51 근처)
    class InputReadyEvent(Message):
        """사용자가 Enter를 눌러 입력이 준비되었음을 알림."""
        pass
    ```
    - 현재: InputReadyEvent가 정의되지 않음
    - 변경:
      1. UpdateStatusMessage, ShowAgentMessage와 같은 패턴으로 정의
      2. line 20-51 근처 (다른 Message 클래스들 바로 뒤)에 배치
      3. 별도 필드 필요 없음 (이벤트 자체가 신호)
  - [x] 1.2 구현: _input_ready_event 속성 추가
    ```python
    # TUI.__init__() 메서드 (line 83-92)
    def __init__(self) -> None:
        super().__init__()
        self.ctrl_c_count = 0
        self.last_ctrl_c_time: datetime | None = None
        self.shutdown_event = anyio.Event()
        self.ready_event = anyio.Event()
        self._input_ready_event = anyio.Event()  # 추가
        self._initialized = False
    ```
    - 현재: `_input_ready_event` 없음
    - 변경: anyio.Event() 추가하여 InputBar Enter 신호 대기
  - [x] 1.3 구현: InputReadyEvent 핸들러 추가
    ```python
    # TUI 클래스 내부, 다른 on_* 핸들러들과 함께
    async def on_input_ready_event(self, message: InputReadyEvent) -> None:
        """InputBar에서 Enter 눌렀을 때 get_input() 깨우기."""
        self._input_ready_event.set()
    ```
    - 현재: 핸들러 없음
    - 변경: `_input_ready_event.set()`로 대기 중인 `get_input()` 깨우기
  - [x] 1.4 구현: _send_stream / _receive_stream 제거
    ```python
    # line 90-91 제거
    # self._send_stream: MemoryObjectSendStream[str] | None = None
    # self._receive_stream: MemoryObjectReceiveStream[str] | None = None

    # line 103-106 제거
    # (
    #     self._send_stream,
    #     self._receive_stream,
    # ) = anyio.create_memory_object_stream(max_buffer_size=100)

    # line 139-142 (_safe_shutdown 메서드) 제거
    # if self._send_stream:
    #     await self._send_stream.aclose()
    # if self._receive_stream:
    #     await self._receive_stream.aclose()
    ```
    - 현재: `_send_stream` / `_receive_stream` 사용하지 않지만 생성됨
    - 변경: 완전히 제거 (더 이상 필요 없음)
  - [x] 1.5 구현: get_input() 메서드 수정
    ```python
    # line 195-203
    async def get_input(self) -> str | None:
        """InputBar 큐에서 메시지를 가져옴.

        큐가 비어있으면 다음 Enter를 대기합니다.
        Agent가 이 메서드를 호출하면 자동으로 큐잉된 메시지를 전송합니다.

        Returns:
            큐잉된 메시지 또는 None (종료 시)
        """
        while True:
            try:
                input_bar = self.query_one(InputBar)
                queued = input_bar.get_and_clear_queue()
                if queued:
                    return queued

                # 큐 비어있으면 다음 Enter 대기
                await self._input_ready_event.wait()
                self._input_ready_event = anyio.Event()  # 리셋
            except Exception as e:
                self.log.error(f"Failed to get input: {e}")
                return None
    ```
    - 현재: `_receive_stream.receive()` 사용
    - 변경:
      1. InputBar의 `get_and_clear_queue()` 직접 호출
      2. 큐 있으면 즉시 반환 (자동 전송)
      3. 큐 없으면 `_input_ready_event.wait()` 대기
      4. Event 리셋하여 다음 Enter 대기 가능하도록
  - [x] 1.6 린트 및 타입 체크
    - [x] `ruff check sisyphus/ui/tui/app.py`
    - [x] `basedpyright sisyphus/ui/tui/app.py`
  - [x] 1.7 커밋: `git add sisyphus/ui/tui/app.py && git commit -m "feat: add InputReadyEvent and refactor get_input to read InputBar queue directly"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] InputReadyEvent 클래스가 다른 Message 클래스들과 같은 위치에 정의되었는가?
    - [x] _input_ready_event가 TUI.__init__()에 추가되었는가?
    - [x] on_input_ready_event 핸들러가 올바르게 구현되었는가?
    - [x] _send_stream / _receive_stream 관련 코드가 완전히 제거되었는가?
    - [x] get_input()이 InputBar.get_and_clear_queue()를 호출하는가?
    - [x] get_input()이 큐 없을 때 _input_ready_event.wait()를 호출하는가?
    - [x] Event를 리셋하여 다음 대기가 가능한가?
    - [x] 타입 체크와 린트가 통과하는가?

- [x] 2. InputBar에서 메시지 큐잉 및 렌더링 구현 (sisyphus/ui/tui/components/input_bar.py)
  - [x] 2.1 구현: InputBar 클래스에 큐 표시 위젯 추가
    ```python
    # input_bar.py 파일 상단 import 섹션
    from textual.app import ComposeResult
    from textual.containers import Vertical
    from textual.events import Key
    from textual.widgets import Input, Static

    class InputBar(Vertical):  # Input이 아니라 Vertical 컨테이너로 변경
        """메시지 입력창 위젯.

        Input 위젯과 큐잉 상태 표시를 포함하는 컨테이너입니다.
        Enter 키로 메시지를 큐에 추가하고, Agent가 get_input() 호출하면 전달됩니다.
        """

        def __init__(self) -> None:
            """InputBar 위젯 초기화."""
            super().__init__(id="input-container")
            self._queued_message: str = ""
            self._last_sent: str = ""  # 마지막 전송 메시지 (UP 키용)
            self._input_widget: Input | None = None
            self._queue_display: Static | None = None

        def compose(self) -> ComposeResult:
            """위젯 구성."""
            self._queue_display = Static("", id="queue-display", classes="queue-hint")
            self._input_widget = Input(
                placeholder="Type and press Enter to queue (UP to edit)",
                id="input-bar",
            )
            yield self._queue_display
            yield self._input_widget
    ```
    - 현재: InputBar가 Input을 직접 상속, 큐 표시 없음
    - 변경:
      1. InputBar를 Vertical 컨테이너로 변경 (큐 표시 + 입력창 포함)
      2. _queued_message: 현재 큐잉 중인 메시지
      3. _last_sent: 마지막 전송 메시지 (UP 키로 편집용)
      4. _queue_display Static 위젯 추가 (큐 상태 표시)
      5. _input_widget Input 위젯 추가
  - [x] 2.1.5 app.py에서 InputBar 사용 부분 확인 및 수정
    - **주의**: InputBar가 Input에서 Vertical 컨테이너로 변경되므로, app.py에서 InputBar를 사용하는 부분을 확인해야 합니다.
    - app.py의 `compose_main_layout()` 또는 다른 부분에서 InputBar 사용 확인
    - InputBar의 속성 접근이 필요한 부분 확인 (예: `.value`, `.focus()` 등)
    - Vertical 컨테이너로 변경되었으므로, 필요 시 `._input_widget`을 통해 Input 위젯에 접근하도록 수정
    - 예시: `input_bar.value` → `input_bar._input_widget.value`
    - 예시: `input_bar.focus()` → `input_bar._input_widget.focus()`
    - **확인 필요**: sisyphus/ui/tui/layouts/main.py에서 InputBar를 어떻게 사용하는지 확인
  - [x] 2.2 구현: Enter 키로 메시지 큐에 누적 및 InputReadyEvent 발생
    ```python
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter 키 입력 시 메시지를 큐에 추가.

        Args:
            event: Input.Submitted 이벤트 객체
        """
        message = event.value.strip()
        if message:
            # 큐에 메시지 누적 (개행으로 구분)
            if self._queued_message:
                self._queued_message += "\n" + message
            else:
                self._queued_message = message

            # 입력창 비우기
            if self._input_widget:
                self._input_widget.value = ""

            # 큐 표시 업데이트
            self._update_queue_display()

            # InputReadyEvent 발생 (get_input() 깨우기)
            from sisyphus.ui.tui.app import InputReadyEvent
            self.app.post_message(InputReadyEvent())
    ```
    - 현재: TODO 주석으로 비활성화됨
    - 변경:
      1. 메시지를 큐에 **누적** (append with "\n")
      2. 입력창 비우기
      3. 큐 표시 업데이트 호출
      4. **InputReadyEvent 발생** (get_input() 깨우기)
  - [x] 2.3 구현: 큐 표시 업데이트 메서드
    ```python
    def _update_queue_display(self) -> None:
        """큐잉된 메시지 표시를 업데이트."""
        if self._queue_display:
            if self._queued_message:
                lines = self._queued_message.split("\n")
                preview = "\n".join(lines[:3])  # 최대 3줄만 표시
                if len(lines) > 3:
                    preview += f"\n... ({len(lines) - 3} more lines)"
                self._queue_display.update(
                    f"[Queue] {preview}\n[Press UP to edit]"
                )
                self._queue_display.display = True
            else:
                self._queue_display.update("")
                self._queue_display.display = False
    ```
    - 현재: 큐 표시 로직 없음
    - 변경:
      1. 큐가 있으면 최대 3줄까지 preview 표시
      2. 나머지 줄 수 표시
      3. 큐가 비어있으면 숨김
  - [x] 2.4 구현: UP 키로 큐 또는 마지막 전송 메시지 로드
    ```python
    def on_key(self, event: Key) -> None:
        """키 이벤트 처리.

        Args:
            event: Key 이벤트 객체
        """
        if event.key == "up":
            # 큐 있으면 큐 로드, 없으면 _last_sent 로드
            if self._queued_message:
                # 큐를 입력창에 로드
                if self._input_widget:
                    self._input_widget.value = self._queued_message
                # 큐 비우기
                self._queued_message = ""
                self._update_queue_display()
            elif self._last_sent:
                # 마지막 전송 메시지 로드
                if self._input_widget:
                    self._input_widget.value = self._last_sent
    ```
    - 현재: UP 키 로직 있지만 _unsent_message만 사용
    - 변경:
      1. UP 키 → 큐 있으면 큐 로드 (편집 가능)
      2. 큐 없으면 _last_sent에서 마지막 전송 메시지 로드
      3. 큐 로드 시 큐 비우기 (편집 상태로 전환)
  - [x] 2.5 구현: get_and_clear_queue() 메서드 추가
    ```python
    def get_and_clear_queue(self) -> str | None:
        """큐잉된 메시지를 반환하고 큐를 비움.

        Returns:
            큐잉된 메시지 또는 None (큐 비어있을 때)
        """
        if self._queued_message:
            msg = self._queued_message
            self._queued_message = ""
            self._last_sent = msg  # 마지막 전송 메시지 저장
            self._update_queue_display()
            return msg
        return None
    ```
    - 현재: 메서드 없음
    - 변경:
      1. 큐 있으면 반환하고 비우기
      2. _last_sent에 저장 (UP 키용)
      3. 큐 표시 업데이트
      4. TUI.get_input()에서 호출됨
  - [x] 2.6 구현: CSS 스타일 수정 (sisyphus/ui/tui/app.py의 CSS 섹션)
    ```python
    # TUI 클래스의 CSS 수정 (line 61-76)
    # 기존 #input-bar 스타일 (line 72-75)을 다음으로 대체:
    CSS = """
    #chat-scroll {
        height: 70%;
        border: solid $primary;
    }

    #status-container {
        height: 20%;
        border: solid $secondary;
    }

    #input-container {
        height: 10%;
        border: solid $accent;
    }

    #queue-display {
        height: auto;
        color: $text-muted;
        background: $panel;
        padding: 0 1;
        text-style: italic;
    }

    #input-bar {
        height: 1;
    }
    """
    ```
    - 현재: `#input-bar` 스타일이 line 72-75에 있음 (height: 10%)
    - 변경:
      1. 기존 `#input-bar` (line 72-75) 삭제
      2. `#input-container` 스타일 추가 (Vertical 컨테이너, height: 10%)
      3. `#queue-display` 스타일 추가 (큐 표시)
      4. `#input-bar` 스타일 추가 (실제 입력창, height: 1)
  - [x] 2.7 린트 및 타입 체크
    - [x] `ruff check sisyphus/ui/tui/components/input_bar.py sisyphus/ui/tui/app.py`
    - [x] `basedpyright sisyphus/ui/tui/components/input_bar.py sisyphus/ui/tui/app.py`
  - [x] 2.8 커밋: `git add sisyphus/ui/tui/components/input_bar.py sisyphus/ui/tui/app.py && git commit -m "feat: implement message queuing with visual feedback and UP key editing"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] InputBar가 Vertical 컨테이너로 변경되었는가?
    - [x] _queue_display Static 위젯이 추가되었는가?
    - [x] _last_sent 속성이 추가되었는가?
    - [x] Enter 키를 누르면 메시지가 큐에 누적되는가?
    - [x] 큐잉된 메시지가 화면에 표시되는가?
    - [x] 여러 번 Enter를 누르면 "\n"으로 구분되어 누적되는가?
    - [x] Enter 키를 누르면 InputReadyEvent가 발생하는가?
    - [x] get_and_clear_queue()가 큐를 반환하고 _last_sent에 저장하는가?
    - [x] UP 키를 누르면 큐 또는 _last_sent가 입력창에 로드되는가?
    - [x] CSS 스타일이 올바르게 적용되었는가?
    - [x] 타입 체크와 린트가 통과하는가?

- [x] 3. ExecutionLoop에 interactive agent 지원 추가 (sisyphus/core/loop.py)
  - [ ] 3.1 구현: loop.py 상단에 anyio import 추가
    ```python
    # loop.py 파일 상단 import 섹션 (line 1-10 근처)
    import anyio  # 추가 (ClosedResourceError, EndOfStream 사용을 위해)
    # ... (나머지 기존 import 유지)
    ```
    - 현재: anyio import가 없음 (확인 필요)
    - 변경: anyio import 추가하여 예외 클래스 사용 가능하게 함
  - [ ] 3.2 구현: supports_interactive 체크 및 분기 로직 추가
    ```python
    # run() 메서드 전체를 다음과 같이 수정 (line 54-110)
    async def run(
        self,
        execute_prompt: str | None,
        execute_extra: str | None = None,
        verify_prompt: str | None = None,
        verify_extra: str | None = None,
    ) -> None:
        """Run the execution loop.

        Args:
            execute_prompt: Execute phase prompt (None = use DEFAULT_EXECUTE_PROMPT)
            execute_extra: Extra prompt for execute phase
            verify_prompt: Verify phase prompt (None = use DEFAULT_VERIFY_PROMPT)
            verify_extra: Extra prompt for verify phase

        Notes:
            - Execute agent can resume previous session
            - Verify agent always starts new session (independent verification)
            - Loop continues until task_validator confirms completion (if provided)
        """
        await self.ui.initialize()

        actual_execute_prompt = execute_prompt if execute_prompt is not None else DEFAULT_EXECUTE_PROMPT

        # Interactive agent 체크
        if hasattr(self.execute_agent, 'supports_interactive') and self.execute_agent.supports_interactive:
            # Interactive mode: 사용자 입력 대기
            await self._run_interactive_mode(actual_execute_prompt, execute_extra)
        else:
            # Non-interactive mode: 기존 방식 (초기 프롬프트만)
            await self._run_non_interactive_mode(actual_execute_prompt, execute_extra, verify_prompt, verify_extra)

        await self.ui.close()
    ```
    - 현재: 모든 agent를 non-interactive로 처리
    - 변경:
      1. hasattr로 supports_interactive 속성 안전하게 체크
      2. True면 _run_interactive_mode 호출
      3. False면 _run_non_interactive_mode 호출 (기존 로직)
  - [ ] 3.3 구현: _run_interactive_mode 메서드 추가 (예외 처리 포함)
    ```python
    async def _run_interactive_mode(
        self,
        execute_prompt: str,
        execute_extra: str | None = None,
    ) -> None:
        """Interactive mode: continuously get user input and send to agent.

        Args:
            execute_prompt: 초기 실행 프롬프트
            execute_extra: 추가 실행 컨텍스트
        """
        # Initialize agent
        await self.execute_agent.initialize()
        agent_type = type(self.execute_agent).__name__.lower().replace("agent", "")
        session_id = await self.session_store.get_session(agent_type)

        self.execute_logger = self.logger_factory.create_logger(agent_type, session_id)
        self.execute_logger.info("Interactive mode starting")

        actual_session_id = await self.execute_agent.start_session(session_id)
        await self.session_store.save_session(agent_type, actual_session_id)

        # Send initial prompt
        final_prompt = await self.prompt_resolver.resolve(execute_prompt, execute_extra)
        await self.execute_agent.send(final_prompt)

        # Stream initial response
        stream = self.execute_agent.stream()
        async for message in stream:
            await self.ui.show_message(message, source="execute")

        # Interactive loop: wait for user input
        try:
            while True:
                try:
                    user_input = await self.ui.get_input()
                    if user_input is None:
                        break  # UI closed
                except (anyio.ClosedResourceError, anyio.EndOfStream):
                    # Stream이 닫혔으므로 정상 종료
                    self.execute_logger.info("Input stream closed, exiting interactive mode")
                    break

                await self.execute_agent.send(user_input)
                stream = self.execute_agent.stream()
                async for message in stream:
                    await self.ui.show_message(message, source="execute")
        finally:
            await self.execute_agent.close()
    ```
    - 현재: 메서드 없음
    - 변경:
      1. Interactive agent를 위한 사용자 입력 대기 루프 구현
      2. **예외 처리 추가**: anyio.ClosedResourceError, anyio.EndOfStream 감지
      3. **finally 블록**: agent 리소스 정리 보장
      4. **타입 힌트 완성**: 모든 파라미터와 반환 타입 명시
  - [ ] 3.4 구현: _run_non_interactive_mode 메서드 추가 (기존 로직 이동)
    ```python
    # 기존 run() 메서드의 line 78-109를 그대로 복사하여 새 메서드로 이동
    async def _run_non_interactive_mode(
        self,
        execute_prompt: str,
        execute_extra: str | None = None,
        verify_prompt: str | None = None,
        verify_extra: str | None = None,
    ) -> None:
        """Non-interactive mode: existing behavior (initial prompt only).

        Args:
            execute_prompt: Execute phase prompt
            execute_extra: Extra prompt for execute phase
            verify_prompt: Verify phase prompt
            verify_extra: Extra prompt for verify phase
        """
        iteration = 0
        while True:
            iteration += 1

            await self.ui.show_status(f"[Iteration {iteration}] Starting Execute phase...")
            await self._execute_phase(execute_prompt, execute_extra)

            if self.verify_agent:
                actual_verify_prompt = verify_prompt if verify_prompt is not None else DEFAULT_VERIFY_PROMPT
                await self.ui.show_status(f"[Iteration {iteration}] Starting Verify phase...")
                await self._verify_phase(actual_verify_prompt, verify_extra)

            if self.task_validator is None:
                await self.ui.show_status("Execution complete (no task validator)")
                break

            # 기존 run() 메서드의 line 94-108을 그대로 복사
            content = self.task_validator.read_content()
            goals_accomplished = self.task_validator.check_all_goals_accomplished(content)
            checkboxes_completed = self.task_validator.check_all_checkboxes_completed(content)

            if goals_accomplished and checkboxes_completed:
                await self.ui.show_status("All tasks completed! Exiting loop.")
                break

            uncompleted = self.task_validator.extract_uncompleted_checkboxes(content)
            total = self.task_validator.count_total_checkboxes(content)
            completed = self.task_validator.count_completed_checkboxes(content)

            await self.ui.show_status(
                f"Progress: {completed}/{total} completed. {len(uncompleted)} tasks remaining. Continuing..."
            )
    ```
    - 현재: run() 메서드 안에 직접 구현됨 (line 78-109)
    - 변경:
      1. 별도 메서드로 분리하여 기존 로직 완전히 유지
      2. **line 94-108의 task validation 로직 전체 복사** (생략 없이)
      3. 타입 힌트 및 docstring 완성
  - [ ] 3.5 린트 및 타입 체크
    - [ ] `ruff check sisyphus/core/loop.py`
    - [ ] `basedpyright sisyphus/core/loop.py`
  - [ ] 3.6 커밋: `git add sisyphus/core/loop.py && git commit -m "feat: add interactive agent support to ExecutionLoop"`
  - [ ] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [ ] run() 메서드가 supports_interactive를 체크하는가?
    - [ ] _run_interactive_mode가 사용자 입력 대기 루프를 구현하는가?
    - [ ] _run_non_interactive_mode가 기존 로직을 유지하는가?
    - [ ] hasattr로 supports_interactive 존재 여부를 안전하게 체크하는가?
    - [ ] anyio import가 추가되었는가?
    - [ ] 예외 처리가 올바르게 구현되었는가?
    - [ ] 타입 체크와 린트가 통과하는가?

- [x] 4. 통합 테스트 및 검증
  - [ ] 4.1 수동 테스트: Terminalcp (ClaudeAgent)로 TUI 모드 실행
    ```
    # TUI 모드로 실행
    uv run sisyphus
    ```
    - 예상 동작:
      1. TUI 화면이 정상 표시됨
      2. InputBar와 큐 표시 영역이 분리되어 표시됨
      3. 플레이스홀더에 "Type and press Enter to queue (UP to edit)" 표시됨
  - [ ] 4.2 terminalcp 로 직접 테스트 (terminalcp)
    - [ ] 4.2.1 테스트 1: 메시지 큐잉 기본 동작
      ```
      # terminalcp로 TUI 시작
      # "Hello" 입력 → Enter
      # stdout에서 "[Queue] Hello" 표시 확인
      # stdout에서 "[Press UP to edit]" 힌트 확인
      ```
      - [ ] 큐 표시에 "Hello" 표시되는가?
      - [ ] 큐 힌트가 표시되는가?
      - [ ] 입력창이 비워지는가?
    - [ ] 4.2.2 테스트 2: 메시지 누적 (Enter 여러 번)
      ```
      # "Hello" 입력 → Enter
      # "World" 입력 → Enter
      # stdout에서 "Hello\nWorld" 또는 "Hello" 와 "World" 모두 표시 확인
      ```
      - [ ] 첫 번째 메시지 "Hello"가 큐에 저장되는가?
      - [ ] 두 번째 메시지 "World"가 누적되는가?
      - [ ] 큐 표시에 "\n"으로 구분되어 표시되는가?
    - [ ] 4.2.3 테스트 3: UP 키로 큐 편집 및 취소
      ```
      # "Hello" 입력 → Enter (큐잉됨)
      # "World" 입력 → Enter (누적됨)
      # UP 키 입력 (stdin: "\u001b[A")
      # stdout에서 입력창에 "Hello\nWorld" 로드 확인
      # stdout에서 큐 표시가 사라짐 확인
      ```
      - [ ] UP 키를 누르면 큐가 입력창으로 이동하는가?
      - [ ] 큐 표시가 사라지는가?
      - [ ] 입력창에 "\n" 포함된 전체 텍스트가 로드되는가?
    - [ ] 4.2.4 테스트 4: 큐 편집 후 재저장
      ```
      # "Hello" 입력 → Enter → UP 키
      # 입력창 내용을 "Hello!" 로 수정
      # Enter
      # stdout에서 "[Queue] Hello!" 표시 확인
      ```
      - [ ] 편집된 내용이 다시 큐에 저장되는가?
      - [ ] 큐 표시가 다시 나타나는가?
    - [ ] 4.2.5 테스트 5: 자동 전송 확인 (Agent가 ready일 때)
      ```
      # "Test message" 입력 → Enter (큐잉됨)
      # Agent 초기 응답 완료 대기
      # stdout에서 ChatLog에 "Test message" 전송 확인
      # stdout에서 큐 표시가 사라짐 확인
      # stdout에서 Agent 응답 표시 확인
      ```
      - [ ] Agent가 ready 상태가 되면 큐가 자동 전송되는가?
      - [ ] 큐 표시가 비워지는가?
      - [ ] Agent 응답이 ChatLog에 표시되는가?
    - [ ] 4.2.6 테스트 6: UP 키로 마지막 전송 메시지 로드
      ```
      # "First" 입력 → Enter → Agent 응답 대기
      # 큐 비워진 상태에서 UP 키
      # stdout에서 입력창에 "First" 로드 확인
      ```
      - [ ] 큐가 비어있을 때 UP 키를 누르면 _last_sent가 로드되는가?
      - [ ] 로드된 메시지를 수정할 수 있는가?
    - [ ] 4.2.7 테스트 7: 여러 번 연속 메시지 전송
      ```
      # "Message 1" → Enter → Agent 응답 대기
      # "Message 2" → Enter → Agent 응답 대기
      # "Message 3" → Enter → Agent 응답 대기
      # stdout에서 3개 메시지 모두 Agent에게 전달되고 응답 확인
      ```
      - [ ] 연속으로 여러 메시지를 보낼 수 있는가?
      - [ ] 각 메시지마다 Agent 응답이 오는가?
  - [ ] 4.3 Non-interactive agent 테스트
    ```
    # DroidAgent로 실행 (설정 변경 필요)
    # 또는 CLI 모드 실행
    ```
    - 예상 동작:
      1. 초기 프롬프트만 전송
      2. InputBar 비활성화 또는 무시됨
      3. 기존 Execute/Verify 루프 정상 작동
  - [ ] 4.4 린트 및 타입 체크 (전체)
    - [ ] `ruff check sisyphus/`
    - [ ] `basedpyright sisyphus/`
  - [ ] 4.5 기존 테스트 실행
    - [ ] `uv run pytest sisyphus/ui/tui/ -xvs`
  - [ ] 4.6 커밋: `git add . && git commit -m "test: verify interactive user input works in TUI mode"`
  - [ ] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [ ] TUI 모드가 정상적으로 시작되는가?
    - [ ] InputBar에 메시지 입력 후 Enter를 누르면 큐에 저장되는가?
    - [ ] 큐잉된 메시지가 화면에 표시되는가?
    - [ ] UP 키로 큐를 편집할 수 있는가?
    - [ ] Agent가 응답 완료 후 큐잉된 메시지가 자동으로 전송되는가?
    - [ ] Agent의 응답이 ChatLog에 표시되는가?
    - [ ] 여러 번 연속으로 메시지를 보낼 수 있는가?
    - [ ] 기존 non-interactive 모드가 여전히 작동하는가?
    - [ ] 모든 테스트가 통과하는가?
    - [ ] 린트와 타입 체크에 에러가 없는가?

# 최종 작업 검증 체크리스트

- [ ] 1. 기능 검증
  - [ ] InputBar에서 Enter를 누르면 메시지가 큐에 저장되는가?
  - [ ] 큐잉된 메시지가 화면에 렌더링되는가?
  - [ ] UP 키로 큐를 편집할 수 있는가?
  - [ ] Agent가 get_input() 호출하면 큐가 자동으로 전달되는가?
  - [ ] 전송된 메시지가 Agent에게 전달되는가?
  - [ ] Agent의 응답이 ChatLog에 표시되는가?
  - [ ] 여러 번 연속으로 메시지를 주고받을 수 있는가?

- [ ] 2. 코드 품질 검증
  - [ ] 모든 타입 힌팅이 올바른가?
  - [ ] 예외 처리가 적절히 구현되었는가?
  - [ ] 기존 코드 패턴을 따르는가?
  - [ ] 린트와 타입 체크에 에러가 없는가?
  - [ ] _send_stream / _receive_stream이 완전히 제거되었는가?

- [ ] 3. 기존 기능 보존
  - [ ] Non-interactive agent (DroidAgent)가 여전히 작동하는가?
  - [ ] CLI 모드가 정상 작동하는가?
  - [ ] 기존 Execute/Verify 루프가 깨지지 않았는가?

- [ ] 4. Interactive vs Non-Interactive 분기
  - [ ] supports_interactive = True인 agent는 사용자 입력을 계속 받는가?
  - [ ] supports_interactive = False인 agent는 초기 프롬프트만 받는가?
  - [ ] hasattr로 안전하게 속성 존재 여부를 체크하는가?

- [ ] 5. Terminalcp 로 직접 테스트 했을때 아래의 모든 동작이 실제로 도는가?
    ```
    # TUI 모드로 실행
    uv run sisyphus
    ```
    - 예상 동작:
      1. TUI 화면이 정상 표시됨
      2. InputBar와 큐 표시 영역이 분리되어 표시됨
      3. 플레이스홀더에 "Type and press Enter to queue (UP to edit)" 표시됨
  - [ ] 5.1 terminalcp 로 직접 테스트 (terminalcp)
    - [ ] 5.2.1 테스트 1: 메시지 큐잉 기본 동작
      ```
      # terminalcp로 TUI 시작
      # "Hello" 입력 → Enter
      # stdout에서 "[Queue] Hello" 표시 확인
      # stdout에서 "[Press UP to edit]" 힌트 확인
      ```
      - [ ] 큐 표시에 "Hello" 표시되는가?
      - [ ] 큐 힌트가 표시되는가?
      - [ ] 입력창이 비워지는가?
    - [ ] 5.2.2 테스트 2: 메시지 누적 (Enter 여러 번)
      ```
      # "Hello" 입력 → Enter
      # "World" 입력 → Enter
      # stdout에서 "Hello\nWorld" 또는 "Hello" 와 "World" 모두 표시 확인
      ```
      - [ ] 첫 번째 메시지 "Hello"가 큐에 저장되는가?
      - [ ] 두 번째 메시지 "World"가 누적되는가?
      - [ ] 큐 표시에 "\n"으로 구분되어 표시되는가?
    - [ ] 5.2.3 테스트 3: UP 키로 큐 편집 및 취소
      ```
      # "Hello" 입력 → Enter (큐잉됨)
      # "World" 입력 → Enter (누적됨)
      # UP 키 입력 (stdin: "\u001b[A")
      # stdout에서 입력창에 "Hello\nWorld" 로드 확인
      # stdout에서 큐 표시가 사라짐 확인
      ```
      - [ ] UP 키를 누르면 큐가 입력창으로 이동하는가?
      - [ ] 큐 표시가 사라지는가?
      - [ ] 입력창에 "\n" 포함된 전체 텍스트가 로드되는가?
    - [ ] 5.2.4 테스트 4: 큐 편집 후 재저장
      ```
      # "Hello" 입력 → Enter → UP 키
      # 입력창 내용을 "Hello!" 로 수정
      # Enter
      # stdout에서 "[Queue] Hello!" 표시 확인
      ```
      - [ ] 편집된 내용이 다시 큐에 저장되는가?
      - [ ] 큐 표시가 다시 나타나는가?
    - [ ] 5.2.5 테스트 5: 자동 전송 확인 (Agent가 ready일 때)
      ```
      # "Test message" 입력 → Enter (큐잉됨)
      # Agent 초기 응답 완료 대기
      # stdout에서 ChatLog에 "Test message" 전송 확인
      # stdout에서 큐 표시가 사라짐 확인
      # stdout에서 Agent 응답 표시 확인
      ```
      - [ ] Agent가 ready 상태가 되면 큐가 자동 전송되는가?
      - [ ] 큐 표시가 비워지는가?
      - [ ] Agent 응답이 ChatLog에 표시되는가?
    - [ ] 5.2.6 테스트 6: UP 키로 마지막 전송 메시지 로드
      ```
      # "First" 입력 → Enter → Agent 응답 대기
      # 큐 비워진 상태에서 UP 키
      # stdout에서 입력창에 "First" 로드 확인
      ```
      - [ ] 큐가 비어있을 때 UP 키를 누르면 _last_sent가 로드되는가?
      - [ ] 로드된 메시지를 수정할 수 있는가?
    - [ ] 5.2.7 테스트 7: 여러 번 연속 메시지 전송
      ```
      # "Message 1" → Enter → Agent 응답 대기
      # "Message 2" → Enter → Agent 응답 대기
      # "Message 3" → Enter → Agent 응답 대기
      # stdout에서 3개 메시지 모두 Agent에게 전달되고 응답 확인
      ```
      - [ ] 연속으로 여러 메시지를 보낼 수 있는가?
      - [ ] 각 메시지마다 Agent 응답이 오는가?
  - [ ] 5.3 Non-interactive agent 테스트
    ```
    # DroidAgent로 실행 (설정 변경 필요)
    # 또는 CLI 모드 실행
    ```
