[2025-10-17 16:53] - ExecutionLoop 메시지 전송 개선

### IMPLEMENTATION DECISIONS
- anyio Task Group 패턴 사용: consume_stream과 monitor_input을 동시 실행
- monitor_scope는 매 while 루프마다 새로 생성: 재사용 시 cancel 상태가 유지되어 문제 발생
- assert 문으로 타입 체커 만족: 중첩 함수 내부에서 외부 변수 초기화를 추적하지 못하는 문제 해결
- consume_stream 정상 종료 시 monitor_scope.cancel() 호출: monitor_input을 강제 종료시켜 Task Group 정상 종료 유도

### VERIFICATION RESULTS
- 타입 체크: basedpyright로 loop.py 검증 완료 (0 errors)
- 커밋: 7bfa108 "add concurrent input monitoring to execution loop"

### LEARNINGS
- anyio Task Group 종료 메커니즘: 모든 task가 완료되어야 Task Group 종료
- CancelScope.cancel()은 해당 scope 내부 코드만 취소 (외부는 영향 없음)
- 중첩 함수에서 타입 체커는 외부 변수 초기화를 추적하지 못함 → assert 필요
- while True 무한 루프: resume을 무한히 지원하는 구조

소요 시간: 약 12분 (16:40 - 16:53)
[2025-10-17 16:56] - ChatLog 스크롤 타이밍 수정

### IMPLEMENTATION DECISIONS
- call_after_refresh() 사용: write() 호출 직후 렌더링 사이클 미완료 문제 해결
- 4개 메서드 수정: write_user_message, write_execute_message, write_verify_message, write_completion_message
- 콜백 전달 방식: 괄호 없이 함수 자체 전달 (self._auto_scroll_if_needed)

### VERIFICATION RESULTS
- 타입 체크: basedpyright로 chat_log.py 검증 완료 (0 errors, 0 warnings)
- 커밋: baa95c2 "fix chat_log scroll timing with call_after_refresh"
- 변경 파일: sisyphus/ui/tui/components/chat_log.py (4개 메서드)

### LEARNINGS
- Textual 렌더링 타이밍: write() 호출 직후 max_scroll_y가 아직 업데이트 안 됨
- call_after_refresh(): 다음 렌더링 완료 후 콜백 실행 → 정확한 max_scroll_y 사용 가능
- 동기 호출의 문제: _auto_scroll_if_needed()를 즉시 호출하면 이전 max_scroll_y 값으로 계산됨

소요 시간: 약 3분 (16:53 - 16:56)
