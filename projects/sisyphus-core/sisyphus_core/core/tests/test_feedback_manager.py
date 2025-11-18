"""Tests for FeedbackManager."""

from __future__ import annotations

from sisyphus_core.core.feedback_manager import FeedbackManager


def test_add_and_get_feedback() -> None:
    """Test adding feedback and retrieving history."""
    # given
    manager = FeedbackManager()

    # when
    manager.add_feedback("feedback1")
    manager.add_feedback("feedback2")

    # then
    assert manager.get_history() == ["feedback1", "feedback2"]


def test_has_history__when_empty__returns_false() -> None:
    """Test has_history returns False when empty."""
    # given
    manager = FeedbackManager()

    # when
    result = manager.has_history()

    # then
    assert result is False


def test_has_history__when_not_empty__returns_true() -> None:
    """Test has_history returns True when not empty."""
    # given
    manager = FeedbackManager()

    # when
    manager.add_feedback("some feedback")
    result = manager.has_history()

    # then
    assert result is True


def test_clear_oldest__removes_first_item() -> None:
    """Test clear_oldest removes first (oldest) item."""
    # given
    manager = FeedbackManager()
    manager.add_feedback("first")
    manager.add_feedback("second")
    manager.add_feedback("third")

    # when
    manager.clear_oldest()

    # then
    assert manager.get_history() == ["second", "third"]

    # when (clear again)
    manager.clear_oldest()

    # then
    assert manager.get_history() == ["third"]


def test_build_feedback_section_for_execute__with_history() -> None:
    """Test Execute section building with feedback."""
    # given
    manager = FeedbackManager()
    manager.add_feedback("Issue 1: Fix bug in authentication")
    manager.add_feedback("Issue 2: Add logging")
    execute_extra = "Some extra context"

    # when
    result = manager.build_feedback_section_for_execute(execute_extra)

    # then
    assert "Some extra context" in result
    assert "## 🔍 Verify Feedback from Previous Iterations" in result
    assert "<verify-feedback-history>" in result
    assert '<feedback iteration="1">' in result
    assert "Issue 1: Fix bug in authentication" in result
    assert '<feedback iteration="2">' in result
    assert "Issue 2: Add logging" in result
    assert "**CRITICAL**: Address ALL issues mentioned in the feedback history above before proceeding." in result


def test_build_feedback_section_for_execute__without_history() -> None:
    """Test Execute section when no history."""
    # given
    manager = FeedbackManager()
    execute_extra = "Some extra context"

    # when
    result = manager.build_feedback_section_for_execute(execute_extra)

    # then
    assert result == "Some extra context"
    assert "## 🔍 Verify Feedback from Previous Iterations" not in result


def test_build_feedback_section_for_verify__with_history() -> None:
    """Test Verify section building with feedback."""
    # given
    manager = FeedbackManager()
    manager.add_feedback("Review 1: Code needs refactoring")
    manager.add_feedback("Review 2: Add tests")
    verify_prompt = "Please verify the implementation"

    # when
    result = manager.build_feedback_section_for_verify(verify_prompt)

    # then
    assert "<previous_verify_reviews>" in result
    assert '<review iteration="1">' in result
    assert "Review 1: Code needs refactoring" in result
    assert '<review iteration="2">' in result
    assert "Review 2: Add tests" in result
    assert "</previous_verify_reviews>" in result
    assert "Please verify the implementation" in result
    # Verify that reviews are prepended
    assert result.index("<previous_verify_reviews>") < result.index("Please verify the implementation")


def test_build_feedback_section_for_verify__without_history() -> None:
    """Test Verify section when no history."""
    # given
    manager = FeedbackManager()
    verify_prompt = "Please verify the implementation"

    # when
    result = manager.build_feedback_section_for_verify(verify_prompt)

    # then
    assert result == verify_prompt
    assert "<previous_verify_reviews>" not in result


def test_xml_format_for_execute() -> None:
    """Verify exact XML format for Execute phase."""
    # given
    manager = FeedbackManager()
    manager.add_feedback("Fix authentication bug")
    manager.add_feedback("Add error handling")

    # when
    result = manager.build_feedback_section_for_execute(None)

    # then
    # Check header
    assert "## 🔍 Verify Feedback from Previous Iterations" in result

    # Check root tag
    assert "<verify-feedback-history>" in result
    assert "</verify-feedback-history>" in result

    # Check feedback tags with iteration numbers starting from 1
    lines = result.split("\n")
    feedback_lines = [line for line in lines if "<feedback iteration=" in line]
    assert len(feedback_lines) >= 2
    assert '<feedback iteration="1">' in result
    assert '<feedback iteration="2">' in result

    # Check critical message
    critical_msg = "**CRITICAL**: Address ALL issues mentioned in the feedback history above before proceeding."
    assert critical_msg in result

    # Verify structure
    root_start = result.index("<verify-feedback-history>")
    root_end = result.index("</verify-feedback-history>")
    assert root_start < root_end


def test_xml_format_for_verify() -> None:
    """Verify exact XML format for Verify phase."""
    # given
    manager = FeedbackManager()
    manager.add_feedback("Needs refactoring")
    manager.add_feedback("Missing unit tests")
    verify_prompt = "Original verify prompt content"

    # when
    result = manager.build_feedback_section_for_verify(verify_prompt)

    # then
    # Check root tag
    assert "<previous_verify_reviews>" in result
    assert "</previous_verify_reviews>" in result

    # Check review tags with iteration numbers starting from 1
    assert '<review iteration="1">' in result
    assert '<review iteration="2">' in result

    # Verify structure: reviews prepended before prompt
    reviews_start = result.index("<previous_verify_reviews>")
    prompt_start = result.index("Original verify prompt content")
    reviews_end = result.index("</previous_verify_reviews>")

    assert reviews_start < reviews_end < prompt_start

    # Verify content is inside review tags
    assert "Needs refactoring" in result
    assert "Missing unit tests" in result
