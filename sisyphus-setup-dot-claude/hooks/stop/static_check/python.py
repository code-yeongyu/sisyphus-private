#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "toml>=0.10.2",
#   "ast-grep-py>=0.24.1",
# ]
# ///
# pyright: reportMissingImports=false, reportMissingModuleSource=false

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NotRequired, TypedDict

import ast_grep_py as sg  # pyright: ignore[reportMissingImports]
import toml

EXIT_CODE_ALLOW: int = 0
EXIT_CODE_BLOCK: int = 2

ALWAYS_ENFORCE_RULES: list[str] = [
    "ASYNC",
    "ANN001",
    "ANN201",
    "ANN202",
    "ANN204",
    "ANN205",
    "ANN206",
    "ANN401",
]
FALLBACK_LINT_RULES: list[str] = [
    "PLE",
    "PLW",
    "E",
    "W",
    "F",
    "I",
    "Q",
    "UP",
    "C4",
    "PT",
]
FALLBACK_EXCLUDE_PATHS: list[str] = []
FALLBACK_LINE_LENGTH: int = 119

VENV_RUFF_PATHS: list[Path] = [
    Path(".venv/bin/ruff"),
    Path("venv/bin/ruff"),
]
PYPROJECT_PATH = Path("pyproject.toml")

RUFF_CMD_CHECK = "check"
RUFF_CMD_FORMAT = "format"

RUFF_FLAG_UNSAFE_FIXES = "--unsafe-fixes"
RUFF_FLAG_EXTEND_SELECT = "--extend-select"
RUFF_FLAG_SELECT = "--select"
RUFF_FLAG_EXCLUDE = "--exclude"
RUFF_FLAG_LINE_LENGTH = "--line-length"
RUFF_FLAG_TARGET_VERSION = "--target-version"

VERSION_WITH_OPERATOR_PATTERN: re.Pattern[str] = re.compile(r"[~>=<!=]+\s*(\d+\.\d+(?:\.\d+)?)")
VERSION_WITHOUT_OPERATOR_PATTERN: re.Pattern[str] = re.compile(r"(\d+\.\d+(?:\.\d+)?)")


class StopCheckInput(TypedDict):
    file_path: str
    cwd: str


class PyprojectToml(TypedDict):
    tool: NotRequired[ToolConfig]


class ToolConfig(TypedDict):
    ruff: NotRequired[RuffConfig]


class RuffConfig(TypedDict):
    lint: NotRequired[RuffLintConfig]


class RuffLintConfig(TypedDict):
    select: NotRequired[list[str]]
    extend_select: NotRequired[list[str]]
    ignore: NotRequired[list[str]]


@dataclass
class RuffConfiguration:
    executable_path: str
    lint_args: list[str]
    format_args: list[str]
    use_fallback: bool


@dataclass
class RuffResults:
    lint_output: str
    lint_exit_code: int
    format_output: str
    format_exit_code: int


PyprojectConfig = PyprojectToml | dict[str, Any]


def main() -> None:
    try:
        input_data = sys.stdin.read()
        if not input_data:
            sys.exit(EXIT_CODE_ALLOW)

        data: StopCheckInput = json.loads(input_data)
        file_path = data.get("file_path", "")
        cwd = data.get("cwd", ".")

        if not file_path or not file_path.endswith(".py"):
            sys.exit(EXIT_CODE_ALLOW)

        if not Path(file_path).exists():
            sys.exit(EXIT_CODE_ALLOW)

        all_errors: list[str] = []

        opinionated_errors = run_opinionated_checks(file_path)
        if opinionated_errors:
            all_errors.extend(opinionated_errors)

        ruff_errors = run_ruff_check(file_path, cwd)
        if ruff_errors:
            all_errors.extend(ruff_errors)

        basedpyright_errors = run_basedpyright_check(file_path, cwd)
        if basedpyright_errors:
            all_errors.extend(basedpyright_errors)

        if all_errors:
            for error in all_errors:
                print(error, file=sys.stderr, end="")
            sys.exit(EXIT_CODE_BLOCK)

        sys.exit(EXIT_CODE_ALLOW)

    except Exception:
        sys.exit(EXIT_CODE_ALLOW)


