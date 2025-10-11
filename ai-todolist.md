# 사용자의 최초 요청 (기록용)
execute loop 이 끝나면
1. ai-todolist.md 의 모든 빈 체크박스 (- [ ]) 검사
2. is_all_goals_accomplished 가 TRUE 인지 검사

아니라면 다시 execute loop 고, 저거가 통과하면
verify 실행시키고, fully done true 일 경우에만 종료, 아닐 경우 verify 피드백 그대로 캡쳐해서, 그 내용 다시 넣어서 execute loop 돌리도록 하는 (그 내용은 프롬프트를 통해서 전해져야하고, 단 한번만 들어가야하고, verify 는 매번 새 세션으로 소환되어야 함)

단 verify 소환시에는 다음과 같은 형태여야 함
<예전에 줬던 피드백 내용>
1차 피드백
2차 피드백
</예전에 줬던 피드백 내용>

지금 작업이 완료됐다 어쩌구 저쩌구 위의 내용 포함 검증
{{원래 검증 프롬프트}}

기존의 코드베이스 구조를 면밀히 파악하고, 의도한 구조대로 적절한 위치에 제대로된 구조에 맡게 들어가도록 작업계획서 작성

## 사용자가 이후에 추가 요청한 내용들 (기록용)
(없음)

# 디테일 레벨
detail_level = detailed

# 작업 목표
- ExecutionLoop의 `_run_non_interactive_mode`에서 verify agent의 피드백을 execute agent에게 전달하는 메커니즘 구현
- Verify phase가 "FULLY_DONE = TRUE"를 반환할 때만 loop 종료
- Verify phase의 모든 피드백을 누적하여 execute phase에 전달
- Task validator 체크는 execute loop 재시작 전에만 수행

# 작업 배경
현재 ExecutionLoop의 non-interactive mode에서:
1. Execute phase 실행
2. Verify phase 실행 (피드백이 UI에만 표시되고 저장/전달되지 않음)
3. Task validator로 완료 체크 (체크박스 + is_all_goals_accomplished)
4. 미완료 시 같은 프롬프트로 다시 Execute phase 반복

**문제점:**
- Verify agent의 피드백이 execute agent에게 전달되지 않음
- "FULLY_DONE = TRUE" 신호를 체크하지 않음
- Architect가 제공한 개선 사항이 다음 iteration에 반영되지 않음

**의도된 동작:**
1. Execute phase 실행
2. Task validator 체크 → 미완료 시 Execute phase 재시작 (verify 없이)
3. Task validator 통과 시에만 Verify phase 실행
4. Verify 피드백 수집 및 "FULLY_DONE" 체크
5. FULLY_DONE = TRUE → 종료
6. FULLY_DONE = FALSE → 누적된 피드백을 포함해서 Execute phase 재시작

# 작업 시작 여부
is_execution_started = FALSE

# 모든 목표 달성 여부
is_all_goals_accomplished = TRUE

# 병렬 실행 여부
parallel_requested = FALSE

# 현재 진행 중인 작업
TODO 5: 통합 테스트 - 전체 피드백 루프 동작 검증 중

# 필요한 사전 지식
- Python async/await 패턴
- anyio 비동기 프레임워크
- AgentMessage 타입 (sisyphus.utils.types)
- TaskValidator의 체크 메서드들
- Verify prompt의 "FULLY_DONE = TRUE" 완료 신호
- SessionLimitError 예외 처리

## 파일 구조 및 역할
- `sisyphus/core/loop.py`: ExecutionLoop 클래스 (메인 수정 대상)
- `sisyphus/core/prompts.py`: DEFAULT_VERIFY_PROMPT (피드백 형식 참고)
- `sisyphus/core/tasks.py`: TaskValidator (완료 검증)
- `sisyphus/utils/types.py`: AgentMessage (메시지 타입)
- `sisyphus/ui/base.py`: UIProtocol (메시지 표시)

## 맥락 이해를 위해 참고해야 할 파일들
### 1. sisyphus/core/loop.py
- **역할**: Execute-Verify 2단계 실행 루프
- **참고할 부분**:
  - `_run_non_interactive_mode` (158-214줄): 메인 루프 로직
  - `_execute_phase` (215-265줄): Execute agent 실행
  - `_verify_phase` (267-319줄): Verify agent 실행 (수정 필요)
