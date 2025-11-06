# pyright: reportMissingImports=false
import json
import subprocess
from pathlib import Path

import pytest


def run_hook_script(json_input: dict[str, str | dict[str, str]], script_path: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["uv", "run", "--script", str(script_path)],
        check=False,
        input=json.dumps(json_input),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_executor_agent_triggers_hook(script_path: Path, tmp_path: Path) -> None:
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

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test-session",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 2
    assert "ALL VERIFICATIONS COMPLETED" in stderr


def test_non_executor_agent_skips_hook(script_path: Path) -> None:
    # given
    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "general-purpose"},
        "cwd": ".",
        "session_id": "test-session",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 0
    assert "Skipping hook" in stderr
    assert "general-purpose" in stderr


def test_invalid_json_returns_error(script_path: Path) -> None:
    # given
    invalid_json = "not valid json"

    # when
    proc = subprocess.run(
        ["uv", "run", "--script", str(script_path)],
        check=False,
        input=invalid_json,
        capture_output=True,
        text=True,
    )

    # then
    assert proc.returncode == 1
    assert "Invalid JSON input" in proc.stderr


def test_missing_subagent_type_skips_hook(script_path: Path) -> None:
    # given
    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {},
        "cwd": ".",
        "session_id": "test-session",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 0
    assert "Skipping hook" in stderr


def test_status_json_missing__exits_with_error(script_path: Path, tmp_path: Path) -> None:
    # given
    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 1
    assert "No active plan" in stderr


def test_no_current_task__exits_quietly(script_path: Path, tmp_path: Path) -> None:
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

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 0
    assert "No task in progress" in stderr


def test_yaml_parsing_success__finds_current_task(script_path: Path, tmp_path: Path) -> None:
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
            title: "Pending Verification"
            description: "Test"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "echo test"
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 2
    assert "BASH VERIFICATION REQUIRED" in stderr
    assert "Pending Verification" in stderr


def test_invalid_yaml__exits_with_error(script_path: Path, tmp_path: Path) -> None:
    # given
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "test.yaml"
    plan_file.write_text("invalid: [yaml: structure")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 1
    assert "Failed to load YAML" in stderr


def test_task_not_found__exits_with_error(script_path: Path, tmp_path: Path) -> None:
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
      current_task_id: non-existent-id
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 1
    assert "Current task not found" in stderr


def test_no_verification_spec__outputs_continue(script_path: Path, tmp_path: Path) -> None:
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

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 2
    assert "ALL VERIFICATIONS COMPLETED" in stderr or "No verification" in stderr


def test_all_verified__outputs_continue(script_path: Path, tmp_path: Path) -> None:
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
            title: "Verification 1"
            description: "Test"
            verified: true
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "echo test"
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 2
    assert "ALL VERIFICATIONS COMPLETED" in stderr


def test_bash_verification_pending__detects_bash_type(script_path: Path, tmp_path: Path) -> None:
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
            title: "Bash Verification"
            description: "Test bash"
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

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 2
    assert "bash" in stderr.lower()
    assert "Bash Verification" in stderr


def test_llm_orchestrator_verification__detects_orchestrator_type(script_path: Path, tmp_path: Path) -> None:
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
            title: "LLM Orchestrator Verification"
            description: "Test llm"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            llm_judge:
              - by: orchestrator-agent
                instruction: "Check the code"
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 2
    assert "llm" in stderr.lower() or "orchestrator" in stderr.lower()


def test_llm_external_verification__detects_external_type(script_path: Path, tmp_path: Path) -> None:
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
            title: "LLM External Verification"
            description: "Test external"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            llm_judge:
              - by: external-agent
                instruction: "Review with external agent"
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 2
    assert "external" in stderr.lower() or "llm" in stderr.lower()


def test_bash_priority_over_llm__returns_bash_type(script_path: Path, tmp_path: Path) -> None:
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
            title: "Mixed Verification"
            description: "Has both bash and llm"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "pytest"
            llm_judge:
              - by: orchestrator-agent
                instruction: "Also check manually"
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 2
    assert "bash" in stderr.lower()


def test_bash_message_content__contains_required_elements(script_path: Path, tmp_path: Path) -> None:
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
            title: "Run Tests"
            description: "Execute pytest"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "pytest tests/"
              - execute: "ruff check ."
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 2
    assert "BASH VERIFICATION REQUIRED" in stderr
    assert "sisyphus task verify bash" in stderr
    assert "pytest tests/" in stderr
    assert "ruff check ." in stderr
    assert "YOU MUST RUN THIS COMMAND" in stderr


def test_llm_orchestrator_message__contains_instruction_and_format(script_path: Path, tmp_path: Path) -> None:
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
            title: "Code Review"
            description: "Manual review required"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            llm_judge:
              - by: orchestrator-agent
                instruction: "Review the code for correctness and style"
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 2
    assert "LLM VERIFICATION REQUIRED - YOUR RESPONSIBILITY" in stderr
    assert "Review the code for correctness and style" in stderr
    assert "RESPOND IN THIS FORMAT" in stderr
    assert "Verification completed for" in stderr
    assert "sisyphus task verify llm-mark v1" in stderr


def test_llm_external_message__contains_external_agent_instructions(script_path: Path, tmp_path: Path) -> None:
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
            title: "External Agent Review"
            description: "Use external agent"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            llm_judge:
              - by: external-agent
                instruction: "Call external reviewer agent"
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 2
    assert "LLM VERIFICATION REQUIRED - EXTERNAL AGENT" in stderr
    assert "Call external reviewer agent" in stderr
    assert "Invoke external agent" in stderr
    assert "v1_VERIFIED = TRUE" in stderr


