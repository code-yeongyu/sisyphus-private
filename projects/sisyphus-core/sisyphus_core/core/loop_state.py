"""State management for ExecutionLoop (counters and flags)."""

from __future__ import annotations


class LoopState:
    """Manages counters and flags for the ExecutionLoop.

    Responsibilities:
    - Track iteration count
    - Monitor consecutive Execute phase executions
    - Manage Execute session resume failures
    - Count SDK exceptions
    - Maintain force exit and interrupt flags
    - Store current plan ID and acceptance criteria retry message
    """

    def __init__(self) -> None:
        """Initialize LoopState with all counters and flags."""
        # Counters
        self.iteration: int = 0
        self._consecutive_execute_count: int = 0
        self._execute_resume_fail_count: int = 0
        self._sdk_exception_count: int = 0

        # Flags
        self._should_exit_execute_phase: bool = False
        self._interrupt_flag: bool = False
        self._resumed_once: bool = False

        # State storage
        self._current_plan_id: str = ""
        self._acceptance_criteria_retry_message: str | None = None

    # Iteration management
    def increment_iteration(self) -> None:
        """Increment iteration counter."""
        self.iteration += 1

    # Consecutive execute count management
    def increment_consecutive_execute(self) -> None:
        """Increment consecutive execute count."""
        self._consecutive_execute_count += 1

    def decrement_consecutive_execute(self) -> None:
        """Decrement consecutive execute count."""
        if self._consecutive_execute_count > 0:
            self._consecutive_execute_count -= 1

    def reset_consecutive_execute(self) -> None:
        """Reset consecutive execute count to 0."""
        self._consecutive_execute_count = 0

    def check_force_verify(self) -> bool:
        """Check if consecutive execute count >= 10 (force verify condition).

        Returns:
            True if count >= 10, False otherwise
        """
        return self._consecutive_execute_count >= 10

    # Execute resume fail count management
    def increment_execute_resume_fail(self) -> None:
        """Increment execute resume fail count."""
        self._execute_resume_fail_count += 1

    def reset_execute_resume_fail(self) -> None:
        """Reset execute resume fail count to 0."""
        self._execute_resume_fail_count = 0

    def check_should_retry_resume(self) -> bool:
        """Check if should retry resume (fail count < 3).

        Returns:
            True if count < 3 (should retry), False otherwise
        """
        return self._execute_resume_fail_count < 3

    # SDK exception count management
    def increment_sdk_exception(self) -> None:
        """Increment SDK exception count."""
        self._sdk_exception_count += 1

    def reset_sdk_exception(self) -> None:
        """Reset SDK exception count to 0."""
        self._sdk_exception_count = 0

    def check_sdk_exception_limit(self) -> bool:
        """Check if SDK exception count >= 3 (limit exceeded).

        Returns:
            True if count >= 3, False otherwise
        """
        return self._sdk_exception_count >= 3

    # Should exit execute phase management
    def set_should_exit_execute_phase(self, value: bool) -> None:
        """Set should exit execute phase flag.

        Args:
            value: Flag value to set
        """
        self._should_exit_execute_phase = value

    def should_exit_execute_phase(self) -> bool:
        """Get should exit execute phase flag.

        Returns:
            Current flag value
        """
        return self._should_exit_execute_phase

    # Interrupt flag management
    def set_interrupt_flag(self, value: bool) -> None:
        """Set interrupt flag.

        Args:
            value: Flag value to set
        """
        self._interrupt_flag = value

    def is_interrupted(self) -> bool:
        """Check if interrupted.

        Returns:
            Current interrupt flag value
        """
        return self._interrupt_flag

    # Resumed once management
    def set_resumed_once(self, value: bool) -> None:
        """Set resumed once flag.

        Args:
            value: Flag value to set
        """
        self._resumed_once = value

    def was_resumed_once(self) -> bool:
        """Check if was resumed once.

        Returns:
            Current resumed once flag value
        """
        return self._resumed_once

    # Plan ID management
    def set_plan_id(self, plan_id: str) -> None:
        """Set current plan ID.

        Args:
            plan_id: Plan ID to set
        """
        self._current_plan_id = plan_id

    def get_plan_id(self) -> str:
        """Get current plan ID.

        Returns:
            Current plan ID
        """
        return self._current_plan_id

    # Acceptance criteria retry message management
    def set_acceptance_criteria_retry_message(self, msg: str | None) -> None:
        """Set acceptance criteria retry message.

        Args:
            msg: Retry message or None
        """
        self._acceptance_criteria_retry_message = msg

    def get_acceptance_criteria_retry_message(self) -> str | None:
        """Get acceptance criteria retry message.

        Returns:
            Retry message or None
        """
        return self._acceptance_criteria_retry_message
