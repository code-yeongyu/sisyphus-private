# Task from Issue #12

**Title:** Sisyphus first work: Fix TUI bugs, fix retry when session resuming failed

**Description:**
# 사용자의 최초 요청 (기록용)
지금 이거 전체 루프세션과 tui 에 몇개의 버그가 있는데,

1. Prompt is too long 처럼 이제 더이상 세션이 진행이 불가능한 경우에도 계속 같은 세션에서 resume 하려고 하고있어 (claude code) - 일단 prompt is too long 은 known pattern 이니까 이 경우 새 세션을 만드는게맞고, claude code 가 exit 0 (아마 우리는 sdk 니까 exception?) 을 연속해서 세번이상 반환할경우 resume 하지말고 continue 하도록 해줬으면 해. (버그수정)
2. TUI 모드에서 로그가 보이는 부분이, 자꾸 새 로그가 쌓이면 스크롤이 맨 밑으로 내려가. 스크롤바가 맨 밑에 있을 경우에만 새 로그가 쌓이면 스크롤이 내려가도록 하고 그게 아니면 스크롤바가 내려가지 않도록 해줘. 단, 저번에 이 작업하다가 아예 스크롤바를 망가뜨렸었으니까 그거에 특히 조심해. 스크롤 기능 자체를 망가뜨리지 않도록 조심해. (아예 pinning 해버리면안된다는이야기야)
3. input bar 의 경우 지금 focus 될 때만 안내 메시지가 뜨고 unfocsed 상태에서는 이게 안뜨는데 그래서 되게 어색해. 항상 안내메시지가 뜨고, 메시지가 새로 type 됐을때만 placeholder 로써 안보이게 기능하도록 하는게 맞아. 이렇게 고쳐줬으면해.

## 사용자가 이후에 추가 요청한 내용들 (기록용)
없음

# 작업 목표
1. ExecutionLoop에서 세션 재개 불가능한 에러 발생 시 자동으로 새 세션 시작
2. TUI ChatLog의 스크롤 동작 개선 (사용자가 위로 스크롤했을 때는 자동 스크롤 비활성화)
3. InputBar의 placeholder/suggestion 표시 방식 개선 (항상 표시, 텍스트 입력 시만 숨김)

# 작업 디테일 레벨
detail_level = balanced

# 작업 배경
현재 sisyphus 프로젝트에서 다음과 같은 UX 문제가 발생하고 있습니다:

**현재 상태:**
- ✅ ExecutionLoop의 기본 세션 관리 로직 존재
- ✅ SessionResumeError 예외 처리 구현되어 있음
- ❌ "Prompt is too long" 등 복구 불가능한 에러에서도 계속 같은 세션 재개 시도
- ❌ 기타 에러가 연속으로 발생할 경우 무한 루프 가능
- ✅ TUI ChatLog는 RichLog 상속
- ❌ ChatLog가 항상 `scroll_end()` 호출 → 사용자가 위로 스크롤해도 강제로 맨 아래로 이동
- ✅ InputBar의 suggestion 기능 구현되어 있음
- ❌ InputBar가 focus 상태에서만 suggestion 표시 → unfocused 상태에서는 빈 화면

**문제점:**
1. **세션 재개 무한 루프**: "Prompt is too long"이나 연속 에러 발생 시 계속 같은 세션 재개 시도 → 작업 진행 불가
2. **스크롤 UX 문제**: 사용자가 이전 로그를 읽으려고 스크롤업 했는데 새 메시지가 오면 강제로 아래로 이동 → 읽던 내용 놓침
3. **InputBar 가이드 부족**: unfocused 상태에서 placeholder가 안 보여서 사용법을 모르는 사용자는 혼란

**목표:**
- 복구 불가능한 세션 에러 발생 시 자동으로 새 세션 시작하여 작업 계속 진행
- 사용자가 스크롤업 했을 때는 자동 스크롤 멈춤, 맨 아래로 다시 내려오면 재개
- InputBar의 안내 메시지가 항상 보이도록 개선 (텍스트 입력 시만 숨김)

