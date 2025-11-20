"""Phase orchestration for Execute and Verify phases with error handling."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import anyio

from sisyphus_core.core.plans.loader import load_plan
from sisyphus_core.utils.errors import RetryRequiredError, SessionLimitError, SessionResumeError
from sisyphus_core.utils.session_limit import sleep_until_next_hour, sleep_until_reset

if TYPE_CHECKING:
    from sisyphus_core.agents.base import Agent
    from sisyphus_core.core.loop_state import LoopState
    from sisyphus_core.core.session import SessionStore
    from sisyphus_core.core.status.manager import StatusManager
    from sisyphus_core.ui.base import UIProtocol
    from sisyphus_core.utils.logging import LoggerFactory


class PhaseOrchestrator:
    """Orchestrates Execute and Verify phase execution with comprehensive error handling.

    Responsibilities:
    - Execute phase: session management, resume logic, error handling
    - Verify phase: new session, FULLY_DONE judgment, Acceptance Criteria validation
    - Common error handling: SessionLimitError, SDK errors, retry logic
    """

    def __init__(
        self,
        execute_agent: Agent,
        verify_agent: Agent,
        ui: UIProtocol,
        session_store: SessionStore,
        logger_factory: LoggerFactory,
        state: LoopState,
        status_manager: StatusManager | None = None,
    ) -> None:
        """Initialize PhaseOrchestrator.

        Args:
            execute_agent: Agent for execute phase
            verify_agent: Agent for verify phase (REQUIRED)
            ui: UI Protocol implementation
            session_store: Session persistence store
            logger_factory: Logger factory
            state: LoopState for state management
            status_manager: Optional status manager for plan tracking
        """
        self.execute_agent: Agent = execute_agent
        self.verify_agent: Agent = verify_agent
        self.ui: UIProtocol = ui
        self.session_store: SessionStore = session_store
        self.logger_factory: LoggerFactory = logger_factory
        self.state: LoopState = state
        self.status_manager: StatusManager | None = status_manager

        self.execute_logger: logging.Logger | None = None
        self.verify_logger: logging.Logger | None = None

        self._resume_event: anyio.Event | None = None
        self._current_cancel_scope: anyio.CancelScope | None = None

    def set_resume_event(self, event: anyio.Event) -> None:
        """Set the resume event for interrupt/resume handling.

        Args:
            event: Resume event to set
        """
        self._resume_event = event

    async def _resolve_plan_path_from_status(self) -> Path:
        """Resolve plan path from status manager.

        Returns:
            Plan file path

        Raises:
            ValueError: If status_manager is None or plan path cannot be resolved
        """
        if not self.status_manager:
            raise ValueError("status_manager is required to resolve plan path")

        status = await self.status_manager.get()
        if not status or not status.current_plan:
            raise ValueError("No current plan found in status")

        return Path(status.current_plan.plan_path)

    async def execute_phase(
        self,
        prompt: str,
        extra: str | None = None,
    ) -> None:
        """Execute phase: can resume previous session.

        Session management:
        - Attempts to resume existing session
        - Retries up to 3 times on SessionResumeError
        - Deletes session and starts new on 3rd failure

        Error handling:
        - SessionLimitError: Sleep until reset time
        - SDK errors: Delete session, increment counter, set exit flag on 3rd occurrence
        - Other errors: Increment resume fail count, delete session on 3rd failure

        Args:
            prompt: Prompt for execute agent
            extra: Extra prompt to append

        Raises:
            SessionLimitError: Re-raised after handling sleep (for loop to retry)
            RetryRequiredError: On SDK errors requiring retry
        """
        final_prompt = prompt if extra is None else f"{prompt}\n\n{extra}"

        await self.execute_agent.initialize()

        plan_id = self.state.get_plan_id()
        if not plan_id:
            raise ValueError("plan_id is required for session management")

        agent_type = type(self.execute_agent).__name__.lower().replace("agent", "")
        session_id = await self.session_store.get_session(agent_type, plan_id)

        self.execute_logger = self.logger_factory.create_logger(agent_type, session_id)
        self.execute_logger.info(f"Execute phase starting (session_id={session_id})")

        # Log resume attempt
        if session_id:
            self.execute_logger.info(f"Attempting to resume session: {session_id}")
        else:
            self.execute_logger.info("Starting new session")

        try:
            actual_session_id = await self.execute_agent.start_session(session_id)

            if session_id:
                self.execute_logger.info(f"✅ Session resumed successfully: {session_id}")
            else:
                self.execute_logger.info("New session initialized (ID will be received during stream)")

            self.state.reset_execute_resume_fail()

        except SessionResumeError as e:
            self.state.increment_execute_resume_fail()
            self.execute_logger.warning(
                f"❌ Failed to resume session {session_id}: {e} (attempt {self.state._execute_resume_fail_count}/3)"
            )

            if not self.state.check_should_retry_resume():
                self.execute_logger.info("Session resume failed 3 times. Resetting session store.")
                await self.session_store.delete_session(agent_type, plan_id)
                self.state.reset_execute_resume_fail()

            self.execute_logger.info("Starting new session instead")
            actual_session_id = await self.execute_agent.start_session(None)

        await self.session_store.save_session(agent_type, actual_session_id, plan_id)

        # Send initial prompt (outside while loop - only once)
        await self.execute_agent.send(final_prompt)
        self.execute_logger.info("Prompt sent")

        self.state.set_resumed_once(False)

        while True:
            self._current_cancel_scope = anyio.CancelScope()
            monitor_scope: anyio.CancelScope = self._current_cancel_scope

            async def consume_stream() -> None:
                """Consume messages from stream and display in UI"""
                assert self.execute_logger is not None
                stream = self.execute_agent.stream()
                async for message in stream:
                    if self.state.is_interrupted():
                        monitor_scope.cancel()
                        break

                    await self.ui.show_message(message, source="execute")
                    self.execute_logger.debug(f"Message: {message.role} - {message.content[:100]}...")

                monitor_scope.cancel()

            async def monitor_input() -> None:
                """Monitor user input and send to Agent"""
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
                first_exception = exception_group.exceptions[0]
                if not isinstance(first_exception, SessionLimitError):
                    raise
                session_limit_error = first_exception

                await self._handle_session_limit_error(session_limit_error, "execute")
                raise session_limit_error
            except* Exception as exception_group:
                if self._detect_and_handle_sdk_error(exception_group, "execute"):
                    agent_type_for_delete = type(self.execute_agent).__name__.lower().replace("agent", "")
                    await self.session_store.delete_session(agent_type_for_delete, plan_id)
                    raise RetryRequiredError(f"SDK error: {exception_group.exceptions[0]}")
                else:
                    self.state.increment_execute_resume_fail()
                    for exception in exception_group.exceptions:
                        attempt_msg = f"(attempt {self.state._execute_resume_fail_count}/3)"
                        self.execute_logger.error(
                            f"Unexpected error in execute phase: {exception} {attempt_msg}",
                            exc_info=exception,
                        )

                    if not self.state.check_should_retry_resume():
                        self.execute_logger.info("Exception occurred 3 times. Resetting session store.")
                        agent_type_for_delete = type(self.execute_agent).__name__.lower().replace("agent", "")
                        await self.session_store.delete_session(agent_type_for_delete, plan_id)
                        self.state.reset_execute_resume_fail()
                        self.state.set_should_exit_execute_phase(True)
                    else:
                        raise

            # Task Group completed normally - check interrupt status
            if self.state.is_interrupted():
                assert self._resume_event is not None
                assert self.execute_logger is not None
                await self.ui.show_status("⏸ Work has been interrupted")
                await self._resume_event.wait()

                resumed_msg: str | None = await self.ui.get_input()
                if resumed_msg:
                    self.execute_logger.info(f"Sending resumed message: {resumed_msg[:100]}...")
                    await self.execute_agent.send(resumed_msg)
                    self.state.set_resumed_once(True)

                self.state.set_interrupt_flag(False)
                await self.ui.show_status("▶ Resuming work")
            else:
                if self.state.should_exit_execute_phase():
                    self.state.set_should_exit_execute_phase(False)
                    self.state.reset_execute_resume_fail()
                    break
                if self.state.was_resumed_once():
                    self.state.set_resumed_once(False)
                    continue
                else:
                    self.state.reset_execute_resume_fail()
                    break

        # Update actual session_id after stream() completes
        final_session_id = self.execute_agent.session_id
        if final_session_id and final_session_id != actual_session_id:
            self.execute_logger.info(f"Updating session ID: '{actual_session_id}' -> '{final_session_id}'")
            await self.session_store.save_session(agent_type, final_session_id, plan_id)

        await self.execute_agent.close()
        self.execute_logger.info("Execute phase complete")

    async def verify_phase(
        self,
        prompt: str,
        extra: str | None = None,
    ) -> tuple[str, bool]:
        """Verify phase: always starts NEW session (independent verification).

        Judgment logic:
        - Searches for FULLY_DONE = TRUE/FALSE in assistant messages
        - Retries up to 5 times if no clear judgment found
        - Validates Acceptance Criteria when FULLY_DONE = TRUE

        Error handling:
        - SessionLimitError: Sleep until reset time
        - SDK errors: Delete session, increment counter, raise RetryRequiredError
        - Other errors: Re-raise

        Args:
            prompt: Prompt for verify agent
            extra: Extra prompt to append

        Returns:
            Tuple of (feedback_text, fully_done_flag)

        Raises:
            SessionLimitError: Re-raised after handling sleep (for loop to retry)
            RetryRequiredError: On SDK errors requiring retry
        """
        feedback_messages: list[str] = []
        fully_done: bool = False

        final_prompt = prompt if extra is None else f"{prompt}\n\n{extra}"

        await self.verify_agent.initialize()

        plan_id = self.state.get_plan_id()
        if not plan_id:
            raise ValueError("plan_id is required for session management")

        agent_type = type(self.verify_agent).__name__.lower().replace("agent", "")

        self.verify_logger = self.logger_factory.create_logger(agent_type, None)
        self.verify_logger.info("Verify phase starting (new session)")

        actual_session_id = await self.verify_agent.start_session(None)
        self.verify_logger.info(f"New session started: {actual_session_id}")

        await self.verify_agent.send(final_prompt)
        self.verify_logger.info("Prompt sent")

        self.state.set_resumed_once(False)
        max_judgment_retries = 5
        judgment_retry_count = 0

        while True:
            self._current_cancel_scope = anyio.CancelScope()
            monitor_scope: anyio.CancelScope = self._current_cancel_scope
            has_judgment = False

            async def consume_stream() -> None:
                """Consume messages from stream and collect feedback"""
                assert self.verify_logger is not None
                nonlocal feedback_messages, fully_done, has_judgment
                stream = self.verify_agent.stream()
                async for message in stream:
                    if self.state.is_interrupted():
                        monitor_scope.cancel()
                        break

                    await self.ui.show_message(message, source="verify")
                    self.verify_logger.debug(f"Message: {message.role} - {message.content[:100]}...")

                    if message.role == "assistant":
                        feedback_messages.append(message.content)

                if not feedback_messages:
                    monitor_scope.cancel()
                    has_judgment = False
                    return

                last_content = feedback_messages[-1].upper()
                has_true = "FULLY_DONE = TRUE" in last_content or "FULLY_DONE=TRUE" in last_content
                has_false = "FULLY_DONE = FALSE" in last_content or "FULLY_DONE=FALSE" in last_content

                if has_true and not has_false:
                    fully_done = True
                    has_judgment = True

                    # Acceptance Criteria validation
                    if self.status_manager:
                        try:
                            plan_path = await self._resolve_plan_path_from_status()
                            plan_doc = await load_plan(plan_path)
                            unchecked_items: list[str] = []

                            for work_plan in plan_doc.work_plans:
                                if work_plan.acceptance_criteria_for_verification_agent:
                                    for criteria in work_plan.acceptance_criteria_for_verification_agent:
                                        for checklist in criteria.checklists:
                                            if checklist.checked_at is None or not checklist.checked_evidence:
                                                unchecked_items.append(
                                                    f"  - [{checklist.id}] {checklist.title}\n"
                                                    f"    Content: {checklist.content}"
                                                )

                            if unchecked_items:
                                assert self.verify_logger is not None
                                self.verify_logger.warning(
                                    f"FULLY_DONE = TRUE but {len(unchecked_items)} AC items unchecked"
                                )
                                self.state.set_acceptance_criteria_retry_message(
                                    "❌ You said FULLY_DONE = TRUE, but you have NOT completed all " +
                                    "acceptance_criteria_for_verification_agent items!\n\n" +
                                    "**UNCHECKED ITEMS**:\n\n" + "\n".join(unchecked_items) + "\n\n" +
                                    "**YOU MUST**:\n\n" +
                                    "1. Read each unchecked item's content carefully\n" +
                                    "2. Perform the verification specified in the content\n" +
                                    "3. Mark each item using:\n" +
                                    "   ```bash\n" +
                                    "   sisyphus-speckit plan accept-as-verification-agent --id <checklist-id> "
                                    + '--evidence "<detailed evidence>"\n'
                                    + "   ```\n\n" +
                                    "4. After ALL items are checked, THEN you can say FULLY_DONE = TRUE\n\n" +
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
                    fully_done = False
                    has_judgment = True
                else:
                    has_judgment = False

                monitor_scope.cancel()

            async def monitor_input() -> None:
                """Monitor user input and send to Verify Agent"""
                assert self.verify_logger is not None
                with monitor_scope:
                    while True:
                        msg: str | None = await self.ui.get_input()
                        if msg:
                            self.verify_logger.info(f"Sending user message: {msg[:100]}...")
                            await self.verify_agent.send(msg)
                        else:
                            await anyio.sleep(0.01)

            try:
                async with anyio.create_task_group() as tg:
                    tg.start_soon(consume_stream)
                    tg.start_soon(monitor_input)
            except* SessionLimitError as exception_group:
                first_exception = exception_group.exceptions[0]
                if not isinstance(first_exception, SessionLimitError):
                    raise
                session_limit_error = first_exception

                await self._handle_session_limit_error(session_limit_error, "verify")
                raise session_limit_error
            except* Exception as exception_group:
                if self._detect_and_handle_sdk_error(exception_group, "verify"):
                    agent_type_for_delete = type(self.verify_agent).__name__.lower().replace("agent", "")
                    await self.session_store.delete_session(agent_type_for_delete, plan_id)
                    raise RetryRequiredError(f"SDK error: {exception_group.exceptions[0]}")
                else:
                    for exception in exception_group.exceptions:
                        self.verify_logger.error(
                            f"Unexpected error in verify phase: {exception}",
                            exc_info=exception,
                        )
                    raise

            # Task Group completed normally - check interrupt status and judgment
            if self.state.is_interrupted():
                assert self._resume_event is not None
                assert self.verify_logger is not None
                await self.ui.show_status("⏸ Verify work has been interrupted")
                await self._resume_event.wait()

                resumed_msg: str | None = await self.ui.get_input()
                if resumed_msg:
                    self.verify_logger.info(f"Sending resumed message: {resumed_msg[:100]}...")
                    await self.verify_agent.send(resumed_msg)
                    self.state.set_resumed_once(True)

                self.state.set_interrupt_flag(False)
                await self.ui.show_status("▶ Resuming verify work")
            else:
                if self.state.was_resumed_once():
                    self.state.set_resumed_once(False)
                    continue
                elif not has_judgment and judgment_retry_count < max_judgment_retries:
                    judgment_retry_count += 1
                    self.verify_logger.info(
                        f"No FULLY_DONE judgment found, retrying ({judgment_retry_count}/{max_judgment_retries})"
                    )

                    ac_retry_msg = self.state.get_acceptance_criteria_retry_message()
                    if ac_retry_msg:
                        retry_message = ac_retry_msg
                        self.state.set_acceptance_criteria_retry_message(None)
                    else:
                        retry_message = (
                            "You did not provide a clear FULLY_DONE judgment in your last response. " +
                            "Please review the execute phase output and provide a clear judgment:\n\n" +
                            "- Say 'FULLY_DONE = TRUE' if all goals in the work plan are accomplished\n" +
                            "- Say 'FULLY_DONE = FALSE' if any goals remain incomplete\n\n" +
                            "Please respond with your judgment now."
                        )

                    feedback_messages.clear()
                    await self.verify_agent.send(retry_message)
                    continue
                elif not has_judgment:
                    self.verify_logger.warning(
                        "Max retries exceeded without clear judgment, defaulting to FULLY_DONE = FALSE"
                    )
                    fully_done = False
                    break
                else:
                    break

        await self.verify_agent.close()

        feedback = "\n\n".join(feedback_messages)
        self.verify_logger.info(
            f"Verify feedback collected: {len(feedback_messages)} messages, fully_done={fully_done}"
        )

        return (feedback, fully_done)

    async def _handle_session_limit_error(self, error: SessionLimitError, phase: str) -> None:
        """Handle SessionLimitError by sleeping until reset time.

        Args:
            error: SessionLimitError with reset_time
            phase: Phase name ("execute" or "verify") for logging
        """
        logger = self.execute_logger if phase == "execute" else self.verify_logger
        if logger:
            logger.error(f"Session limit reached: {error}", exc_info=error)

        await self.ui.show_status(f"⚠️  {phase.capitalize()} session limit reached")

        if error.reset_time:
            if logger:
                logger.info(f"Reset time parsed: {error.reset_time}")
            await sleep_until_reset(error.reset_time, self.ui)
        else:
            if logger:
                logger.warning("Reset time unknown, waiting until next hour")
            await self.ui.show_status("Reset time unknown, waiting until next hour...")
            await sleep_until_next_hour(self.ui)

    def _detect_and_handle_sdk_error(self, exception_group: BaseExceptionGroup, phase: str) -> bool:
        """Detect and handle SDK errors (command failed, exit code).

        Args:
            exception_group: ExceptionGroup to search for SDK errors
            phase: Phase name ("execute" or "verify") for state management

        Returns:
            True if SDK error detected and handled, False otherwise
        """
        sdk_error_detected = False
        sdk_exception = None

        for exception in exception_group.exceptions:
            error_str = str(exception).lower()
            if "command failed" in error_str or "exit code" in error_str:
                sdk_error_detected = True
                sdk_exception = exception
                break

        if sdk_error_detected:
            self.state.increment_sdk_exception()
            attempt_msg = f"(attempt {self.state._sdk_exception_count}/3)"

            logger = self.execute_logger if phase == "execute" else self.verify_logger
            if logger:
                logger.error(f"SDK error in {phase} phase: {sdk_exception} {attempt_msg}", exc_info=sdk_exception)
                logger.info("SDK error detected. Deleting invalid session.")

            if self.state.check_sdk_exception_limit():
                if logger:
                    logger.error(f"SDK error occurred 3 times. Exiting {phase} phase.")
                if phase == "execute":
                    self.state.set_should_exit_execute_phase(True)

            return True

        return False