- **예상 코드 구조**:
  ```python
  async def _run_non_interactive_mode(self, ...):
      iteration = 0
      while True:
          # Execute phase
          await self._execute_phase(execute_prompt, execute_extra)

          # Task validator 체크
          if not (goals + checkboxes completed):
              continue  # Execute 재시작

          # Verify phase (task 완료 시에만)
          if self.verify_agent:
              feedback, fully_done = await self._verify_phase(...)
              if fully_done:
                  break  # 완전 종료
              # else: 피드백 포함해서 Execute 재시작
  ```

### 2. sisyphus/core/prompts.py
- **역할**: Execute/Verify 기본 프롬프트 정의
- **주의사항**:
  - DEFAULT_VERIFY_PROMPT의 249줄: "FULLY_DONE = TRUE" 신호 형식
  - 262-268줄: "피드백이 agent에게 전달된다"는 의도 명시
  - 피드백을 프롬프트에 추가할 때 명확한 구분자 사용 필요

### 3. sisyphus/core/tasks.py
- **역할**: ai-todolist.md 검증 도구
- **주의사항**:
  - `check_all_goals_accomplished()`: is_all_goals_accomplished = FALSE 체크
  - `check_all_checkboxes_completed()`: 모든 체크박스 [x] 확인
  - 둘 다 통과해야 verify phase 진입

# 작업 계획

## PRDs & Structures
**목표:** ExecutionLoop의 피드백 루프 구현

**핵심 흐름:**
```
┌─────────────────────────────────────────────┐
│          Start Iteration N                  │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  Execute Phase     │◄──────────┐
         │  (with feedback)   │           │
         └────────┬───────────┘           │
                  │                        │
                  ▼                        │
         ┌────────────────────┐           │
         │  Task Validator    │           │
         │  Check             │           │
         └────────┬───────────┘           │
                  │                        │
         ┌────────┴────────┐              │
         │                 │              │
    Not Done          All Done            │
         │                 │              │
         └─────────────────┘              │
                           │              │
                           ▼              │
                  ┌────────────────────┐  │
                  │  Verify Phase      │  │
                  │  (new session)     │  │
                  └────────┬───────────┘  │
                           │              │
                  ┌────────┴────────┐     │
                  │                 │     │
          FULLY_DONE=TRUE    FULLY_DONE=FALSE
                  │                 │     │
                  ▼                 │     │
            ┌─────────┐            │     │
            │  Exit   │            └─────┘
            └─────────┘         (feedback 누적)
```

**컴포넌트 상호작용:**
1. `_run_non_interactive_mode`: 메인 orchestrator
2. `_execute_phase`: 작업 실행 (피드백 받음)
3. `_verify_phase`: 검증 및 피드백 생성 (수정 필요)
4. `TaskValidator`: 완료 여부 판단
5. `verify_feedback_history`: 누적된 피드백 리스트 (신규)

## 구현 세부사항

### 1. `_verify_phase` 반환 타입 변경
- 현재: `-> None`
- 변경 후: `-> tuple[str, bool]`
  - `str`: 전체 피드백 내용 (모든 assistant 메시지 합침)
  - `bool`: FULLY_DONE = TRUE 여부

### 2. `_verify_phase` 내부 로직 추가
- `feedback_messages: list[str]` 변수로 메시지 수집
- `fully_done: bool = False` 변수로 완료 신호 감지
- "FULLY_DONE = TRUE" 문자열 체크 (대소문자 구분 없이)
- 모든 assistant 메시지를 "\n\n" 구분자로 합쳐서 반환

### 3. `_run_non_interactive_mode` 로직 재구성
**현재 순서:** Execute → Verify → Task Validator
**변경 후 순서:** Execute → Task Validator → (통과 시) Verify