def run_ruff_check(file_path: str, cwd: str) -> list[str]:
    config = resolve_ruff_configuration()
    if not config:
        return []

    results = execute_ruff_operations(config, file_path, cwd)
    return build_ruff_error_messages(results, file_path)


def resolve_ruff_configuration() -> RuffConfiguration | None:
    ruff_path, needs_fallback = find_ruff_executable()
    if not ruff_path:
        ruff_path = shutil.which("ruff")
        if not ruff_path:
            return None
        needs_fallback = True

    if needs_fallback or should_use_fallback_config():
        lint_args, format_args = get_fallback_args()
        use_fallback = True
    else:
        lint_args = [RUFF_FLAG_EXTEND_SELECT, ",".join(ALWAYS_ENFORCE_RULES)]
        format_args = []
        use_fallback = False

    return RuffConfiguration(
        executable_path=ruff_path,
        lint_args=lint_args,
        format_args=format_args,
        use_fallback=use_fallback,
    )


def execute_ruff_operations(config: RuffConfiguration, file_path: str, cwd: str) -> RuffResults:
    lint_output, lint_exit_code = run_ruff_command(
        config.executable_path,
        [RUFF_CMD_CHECK, RUFF_FLAG_UNSAFE_FIXES] + config.lint_args + [file_path],
        cwd,
    )
    lint_output = lint_output.strip()

    _, format_check_exit_code = run_ruff_command(
        config.executable_path,
        [RUFF_CMD_FORMAT, "--check"] + config.format_args + [file_path],
        cwd,
    )

    format_output = ""
    if format_check_exit_code != 0:
        format_output = f"File would be reformatted: {file_path}"

    return RuffResults(
        lint_output=lint_output,
        lint_exit_code=lint_exit_code,
        format_output=format_output,
        format_exit_code=format_check_exit_code,
    )


def build_ruff_error_messages(results: RuffResults, file_path: str) -> list[str]:
    messages: list[str] = []

    if results.lint_exit_code != 0 and results.lint_output:
        messages.append("\n[Ruff Lint]\n")
        messages.append(results.lint_output)
        messages.append("\n")

    if results.format_exit_code != 0 and results.format_output:
        messages.append("\n[Ruff Format]\n")
        messages.append(results.format_output)
        messages.append("\n")

    return messages


def find_ruff_executable() -> tuple[str | None, bool]:
    if venv_ruff := next((p for p in VENV_RUFF_PATHS if p.exists()), None):
        return str(venv_ruff.absolute()), False

    system_ruff = shutil.which("ruff")
    if system_ruff:
        return system_ruff, False

    return None, True


def should_use_fallback_config() -> bool:
    if not PYPROJECT_PATH.exists():
        return True

    try:
        with open(PYPROJECT_PATH) as f:
            config: PyprojectConfig = toml.load(f)

        has_ruff_config = "tool" in config and "ruff" in config["tool"]
        if not has_ruff_config:
            return True

        ruff_config = config["tool"]["ruff"]
        has_lint_select = "lint" in ruff_config and "select" in ruff_config["lint"]
        has_line_length = "line-length" in ruff_config

        return not (has_lint_select or has_line_length)
    except (OSError, toml.TomlDecodeError, KeyError, TypeError):
        return True


def get_python_version() -> str:
    if not PYPROJECT_PATH.exists():
        return _get_current_python_version()

    try:
        with open(PYPROJECT_PATH) as f:
            config: PyprojectConfig = toml.load(f)

        target_version = _get_ruff_target_version(config)
        if target_version:
            return target_version

        project_version = _get_project_python_version(config)
        if project_version:
            return project_version

        return _get_current_python_version()
    except (OSError, toml.TomlDecodeError, KeyError, TypeError):
        return _get_current_python_version()


