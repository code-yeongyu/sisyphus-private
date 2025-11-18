ExecutionLoop 완전 구현 스펙 문서

1. 개요

파일: projects/sisyphus-core/sisyphus_core/core/loop.py

목적: LLM Agent 기반의 Execute → Verify 2단계 피드백 루프를 통해 작업을 완료하고 검증하는 실행 엔진

핵심 로직:
- Execute 에이전트가 작업 수행
- Task Validator가 완료 여부 확인
- Verify 에이전트가 품질 검증
- 피드백을 Execute에 전달하여 재작업
- 모든 작업이 검증될 때까지 반복

---
2. 클래스 구조

2.1 TaskValidatorProtocol

class TaskValidatorProtocol(Protocol):
    todolist_path: Path

    def read_content(self) -> str:
        """todolist 내용 읽기"""

    async def check_all_goals_accomplished(self, content: str | None = None) -> bool:
        """모든 목표 달성 확인"""

    async def check_all_checkboxes_completed(self, content: str | None = None) -> bool:
        """모든 체크박스 완료 확인"""

2.2 ExecutionLoop

인스턴스 변수:

# 의존성
self.execute_agent: Agent              # Execute 단계 에이전트
self.verify_agent: Agent | None        # Verify 단계 에이전트 (선택)
self.ui: UIProtocol                    # UI 인터페이스
self.session_store: SessionStore       # 세션 영속화
self.logger_factory: LoggerFactory     # 로거 팩토리
self.task_validator: TaskValidatorProtocol  # 작업 검증기
self.working_directory: Path | None    # 작업 디렉토리
self.status_manager: StatusManager | None  # 상태 관리자

# 로거
self.execute_logger: logging.Logger | None
self.verify_logger: logging.Logger | None

# 인터럽트 관련
self._interrupt_flag: bool = False                      # 인터럽트 플래그
self._current_cancel_scope: anyio.CancelScope | None   # 현재 취소 스코프
self._resume_event: anyio.Event | None                 # 재개 이벤트
self._resumed_once: bool = False                        # 재개 1회 처리

# 재시도 카운터
self._consecutive_execute_count: int = 0         # 연속 Execute 횟수
self._execute_resume_fail_count: int = 0         # Execute 재개 실패 횟수
self._sdk_exception_count: int = 0               # SDK 오류 카운터

# 제어 플래그
self._should_exit_execute_phase: bool = False    # Execute 강제 종료 플래그
self._current_plan_id: str = ""                  # 현재 Plan ID
self._acceptance_criteria_retry_message: str | None = None  # AC 재시도 메시지

---
3. 메인 메서드: run()

시그니처:
async def run(
    self,
    execute_extra: str | None = None,
    verify_extra: str | None = None,
) -> None

동작:
1. UI 초기화: await self.ui.initialize()
2. Plan 경로 해석 및 프롬프트 구성
3. Unified 모드 실행

Plan 경로 해석 로직:

# 1. status_manager에서 현재 plan 경로 가져오기 시도
try:
    plan_path = await self._resolve_plan_path_from_status()
    execute_prompt, verify_prompt, resolved_plan_path = await self._initialize_from_plan(plan_path)
except (ValueError, FileNotFoundError):
    # 2. plan_path를 가져오지 못한 경우
    if not self._current_plan_id:
        self._current_plan_id = await self._resolve_plan_id()
    if not verify_prompt:
        verify_prompt = build_verify_prompt("(plan path unavailable)")

# 3. Unified 모드 실행
await self._run_unified_mode(execute_prompt, execute_extra, verify_prompt, verify_extra)

---
4. 핵심 메서드: _run_unified_mode()

4.1 초기화

# 재개 이벤트 생성
self._resume_event = anyio.Event()

# 루프 변수 초기화
iteration = 0                              # 반복 횟수
verify_feedback_history: list[str] = []    # 검증 피드백 히스토리
execute_throttle_max_count = 10            # Execute 스로틀 최대 횟수

# 사전 체크: 이미 완료된 경우 안내 메시지만 표시
if self.task_validator:
    content = self.task_validator.read_content()
    goals = await self.task_validator.check_all_goals_accomplished(content)
    checkboxes = await self.task_validator.check_all_checkboxes_completed(content)
    if goals and checkboxes:
        await self.ui.show_status("✅ All tasks already completed. Starting Verify phase...")

