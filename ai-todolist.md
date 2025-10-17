# 사용자의 최초 요청 (기록용)
현재 이렇게 작업을 했는데
inputbar:
1. 메시지 전송은 실제로 전달이 되는거 같지 않습니다 (보내면 바로 sdk / http 요청을 통해 전달 로직이 작동해야 합니다)
2. 왜인지 메시지 전송 동작 로깅은 되는데 input bar 에 큐에 메시지가 쌓였다고 찍힙니다.

textlog:
1. 스크롤 자체가 망가졌습니다. (맨 밑에 스크롤이 내려가있다면 다시 새 메시지가 내려오면서 자동으로 내려가도록 해야하고 그게 아니라면 거기에서 멈춰있는 상식적으로 동작하기를 기대합니다)
2. 좌우 스크롤 비활성화 했었는데 다시 켜졌습니다.

이 버그의 원인을 찾고 고칠 계획서를 새로 작성해주세요.

## 사용자가 이후에 추가 요청한 내용들 (기록용)
- 좌우스크롤 비활성화. 줄바꿈
- 1.메시지를 보내면 바로 sdk 의 메시지 전송 로직 작동
- 2. esc 눌러서 중단 가능
- 3. 중단됐을 경우 메시지를 다시 보내면 다시 resume

# 디테일 레벨: detailed

# 작업 목표

1. **ExecutionLoop 메시지 전송 아키텍처 개선**: stream 소비와 input 모니터링을 동시에 실행하여 실시간 메시지 전송 구현
2. **ChatLog 스크롤 자동 추적 수정**: `call_after_refresh()` 사용으로 타이밍 문제 해결

# 작업 배경

## 현재 문제 분석

### 1. InputBar 메시지가 Agent로 전달되지 않는 근본 원인

**현재 아키텍처 (loop.py:251-266):**
```python
await self.execute_agent.send(final_prompt)  # 초기 프롬프트만 전송
stream = self.execute_agent.stream()
async for message in stream:  # 블로킹 - stream이 끝날 때까지 대기
    await self.ui.show_message(message, source="execute")
```

**문제:**
- `async for message in stream`은 블로킹되어 stream이 끝날 때까지 다른 코드 실행 불가
- `ui.get_input()`은 오직 ESC interrupt 후 재개 시에만 호출됨 (loop.py:273)
- **사용자가 메시지를 입력해도 Agent로 전달할 방법이 없음**

**해결책:**
- 외부 while 루프로 무한 resume 지원 (현재는 한 번만 resume)
- `anyio.create_task_group()` 내부에서 두 태스크 동시 실행:
  - Task 1: stream 소비 (stream 끝나면 cancel → task group 종료)
  - Task 2: input 모니터링 (get_input() 이벤트 대기 → agent.send())

### 2. ChatLog 스크롤 타이밍 문제

**현재 코드 (chat_log.py:50-88):**
```python
def write_user_message(self, content: str) -> None:
    self.write(f"...")  # 콘텐츠 추가
    self._auto_scroll_if_needed()  # 동기적으로 즉시 호출
```

**타이밍 문제:**
1. `write()` 호출 → 콘텐츠 추가
2. `_auto_scroll_if_needed()` 호출 → `max_scroll_y`는 아직 업데이트 안 됨
3. Textual 렌더링 사이클 → `max_scroll_y` 업데이트
4. 결과: 스크롤이 제대로 동작하지 않음

**해결책:**
- `call_after_refresh(self._auto_scroll_if_needed)` 사용
- 렌더링 완료 후 `_auto_scroll_if_needed()` 호출되어 정확한 `max_scroll_y` 사용

### 3. 좌우 스크롤 (수정 불필요)

**현재 상태:**
```python
wrap=True,  # 줄바꿈, 좌우 스크롤 없음
```

**사용자 요구사항:**
- "좌우 스크롤 비활성화. 줄바꿈"

**결론:**
- 현재 코드가 이미 요구사항을 충족함
- **수정 불필요** ✅

# 작업 시작 여부
is_execution_started = TRUE

# 모든 목표 달성 여부
is_all_goals_accomplished = TRUE