def get_fallback_args() -> tuple[list[str], list[str]]:
    all_rules = FALLBACK_LINT_RULES + ALWAYS_ENFORCE_RULES

    lint_args = [
        RUFF_FLAG_SELECT,
        ",".join(all_rules),
        RUFF_FLAG_EXCLUDE,
        ",".join(FALLBACK_EXCLUDE_PATHS),
        RUFF_FLAG_LINE_LENGTH,
        str(FALLBACK_LINE_LENGTH),
    ]

    format_args = [
        RUFF_FLAG_LINE_LENGTH,
        str(FALLBACK_LINE_LENGTH),
    ]

    python_version = get_python_version()
    lint_args.extend([RUFF_FLAG_TARGET_VERSION, python_version])
    format_args.extend([RUFF_FLAG_TARGET_VERSION, python_version])

    return lint_args, format_args


def run_ruff_command(ruff_path: str, args: list[str], cwd: str) -> tuple[str, int]:
    try:
        result = subprocess.run(
            [ruff_path] + args,
            check=False,
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        return result.stdout + result.stderr, result.returncode
    except (FileNotFoundError, subprocess.SubprocessError) as e:
        return f"Error running ruff: {e}", 1


def _get_current_python_version() -> str:
    return f"py{sys.version_info.major}{sys.version_info.minor}"


def _extract_version_from_string(requires_python: str) -> str | None:
    if version_match := VERSION_WITH_OPERATOR_PATTERN.search(requires_python):
        return version_match.group(1)
    if version_match := VERSION_WITHOUT_OPERATOR_PATTERN.match(requires_python.strip()):
        return version_match.group(1)
    return None


def _format_python_version(version: str) -> str | None:
    version_parts = version.split(".")[:2]
    if len(version_parts) < 2:
        return None

    major, minor = version_parts[0], version_parts[1]
    return f"py{major}{minor}"


def _get_ruff_target_version(config: PyprojectConfig) -> str | None:
    match config:
        case {"tool": {"ruff": {"target-version": str(version)}}}:
            return version
        case _:
            return None


def _get_project_python_version(config: PyprojectConfig) -> str | None:
    match config:
        case {"project": {"requires-python": str(requires_python)}} if requires_python:
            version = _extract_version_from_string(requires_python)
            if version:
                return _format_python_version(version)
            return None
        case _:
            return None


def run_basedpyright_check(file_path: str, cwd: str) -> list[str]:
    basedpyright_path = find_basedpyright_executable()
    if not basedpyright_path:
        return []

    project_root = find_project_root(Path(file_path))
    if has_mypy_config(project_root):
        return []

    output, exit_code = run_basedpyright_command(basedpyright_path, file_path, cwd)
    if exit_code != 0 and output:
        return ["\n[Basedpyright]\n", output, "\n"]

    return []


def find_basedpyright_executable() -> str | None:
    venv_paths = [
        Path(".venv/bin/basedpyright"),
        Path("venv/bin/basedpyright"),
    ]

    for venv_path in venv_paths:
        if venv_path.exists():
            return str(venv_path.absolute())

    return shutil.which("basedpyright")


def run_basedpyright_command(basedpyright_path: str, file_path: str, cwd: str) -> tuple[str, int]:
    try:
        result = subprocess.run(
            [basedpyright_path, "--level", "error", file_path],
            check=False,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=60.0,
        )
        return result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "Basedpyright timed out", 2
    except (FileNotFoundError, subprocess.SubprocessError) as e:
        return f"Error running basedpyright: {e}", 2


def find_project_root(file_path: Path) -> Path:
    current = file_path.parent

    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        current = current.parent

    return file_path.parent


def has_mypy_config(project_root: Path) -> bool:
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, encoding="utf-8") as f:
                data = toml.loads(f.read())

            if "tool" in data and "mypy" in data["tool"]:
                return True
        except Exception:
            pass

    mypy_ini = project_root / "mypy.ini"
    if mypy_ini.exists():
        return True

    setup_cfg = project_root / "setup.cfg"
    if setup_cfg.exists():
        try:
            with open(setup_cfg, encoding="utf-8") as f:
                content = f.read()
                if "[mypy" in content:
                    return True
        except Exception:
            pass

    return False


