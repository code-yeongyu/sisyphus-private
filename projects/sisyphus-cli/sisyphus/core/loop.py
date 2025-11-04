"""ExecutionLoop for two-phase agent execution (Execute + Verify)."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

import anyio

from sisyphus.core.plans.loader import load_plan
from sisyphus.core.prompts import DEFAULT_EXECUTE_PROMPT, DEFAULT_VERIFY_PROMPT, build_execute_prompt
from sisyphus.utils.errors import PromptTooLongError, RetryRequiredError, SessionLimitError, SessionResumeError
from sisyphus.utils.session_limit import sleep_until_next_hour, sleep_until_reset

if TYPE_CHECKING:
    from sisyphus.agents.base import Agent
    from sisyphus.core.session import SessionStore
    from sisyphus.core.tasks import TaskValidator
    from sisyphus.ui.base import UIProtocol
    from sisyphus.utils.logging import LoggerFactory


class ExecutionLoop:
    """Main execution loop (Execute → Verify)."""

    def __init__(
        self,
        execute_agent: Agent,
        ui: UIProtocol,
        session_store: SessionStore,
        logger_factory: LoggerFactory,
        verify_agent: Agent | None = None,
        task_validator: TaskValidator | None = None,
    ) -> None:
        """Initialize ExecutionLoop.

        Args:
            execute_agent: Agent for execute phase
            ui: UI Protocol implementation
            session_store: Session persistence store
            logger_factory: Logger factory
            verify_agent: Optional agent for verify phase
            task_validator: Optional task validator for loop control
        """
        self.execute_agent = execute_agent
        self.verify_agent = verify_agent
        self.ui = ui
        self.session_store = session_store
        self.logger_factory = logger_factory
        self.task_validator = task_validator

        # DEBUG: Verify verify_agent during ExecutionLoop initialization
        print(f"DEBUG ExecutionLoop.__init__: verify_agent={verify_agent}", file=sys.stderr)

        self.execute_logger: logging.Logger | None = None
        self.verify_logger: logging.Logger | None = None

        self._interrupt_flag = False
        self._current_cancel_scope: anyio.CancelScope | None = None
        self._resume_event: anyio.Event | None = None
        self._resumed_once = False
        self._consecutive_execute_count: int = 0
        self._execute_resume_fail_count: int = 0
        self._sdk_exception_count: int = 0
        self._should_exit_execute_phase = False

    async def run(
        self,
        execute_extra: str | None = None,
        verify_extra: str | None = None,
    ) -> None:
        """Run the execution loop in unified mode.

        ExecutionLoop only handles task execution and does not interfere with UI lifecycle.
        After task completion, the UI continues running until the user explicitly terminates it.

        This method runs a unified execution flow that works for both interactive
        and non-interactive agents:
        - Execute Phase: Agent performs tasks (interactive features handled by agent)
        - Task Validator: Checks completion (if ai-todolist.md exists)
        - Verify Phase: Quality verification (if verify_agent provided)
        - Feedback Loop: Continues until FULLY_DONE = TRUE

        Args:
            execute_extra: Extra prompt for execute phase
            verify_extra: Extra prompt for verify phase

        Notes:
            - Execute agent can resume previous session
            - Verify agent always starts new session (independent verification)
            - Loop continues until task_validator confirms completion (if provided)
            - Interactive/non-interactive distinction is handled by agent implementation
            - UI lifecycle is managed independently by the UI itself
        """
        await self.ui.initialize()

        execute_prompt = DEFAULT_EXECUTE_PROMPT
        if self.task_validator and self.task_validator.todolist_path:
            try:
                plan_doc = await load_plan(self.task_validator.todolist_path)
                uncompleted_todos = []
                for plan in plan_doc.work_plans:
                    for todo in plan.todos:
                        if todo.status != "completed":
                            uncompleted_todos.append(f"  - [{todo.id}] {todo.title}")

                if uncompleted_todos:
                    todo_summary = "\n".join(uncompleted_todos[:10])
                    if len(uncompleted_todos) > 10:
                        todo_summary += f"\n  ... and {len(uncompleted_todos) - 10} more"

                    execute_prompt = build_execute_prompt(str(self.task_validator.todolist_path), todo_summary)
            except Exception:
                pass

        await self._run_unified_mode(execute_prompt, execute_extra, DEFAULT_VERIFY_PROMPT, verify_extra)

    async def _run_unified_mode(
        self,
        execute_prompt: str,
        execute_extra: str | None = None,
        verify_prompt: str = DEFAULT_VERIFY_PROMPT,
        verify_extra: str | None = None,
    ) -> None:
        """Unified mode: Execute -> Task Validator -> Verify phases in one flow.

        This mode runs in the following order:
        - Execute phase runs first
        - Task Validator checks completion after Execute (if provided)
        - If completed: Run Verify phase
        - If Verify returns TRUE: Exit
        - If Verify returns FALSE: Loop back to Execute
        - Feedback loop continues until FULLY_DONE = TRUE

        Args:
            execute_prompt: Execute phase prompt
            execute_extra: Extra prompt for execute phase
            verify_prompt: Verify phase prompt
            verify_extra: Extra prompt for verify phase
        """
        self._resume_event = anyio.Event()
        iteration = 0
        verify_feedback_history: list[str] = []

        execute_throttle_max_count = 10

        while True:
            iteration += 1

            self._consecutive_execute_count += 1

            force_verify = self._consecutive_execute_count >= execute_throttle_max_count

            if force_verify:
                await self.ui.show_status(
                    f"⚠️  Execute phase repeated {self._consecutive_execute_count} times consecutively. "
                    f"Forcing Verify phase to break potential infinite loop."
                )

            await self.ui.show_status(f"[Iteration {iteration}] Starting Execute phase...")

            current_execute_extra = execute_extra
            if verify_feedback_history:
                feedback_section = (
                    "\n\n## 🔍 Architect Feedback from Previous Iterations\n\n<architect-feedback-history>\n"
                )

                for i, feedback in enumerate(verify_feedback_history, 1):
                    feedback_section += f'<feedback iteration="{i}">\n{feedback}\n</feedback>\n\n'

                feedback_section += "</architect-feedback-history>\n\n"
                feedback_section += (
                    "**CRITICAL**: Address ALL issues mentioned in the feedback history above before proceeding.\n"
                )

                current_execute_extra = (execute_extra or "") + feedback_section

            should_retry_execute = False
            try:
                await self._execute_phase(execute_prompt, current_execute_extra)
            except* RetryRequiredError as exception_group:
                error = exception_group.exceptions[0]
                await self.ui.show_status(
                    f"[Iteration {iteration}] Retry required ({error.__class__.__name__}): {error}"
                )

                # PromptTooLongError → delete session and start new one
                if isinstance(error, PromptTooLongError):
                    agent_type = type(self.execute_agent).__name__.lower().replace("agent", "")
                    await self.session_store.delete_session(agent_type)
                    await self.ui.show_status(
                        f"Session '{agent_type}' cleared due to prompt length exceeded. Starting new session."
                    )

                should_retry_execute = True

            if should_retry_execute:
                continue

            should_verify = False
            if self.task_validator is not None:
                content = self.task_validator.read_content()
                goals_accomplished = self.task_validator.check_all_goals_accomplished(content)
                checkboxes_completed = self.task_validator.check_all_checkboxes_completed(content)
                should_verify = goals_accomplished and checkboxes_completed

            should_verify = should_verify or force_verify

            if force_verify and not self.verify_agent:
                await self.ui.show_status(
                    "⚠️  Execute loop detected but no Verify agent available. Terminating to prevent infinite loop."
                )
                break

            if should_verify and self.verify_agent:
                actual_verify_prompt = verify_prompt

                if verify_feedback_history:
                    history_section = "<previous_architect_reviews>\n"
                    for i, feedback in enumerate(verify_feedback_history, 1):
                        history_section += f'<review iteration="{i}">\n{feedback}\n</review>\n\n'
                    history_section += "</previous_architect_reviews>\n\n"
                    actual_verify_prompt = history_section + actual_verify_prompt

                await self.ui.show_status(f"[Iteration {iteration}] Starting Verify phase...")

                # Verify retry loop - separate from main loop to prevent Execute phase execution
                verify_retry_count = 0
                max_verify_retries = 3
                feedback = ""
                fully_done = False
                verify_succeeded = False

                while verify_retry_count < max_verify_retries and not verify_succeeded:
                    try:
                        feedback, fully_done = await self._verify_phase(actual_verify_prompt, verify_extra)
                        # Verify succeeded - exit retry loop
                        verify_succeeded = True

                    except* RetryRequiredError as exception_group:
                        error = exception_group.exceptions[0]
                        verify_retry_count += 1

                        if verify_retry_count >= max_verify_retries:
                            await self.ui.show_status(
                                f"⚠️ Verify phase failed after {max_verify_retries} attempts. "
                                "Skipping verify this iteration."
                            )
                            # Max retry exceeded - skip verify and continue to execute
                            feedback = ""
                            fully_done = False
                        else:
                            await self.ui.show_status(
                                f"[Iteration {iteration}] Verify retry required ({error.__class__.__name__}): {error} "
                                f"(attempt {verify_retry_count}/{max_verify_retries})"
                            )
                            # RetryRequiredError handling (sleep_until_reset) already done in error class
                            # Loop will continue to retry verify phase

                # Process verify results after retry loop completes
                if fully_done:
                    # Reset consecutive execute counter only when verify phase completes successfully
                    self._consecutive_execute_count = 0
                    await self.ui.show_status("✅ Architect confirmed FULLY_DONE. All work verified!")
                    break

                # Verify returned FALSE - maintain counter to ensure immediate verify re-entry on next iteration
                if feedback:
                    verify_feedback_history.append(feedback)
                await self.ui.show_status(f"[Iteration {iteration}] Verify FALSE. Feedback received, will execute...")
            elif should_verify and not self.verify_agent:
                await self.ui.show_status("✅ All tasks completed!")
                break

            if self.task_validator is None:
                if self.verify_agent:
                    await self.ui.show_status("Verification complete (no task validator for feedback loop).")
                else:
                    await self.ui.show_status("Execution complete.")
                break

    async def _execute_phase(
        self,
        prompt: str,
        extra: str | None = None,
    ) -> None:
        """Execute phase: can resume previous session.

        Args:
            prompt: Prompt for execute agent
            extra: Extra prompt to append

        Raises:
            SessionLimitError: Re-raised after handling sleep (for loop to retry)
        """
        final_prompt = prompt if extra is None else f"{prompt}\n\n{extra}"

        await self.execute_agent.initialize()

        agent_type = type(self.execute_agent).__name__.lower().replace("agent", "")
        session_id = await self.session_store.get_session(agent_type)

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

            self._execute_resume_fail_count = 0

        except SessionResumeError as e:
            self._execute_resume_fail_count += 1
            self.execute_logger.warning(
                f"❌ Failed to resume session {session_id}: {e} (attempt {self._execute_resume_fail_count}/3)"
            )

            if self._execute_resume_fail_count >= 3:
                self.execute_logger.info("Session resume failed 3 times. Resetting session store.")
                await self.session_store.delete_session(agent_type)
                self._execute_resume_fail_count = 0

            self.execute_logger.info("Starting new session instead")
            actual_session_id = await self.execute_agent.start_session(None)

        await self.session_store.save_session(agent_type, actual_session_id)

        # Send initial prompt (outside while loop - only once)
        await self.execute_agent.send(final_prompt)
        self.execute_logger.info("Prompt sent")

        self._resumed_once = False

        while True:
            # Create new CancelScope for each loop iteration
            self._current_cancel_scope = anyio.CancelScope()
            monitor_scope = self._current_cancel_scope

            async def consume_stream() -> None:
                """Consume messages from stream and display in UI"""
                assert self.execute_logger is not None
                stream = self.execute_agent.stream()
                async for message in stream:
                    if self._interrupt_flag:
                        # Interrupt occurred - cancel monitor_input and break loop
                        monitor_scope.cancel()
                        break

                    await self.ui.show_message(message, source="execute")
                    self.execute_logger.debug(f"Message: {message.role} - {message.content[:100]}...")

                # Stream completed normally - cancel monitor_input to terminate Task Group
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
                            # Short sleep when get_input() returns None (prevents CPU 100%)
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

                self.execute_logger.error(
                    f"Session limit reached: {session_limit_error}",
                    exc_info=session_limit_error,
                )
                await self.ui.show_status("⚠️  Session limit reached")

                if session_limit_error.reset_time:
                    self.execute_logger.info(f"Reset time parsed: {session_limit_error.reset_time}")
                    await sleep_until_reset(session_limit_error.reset_time, self.ui)
                else:
                    self.execute_logger.warning("Reset time unknown, waiting until next hour")
                    await self.ui.show_status("Reset time unknown, waiting until next hour...")
                    await sleep_until_next_hour(self.ui)

                raise session_limit_error
            except* Exception as exception_group:
                sdk_error_detected = False
                sdk_exception = None

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

                    await self.session_store.delete_session(agent_type)
                    if self._sdk_exception_count >= 3:
                        self.execute_logger.error("SDK error occurred 3 times. Exiting execute phase.")
                        self._should_exit_execute_phase = True

                    raise RetryRequiredError(f"SDK error: {sdk_exception}")
                else:
                    self._execute_resume_fail_count += 1
                    for exception in exception_group.exceptions:
                        attempt_msg = f"(attempt {self._execute_resume_fail_count}/3)"
                        self.execute_logger.error(
                            f"Unexpected error in execute phase: {exception} {attempt_msg}",
                            exc_info=exception,
                        )

                    if self._execute_resume_fail_count >= 3:
                        self.execute_logger.info("Exception occurred 3 times. Resetting session store.")
                        await self.session_store.delete_session(agent_type)
                        self._execute_resume_fail_count = 0
                        self._should_exit_execute_phase = True
                    else:
                        raise

            # Task Group completed normally - check interrupt status
            if self._interrupt_flag:
                assert self._resume_event is not None
                assert self.execute_logger is not None
                await self.ui.show_status("⏸ Work has been interrupted")
                await self._resume_event.wait()

                resumed_msg: str | None = await self.ui.get_input()
                if resumed_msg:
                    self.execute_logger.info(f"Sending resumed message: {resumed_msg[:100]}...")
                    await self.execute_agent.send(resumed_msg)
                    self._resumed_once = True

                self._interrupt_flag = False
                await self.ui.show_status("▶ Resuming work")
            else:
                if self._should_exit_execute_phase:
                    self._should_exit_execute_phase = False
                    self._execute_resume_fail_count = 0
                    break
                if self._resumed_once:
                    self._resumed_once = False
                    continue
                else:
                    self._execute_resume_fail_count = 0
                    break

        # Update actual session_id after stream() completes
        final_session_id = self.execute_agent.session_id
        if final_session_id and final_session_id != actual_session_id:
            self.execute_logger.info(f"Updating session ID: '{actual_session_id}' -> '{final_session_id}'")
            await self.session_store.save_session(agent_type, final_session_id)

        await self.execute_agent.close()
        self.execute_logger.info("Execute phase complete")

    async def _verify_phase(
        self,
        prompt: str,
        extra: str | None = None,
    ) -> tuple[str, bool]:
        """Verify phase: always starts NEW session (independent verification).

        Args:
            prompt: Prompt for verify agent
            extra: Extra prompt to append

        Raises:
            SessionLimitError: Re-raised after handling sleep (for loop to retry)
        """
        if self.verify_agent is None:
            return ("", False)

        feedback_messages: list[str] = []
        fully_done: bool = False

        final_prompt = prompt if extra is None else f"{prompt}\n\n{extra}"

        await self.verify_agent.initialize()

        agent_type = type(self.verify_agent).__name__.lower().replace("agent", "")

        self.verify_logger = self.logger_factory.create_logger(agent_type, None)
        self.verify_logger.info("Verify phase starting (new session)")

        actual_session_id = await self.verify_agent.start_session(None)
        self.verify_logger.info(f"New session started: {actual_session_id}")

        await self.verify_agent.send(final_prompt)
        self.verify_logger.info("Prompt sent")

        self._resumed_once = False
        max_judgment_retries = 5
        judgment_retry_count = 0

        while True:
            # Create new CancelScope for each loop iteration
            self._current_cancel_scope = anyio.CancelScope()
            monitor_scope = self._current_cancel_scope
            has_judgment = False

            async def consume_stream() -> None:
                """Consume messages from stream and collect feedback"""
                assert self.verify_logger is not None
                assert self.verify_agent is not None
                nonlocal feedback_messages, fully_done, has_judgment
                stream = self.verify_agent.stream()
                async for message in stream:
                    if self._interrupt_flag:
                        # Interrupt occurred - cancel monitor_input and break loop
                        monitor_scope.cancel()
                        break

                    await self.ui.show_message(message, source="verify")
                    self.verify_logger.debug(f"Message: {message.role} - {message.content[:100]}...")

                    if message.role == "assistant":
                        feedback_messages.append(message.content)

                # Stream completed - check FULLY_DONE only in last assistant message
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
                elif has_true or has_false:
                    fully_done = False
                    has_judgment = True
                else:
                    has_judgment = False

                monitor_scope.cancel()

            async def monitor_input() -> None:
                """Monitor user input and send to Verify Agent"""
                assert self.verify_logger is not None
                assert self.verify_agent is not None
                with monitor_scope:
                    while True:
                        msg: str | None = await self.ui.get_input()
                        if msg:
                            self.verify_logger.info(f"Sending user message: {msg[:100]}...")
                            await self.verify_agent.send(msg)
                        else:
                            # Short sleep when get_input() returns None (prevents CPU 100%)
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

                self.verify_logger.error(
                    f"Session limit reached: {session_limit_error}",
                    exc_info=session_limit_error,
                )
                await self.ui.show_status("⚠️  Verify session limit reached")

                if session_limit_error.reset_time:
                    self.verify_logger.info(f"Reset time parsed: {session_limit_error.reset_time}")
                    await sleep_until_reset(session_limit_error.reset_time, self.ui)
                else:
                    self.verify_logger.warning("Reset time unknown, waiting until next hour")
                    await self.ui.show_status("Reset time unknown, waiting until next hour...")
                    await sleep_until_next_hour(self.ui)

                raise session_limit_error
            except* Exception as exception_group:
                sdk_error_detected = False
                sdk_exception = None

                for exception in exception_group.exceptions:
                    error_str = str(exception).lower()
                    if "command failed" in error_str or "exit code" in error_str:
                        sdk_error_detected = True
                        sdk_exception = exception
                        break

                if sdk_error_detected:
                    self._sdk_exception_count += 1
                    attempt_msg = f"(attempt {self._sdk_exception_count}/3)"
                    self.verify_logger.error(
                        f"SDK error in verify phase: {sdk_exception} {attempt_msg}",
                        exc_info=sdk_exception,
                    )
                    self.verify_logger.info("SDK error detected in verify phase. Deleting invalid session.")

                    # Delete invalid session (verify always uses new session)
                    agent_type = type(self.verify_agent).__name__.lower().replace("agent", "")
                    await self.session_store.delete_session(agent_type)

                    raise RetryRequiredError(f"SDK error: {sdk_exception}")
                else:
                    for exception in exception_group.exceptions:
                        self.verify_logger.error(
                            f"Unexpected error in verify phase: {exception}",
                            exc_info=exception,
                        )
                    raise

            # Task Group completed normally - check interrupt status and judgment
            if self._interrupt_flag:
                assert self._resume_event is not None
                assert self.verify_logger is not None
                await self.ui.show_status("⏸ Verify work has been interrupted")
                await self._resume_event.wait()

                resumed_msg: str | None = await self.ui.get_input()
                if resumed_msg:
                    self.verify_logger.info(f"Sending resumed message: {resumed_msg[:100]}...")
                    await self.verify_agent.send(resumed_msg)
                    self._resumed_once = True

                self._interrupt_flag = False
                await self.ui.show_status("▶ Resuming verify work")
            else:
                if self._resumed_once:
                    self._resumed_once = False
                    continue
                elif not has_judgment and judgment_retry_count < max_judgment_retries:
                    judgment_retry_count += 1
                    self.verify_logger.info(
                        f"No FULLY_DONE judgment found, retrying ({judgment_retry_count}/{max_judgment_retries})"
                    )
                    retry_message = (
                        "You did not provide a clear FULLY_DONE judgment in your last response. "
                        "Please review the execute phase output and provide a clear judgment:\n\n"
                        "- Say 'FULLY_DONE = TRUE' if all goals in ai-todolist.md are accomplished\n"
                        "- Say 'FULLY_DONE = FALSE' if any goals remain incomplete\n\n"
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

    def request_interrupt(self) -> None:
        """Request an interrupt."""
        self._interrupt_flag = True
        if self._current_cancel_scope:
            self._current_cancel_scope.cancel()

    def clear_interrupt(self) -> None:
        """Clear the interrupt."""
        self._interrupt_flag = False
        if self._resume_event is not None:
            self._resume_event.set()
