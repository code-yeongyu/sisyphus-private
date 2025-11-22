"""Test acceptance_criteria minimum validation in PlanLinter.

Tests validate that:
1. todos[].acceptance_criteria must have at least 2 items
2. acceptance_criteria_for_verification_agent must have at least 2 items
"""

from __future__ import annotations

from sisyphus_core.core.plan_linter import PlanLinter


class TestTodosAcceptanceCriteriaMinimum:
    """Test todos[].acceptance_criteria minimum validation."""

    def test_todos_acceptance_criteria_with_two_items_passes(self) -> None:
        """Given: todo with acceptance_criteria containing 2 items.
        When: lint is called.
        Then: no errors related to acceptance_criteria
        """
        # Given
        yaml_data = {
            "version": "3.0",
            "metadata": {
                "created_at": "2025-11-21T00:00:00Z",
            },
            "work_plans": [
                {
                    "id": "plan1",
                    "name": "Test Plan",
                    "objectives": {"core": "Test", "detailed": []},
                    "todos": [
                        {
                            "id": "1",
                            "title": "Task 1",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Condition 1"},
                                {"id": "c2", "condition": "Condition 2"},
                            ],
                        }
                    ],
                    "acceptance_criteria_for_verification_agent": [
                        {"id": "a1", "title": "Check 1"},
                        {"id": "a2", "title": "Check 2"},
                        {"id": "a3", "title": "Check 3"},
                        {"id": "a4", "title": "Check 4"},
                    ],
                }
            ],
        }
        linter = PlanLinter({})

        # When
        errors = linter.lint(yaml_data)

        # Then
        acceptance_criteria_errors = [e for e in errors if "acceptance_criteria" in e.location]
        assert len(acceptance_criteria_errors) == 0

    def test_todos_acceptance_criteria_with_one_item_fails(self) -> None:
        """Given: todo with acceptance_criteria containing 1 item.
        When: lint is called.
        Then: lint error about minimum 2 items
        """
        # Given
        yaml_data = {
            "version": "3.0",
            "metadata": {
                "created_at": "2025-11-21T00:00:00Z",
            },
            "work_plans": [
                {
                    "id": "plan1",
                    "name": "Test Plan",
                    "objectives": {"core": "Test", "detailed": []},
                    "todos": [
                        {
                            "id": "1",
                            "title": "Task 1",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Condition 1"},
                            ],
                        }
                    ],
                    "acceptance_criteria_for_verification_agent": [
                        {"id": "a1", "title": "Check 1"},
                        {"id": "a2", "title": "Check 2"},
                        {"id": "a3", "title": "Check 3"},
                        {"id": "a4", "title": "Check 4"},
                    ],
                }
            ],
        }
        linter = PlanLinter({})

        # When
        errors = linter.lint(yaml_data)

        # Then
        acceptance_criteria_errors = [
            e for e in errors if "todos[0].acceptance_criteria" in e.location and "at least 2 items" in e.message
        ]
        assert len(acceptance_criteria_errors) == 1
        error = acceptance_criteria_errors[0]
        assert error.expected == "at least 2 items"
        assert error.actual == "1 item(s)"
        assert error.category == "validation"

    def test_todos_acceptance_criteria_empty_fails(self) -> None:
        """Given: todo with acceptance_criteria as empty list.
        When: lint is called.
        Then: lint error about minimum 2 items
        """
        # Given
        yaml_data = {
            "version": "3.0",
            "metadata": {
                "created_at": "2025-11-21T00:00:00Z",
            },
            "work_plans": [
                {
                    "id": "plan1",
                    "name": "Test Plan",
                    "objectives": {"core": "Test", "detailed": []},
                    "todos": [
                        {
                            "id": "1",
                            "title": "Task 1",
                            "status": "pending",
                            "acceptance_criteria": [],
                        }
                    ],
                    "acceptance_criteria_for_verification_agent": [
                        {"id": "a1", "title": "Check 1"},
                        {"id": "a2", "title": "Check 2"},
                        {"id": "a3", "title": "Check 3"},
                        {"id": "a4", "title": "Check 4"},
                    ],
                }
            ],
        }
        linter = PlanLinter({})

        # When
        errors = linter.lint(yaml_data)

        # Then
        acceptance_criteria_errors = [
            e for e in errors if "todos[0].acceptance_criteria" in e.location and "at least 2 items" in e.message
        ]
        assert len(acceptance_criteria_errors) == 1
        error = acceptance_criteria_errors[0]
        assert error.expected == "at least 2 items"
        assert error.actual == "0 item(s)"
        assert error.category == "validation"

    def test_todos_acceptance_criteria_with_three_items_passes(self) -> None:
        """Given: todo with acceptance_criteria containing 3 items.
        When: lint is called.
        Then: no errors related to acceptance_criteria
        """
        # Given
        yaml_data = {
            "version": "3.0",
            "metadata": {
                "created_at": "2025-11-21T00:00:00Z",
            },
            "work_plans": [
                {
                    "id": "plan1",
                    "name": "Test Plan",
                    "objectives": {"core": "Test", "detailed": []},
                    "todos": [
                        {
                            "id": "1",
                            "title": "Task 1",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Condition 1"},
                                {"id": "c2", "condition": "Condition 2"},
                                {"id": "c3", "condition": "Condition 3"},
                            ],
                        }
                    ],
                    "acceptance_criteria_for_verification_agent": [
                        {"id": "a1", "title": "Check 1"},
                        {"id": "a2", "title": "Check 2"},
                        {"id": "a3", "title": "Check 3"},
                        {"id": "a4", "title": "Check 4"},
                    ],
                }
            ],
        }
        linter = PlanLinter({})

        # When
        errors = linter.lint(yaml_data)

        # Then
        acceptance_criteria_errors = [e for e in errors if "todos[0].acceptance_criteria" in e.location]
        assert len(acceptance_criteria_errors) == 0

    def test_multiple_todos_with_one_failing(self) -> None:
        """Given: multiple todos where one has insufficient acceptance_criteria.
        When: lint is called.
        Then: error only for the failing todo
        """
        # Given
        yaml_data = {
            "version": "3.0",
            "metadata": {
                "created_at": "2025-11-21T00:00:00Z",
            },
            "work_plans": [
                {
                    "id": "plan1",
                    "name": "Test Plan",
                    "objectives": {"core": "Test", "detailed": []},
                    "todos": [
                        {
                            "id": "1",
                            "title": "Task 1",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Condition 1"},
                                {"id": "c2", "condition": "Condition 2"},
                            ],
                        },
                        {
                            "id": "2",
                            "title": "Task 2",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Only one condition"},
                            ],
                        },
                        {
                            "id": "3",
                            "title": "Task 3",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Condition 1"},
                                {"id": "c2", "condition": "Condition 2"},
                            ],
                        },
                    ],
                    "acceptance_criteria_for_verification_agent": [
                        {"id": "a1", "title": "Check 1"},
                        {"id": "a2", "title": "Check 2"},
                        {"id": "a3", "title": "Check 3"},
                        {"id": "a4", "title": "Check 4"},
                    ],
                }
            ],
        }
        linter = PlanLinter({})

        # When
        errors = linter.lint(yaml_data)

        # Then
        acceptance_criteria_errors = [
            e for e in errors if "acceptance_criteria" in e.location and "at least 2 items" in e.message
        ]
        assert len(acceptance_criteria_errors) == 1
        assert "todos[1].acceptance_criteria" in acceptance_criteria_errors[0].location


