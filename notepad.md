# Task Started
All tasks execution STARTED: Sun Oct 12 12:38:59 KST 2025


[2025-10-12 12:48] - 1.1 `_run_unified_mode()` 메서드 설계

### DISCOVERED ISSUES
- Task Validator 로직 버그: `if self.task_validator is None: break` 로직이 Verify Phase를 건너뛰게 만듦
  - 위치: sisyphus/core/loop.py:305-309 (수정 전 _run_non_interactive_mode)
  - 원인: Task Validator가 없을 때 Execute 후 바로 종료되어 Verify Phase가 실행되지 않음
  - 해결: Task Validator가 있을 때만 체크하도록 로직 변경 (`if self.task_validator is not None:`)

- 무한 루프 버그: Task Validator 없이 Verify Agent만 있을 때 무한 루프 발생
  - 위치: sisyphus/core/loop.py:339-342 (Verify phase에서 FULLY_DONE=FALSE 처리)
  - 원인: FULLY_DONE 신호 없이 `continue`로 재시작하면서 무한 반복
  - 해결: Task Validator가 없으면 Verify 후 무조건 종료 (`if self.task_validator is None: break`)

### IMPLEMENTATION DECISIONS
- `_run_unified_mode()` 메서드를 `_run_non_interactive_mode()` 로직 기반으로 구현
  - Execute Phase: `_execute_phase()` 헬퍼 메서드 재사용
  - Task Validator: Optional 체크로 변경 (있을 때만 검증)
  - Verify Phase: `_verify_phase()` 헬퍼 메서드 재사용
  - 피드백 루프: Task Validator 존재 여부에 따라 분기

- 피드백 루프 조건 설계:
  - Task Validator가 **있으면**: FULLY_DONE=FALSE 시 피드백 포함해서 Execute 재시작
  - Task Validator가 **없으면**: Verify 한 번 실행 후 무조건 종료 (피드백 루프 불필요)
  - 이유: Task Validator 없이는 작업 완료 여부를 판단할 방법이 없기 때문

### PROBLEMS FOR NEXT TASKS
- Task 1.2: `run()` 메서드를 수정하여 `_run_unified_mode()` 호출하도록 변경 필요
- Task 1.3: Interactive 기능 테스트 필요 (현재는 기존 테스트만 통과 확인)
- `_run_interactive_mode()`와 `_run_non_interactive_mode()` 메서드 제거는 Task 4.1에서 수행

### VERIFICATION RESULTS
- 실행 명령: uv run pytest sisyphus/core/tests/test_loop*.py -v
- 결과: 50개 테스트 모두 PASSED (0.15초)
- 수정한 파일: sisyphus/core/loop.py
  - Line 158-258: `_run_unified_mode()` 메서드 추가
  - Line 260-354: `_run_non_interactive_mode()` Task Validator 로직 수정
  - 무한 루프 방지 로직 추가 (line 246-248, 342-344)

### LEARNINGS
- Task Validator의 역할: 작업 완료 여부 판단 + 피드백 루프 가능 여부 결정
- Task Validator 없는 경우: 단순 Execute + Verify 실행 후 종료 (피드백 루프 불가)
- Task Validator 있는 경우: Execute → Task 체크 → Verify → 피드백 루프 가능
- anyio stream() 패턴: Agent의 `stream()` 메서드가 자연스럽게 interactive 특성을 처리

소요 시간: 10분