**피드백 누적:**
- `verify_feedback_history: list[str] = []` 변수 추가
- Verify가 FULLY_DONE=FALSE 반환 시 피드백을 리스트에 추가
- 다음 Execute phase에 전달할 때:
  ```python
  if verify_feedback_history:
      feedback_section = (
          "\n\n## 🔍 Architect Feedback from Previous Iterations\n\n"
          "<architect-feedback-history>\n"
      )
      for i, feedback in enumerate(verify_feedback_history, 1):
          feedback_section += f'<feedback iteration="{i}">\n{feedback}\n</feedback>\n\n'

      feedback_section += "</architect-feedback-history>\n\n"
      feedback_section += "**CRITICAL**: Address ALL issues mentioned in the feedback history above before proceeding.\n"

      current_execute_extra = (execute_extra or "") + feedback_section
  ```

### 4. Verify phase의 verify_extra 처리
- Verify는 매번 새 세션이므로 **verify_extra는 매번 동일하게 전달**
- 피드백 히스토리는 verify_extra가 아닌 **verify 프롬프트 앞에 추가**:
  ```python
  if verify_feedback_history:
      history_section = "<previous_architect_reviews>\n"
      for i, feedback in enumerate(verify_feedback_history, 1):
          history_section += f'<review iteration="{i}">\n{feedback}\n</review>\n\n'
      history_section += "</previous_architect_reviews>\n\n"

      actual_verify_prompt = history_section + actual_verify_prompt
  ```

### 5. 종료 조건 변경
- **기존:** task_validator 체크만으로 종료
- **변경:** FULLY_DONE=TRUE 신호로만 종료
- task_validator는 verify phase 진입 여부 판단에만 사용

## 프로젝트 커밋 메시지 스타일
최근 커밋 분석 결과:
- 간결한 한글 설명 (예: "세션 리밋", "작업계획서 비우기")
- 또는 영어 prefix 사용 (예: "fix: ...", "docs: ...")
- 기능 추가는 간단한 동사구 (예: "time logging & nested json printing")
- 버그 수정은 "fix: " prefix

이번 작업에는 한글 간결체 사용 권장: "verify 피드백 루프 구현"

# TODOs

