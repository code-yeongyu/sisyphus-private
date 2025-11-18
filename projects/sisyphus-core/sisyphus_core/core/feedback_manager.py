"""Feedback history management for ExecutionLoop."""

from __future__ import annotations


class FeedbackManager:
    """Manages verify feedback history with XML formatting.

    Responsibilities:
    - Store feedback messages from Verify phases
    - Format feedback for Execute phase (XML with iteration numbers)
    - Format feedback for Verify phase (prepend previous reviews)
    - Remove oldest feedback when prompt becomes too long
    """

    def __init__(self) -> None:
        """Initialize FeedbackManager with empty history."""
        self.verify_feedback_history: list[str] = []

    def add_feedback(self, feedback: str) -> None:
        """Add feedback to history.

        Args:
            feedback: Feedback message to add
        """
        self.verify_feedback_history.append(feedback)

    def get_history(self) -> list[str]:
        """Get the feedback history list.

        Returns:
            List of feedback messages
        """
        return self.verify_feedback_history

    def has_history(self) -> bool:
        """Check if history is not empty.

        Returns:
            True if history has items, False otherwise
        """
        return len(self.verify_feedback_history) > 0

    def clear_oldest(self) -> None:
        """Remove the first (oldest) item from history.

        Used when PromptTooLongError occurs to reduce prompt length.
        """
        if self.verify_feedback_history:
            self.verify_feedback_history.pop(0)

    def build_feedback_section_for_execute(self, execute_extra: str | None) -> str:
        """Build Execute phase prompt with feedback XML.

        Format:
        {execute_extra if exists}

        ## 🔍 Verify Feedback from Previous Iterations

        <verify-feedback-history>
        <feedback iteration="1">
        {feedback1}
        </feedback>

        <feedback iteration="2">
        {feedback2}
        </feedback>
        </verify-feedback-history>

        **CRITICAL**: Address ALL issues mentioned in the feedback history above before proceeding.

        Args:
            execute_extra: Extra execute prompt content (or None)

        Returns:
            Complete execute prompt with feedback section, or original execute_extra if no history
        """
        if not self.has_history():
            return execute_extra or ""

        feedback_section = "\n\n## 🔍 Verify Feedback from Previous Iterations\n\n<verify-feedback-history>\n"

        for i, feedback in enumerate(self.verify_feedback_history, 1):
            feedback_section += f'<feedback iteration="{i}">\n{feedback}\n</feedback>\n\n'

        feedback_section += "</verify-feedback-history>\n\n"
        msg_line1 = "**CRITICAL**: Address ALL issues mentioned in the "
        msg_line2 = "feedback history above before proceeding.\n"
        feedback_section += msg_line1 + msg_line2

        return (execute_extra or "") + feedback_section

    def build_feedback_section_for_verify(self, verify_prompt: str) -> str:
        """Build Verify phase prompt with feedback XML prepended.

        Format:
        <previous_verify_reviews>
        <review iteration="1">
        {feedback1}
        </review>

        <review iteration="2">
        {feedback2}
        </review>
        </previous_verify_reviews>

        {verify_prompt}

        Args:
            verify_prompt: Original verify prompt

        Returns:
            Verify prompt with previous reviews prepended, or original prompt if no history
        """
        if not self.has_history():
            return verify_prompt

        reviews_section = "<previous_verify_reviews>\n"

        for i, feedback in enumerate(self.verify_feedback_history, 1):
            reviews_section += f'<review iteration="{i}">\n{feedback}\n</review>\n\n'

        reviews_section += "</previous_verify_reviews>\n\n"

        return reviews_section + verify_prompt
