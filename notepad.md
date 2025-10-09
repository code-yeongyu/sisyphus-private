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