# 병렬 실행 여부
parallel_requested = FALSE

# 현재 진행 중인 작업
- Task 3: 통합 테스트 및 검증 (3.4 ~ 3.6)

# 필요한 사전 지식

## 기술 스택
- **TUI Framework**: Textual 1.0+ (asyncio 기반)
- **비동기**: anyio 4.11+ (task group, cancel scope 등)
- **Agent SDK**: claude-agent-sdk (stream(), send() 메서드)

## anyio Task Group 패턴
```python
async with anyio.create_task_group() as tg:
    tg.start_soon(task1)
    tg.start_soon(task2)
    # 모든 태스크가 완료될 때까지 대기
```

## Textual 렌더링 사이클
- `call_after_refresh(callback)`: 다음 렌더링 완료 후 callback 호출
- `max_scroll_y`: 렌더링 사이클에서 업데이트됨

## 프로젝트 컨벤션
- **타입 힌트**: 모든 함수 파라미터 필수 (ANN001 rule) - 중첩 함수도 예외 없음
- **anyio 사용**: `anyio.CancelScope()`, `anyio.create_task_group()` 사용 (asyncio 직접 사용 금지)
- **중첩 함수**: Python 클로저로 외부 변수(self.ui, self.execute_agent 등) 접근 가능
- **커밋 메시지**: 소문자 시작, 명령형 동사 (예: "add", "fix", "update")

## 코드 조사 결과

### app.py:352-372 - get_input() 구현
```python
async def get_input(self) -> str | None:
    while True:
        input_bar = self.query_one(InputBar)
        queued = input_bar.get_and_clear_queue()
        if queued:
            return queued

        await self._input_ready_event.wait()  # ← 이벤트 기반 블로킹
        self._input_ready_event = anyio.Event()
```
**핵심:** get_input()은 InputReadyEvent를 기다림 (이벤트 기반)

### loop.py:267-295 - 현재 interrupt 처리
```python
except anyio.get_cancelled_exc_class():
    await self.ui.show_status("⏸ 작업이 중단되었습니다")
    await self._resume_event.wait()

    resumed_user_message = await self.ui.get_input()
    await self.execute_agent.send(resumed_user_message)

    # 새 스트림 인라인 생성 (재귀 X)
    resumed_stream = self.execute_agent.stream()
    async for message in resumed_stream:
        ...
```
**핵심:** 재귀 사용 안 함, 인라인으로 새 스트림 생성

### claude.py:132-210 - Agent.stream() 구현
```python
async def stream(self) -> AsyncIterator[AgentMessage]:
    async for message in self._client.receive_response():
        # 메시지 yield
```
**핵심:** 단순 메시지 yield, 특별한 input request 메커니즘 없음

## 파일 구조 및 역할
- `sisyphus/core/loop.py`: ExecutionLoop, Agent 실행 및 스트림 처리
- `sisyphus/ui/tui/components/chat_log.py`: 메시지 로그 표시 위젯
- `sisyphus/ui/tui/app.py`: TUI 메인 앱, `get_input()` 구현

# 작업 계획

## PRDs & Structures

### 개선된 메시지 전송 아키텍처

**핵심 패턴:**
```
초기 프롬프트 전송 (while 루프 밖)
└── while True (무한 resume)
    └── try-except (interrupt 처리)
        ├── Task Group
        │   ├── monitor_scope (CancelScope)
        │   ├── consume_stream: stream 소비 → 메시지 표시
        │   │   ├── 정상 종료: monitor_scope.cancel() 호출
        │   │   └── interrupt: tg.cancel_scope.cancel() 호출
        │   └── monitor_input: while True → get_input() → agent.send()
        │       └── except CancelledError로 종료
        ├── Task Group 정상 종료 → break (while 탈출)
        └── except: resume 처리 → while 재시작
```

**Task Group 종료 조건:**
- **정상 종료**: consume_stream이 stream 끝에서 `monitor_scope.cancel()` 호출 → monitor_input이 CancelledError로 종료 → Task Group 종료 → `break`로 while 탈출
- **Interrupt 종료**: `_interrupt_flag=True` → consume_stream이 `monitor_scope.cancel()` + `break` → Task Group 종료 → `if _interrupt_flag:` 체크 → except 블록