- [x] 1. `_verify_phase` 메서드 수정: 피드백 수집 및 FULLY_DONE 체크
   - [x] 1.1 구현: `sisyphus/core/loop.py`의 `_verify_phase` 메서드 (267-319줄)
      **정확한 변경 위치:**
      - **271줄**: `-> None:` → `-> tuple[str, bool]:`
      - **281줄**: `if self.verify_agent is None:` 직후(282줄)에 다음 2줄 추가:
        ```python
        feedback_messages: list[str] = []
        fully_done: bool = False
        ```
      - **304줄**: `await self.ui.show_message(message, source="verify")` 직후(305줄)에 추가:
        ```python
        if message.role == "assistant":
            feedback_messages.append(message.content)
            if "FULLY_DONE = TRUE" in message.content.upper():
                fully_done = True
        ```
      - **318줄**: `await self.verify_agent.close()` 직후(319줄, 기존 마지막 줄 직전)에 추가:
        ```python
        feedback = "\n\n".join(feedback_messages)
        self.verify_logger.info(f"Verify feedback collected: {len(feedback_messages)} messages, fully_done={fully_done}")
        return (feedback, fully_done)
        ```
      - **319줄**: 기존 `self.verify_logger.info("Verify phase complete")` 제거 (return 앞으로 이동됨)

   - [x] 1.2 테스트 작성: `sisyphus/core/tests/test_loop__verify_phase_feedback.py` 생성
      **Mock 설정 방법:**
      ```python
      from unittest.mock import AsyncMock, MagicMock
      from sisyphus.utils.types import AgentMessage

      # 기본 setup
      mock_verify_agent = AsyncMock()
      mock_ui = AsyncMock()
      mock_session_store = AsyncMock()
      mock_prompt_resolver = AsyncMock()
      mock_prompt_resolver.resolve = AsyncMock(return_value="resolved prompt")
      mock_logger_factory = MagicMock()
      mock_logger = MagicMock()
      mock_logger_factory.create_logger = MagicMock(return_value=mock_logger)

      loop = ExecutionLoop(
          execute_agent=AsyncMock(),
          ui=mock_ui,
          session_store=mock_session_store,
          prompt_resolver=mock_prompt_resolver,
          logger_factory=mock_logger_factory,
          verify_agent=mock_verify_agent,
      )
      ```

      **테스트 케이스:**

      1. `test_verify_phase__if_fully_done_true_in_message__returns_true_and_feedback`:
         ```python
         # Mock stream with FULLY_DONE = TRUE
         mock_stream = AsyncMock()
         mock_stream.__aiter__.return_value = [
             AgentMessage(role="assistant", content="Good work!\nFULLY_DONE = TRUE"),
         ]
         mock_verify_agent.stream.return_value = mock_stream
         mock_verify_agent.start_session.return_value = "test-session"

         feedback, fully_done = await loop._verify_phase("test prompt", None)

         assert fully_done is True
         assert "Good work!" in feedback
         assert "FULLY_DONE = TRUE" in feedback
         ```

      2. `test_verify_phase__if_fully_done_false__returns_false_and_feedback`:
         ```python
         # Mock stream without FULLY_DONE = TRUE
         mock_stream = AsyncMock()
         mock_stream.__aiter__.return_value = [
             AgentMessage(role="assistant", content="Needs improvement"),
         ]
         mock_verify_agent.stream.return_value = mock_stream

         feedback, fully_done = await loop._verify_phase("test prompt", None)

         assert fully_done is False
         assert "Needs improvement" in feedback
         ```

      3. `test_verify_phase__if_multiple_messages__concatenates_with_newlines`:
         ```python
         mock_stream = AsyncMock()
         mock_stream.__aiter__.return_value = [
             AgentMessage(role="assistant", content="First message"),
             AgentMessage(role="assistant", content="Second message"),
         ]
         mock_verify_agent.stream.return_value = mock_stream

         feedback, fully_done = await loop._verify_phase("test prompt", None)

         assert "First message\n\nSecond message" == feedback
         ```

      4. `test_verify_phase__if_no_assistant_messages__returns_empty_string`:
         ```python
         mock_stream = AsyncMock()
         mock_stream.__aiter__.return_value = [
             AgentMessage(role="system", content="System message"),
         ]
         mock_verify_agent.stream.return_value = mock_stream

         feedback, fully_done = await loop._verify_phase("test prompt", None)

         assert feedback == ""
         assert fully_done is False
         ```
   - [x] 1.3 테스트 실행: `uv run pytest -xvs sisyphus/core/tests/test_loop__verify_phase_feedback.py`
   - [x] 1.4 린트 및 타입 체크
      - [x] `uv run ruff check sisyphus/core/loop.py`
      - [x] `uv run basedpyright sisyphus/core/loop.py`
   - [x] 1.5 테스트 통과 확인 후 커밋
      - `git add sisyphus/core/loop.py sisyphus/core/tests/test_loop__verify_phase_feedback.py && git commit -m "verify phase 피드백 수집 및 FULLY_DONE 체크 구현"`
   - [x] 아래의 가이드대로 진행했을 때 Orchestrator 1번 작업 검증 성공 여부
      - [x] `_verify_phase`가 `tuple[str, bool]`을 반환하는가?
      - [x] Assistant 메시지가 모두 수집되어 피드백 문자열로 합쳐지는가?
      - [x] "FULLY_DONE = TRUE" 문자열이 감지되면 `fully_done=True`가 반환되는가?
      - [x] 테스트가 모두 통과하는가?
      - [x] 타입 체크와 린트가 통과하는가?
      - [x] 커밋이 정상적으로 생성되었는가?