# 작업 시작 여부
is_execution_started = TRUE

# 모든 목표 달성 여부
is_all_goals_accomplished = TRUE

# 병렬 실행 여부
parallel_requested = FALSE

# 현재 진행 중인 작업
- ✅ 작업 완료: 4. 전체 통합 테스트 및 검증 (items 4.1-4.4)
   - 모든 subtask 완료
   - 478 tests passed, 0 failures
   - All lint checks passed
   - 0 type errors
   - Code review 완료
   - 다음 작업 예약 대기 중

# 필요한 사전 지식

## ExecutionLoop 세션 관리 개념
- **Session Resume**: 이전 대화 컨텍스트를 유지하며 세션 재개
- **SessionResumeError**: 세션 재개 실패 시 발생하는 예외
- **연속 에러 정의**: SessionResumeError 또는 기타 예외가 3회 연속 발생 (정상 실행 시 리셋)
- **세션 초기화**: `await self.session_store.save_session(agent_type, None)` 호출

## Textual TUI 스크롤 관리
- **RichLog**: Textual의 로그 위젯, `auto_scroll` 속성 제공
- **scroll_end()**: 강제로 맨 아래로 스크롤
- **call_after_refresh()**: Textual 렌더링 완료 후 콜백 실행 (race condition 방지)
- **scroll_offset.y**: 현재 스크롤 Y 위치
- **max_scroll_y**: 최대 스크롤 가능 Y 위치

## Textual TextArea placeholder
- **TextArea.suggestion**: placeholder 역할을 하는 텍스트 속성
- **text 속성**: 현재 입력된 텍스트

# 작업 계획

## 세션 재개 실패 카운터 정책

**카운터 증가 조건:**
- SessionResumeError 발생: +1
- except* Exception 블록에서 예외 발생: +1
- 최대값: 3회

**카운터 리셋 조건:**
- start_session() 성공 직후 (try 블록 내 마지막): 0으로 리셋
- while True 루프 정상 종료 시 (break 직전): 0으로 리셋

**세션 초기화 조건:**
- 카운터 >= 3: 세션 스토어 초기화 후 카운터 리셋

## 현재 코드 구조 (sisyphus/core/loop.py)

```python
class ExecutionLoop:
    def __init__(self, ...):
        self._interrupt_flag = False
        # 카운터 추가 필요

async def _execute_phase(self, ...):
    session_id = await self.session_store.get_session(agent_type)
    
    # (line 234-248) 세션 재개 시도
    try:
        actual_session_id = await self.execute_agent.start_session(session_id)
        # 성공 시 카운터 리셋 위치
    except SessionResumeError as e:
        # 카운터 증가 필요
        actual_session_id = await self.execute_agent.start_session(None)
    
    await self.session_store.save_session(agent_type, actual_session_id)
    
    # (line 257-344) 스트림 처리 루프
    while True:
        try:
            async with anyio.create_task_group() as tg:
                tg.start_soon(consume_stream)
                tg.start_soon(monitor_input)
        except* SessionLimitError:
            raise  # 재시도
        except* Exception as exception_group:
            # (line 315-322) 카운터 증가 필요
            raise
        
        # 인터럽트 처리 또는 break
        if not self._interrupt_flag:
            if not self._resumed_once:
                break  # 정상 종료 - 카운터 리셋 위치
```

## 구현 방법

### 1. ExecutionLoop 세션 복구 로직 개선

**변경 파일**: `sisyphus/core/loop.py`

**핵심 변경:**
1. `__init__()`: `self._execute_resume_fail_count: int = 0` 추가
2. SessionResumeError except 블록:
   - 카운터 증가
   - 로그에 "attempt N/3" 표시
   - 3회 이상 시: 세션 스토어 초기화 (`save_session(agent_type, None)`) + 카운터 리셋 + 로그 출력
   - 이후 새 세션 시작 (기존 로직 유지)
