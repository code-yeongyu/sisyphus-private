"""Shared test fixtures for sisyphus-cli tests."""

import pytest

from sisyphus.core.plans.models import (
    Background,
    Objectives,
    RequiredBackground,
    SuccessVision,
    UserRequest,
    Workflow,
)


@pytest.fixture()
def minimal_user_request() -> UserRequest:
    """Minimal UserRequest for testing."""
    return UserRequest(
        original="Test user request",
        created_at="2025-11-06T00:00:00Z",
        additional=[],
    )


@pytest.fixture()
def minimal_objectives() -> Objectives:
    """Minimal Objectives for testing."""
    return Objectives(core="Test objective", detailed=[])


@pytest.fixture()
def minimal_background() -> Background:
    """Minimal Background for testing."""
    return Background(
        current_situation="Test situation",
        reason_for_change="Test reason",
        changes_to_make="Test changes",
    )


@pytest.fixture()
def minimal_required_background() -> RequiredBackground:
    """Minimal RequiredBackground for testing."""
    return RequiredBackground(description="Test background", file_structure=None, references=[])


@pytest.fixture()
def minimal_workflow() -> Workflow:
    """Minimal Workflow for testing."""
    return Workflow(dependency_diagram="Test diagram", critical_path=[])


@pytest.fixture()
def minimal_success_vision() -> SuccessVision:
    """Minimal SuccessVision for testing."""
    return SuccessVision(
        user_perspective=[],
        business_perspective=[],
        technical_criteria=[],
    )