- [x] 2. `_run_non_interactive_mode` 로직 재구성: Task validator 먼저, Verify는 완료 시에만
   **⚠️ Prerequisites:** TODO 1이 완료되어야 합니다 (`_verify_phase`가 `tuple[str, bool]`을 반환해야 함)

   - [x] 2.1 구현: `sisyphus/core/loop.py`의 `_run_non_interactive_mode` (158-214줄)
      **정확한 변경 위치:**
      - **173줄**: `iteration = 0` 직후(174줄)에 추가:
        ```python
        verify_feedback_history: list[str] = []
        ```
      - **179-213줄**: 전체 로직 재구성

      **SessionLimitError 처리:**
      - Execute phase의 try-except (179-183줄)는 **그대로 유지**
      - Task Validator는 try 블록 **밖**에 위치 (Execute 성공 후에만 실행)
      - Verify phase도 별도 try-except로 감싸되, SessionLimitError 발생 시 `continue`

      **변경 후 전체 구조 (179-213줄 교체):**
      ```python
      try:
          await self._execute_phase(execute_prompt, execute_extra)
      except SessionLimitError:
          await self.ui.show_status(f"[Iteration {iteration}] Session limit handled, retrying...")
          continue

      # Task Validator 체크 (Execute 성공 후에만)
      if self.task_validator is None:
          await self.ui.show_status("Execution complete (no task validator)")
          break

      content = self.task_validator.read_content()
      goals_accomplished = self.task_validator.check_all_goals_accomplished(content)
      checkboxes_completed = self.task_validator.check_all_checkboxes_completed(content)

      if not (goals_accomplished and checkboxes_completed):
          uncompleted = self.task_validator.extract_uncompleted_checkboxes(content)
          total = self.task_validator.count_total_checkboxes(content)
          completed = self.task_validator.count_completed_checkboxes(content)
          await self.ui.show_status(
              f"Progress: {completed}/{total} completed. {len(uncompleted)} tasks remaining. Continuing..."
          )
          continue  # Task 미완료 → Execute 재시작

      # Task 완료 시에만 Verify phase
      if self.verify_agent:
          actual_verify_prompt = verify_prompt if verify_prompt is not None else DEFAULT_VERIFY_PROMPT
          await self.ui.show_status(f"[Iteration {iteration}] Starting Verify phase...")

          try:
              feedback, fully_done = await self._verify_phase(actual_verify_prompt, verify_extra)

              if fully_done:
                  await self.ui.show_status("✅ Architect confirmed FULLY_DONE. All work verified!")
                  break  # 완전 종료

              # FULLY_DONE = FALSE → 피드백 누적 후 계속
              verify_feedback_history.append(feedback)
              await self.ui.show_status(f"[Iteration {iteration}] Verify feedback received. Continuing with improvements...")
              continue  # 피드백 포함해서 Execute 재시작
          except SessionLimitError:
              await self.ui.show_status(f"[Iteration {iteration}] Verify session limit handled, retrying...")
              continue

      # Verify agent 없으면 종료
      await self.ui.show_status("All tasks completed! Exiting loop.")
      break
      ```
   - [x] 2.2 테스트 작성: `sisyphus/core/tests/test_loop__non_interactive_flow.py` 생성
      **Mock 설정 패턴 (TODO 1의 setup 참고):**
      - task_validator Mock: `side_effect`로 iteration별 결과 제어
      - verify_agent Mock: stream 응답 제어

      **테스트 케이스:**
      1. `test_non_interactive__if_task_incomplete__skips_verify_and_retries_execute`:
         ```python
         mock_task_validator.check_all_goals_accomplished.side_effect = [False, True]
         mock_task_validator.check_all_checkboxes_completed.side_effect = [False, True]

         # First iteration: task incomplete → verify NOT called
         # Second iteration: task complete → verify called
         await loop._run_non_interactive_mode(...)
         assert mock_verify_agent.stream.call_count == 1
         ```

      2. `test_non_interactive__if_task_complete_and_fully_done__exits_loop` (패턴 동일)
      3. `test_non_interactive__if_task_complete_but_not_fully_done__continues_with_feedback` (패턴 동일)
   - [x] 2.3 테스트 실행: `uv run pytest -xvs sisyphus/core/tests/test_loop__non_interactive_flow.py`
   - [x] 2.4 린트 및 타입 체크
      - [x] `uv run ruff check sisyphus/core/loop.py`
      - [x] `uv run basedpyright sisyphus/core/loop.py`
   - [x] 2.5 테스트 통과 확인 후 커밋
      - `git add sisyphus/core/loop.py sisyphus/core/tests/test_loop__non_interactive_flow.py && git commit -m "execute-verify 순서 재구성 및 피드백 히스토리 추가"`
   - [x] 아래의 가이드대로 진행했을 때 Orchestrator 2번 작업 검증 성공 여부
      - [x] Execute phase 후 Task Validator가 먼저 체크되는가?
      - [x] Task 미완료 시 Verify를 건너뛰고 Execute를 재시작하는가?
      - [x] Task 완료 시에만 Verify가 실행되는가?
      - [x] `fully_done=True`일 때 loop가 종료되는가?
      - [x] `verify_feedback_history`가 올바르게 누적되는가?
      - [x] 테스트가 모두 통과하는가?
      - [x] 커밋이 정상적으로 생성되었는가?