4.2 메인 루프 구조

while True:
    iteration++
    _consecutive_execute_count++

    # 스로틀 체크
    force_verify = (_consecutive_execute_count >= 10)
    if force_verify:
        show warning message

    # Execute 건너뛰기 판단
    skip_execute = task_validator(goals && checkboxes완료)

    # Execute 실행 (skip_execute=False일 때만)
    if not skip_execute:
        # 프롬프트 구성
        if verify_feedback_history:
            # 실패 프롬프트 + 피드백 히스토리 추가

        # Execute 호출
        try:
            await _execute_phase(...)
        except RetryRequiredError:
            # PromptTooLongError → 히스토리 제거
            # 기타 → 재시도

    # 재시도 제어
    if skip_count_and_retry:
        _consecutive_execute_count--
        continue
    if should_retry_execute:
        continue

    # Verify 여부 판단
    should_verify = force_verify or execution.completed or task_validator(완료)

    # Verify 실행
    if should_verify:
        # Verify 재시도 루프 (최대 3회)
        for verify_retry in range(3):
            try:
                feedback, fully_done = await _verify_phase(...)
                break
            except RetryRequiredError:
                if retry >= 3:
                    feedback = ""; fully_done = False

        # Plan 업데이트
        if status_manager:
            plan.execution.completed = fully_done
            if not fully_done and current_task_id:
                # 해당 todo를 completed → in_progress로 되돌림
            save plan

        # 종료 또는 피드백 추가
        if fully_done:
            _consecutive_execute_count = 0
            break  # 메인 루프 종료
        else:
            if feedback:
                verify_feedback_history.append(feedback)

4.3 상세 분기 로직

4.3.1 Execute 프롬프트 구성

current_execute_prompt = execute_prompt
current_execute_extra = execute_extra

# verify_feedback_history가 있으면 실패 프롬프트로 교체
if verify_feedback_history:
    try:
        # status_manager에서 plan 경로 가져오기
        if self.status_manager:
            status_file = await self.status_manager.get()
            if status_file.current_plan and status_file.current_plan.plan_path:
                plan_path = Path(status_file.current_plan.plan_path)

        # plan 로드하여 미완료 todo 요약
        if plan_path:
            plan_doc = await load_plan(plan_path)
            uncompleted_todos = []
            for plan in plan_doc.work_plans:
                for todo in plan.todos:
                    if todo.status != "completed":
                        uncompleted_todos.append(f"  - [{todo.id}] {todo.title}")

            todo_summary = "\n".join(uncompleted_todos[:10]) if uncompleted_todos else "All tasks completed"
            if len(uncompleted_todos) > 10:
                todo_summary += f"\n  ... and {len(uncompleted_todos) - 10} more"

            # 실패 프롬프트 생성
            current_execute_prompt = build_verification_failure_prompt(
                str(plan_path), todo_summary
            )
    except Exception:
        pass  # 실패 시 기본 프롬프트 사용

    # 피드백 히스토리 섹션 추가
    feedback_section = "\n\n## 🔍 Verify Feedback from Previous Iterations\n\n"
    feedback_section += "<verify-feedback-history>\n"

    for i, feedback in enumerate(verify_feedback_history, 1):
        feedback_section += f'<feedback iteration="{i}">\n{feedback}\n</feedback>\n\n'

    feedback_section += "</verify-feedback-history>\n\n"
    feedback_section += "**CRITICAL**: Address ALL issues mentioned in the feedback history above before proceeding.\n"

    current_execute_extra = (execute_extra or "") + feedback_section

4.3.2 Execute 에러 처리

try:
    await self._execute_phase(current_execute_prompt, current_execute_extra)
except* RetryRequiredError as exception_group:
    error = exception_group.exceptions[0]

    # PromptTooLongError + 히스토리 존재 → 가장 오래된 피드백 제거
    if isinstance(error, PromptTooLongError) and verify_feedback_history:
        verify_feedback_history.pop(0)
        await self.ui.show_status(
            f"⚠️  Prompt too long. Removing oldest feedback (remaining: {len(verify_feedback_history)})"
        )
        skip_count_and_retry = True
    else:
        # 기타 재시도 필요
        await self.ui.show_status(
            f"[Iteration {iteration}] Retry required ({error.__class__.__name__}): {error}"
        )

        # PromptTooLongError인 경우 세션 삭제
        if isinstance(error, PromptTooLongError):
            agent_type = type(self.execute_agent).__name__.lower().replace("agent", "")
            await self.session_store.delete_session(agent_type, self._current_plan_id)
            await self.ui.show_status(
                f"Session '{agent_type}' cleared due to prompt length exceeded. Starting new session."
            )

        should_retry_execute = True

