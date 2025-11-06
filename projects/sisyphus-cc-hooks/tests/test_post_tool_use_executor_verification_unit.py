# pyright: reportMissingImports=false
import io
import json
from pathlib import Path

import pytest
from sisyphus_cc_hooks.post_tool_use_executor_verification import (
    BashVerification,
    LLMJudgeBy,
    LLMJudgeVerification,
    PlanDocument,
    Todo,
    VerificationItem,
    WorkMode,
    WorkPlan,
    determine_verification_type,
    find_next_unverified,
    find_todo_by_id_standalone,
    format_bash_message,
    format_llm_external_message,
    format_llm_orchestrator_message,
    load_plan_from_status,
    main,
    parse_input,
    process_verification,
)


def test_find_next_unverified__returns_first_unverified() -> None:
    # given
    verifications = [
        VerificationItem(
            id="v1",
            title="First",
            description="Test",
            verified=True,
            orchestrator_manually_verified=False,
            manual_verification_evidence="",
            bash=[],
            llm_judge=[],
        ),
        VerificationItem(
            id="v2",
            title="Second",
            description="Test",
            verified=False,
            orchestrator_manually_verified=False,
            manual_verification_evidence="",
            bash=[],
            llm_judge=[],
        ),
        VerificationItem(
            id="v3",
            title="Third",
            description="Test",
            verified=False,
            orchestrator_manually_verified=False,
            manual_verification_evidence="",
            bash=[],
            llm_judge=[],
        ),
    ]

    # when
    result = find_next_unverified(verifications)

    # then
    assert result is not None
    assert result.id == "v2"


def test_find_next_unverified__returns_none_when_all_verified() -> None:
    # given
    verifications = [
        VerificationItem(
            id="v1",
            title="First",
            description="Test",
            verified=True,
            orchestrator_manually_verified=False,
            manual_verification_evidence="",
            bash=[],
            llm_judge=[],
        ),
    ]

    # when
    result = find_next_unverified(verifications)

    # then
    assert result is None


def test_find_todo_by_id__finds_top_level_todo() -> None:
    # given
    todos = [
        Todo(id="task-1", title="Task 1", status="pending", verification_spec=[]),
        Todo(id="task-2", title="Task 2", status="pending", verification_spec=[]),
    ]

    # when
    result = find_todo_by_id_standalone(todos, "task-2")

    # then
    assert result is not None
    assert result.id == "task-2"


def test_find_todo_by_id__finds_nested_todo() -> None:
    # given
    todos = [
        Todo(
            id="parent-1",
            title="Parent",
            status="pending",
            verification_spec=[],
            children=[
                Todo(id="child-1", title="Child 1", status="pending", verification_spec=[]),
                Todo(id="child-2", title="Child 2", status="pending", verification_spec=[]),
            ],
        ),
    ]

    # when
    result = find_todo_by_id_standalone(todos, "child-2")

    # then
    assert result is not None
    assert result.id == "child-2"


def test_find_todo_by_id__returns_none_when_not_found() -> None:
    # given
    todos = [
        Todo(id="task-1", title="Task 1", status="pending", verification_spec=[]),
    ]

    # when
    result = find_todo_by_id_standalone(todos, "non-existent")

    # then
    assert result is None


def test_determine_verification_type__returns_bash_when_bash_present(bash_verification_item: VerificationItem) -> None:
    # given

    # when
    verify_type, verify_item = determine_verification_type(bash_verification_item)

    # then
    assert verify_type == "bash"
    assert verify_item == bash_verification_item


def test_determine_verification_type__returns_llm_orchestrator(llm_orchestrator_item: VerificationItem) -> None:
    # given

    # when
    verify_type, verify_item = determine_verification_type(llm_orchestrator_item)

    # then
    assert verify_type == "llm_orchestrator"
    assert verify_item == llm_orchestrator_item


def test_determine_verification_type__returns_llm_external(llm_external_item: VerificationItem) -> None:
    # given

    # when
    verify_type, verify_item = determine_verification_type(llm_external_item)

    # then
    assert verify_type == "llm_external"
    assert verify_item == llm_external_item


def test_determine_verification_type__bash_priority_over_llm(mixed_verification_item: VerificationItem) -> None:
    # given

    # when
    verify_type, _ = determine_verification_type(mixed_verification_item)

    # then
    assert verify_type == "bash"