3. except* Exception 블록 (line 315-322):
   - 카운터 증가
   - 3회 이상 시: 세션 스토어 초기화 + 카운터 리셋 + 로그 출력 + return (함수 종료)
   - 3회 미만: 예외를 다시 raise (기존 동작 유지)
4. start_session() 성공 후 (try 블록 내부, line 241 다음에 카운터 리셋 추가): 카운터 = 0
5. while 루프 break 직전 (line 344): 카운터 = 0

**세션 초기화 후 동작:**
- SessionResumeError: 초기화 후 새 세션 시작 (start_session(None) 호출)
- Exception (3회 이상): 초기화 후 return으로 함수 종료 → 외부 _run_unified_mode()가 다음 iteration 진행
- Exception (3회 미만): 예외 raise → 프로그램 종료 (기존 동작)

### 2. ChatLog 스크롤 동작 개선

**변경 파일**: `sisyphus/ui/tui/components/chat_log.py`

**핵심 변경:**
1. `_should_auto_scroll()` 헬퍼 메서드 추가:
   - `return self.scroll_offset.y >= self.max_scroll_y - 5`
   - 5줄 여유: UX 개선
2. 모든 write 메서드 (write_user_message, write_execute_message, write_verify_message, write_completion_message):
   - 기존 `self.scroll_end()` 제거
   - 조건부 스크롤: `if self._should_auto_scroll(): self.call_after_refresh(self.scroll_end)`

**주의사항**:
- `call_after_refresh()` 사용으로 race condition 방지
- `auto_scroll=True` 속성은 유지

### 3. InputBar suggestion 항상 표시

**변경 파일**: `sisyphus/ui/tui/components/input_bar.py`

**핵심 변경:**
- `_update_suggestion()` 메서드 확장:
  - Queue 메시지 있으면: Queue status 표시 (기존 로직 유지)
  - 텍스트 있으면 (`self.text.strip()`): suggestion 숨김 (`""`)
  - 텍스트 없으면: `self.suggestion = self._original_suggestion` (이미 __init__에서 정의됨)

**참고**: `self._original_suggestion`은 이미 `__init__()`에서 `"Type a message... (ESC: pause)"`로 초기화되어 있음

**추가 조치 불필요**: `on_key()` 메서드에서 이미 `_update_suggestion()` 호출 중

## 프로젝트 커밋 메시지 스타일
- 형식: `<type>: <description>`
- 타입: `fix`, `feat`, `chore` 등
- 예시:
  - `fix: handle unrecoverable session errors with auto-reset`
  - `fix: improve chatlog scroll behavior for better ux`
  - `fix: show inputbar placeholder always regardless of focus`

# TODOs

- [x] 1. ExecutionLoop 세션 복구 로직 개선
   - [x] 1.1 __init__에 카운터 추가: self._execute_resume_fail_count: int = 0
   - [x] 1.2 SessionResumeError except 블록에 카운터 로직 추가
      - 카운터 증가
      - 로그에 attempt N/3 표시
      - 3회 이상 시 세션 스토어 초기화
   - [x] 1.3 except* Exception 블록에 카운터 로직 추가 (line 315-322)
      - 카운터 증가
      - 3회 이상 시: 세션 스토어 초기화 + return
      - 3회 미만: 예외 raise (기존 동작)
   - [x] 1.4 start_session() 성공 후 카운터 리셋 (try 블록 내부, line 241 다음)
   - [x] 1.5 while 루프 break 직전 카운터 리셋 (line 344)
   - [x] 1.6 수동 테스트 (선택적이지만 권장)
      - 로그 파일에서 "attempt N/3" 출력 확인
      - 3회 이상 실패 시 "세션 스토어 초기화" 로그 확인
   - [x] 1.7 린트 및 타입 체크: ruff check, basedpyright
   - [x] 1.8 커밋: git add sisyphus/core/loop.py && git commit -m "fix: handle unrecoverable session errors with auto-reset"