class TestAcceptanceCriteriaForVerificationAgent:
    """Test acceptance_criteria_for_verification_agent minimum validation."""

    def test_verification_agent_criteria_with_two_items_fails(self) -> None:
        """Given: acceptance_criteria_for_verification_agent with 2 items.
        When: lint is called.
        Then: lint error about at least 4 items (expected: "at least 4 items", actual: "2 item(s)").
        """
        # Given
        yaml_data = {
            "version": "3.0",
            "metadata": {
                "created_at": "2025-11-21T00:00:00Z",
            },
            "work_plans": [
                {
                    "id": "plan1",
                    "name": "Test Plan",
                    "objectives": {"core": "Test", "detailed": []},
                    "todos": [
                        {
                            "id": "1",
                            "title": "Task 1",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Condition 1"},
                                {"id": "c2", "condition": "Condition 2"},
                            ],
                        }
                    ],
                    "acceptance_criteria_for_verification_agent": [
                        {"id": "a1", "title": "Check 1"},
                        {"id": "a2", "title": "Check 2"},
                    ],
                }
            ],
        }
        linter = PlanLinter({})

        # When
        errors = linter.lint(yaml_data)

        # Then
        verification_errors = [
            e
            for e in errors
            if "acceptance_criteria_for_verification_agent" in e.location and "at least 4 items" in e.message
        ]
        assert len(verification_errors) == 1
        error = verification_errors[0]
        assert error.expected == "at least 4 items"
        assert error.actual == "2 item(s)"
        assert error.category == "validation"

    def test_verification_agent_criteria_with_one_item_fails(self) -> None:
        """Given: acceptance_criteria_for_verification_agent with 1 item.
        When: lint is called.
        Then: lint error about minimum 4 items
        """
        # Given
        yaml_data = {
            "version": "3.0",
            "metadata": {
                "created_at": "2025-11-21T00:00:00Z",
            },
            "work_plans": [
                {
                    "id": "plan1",
                    "name": "Test Plan",
                    "objectives": {"core": "Test", "detailed": []},
                    "todos": [
                        {
                            "id": "1",
                            "title": "Task 1",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Condition 1"},
                                {"id": "c2", "condition": "Condition 2"},
                            ],
                        }
                    ],
                    "acceptance_criteria_for_verification_agent": [
                        {"id": "a1", "title": "Check 1"},
                    ],
                }
            ],
        }
        linter = PlanLinter({})

        # When
        errors = linter.lint(yaml_data)

        # Then
        verification_errors = [
            e
            for e in errors
            if "acceptance_criteria_for_verification_agent" in e.location and "at least 4 items" in e.message
        ]
        assert len(verification_errors) == 1
        error = verification_errors[0]
        assert error.expected == "at least 4 items"
        assert error.actual == "1 item(s)"
        assert error.category == "validation"

    def test_verification_agent_criteria_empty_fails(self) -> None:
        """Given: acceptance_criteria_for_verification_agent as empty list.
        When: lint is called.
        Then: lint error about minimum 4 items
        """
        # Given
        yaml_data = {
            "version": "3.0",
            "metadata": {
                "created_at": "2025-11-21T00:00:00Z",
            },
            "work_plans": [
                {
                    "id": "plan1",
                    "name": "Test Plan",
                    "objectives": {"core": "Test", "detailed": []},
                    "todos": [
                        {
                            "id": "1",
                            "title": "Task 1",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Condition 1"},
                                {"id": "c2", "condition": "Condition 2"},
                            ],
                        }
                    ],
                    "acceptance_criteria_for_verification_agent": [],
                }
            ],
        }
        linter = PlanLinter({})

        # When
        errors = linter.lint(yaml_data)

        # Then
        verification_errors = [
            e
            for e in errors
            if "acceptance_criteria_for_verification_agent" in e.location and "at least 4 items" in e.message
        ]
        assert len(verification_errors) == 1
        error = verification_errors[0]
        assert error.expected == "at least 4 items"
        assert error.actual == "0 item(s)"
        assert error.category == "validation"

    def test_verification_agent_criteria_with_three_items_fails(self) -> None:
        """Given: acceptance_criteria_for_verification_agent with 3 items.
        When: lint is called.
        Then: lint error about at least 4 items (expected: "at least 4 items", actual: "3 item(s)").
        """
        # Given
        yaml_data = {
            "version": "3.0",
            "metadata": {
                "created_at": "2025-11-21T00:00:00Z",
            },
            "work_plans": [
                {
                    "id": "plan1",
                    "name": "Test Plan",
                    "objectives": {"core": "Test", "detailed": []},
                    "todos": [
                        {
                            "id": "1",
                            "title": "Task 1",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Condition 1"},
                                {"id": "c2", "condition": "Condition 2"},
                            ],
                        }
                    ],
                    "acceptance_criteria_for_verification_agent": [
                        {"id": "a1", "title": "Check 1"},
                        {"id": "a2", "title": "Check 2"},
                        {"id": "a3", "title": "Check 3"},
                    ],
                }
            ],
        }
        linter = PlanLinter({})

        # When
        errors = linter.lint(yaml_data)

        # Then
        verification_errors = [
            e
            for e in errors
            if "acceptance_criteria_for_verification_agent" in e.location and "at least 4 items" in e.message
        ]
        assert len(verification_errors) == 1
        error = verification_errors[0]
        assert error.expected == "at least 4 items"
        assert error.actual == "3 item(s)"
        assert error.category == "validation"