def run_opinionated_checks(file_path: str) -> list[str]:
    try:
        with open(file_path, encoding="utf-8") as f:
            code = f.read()
    except Exception:
        return []

    errors: list[str] = []

    nested_import_errors = check_nested_imports(code, file_path)
    if nested_import_errors:
        errors.extend(nested_import_errors)

    any_return_errors = check_any_return(code, file_path)
    if any_return_errors:
        errors.extend(any_return_errors)

    return errors


def check_nested_imports(code: str, file_path: str) -> list[str]:
    try:
        root: sg.SgRoot = sg.SgRoot(code, "python")
        node: sg.SgNode = root.root()

        violations: list[str] = []

        import_nodes: list[sg.SgNode] = node.find_all(pattern="import $MODULE")
        for import_node in import_nodes:
            parent_function = _find_parent_function(import_node)
            if parent_function:
                function_name = _extract_function_name(parent_function)
                module_name = _extract_module_from_import(import_node)
                line = import_node.range().start.line + 1
                violations.append(f"Line {line}: Import '{module_name}' inside function '{function_name}'")

        from_import_nodes: list[sg.SgNode] = node.find_all(pattern="from $MODULE import $$$ITEMS")
        for from_import_node in from_import_nodes:
            parent_function = _find_parent_function(from_import_node)
            if parent_function:
                function_name = _extract_function_name(from_import_node)
                module_name = _extract_module_from_from_import(from_import_node)
                line = from_import_node.range().start.line + 1
                violations.append(f"Line {line}: Import from '{module_name}' inside function '{function_name}'")

        if violations:
            messages = ["\n[Nested Imports]\n"]
            messages.extend(f"{v}\n" for v in violations)
            return messages

        return []
    except Exception:
        return []


def check_any_return(code: str, file_path: str) -> list[str]:
    try:
        root: sg.SgRoot = sg.SgRoot(code, "python")
        node: sg.SgNode = root.root()

        violations: list[str] = []

        patterns = [
            "def $FUNC($$$PARAMS) -> Any:",
            "async def $FUNC($$$PARAMS) -> Any:",
            "def $FUNC($$$PARAMS) -> Optional[Any]:",
            "async def $FUNC($$$PARAMS) -> Optional[Any]:",
            "def $FUNC($$$PARAMS) -> Any | None:",
            "async def $FUNC($$$PARAMS) -> Any | None:",
        ]

        for pattern in patterns:
            function_nodes: list[sg.SgNode] = node.find_all(pattern=pattern)
            for function_node in function_nodes:
                func_match: sg.SgNode | None = function_node.get_match("FUNC")
                if func_match:
                    function_name = func_match.text()
                    line = function_node.range().start.line + 1
                    violations.append(f"Line {line}: Function '{function_name}' has '-> Any' return type")

        if violations:
            messages = ["\n[Any Return Type]\n"]
            messages.extend(f"{v}\n" for v in violations)
            return messages

        return []
    except Exception:
        return []


def _find_parent_function(node: sg.SgNode) -> sg.SgNode | None:
    current: sg.SgNode | None = node.parent()
    while current:
        if current.kind() == "function_definition":
            return current
        current = current.parent()
    return None


def _extract_function_name(function_node: sg.SgNode) -> str:
    name_node: sg.SgNode | None = function_node.field("name")
    if name_node:
        return name_node.text()
    return "unknown"


def _extract_module_from_import(import_node: sg.SgNode) -> str:
    module_match: sg.SgNode | None = import_node.get_match("MODULE")
    if module_match:
        return module_match.text()
    return "unknown"


def _extract_module_from_from_import(from_import_node: sg.SgNode) -> str:
    module_match: sg.SgNode | None = from_import_node.get_match("MODULE")
    if module_match:
        return module_match.text()
    return "unknown"


if __name__ == "__main__":
    main()