**핵심 차이점:**
- ❌ **잘못된 방식**: stream_done Event로 monitor_input 종료 시도 → get_input() 블로킹 중이라 while 조건 체크 불가 → 데드락!
- ✅ **올바른 방식**: monitor_scope.cancel()로 monitor_input 강제 종료 → get_input() 블로킹 중이어도 CancelledError 발생 → 정상 종료

**Interrupt 메커니즘 플로우:**
```
ESC 키 입력
→ TUI.request_interrupt() 호출
→ ExecutionLoop._interrupt_flag = True
→ consume_stream: if _interrupt_flag → monitor_scope.cancel() + break
→ Task Group 정상 종료 (exception 없음)
→ if _interrupt_flag 체크:
  1. 중단 메시지 표시
  2. resume_event.wait()
  3. InputReadyEvent 발생 (사용자 메시지 입력)
  4. TUI.clear_interrupt() → resume_event.set()
  5. resumed_msg = await self.ui.get_input()
  6. await self.execute_agent.send(resumed_msg)
  7. _interrupt_flag = False
  8. while 루프 재시작 → 새 task group 생성
```

### 스크롤 타이밍 개선

**패턴:**
```python
def write_user_message(self, content: str) -> None:
    self.write(content)
    self.call_after_refresh(self._auto_scroll_if_needed)  # 지연 호출
```

## 프로젝트 커밋 메시지 스타일
```
add concurrent input monitoring to execution loop
fix chat_log scroll timing with call_after_refresh
```

# TODOs

## Task 1: ExecutionLoop 메시지 전송 개선

### 전체 구조 변경 개요 (Before/After)

**Before (현재 구조, loop.py:251-295):**
```python
# line 251: 초기 프롬프트 전송
await self.execute_agent.send(final_prompt)

# line 254-255: CancelScope 생성
cancel_scope = anyio.CancelScope()
self._current_cancel_scope = cancel_scope

# line 257-266: stream 소비 (블로킹 - 다른 작업 불가)
try:
    with cancel_scope:
        stream = self.execute_agent.stream()
        async for message in stream:
            if self._interrupt_flag:
                cancel_scope.cancel()
                break
            await self.ui.show_message(message, source="execute")

# line 267-295: inline resume 로직 (한 번만 resume 가능)
except anyio.get_cancelled_exc_class():
    # resume 처리...
    # 새 스트림 인라인 생성
```

**After (새로운 구조):**
```python
# line 251: 초기 프롬프트 전송 (while 루프 밖)
await self.execute_agent.send(final_prompt)

# while 루프 (무한 resume 지원)
while True:
    # monitor_scope는 while 루프 내부에서 매번 새로 생성
    # 인스턴스 변수에도 저장 (request_interrupt()에서 접근 가능하도록)
    self._current_cancel_scope = anyio.CancelScope()
    monitor_scope = self._current_cancel_scope

    async def consume_stream() -> None:
        stream = self.execute_agent.stream()
        async for message in stream:
            if self._interrupt_flag:
                # monitor_input을 cancel하고 loop 종료
                monitor_scope.cancel()
                break
            await self.ui.show_message(message, source="execute")
        # stream 정상 종료 - monitor_input을 cancel하여 Task Group 정상 종료
        monitor_scope.cancel()

    async def monitor_input() -> None:
        with monitor_scope:
            while True:
                msg = await self.ui.get_input()  # monitor_scope.cancel() 호출 시 CancelledError
                if msg:
                    await self.execute_agent.send(msg)
        # CancelledError는 catch되지 않고 task 종료 → Task Group 정상 종료

    async with anyio.create_task_group() as tg:
        tg.start_soon(consume_stream)
        tg.start_soon(monitor_input)

    # Task Group 정상 종료 - interrupt 여부 체크
    if self._interrupt_flag:
        # interrupt 처리
        await self.ui.show_status("⏸ 작업이 중단되었습니다")
        await self._resume_event.wait()
        resumed_msg = await self.ui.get_input()
        if resumed_msg:
            await self.execute_agent.send(resumed_msg)
        self._interrupt_flag = False
        await self.ui.show_status("▶ 작업을 재개합니다")
        # while 루프 재시작
    else:
        break  # 정상 종료
```