- [x] 3. Execute phase에 피드백 전달: verify_feedback_history를 execute_extra에 추가
   - [x] 3.1 구현: `sisyphus/core/loop.py`의 `_run_non_interactive_mode` 내부
      **정확한 변경 위치:**
      - **TODO 2에서 재구성한 코드의 `await self._execute_phase(execute_prompt, execute_extra)` 부분 (386줄 예상)**을 다음과 같이 변경:

      **변경 전 (1줄):**
      ```python
      await self._execute_phase(execute_prompt, execute_extra)
      ```

      **변경 후 (코드 블록 앞에 추가):**
      ```python
      # 피드백 히스토리를 execute_extra에 주입
      current_execute_extra = execute_extra
      if verify_feedback_history:
          feedback_section = "\n\n## 🔍 Architect Feedback from Previous Iterations\n\n<architect-feedback-history>\n"

          for i, feedback in enumerate(verify_feedback_history, 1):
              feedback_section += f'<feedback iteration="{i}">\n{feedback}\n</feedback>\n\n'

          feedback_section += "</architect-feedback-history>\n\n"
          feedback_section += "**CRITICAL**: Address ALL issues mentioned in the feedback history above before proceeding.\n"

          current_execute_extra = (execute_extra or "") + feedback_section

      await self._execute_phase(execute_prompt, current_execute_extra)
      ```

      **위치 요약:** while loop 내부, try 블록 바로 전에 위치 (매 iteration마다 실행)
   - [x] 3.2 테스트 작성: `sisyphus/core/tests/test_loop__execute_feedback_injection.py` 생성
      - 테스트 케이스:
        - `test_execute__if_no_feedback_history__uses_original_extra`
        - `test_execute__if_feedback_history_exists__appends_feedback_section`
        - `test_execute__if_multiple_feedbacks__includes_all_with_correct_numbering`
   - [x] 3.3 테스트 실행: `uv run pytest -xvs sisyphus/core/tests/test_loop__execute_feedback_injection.py`
   - [x] 3.4 린트 및 타입 체크
      - [x] `uv run ruff check sisyphus/core/loop.py`
      - [x] `uv run basedpyright sisyphus/core/loop.py`
   - [x] 3.5 테스트 통과 확인 후 커밋
      - `git add sisyphus/core/loop.py sisyphus/core/tests/test_loop__execute_feedback_injection.py && git commit -m "execute phase에 verify 피드백 히스토리 주입"`
   - [x] 아래의 가이드대로 진행했을 때 Orchestrator 3번 작업 검증 성공 여부
      - [x] 피드백이 없을 때 원래 execute_extra가 그대로 사용되는가?
      - [x] 피드백이 있을 때 올바른 형식으로 추가되는가?
      - [x] 여러 피드백이 순서대로 번호가 매겨지는가?
      - [x] 피드백 섹션이 execute_extra 뒤에 추가되는가?
      - [x] 테스트가 모두 통과하는가?
      - [x] 커밋이 정상적으로 생성되었는가?

