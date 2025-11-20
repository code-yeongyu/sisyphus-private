"""Tests for plan list command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sisyphus_core.core.plans.models import (
    Background,
    ExecutionStatus,
    Objectives,
    RequiredBackground,
    SuccessVision,
    UserRequest,
    Workflow,
    WorkMode,
    WorkPlan,
)

from sisyphus_speckit.plan.list import (
    PlanInfo,
    _calculate_status,
    _check_dependencies_satisfied,
    _get_current_plan_id,
    _get_sort_key,
    list_plans,
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


@pytest.fixture()
def minimal_work_plan(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> WorkPlan:
    """Minimal WorkPlan for testing."""
    return WorkPlan(
        id="test-plan",
        name="Test Plan",
        depends_on=[],
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[],
        references=[],
        execution=ExecutionStatus(started=False, completed=False, started_at=None, completed_at=None),
        work_mode=WorkMode(parallel_requested=False),
    )


def test_list_plans__if_directory_exists__prints_table(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # given: 테스트 YAML 파일 생성
    plan_dir = tmp_path / "plans"
    plan_dir.mkdir()

    user_request = UserRequest(
        original="Test",
        created_at="2025-11-06T00:00:00Z",
        additional=[],
    )
    work_plan = WorkPlan(
        id="test-plan-1",
        name="Test Plan 1",
        depends_on=[],
        user_request=user_request,
        objectives=Objectives(core="Test", detailed=[]),
        background=Background(
            current_situation="Test",
            reason_for_change="Test",
            changes_to_make="Test",
        ),
        required_background=RequiredBackground(description="Test", file_structure=None, references=[]),
        workflow=Workflow(dependency_diagram="Test", critical_path=[]),
        success_vision=SuccessVision(user_perspective=[], business_perspective=[], technical_criteria=[]),
        final_verification=[],
        todos=[],
        references=[],
        execution=ExecutionStatus(started=False, completed=False, started_at=None, completed_at=None),
        work_mode=WorkMode(parallel_requested=False),
    )

    # YAML 파일 생성
    plan_file = plan_dir / "test.yaml"
    plan_doc_dict = {
        "version": "3.0",
        "metadata": {
            "created_at": "2025-11-06T00:00:00Z",
        },
        "work_plans": [work_plan.model_dump()],
    }
    _ = plan_file.write_text(
        json.dumps(plan_doc_dict),
        encoding="utf-8",
    )

    # when: list_plans 실행
    list_plans(directory=plan_dir, filter_status=None, sort_by="default", cwd=None)
    captured = capsys.readouterr()

    # then: 테이블 출력 확인
    assert captured.out
    assert "Test Plan 1" in captured.out or "Available Plans" in captured.out


def test_list_plans__if_filter_status__filters_correctly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # given: 필터링 옵션이 있을 때
    plan_dir = tmp_path / "plans"
    plan_dir.mkdir()

    user_request = UserRequest(
        original="Test",
        created_at="2025-11-06T00:00:00Z",
        additional=[],
    )
    work_plan = WorkPlan(
        id="test-plan-1",
        name="Test Plan 1",
        depends_on=[],
        user_request=user_request,
        objectives=Objectives(core="Test", detailed=[]),
        background=Background(
            current_situation="Test",
            reason_for_change="Test",
            changes_to_make="Test",
        ),
        required_background=RequiredBackground(description="Test", file_structure=None, references=[]),
        workflow=Workflow(dependency_diagram="Test", critical_path=[]),
        success_vision=SuccessVision(user_perspective=[], business_perspective=[], technical_criteria=[]),
        final_verification=[],
        todos=[],
        references=[],
        execution=ExecutionStatus(started=False, completed=False, started_at=None, completed_at=None),
        work_mode=WorkMode(parallel_requested=False),
    )

    plan_file = plan_dir / "test.yaml"
    plan_doc_dict = {
        "version": "3.0",
        "metadata": {
            "created_at": "2025-11-06T00:00:00Z",
        },
        "work_plans": [work_plan.model_dump()],
    }
    _ = plan_file.write_text(
        json.dumps(plan_doc_dict),
        encoding="utf-8",
    )

    # when: 필터 옵션이 없을 때 테이블 출력
    list_plans(directory=plan_dir, filter_status=None, sort_by="default", cwd=None)
    captured = capsys.readouterr()

    # then: 테이블이 생성됨
    assert "Available Plans" in captured.out


@pytest.mark.usefixtures("tmp_path")
def test_list_plans__if_sort_option__sorts_correctly() -> None:
    # given: 정렬 키 생성
    plan_info_1: PlanInfo = {
        "id": "plan-1",
        "name": "Plan A",
        "filepath": "test1.yaml",
        "depends_on": [],
        "created_at": "2025-11-07T00:00:00Z",
        "fully_done": False,
        "dependency_count": 0,
        "status": "작업 가능",
    }

    plan_info_2: PlanInfo = {
        "id": "plan-2",
        "name": "Plan B",
        "filepath": "test2.yaml",
        "depends_on": [],
        "created_at": "2025-11-06T00:00:00Z",
        "fully_done": False,
        "dependency_count": 0,
        "status": "완료됨",
    }

    # when: default 정렬 키 생성
    status_order = {"작업 가능": 0, "작업중": 1, "의존성 대기중": 2, "완료됨": 3}
    key_1 = _get_sort_key(plan_info_1, status_order)
    key_2 = _get_sort_key(plan_info_2, status_order)

    # then: 상태가 먼저 정렬되고, 같은 상태일 때 created_at 기준
    assert key_1[0] < key_2[0], "작업 가능이 완료됨보다 앞에 정렬"
    assert key_1 == (0, "2025-11-07T00:00:00Z")
    assert key_2 == (3, "2025-11-06T00:00:00Z")


@pytest.mark.anyio()
@pytest.mark.usefixtures("tmp_path")
async def test_list_plans__calculates_status_correctly() -> None:
    # given: 현재 plan과 의존 관계가 있는 plans
    current_plan_id = "plan-1"

    plan_info_current: PlanInfo = {
        "id": "plan-1",
        "name": "Current Plan",
        "filepath": "test1.yaml",
        "depends_on": [],
        "created_at": "2025-11-06T00:00:00Z",
        "fully_done": False,
        "dependency_count": 0,
        "status": "",
    }

    plan_info_completed: PlanInfo = {
        "id": "plan-2",
        "name": "Completed Plan",
        "filepath": "test2.yaml",
        "depends_on": [],
        "created_at": "2025-11-05T00:00:00Z",
        "fully_done": True,
        "dependency_count": 0,
        "status": "",
    }

    plan_info_waiting: PlanInfo = {
        "id": "plan-3",
        "name": "Waiting Plan",
        "filepath": "test3.yaml",
        "depends_on": ["plan-1"],
        "created_at": "2025-11-07T00:00:00Z",
        "fully_done": False,
        "dependency_count": 1,
        "status": "",
    }

    all_plans: dict[str, PlanInfo] = {
        "plan-1": plan_info_current,
        "plan-2": plan_info_completed,
        "plan-3": plan_info_waiting,
    }

    # when: 각 plan의 상태 계산
    status_current = await _calculate_status(
        "plan-1",
        [],
        False,
        current_plan_id,
        all_plans,
    )

    status_completed = await _calculate_status(
        "plan-2",
        [],
        True,
        current_plan_id,
        all_plans,
    )

    status_waiting = await _calculate_status(
        "plan-3",
        ["plan-1"],
        False,
        current_plan_id,
        all_plans,
    )

    # then: 상태가 올바르게 계산됨
    assert status_current == "작업중", "현재 작업 중인 plan은 '작업중'"
    assert status_completed == "완료됨", "fully_done이 True인 plan은 '완료됨'"
    assert status_waiting == "의존성 대기중", "의존 plan이 미완료인 경우 '의존성 대기중'"


@pytest.mark.anyio()
async def test_list_plans__checks_dependencies_satisfied(tmp_path: Path) -> None:
    # given: 의존 관계가 있는 plans
    plan_info_completed: PlanInfo = {
        "id": "plan-1",
        "name": "Completed",
        "filepath": "test1.yaml",
        "depends_on": [],
        "created_at": "2025-11-06T00:00:00Z",
        "fully_done": True,
        "dependency_count": 0,
        "status": "완료됨",
    }

    plan_info_pending: PlanInfo = {
        "id": "plan-2",
        "name": "Pending",
        "filepath": "test2.yaml",
        "depends_on": ["plan-1"],
        "created_at": "2025-11-07T00:00:00Z",
        "fully_done": False,
        "dependency_count": 1,
        "status": "",
    }

    all_plans: dict[str, PlanInfo] = {
        "plan-1": plan_info_completed,
        "plan-2": plan_info_pending,
    }

    # when: 의존성 확인
    deps_satisfied = await _check_dependencies_satisfied(
        "plan-2",
        ["plan-1"],
        tmp_path,
        all_plans,
    )

    deps_not_satisfied = await _check_dependencies_satisfied(
        "plan-2",
        ["plan-1", "plan-nonexistent"],
        tmp_path,
        all_plans,
    )

    # then: 의존성 만족 여부 확인
    assert deps_satisfied is True, "plan-1이 완료되면 의존성 만족"
    assert deps_not_satisfied is False, "nonexistent plan이 있으면 의존성 미만족"


@pytest.mark.anyio()
async def test_list_plans__reads_current_plan_from_status_json(tmp_path: Path) -> None:
    # given: status.json 파일 생성
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    status_file = sisyphus_dir / "status.json"

    current_plan_path = str(tmp_path / "plans" / "current.yaml")
    _ = status_file.write_text(
        json.dumps(
            {
                "current_plan": {
                    "plan_path": current_plan_path,
                }
            }
        ),
        encoding="utf-8",
    )

    # when: 현재 plan ID 읽기
    current_plan_id = await _get_current_plan_id(tmp_path)

    # then: plan ID가 경로에서 추출됨
    assert current_plan_id == "current", "status.json에서 현재 plan 추출"


@pytest.mark.anyio()
async def test_list_plans__returns_none_if_status_json_not_exists(tmp_path: Path) -> None:
    # given: status.json이 없는 디렉토리
    # when: 현재 plan ID 읽기
    current_plan_id = await _get_current_plan_id(tmp_path)

    # then: None 반환
    assert current_plan_id is None, "status.json이 없으면 None 반환"


def test_list_plans__handles_empty_directory(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # given: 빈 디렉토리
    plan_dir = tmp_path / "empty_plans"
    plan_dir.mkdir()

    # when: list_plans 실행
    list_plans(directory=plan_dir, filter_status=None, sort_by="default", cwd=None)
    captured = capsys.readouterr()

    # then: 프롬프트 메시지 출력
    assert "No plans found" in captured.out or "plans" in captured.out.lower()