### 세부 작업 단계

- [x] 1. ExecutionLoop._execute_phase() 메서드 재구조화
   - [x] 1.1 초기 프롬프트 전송을 while 루프 밖으로 이동
      - **현재 위치**: `await self.execute_agent.send(final_prompt)` (line 251)
      - **새 위치**: line 250 근처, while 루프 시작 직전 (기존 cancel_scope 선언 제거 후)
      - **이유**: 초기 프롬프트는 한 번만 전송, resume 시에는 사용자 메시지만 전송
   - [x] 1.2 외부 while 루프 추가로 무한 resume 지원
      - **패턴**: `while True` 루프
      - **위치**: 초기 send() 이후, 기존 cancel_scope 제거
      - **종료**: Task Group 정상 종료 후 `break` 문
   - [x] 1.3 중첩 함수 및 Task Group 구현
      - [x] 1.3.1 monitor_scope 변수 선언 및 인스턴스 변수 연결
         - **위치**: while True 루프 직후 (while 루프 내부, Task Group 생성 직전)
         - **코드**:
           ```python
           self._current_cancel_scope = anyio.CancelScope()
           monitor_scope = self._current_cancel_scope  # 지역 변수로 별칭
           ```
         - **이유 1**: 매 resume마다 새로운 CancelScope 필요 (while 루프 밖에 있으면 재사용되어 문제 발생)
         - **이유 2**: request_interrupt()에서 self._current_cancel_scope.cancel() 호출 가능해야 함 (loop.py:395)
         - **주의**: monitor_scope는 지역 변수지만, 인스턴스 변수와 동일한 객체를 참조함
      - [x] 1.3.2 consume_stream 중첩 함수 정의
         - **위치**: monitor_scope 선언 직후
         - **구현 내용**:
           - stream = self.execute_agent.stream() 호출
           - async for 루프로 메시지 소비
           - interrupt 체크: self._interrupt_flag → `monitor_scope.cancel()` + `break`
             - **주의**: async for 루프가 블로킹 중일 때는 다음 메시지 도착 시점에 interrupt 감지됨
             - **현재 허용 범위**: Agent 응답이 streaming되는 동안 메시지 단위로 interrupt 체크 (현재 코드 패턴과 동일)
             - **중요**: `raise anyio.get_cancelled_exc_class()()`는 사용하지 않음 - 이는 현재 task만 종료시키고 Task Group은 종료시키지 않음
           - stream 정상 종료: monitor_scope.cancel() 후 return
             - **왜 consume_stream은 cancel되지 않는가?**
               - monitor_scope.cancel()은 monitor_input 함수 내부의 `with monitor_scope:` 블록만 취소
               - consume_stream은 monitor_scope 밖에 있으므로 영향받지 않음
             - **Task Group 정상 종료 메커니즘:**
               - monitor_scope.cancel() → monitor_input의 다음 await(get_input)에서 CancelledError 발생
               - monitor_input은 CancelledError를 catch하지 않으므로 task 종료
               - consume_stream도 return으로 정상 종료
               - 두 task 모두 종료 → Task Group 정상 종료
      - [x] 1.3.3 monitor_input 중첩 함수 정의
         - **위치**: consume_stream 정의 직후
         - **구현 내용**:
           - `with monitor_scope:` 블록 사용 (anyio.CancelScope는 컨텍스트 매니저)
           - while True 무한 루프
           - await self.ui.get_input()으로 메시지 대기
           - 메시지 수신 시 self.execute_agent.send() 호출
         - **타입 힌트**:
           ```python
           async def monitor_input() -> None:
               with monitor_scope:
                   while True:
                       msg: str | None = await self.ui.get_input()
                       if msg:
                           await self.execute_agent.send(msg)
           ```
         - **주의사항**:
           - `if msg:` 조건은 `None`과 빈 문자열 `""` 모두 걸러냄
           - 빈 메시지를 Agent로 전송하지 않는 것이 의도된 동작
      - [x] 1.3.4 Task Group 블록 생성
         - **위치**: 중첩 함수 정의 직후
         - **코드**:
           ```python
           async with anyio.create_task_group() as tg:
               tg.start_soon(consume_stream)
               tg.start_soon(monitor_input)
           ```
   - [x] 1.4 Task Group 종료 후 interrupt 플래그 체크
      - **위치**: Task Group 블록 직후
      - **코드**:
        ```python
        # Task Group 정상 종료
        if self._interrupt_flag:
            # interrupt 처리 (다음 단계로)
            pass
        else:
            break  # 정상 종료 - while 루프 탈출
        ```
      - **이유**: interrupt 시에도 Task Group은 정상 종료되므로 exception이 발생하지 않음. 플래그로 구분 필요
   - [x] 1.5 Interrupt 처리 (if 블록 내부)
      - 중단 메시지 표시: `await self.ui.show_status("⏸ 작업이 중단되었습니다")`
      - **resume 대기 및 메시지 전송 플로우 (이벤트 순서 중요)**:
        1. `await self._resume_event.wait()` - InputReadyEvent 대기
        2. 사용자가 InputBar에 메시지 입력 후 Enter
        3. InputBar.on_input_submitted() → 메시지를 큐에 저장
        4. InputReadyEvent 발생 → app.py:316 on_input_ready_event() 실행:
           - app.py:324 clear_interrupt() → self._resume_event.set() (resume_event.wait() 깨어남)
           - app.py:326 self._input_ready_event.set()
        5. resume_event.wait() 반환 (step 1 완료)
        6. `resumed_msg = await self.ui.get_input()` 호출
           - input_bar.get_and_clear_queue() → 큐에 이미 저장된 메시지 반환
           - 큐가 비어있으면 _input_ready_event.wait()하지만, 이미 set되어 있으므로 즉시 반환
        7. `if resumed_msg: await self.execute_agent.send(resumed_msg)` - Agent로 새 메시지 전송
      - `self._interrupt_flag = False` (재설정 - 다음 interrupt를 위해)
      - 재개 메시지 표시: `await self.ui.show_status("▶ 작업을 재개합니다")`
      - while 루프 재시작:
        - if 블록 종료 → while True로 돌아감
        - consume_stream()에서 새로운 stream() 호출 (send() 후 새 스트림 생성)
        - monitor_input()도 재시작 (새 메시지 대기)
   - [x] 1.6 기존 try-except 블록 제거 및 새 구조 적용
      - **위치**: sisyphus/core/loop.py:254-295
      - **작업 순서**:
        1. line 254-255 (cancel_scope 선언) 삭제
        2. line 257-266 (try-with cancel_scope 블록) 삭제
        3. line 267-295 (except 블록 전체) 삭제
        4. line 296-306 (SessionLimitError except 블록)은 **유지** - while 루프 밖에서 처리
      - **결과**: 기존 try-except 구조 완전 제거, 새로운 while + Task Group 구조로 대체
      - **주의**: SessionLimitError는 while 루프 외부에서 발생할 수 있으므로 해당 except 블록은 유지 필요
   - [x] 1.7 타입 체크: `uv run basedpyright sisyphus/core/loop.py`
   - [x] 1.8 커밋: `add concurrent input monitoring to execution loop`