- [x] 4. Verify phase에 피드백 히스토리 전달: verify 프롬프트 앞에 추가
   - [x] 4.1 구현: `sisyphus/core/loop.py`의 `_run_non_interactive_mode` 내부
      **정확한 변경 위치:**
      - **TODO 2에서 추가한 `actual_verify_prompt =` 라인 (411줄 예상)과 `feedback, fully_done = await self._verify_phase(` 라인 (415줄 예상) 사이**에 추가:

      **변경 전:**
      ```python
      actual_verify_prompt = verify_prompt if verify_prompt is not None else DEFAULT_VERIFY_PROMPT
      await self.ui.show_status(f"[Iteration {iteration}] Starting Verify phase...")

      try:
          feedback, fully_done = await self._verify_phase(actual_verify_prompt, verify_extra)
      ```

      **변경 후 (actual_verify_prompt 생성 직후, ui.show_status 전에 추가):**
      ```python
      actual_verify_prompt = verify_prompt if verify_prompt is not None else DEFAULT_VERIFY_PROMPT

      # 피드백 히스토리를 verify 프롬프트 앞에 추가
      if verify_feedback_history:
          history_section = "<previous_architect_reviews>\n"
          for i, feedback in enumerate(verify_feedback_history, 1):
              history_section += f'<review iteration="{i}">\n{feedback}\n</review>\n\n'
          history_section += "</previous_architect_reviews>\n\n"

          actual_verify_prompt = history_section + actual_verify_prompt

      await self.ui.show_status(f"[Iteration {iteration}] Starting Verify phase...")

      try:
          feedback, fully_done = await self._verify_phase(actual_verify_prompt, verify_extra)
      ```
   - [x] 4.2 테스트 작성: `sisyphus/core/tests/test_loop__verify_feedback_history.py` 생성
      - 테스트 케이스:
        - `test_verify__if_no_feedback_history__uses_original_prompt`
        - `test_verify__if_feedback_history_exists__prepends_history_section`
        - `test_verify__if_multiple_feedbacks__includes_all_in_history`
   - [x] 4.3 테스트 실행: `uv run pytest -xvs sisyphus/core/tests/test_loop__verify_feedback_history.py`
   - [x] 4.4 린트 및 타입 체크
      - [x] `uv run ruff check sisyphus/core/loop.py`
      - [x] `uv run basedpyright sisyphus/core/loop.py`
   - [x] 4.5 테스트 통과 확인 후 커밋
      - `git add sisyphus/core/loop.py sisyphus/core/tests/test_loop__verify_feedback_history.py && git commit -m "verify phase에 피드백 히스토리 전달"`
   - [x] 아래의 가이드대로 진행했을 때 Orchestrator 4번 작업 검증 성공 여부
      - [x] 피드백 히스토리가 없을 때 원래 프롬프트가 그대로 사용되는가?
      - [x] 피드백 히스토리가 있을 때 프롬프트 앞에 추가되는가?
      - [x] 여러 피드백이 올바른 순서와 형식으로 포함되는가?
      - [x] verify_extra는 여전히 올바르게 전달되는가?
      - [x] 테스트가 모두 통과하는가?
      - [x] 커밋이 정상적으로 생성되었는가?

- [x] 5. 통합 테스트: 전체 피드백 루프 동작 검증
   - [x] 5.1 구현: `sisyphus/core/tests/test_loop__integration_feedback_loop.py` 생성
      - 통합 시나리오 테스트:
        - `test_feedback_loop__scenario_1_immediate_success`
          - Execute → Task 완료 → Verify (FULLY_DONE=TRUE) → 종료
        - `test_feedback_loop__scenario_2_task_incomplete_retry`
          - Execute → Task 미완료 → Execute 재시작 → Task 완료 → Verify → 종료
        - `test_feedback_loop__scenario_3_verify_feedback_iteration`
          - Execute → Task 완료 → Verify (FULLY_DONE=FALSE, 피드백1)
          - Execute (피드백1 포함) → Task 완료 → Verify (FULLY_DONE=FALSE, 피드백2)
          - Execute (피드백1+2 포함) → Task 완료 → Verify (FULLY_DONE=TRUE) → 종료
   - [x] 5.2 테스트 실행: `uv run pytest -xvs sisyphus/core/tests/test_loop__integration_feedback_loop.py`
   - [x] 5.3 전체 테스트 스위트 실행: `uv run pytest sisyphus/core/tests/test_loop*.py`
   - [x] 5.4 린트 및 타입 체크 (전체)
      - [x] `uv run ruff check sisyphus/core/loop.py`
      - [x] `uv run basedpyright sisyphus/core/loop.py`
   - [x] 5.5 테스트 통과 확인 후 커밋
      - `git add sisyphus/core/tests/test_loop__integration_feedback_loop.py && git commit -m "verify 피드백 루프 통합 테스트 추가"`
   - [x] 아래의 가이드대로 진행했을 때 Orchestrator 5번 작업 검증 성공 여부
      - [x] 시나리오 1: 즉시 성공 케이스가 올바르게 동작하는가?
      - [x] 시나리오 2: Task 미완료 재시도가 올바르게 동작하는가?
      - [x] 시나리오 3: 여러 번의 verify 피드백 iteration이 올바르게 동작하는가?
      - [x] 모든 통합 테스트가 통과하는가?
      - [x] 전체 테스트 스위트가 통과하는가?
      - [x] 타입 체크와 린트가 통과하는가?
      - [x] 커밋이 정상적으로 생성되었는가?