4.3.3 Verify 여부 판단

should_verify = force_verify  # 기본값: 스로틀 초과 여부

if self.status_manager:
    try:
        status = await self.status_manager.get()
        if status.current_plan and status.current_plan.plan_path:
            plan_path_obj = Path(status.current_plan.plan_path)
            plan_doc = await load_plan(plan_path_obj)
            if plan_doc.work_plans:
                execution_completed = plan_doc.work_plans[0].execution.completed
                should_verify = should_verify or execution_completed
    except Exception:
        # fallback: task_validator 사용
        if self.task_validator:
            content = self.task_validator.read_content()
            goals = await self.task_validator.check_all_goals_accomplished(content)
            checkboxes = await self.task_validator.check_all_checkboxes_completed(content)
            should_verify = should_verify or (goals and checkboxes)
elif self.task_validator:
    content = self.task_validator.read_content()
    goals = await self.task_validator.check_all_goals_accomplished(content)
    checkboxes = await self.task_validator.check_all_checkboxes_completed(content)
    should_verify = should_verify or (goals and checkboxes)

4.3.4 Verify 재시도 루프

if should_verify:
    # 이전 verify 피드백이 있으면 prepend
    actual_verify_prompt = verify_prompt
    if verify_feedback_history:
        history_section = "<previous_verify_reviews>\n"
        for i, feedback in enumerate(verify_feedback_history, 1):
            history_section += f'<review iteration="{i}">\n{feedback}\n</review>\n\n'
        history_section += "</previous_verify_reviews>\n\n"
        actual_verify_prompt = history_section + actual_verify_prompt

    await self.ui.show_status(f"[Iteration {iteration}] Starting Verify phase...")

    # Verify 재시도 루프
    verify_retry_count = 0
    max_verify_retries = 3
    feedback = ""
    fully_done = False
    verify_succeeded = False

    while verify_retry_count < max_verify_retries and not verify_succeeded:
        try:
            feedback, fully_done = await self._verify_phase(actual_verify_prompt, verify_extra)
            verify_succeeded = True
        except* RetryRequiredError as exception_group:
            error = exception_group.exceptions[0]
            verify_retry_count += 1

            if verify_retry_count >= max_verify_retries:
                await self.ui.show_status(
                    f"⚠️ Verify phase failed after {max_verify_retries} attempts. "
                    "Skipping verify this iteration."
                )
                feedback = ""
                fully_done = False
            else:
                await self.ui.show_status(
                    f"[Iteration {iteration}] Verify retry required ({error.__class__.__name__}): {error} "
                    f"(attempt {verify_retry_count}/{max_verify_retries})"
                )

4.3.5 Plan 업데이트 로직

if self.status_manager:
    try:
        plan_path = await self._resolve_plan_path_from_status()
        plan_doc = await load_plan(plan_path)

        # 모든 work_plan의 execution.completed 업데이트
        for work_plan in plan_doc.work_plans:
            work_plan.execution.completed = fully_done

            # fully_done=False이고 current_task_id가 있으면 해당 task를 되돌림
            if not fully_done and work_plan.work_mode.current_task_id:
                def find_and_reset_task(todos: list[Todo]) -> bool:
                    for todo in todos:
                        if todo.id == work_plan.work_mode.current_task_id:
                            if todo.status == TodoStatus.completed:
                                todo.status = TodoStatus.in_progress
                                return True
                        if todo.children and find_and_reset_task(todo.children):
                            return True
                    return False

                find_and_reset_task(work_plan.todos)

        await save_plan(plan_path, plan_doc)
    except (ValueError, FileNotFoundError):
        pass

4.3.6 종료 조건

if fully_done:
    self._consecutive_execute_count = 0
    await self.ui.show_status("✅ Verify agent confirmed FULLY_DONE. All work verified!")
    break  # 메인 루프 종료
else:
    await self.ui.show_status(
        f"[Iteration {iteration}] Verify FALSE. Task reset to in_progress, will re-execute..."
    )

if feedback:
    verify_feedback_history.append(feedback)