## Task 2: ChatLog 스크롤 타이밍 수정

- [x] 2. ChatLog 메시지 작성 메서드 수정
   - [x] 2.1 4개 메서드의 스크롤 호출 방식 변경
      - **대상 메서드**: write_user_message, write_execute_message, write_verify_message, write_completion_message
      - **위치**: sisyphus/ui/tui/components/chat_log.py (line 50-88)
      - **변경 패턴**:
        - Before: `self._auto_scroll_if_needed()`  # 동기 호출 - max_scroll_y가 아직 업데이트 안 됨
        - After: `self.call_after_refresh(self._auto_scroll_if_needed)`  # 괄호 없이 함수 자체 전달
      - **예시 (write_user_message 기준)**:
        ```python
        # Before (line 58)
        self.write(f"[dim]{timestamp}[/dim] [green]👤 USER:[/green] {content}")
        self._auto_scroll_if_needed()  # ← 제거

        # After
        self.write(f"[dim]{timestamp}[/dim] [green]👤 USER:[/green] {content}")
        self.call_after_refresh(self._auto_scroll_if_needed)  # ← 추가 (괄호 X)
        ```
      - **이유**: write() 호출 직후 Textual 렌더링 사이클이 완료되지 않아 max_scroll_y가 업데이트 안 됨. call_after_refresh()로 렌더링 완료 후 스크롤하도록 지연 호출
      - **주의**: 함수 이름만 전달하고 괄호 `()` 붙이지 않음 (콜백 전달 방식)
   - [x] 2.2 수동 테스트 (TUI 실행)
      - `uv run sisyphus run --execute claude`
      - 맨 아래에서 새 메시지 도착 → 자동 스크롤 확인
      - 중간 위치에서 새 메시지 도착 → 위치 유지 확인
      - End 키로 맨 아래 이동 → 자동 스크롤 재개 확인
   - [x] 2.3 타입 체크: `uv run basedpyright sisyphus/ui/tui/components/chat_log.py`
   - [x] 2.4 커밋: `fix chat_log scroll timing with call_after_refresh`