- [x] 2. ChatLog 스크롤 동작 개선
   - [x] 2.1 _should_auto_scroll() 헬퍼 메서드 추가
      - 로직: scroll_offset.y >= max_scroll_y - 5
   - [x] 2.2 모든 write 메서드 수정
      - write_user_message, write_execute_message, write_verify_message, write_completion_message
      - 기존 scroll_end() 제거
      - 조건부 스크롤 추가: if self._should_auto_scroll(): self.call_after_refresh(self.scroll_end)
   - [x] 2.3 수동 테스트: TUI 실행 후 PageUp으로 스크롤업, 새 메시지 시 위치 유지 확인
   - [x] 2.4 린트 및 타입 체크
   - [x] 2.5 커밋: git add sisyphus/ui/tui/components/chat_log.py && git commit -m "fix: improve chatlog scroll behavior for better ux"

- [x] 3. InputBar placeholder 항상 표시
   - [x] 3.1 _update_suggestion() 메서드 확장
      - Queue 메시지 있으면: 기존 로직
      - self.text.strip() 있으면: self.suggestion = ""
      - 텍스트 없으면: self.suggestion = self._original_suggestion
   - [x] 3.2 수동 테스트: Tab으로 unfocused, placeholder 표시 확인
      - 자동화 테스트로 검증: test_update_suggestion__if_user_typed_text__hides_suggestion, test_update_suggestion__if_text_deleted__shows_suggestion_again
   - [x] 3.3 린트 및 타입 체크
      - Lint: All checks passed!
      - Type: 0 errors, 0 warnings
   - [x] 3.4 커밋: git add sisyphus/ui/tui/components/input_bar.py && git commit -m "fix: show inputbar placeholder always regardless of focus"
      - Commit SHA: 6dd6a01

- [x] 4. 전체 통합 테스트 및 검증
   - [x] 4.1 기존 테스트: uv run pytest -v
   - [x] 4.2 전체 린트: uv run ruff check sisyphus/
   - [x] 4.3 전체 타입 체크: uv run basedpyright
   - [x] 4.4 종합 수동 테스트: 세 가지 버그 동시 확인

- [x] 5. 작업 완료 처리
   - [x] 5.1 git status 확인: nothing to commit, working tree clean
   - [x] 5.2 is_all_goals_accomplished = TRUE 업데이트

# 최종 작업 검증 체크리스트

## 1. 세션 복구 로직
- [x] __init__에 _execute_resume_fail_count 속성 추가되었는가?
- [x] SessionResumeError except 블록에서 카운터 증가하는가?
- [x] except* Exception 블록에서 카운터 증가하는가?
- [x] 카운터 >= 3 시 세션 스토어 초기화하는가?
- [x] start_session() 성공 후 카운터 리셋되는가?
- [x] while 루프 종료 시 카운터 리셋되는가?
- [x] 로그에 attempt N/3 출력되는가?

## 2. ChatLog 스크롤
- [x] _should_auto_scroll() 메서드 추가되었는가?
- [x] 모든 write 메서드에서 조건부 스크롤하는가?
- [x] PageUp 후 스크롤 위치 유지되는가?
- [x] End 후 자동 스크롤 재개되는가?

## 3. InputBar placeholder
- [x] _update_suggestion()에 텍스트 상태 확인 로직 추가되었는가?
- [x] unfocused 상태에서도 placeholder 표시되는가?
- [x] 텍스트 입력 시 placeholder 숨겨지는가?
- [x] 텍스트 삭제 시 placeholder 다시 나타나는가?

## 4. 코드 품질
- [x] 전체 린트 통과: uv run ruff check sisyphus/
- [x] 전체 타입 체크 통과: uv run basedpyright
- [x] 기존 테스트 통과: uv run pytest
- [x] 모든 커밋 완료: git status


---
