# pyright: reportMissingImports=false
"""Integration tests for executor verification hook - end-to-end workflow."""

import json
import subprocess
from pathlib import Path

import pytest


def run_hook_script(json_input: dict[str, str | dict[str, str]], script_path: Path) -> tuple[int, str, str]:
    """Execute hook script with JSON input via stdin."""
    proc = subprocess.run(
        ["uv", "run", "--script", str(script_path)],
        check=False,
        input=json.dumps(json_input),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_integration_bash_verification_workflow(script_path: Path, tmp_path: Path) -> None:
    """Test complete workflow: unverified bash -> verification message -> continue."""
    # given - Create realistic YAML plan with bash verification
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "integration-test.yaml"
    plan_file.write_text("""work_plans:
  - id: integration-test-plan
    todos:
      - id: task-1
        title: "Implement Feature X"
        status: in_progress
        verification_spec:
          - id: v1
            title: "Run All Tests"
            description: "Execute full test suite"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "pytest tests/"
                expected_exit_code: 0
              - execute: "ruff check ."
                expected_exit_code: 0
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/integration-test.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "integration-test",
    }

    # when - Trigger hook (first time - unverified)
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then - Should output bash verification message
    assert exit_code == 2
    assert "BASH VERIFICATION REQUIRED" in stderr
    assert "sisyphus task verify bash" in stderr
    assert "pytest tests/" in stderr
    assert "ruff check ." in stderr
    assert "YOU MUST RUN THIS COMMAND" in stderr


def test_integration_llm_orchestrator_workflow(script_path: Path, tmp_path: Path) -> None:
    """Test LLM orchestrator verification workflow."""
    # given - Create YAML plan with LLM orchestrator verification
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "integration-llm.yaml"
    plan_file.write_text("""work_plans:
  - id: integration-llm-plan
    todos:
      - id: task-2
        title: "Code Review Required"
        status: in_progress
        verification_spec:
          - id: v2
            title: "Manual Code Review"
            description: "Review code quality and correctness"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            llm_judge:
              - by: orchestrator-agent
                instruction: "Review the implementation for correctness, edge cases, and code quality"
    work_mode:
      current_task_id: task-2
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/integration-llm.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "integration-llm-test",
    }

    # when - Trigger hook
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then - Should output LLM orchestrator verification message
    assert exit_code == 2
    assert "LLM VERIFICATION REQUIRED - YOUR RESPONSIBILITY" in stderr
    assert "ORCHESTRATOR (YOU)" in stderr
    assert "Review the implementation for correctness" in stderr
    assert "RESPOND IN THIS FORMAT" in stderr
    assert "sisyphus task verify llm-mark v2" in stderr


def test_integration_llm_external_workflow(script_path: Path, tmp_path: Path) -> None:
    """Test LLM external agent verification workflow."""
    # given - Create YAML plan with external agent verification
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "integration-external.yaml"
    plan_file.write_text("""work_plans:
  - id: integration-external-plan
    todos:
      - id: task-3
        title: "External Security Review"
        status: in_progress
        verification_spec:
          - id: v3
            title: "Security Audit"
            description: "External agent security review"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            llm_judge:
              - by: external-agent
                instruction: "Perform security audit using external security agent"
    work_mode:
      current_task_id: task-3
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/integration-external.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "integration-external-test",
    }

    # when - Trigger hook
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then - Should output external agent verification message
    assert exit_code == 2
    assert "LLM VERIFICATION REQUIRED - EXTERNAL AGENT" in stderr
    assert "EXTERNAL AGENT (Claude Agent SDK)" in stderr
    assert "Perform security audit" in stderr
    assert "Invoke external agent" in stderr
    assert "v3_VERIFIED = TRUE" in stderr


def test_integration_all_verified_continue_workflow(script_path: Path, tmp_path: Path) -> None:
    """Test continue message when all verifications completed."""
    # given - Create YAML plan with all verifications completed
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "integration-complete.yaml"
    plan_file.write_text("""work_plans:
  - id: integration-complete-plan
    todos:
      - id: task-4
        title: "Completed Task"
        status: in_progress
        verification_spec:
          - id: v4
            title: "All Tests Pass"
            description: "All verifications completed"
            verified: true
            verified_at: "2025-11-06T10:00:00Z"
            verification_evidence: "All tests passed successfully"
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "pytest"
    work_mode:
      current_task_id: task-4
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/integration-complete.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "integration-complete-test",
    }

    # when - Trigger hook
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then - Should output continue message
    assert exit_code == 2
    assert "ALL VERIFICATIONS COMPLETED" in stderr
    assert "sisyphus task continue" in stderr
    assert "RESPOND IN THIS FORMAT" in stderr
    assert "executed successfully" in stderr


def test_integration_multiple_verifications_sequential(script_path: Path, tmp_path: Path) -> None:
    """Test multiple verification items processed in list order."""
    # given - Create YAML plan with multiple verification items
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "integration-multi.yaml"
    plan_file.write_text("""work_plans:
  - id: integration-multi-plan
    todos:
      - id: task-5
        title: "Multi-Step Verification"
        status: in_progress
        verification_spec:
          - id: v5a
            title: "Unit Tests"
            description: "First verification step"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "pytest tests/unit/"
          - id: v5b
            title: "Integration Tests"
            description: "Second verification step"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "pytest tests/integration/"
          - id: v5c
            title: "Code Review"
            description: "Third verification step"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            llm_judge:
              - by: orchestrator-agent
                instruction: "Review code quality"
    work_mode:
      current_task_id: task-5
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/integration-multi.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "integration-multi-test",
    }

    # when - Trigger hook (first unverified should be v5a)
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then - Should output first verification (v5a - Unit Tests)
    assert exit_code == 2
    assert "Unit Tests" in stderr
    assert "pytest tests/unit/" in stderr
    assert "First verification step" in stderr


def test_integration_empty_verification_spec(script_path: Path, tmp_path: Path) -> None:
    """Test task with no verification requirements."""
    # given - Create YAML plan with empty verification_spec
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "integration-empty.yaml"
    plan_file.write_text("""work_plans:
  - id: integration-empty-plan
    todos:
      - id: task-6
        title: "No Verification Required"
        status: in_progress
        verification_spec: []
    work_mode:
      current_task_id: task-6
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/integration-empty.yaml"}}))

    json_input: dict[str, str | dict[str, str]] = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "integration-empty-test",
    }

    # when - Trigger hook
    exit_code, _stdout, stderr = run_hook_script(json_input, script_path)

    # then - Should directly output continue message
    assert exit_code == 2
    assert "ALL VERIFICATIONS COMPLETED" in stderr
    assert "sisyphus task continue" in stderr


@pytest.fixture
def script_path() -> Path:
    """Path to the main hook script."""
    return Path(__file__).parent.parent / "sisyphus_cc_hooks" / "post_tool_use_executor_verification.py"
