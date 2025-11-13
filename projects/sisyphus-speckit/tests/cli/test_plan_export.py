from pathlib import Path

from typer.testing import CliRunner

from sisyphus_speckit.cli import app

runner = CliRunner()


def test_export__with_valid_v3_yaml__outputs_markdown(tmp_path: Path) -> None:
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-11-01T00:00:00Z"
work_plans:
  - id: test-plan
    name: "Test Plan"
    depends_on: []
    user_request:
      original: "Test request"
      created_at: "2025-11-01T00:00:00Z"
    objectives:
      core: "Test objective"
    background:
      current_situation: "Test situation"
      reason_for_change: "Test reason"
      changes_to_make: "Test changes"
    required_background:
      description: "Test background"
    workflow:
      dependency_diagram: "Test diagram"
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "First Task"
        status: pending
        created_at: "2025-11-01T00:00:00Z"
        updated_at: "2025-11-01T00:00:00Z"
"""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(yaml_content)

    result = runner.invoke(app, ["plan", "export", str(yaml_file)])

    assert result.exit_code == 0
    assert "# 사용자의 최초 요청" in result.stdout
    assert "Test Plan" in result.stdout
    assert "# TODOs" in result.stdout
    assert "- [ ] 1. First Task" in result.stdout


def test_export__with_completed_task__shows_checked_checkbox(tmp_path: Path) -> None:
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-11-01T00:00:00Z"
work_plans:
  - id: test-plan
    name: "Test Plan"
    depends_on: []
    user_request:
      original: "Test request"
      created_at: "2025-11-01T00:00:00Z"
    objectives:
      core: "Test objective"
    background:
      current_situation: "Test situation"
      reason_for_change: "Test reason"
      changes_to_make: "Test changes"
    required_background:
      description: "Test background"
    workflow:
      dependency_diagram: "Test diagram"
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Completed Task"
        status: completed
        created_at: "2025-11-01T00:00:00Z"
        updated_at: "2025-11-01T00:00:00Z"
"""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(yaml_content)

    result = runner.invoke(app, ["plan", "export", str(yaml_file)])

    assert result.exit_code == 0
    assert "- [x] 1. Completed Task" in result.stdout


def test_export__with_output_option__creates_markdown_file(tmp_path: Path) -> None:
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-11-01T00:00:00Z"
work_plans:
  - id: test-plan
    name: "Test Plan"
    depends_on: []
    user_request:
      original: "Test request"
      created_at: "2025-11-01T00:00:00Z"
    objectives:
      core: "Test objective"
    background:
      current_situation: "Test situation"
      reason_for_change: "Test reason"
      changes_to_make: "Test changes"
    required_background:
      description: "Test background"
    workflow:
      dependency_diagram: "Test diagram"
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Task"
        status: pending
        created_at: "2025-11-01T00:00:00Z"
        updated_at: "2025-11-01T00:00:00Z"
"""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(yaml_content)
    output_file = tmp_path / "output.md"

    result = runner.invoke(app, ["plan", "export", str(yaml_file), "--output", str(output_file)])

    assert result.exit_code == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "# 사용자의 최초 요청" in content
    assert "Test Plan" in content
    assert "- [ ] 1. Task" in content


def test_export__with_nonexistent_file__fails(tmp_path: Path) -> None:
    nonexistent = tmp_path / "nonexistent.yaml"

    result = runner.invoke(app, ["plan", "export", str(nonexistent)])

    assert result.exit_code == 1
    assert "Error: File not found" in result.stdout


def test_export__with_children__indents_properly(tmp_path: Path) -> None:
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-11-01T00:00:00Z"
work_plans:
  - id: test-plan
    name: "Test Plan"
    depends_on: []
    user_request:
      original: "Test request"
      created_at: "2025-11-01T00:00:00Z"
    objectives:
      core: "Test objective"
    background:
      current_situation: "Test situation"
      reason_for_change: "Test reason"
      changes_to_make: "Test changes"
    required_background:
      description: "Test background"
    workflow:
      dependency_diagram: "Test diagram"
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Parent Task"
        status: pending
        created_at: "2025-11-01T00:00:00Z"
        updated_at: "2025-11-01T00:00:00Z"
        children:
          - id: "1.1"
            title: "Child Task"
            status: pending
            created_at: "2025-11-01T00:00:00Z"
            updated_at: "2025-11-01T00:00:00Z"
"""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(yaml_content)

    result = runner.invoke(app, ["plan", "export", str(yaml_file)])

    assert result.exit_code == 0
    assert "- [ ] 1. Parent Task" in result.stdout
    assert "   - [ ] 1.1. Child Task" in result.stdout


def test_export__with_references__creates_references_section(tmp_path: Path) -> None:
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-11-01T00:00:00Z"
work_plans:
  - id: test-plan
    name: "Test Plan"
    depends_on: []
    user_request:
      original: "Test request"
      created_at: "2025-11-01T00:00:00Z"
    objectives:
      core: "Test objective"
    background:
      current_situation: "Test situation"
      reason_for_change: "Test reason"
      changes_to_make: "Test changes"
    required_background:
      description: "Test background"
    workflow:
      dependency_diagram: "Test diagram"
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Task"
        status: pending
        created_at: "2025-11-01T00:00:00Z"
        updated_at: "2025-11-01T00:00:00Z"
    references:
      - ref_id: "ref1"
        uri: "https://example.com"
      - ref_id: "ref2"
        inline: "Inline reference text"
"""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(yaml_content)

    result = runner.invoke(app, ["plan", "export", str(yaml_file)])

    assert result.exit_code == 0
    assert "## References" in result.stdout
    assert "- [ref1]: https://example.com" in result.stdout
    assert "- [ref2]: Inline reference text" in result.stdout


def test_export__with_cwd_option__resolves_paths(tmp_path: Path) -> None:
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-11-01T00:00:00Z"
work_plans:
  - id: test-plan
    name: "Test Plan"
    depends_on: []
    user_request:
      original: "Test request"
      created_at: "2025-11-01T00:00:00Z"
    objectives:
      core: "Test objective"
    background:
      current_situation: "Test situation"
      reason_for_change: "Test reason"
      changes_to_make: "Test changes"
    required_background:
      description: "Test background"
    workflow:
      dependency_diagram: "Test diagram"
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Task"
        status: pending
        created_at: "2025-11-01T00:00:00Z"
        updated_at: "2025-11-01T00:00:00Z"
"""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(yaml_content)

    result = runner.invoke(app, ["plan", "export", "test.yaml", "--cwd", str(tmp_path)])

    assert result.exit_code == 0
    assert "Test Plan" in result.stdout