def test_continue_message__contains_format_instructions(script_path: Path, tmp_path: Path) -> None:
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
            title: "Completed Verification"
            description: "Already verified"
            verified: true
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "echo done"
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 2
    assert "ALL VERIFICATIONS COMPLETED" in stderr
    assert "sisyphus task continue" in stderr
    assert "RESPOND IN THIS FORMAT" in stderr
    assert "executed successfully" in stderr


def test_all_messages_in_english__no_korean_characters(script_path: Path, tmp_path: Path) -> None:
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
              - execute: "echo test"
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 2
    korean_chars = any("\uac00" <= char <= "\ud7a3" for char in stderr)
    assert not korean_chars, "Message contains Korean characters"


def test_exit_code_2_for_all_verification_types(script_path: Path, tmp_path: Path) -> None:
    # given
    test_cases = [
        (
            "bash",
            """
            bash:
              - execute: "pytest"
        """,
        ),
        (
            "orchestrator",
            """
            llm_judge:
              - by: orchestrator-agent
                instruction: "Check"
        """,
        ),
        (
            "external",
            """
            llm_judge:
              - by: external-agent
                instruction: "Review"
        """,
        ),
    ]

    for test_name, verification_yaml in test_cases:
        test_root = tmp_path / test_name
        test_root.mkdir(exist_ok=True)
        sisyphus_dir = test_root / ".sisyphus"
        sisyphus_dir.mkdir(exist_ok=True)
        tasks_dir = sisyphus_dir / "tasks"
        tasks_dir.mkdir(exist_ok=True)

        plan_file = tasks_dir / "test.yaml"
        plan_file.write_text(f"""work_plans:
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
            {verification_yaml}
    work_mode:
      current_task_id: task-1
""")

        status_file = sisyphus_dir / "status.json"
        status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

        json_input: dict[str, str | dict[str, str]] = {
            "tool_input": {"subagent_type": "sisyphus-executor"},
            "cwd": str(test_root),
            "session_id": "test",
        }

        # when
        exit_code, _stdout, _stderr = run_hook_script(json_input, script_path)

        # then
        assert exit_code == 2, f"Exit code should be 2 for {test_name} verification"


def test_common_header_in_all_messages(script_path: Path, tmp_path: Path) -> None:
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

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 2
    assert "EXECUTOR TASK COMPLETION DETECTED" in stderr
    assert "CRITICAL NOTICE" in stderr
    assert "VERIFICATION IS MANDATORY" in stderr


@pytest.fixture
def script_path() -> Path:
    return Path(__file__).parent.parent / "sisyphus_cc_hooks" / "post_tool_use_executor_verification.py"


def test_nested_todo_structure(script_path: Path, tmp_path: Path) -> None:
    """Test finding todo in nested children structure."""
    # given
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "nested.yaml"
    plan_file.write_text("""work_plans:
  - id: test-plan
    todos:
      - id: parent-1
        title: "Parent Task"
        status: pending
        verification_spec: []
        children:
          - id: child-1
            title: "Child Task"
            status: in_progress
            verification_spec: []
      - id: parent-2
        title: "Another Parent"
        status: pending
        verification_spec: []
    work_mode:
      current_task_id: child-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/nested.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test-nested",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then - Should find nested child task
    assert exit_code == 2
    assert "ALL VERIFICATIONS COMPLETED" in stderr


def test_invalid_yaml_format(script_path: Path, tmp_path: Path) -> None:
    """Test handling of invalid YAML format."""
    # given
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "invalid.yaml"
    plan_file.write_text("""work_plans:
  - id: test-plan
    todos: [this is invalid yaml structure
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/invalid.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test-invalid-yaml",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 1
    assert "Failed to load YAML" in stderr


def test_invalid_json_input(script_path: Path, tmp_path: Path) -> None:
    """Test handling of invalid JSON input."""
    # given

    # when - Send invalid JSON
    proc = subprocess.run(
        ["uv", "run", "--script", str(script_path)],
        check=False,
        input="this is not valid json",
        capture_output=True,
        text=True,
    )

    # then
    assert proc.returncode == 1
    assert "Invalid JSON input" in proc.stderr


def test_task_not_found_in_todos(script_path: Path, tmp_path: Path) -> None:
    """Test when current_task_id doesn't exist in todos."""
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
        title: "Task 1"
        status: pending
        verification_spec: []
    work_mode:
      current_task_id: non-existent-task
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 1
    assert "Current task not found" in stderr


def test_missing_plan_file(script_path: Path, tmp_path: Path) -> None:
    """Test when plan file specified in status.json doesn't exist."""
    # given
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/nonexistent.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 1
    assert "Plan file not found" in stderr


def test_llm_external_agent_verification(script_path: Path, tmp_path: Path) -> None:
    """Test LLM external agent verification message."""
    # given
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "external.yaml"
    plan_file.write_text("""work_plans:
  - id: test-plan
    todos:
      - id: task-1
        title: "External Agent Task"
        status: in_progress
        verification_spec:
          - id: v1
            title: "External Verification"
            description: "Use external agent"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            llm_judge:
              - by: external-agent
                instruction: "Run external security scan"
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/external.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then
    assert exit_code == 2
    assert "LLM VERIFICATION REQUIRED - EXTERNAL AGENT" in stderr
    assert "external-agent" in stderr.lower() or "external agent" in stderr.lower()