def test_load_plan_from_status__loads_successfully(tmp_path: Path) -> None:
    # given
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "test.yaml"
    plan_file.write_text("""work_plans:
  - id: test-plan
    todos:
      - id: task-1
        title: "Test Task"
        status: in_progress
        verification_spec: []
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    # when
    plan_doc, current_task_id = load_plan_from_status(str(tmp_path))

    # then
    assert isinstance(plan_doc, PlanDocument)
    assert current_task_id == "task-1"


def test_load_plan_from_status__raises_when_status_missing(tmp_path: Path) -> None:
    # given

    # when / then
    with pytest.raises(FileNotFoundError, match="No active plan"):
        load_plan_from_status(str(tmp_path))


def test_load_plan_from_status__raises_when_no_current_task(tmp_path: Path) -> None:
    # given
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "test.yaml"
    plan_file.write_text("""work_plans:
  - id: test-plan
    todos: []
    work_mode:
      current_task_id: null
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    # when / then
    with pytest.raises(ValueError, match="No task in progress"):
        load_plan_from_status(str(tmp_path))


def test_process_verification__returns_continue_when_no_verifications(simple_plan_doc: PlanDocument) -> None:
    # given

    # when
    exit_code, message = process_verification(simple_plan_doc, "task-1")

    # then
    assert exit_code == 2
    assert "ALL VERIFICATIONS COMPLETED" in message


def test_process_verification__returns_continue_when_all_verified(verified_plan_doc: PlanDocument) -> None:
    # given

    # when
    exit_code, message = process_verification(verified_plan_doc, "task-1")

    # then
    assert exit_code == 2
    assert "ALL VERIFICATIONS COMPLETED" in message


def test_process_verification__returns_bash_message_when_bash_pending(bash_pending_plan_doc: PlanDocument) -> None:
    # given

    # when
    exit_code, message = process_verification(bash_pending_plan_doc, "task-1")

    # then
    assert exit_code == 2
    assert "BASH VERIFICATION REQUIRED" in message
    assert "sisyphus task verify bash" in message


def test_process_verification__raises_when_task_not_found(simple_plan_doc: PlanDocument) -> None:
    # given

    # when / then
    with pytest.raises(RuntimeError, match="Current task not found"):
        process_verification(simple_plan_doc, "non-existent")


@pytest.fixture
def bash_verification_item() -> VerificationItem:
    return VerificationItem(
        id="v1",
        title="Bash Test",
        description="Test",
        verified=False,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[BashVerification(execute="pytest")],
        llm_judge=[],
    )


@pytest.fixture
def llm_orchestrator_item() -> VerificationItem:
    return VerificationItem(
        id="v1",
        title="LLM Test",
        description="Test",
        verified=False,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[],
        llm_judge=[LLMJudgeVerification(by=LLMJudgeBy.ORCHESTRATOR, instruction="Check code")],
    )


@pytest.fixture
def llm_external_item() -> VerificationItem:
    return VerificationItem(
        id="v1",
        title="External Test",
        description="Test",
        verified=False,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[],
        llm_judge=[LLMJudgeVerification(by=LLMJudgeBy.EXTERNAL, instruction="External check")],
    )


@pytest.fixture
def mixed_verification_item() -> VerificationItem:
    return VerificationItem(
        id="v1",
        title="Mixed Test",
        description="Test",
        verified=False,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[BashVerification(execute="pytest")],
        llm_judge=[LLMJudgeVerification(by=LLMJudgeBy.ORCHESTRATOR, instruction="Check")],
    )


@pytest.fixture
def simple_plan_doc() -> PlanDocument:
    return PlanDocument(
        work_plans=[
            WorkPlan(
                id="test-plan",
                todos=[
                    Todo(id="task-1", title="Test Task", status="in_progress", verification_spec=[]),
                ],
                work_mode=WorkMode(current_task_id="task-1"),
            )
        ]
    )


@pytest.fixture
def verified_plan_doc() -> PlanDocument:
    return PlanDocument(
        work_plans=[
            WorkPlan(
                id="test-plan",
                todos=[
                    Todo(
                        id="task-1",
                        title="Test Task",
                        status="in_progress",
                        verification_spec=[
                            VerificationItem(
                                id="v1",
                                title="Verified",
                                description="Test",
                                verified=True,
                                orchestrator_manually_verified=False,
                                manual_verification_evidence="",
                                bash=[],
                                llm_judge=[],
                            )
                        ],
                    ),
                ],
                work_mode=WorkMode(current_task_id="task-1"),
            )
        ]
    )


@pytest.fixture
def bash_pending_plan_doc() -> PlanDocument:
    return PlanDocument(
        work_plans=[
            WorkPlan(
                id="test-plan",
                todos=[
                    Todo(
                        id="task-1",
                        title="Test Task",
                        status="in_progress",
                        verification_spec=[
                            VerificationItem(
                                id="v1",
                                title="Bash Pending",
                                description="Test",
                                verified=False,
                                orchestrator_manually_verified=False,
                                manual_verification_evidence="",
                                bash=[BashVerification(execute="pytest")],
                                llm_judge=[],
                            )
                        ],
                    ),
                ],
                work_mode=WorkMode(current_task_id="task-1"),
            )
        ]
    )


def test_parse_input__parses_valid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    test_input = {"tool_input": {"subagent_type": "test"}, "cwd": "/tmp", "session_id": "123"}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(test_input)))

    # when
    result = parse_input()

    # then
    assert result == test_input