---
5. Execute 단계: _execute_phase()

5.1 세션 관리

# 최종 프롬프트 구성
final_prompt = prompt if extra is None else f"{prompt}\n\n{extra}"

# Agent 초기화
await self.execute_agent.initialize()

# Plan ID 확보
if not self._current_plan_id:
    self._current_plan_id = await self._resolve_plan_id()
if not self._current_plan_id:
    raise ValueError("plan_id is required for session management")

# 세션 ID 조회
agent_type = type(self.execute_agent).__name__.lower().replace("agent", "")
session_id = await self.session_store.get_session(agent_type, self._current_plan_id)

# 로거 생성
self.execute_logger = self.logger_factory.create_logger(agent_type, session_id)
self.execute_logger.info(f"Execute phase starting (session_id={session_id})")

5.2 세션 재개 로직

# 세션 재개 시도
try:
    actual_session_id = await self.execute_agent.start_session(session_id)

    if session_id:
        self.execute_logger.info(f"✅ Session resumed successfully: {session_id}")
    else:
        self.execute_logger.info("New session initialized (ID will be received during stream)")

    self._execute_resume_fail_count = 0

except SessionResumeError as e:
    self._execute_resume_fail_count += 1
    self.execute_logger.warning(
        f"❌ Failed to resume session {session_id}: {e} (attempt {self._execute_resume_fail_count}/3)"
    )

    # 3회 실패 시 세션 삭제
    if self._execute_resume_fail_count >= 3:
        self.execute_logger.info("Session resume failed 3 times. Resetting session store.")
        await self.session_store.delete_session(agent_type, self._current_plan_id)
        self._execute_resume_fail_count = 0

    # 신규 세션으로 시작
    self.execute_logger.info("Starting new session instead")
    actual_session_id = await self.execute_agent.start_session(None)

# 세션 저장
await self.session_store.save_session(agent_type, actual_session_id, self._current_plan_id)

5.3 프롬프트 전송 및 루프 준비

# 초기 프롬프트 전송 (루프 밖에서 1회만)
await self.execute_agent.send(final_prompt)
self.execute_logger.info("Prompt sent")

# 재개 플래그 초기화
self._resumed_once = False

5.4 동시 작업: consume_stream + monitor_input

while True:
    self._current_cancel_scope = anyio.CancelScope()
    monitor_scope: anyio.CancelScope = self._current_cancel_scope

    async def consume_stream() -> None:
        """스트림에서 메시지 소비 및 UI 표시"""
        assert self.execute_logger is not None
        stream = self.execute_agent.stream()
        async for message in stream:
            # 인터럽트 플래그 체크
            if self._interrupt_flag:
                monitor_scope.cancel()
                break

            # UI에 메시지 표시
            await self.ui.show_message(message, source="execute")
            self.execute_logger.debug(f"Message: {message.role} - {message.content[:100]}...")

        # 스트림 종료 시 cancel scope 취소
        monitor_scope.cancel()

    async def monitor_input() -> None:
        """사용자 입력 모니터링 및 Agent에 전송"""
        assert self.execute_logger is not None
        with monitor_scope:
            while True:
                msg: str | None = await self.ui.get_input()
                if msg:
                    self.execute_logger.info(f"Sending user message: {msg[:100]}...")
                    await self.execute_agent.send(msg)
                else:
                    await anyio.sleep(0.01)

    try:
        async with anyio.create_task_group() as tg:
            tg.start_soon(consume_stream)
            tg.start_soon(monitor_input)
    except* SessionLimitError as exception_group:
        # SessionLimitError 처리
        ...
    except* Exception as exception_group:
        # 기타 에러 처리
        ...

    # 정상 종료 후 인터럽트/재개 처리
    if self._interrupt_flag:
        # 인터럽트 처리
        ...
    else:
        # 루프 종료 또는 계속
        ...

5.5 에러 처리

5.5.1 SessionLimitError

except* SessionLimitError as exception_group:
    first_exception = exception_group.exceptions[0]
    if not isinstance(first_exception, SessionLimitError):
        raise
    session_limit_error = first_exception

    self.execute_logger.error(
        f"Session limit reached: {session_limit_error}",
        exc_info=session_limit_error,
    )
    await self.ui.show_status("⚠️  Session limit reached")

    # reset_time까지 대기
    if session_limit_error.reset_time:
        self.execute_logger.info(f"Reset time parsed: {session_limit_error.reset_time}")
        await sleep_until_reset(session_limit_error.reset_time, self.ui)
    else:
        self.execute_logger.warning("Reset time unknown, waiting until next hour")
        await self.ui.show_status("Reset time unknown, waiting until next hour...")
        await sleep_until_next_hour(self.ui)

    raise session_limit_error  # 상위로 재전파 (RetryRequiredError 계열)

