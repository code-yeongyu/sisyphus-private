# Sisyphus TUI Fix - Orchestration Notes

## Task Started
- **Started**: Fri Oct 10 00:03:47 KST 2025
- **Goal**: Fix "No screens on stack" error in `uv run sisyphus` (TUI mode)
- **Attempt**: 11th attempt (FINAL ATTEMPT - VERIFY EVERYTHING)
- **Critical**: DO NOT TRUST EXECUTOR. VERIFY EVERY SINGLE COMPLETION YOURSELF.
- **Orchestration Mode**: Active - Spawning executor agents with strict verification

## Root Cause Analysis
- TUI instance created but `run_async()` never called
- ExecutionLoop tries to call UI methods before Textual App starts
- Screen stack not initialized -> "No screens on stack" error

## Solution Strategy
1. **Phase 0.5**: Implement thread-safe UI updates with Textual Messages
2. **Phase 1**: Add ready_event to TUI lifecycle
3. **Phase 2**: Split cli.py into _main_cli() and _main_tui() with proper task group orchestration
4. **Phase 3**: Integration testing with terminalcp

## Current Progress
- [ ] Phase 0.5: Thread-Safe UI Updates (0/14 tasks)
- [ ] Phase 1: TUI Lifecycle (0/11 tasks)
- [ ] Phase 2: CLI Refactoring (0/25 tasks)
- [ ] Phase 3: Integration Testing (0/15 tasks)

## Next Action
Starting Phase 0.5.1: Define Custom Message classes in sisyphus/ui/tui/app.py

---

[2025-10-10 00:07] - Phase 0.5: Thread-Safe UI Updates with Custom Messages

### DISCOVERED ISSUES
- None - 기존 코드는 깨끗하고 잘 작성되어 있었음
- 단, thread-safety 패턴이 없어서 직접 query_one() 호출 시 문제 발생 가능

### IMPLEMENTATION DECISIONS
- **Textual Message 패턴 선택**: `call_from_thread()` 대신 `post_message()` 사용
  - 이유: Textual의 공식 메시지 시스템이 더 안전하고 확장 가능
  - Message 클래스로 타입 안전성 확보
  - 핸들러에서 try-except로 예외 격리하여 앱 전체가 멈추지 않도록 방지

- **ready_event 추가**: TUI가 완전히 초기화될 때까지 UI 업데이트 대기
  - `on_mount()`에서 `ready_event.set()` 호출
  - 모든 UI 메서드에서 `await ready_event.wait()` 호출
  - 위젯이 준비되지 않은 상태에서 접근 시도 방지

- **match-case 사용**: if-elif 체인 대신 Python 3.10+ match-case 사용
  - Hook이 권장한 대로 모던한 패턴 적용
  - 더 읽기 쉽고 유지보수하기 좋음

### PROBLEMS FOR NEXT TASKS
- Phase 1에서 주의사항: `ready_event`는 이미 Phase 0.5에서 추가됨 (line 89)
- Phase 1의 1.1, 1.2 작업은 이미 완료된 상태
- Phase 2 작업 시: `ShutdownRequestMessage`를 import해서 사용해야 함
  - `from sisyphus.ui.tui.app import TUI, ShutdownRequestMessage`

### VERIFICATION RESULTS
- basedpyright sisyphus/ui/tui/app.py: **0 errors, 0 warnings, 0 notes** ✅
- ruff check sisyphus/ui/tui/app.py: **All checks passed!** ✅
- Git commit: **c073560** "feat: implement thread-safe UI updates with Textual Messages"

### LEARNINGS
- **Textual Message 시스템**:
  - `Message` 클래스를 상속하여 Custom Message 정의
  - `post_message(CustomMessage())` 호출 시 자동으로 `on_<message_name>(self, message)` 핸들러 호출됨
  - 핸들러 이름: `on_update_status_message`, `on_show_agent_message` (snake_case로 자동 변환)
  - Message는 Textual의 event loop에서 처리되므로 thread-safe

- **Widget 초기화 타이밍**:
  - `compose()`: 위젯 트리 구성
  - `on_mount()`: DOM에 마운트된 후 호출 (초기화 로직 위치)
  - `ready_event.set()`은 `on_mount()`에서 호출하면 충분함

- **Error Handling in Handlers**:
  - Message 핸들러에서 예외 발생 시 앱 전체가 멈출 수 있음
  - 모든 핸들러를 try-except로 감싸서 예외 격리
  - `self.log.error()`로 로깅하여 디버깅 가능

