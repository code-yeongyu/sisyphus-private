# 사용자의 최초 요청 (기록용)

`uv run sisyphus` 실행 시 `[bold red]Error: No screens on stack[/bold red]` 에러 발생. 원인을 면밀히 찾아 수정.

## 사용자가 이후에 추가 요청한 내용들 (기록용)

- 최초 계획서에서 누락된 부분이나 잘 작동하지 않을 것으로 추정되는 부분들을 찾아서 보완
- git log의 원본 ai-todolist.md와 비교하여 구현 패턴 확인
- Codex를 통한 Textual thread-safety 분석 완료

# 작업 목표

- Textual TUI와 anyio 기반 ExecutionLoop의 올바른 통합
- TUI 모드에서 `uv run sisyphus` 정상 실행
- Textual App의 라이프사이클을 올바르게 관리
- CLI 모드는 영향 없이 유지

# 작업 배경

현재 구현은 `TUI()` 인스턴스를 생성만 하고 실제로 Textual App을 시작(`app.run_async()`)하지 않은 상태에서 `ExecutionLoop`이 UI 메서드를 호출하려 합니다. Textual은 자체 async event loop를 관리하는 프레임워크이므로, `App.run()` 또는 `App.run_async()`를 통해 시작되기 전까지는 screen stack이 초기화되지 않아 "No screens on stack" 에러가 발생합니다.

**근본 원인**:
1. `cli.py`의 `run()` 함수에서 `anyio.run(_main, ...)`을 호출
2. `_main()`에서 `TUI()` 인스턴스만 생성하고 `ExecutionLoop`에 전달
3. `ExecutionLoop.run()`에서 `await ui.initialize()`, `await ui.show_message()` 등을 호출
4. 하지만 `TUI.run_async()`가 호출되지 않아 Textual App이 시작되지 않음
5. Screen stack이 초기화되지 않은 상태에서 UI 메서드 호출 시도 → 에러

**올바른 통합 패턴** (Codex 분석 결과):
- Textual이 자체 라이프사이클을 소유하되, anyio로 orchestration
- `anyio.run(_main, backend="asyncio")` 사용 (Textual은 asyncio만 지원)
- `anyio.create_task_group()`로 TUI와 ExecutionLoop을 병렬 실행
- `tg.start_soon(app.run_async)`로 Textual App 시작
- `on_mount`에서 `anyio.Event()`로 준비 완료 신호
- UI 업데이트는 `self.call_from_thread()` 또는 메시지 큐를 통해 안전하게 처리

# 작업 시작 여부
is_execution_started = TRUE

# 모든 목표 달성 여부
is_all_goals_accomplished = FALSE

# 병렬 실행 여부
parallel_requested = FALSE

# 현재 진행 중인 작업
- 2. cli.py에서 TUI/CLI 모드별 _main 함수 분리 (Phase 2 - THE CORE FIX)
  - _main_cli() 구현 (기존 로직)
  - _main_tui() 구현 (Task group + ui.run_async() + coordination)
  - run() 함수 수정 (backend="asyncio" for TUI)
  - 기존 _main() 제거

# 작업 계획

## 필요한 사전 지식

### Textual App 라이프사이클
- `App.run()` (동기) 또는 `App.run_async()` (비동기): App을 시작하고 event loop 실행
- `on_mount()`: 위젯이 DOM에 마운트되었을 때 호출 (초기화 로직)
- `compose()`: 위젯 트리 구성
- `call_from_thread()`: 다른 스레드/태스크에서 안전하게 UI 업데이트
- `exit()`: App 종료

### anyio Task Groups
- `async with anyio.create_task_group() as tg`: 여러 async 태스크를 병렬 실행
- `tg.start_soon(async_func, *args)`: 태스크 시작
- Task group은 모든 태스크가 완료될 때까지 대기

