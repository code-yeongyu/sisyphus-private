"""ExecutionLoop for two-phase agent execution (Execute + Verify)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import anyio

from sisyphus.core.prompts import DEFAULT_EXECUTE_PROMPT, DEFAULT_VERIFY_PROMPT

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
        """Run the execution loop.

        Args:
            execute_prompt: Execute phase prompt (None = use DEFAULT_EXECUTE_PROMPT)
            execute_extra: Extra prompt for execute phase
            verify_prompt: Verify phase prompt (None = use DEFAULT_VERIFY_PROMPT)
            verify_extra: Extra prompt for verify phase

        Notes:
            - Execute agent can resume previous session
            - Verify agent always starts new session (independent verification)
            - Loop continues until task_validator confirms completion (if provided)
        """
        await self.ui.initialize()

        actual_execute_prompt = execute_prompt if execute_prompt is not None else DEFAULT_EXECUTE_PROMPT

        if hasattr(self.execute_agent, "supports_interactive") and self.execute_agent.supports_interactive:
            await self._run_interactive_mode(actual_execute_prompt, execute_extra)
        else:
            await self._run_non_interactive_mode(actual_execute_prompt, execute_extra, verify_prompt, verify_extra)

        await self.ui.close()

    async def _run_interactive_mode(
        self,
        execute_prompt: str,
        execute_extra: str | None = None,
    ) -> None:
        """Interactive mode: continuously get user input and send to agent.

        Args:
            execute_prompt: 초기 실행 프롬프트
            execute_extra: 추가 실행 컨텍스트
        """
        await self.execute_agent.initialize()
        agent_type = type(self.execute_agent).__name__.lower().replace("agent", "")
        session_id = await self.session_store.get_session(agent_type)

        self.execute_logger = self.logger_factory.create_logger(agent_type, session_id)
        self.execute_logger.info("Interactive mode starting")

        actual_session_id = await self.execute_agent.start_session(session_id)
        await self.session_store.save_session(agent_type, actual_session_id)

        final_prompt = await self.prompt_resolver.resolve(execute_prompt, execute_extra)
        await self.execute_agent.send(final_prompt)

        stream = self.execute_agent.stream()
        async for message in stream:
            await self.ui.show_message(message, source="execute")

        try:
            while True:
                try:
                    user_input = await self.ui.get_input()
                    if user_input is None:
                        break
                except (anyio.ClosedResourceError, anyio.EndOfStream):
                    self.execute_logger.info("Input stream closed, exiting interactive mode")
                    break

                await self.execute_agent.send(user_input)
                stream = self.execute_agent.stream()
                async for message in stream:
                    await self.ui.show_message(message, source="execute")
        finally:
            await self.execute_agent.close()

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
        while True:
            iteration += 1

            await self.ui.show_status(f"[Iteration {iteration}] Starting Execute phase...")
            await self._execute_phase(execute_prompt, execute_extra)

            if self.verify_agent:
                actual_verify_prompt = verify_prompt if verify_prompt is not None else DEFAULT_VERIFY_PROMPT
                await self.ui.show_status(f"[Iteration {iteration}] Starting Verify phase...")
                await self._verify_phase(actual_verify_prompt, verify_extra)

            if self.task_validator is None:
                await self.ui.show_status("Execution complete (no task validator)")
                break

            content = self.task_validator.read_content()
            goals_accomplished = self.task_validator.check_all_goals_accomplished(content)
            checkboxes_completed = self.task_validator.check_all_checkboxes_completed(content)

            if goals_accomplished and checkboxes_completed:
                await self.ui.show_status("All tasks completed! Exiting loop.")
                break

            uncompleted = self.task_validator.extract_uncompleted_checkboxes(content)
            total = self.task_validator.count_total_checkboxes(content)
            completed = self.task_validator.count_completed_checkboxes(content)

            await self.ui.show_status(
                f"Progress: {completed}/{total} completed. {len(uncompleted)} tasks remaining. Continuing..."
            )

    async def _execute_phase(
        self,
        prompt: str,
        extra: str | None = None,
    ) -> None:
        """Execute phase: can resume previous session.

        Args:
            prompt: Prompt for execute agent
            extra: Extra prompt to append
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

        stream = self.execute_agent.stream()
        async for message in stream:
            await self.ui.show_message(message, source="execute")
            self.execute_logger.debug(f"Message: {message.role} - {message.content[:100]}...")

        await self.execute_agent.close()
        self.execute_logger.info("Execute phase complete")

    async def _verify_phase(
        self,
        prompt: str,
        extra: str | None = None,
    ) -> None:
        """Verify phase: always starts NEW session (independent verification).

        Args:
            prompt: Prompt for verify agent
            extra: Extra prompt to append
        """
        if self.verify_agent is None:
            return

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

        stream = self.verify_agent.stream()
        async for message in stream:
            await self.ui.show_message(message, source="verify")
            self.verify_logger.debug(f"Message: {message.role} - {message.content[:100]}...")

        await self.verify_agent.close()
        self.verify_logger.info("Verify phase complete")