5.5.2 SDK 오류 (휴리스틱)

except* Exception as exception_group:
    sdk_error_detected = False
    sdk_exception = None

    # SDK 오류 감지 (문자열 휴리스틱)
    for exception in exception_group.exceptions:
        error_str = str(exception).lower()
        if "command failed" in error_str or "exit code" in error_str:
            sdk_error_detected = True
            sdk_exception = exception
            break

    if sdk_error_detected:
        self._sdk_exception_count += 1
        attempt_msg = f"(attempt {self._sdk_exception_count}/3)"
        self.execute_logger.error(
            f"SDK error in execute phase: {sdk_exception} {attempt_msg}",
            exc_info=sdk_exception,
        )
        self.execute_logger.info("SDK error detected. Deleting invalid session.")

        # 세션 삭제
        await self.session_store.delete_session(agent_type, self._current_plan_id)

        # 3회 이상 시 Execute 단계 강제 종료
        if self._sdk_exception_count >= 3:
            self.execute_logger.error("SDK error occurred 3 times. Exiting execute phase.")
            self._should_exit_execute_phase = True

        raise RetryRequiredError(f"SDK error: {sdk_exception}")
    else:
        # SDK 오류 아닌 기타 예외
        ...

5.5.3 기타 예외

    else:
        self._execute_resume_fail_count += 1
        for exception in exception_group.exceptions:
            attempt_msg = f"(attempt {self._execute_resume_fail_count}/3)"
            self.execute_logger.error(
                f"Unexpected error in execute phase: {exception} {attempt_msg}",
                exc_info=exception,
            )

        # 3회 이상 시 세션 삭제 + 강제 종료
        if self._execute_resume_fail_count >= 3:
            self.execute_logger.info("Exception occurred 3 times. Resetting session store.")
            await self.session_store.delete_session(agent_type, self._current_plan_id)
            self._execute_resume_fail_count = 0
            self._should_exit_execute_phase = True
        else:
            raise  # 3회 미만이면 예외 재전파

5.6 인터럽트 및 재개

if self._interrupt_flag:
    assert self._resume_event is not None
    assert self.execute_logger is not None

    await self.ui.show_status("⏸ Work has been interrupted")
    await self._resume_event.wait()

    # 재개 입력 받기
    resumed_msg: str | None = await self.ui.get_input()
    if resumed_msg:
        self.execute_logger.info(f"Sending resumed message: {resumed_msg[:100]}...")
        await self.execute_agent.send(resumed_msg)
        self._resumed_once = True

    self._interrupt_flag = False
    await self.ui.show_status("▶ Resuming work")
else:
    # 강제 종료 플래그 체크
    if self._should_exit_execute_phase:
        self._should_exit_execute_phase = False
        self._execute_resume_fail_count = 0
        break

    # 재개 1회 처리
    if self._resumed_once:
        self._resumed_once = False
        continue
    else:
        self._execute_resume_fail_count = 0
        break

5.7 세션 ID 동기화 및 종료

# 최종 세션 ID 동기화
final_session_id = self.execute_agent.session_id
if final_session_id and final_session_id != actual_session_id:
    self.execute_logger.info(f"Updating session ID: '{actual_session_id}' -> '{final_session_id}'")
    await self.session_store.save_session(agent_type, final_session_id, self._current_plan_id)

# Agent 종료
await self.execute_agent.close()
self.execute_logger.info("Execute phase complete")

---
6. Verify 단계: _verify_phase()

6.1 초기화

# verify_agent 없으면 즉시 반환
if self.verify_agent is None:
    return ("", False)

# 피드백 수집 변수
feedback_messages: list[str] = []
fully_done: bool = False

# 최종 프롬프트
final_prompt = prompt if extra is None else f"{prompt}\n\n{extra}"

# Agent 초기화
await self.verify_agent.initialize()

# Plan ID 확보
if not self._current_plan_id:
    self._current_plan_id = await self._resolve_plan_id()