def test_parse_input__raises_on_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    monkeypatch.setattr("sys.stdin", io.StringIO("not valid json"))

    # when / then
    with pytest.raises(json.JSONDecodeError):
        parse_input()


def test_main__returns_0_for_non_executor_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    test_input = {"tool_input": {"subagent_type": "other"}, "cwd": "/tmp", "session_id": "123"}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(test_input)))

    # when
    exit_code = main()

    # then
    assert exit_code == 0


def test_main__returns_1_on_json_decode_error(monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    monkeypatch.setattr("sys.stdin", io.StringIO("invalid json"))

    # when
    exit_code = main()

    # then
    assert exit_code == 1


def test_main__returns_1_when_status_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # given
    test_input = {"tool_input": {"subagent_type": "sisyphus-executor"}, "cwd": str(tmp_path), "session_id": "123"}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(test_input)))

    # when
    exit_code = main()

    # then
    assert exit_code == 1


def test_main__returns_0_when_no_task_in_progress(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # given
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "test.yaml"
    plan_file.write_text("""work_plans:
  - id: test-plan
    todos: []
    work_mode:
      current_task_id: null
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    test_input = {"tool_input": {"subagent_type": "sisyphus-executor"}, "cwd": str(tmp_path), "session_id": "123"}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(test_input)))

    # when
    exit_code = main()

    # then
    assert exit_code == 0


def test_main__returns_2_when_verification_pending(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # given
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "test.yaml"
    plan_file.write_text("""work_plans:
  - id: test-plan
    todos:
      - id: task-1
        title: "Test Task"
        status: in_progress
        verification_spec:
          - id: v1
            title: "Test"
            description: "Test"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "pytest"
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    test_input = {"tool_input": {"subagent_type": "sisyphus-executor"}, "cwd": str(tmp_path), "session_id": "123"}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(test_input)))

    # when
    exit_code = main()

    # then
    assert exit_code == 2


def test_format_bash_message__includes_all_commands() -> None:
    # given
    item = VerificationItem(
        id="v1",
        title="Test",
        description="Desc",
        verified=False,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[BashVerification(execute="cmd1"), BashVerification(execute="cmd2")],
        llm_judge=[],
    )

    # when
    message = format_bash_message(item)

    # then
    assert "cmd1" in message
    assert "cmd2" in message


def test_format_llm_orchestrator_message__includes_instruction() -> None:
    # given
    item = VerificationItem(
        id="v1",
        title="Test",
        description="Desc",
        verified=False,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[],
        llm_judge=[LLMJudgeVerification(by=LLMJudgeBy.ORCHESTRATOR, instruction="Do this")],
    )

    # when
    message = format_llm_orchestrator_message(item)

    # then
    assert "Do this" in message


def test_format_llm_external_message__includes_instruction() -> None:
    # given
    item = VerificationItem(
        id="v1",
        title="Test",
        description="Desc",
        verified=False,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[],
        llm_judge=[LLMJudgeVerification(by=LLMJudgeBy.EXTERNAL, instruction="External task")],
    )

    # when
    message = format_llm_external_message(item)

    # then
    assert "External task" in message