### Textual과 anyio 통합 제약
- Textual은 asyncio만 지원 (trio 미지원)
- `anyio.run(..., backend="asyncio")` 명시 필요
- UI 업데이트는 Textual event loop에서만 안전

## 파일 구조 및 역할

```
sisyphus/
├── sisyphus/
│   ├── cli.py              # Typer CLI - anyio.run() 호출 (수정 필요)
│   ├── core/
│   │   └── loop.py         # ExecutionLoop (수정 필요)
│   ├── ui/
│   │   ├── base.py         # UIProtocol (변경 없음)
│   │   ├── cli/
│   │   │   └── console.py  # CLI UI (변경 없음)
│   │   └── tui/
│   │       └── app.py      # TUI App (수정 필요)
```

## 맥락 이해를 위해 참고해야 할 파일들

### 1. sisyphus/cli.py (lines 194-216)
- **역할**: Typer CLI 엔트리 포인트, `anyio.run(_main, ...)`으로 비동기 실행
- **참고할 부분**: `run()` 함수의 `anyio.run()` 호출 부분
- **현재 코드**:
  ```python
  ui = create_ui("cli" if no_tui else "tui")
  session_store = SessionStore()

  try:
      anyio.run(
          _main,
          execute_agent,
          verify_agent,
          execute_prompt,
          verify_prompt,
          execute_extra_prompt,
          verify_extra_prompt,
          ui,
          session_store,
      )
  ```
- **문제점**: `backend="asyncio"` 명시 없음, TUI 시작 로직 없음

### 2. sisyphus/cli.py의 `_main()` 함수 (lines 105-147)
- **역할**: 비동기 메인 함수, ExecutionLoop 생성 및 실행
- **현재 코드**:
  ```python
  async def _main(
      execute_agent: Agent,
      verify_agent: Agent | None,
      execute_prompt_spec: str,
      verify_prompt_spec: str | None,
      execute_extra: str | None,
      verify_extra: str | None,
      ui: UIProtocol,
      session_store: SessionStore,
  ) -> None:
      # ... 초기화 ...
      loop = ExecutionLoop(...)
      await loop.run(...)  # ExecutionLoop 직접 실행
  ```
- **문제점**: TUI를 시작하지 않고 바로 `loop.run()` 호출

### 3. sisyphus/ui/tui/app.py
- **역할**: Textual App 구현 (UIProtocol 준수)
- **참고할 부분**: `__init__`, `on_mount`, `show_message`, `show_status`
- **현재 구조**:
  ```python
  class TUI(App[None]):
      def __init__(self) -> None:
          super().__init__()
          self.shutdown_event = anyio.Event()
          # ...

      async def on_mount(self) -> None:
          self.title = "Sisyphus - Multi-Agent Execution System"
          # 메시지 큐 생성
          (self._send_stream, self._receive_stream) = anyio.create_memory_object_stream(...)

      async def show_message(self, message: AgentMessage, source: str) -> None:
          chat_log = self.query_one(ChatLog)
          # ...
  ```
- **문제점**: `run_async()` 호출 없이 메서드만 정의됨

### 4. sisyphus/core/loop.py
- **역할**: Execute + Verify 페이즈 orchestration
- **참고할 부분**: `run()` 메서드의 UI 호출 패턴
- **현재 코드**:
  ```python
  async def run(self, ...) -> None:
      await self.ui.initialize()

      while True:
          await self.ui.show_status(...)
          await self._execute_phase(...)
          # ...
  ```
- **주의사항**: UI 메서드 호출이 Textual event loop 외부에서 발생

## 구현 세부사항

### 아키텍처 변경 방향

**Option A: TUI가 ExecutionLoop을 worker로 실행** (권장)
- TUI의 `on_mount()`에서 ExecutionLoop을 백그라운드 태스크로 시작
- ExecutionLoop은 메시지 큐나 `call_from_thread()`를 통해 UI 업데이트 요청
- TUI의 라이프사이클이 전체 시스템을 제어