class TestAcceptanceCriteriaBothValidation:
    """Test both todos[].acceptance_criteria and acceptance_criteria_for_verification_agent together."""

    def test_both_criteria_insufficient_reports_two_errors(self) -> None:
        """Given: both todos[].acceptance_criteria and acceptance_criteria_for_verification_agent insufficient.
        When: lint is called.
        Then: two separate errors reported
        """
        # Given
        yaml_data = {
            "version": "3.0",
            "metadata": {
                "created_at": "2025-11-21T00:00:00Z",
            },
            "work_plans": [
                {
                    "id": "plan1",
                    "name": "Test Plan",
                    "objectives": {"core": "Test", "detailed": []},
                    "todos": [
                        {
                            "id": "1",
                            "title": "Task 1",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Only one"},
                            ],
                        }
                    ],
                    "acceptance_criteria_for_verification_agent": [
                        {"id": "a1", "title": "Only one"},
                    ],
                }
            ],
        }
        linter = PlanLinter({})

        # When
        errors = linter.lint(yaml_data)

        # Then
        acceptance_criteria_errors = [
            e
            for e in errors
            if "acceptance_criteria" in e.location
            and ("at least 2 items" in e.message or "at least 4 items" in e.message)
        ]
        assert len(acceptance_criteria_errors) == 2
        locations = {e.location for e in acceptance_criteria_errors}
        assert "work_plans[0].todos[0].acceptance_criteria" in locations
        assert "work_plans[0].acceptance_criteria_for_verification_agent" in locations

    def test_both_criteria_sufficient_passes(self) -> None:
        """Given: both todos[].acceptance_criteria and acceptance_criteria_for_verification_agent sufficient.
        When: lint is called.
        Then: no acceptance_criteria errors
        """
        # Given
        yaml_data = {
            "version": "3.0",
            "metadata": {
                "created_at": "2025-11-21T00:00:00Z",
            },
            "work_plans": [
                {
                    "id": "plan1",
                    "name": "Test Plan",
                    "objectives": {"core": "Test", "detailed": []},
                    "todos": [
                        {
                            "id": "1",
                            "title": "Task 1",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Condition 1"},
                                {"id": "c2", "condition": "Condition 2"},
                            ],
                        },
                        {
                            "id": "2",
                            "title": "Task 2",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Condition 1"},
                                {"id": "c2", "condition": "Condition 2"},
                            ],
                        },
                    ],
                    "acceptance_criteria_for_verification_agent": [
                        {"id": "a1", "title": "Check 1"},
                        {"id": "a2", "title": "Check 2"},
                        {"id": "a3", "title": "Check 3"},
                        {"id": "a4", "title": "Check 4"},
                    ],
                }
            ],
        }
        linter = PlanLinter({})

        # When
        errors = linter.lint(yaml_data)

        # Then
        acceptance_criteria_errors = [
            e
            for e in errors
            if "acceptance_criteria" in e.location
            and ("at least 2 items" in e.message or "at least 4 items" in e.message)
        ]
        assert len(acceptance_criteria_errors) == 0