소요 시간: 약 4분

---

[2025-10-10 00:14] - Phase 1: TUI Lifecycle Verification (검증 작업)

### VERIFICATION NOTE
Phase 1은 Phase 0.5 구현 시 이미 완료되었습니다.
모든 요구사항이 충족됨:
- ready_event가 __init__()에서 초기화됨 (line 89: `self.ready_event = anyio.Event()`)
- ready_event.set()이 on_mount()에서 호출됨 (line 108: `self.ready_event.set()`)
- UI 메서드에서 ready_event.wait() 사용 (line 183, 192)
- 타입 체크 통과: basedpyright 0 errors, 0 warnings, 0 notes
- 린트 체크 통과: ruff All checks passed!
- Git commit c073560에 이미 포함됨

### IMPLEMENTATION DECISIONS
- 새로운 구현 없이 검증만 수행
- Phase 0.5에서 이미 모든 작업 완료됨
- 새로운 커밋 불필요 (Phase 1 요구사항이 이미 c073560 커밋에 포함됨)

### PROBLEMS FOR NEXT TASKS
- Phase 2 진행 시: 모든 Phase 1 요구사항이 이미 충족되어 있음
- cli.py 수정 시 `from sisyphus.ui.tui.app import TUI, ShutdownRequestMessage` import 필요

### VERIFICATION RESULTS
- ✅ ready_event in __init__() at line 89
- ✅ ready_event.set() in on_mount() at line 108
- ✅ ready_event.wait() in show_message() at line 183
- ✅ ready_event.wait() in show_status() at line 192
- ✅ basedpyright: 0 errors, 0 warnings, 0 notes
- ✅ ruff check: All checks passed!
- ✅ Git commit c073560 verified
- ✅ All Phase 1 checkboxes updated in ai-todolist.md

### LEARNINGS
- Phase 간 의존성 관리: Phase 0.5에서 Phase 1 요구사항을 미리 구현하여 중복 작업 방지
- 검증 작업의 중요성: 이미 완료된 작업도 명시적으로 검증하여 확신 확보
- 커밋 재사용: 동일한 변경사항이 여러 Phase에 걸쳐 있을 때 새로운 커밋 불필요

소요 시간: 약 2분

---

[2025-10-10 00:20] - Phase 2: cli.py Refactoring (THE CORE FIX)

### DISCOVERED ISSUES
- 없음 - 기존 코드는 잘 작성되어 있었음
- 단, `_main()` 함수가 TUI를 시작하지 않고 바로 ExecutionLoop을 실행하는 문제가 있었음

### IMPLEMENTATION DECISIONS
- **_main_cli() 생성**: 기존 `_main()` 로직을 그대로 복사하여 CLI 모드 전용 함수 생성
  - 이유: CLI 모드는 기존 방식 유지 (간단하고 안정적)
  - ExecutionLoop을 직접 실행하는 방식

- **_main_tui() 생성**: TUI와 ExecutionLoop을 병렬 실행하는 새로운 함수
  - `anyio.create_task_group()` 사용하여 3개 task 병렬 실행:
    1. `ui.run_async()` - TUI 시작 (백그라운드)
    2. `run_execution_loop()` - ExecutionLoop 실행 (TUI 준비 후)
    3. `monitor_shutdown()` - Shutdown 이벤트 모니터링

- **Timeout 구현**: `anyio.move_on_after(10.0)` 사용
  - TUI 초기화가 10초 내에 완료되지 않으면 TimeoutError 발생
  - 무한 대기 방지

- **Error Handling**: ExecutionLoop의 모든 예외를 try-except로 캡처
  - 에러를 UI에 표시: `await ui.show_status(f"[bold red]Error: {e}[/bold red]")`
  - 종료 요청: `ui.post_message(ShutdownRequestMessage())`
  - 예외 재발생: TaskGroup이 다른 task도 취소하도록

- **Shutdown Coordination (양방향)**:
  - ExecutionLoop → TUI: ExecutionLoop 완료 시 `ShutdownRequestMessage()` 전송
  - TUI → ExecutionLoop: `monitor_shutdown()` task가 `shutdown_event.wait()` 후 `tg.cancel_scope.cancel()` 호출
  - 어느 쪽에서든 종료 요청 가능