**Option B: anyio task group에서 TUI와 ExecutionLoop 병렬 실행**
- `_main()`에서 `anyio.create_task_group()` 사용
- `tg.start_soon(ui.run_async)`로 TUI 시작
- `on_mount`에서 `anyio.Event().set()`로 준비 신호
- ExecutionLoop은 준비 신호 대기 후 시작
- UI 업데이트는 thread-safe하게 처리

**선택**: Option B (기존 구조를 최소한으로 수정, anyio 중심 유지)

### 구현 전략

#### Codex 분석 결과 (Thread-Safety & Coordination)

**CRITICAL: Textual Thread-Safety 위반**
- 현재 ExecutionLoop에서 `ui.show_message()`, `ui.show_status()`를 직접 호출하면 `query_one()`이 다른 async task에서 실행됨
- **Textual은 Widget DOM 접근이 반드시 App의 메시지 펌프를 통해야 함**
- **해결 방법**:
  1. `call_from_thread()` 사용: ExecutionLoop → TUI의 UI 업데이트를 Textual event loop에서 실행
  2. `post_message()` 사용 (권장): Custom Message를 정의하고 TUI가 메시지를 받아서 위젯 업데이트
  3. `run_worker()` 사용: TUI 내부에서 worker로 ExecutionLoop 실행

**Widget 초기화 타이밍**
- `on_mount()`에서 `ready_event.set()`은 맞지만, 첫 렌더링이 완료되지 않을 수 있음
- `await self.call_after_refresh(...)` 사용하여 첫 레이아웃/렌더링 완료 후 신호 보내기 고려
- 모든 UI 메서드에서 `ready_event.wait()` 추가하여 위젯이 준비될 때까지 대기

**Shutdown Coordination (현재 계획서에 누락됨)**
- ExecutionLoop 완료 시: `self.app.call_from_thread(self.app.exit)` 또는 shutdown message 전송
- TUI 종료(Ctrl+C) 시: `shutdown_event.set()` + ExecutionLoop task 취소
- `_main_tui()`에서 `shutdown_event.wait()`를 task group에 연결하여 양방향 종료 처리

**Error Propagation (현재 계획서에 누락됨)**
- anyio.TaskGroup은 한 task 예외 시 다른 task도 취소
- 각 task를 try-except로 감싸서 에러를 UI에 표시하고 정리 후 재발생
- Widget 업데이트 핸들러에서 예외 처리하여 앱 전체가 멈추지 않도록 방지

**Timeout & Edge Cases (현재 계획서에 누락됨)**
- `ready_event.wait()`에 `anyio.fail_after()` 또는 `move_on_after()` 적용 (예: 10초 타임아웃)
- 타임아웃 발생 시 CLI UI로 fallback 또는 사용자에게 알림
- TUI 초기화 실패 시 graceful degradation

1. **cli.py 수정**:
   - `anyio.run(..., backend="asyncio")` 명시
   - TUI 모드일 때 `_main_tui()`, CLI 모드일 때 `_main_cli()` 분리
   - **Task group에서 에러 처리 및 shutdown coordination 추가**

2. **TUI 클래스 수정** (Thread-Safe UI 업데이트):
   - `ready_event: anyio.Event` 추가 (준비 완료 신호)
   - `on_mount()`에서 `self.ready_event.set()` 호출 (또는 `call_after_refresh` 사용)
   - **Custom Message 정의**: `UpdateStatusMessage`, `ShowMessageMessage` 등
   - **Message 핸들러 구현**: `on_update_status_message()`, `on_show_message_message()` 등
   - **모든 UI 메서드에서 `call_from_thread()` 사용 또는 메시지 전송으로 변경**
   - **`shutdown_event` 활용**: TUI 종료 시 ExecutionLoop에 신호

