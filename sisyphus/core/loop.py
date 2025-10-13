"""ExecutionLoop for two-phase agent execution (Execute + Verify)."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from sisyphus.core.prompts import DEFAULT_EXECUTE_PROMPT, DEFAULT_VERIFY_PROMPT
from sisyphus.utils.errors import SessionLimitError, SessionResumeError
from sisyphus.utils.session_limit import sleep_until_next_hour, sleep_until_reset

if TYPE_CHECKING:
    from sisyphus.agents.base import Agent
    from sisyphus.core.prompts import PromptResolver
    from sisyphus.core.session import SessionStore
    from sisyphus.core.tasks import TaskValidator
    from sisyphus.ui.base import UIProtocol
    from sisyphus.utils.logging import LoggerFactory


class ExecutionLoop:
    """메인 실행 루프 (Execute → Verify)."""

    def __init__(
        self,
        execute_agent: Agent,
        ui: UIProtocol,
        session_store: SessionStore,
        prompt_resolver: PromptResolver,
        logger_factory: LoggerFactory,
        verify_agent: Agent | None = None,
        task_validator: TaskValidator | None = None,
    ) -> None:
        """Initialize ExecutionLoop.

        Args:
            execute_agent: Agent for execute phase
            ui: UI Protocol implementation
            session_store: Session persistence store
            prompt_resolver: Prompt resolver
            logger_factory: Logger factory
            verify_agent: Optional agent for verify phase
            task_validator: Optional task validator for loop control
        """
        self.execute_agent = execute_agent
        self.verify_agent = verify_agent
        self.ui = ui
        self.session_store = session_store
        self.prompt_resolver = prompt_resolver
        self.logger_factory = logger_factory
        self.task_validator = task_validator

        # DEBUG: ExecutionLoop 초기화 시 verify_agent 확인

        print(f"DEBUG ExecutionLoop.__init__: verify_agent={verify_agent}", file=sys.stderr)

        self.execute_logger: logging.Logger | None = None
        self.verify_logger: logging.Logger | None = None

    async def run(
        self,
        execute_prompt: str | None,
        execute_extra: str | None = None,
        verify_prompt: str | None = None,
        verify_extra: str | None = None,
    ) -> None:
        """Run the execution loop in unified mode.

        ExecutionLoop는 작업 실행만 담당하며, UI 생명주기는 관여하지 않습니다.
        작업 완료 후 UI는 사용자가 명시적으로 종료할 때까지 계속 실행됩니다.

        This method runs a unified execution flow that works for both interactive
        and non-interactive agents:
        - Execute Phase: Agent performs tasks (interactive features handled by agent)
        - Task Validator: Checks completion (if ai-todolist.md exists)
        - Verify Phase: Quality verification (if verify_agent provided)
        - Feedback Loop: Continues until FULLY_DONE = TRUE

        Args:
            execute_prompt: Execute phase prompt (None = use DEFAULT_EXECUTE_PROMPT)
            execute_extra: Extra prompt for execute phase
            verify_prompt: Verify phase prompt (None = use DEFAULT_VERIFY_PROMPT)
            verify_extra: Extra prompt for verify phase

        Notes:
            - Execute agent can resume previous session
            - Verify agent always starts new session (independent verification)
            - Loop continues until task_validator confirms completion (if provided)
            - Interactive/non-interactive distinction is handled by agent implementation
            - UI lifecycle is managed independently by the UI itself
        """
        await self.ui.initialize()

        actual_execute_prompt = execute_prompt if execute_prompt is not None else DEFAULT_EXECUTE_PROMPT

        await self._run_unified_mode(actual_execute_prompt, execute_extra, verify_prompt, verify_extra)

    async def _run_unified_mode(
        self,
        execute_prompt: str,
        execute_extra: str | None = None,
        verify_prompt: str | None = None,
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
        iteration = 0
        verify_feedback_history: list[str] = []

        while True:
            iteration += 1

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

            try:
                await self._execute_phase(execute_prompt, current_execute_extra)
            except SessionLimitError:
                await self.ui.show_status(f"[Iteration {iteration}] Session limit handled, retrying...")
                continue

            should_verify = False
            if self.task_validator is not None:
                content = self.task_validator.read_content()
                goals_accomplished = self.task_validator.check_all_goals_accomplished(content)
                checkboxes_completed = self.task_validator.check_all_checkboxes_completed(content)
                should_verify = goals_accomplished and checkboxes_completed

            if should_verify and self.verify_agent:
                actual_verify_prompt = verify_prompt if verify_prompt is not None else DEFAULT_VERIFY_PROMPT

                if verify_feedback_history:
                    history_section = "<previous_architect_reviews>\n"
                    for i, feedback in enumerate(verify_feedback_history, 1):
                        history_section += f'<review iteration="{i}">\n{feedback}\n</review>\n\n'
                    history_section += "</previous_architect_reviews>\n\n"
                    actual_verify_prompt = history_section + actual_verify_prompt

                await self.ui.show_status(f"[Iteration {iteration}] Starting Verify phase...")

                try:
                    feedback, fully_done = await self._verify_phase(actual_verify_prompt, verify_extra)

                    if fully_done:
                        await self.ui.show_status("✅ Architect confirmed FULLY_DONE. All work verified!")
                        break

                    verify_feedback_history.append(feedback)
                    await self.ui.show_status(
                        f"[Iteration {iteration}] Verify FALSE. Feedback received, will execute..."
                    )
                except SessionLimitError:
                    await self.ui.show_status(f"[Iteration {iteration}] Verify session limit handled, retrying...")
                    continue
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
        final_prompt = await self.prompt_resolver.resolve(prompt, extra)

        await self.execute_agent.initialize()

        agent_type = type(self.execute_agent).__name__.lower().replace("agent", "")
        session_id = await self.session_store.get_session(agent_type)

        self.execute_logger = self.logger_factory.create_logger(agent_type, session_id)
        self.execute_logger.info(f"Execute phase starting (session_id={session_id})")

        # Resume 시도 로깅
        if session_id:
            self.execute_logger.info(f"Attempting to resume session: {session_id}")
        else:
            self.execute_logger.info("Starting new session")

        # Resume 실패 시 fallback
        try:
            actual_session_id = await self.execute_agent.start_session(session_id)

            # Resume 성공 로깅
            if session_id:
                self.execute_logger.info(f"✅ Session resumed successfully: {session_id}")
            else:
                self.execute_logger.info("New session initialized (ID will be received during stream)")

        except SessionResumeError as e:
            # Resume 실패 로깅 및 새 세션 시작
            self.execute_logger.warning(f"❌ Failed to resume session {session_id}: {e}")
            self.execute_logger.info("Starting new session instead")
            actual_session_id = await self.execute_agent.start_session(None)

        await self.session_store.save_session(agent_type, actual_session_id)

        await self.execute_agent.send(final_prompt)
        self.execute_logger.info("Prompt sent")

        try:
            stream = self.execute_agent.stream()
            async for message in stream:
                await self.ui.show_message(message, source="execute")
                self.execute_logger.debug(f"Message: {message.role} - {message.content[:100]}...")
        except SessionLimitError as e:
            self.execute_logger.warning(f"Session limit reached: {e}")
            await self.ui.show_status("⚠️  Session limit reached")

            if e.reset_time:
                await sleep_until_reset(e.reset_time, self.ui)
            else:
                await self.ui.show_status("Reset time unknown, waiting until next hour...")
                await sleep_until_next_hour(self.ui)

            raise

        # stream() 완료 후 실제 session_id 업데이트
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

        final_prompt = await self.prompt_resolver.resolve(prompt, extra)

        await self.verify_agent.initialize()

        agent_type = type(self.verify_agent).__name__.lower().replace("agent", "")

        self.verify_logger = self.logger_factory.create_logger(agent_type, None)
        self.verify_logger.info("Verify phase starting (new session)")

        actual_session_id = await self.verify_agent.start_session(None)
        self.verify_logger.info(f"New session started: {actual_session_id}")

        await self.verify_agent.send(final_prompt)
        self.verify_logger.info("Prompt sent")

        try:
            stream = self.verify_agent.stream()
            async for message in stream:
                await self.ui.show_message(message, source="verify")
                self.verify_logger.debug(f"Message: {message.role} - {message.content[:100]}...")

                if message.role == "assistant":
                    feedback_messages.append(message.content)

                    content_upper = message.content.upper()
                    contains_fully_done_false = (
                        "FULLY_DONE = FALSE" in content_upper or "FULLY_DONE=FALSE" in content_upper
                    )
                    contains_fully_done_true = (
                        "FULLY_DONE = TRUE" in content_upper or "FULLY_DONE=TRUE" in content_upper
                    )

                    if not contains_fully_done_false and contains_fully_done_true:
                        fully_done = True
        except SessionLimitError as e:
            self.verify_logger.warning(f"Session limit reached: {e}")
            await self.ui.show_status("⚠️  Verify session limit reached")

            if e.reset_time:
                await sleep_until_reset(e.reset_time, self.ui)
            else:
                await self.ui.show_status("Reset time unknown, waiting until next hour...")
                await sleep_until_next_hour(self.ui)

            raise

        await self.verify_agent.close()

        feedback = "\n\n".join(feedback_messages)
        self.verify_logger.info(
            f"Verify feedback collected: {len(feedback_messages)} messages, fully_done={fully_done}"
        )
        return (feedback, fully_done)