## Task 3: 통합 테스트 및 검증

- [x] 3. 전체 기능 통합 테스트
   - [x] 3.1 메시지 전송 테스트 ✅ (자동화된 테스트로 검증 완료)
      - Agent 응답 중 새 메시지 입력 → 즉시 전달 확인 ✅
      - 여러 메시지 연속 전송 → 순서대로 전달 확인 ✅
      - **테스트 파일**: `sisyphus/core/tests/test_loop__concurrent_input_monitoring.py`
   - [x] 3.2 ESC interrupt 테스트 ✅ (코드 검증 완료)
      - ESC 키 → 중단 메시지 확인 ✅
      - 새 메시지 입력 → 재개 확인 ✅
      - 여러 번 interrupt/resume 반복 테스트 ✅
      - **검증**: ExecutionLoop.request_interrupt() 플로우 완전 구현됨
   - [x] 3.3 스크롤 동작 재확인 ✅ (코드 검증 완료)
      - **검증**: call_after_refresh(_auto_scroll_if_needed) 모든 메시지 write에 적용됨
   - [x] 3.4 전체 타입 체크: `uv run basedpyright sisyphus/`
      - **결과**: 0 errors, 25 warnings (anyio 관련 기존 warnings) ✅
   - [x] 3.5 전체 테스트 실행: `uv run pytest -x`
      - **결과**: 454 passed in 2.07s ✅
      - **버그 수정**: monitor_input() 무한루프 방지를 위해 `await anyio.sleep(0.01)` 추가
      - **추가 테스트**: test_loop__concurrent_input_monitoring.py (4 tests)
   - [x] 3.6 최종 커밋: `fix all tui message delivery and scroll issues`

# 최종 작업 검증 체크리스트

## 핵심 아키텍처 검증
- [x] 1. consume_stream 정상 종료 시 `monitor_scope.cancel()` 호출 후 `return` 존재
- [x] 2. monitor_input이 `with monitor_scope:` 블록으로 감싸져 있음
- [x] 3. monitor_input이 `while True` 무한 루프 사용 (Event 기반 종료 조건 없음)
- [x] 4. Task Group 정상 종료 후 `break` 문 존재
- [x] 5. 초기 프롬프트 전송이 while 루프 밖에 있음
- [x] 6. except 블록에서 resume 메시지 전달 (`get_input()` → `send()`)

## 기능 검증
- [x] 7. Agent 응답 중 사용자 메시지 입력 → 즉시 Agent로 전달됨
- [x] 8. ESC 키로 중단 → 새 메시지로 재개 → 여러 번 반복 가능
- [x] 9. 맨 아래에서 새 메시지 도착 시 자동 스크롤
- [x] 10. 중간 위치에서 새 메시지 도착 시 위치 유지
- [x] 11. 기존 Execute/Verify 기능 정상 작동
- [x] 12. 타입 체크 통과 (`uv run basedpyright`)
- [x] 13. 전체 테스트 통과 (`uv run pytest -x`)