3. **_main 함수 재구성**:
   - TUI 모드: Task group으로 `TUI.run_async()`와 ExecutionLoop 병렬 실행
   - CLI 모드: 기존 방식 유지
   - **Shutdown coordination**: `shutdown_event` 모니터링 task 추가
   - **Error handling**: 각 task를 try-except로 감싸기
   - **Timeout**: `ready_event.wait()`에 타임아웃 적용

## 프로젝트 커밋 메시지 스타일

Recent commits:
```
fa4fd06 feat: complete all tasks - set is_all_goals_accomplished = FALSE
f61eb0b test: verify all integration tests pass
dfb92f4 test: verify all integration tests pass and mark project complete
a6cef66 fix: correct Agent Protocol stream() signature and usage
500cd50 docs: update Task 18 progress in ai-todolist.md
```

패턴: `<type>: <subject>` (feat, fix, test, docs)

# TODOs

## Phase 0.5: Thread-Safe UI 업데이트 패턴 구현 (CRITICAL - Codex 분석 결과)

- [x] 0.5. TUI에 Custom Message 및 Thread-Safe 업데이트 구현
  - [x] 0.5.1 구현: Custom Message 클래스 정의 (sisyphus/ui/tui/app.py 상단)
    ```python
    from textual.message import Message

    class UpdateStatusMessage(Message):
        """상태 업데이트 메시지"""
        def __init__(self, status: str) -> None:
            super().__init__()
            self.status = status

    class ShowAgentMessage(Message):
        """에이전트 메시지 표시"""
        def __init__(self, message: AgentMessage, source: str) -> None:
            super().__init__()
            self.message = message
            self.source = source

    class ShutdownRequestMessage(Message):
        """종료 요청 메시지 (ExecutionLoop → TUI)"""
        pass
    ```
    - 현재: Custom Message 없음
    - 변경: Textual Message 기반 커스텀 메시지 정의
  - [x] 0.5.2 구현: Message 핸들러 추가 (TUI 클래스 내부)
    ```python
    async def on_update_status_message(self, message: UpdateStatusMessage) -> None:
        """상태 업데이트 핸들러"""
        try:
            status_panel = self.query_one(StatusPanel)
            status_panel.update_status(message.status)
        except Exception as e:
            self.log.error(f"Failed to update status: {e}")

    async def on_show_agent_message(self, message: ShowAgentMessage) -> None:
        """에이전트 메시지 표시 핸들러"""
        try:
            chat_log = self.query_one(ChatLog)
            if message.source == "execute":
                chat_log.write_execute_message(message.message.content)
            elif message.source == "verify":
                chat_log.write_verify_message(message.message.content)
        except Exception as e:
            self.log.error(f"Failed to show message: {e}")

    async def on_shutdown_request_message(self, message: ShutdownRequestMessage) -> None:
        """종료 요청 핸들러"""
        await self._safe_shutdown()
    ```
    - 현재: 메시지 핸들러 없음
    - 변경: 각 Message에 대한 핸들러 구현, 예외 처리 포함
  - [x] 0.5.3 구현: UI 메서드를 Message 전송으로 변경
    ```python
    async def show_status(self, status: str) -> None:
        """상태 표시 (Thread-Safe)"""
        await self.ready_event.wait()  # 위젯 준비 대기
        self.post_message(UpdateStatusMessage(status))

    async def show_message(self, message: AgentMessage, source: str) -> None:
        """메시지 표시 (Thread-Safe)"""
        await self.ready_event.wait()  # 위젯 준비 대기
        self.post_message(ShowAgentMessage(message, source))
    ```
    - 현재: 직접 `query_one()` 호출
    - 변경: `post_message()`로 메시지 전송, `ready_event.wait()` 추가
  - [x] 0.5.4 린트 및 타입 체크
    - [x] `ruff check sisyphus/ui/tui/app.py`
    - [x] `basedpyright sisyphus/ui/tui/app.py`
  - [x] 0.5.5 커밋: `git add sisyphus/ui/tui/app.py && git commit -m "feat: implement thread-safe UI updates with Textual Messages"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] Custom Message 클래스들이 정의되었는가?
    - [x] Message 핸들러에 예외 처리가 포함되었는가?
    - [x] `show_status()`, `show_message()`가 `post_message()` 사용하는가?
    - [x] 모든 UI 메서드에서 `ready_event.wait()` 호출하는가?
    - [x] 타입 체크와 린트가 통과하는가?

## Phase 1: TUI 라이프사이클 수정

- [x] 1. TUI 클래스에 준비 신호 추가 (sisyphus/ui/tui/app.py)
  - [x] 1.1 구현: `TUI.__init__()`에 `ready_event` 추가
    ```python
    def __init__(self) -> None:
        super().__init__()
        self.ctrl_c_count = 0
        self.last_ctrl_c_time: datetime | None = None
        self.shutdown_event = anyio.Event()
        self.ready_event = anyio.Event()  # 추가
        # ...
    ```
    - 현재: `ready_event` 없음
    - 변경: `self.ready_event = anyio.Event()` 추가
  - [x] 1.2 구현: `on_mount()`에서 준비 신호 발송
    ```python
    async def on_mount(self) -> None:
        self.title = "Sisyphus - Multi-Agent Execution System"
        self.sub_title = "Execute & Verify"

        (self._send_stream, self._receive_stream) = anyio.create_memory_object_stream(max_buffer_size=100)

        self.ready_event.set()  # 추가: TUI 준비 완료 신호
    ```
    - 현재: 준비 신호 없음
    - 변경: `self.ready_event.set()` 추가
  - [x] 1.3 린트 및 타입 체크
    - [x] `ruff check sisyphus/ui/tui/app.py`
    - [x] `basedpyright sisyphus/ui/tui/app.py`
  - [x] 1.4 커밋: `git add sisyphus/ui/tui/app.py && git commit -m "feat: add ready_event to TUI for lifecycle sync"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] `TUI.__init__`에 `self.ready_event = anyio.Event()` 추가되었는가?
    - [x] `on_mount()`에서 `self.ready_event.set()` 호출하는가?
    - [x] 타입 체크와 린트가 통과하는가?