# 로거 생성 (verify는 항상 신규 세션)
agent_type = type(self.verify_agent).__name__.lower().replace("agent", "")
self.verify_logger = self.logger_factory.create_logger(agent_type, None)
self.verify_logger.info("Verify phase starting (new session)")

# 신규 세션 시작
actual_session_id = await self.verify_agent.start_session(None)
self.verify_logger.info(f"New session started: {actual_session_id}")

# 프롬프트 전송
await self.verify_agent.send(final_prompt)
self.verify_logger.info("Prompt sent")

# Judgment 재시도 변수
self._resumed_once = False
max_judgment_retries = 5
judgment_retry_count = 0

6.2 동시 작업: consume_stream (판단 수집)

while True:
    self._current_cancel_scope = anyio.CancelScope()
    monitor_scope: anyio.CancelScope = self._current_cancel_scope
    has_judgment = False

    async def consume_stream() -> None:
        """스트림에서 메시지 소비 및 fully_done 판단"""
        assert self.verify_logger is not None
        assert self.verify_agent is not None
        nonlocal feedback_messages, fully_done, has_judgment

        stream = self.verify_agent.stream()
        async for message in stream:
            if self._interrupt_flag:
                monitor_scope.cancel()
                break

            await self.ui.show_message(message, source="verify")
            self.verify_logger.debug(f"Message: {message.role} - {message.content[:100]}...")

            # assistant 메시지만 수집
            if message.role == "assistant":
                feedback_messages.append(message.content)

        # 메시지가 없으면 판단 없음
        if not feedback_messages:
            monitor_scope.cancel()
            has_judgment = False
            return

        # 마지막 메시지에서 FULLY_DONE 판단 추출
        last_content = feedback_messages[-1].upper()
        has_true = "FULLY_DONE = TRUE" in last_content or "FULLY_DONE=TRUE" in last_content
        has_false = "FULLY_DONE = FALSE" in last_content or "FULLY_DONE=FALSE" in last_content

        if has_true and not has_false:
            fully_done = True
            has_judgment = True

            # Acceptance Criteria 검증 (CRITICAL)
            if self.status_manager:
                try:
                    plan_path = await self._resolve_plan_path_from_status()
                    plan_doc = await load_plan(plan_path)
                    unchecked_items: list[str] = []

                    # 모든 work_plan의 AC 체크
                    for work_plan in plan_doc.work_plans:
                        if work_plan.acceptance_criteria_for_verification_agent:
                            for criteria in work_plan.acceptance_criteria_for_verification_agent:
                                for checklist in criteria.checklists:
                                    if checklist.checked_at is None or not checklist.checked_evidence:
                                        unchecked_items.append(
                                            f"  - [{checklist.id}] {checklist.title}\n"
                                            f"    Content: {checklist.content}"
                                        )

                    # 미체크 항목이 있으면 강제로 fully_done=False
                    if unchecked_items:
                        assert self.verify_logger is not None
                        self.verify_logger.warning(
                            f"FULLY_DONE = TRUE but {len(unchecked_items)} AC items unchecked"
                        )

                        # 재시도 메시지 설정
                        self._acceptance_criteria_retry_message = (
                            "❌ You said FULLY_DONE = TRUE, but you have NOT completed all "
                            "acceptance_criteria_for_verification_agent items!\n\n"
                            "**UNCHECKED ITEMS**:\n\n" + "\n".join(unchecked_items) + "\n\n"
                            "**YOU MUST**:\n\n"
                            "1. Read each unchecked item's content carefully\n"
                            "2. Perform the verification specified in the content\n"
                            "3. Mark each item using:\n"
                            "   ```bash\n"
                            "   sisyphus-speckit plan accept-as-verification-agent --id <checklist-id> "
                            '--evidence "<detailed evidence>"\n'
                            "   ```\n\n"
                            "4. After ALL items are checked, THEN you can say FULLY_DONE = TRUE\n\n"
                            "Please complete the unchecked items now and resume your work."
                        )
                        fully_done = False
                        has_judgment = False
                        self.verify_logger.info(
                            "Forcing has_judgment=False to trigger retry with acceptance criteria message"
                        )
                except Exception as e:
                    assert self.verify_logger is not None
                    self.verify_logger.error(
                        f"Error checking acceptance_criteria_for_verification_agent: {e}",
                        exc_info=e,
                    )

        elif has_true or has_false:
            # TRUE와 FALSE 둘 다 있거나 FALSE만 있는 경우
            fully_done = False
            has_judgment = True
        else:
            # 판단 문자열이 없음
            has_judgment = False

        monitor_scope.cancel()

    async def monitor_input() -> None:
        """사용자 입력 모니터링"""
        assert self.verify_logger is not None
        assert self.verify_agent is not None
        with monitor_scope:
            while True:
                msg: str | None = await self.ui.get_input()
                if msg:
                    self.verify_logger.info(f"Sending user message: {msg[:100]}...")
                    await self.verify_agent.send(msg)
                else:
                    await anyio.sleep(0.01)

