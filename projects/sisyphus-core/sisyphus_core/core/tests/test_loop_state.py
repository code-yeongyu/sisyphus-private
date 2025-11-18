"""Tests for LoopState."""

from __future__ import annotations

from sisyphus_core.core.loop_state import LoopState


def test_increment_and_reset_consecutive_execute() -> None:
    """Test increment, decrement, reset of consecutive execute count."""
    # given
    state = LoopState()

    # when
    state.increment_consecutive_execute()
    state.increment_consecutive_execute()

    # then
    assert state._consecutive_execute_count == 2

    # when
    state.decrement_consecutive_execute()

    # then
    assert state._consecutive_execute_count == 1

    # when
    state.reset_consecutive_execute()

    # then
    assert state._consecutive_execute_count == 0


def test_check_force_verify__when_count_below_10__returns_false() -> None:
    """Test check_force_verify returns False when count < 10."""
    # given
    state = LoopState()

    # when
    for _ in range(9):
        state.increment_consecutive_execute()

    # then
    assert state.check_force_verify() is False


def test_check_force_verify__when_count_equals_10__returns_true() -> None:
    """Test check_force_verify returns True when count >= 10."""
    # given
    state = LoopState()

    # when
    for _ in range(10):
        state.increment_consecutive_execute()

    # then
    assert state.check_force_verify() is True


def test_increment_execute_resume_fail__when_below_3__returns_true() -> None:
    """Test check_should_retry_resume returns True when count < 3."""
    # given
    state = LoopState()

    # when
    for _ in range(2):
        state.increment_execute_resume_fail()

    # then
    assert state.check_should_retry_resume() is True


def test_increment_execute_resume_fail__when_equals_3__returns_false() -> None:
    """Test check_should_retry_resume returns False when count >= 3."""
    # given
    state = LoopState()

    # when
    for _ in range(3):
        state.increment_execute_resume_fail()

    # then
    assert state.check_should_retry_resume() is False


def test_sdk_exception_increment_and_limit() -> None:
    """Test SDK exception count increment, reset, and limit check."""
    # given
    state = LoopState()

    # when
    state.increment_sdk_exception()
    state.increment_sdk_exception()

    # then
    assert state._sdk_exception_count == 2
    assert state.check_sdk_exception_limit() is False

    # when
    state.increment_sdk_exception()

    # then
    assert state._sdk_exception_count == 3
    assert state.check_sdk_exception_limit() is True

    # when
    state.reset_sdk_exception()

    # then
    assert state._sdk_exception_count == 0
    assert state.check_sdk_exception_limit() is False


def test_interrupt_flag_set_and_check() -> None:
    """Test interrupt flag set/get."""
    # given
    state = LoopState()

    # when
    state.set_interrupt_flag(True)

    # then
    assert state.is_interrupted() is True

    # when
    state.set_interrupt_flag(False)

    # then
    assert state.is_interrupted() is False


def test_plan_id_set_and_get() -> None:
    """Test plan ID set/get."""
    # given
    state = LoopState()
    test_plan_id = "test-plan-123"

    # when
    state.set_plan_id(test_plan_id)

    # then
    assert state.get_plan_id() == test_plan_id

    # when
    state.set_plan_id("another-plan")

    # then
    assert state.get_plan_id() == "another-plan"


def test_acceptance_criteria_retry_message() -> None:
    """Test AC retry message set/get."""
    # given
    state = LoopState()
    test_message = "Please fix the following issues"

    # when
    state.set_acceptance_criteria_retry_message(test_message)

    # then
    assert state.get_acceptance_criteria_retry_message() == test_message

    # when
    state.set_acceptance_criteria_retry_message(None)

    # then
    assert state.get_acceptance_criteria_retry_message() is None