## Phase 2: cli.py 수정 - anyio backend 명시 및 TUI/CLI 분리

- [x] 2. cli.py에서 TUI/CLI 모드별 _main 함수 분리
  - [x] 2.1 구현: `_main_cli()` 함수 작성 (기존 `_main` 로직)
    ```python
    async def _main_cli(
        execute_agent: Agent,
        verify_agent: Agent | None,
        execute_prompt_spec: str,
        verify_prompt_spec: str | None,
        execute_extra: str | None,
        verify_extra: str | None,
        ui: UIProtocol,
        session_store: SessionStore,
    ) -> None:
        """CLI 모드 메인 함수 (기존 로직)."""
        prompt_resolver = PromptResolver()
        logger_factory = LoggerFactory()
        task_validator = TaskValidator() if Path("ai-todolist.md").exists() else None

        loop = ExecutionLoop(
            execute_agent=execute_agent,
            ui=ui,
            session_store=session_store,
            prompt_resolver=prompt_resolver,
            logger_factory=logger_factory,
            verify_agent=verify_agent,
            task_validator=task_validator,
        )

        await loop.run(
            execute_prompt=execute_prompt_spec,
            execute_extra=execute_extra,
            verify_prompt=verify_prompt_spec,
            verify_extra=verify_extra,
        )
    ```
    - 현재: 단일 `_main()` 함수
    - 변경: `_main_cli()` 함수로 분리 (기존 로직 그대로)
  - [x] 2.2 구현: `_main_tui()` 함수 작성 (TUI + ExecutionLoop 병렬 실행 + Shutdown/Error 처리)
    ```python
    async def _main_tui(
        execute_agent: Agent,
        verify_agent: Agent | None,
        execute_prompt_spec: str,
        verify_prompt_spec: str | None,
        execute_extra: str | None,
        verify_extra: str | None,
        ui: UIProtocol,
        session_store: SessionStore,
    ) -> None:
        """TUI 모드 메인 함수 (TUI와 ExecutionLoop 병렬 실행)."""
        from sisyphus.ui.tui.app import TUI, ShutdownRequestMessage

        if not isinstance(ui, TUI):
            raise TypeError("ui must be TUI instance for TUI mode")

        async def monitor_shutdown(tg: anyio.abc.TaskGroup) -> None:
            """Shutdown 이벤트 모니터링 (TUI → ExecutionLoop 종료)."""
            await ui.shutdown_event.wait()
            tg.cancel_scope.cancel()

        async def run_execution_loop() -> None:
            """ExecutionLoop 실행 (TUI 준비 완료 후)."""
            try:
                # TUI 준비 대기 (타임아웃 10초)
                with anyio.move_on_after(10.0) as cancel_scope:
                    await ui.ready_event.wait()

                if cancel_scope.cancelled_caught:
                    raise TimeoutError("TUI initialization timeout")

                prompt_resolver = PromptResolver()
                logger_factory = LoggerFactory()
                task_validator = TaskValidator() if Path("ai-todolist.md").exists() else None

                loop = ExecutionLoop(
                    execute_agent=execute_agent,
                    ui=ui,
                    session_store=session_store,
                    prompt_resolver=prompt_resolver,
                    logger_factory=logger_factory,
                    verify_agent=verify_agent,
                    task_validator=task_validator,
                )

                await loop.run(
                    execute_prompt=execute_prompt_spec,
                    execute_extra=execute_extra,
                    verify_prompt=verify_prompt_spec,
                    verify_extra=verify_extra,
                )

                # ExecutionLoop 완료 시 TUI에 종료 요청
                ui.post_message(ShutdownRequestMessage())
            except Exception as e:
                # 에러를 UI에 표시하고 종료 요청
                try:
                    await ui.show_status(f"[bold red]Error: {e}[/bold red]")
                except:
                    pass
                ui.post_message(ShutdownRequestMessage())
                raise  # TaskGroup이 다른 task도 취소하도록 재발생

        try:
            async with anyio.create_task_group() as tg:
                # TUI 시작 (백그라운드)
                tg.start_soon(ui.run_async)
                # ExecutionLoop 시작 (TUI 준비 후)
                tg.start_soon(run_execution_loop)
                # Shutdown 모니터링 (별도 task)
                tg.start_soon(monitor_shutdown, tg)
        except* (SystemExit, KeyboardInterrupt):
            # 정상 종료 (Ctrl+C 등) - ExceptionGroup 처리
            pass
        except (SystemExit, KeyboardInterrupt):
            # 정상 종료 (Ctrl+C 등) - ExceptionGroup 외부 예외 처리
            pass
    ```
    - 현재: TUI를 시작하지 않음
    - 변경:
      * Task group으로 `ui.run_async()`, `run_execution_loop()`, `monitor_shutdown()` 병렬 실행
      * **Timeout**: `ready_event.wait()`에 10초 타임아웃 적용
      * **Error Handling**: ExecutionLoop 예외를 UI에 표시하고 재발생
      * **Shutdown Coordination**: ExecutionLoop 완료 시 `ShutdownRequestMessage` 전송
      * **Bidirectional Shutdown**: `monitor_shutdown()` task가 `shutdown_event.wait()` 후 `tg.cancel_scope.cancel()` 호출
      * **Exception Handling**: `except*` (ExceptionGroup) 및 `except` (일반 예외) 모두 처리
  - [x] 2.3 구현: `run()` 함수에서 모드별 분기
    ```python
    # run() 함수 내부 (line 194~)
    ui = create_ui("cli" if no_tui else "tui")
    session_store = SessionStore()

    try:
        if no_tui:
            # CLI 모드 (trio/asyncio 자동 선택 - backend 미지정)
            anyio.run(
                _main_cli,
                execute_agent,
                verify_agent,
                execute_prompt,
                verify_prompt,
                execute_extra_prompt,
                verify_extra_prompt,
                ui,
                session_store,
            )
        else:
            # TUI 모드 (Textual은 asyncio만 지원)
            anyio.run(
                _main_tui,
                execute_agent,
                verify_agent,
                execute_prompt,
                verify_prompt,
                execute_extra_prompt,
                verify_extra_prompt,
                ui,
                session_store,
                backend="asyncio",
            )
    except KeyboardInterrupt:
        # ...
    ```
    - 현재: 단일 `_main` 호출, `backend` 미지정
    - 변경:
      * `_main_cli` vs `_main_tui` 분기
      * **CLI 모드**: `backend` 미지정 (trio 지원)
      * **TUI 모드**: `backend="asyncio"` 명시 (Textual 제약)
  - [x] 2.4 구현: 기존 `_main()` 함수 제거
    - 현재: `async def _main(...)`
    - 변경: 삭제 (더 이상 사용 안 함)
  - [x] 2.5 테스트 작성: CLI 모드 테스트 (sisyphus/tests/test_cli.py)
    - 기존 테스트가 여전히 통과하는지 확인
    - `_main_cli` 로직이 기존 `_main`과 동일한지 검증
  - [x] 2.6 테스트 실행: `pytest -xvs sisyphus/tests/test_cli.py`
  - [x] 2.7 린트 및 타입 체크
    - [x] `ruff check sisyphus/cli.py`
    - [x] `basedpyright sisyphus/cli.py`
  - [x] 2.8 커밋: `git add sisyphus/cli.py sisyphus/tests/ && git commit -m "refactor: split _main into _main_cli and _main_tui for proper Textual integration"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] `_main_cli()` 함수가 기존 `_main()` 로직과 동일한가?
    - [x] `_main_tui()` 함수가 `anyio.create_task_group()`를 사용하는가?
    - [x] `ui.run_async()`가 task group에서 시작되는가?
    - [x] ExecutionLoop이 `ui.ready_event.wait()` 후 시작되는가?
    - [x] **Timeout**: `ready_event.wait()`에 10초 타임아웃이 적용되었는가?
    - [x] **Error Handling**: ExecutionLoop의 예외가 try-except로 처리되고 UI에 표시되는가?
    - [x] **Shutdown Coordination**: ExecutionLoop 완료 시 `ShutdownRequestMessage` 전송하는가?
    - [x] **Bidirectional Shutdown**: `monitor_shutdown()` task가 별도로 실행되어 `shutdown_event.wait()` 후 `tg.cancel_scope.cancel()` 호출하는가?
    - [x] **Exception Handling**: `except*` (ExceptionGroup) 만 처리 (except와 동시 사용 불가)
    - [x] **CLI Backend**: CLI 모드는 `backend` 파라미터가 없는가? (trio 지원)
    - [x] **TUI Backend**: TUI 모드만 `backend="asyncio"`가 명시되었는가?
    - [x] 기존 테스트가 여전히 통과하는가?
    - [x] 타입 체크와 린트가 통과하는가?

## Phase 3: 통합 테스트 및 검증

- [ ] 3. TUI 모드 실제 실행 테스트
  - [ ] 3.1 수동 테스트: `uv run sisyphus` (TUI 모드)
    ```bash
    uv run sisyphus
    ```
    - 예상: TUI 화면이 정상 표시되고 "No screens on stack" 에러 없음
    - 확인 사항:
      1. TUI 화면이 정상적으로 렌더링되는가?
      2. ExecutionLoop이 정상 실행되는가?
      3. 메시지가 화면에 표시되는가?
      4. Ctrl+C 2회로 종료 가능한가?
  - [ ] 3.2 수동 테스트: `uv run sisyphus --no-tui` (CLI 모드)
    ```bash
    uv run sisyphus --no-tui
    ```
    - 예상: CLI 모드가 기존처럼 정상 작동
    - 확인: CLI 출력이 정상인가?
  - [ ] 3.3 전체 테스트 실행: `pytest -xvs`
    - 모든 기존 테스트가 통과해야 함
    - 새로운 회귀가 없는지 확인
  - [ ] 3.4 린트 및 타입 체크 (전체)
    - [ ] `ruff check sisyphus/`
    - [ ] `basedpyright sisyphus/`
  - [ ] 3.5 커밋: `git add . && git commit -m "test: verify TUI and CLI modes work correctly"`
  - [ ] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [ ] `uv run sisyphus` 실행 시 TUI가 정상 표시되는가?
    - [ ] "No screens on stack" 에러가 발생하지 않는가?
    - [ ] ExecutionLoop이 정상 실행되는가?
    - [ ] `uv run sisyphus --no-tui` 실행 시 CLI 모드가 정상 작동하는가?
    - [ ] 모든 유닛 테스트가 통과하는가?
    - [ ] 린트와 타입 체크에 에러가 없는가?

# 최종 작업 검증 체크리스트

- [ ] 1. 기능 검증
  - [ ] TUI 모드에서 "No screens on stack" 에러가 해결되었는가?
  - [ ] TUI 화면이 정상적으로 표시되는가?
  - [ ] ExecutionLoop이 TUI와 함께 정상 실행되는가?
  - [ ] CLI 모드가 기존처럼 정상 작동하는가?
  - [ ] Ctrl+C로 TUI 종료가 가능한가?

- [ ] 2. 코드 품질 검증
  - [ ] 모든 타입 힌팅이 올바른가?
  - [ ] **CLI Backend**: CLI 모드는 `backend` 파라미터가 없는가? (trio 지원)
  - [ ] **TUI Backend**: TUI 모드만 `backend="asyncio"` 명시되었는가?
  - [ ] Task group 패턴이 올바르게 구현되었는가?
  - [ ] `ready_event` 동기화가 올바른가?
  - [ ] 린트와 타입 체크에 에러가 없는가?

- [ ] 3. 테스트 검증
  - [ ] 모든 유닛 테스트가 통과하는가?
  - [ ] TUI 모드 수동 테스트가 성공하는가?
  - [ ] CLI 모드 수동 테스트가 성공하는가?

- [ ] 4. 아키텍처 검증
  - [ ] Textual App 라이프사이클이 올바르게 관리되는가?
  - [ ] anyio와 Textual의 통합이 올바른가?
  - [ ] **Thread-Safe UI 업데이트**: `post_message()` 패턴이 올바르게 구현되었는가?
  - [ ] **Custom Message**: UpdateStatusMessage, ShowAgentMessage, ShutdownRequestMessage가 정의되었는가?
  - [ ] **Message 핸들러**: 각 메시지에 대한 핸들러가 예외 처리와 함께 구현되었는가?
  - [ ] **Shutdown Coordination**: ExecutionLoop ↔ TUI 양방향 종료가 올바르게 작동하는가?
  - [ ] **Error Propagation**: 한 task의 예외가 다른 task를 취소하는가?
  - [ ] **Timeout**: ready_event.wait()에 타임아웃이 적용되었는가?
  - [ ] **Graceful Degradation**: 타임아웃 발생 시 적절히 처리되는가?

- [ ] 5. 기존 기능 보존
  - [ ] CLI 모드 동작이 변경되지 않았는가?
  - [ ] 세션 관리가 여전히 작동하는가?
  - [ ] 프롬프트 처리가 정상인가?
  - [ ] 로깅이 정상적으로 작동하는가?

- [ ] 6. 실제 작업 검증
  - [ ] 직접 terminalcp 로, ./local-ignore/playground 밑에 ai-todolist.md 계획서를 작성하고서 sisyphus 를 "직접" 호출하여 실제로 작업이 완료되는것을 확인했는가?