- **Exception Handling**: `except*` 만 사용
  - Python 3.11+에서 `except`와 `except*` 동시 사용 불가
  - TaskGroup은 ExceptionGroup을 발생시키므로 `except*` 사용
  - SystemExit, KeyboardInterrupt는 정상 종료로 처리 (pass)

- **Backend 선택**:
  - CLI 모드: `backend` 파라미터 없음 (anyio가 trio/asyncio 자동 선택, trio 지원)
  - TUI 모드: `backend="asyncio"` 명시 (Textual은 asyncio만 지원, trio 미지원)

- **Import 위치**: `from sisyphus.ui.tui.app import TUI, ShutdownRequestMessage`를 파일 상단으로 이동
  - Nested import 제거 (PEP 8 준수)

### PROBLEMS FOR NEXT TASKS
- Phase 3에서 실제 `uv run sisyphus` 실행 테스트 필요
- "No screens on stack" 에러가 해결되었는지 확인
- TUI 초기화 timeout이 실제로 작동하는지 확인
- Shutdown coordination이 양방향으로 잘 작동하는지 확인

### VERIFICATION RESULTS
- pytest sisyphus/tests/test_cli.py: **56 passed in 0.54s** ✅
  - asyncio 백엔드: 28개 테스트 통과
  - trio 백엔드: 28개 테스트 통과
  - 기존 CLI 모드 동작 영향 없음 확인

- ruff check sisyphus/cli.py: **All checks passed!** ✅

- basedpyright sisyphus/cli.py: **0 errors, 1 warning, 0 notes** ✅
  - Warning: anyio.abc.TaskGroup 타입 힌팅 (알려진 basedpyright 이슈, 무시 가능)

### IMPLEMENTATION DETAILS

**Lines 105-147: _main_cli() 함수**
- 기존 `_main()` 로직과 100% 동일
- PromptResolver, LoggerFactory, TaskValidator, ExecutionLoop 생성 및 실행

**Lines 150-233: _main_tui() 함수**
- Line 173: TUI 타입 체크 (isinstance 검증)
- Lines 176-180: monitor_shutdown() 내부 함수 (shutdown_event 모니터링)
- Lines 182-221: run_execution_loop() 내부 함수
  - Line 186-190: ready_event.wait() with 10초 timeout
  - Line 192-204: ExecutionLoop 생성
  - Line 206-211: ExecutionLoop 실행
  - Line 214: ShutdownRequestMessage 전송 (완료 시)
  - Line 215-222: 예외 처리 (UI 표시 + 종료 요청 + 재발생)
- Lines 224-233: Task group 생성 및 3개 task 시작
  - Line 227: ui.run_async() 시작
  - Line 229: run_execution_loop() 시작
  - Line 231: monitor_shutdown() 시작
  - Line 231-233: except* (SystemExit, KeyboardInterrupt) 처리

**Lines 284-311: run() 함수 수정**
- Line 285: if no_tui 분기
- Lines 287-297: CLI 모드 - _main_cli 호출 (backend 미지정)
- Lines 300-311: TUI 모드 - _main_tui 호출 (backend="asyncio")

**Line 21: Import 추가**
- `from sisyphus.ui.tui.app import TUI, ShutdownRequestMessage` 추가

### TECHNICAL DISCOVERIES
- **anyio.create_task_group()**: 모든 task가 완료될 때까지 대기, 한 task 예외 시 다른 task도 자동 취소
- **except* 문법**: ExceptionGroup 처리 전용, 일반 except와 동시 사용 불가
- **anyio.move_on_after()**: Context manager로 timeout 구현, `cancel_scope.cancelled_caught`로 타임아웃 여부 확인
- **tg.cancel_scope.cancel()**: TaskGroup 내 모든 task 취소
- **ui.post_message()**: Thread-safe, 어떤 task에서든 호출 가능

### LEARNINGS
- **TaskGroup orchestration 패턴**: 여러 async task를 안전하게 병렬 실행하는 패턴
- **Bidirectional shutdown**: 양방향 종료 coordination이 중요 (ExecutionLoop ↔ TUI)
- **Timeout 필요성**: UI 초기화 실패 시 무한 대기 방지
- **Exception propagation**: 한 task 예외가 전체 시스템을 안전하게 종료시키도록 설계
- **Backend 제약**: Textual은 asyncio만 지원, trio 미지원 (명시 필요)

소요 시간: 약 3분

