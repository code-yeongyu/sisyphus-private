"""ExecutionLoop for two-phase agent execution (Execute + Verify)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import anyio

from sisyphus.core.plans.loader import load_plan, save_plan
from sisyphus.core.plans.models import Todo, TodoStatus
from sisyphus.core.prompts import (
    DEFAULT_EXECUTE_PROMPT,
    build_execute_prompt,
    build_verification_failure_prompt,
    build_verify_prompt,
)
from sisyphus.utils.errors import PromptTooLongError, RetryRequiredError, SessionLimitError, SessionResumeError
from sisyphus.utils.session_limit import sleep_until_next_hour, sleep_until_reset

if TYPE_CHECKING:
    from sisyphus.agents.base import Agent
    from sisyphus.core.session import SessionStore
    from sisyphus.core.status.manager import StatusManager
    from sisyphus.ui.base import UIProtocol
    from sisyphus.utils.logging import LoggerFactory


class TaskValidatorProtocol(Protocol):
    """Protocol for task validator objects."""

    todolist_path: Path

    def read_content(self) -> str:
        """Read todolist content."""
        ...

    async def check_all_goals_accomplished(self, content: str | None = None) -> bool:
        """Check if all goals are accomplished."""
        ...

    async def check_all_checkboxes_completed(self, content: str | None = None) -> bool:
        """Check if all checkboxes are completed."""
        ...


class ExecutionLoop:
    """Main execution loop (Execute → Verify)."""

    def __init__(
        self,
        execute_agent: Agent,
        ui: UIProtocol,
        session_store: SessionStore,
        logger_factory: LoggerFactory,
        verify_agent: Agent,
        task_validator: TaskValidatorProtocol,
        working_directory: Path | None = None,
        status_manager: StatusManager | None = None,
    ) -> None:
        """Initialize ExecutionLoop.

        Args:
            execute_agent: Agent for execute phase
            ui: UI Protocol implementation
            session_store: Session persistence store
            logger_factory: Logger factory
            verify_agent: Agent for verify phase
            task_validator: Task validator for loop control
            working_directory: Optional execution working directory
            status_manager: Optional status manager for tracking current plan
        """
        self.execute_agent = execute_agent
        self.verify_agent = verify_agent
        self.ui = ui
        self.session_store = session_store
        self.logger_factory = logger_factory
        self.task_validator = task_validator
        self.working_directory = working_directory
        self.status_manager = status_manager

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
        self._current_plan_id: str = ""

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
        - Task Validator: Checks completion (if task file exists)
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
        verify_prompt = ""
        resolved_plan_path: str | None = None

        # Priority 1: Try status_manager first (if available)
        if self.status_manager:
            try:
                status_file = await self.status_manager.get()
                if status_file.current_plan and status_file.current_plan.plan_path:
                    plan_path = Path(status_file.current_plan.plan_path)
                    resolved_plan_path = str(plan_path)
                    plan_doc = await load_plan(plan_path)

                    if not plan_doc.work_plans:
                        self._current_plan_id = "default"
                    else:
                        self._current_plan_id = plan_doc.work_plans[0].id

                    uncompleted_todos = []
                    for plan in plan_doc.work_plans:
                        for todo in plan.todos:
                            if todo.status != "completed":
                                uncompleted_todos.append(f"  - [{todo.id}] {todo.title}")

                    todo_summary = "\n".join(uncompleted_todos[:10]) if uncompleted_todos else "All tasks completed"
                    if len(uncompleted_todos) > 10:
                        todo_summary += f"\n  ... and {len(uncompleted_todos) - 10} more"

                    execute_prompt = build_execute_prompt(resolved_plan_path, todo_summary)
                    verify_prompt = build_verify_prompt(resolved_plan_path)
                else:
                    # status.json exists but no current_plan → fallback to task_validator
                    if self.task_validator and self.task_validator.todolist_path:
                        resolved_plan_path = str(self.task_validator.todolist_path)
                        plan_doc = await load_plan(self.task_validator.todolist_path)

                        if not plan_doc.work_plans:
                            self._current_plan_id = "default"
                        else:
                            self._current_plan_id = plan_doc.work_plans[0].id

                        uncompleted_todos = []
                        for plan in plan_doc.work_plans:
                            for todo in plan.todos:
                                if todo.status != "completed":
                                    uncompleted_todos.append(f"  - [{todo.id}] {todo.title}")

                        todo_summary = (
                            "\n".join(uncompleted_todos[:10]) if uncompleted_todos else "All tasks completed"
                        )
                        if len(uncompleted_todos) > 10:
                            todo_summary += f"\n  ... and {len(uncompleted_todos) - 10} more"

                        execute_prompt = build_execute_prompt(resolved_plan_path, todo_summary)
                        verify_prompt = build_verify_prompt(resolved_plan_path)
                    else:
                        self._current_plan_id = "default"
            except Exception:
                # If status.json read fails, fallback to task_validator
                if self.task_validator and self.task_validator.todolist_path:
                    try:
                        resolved_plan_path = str(self.task_validator.todolist_path)
                        plan_doc = await load_plan(self.task_validator.todolist_path)

                        if not plan_doc.work_plans:
                            self._current_plan_id = "default"
                        else:
                            self._current_plan_id = plan_doc.work_plans[0].id

                        uncompleted_todos = []
                        for plan in plan_doc.work_plans:
                            for todo in plan.todos:
                                if todo.status != "completed":
                                    uncompleted_todos.append(f"  - [{todo.id}] {todo.title}")

                        todo_summary = (
                            "\n".join(uncompleted_todos[:10]) if uncompleted_todos else "All tasks completed"
                        )
                        if len(uncompleted_todos) > 10:
                            todo_summary += f"\n  ... and {len(uncompleted_todos) - 10} more"

                        execute_prompt = build_execute_prompt(resolved_plan_path, todo_summary)
                        verify_prompt = build_verify_prompt(resolved_plan_path)
                    except Exception:
                        self._current_plan_id = "default"
                else:
                    self._current_plan_id = "default"
        # Priority 2: Fallback to task_validator (backward compatibility)
        elif self.task_validator and self.task_validator.todolist_path:
            try:
                resolved_plan_path = str(self.task_validator.todolist_path)
                plan_doc = await load_plan(self.task_validator.todolist_path)

                if not plan_doc.work_plans:
                    self._current_plan_id = "default"
                else:
                    self._current_plan_id = plan_doc.work_plans[0].id

                uncompleted_todos = []
                for plan in plan_doc.work_plans:
                    for todo in plan.todos:
                        if todo.status != "completed":
                            uncompleted_todos.append(f"  - [{todo.id}] {todo.title}")

                todo_summary = "\n".join(uncompleted_todos[:10]) if uncompleted_todos else "All tasks completed"
                if len(uncompleted_todos) > 10:
                    todo_summary += f"\n  ... and {len(uncompleted_todos) - 10} more"

                execute_prompt = build_execute_prompt(resolved_plan_path, todo_summary)
                verify_prompt = build_verify_prompt(resolved_plan_path)
            except Exception:
                self._current_plan_id = "default"
        else:
            self._current_plan_id = "default"

        await self._run_unified_mode(execute_prompt, execute_extra, verify_prompt, verify_extra)

    async def _run_unified_mode(
        self,
        execute_prompt: str,
        execute_extra: str | None = None,
        verify_prompt: str = "",
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

        if self.task_validator:
            content = self.task_validator.read_content()
            goals_accomplished = await self.task_validator.check_all_goals_accomplished(content)
            checkboxes_completed = await self.task_validator.check_all_checkboxes_completed(content)
            if goals_accomplished and checkboxes_completed:
                await self.ui.show_status("✅ All tasks already completed. Starting Verify phase...")

        while True:
            iteration += 1

            self._consecutive_execute_count += 1

            force_verify = self._consecutive_execute_count >= execute_throttle_max_count

            if force_verify:
                await self.ui.show_status(
                    f"⚠️  Execute phase repeated {self._consecutive_execute_count} times consecutively. "
                    f"Forcing Verify phase to break potential infinite loop."
                )

            skip_execute = False
            if iteration == 1 and self.task_validator:
                content = self.task_validator.read_content()
                goals_accomplished = await self.task_validator.check_all_goals_accomplished(content)
                checkboxes_completed = await self.task_validator.check_all_checkboxes_completed(content)
                if goals_accomplished and checkboxes_completed:
                    skip_execute = True
                    await self.ui.show_status("✅ All tasks already completed. Skipping Execute phase...")

            should_retry_execute = False
            skip_count_and_retry = False
            if not skip_execute:
                await self.ui.show_status(f"[Iteration {iteration}] Starting Execute phase...")

                current_execute_prompt = execute_prompt
                current_execute_extra = execute_extra

                if verify_feedback_history:
                    try:
                        plan_path_for_failure_prompt = None
                        if self.status_manager:
                            status_file = await self.status_manager.get()
                            if status_file.current_plan and status_file.current_plan.plan_path:
                                plan_path_for_failure_prompt = Path(status_file.current_plan.plan_path)
                        elif self.task_validator and self.task_validator.todolist_path:
                            plan_path_for_failure_prompt = self.task_validator.todolist_path

                        if plan_path_for_failure_prompt:
                            plan_doc = await load_plan(plan_path_for_failure_prompt)
                            uncompleted_todos = []
                            for plan in plan_doc.work_plans:
                                for todo in plan.todos:
                                    if todo.status != "completed":
                                        uncompleted_todos.append(f"  - [{todo.id}] {todo.title}")

                            todo_summary = (
                                "\n".join(uncompleted_todos[:10]) if uncompleted_todos else "All tasks completed"
                            )
                            if len(uncompleted_todos) > 10:
                                todo_summary += f"\n  ... and {len(uncompleted_todos) - 10} more"

                            current_execute_prompt = build_verification_failure_prompt(
                                str(plan_path_for_failure_prompt), todo_summary
                            )
                    except Exception:
                        pass

                    feedback_section = (
                        "\n\n## 🔍 Verify Feedback from Previous Iterations\n\n<verify-feedback-history>\n"
                    )

                    for i, feedback in enumerate(verify_feedback_history, 1):
                        feedback_section += f'<feedback iteration="{i}">\n{feedback}\n</feedback>\n\n'

                    feedback_section += "</verify-feedback-history>\n\n"
                    feedback_section += (
                        "**CRITICAL**: Address ALL issues mentioned in the feedback history above before proceeding.\n"
                    )

                    current_execute_extra = (execute_extra or "") + feedback_section

                try:
                    await self._execute_phase(current_execute_prompt, current_execute_extra)
                except* RetryRequiredError as exception_group:
                    error = exception_group.exceptions[0]

                    if isinstance(error, PromptTooLongError) and verify_feedback_history:
                        verify_feedback_history.pop(0)
                        await self.ui.show_status(
                            f"⚠️  Prompt too long. Removing oldest feedback (remaining: {len(verify_feedback_history)})"
                        )
                        skip_count_and_retry = True
                    else:
                        await self.ui.show_status(
                            f"[Iteration {iteration}] Retry required ({error.__class__.__name__}): {error}"
                        )

                        if isinstance(error, PromptTooLongError):
                            agent_type = type(self.execute_agent).__name__.lower().replace("agent", "")
                            await self.session_store.delete_session(agent_type, self._current_plan_id)
                            await self.ui.show_status(
                                f"Session '{agent_type}' cleared due to prompt length exceeded. Starting new session."
                            )

                        should_retry_execute = True

            if skip_count_and_retry:
                self._consecutive_execute_count -= 1
                continue

            if should_retry_execute:
                continue

            should_verify = force_verify
            if self.task_validator:
                content = self.task_validator.read_content()
                goals_accomplished = await self.task_validator.check_all_goals_accomplished(content)
                checkboxes_completed = await self.task_validator.check_all_checkboxes_completed(content)
                should_verify = should_verify or (goals_accomplished and checkboxes_completed)

            if should_verify:
                actual_verify_prompt = verify_prompt

                if verify_feedback_history:
                    history_section = "<previous_verify_reviews>\n"
                    for i, feedback in enumerate(verify_feedback_history, 1):
                        history_section += f'<review iteration="{i}">\n{feedback}\n</review>\n\n'
                    history_section += "</previous_verify_reviews>\n\n"
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

                if self.task_validator:
                    plan_doc = await load_plan(self.task_validator.todolist_path)

                    for work_plan in plan_doc.work_plans:
                        work_plan.execution.completed = fully_done

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

                    await save_plan(self.task_validator.todolist_path, plan_doc)

                if fully_done:
                    self._consecutive_execute_count = 0
                    await self.ui.show_status("✅ Verify agent confirmed FULLY_DONE. All work verified!")
                    break
                else:
                    await self.ui.show_status(
                        f"[Iteration {iteration}] Verify FALSE. Task reset to in_progress, will re-execute..."
                    )

                if feedback:
                    verify_feedback_history.append(feedback)
            elif should_verify and not self.verify_agent:
                await self.ui.show_status("✅ All tasks completed!")
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

        if not self._current_plan_id and self.status_manager:
            if hasattr(self.status_manager, "get_plan_id"):
                self._current_plan_id = await self.status_manager.get_plan_id()
            else:
                status = await self.status_manager.get()
                if status.current_plan:
                    plan_path = Path(status.current_plan.plan_path)
                    plan = await load_plan(plan_path)
                    self._current_plan_id = plan.work_plans[0].id

        if not self._current_plan_id:
            raise ValueError("plan_id is required for session management")

        agent_type = type(self.execute_agent).__name__.lower().replace("agent", "")
        session_id = await self.session_store.get_session(agent_type, self._current_plan_id)

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
                await self.session_store.delete_session(agent_type, self._current_plan_id)
                self._execute_resume_fail_count = 0

            self.execute_logger.info("Starting new session instead")
            actual_session_id = await self.execute_agent.start_session(None)

        await self.session_store.save_session(agent_type, actual_session_id, self._current_plan_id)

        # Send initial prompt (outside while loop - only once)
        await self.execute_agent.send(final_prompt)
        self.execute_logger.info("Prompt sent")

        self._resumed_once = False

        while True:
            self._current_cancel_scope = anyio.CancelScope()
            monitor_scope: anyio.CancelScope = self._current_cancel_scope

            async def consume_stream() -> None:
                """Consume messages from stream and display in UI"""
                assert self.execute_logger is not None
                stream = self.execute_agent.stream()
                async for message in stream:
                    if self._interrupt_flag:
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

                    await self.session_store.delete_session(agent_type, self._current_plan_id)
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
                        await self.session_store.delete_session(agent_type, self._current_plan_id)
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
            await self.session_store.save_session(agent_type, final_session_id, self._current_plan_id)

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

        if not self._current_plan_id and self.status_manager:
            if hasattr(self.status_manager, "get_plan_id"):
                self._current_plan_id = await self.status_manager.get_plan_id()
            else:
                status = await self.status_manager.get()
                if status.current_plan:
                    plan_path = Path(status.current_plan.plan_path)
                    plan = await load_plan(plan_path)
                    self._current_plan_id = plan.work_plans[0].id

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
            self._current_cancel_scope = anyio.CancelScope()
            monitor_scope: anyio.CancelScope = self._current_cancel_scope
            has_judgment = False

            async def consume_stream() -> None:
                """Consume messages from stream and collect feedback"""
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
                    await self.session_store.delete_session(agent_type, self._current_plan_id)

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
                        "- Say 'FULLY_DONE = TRUE' if all goals in the work plan are accomplished\n"
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