6.3 Verify 에러 처리

동일한 패턴 (SessionLimitError, SDK 오류 등)이지만 verify는 항상 신규 세션이므로 세션 삭제만 수행합니다.

6.4 Judgment 재시도 로직

# 태스크 그룹 종료 후
if self._interrupt_flag:
    # 인터럽트 처리 (Execute와 동일)
    ...
else:
    if self._resumed_once:
        self._resumed_once = False
        continue
    elif not has_judgment and judgment_retry_count < max_judgment_retries:
        judgment_retry_count += 1
        self.verify_logger.info(
            f"No FULLY_DONE judgment found, retrying ({judgment_retry_count}/{max_judgment_retries})"
        )

        # AC 재시도 메시지 또는 기본 메시지
        if self._acceptance_criteria_retry_message:
            retry_message = self._acceptance_criteria_retry_message
            self._acceptance_criteria_retry_message = None
        else:
            retry_message = (
                "You did not provide a clear FULLY_DONE judgment in your last response. "
                "Please review the execute phase output and provide a clear judgment:\n\n"
                "- Say 'FULLY_DONE = TRUE' if all goals in the work plan are accomplished\n"
                "- Say 'FULLY_DONE = FALSE' if any goals remain incomplete\n\n"
                "Please respond with your judgment now."
            )

        # 피드백 초기화 후 재요청
        feedback_messages.clear()
        await self.verify_agent.send(retry_message)
        continue
    elif not has_judgment:
        # 최대 재시도 초과
        self.verify_logger.warning(
            "Max retries exceeded without clear judgment, defaulting to FULLY_DONE = FALSE"
        )
        fully_done = False
        break
    else:
        # 판단 존재, 루프 종료
        break

6.5 종료 및 반환

await self.verify_agent.close()

# 피드백 합치기
feedback = "\n\n".join(feedback_messages)
self.verify_logger.info(
    f"Verify feedback collected: {len(feedback_messages)} messages, fully_done={fully_done}"
)

return (feedback, fully_done)

---
7. 인터럽트 API

7.1 request_interrupt()

def request_interrupt(self) -> None:
    """인터럽트 요청"""
    self._interrupt_flag = True
    if self._current_cancel_scope:
        self._current_cancel_scope.cancel()

7.2 clear_interrupt()

def clear_interrupt(self) -> None:
    """인터럽트 해제"""
    self._interrupt_flag = False
    if self._resume_event is not None:
        self._resume_event.set()

---
8. 상태 전이 요약

8.1 카운터 변수

| 변수                         | 증가                        | 감소                      | 리셋                | 용도                        |
|----------------------------|---------------------------|-------------------------|-------------------|---------------------------|
| iteration                  | 메인 루프 매 반복                | -                       | -                 | 표시용                       |
| _consecutive_execute_count | 메인 루프 매 반복                | PromptTooLong+히스토리 제거 시 | fully_done=True 시 | 스로틀 (10회 이상 시 강제 Verify)  |
| _execute_resume_fail_count | SessionResumeError, 기타 예외 | -                       | 3회 도달 시, 정상 종료 시  | Execute 재개 실패 추적          |
| _sdk_exception_count       | SDK 오류 감지 시               | -                       | 없음                | SDK 오류 추적 (3회 이상 시 강제 종료) |

8.2 제어 플래그