class TestRequiredField:
    """Test acceptance_criteria_for_verification_agent required field validation."""

    def test_verification_agent_criteria_missing_required_field(self) -> None:
        """Given: work plan without acceptance_criteria_for_verification_agent field.
        When: lint is called.
        Then: lint error about missing required field.
        """
        # Given
        yaml_data = {
            "version": "3.0",
            "metadata": {
                "created_at": "2025-11-21T00:00:00Z",
            },
            "work_plans": [
                {
                    "id": "plan1",
                    "name": "Test Plan",
                    "objectives": {"core": "Test", "detailed": []},
                    "todos": [
                        {
                            "id": "1",
                            "title": "Task 1",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Condition 1"},
                                {"id": "c2", "condition": "Condition 2"},
                            ],
                        }
                    ],
                    # acceptance_criteria_for_verification_agent field is missing
                }
            ],
        }
        linter = PlanLinter({})

        # When
        errors = linter.lint(yaml_data)

        # Then
        missing_field_errors = [
            e
            for e in errors
            if "acceptance_criteria_for_verification_agent" in e.location and "Missing required field" in e.message
        ]
        assert len(missing_field_errors) == 1
        error = missing_field_errors[0]
        assert error.message == "Missing required field"
        assert error.expected == "field must exist"
        assert error.category == "schema"