- [x] 6. 실제 동작 검증: 실제 sisyphus를 돌려서 피드백 루프 테스트
   - [x] 6.1 테스트 시나리오 준비: 간단한 ai-todolist.md 작성
      - 의도적으로 실패할 수 있는 간단한 작업 포함
      - 예: "print hello world" → "print goodbye world"로 수정하는 작업
   - [x] 6.2 Execute phase 실행 및 로그 확인
      - `uv run sisyphus execute` 실행
      - Execute phase 로그 확인
      - Task validator 체크 확인
   - [x] 6.3 Verify phase 실행 및 피드백 캡처 확인
      - Verify phase 실행 확인
      - 피드백 메시지가 수집되는지 로그 확인
      - "FULLY_DONE" 신호 감지 확인
   - [x] 6.4 피드백 재주입 확인
      - 다음 iteration에서 execute_extra에 피드백이 포함되는지 확인
      - Verify 프롬프트에 히스토리가 추가되는지 확인
   - [x] 6.5 종료 조건 확인
      - "FULLY_DONE = TRUE" 시 정상 종료 확인
      - "✅ Architect confirmed FULLY_DONE" 메시지 확인
   - [x] 6.6 실제 동작 검증 완료 후 최종 커밋
      - `git add -A && git commit -m "verify 피드백 루프 구현 완료"`
   - [x] 아래의 가이드대로 진행했을 때 Orchestrator 6번 작업 검증 성공 여부
      - [x] 실제 sisyphus가 정상적으로 실행되는가?
      - [x] Execute → Task Validator → Verify 순서가 로그에서 확인되는가?
      - [x] Verify 피드백이 실제로 캡처되는가?
      - [x] 다음 Execute에 피드백이 포함되는가?
      - [x] Verify에 히스토리가 전달되는가?
      - [x] "FULLY_DONE = TRUE" 시 정상 종료되는가?
      - [x] 최종 커밋이 생성되었는가?
      - [x] Python REPL이나 playwright를 사용하여 실제 동작을 확인했는가?

# 최종 작업 검증 체크리스트
- [x] 1. Execute → Task Validator → Verify 순서가 올바르게 동작하는가?
   - Task 미완료 시 Verify를 건너뛰는가?
   - Task 완료 시에만 Verify가 실행되는가?
- [x] 2. Verify phase가 피드백과 FULLY_DONE 신호를 올바르게 반환하는가?
   - `tuple[str, bool]` 타입으로 반환되는가?
   - "FULLY_DONE = TRUE" 문자열이 감지되는가?
- [x] 3. 피드백 히스토리가 올바르게 누적되고 전달되는가?
   - Execute phase에 피드백이 추가되는가?
   - Verify phase에 히스토리가 전달되는가?
   - 여러 번의 iteration에서 피드백이 올바르게 쌓이는가?
- [x] 4. "FULLY_DONE = TRUE" 시 loop가 정상 종료되는가?
- [x] 5. 모든 테스트가 통과하는가?
   - 단위 테스트 (각 메서드별)
   - 통합 테스트 (전체 시나리오)
- [x] 6. 타입 체크와 린트가 통과하는가?
- [x] 7. 실제 sisyphus 실행 시 피드백 루프가 정상 동작하는가?
- [x] 8. 기존 기능이 영향받지 않았는가?
   - Interactive mode는 여전히 작동하는가?
   - Task validator가 없는 경우는 여전히 작동하는가?
   - Verify agent가 없는 경우는 여전히 작동하는가?