| 플래그                        | True 조건                                               | False 조건 | 영향              |
|----------------------------|-------------------------------------------------------|----------|-----------------|
| force_verify               | _consecutive_execute_count >= 10                      | -        | Verify 강제 실행    |
| skip_execute               | task_validator(goals && checkboxes 완료)                | -        | Execute 건너뛰기    |
| should_retry_execute       | RetryRequiredError 발생 (PromptTooLong 제외)              | -        | Execute 재시도     |
| skip_count_and_retry       | PromptTooLong + 히스토리 존재                               | -        | 카운트 감소 후 즉시 재시도 |
| should_verify              | force_verify OR execution.completed OR task_validator | -        | Verify 실행 여부    |
| _should_exit_execute_phase | SDK 오류 3회 OR 기타 예외 3회                                 | 루프 종료 후  | Execute 강제 종료   |

8.3 Plan 상태

- execution.completed: Verify 종료 후에만 업데이트 (fully_done 값으로)
- todo.status: Verify에서 fully_done=False이고 current_task_id가 설정된 경우, 해당 todo를 completed → in_progress로 되돌림

---
9. 주요 에러 타입

# RetryRequiredError 계열 (재시도 가능)
class RetryRequiredError(SisyphusError):
    pass

class SessionLimitError(RetryRequiredError):
    reset_time: datetime | None  # 리셋 시간

class PromptTooLongError(RetryRequiredError):
    pass

# 기타
class SessionResumeError(SisyphusError):
    pass

---
10. 구현 시 주의사항

10.1 버그 의심 포인트

1. verify_agent=None 케이스: elif should_verify and not self.verify_agent 분기가 도달 불가능. verify_agent가 None이어도 if should_verify: 블록에서 _verify_phase() 호출 → 즉시 ("", False) 반환 → fully_done=False로 무한 루프
가능.
2. SDK 카운터 리셋 없음: _sdk_exception_count는 Execute/Verify 공유이지만 리셋 로직이 없어 누적될 수 있음.

10.2 구현 권장사항

1. 타입 힌트: 모든 변수와 함수에 명시적 타입 힌트 추가
2. 로깅: 모든 분기에서 충분한 로깅 (디버깅 용이)
3. 에러 메시지: 사용자에게 명확한 상태 안내
4. 테스트: 각 분기별 유닛 테스트 필수 (특히 nested try/except)

10.3 재구현 시 개선 포인트

1. 상태 기계 패턴: nested if/else를 상태 기계로 리팩토링
2. 전략 패턴: Execute/Verify 에러 처리를 전략 객체로 분리
3. 명시적 종료 조건: verify_agent=None 케이스 처리
4. 카운터 관리: SDK 카운터 리셋 정책 명확화

---

⏺ 완료했습니다! loop.py의 모든 로직을 구현 가능한 수준의 상세한 스펙으로 작성했습니다.

📋 작성된 스펙 요약

1. 전체 구조

- ExecutionLoop 클래스의 모든 인스턴스 변수 (16개)
- TaskValidatorProtocol 프로토콜 정의

2. 메인 메서드 상세 분석

run(): Plan 경로 해석 및 초기화 로직

_run_unified_mode():
- 초기화 단계
- 메인 루프 구조 (while True)
- Execute 프롬프트 구성 (verify_feedback_history 처리)
- Execute 에러 처리 (PromptTooLongError, RetryRequiredError)
- Verify 여부 판단 (force_verify, execution.completed, task_validator)
- Verify 재시도 루프 (최대 3회)
- Plan 업데이트 로직 (execution.completed, todo status 되돌림)
- 종료 조건

_execute_phase():
- 세션 관리 (재개 vs 신규)
- 세션 재개 실패 처리 (최대 3회)
- 동시 작업 (consume_stream + monitor_input)
- 에러 처리 (SessionLimitError, SDK 오류, 기타 예외)
- 인터럽트/재개 메커니즘
- 세션 ID 동기화

_verify_phase():
- 항상 신규 세션
- fully_done 판단 로직 ("FULLY_DONE = TRUE/FALSE" 문자열 파싱)
- Acceptance Criteria 검증 (미체크 시 강제 재시도)
- Judgment 재시도 (최대 5회)
- 에러 처리

3. 상태 전이 매트릭스

- 카운터 변수 4개의 증가/감소/리셋 조건
- 제어 플래그 6개의 True/False 조건 및 영향
- Plan 상태 변경 시점

4. 에러 처리

- RetryRequiredError 계열 (SessionLimitError, PromptTooLongError)
- SessionResumeError
- SDK 오류 (휴리스틱)
- 기타 예외

5. 구현 시 주의사항

- 버그 의심 포인트 2개 발견 및 설명
- 구현 권장사항
- 재구현 시 개선 포인트 4가지