class TestMinimumFourItems:
    """Test acceptance_criteria_for_verification_agent minimum 4 items validation."""

    def test_verification_agent_criteria_with_three_items_fails(self) -> None:
        """Given: acceptance_criteria_for_verification_agent with 3 items.
        When: lint is called.
        Then: lint error about at least 4 items (expected: "at least 4 items", actual: "3 item(s)").
        """
        # Given
        yaml_data = {
            "version": "3.0",
            "metadata": {
                "created_at": "2025-11-21T00:00:00Z",
            },
            "work_plans": [
                {
                    "id": "plan1",
                    "name": "Test Plan",
                    "objectives": {"core": "Test", "detailed": []},
                    "todos": [
                        {
                            "id": "1",
                            "title": "Task 1",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Condition 1"},
                                {"id": "c2", "condition": "Condition 2"},
                            ],
                        }
                    ],
                    "acceptance_criteria_for_verification_agent": [
                        {"id": "a1", "title": "Check 1"},
                        {"id": "a2", "title": "Check 2"},
                        {"id": "a3", "title": "Check 3"},
                    ],
                }
            ],
        }
        linter = PlanLinter({})

        # When
        errors = linter.lint(yaml_data)

        # Then
        verification_errors = [
            e
            for e in errors
            if "acceptance_criteria_for_verification_agent" in e.location and "at least 4 items" in e.message
        ]
        assert len(verification_errors) == 1
        error = verification_errors[0]
        assert error.expected == "at least 4 items"
        assert error.actual == "3 item(s)"
        assert error.category == "validation"

    def test_verification_agent_criteria_with_four_items_passes(self) -> None:
        """Given: acceptance_criteria_for_verification_agent with 4 items.
        When: lint is called.
        Then: no errors.
        """
        # Given
        yaml_data = {
            "version": "3.0",
            "metadata": {
                "created_at": "2025-11-21T00:00:00Z",
            },
            "work_plans": [
                {
                    "id": "plan1",
                    "name": "Test Plan",
                    "objectives": {"core": "Test", "detailed": []},
                    "todos": [
                        {
                            "id": "1",
                            "title": "Task 1",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Condition 1"},
                                {"id": "c2", "condition": "Condition 2"},
                            ],
                        }
                    ],
                    "acceptance_criteria_for_verification_agent": [
                        {"id": "a1", "title": "Check 1"},
                        {"id": "a2", "title": "Check 2"},
                        {"id": "a3", "title": "Check 3"},
                        {"id": "a4", "title": "Check 4"},
                    ],
                }
            ],
        }
        linter = PlanLinter({})

        # When
        errors = linter.lint(yaml_data)

        # Then
        verification_errors = [e for e in errors if "acceptance_criteria_for_verification_agent" in e.location]
        assert len(verification_errors) == 0

    def test_verification_agent_criteria_with_five_items_passes(self) -> None:
        """Given: acceptance_criteria_for_verification_agent with 5 items.
        When: lint is called.
        Then: no errors.
        """
        # Given
        yaml_data = {
            "version": "3.0",
            "metadata": {
                "created_at": "2025-11-21T00:00:00Z",
            },
            "work_plans": [
                {
                    "id": "plan1",
                    "name": "Test Plan",
                    "objectives": {"core": "Test", "detailed": []},
                    "todos": [
                        {
                            "id": "1",
                            "title": "Task 1",
                            "status": "pending",
                            "acceptance_criteria": [
                                {"id": "c1", "condition": "Condition 1"},
                                {"id": "c2", "condition": "Condition 2"},
                            ],
                        }
                    ],
                    "acceptance_criteria_for_verification_agent": [
                        {"id": "a1", "title": "Check 1"},
                        {"id": "a2", "title": "Check 2"},
                        {"id": "a3", "title": "Check 3"},
                        {"id": "a4", "title": "Check 4"},
                        {"id": "a5", "title": "Check 5"},
                    ],
                }
            ],
        }
        linter = PlanLinter({})

        # When
        errors = linter.lint(yaml_data)

        # Then
        verification_errors = [e for e in errors if "acceptance_criteria_for_verification_agent" in e.location]
        assert len(verification_errors) == 0
