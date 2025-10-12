"""ExecutionLoop for two-phase agent execution (Execute + Verify)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import anyio

from sisyphus.core.prompts import DEFAULT_EXECUTE_PROMPT, DEFAULT_VERIFY_PROMPT
from sisyphus.utils.errors import SessionLimitError
from sisyphus.utils.session_limit import sleep_until_reset

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
        """
        await self.ui.initialize()

        actual_execute_prompt = execute_prompt if execute_prompt is not None else DEFAULT_EXECUTE_PROMPT

        await self._run_unified_mode(actual_execute_prompt, execute_extra, verify_prompt, verify_extra)

        await self.ui.close()

    async def _run_interactive_mode(
        self,
        execute_prompt: str,
        execute_extra: str | None = None,
    ) -> None:
        """Interactive mode: continuously get user input and send to agent in parallel.

        사용자가 Enter를 누르는 순간 즉시 Agent에 전송됩니다.
        Agent 응답과 사용자 입력을 병렬로 처리합니다.

        Args:
            execute_prompt: 초기 실행 프롬프트
            execute_extra: 추가 실행 컨텍스트
        """
        await self.execute_agent.initialize()
        agent_type = type(self.execute_agent).__name__.lower().replace("agent", "")
        session_id = await self.session_store.get_session(agent_type)

        self.execute_logger = self.logger_factory.create_logger(agent_type, session_id)
        self.execute_logger.info("Interactive mode starting (parallel input/output)")

        actual_session_id = await self.execute_agent.start_session(session_id)
        await self.session_store.save_session(agent_type, actual_session_id)

        final_prompt = await self.prompt_resolver.resolve(execute_prompt, execute_extra)
        await self.execute_agent.send(final_prompt)

        try:
            async with anyio.create_task_group() as tg:

                async def receive_loop() -> None:
                    """Agent 응답을 계속 수신하는 루프."""
                    try:
                        while True:
                            stream = self.execute_agent.stream()
                            async for message in stream:
                                await self.ui.show_message(message, source="execute")
                    except Exception as e:
                        if self.execute_logger:
                            self.execute_logger.error(f"Receive loop error: {e}")
                        tg.cancel_scope.cancel()

                async def input_loop() -> None:
                    """사용자 입력을 계속 받아서 즉시 전송하는 루프."""
                    try:
                        while True:
                            try:
                                user_input = await self.ui.get_input()
                                if user_input is None:
                                    if self.execute_logger:
                                        self.execute_logger.info("User requested exit")
                                    tg.cancel_scope.cancel()
                                    break
                                await self.execute_agent.send(user_input)
                            except (anyio.ClosedResourceError, anyio.EndOfStream):
                                if self.execute_logger:
                                    self.execute_logger.info("Input stream closed, exiting interactive mode")
                                tg.cancel_scope.cancel()
                                break
                    except Exception as e:
                        if self.execute_logger:
                            self.execute_logger.error(f"Input loop error: {e}")
                        tg.cancel_scope.cancel()

                tg.start_soon(receive_loop)
                tg.start_soon(input_loop)
        finally:
            await self.execute_agent.close()

    async def _run_unified_mode(
        self,
        execute_prompt: str,
        execute_extra: str | None = None,
        verify_prompt: str | None = None,
        verify_extra: str | None = None,
    ) -> None:
        """Unified mode: Execute -> Task Validator -> Verify phases in one flow.

        This mode combines the logic from interactive and non-interactive modes:
        - Execute Phase uses agent.stream() which naturally handles interactive agents
        - Task Validator checks completion after Execute (if provided)
        - Verify Phase runs after Task completion (if verify_agent provided)
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

            # 피드백 히스토리를 execute_extra에 주입
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

            # Task Validator 체크 (있는 경우에만)
            if self.task_validator is not None:
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
                    continue

            # Verify phase (verify_agent가 있는 경우)
            if self.verify_agent:
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

                    if fully_done:
                        await self.ui.show_status("✅ Architect confirmed FULLY_DONE. All work verified!")
                        break

                    if self.task_validator is None:
                        await self.ui.show_status("Verification complete (no task validator for feedback loop).")
                        break

                    verify_feedback_history.append(feedback)
                    await self.ui.show_status(f"[Iteration {iteration}] Verify feedback received. Continuing...")
                    continue
                except SessionLimitError:
                    await self.ui.show_status(f"[Iteration {iteration}] Verify session limit handled, retrying...")
                    continue

            await self.ui.show_status("All tasks completed! Exiting loop.")
            break

    async def _run_non_interactive_mode(
        self,
        execute_prompt: str,
        execute_extra: str | None = None,
        verify_prompt: str | None = None,
        verify_extra: str | None = None,
    ) -> None:
        """Non-interactive mode: existing behavior (initial prompt only).

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

            # 피드백 히스토리를 execute_extra에 주입
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

            # Task Validator 체크 (있는 경우에만)
            if self.task_validator is not None:
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

            # Verify phase (verify_agent가 있는 경우)
            if self.verify_agent:
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

                    if fully_done:
                        await self.ui.show_status("✅ Architect confirmed FULLY_DONE. All work verified!")
                        break

                    if self.task_validator is None:
                        await self.ui.show_status("Verification complete (no task validator for feedback loop).")
                        break

                    verify_feedback_history.append(feedback)
                    await self.ui.show_status(f"[Iteration {iteration}] Verify feedback received. Continuing...")
                    continue
                except SessionLimitError:
                    await self.ui.show_status(f"[Iteration {iteration}] Verify session limit handled, retrying...")
                    continue

            await self.ui.show_status("All tasks completed! Exiting loop.")
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

        actual_session_id = await self.execute_agent.start_session(session_id)
        self.execute_logger.info(f"Session started: {actual_session_id}")

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
                await self.ui.show_status("Reset time unknown, waiting 1 hour...")
                await anyio.sleep(3600)

            raise

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

        await self.session_store.save_session(agent_type, actual_session_id)

        await self.verify_agent.send(final_prompt)
        self.verify_logger.info("Prompt sent")

        try:
            stream = self.verify_agent.stream()
            async for message in stream:
                await self.ui.show_message(message, source="verify")
                self.verify_logger.debug(f"Message: {message.role} - {message.content[:100]}...")

                if message.role == "assistant":
                    feedback_messages.append(message.content)
                    if "FULLY_DONE = TRUE" in message.content.upper():
                        fully_done = True
        except SessionLimitError as e:
            self.verify_logger.warning(f"Session limit reached: {e}")
            await self.ui.show_status("⚠️  Verify session limit reached")

            if e.reset_time:
                await sleep_until_reset(e.reset_time, self.ui)
            else:
                await self.ui.show_status("Reset time unknown, waiting 1 hour...")
                await anyio.sleep(3600)

            raise

        await self.verify_agent.close()

        feedback = "\n\n".join(feedback_messages)
        self.verify_logger.info(
            f"Verify feedback collected: {len(feedback_messages)} messages, fully_done={fully_done}"
        )
        return (feedback, fully_done)
