# pyright: reportImportCycles=false
"""ExecutionLoop for two-phase agent execution (Execute + Verify)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import anyio

from sisyphus_core.core.feedback_manager import FeedbackManager
from sisyphus_core.core.loop_state import LoopState
from sisyphus_core.core.phase_orchestrator import PhaseOrchestrator
from sisyphus_core.core.plans.loader import load_plan, save_plan
from sisyphus_core.core.plans.models import Todo, TodoStatus
from sisyphus_core.core.prompts import (
    DEFAULT_EXECUTE_PROMPT,
    build_execute_prompt,
    build_simple_execute_prompt,
    build_verification_failure_prompt,
    build_verify_prompt,
)
from sisyphus_core.utils.errors import PromptTooLongError, RetryRequiredError

if TYPE_CHECKING:
    from sisyphus_core.agents.base import Agent
    from sisyphus_core.core.session import SessionStore
    from sisyphus_core.core.status.manager import StatusManager
    from sisyphus_core.ui.base import UIProtocol
    from sisyphus_core.utils.logging import LoggerFactory


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
        verify_agent: Agent,
        ui: UIProtocol,
        session_store: SessionStore,
        logger_factory: LoggerFactory,
        task_validator: TaskValidatorProtocol,
        working_directory: Path | None = None,
        status_manager: StatusManager | None = None,
    ) -> None:
        """Initialize ExecutionLoop.

        Args:
            execute_agent: Agent for execute phase
            verify_agent: Agent for verify phase (REQUIRED)
            ui: UI Protocol implementation
            session_store: Session persistence store
            logger_factory: Logger factory
            task_validator: Task validator for loop control
            working_directory: Optional execution working directory
            status_manager: Optional status manager for tracking current plan
        """
        self.state = LoopState()
        self.feedback_manager = FeedbackManager()
        self.phase_orchestrator = PhaseOrchestrator(
            execute_agent, verify_agent, ui, session_store, logger_factory, self.state, status_manager
        )

        self.execute_agent: Agent = execute_agent
        self.ui: UIProtocol = ui
        self.task_validator: TaskValidatorProtocol = task_validator
        self.status_manager: StatusManager | None = status_manager
        self.working_directory: Path | None = working_directory

        self._resume_event: anyio.Event | None = None
        self._current_cancel_scope: anyio.CancelScope | None = None

        print(f"DEBUG ExecutionLoop.__init__: verify_agent={verify_agent}", file=sys.stderr)

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

        try:
            plan_path = await self._resolve_plan_path_from_status()
            execute_prompt, verify_prompt, _ = await self._initialize_from_plan(plan_path)
        except (ValueError, FileNotFoundError):
            if not self.state.get_plan_id():
                plan_id = await self._resolve_plan_id()
                self.state.set_plan_id(plan_id)
            if not verify_prompt:
                verify_prompt = build_verify_prompt("(plan path unavailable)")

        await self._run_unified_mode(execute_prompt, execute_extra, verify_prompt, verify_extra)

    async def _resolve_plan_path_from_status(self) -> Path:
        """Resolve plan path from status_manager (single source of truth).

        Returns:
            Path: Resolved plan path

        Raises:
            ValueError: If status_manager is None or current_plan is not set
        """
        if not self.status_manager:
            raise ValueError(
                "status_manager is required. "
                + "task_validator.todolist_path fallback has been removed in v3.0. "
                + "Please set status_manager in ExecutionLoop initialization."
            )

        status_file = await self.status_manager.get()
        if not status_file.current_plan or not status_file.current_plan.plan_path:
            raise ValueError(
                "current_plan is not set in status.json. "
                + "Please run 'sisyphus-speckit plan init' or set current plan first."
            )

        return Path(status_file.current_plan.plan_path)

    async def _initialize_from_plan(
        self,
        plan_path: Path,
    ) -> tuple[str, str, str]:
        """Initialize plan context from plan path (DRY - used once).

        Args:
            plan_path: Path to YAML plan file

        Returns:
            Tuple of (execute_prompt, verify_prompt, resolved_plan_path_str)
        """
        plan_doc = await load_plan(plan_path)

        if not plan_doc.work_plans:
            plan_id = "default"
        else:
            plan_id = plan_doc.work_plans[0].id

        self.state.set_plan_id(plan_id)

        uncompleted_todos = []
        for plan in plan_doc.work_plans:
            for todo in plan.todos:
                if todo.status != "completed":
                    uncompleted_todos.append(f"  - [{todo.id}] {todo.title}")

        todo_summary = "\n".join(uncompleted_todos[:10]) if uncompleted_todos else "All tasks completed"
        if len(uncompleted_todos) > 10:
            todo_summary += f"\n  ... and {len(uncompleted_todos) - 10} more"

        # Use simple prompt if execute agent has orchestrator system prompt
        from sisyphus_core.agents.claude import ClaudeAgent

        if isinstance(self.execute_agent, ClaudeAgent) and self.execute_agent._system_prompt:
            execute_prompt = build_simple_execute_prompt(str(plan_path), todo_summary)
        else:
            execute_prompt = build_execute_prompt(str(plan_path), todo_summary)

        verify_prompt = build_verify_prompt(str(plan_path))

        return (execute_prompt, verify_prompt, str(plan_path))

    async def _resolve_plan_id(self) -> str:
        """Resolve plan ID from status_manager (single source of truth).

        Returns:
            str: Plan ID or "default" if not available
        """
        if not self.status_manager:
            return "default"

        # MockStatusManager support (testing)
        if hasattr(self.status_manager, "get_plan_id"):
            return await self.status_manager.get_plan_id()  # type: ignore

        try:
            status = await self.status_manager.get()
            if status.current_plan:
                plan_path = Path(status.current_plan.plan_path)
                plan = await load_plan(plan_path)
                return plan.work_plans[0].id if plan.work_plans else "default"
        except Exception:
            pass

        return "default"

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
        self.phase_orchestrator.set_resume_event(self._resume_event)

        if self.task_validator:
            content = self.task_validator.read_content()
            goals = await self.task_validator.check_all_goals_accomplished(content)
            checkboxes = await self.task_validator.check_all_checkboxes_completed(content)
            if goals and checkboxes:
                await self.ui.show_status("✅ All tasks already completed. Starting Verify phase...")

        while True:
            self.state.increment_iteration()
            self.state.increment_consecutive_execute()

            skip_execute = await self._should_skip_execute()

            should_retry_execute = False
            if not skip_execute:
                await self.ui.show_status(f"[Iteration {self.state.iteration}] Starting Execute phase...")

                prompt, extra = await self._build_execute_prompt(execute_prompt, execute_extra)

                try:
                    await self.phase_orchestrator.execute_phase(prompt, extra)
                except* RetryRequiredError as eg:
                    should_retry_execute = await self._handle_execute_retry_error(eg)

            if should_retry_execute:
                continue

            if not await self._should_verify():
                continue

            await self.ui.show_status(f"[Iteration {self.state.iteration}] Starting Verify phase...")

            prompt = self.feedback_manager.build_feedback_section_for_verify(verify_prompt)

            feedback = ""
            fully_done = False
            should_retry_verify = False

            try:
                feedback, fully_done = await self._verify_phase_with_retry(prompt, verify_extra)
            except* RetryRequiredError as eg:
                should_retry_verify = await self._handle_verify_retry_error(eg)

            if should_retry_verify:
                continue

            await self._update_plan_execution_status(fully_done)

            if fully_done:
                self.state.reset_consecutive_execute()
                self.state.reset_sdk_exception()
                await self.ui.show_status("✅ Verify agent confirmed FULLY_DONE. All work verified!")
                break
            else:
                await self.ui.show_status(
                    f"[Iteration {self.state.iteration}] Verify FALSE. Task reset to in_progress, will re-execute..."
                )

            if feedback:
                self.feedback_manager.add_feedback(feedback)

    async def _should_skip_execute(self) -> bool:
        """Check if Execute phase should be skipped.

        Returns:
            True if should skip, False otherwise
        """
        if not self.task_validator:
            return False

        content = self.task_validator.read_content()
        goals_accomplished = await self.task_validator.check_all_goals_accomplished(content)
        checkboxes_completed = await self.task_validator.check_all_checkboxes_completed(content)

        if goals_accomplished and checkboxes_completed:
            if self.state.iteration == 1:
                await self.ui.show_status("✅ All tasks already completed. Skipping Execute phase...")
            return True

        return False

    async def _should_verify(self) -> bool:
        """Check if Verify phase should run.

        Returns:
            True if should verify, False otherwise
        """
        should_verify = self.state.check_force_verify()

        if should_verify:
            await self.ui.show_status(
                f"⚠️  Execute phase repeated {self.state._consecutive_execute_count} times consecutively. "
                f"Forcing Verify phase to break potential infinite loop."
            )

        # Check execution.completed from plan
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
                # Fallback to task_validator
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

        return should_verify

    async def _build_execute_prompt(
        self,
        execute_prompt: str,
        execute_extra: str | None,
    ) -> tuple[str, str]:
        """Build Execute phase prompt with feedback history.

        Args:
            execute_prompt: Base execute prompt
            execute_extra: Extra execute content

        Returns:
            Tuple of (prompt, extra_with_feedback)
        """
        current_execute_prompt = execute_prompt
        current_execute_extra = execute_extra

        # Update execute prompt to verification_failure_prompt if feedback exists
        if self.feedback_manager.has_history():
            try:
                plan_path_for_failure_prompt = None
                if self.status_manager:
                    status_file = await self.status_manager.get()
                    if status_file.current_plan and status_file.current_plan.plan_path:
                        plan_path_for_failure_prompt = Path(status_file.current_plan.plan_path)

                if plan_path_for_failure_prompt:
                    plan_doc = await load_plan(plan_path_for_failure_prompt)
                    uncompleted_todos = []
                    for plan in plan_doc.work_plans:
                        for todo in plan.todos:
                            if todo.status != "completed":
                                uncompleted_todos.append(f"  - [{todo.id}] {todo.title}")

                    todo_summary = "\n".join(uncompleted_todos[:10]) if uncompleted_todos else "All tasks completed"
                    if len(uncompleted_todos) > 10:
                        todo_summary += f"\n  ... and {len(uncompleted_todos) - 10} more"

                    current_execute_prompt = build_verification_failure_prompt(
                        str(plan_path_for_failure_prompt), todo_summary
                    )
            except Exception:
                pass

        # Add feedback to execute_extra
        current_execute_extra = self.feedback_manager.build_feedback_section_for_execute(execute_extra)

        return (current_execute_prompt, current_execute_extra)

    async def _handle_execute_retry_error(self, exception_group: BaseExceptionGroup) -> bool:
        """Handle Execute phase RetryRequiredError.

        Args:
            exception_group: ExceptionGroup containing RetryRequiredError

        Returns:
            True if should continue loop (retry), False otherwise
        """
        error = exception_group.exceptions[0]

        # PromptTooLongError with feedback history: remove oldest feedback and retry
        if isinstance(error, PromptTooLongError) and self.feedback_manager.has_history():
            self.feedback_manager.clear_oldest()
            await self.ui.show_status(
                f"⚠️  Prompt too long. Removing oldest feedback (remaining: {len(self.feedback_manager.get_history())})"
            )
            self.state.decrement_consecutive_execute()  # Don't count this iteration
            return True  # Continue loop (retry)

        # Other RetryRequiredError: log and retry
        await self.ui.show_status(
            f"[Iteration {self.state.iteration}] Retry required ({error.__class__.__name__}): {error}"
        )

        # PromptTooLongError: delete session
        if isinstance(error, PromptTooLongError):
            agent_type = type(self.phase_orchestrator.execute_agent).__name__.lower().replace("agent", "")
            await self.phase_orchestrator.session_store.delete_session(agent_type, self.state.get_plan_id())
            await self.ui.show_status(
                f"Session '{agent_type}' cleared due to prompt length exceeded. Starting new session."
            )

        return True  # Continue loop (retry)

    async def _handle_verify_retry_error(self, exception_group: BaseExceptionGroup) -> bool:
        """Handle Verify phase RetryRequiredError.

        Args:
            exception_group: ExceptionGroup containing RetryRequiredError

        Returns:
            True if should continue loop (retry), False otherwise
        """
        error = exception_group.exceptions[0]
        await self.ui.show_status(
            f"[Iteration {self.state.iteration}] Verify retry required ({error.__class__.__name__}): {error}"
        )
        return True  # Continue loop (retry)

    async def _verify_phase_with_retry(
        self,
        prompt: str,
        extra: str | None,
    ) -> tuple[str, bool]:
        """Run Verify phase with retry logic.

        Retries up to 3 times on RetryRequiredError.

        Args:
            prompt: Verify phase prompt
            extra: Extra verify content

        Returns:
            Tuple of (feedback, fully_done)
        """
        verify_retry_count = 0
        max_verify_retries = 3
        feedback = ""
        fully_done = False
        verify_succeeded = False

        while verify_retry_count < max_verify_retries and not verify_succeeded:
            try:
                feedback, fully_done = await self.phase_orchestrator.verify_phase(prompt, extra)
                verify_succeeded = True
            except* RetryRequiredError as exception_group:
                error = exception_group.exceptions[0]
                verify_retry_count += 1

                if verify_retry_count >= max_verify_retries:
                    await self.ui.show_status(
                        f"⚠️ Verify phase failed after {max_verify_retries} attempts. Skipping verify this iteration."
                    )
                    feedback = ""
                    fully_done = False
                else:
                    error_name = error.__class__.__name__
                    await self.ui.show_status(
                        f"[Iteration {self.state.iteration}] Verify retry required ({error_name}): {error} "
                        f"(attempt {verify_retry_count}/{max_verify_retries})"
                    )

        return (feedback, fully_done)

    async def _update_plan_execution_status(self, fully_done: bool) -> None:
        """Update plan execution status and task status.

        Args:
            fully_done: Whether verify phase confirmed FULLY_DONE
        """
        if not self.status_manager:
            return

        try:
            plan_path = await self._resolve_plan_path_from_status()
            plan_doc = await load_plan(plan_path)

            for work_plan in plan_doc.work_plans:
                work_plan.execution.completed = fully_done

                # Reset current task to in_progress if not fully_done
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

                    _ = find_and_reset_task(work_plan.todos)

            await save_plan(plan_path, plan_doc)
        except (ValueError, FileNotFoundError):
            pass

    def request_interrupt(self) -> None:
        """Request an interrupt."""
        self.state.set_interrupt_flag(True)
        if self.phase_orchestrator._current_cancel_scope:
            self.phase_orchestrator._current_cancel_scope.cancel()

    def clear_interrupt(self) -> None:
        """Clear the interrupt."""
        self.state.set_interrupt_flag(False)
        if self._resume_event is not None:
            self._resume_event.set()
