#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "orjson",
#     "toml>=0.10.2",
# ]
# ///
# pyright: reportMissingImports=false, reportMissingModuleSource=false, reportImplicitRelativeImport=false

from __future__ import annotations

import asyncio
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

import orjson
import toml

sys.path.insert(0, str(Path(__file__).parent))
from _shared_transcript_analyzer import TranscriptAnalyzer


class ReadToolInput(TypedDict):
    file_path: str


class PostToolUseInput(TypedDict):
    session_id: str
    tool_name: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    tool_input: ReadToolInput
    tool_response: dict[str, Any]


class ConftestInfo(TypedDict):
    path: str
    distance: int
    hash: str
    last_modified: str


class ProjectRootFinder:
    PROJECT_ROOT_MARKERS = ["pyproject.toml", ".venv", ".git"]

    @classmethod
    def find_root(cls, start_path: Path) -> Path | None:
        current_dir = start_path.resolve()

        while current_dir != current_dir.parent:
            for marker in cls.PROJECT_ROOT_MARKERS:
                marker_path = current_dir / marker
                if marker_path.exists() and (marker_path.is_file() or marker_path.is_dir()):
                    return current_dir
            current_dir = current_dir.parent

        return None


class TestFileDetector:
    DEFAULT_TEST_PATTERNS = ["test_*.py", "*_test.py", "*_tests.py", "tests.py"]

    def __init__(self) -> None:
        self.test_patterns = self._load_test_patterns()

    def _load_test_patterns(self) -> list[str]:
        pyproject_path = Path("pyproject.toml")

        if not pyproject_path.exists():
            return self.DEFAULT_TEST_PATTERNS

        try:
            with open(pyproject_path, encoding="utf-8") as f:
                config: dict[str, Any] = toml.load(f)

            tool_config = config.get("tool", {})
            pytest_config = tool_config.get("pytest", {})
            ini_options = pytest_config.get("ini_options", {})

            python_files = ini_options.get("python_files", [])
            if isinstance(python_files, list) and python_files:
                return python_files

            return self.DEFAULT_TEST_PATTERNS
        except Exception:
            return self.DEFAULT_TEST_PATTERNS

    def is_test_file(self, file_path: str) -> bool:
        if not file_path.endswith(".py"):
            return False

        path = Path(file_path)
        file_name = path.name

        if (
            file_name.startswith("test_")
            or file_name.endswith("_test.py")
            or file_name.endswith("_tests.py")
            or file_name == "tests.py"
        ):
            return True

        for pattern in self.test_patterns:
            cleaned_pattern = pattern.replace("*", "")
            if cleaned_pattern in file_name:
                return True

        return False


class ConftestFinder:
    PACKAGE_CONFTEST_DISTANCE_OFFSET = 1000

    def __init__(self, test_file_path: str, cwd: str | None = None) -> None:
        self.test_file = Path(test_file_path).resolve()
        self.project_root = Path(cwd).resolve() if cwd else ProjectRootFinder.find_root(self.test_file.parent)

    async def find_conftests(self) -> list[ConftestInfo]:
        if not self.project_root:
            return []

        conftest_infos = await self._collect_upward_conftests()
        existing_paths = {info["path"] for info in conftest_infos}

        package_conftests = await self._collect_mirrored_package_conftests(existing_paths)
        conftest_infos.extend(package_conftests)

        return sorted(conftest_infos, key=lambda x: x["distance"])

    async def _collect_upward_conftests(self) -> list[ConftestInfo]:
        conftest_infos: list[ConftestInfo] = []

        if not self.project_root:
            return conftest_infos

        try:
            _ = self.test_file.relative_to(self.project_root)
        except ValueError:
            return conftest_infos

        current_dir = self.test_file.parent
        distance = 0

        while current_dir >= self.project_root and current_dir != current_dir.parent:
            conftest_path = current_dir / "conftest.py"
            if conftest_path.is_file():
                try:
                    relative_path = conftest_path.relative_to(self.project_root)
                    path_str = str(relative_path) if relative_path != Path(".") else "conftest.py"
                except ValueError:
                    path_str = str(conftest_path)

                try:
                    content_hash = await self._hash_file_content(conftest_path)
                    last_modified = datetime.fromtimestamp(conftest_path.stat().st_mtime).isoformat()
                except OSError:
                    content_hash = "unknown"
                    last_modified = "unknown"

                conftest_infos.append(
                    ConftestInfo(
                        path=path_str,
                        distance=distance,
                        hash=content_hash,
                        last_modified=last_modified,
                    )
                )

            if current_dir == self.project_root:
                break

            current_dir = current_dir.parent
            distance += 1

        return conftest_infos

    async def _collect_mirrored_package_conftests(self, existing_paths: set[str]) -> list[ConftestInfo]:
        conftest_infos: list[ConftestInfo] = []

        if not self.project_root:
            return conftest_infos

        try:
            relative_path = self.test_file.relative_to(self.project_root)
        except ValueError:
            return conftest_infos

        if not relative_path.parts or relative_path.parts[0] != "tests":
            return conftest_infos

        test_subdirectory_parts = list(relative_path.parts[1:-1])

        if not test_subdirectory_parts:
            return conftest_infos

        current_pkg_path = self.project_root

        for i, part in enumerate(test_subdirectory_parts):
            current_pkg_path = current_pkg_path / part
            pkg_conftest = current_pkg_path / "conftest.py"

            if pkg_conftest.is_file():
                try:
                    relative_path = pkg_conftest.relative_to(Path.cwd())
                    path_str = str(relative_path)
                except ValueError:
                    path_str = str(pkg_conftest)

                if path_str not in existing_paths:
                    try:
                        content_hash = await self._hash_file_content(pkg_conftest)
                        last_modified = datetime.fromtimestamp(pkg_conftest.stat().st_mtime).isoformat()
                    except OSError:
                        content_hash = "unknown"
                        last_modified = "unknown"

                    conftest_infos.append(
                        ConftestInfo(
                            path=path_str,
                            distance=self.PACKAGE_CONFTEST_DISTANCE_OFFSET + i,
                            hash=content_hash,
                            last_modified=last_modified,
                        )
                    )

        return conftest_infos

    @staticmethod
    async def _hash_file_content(file_path: Path) -> str:
        try:
            content = file_path.read_text(encoding="utf-8")
            stripped = content.strip()
            return hashlib.sha256(stripped.encode("utf-8")).hexdigest()[:16]
        except OSError:
            return "error"


class ConftestInjector:
    TODOS_DIR = Path.home() / ".claude" / "todos"

    def __init__(self, project_root: Path, transcript_path: str, session_id: str) -> None:
        self.project_root = project_root
        self.transcript_path = Path(transcript_path)
        self.session_id = session_id

    def _generate_todo_id(self, conftest_info: ConftestInfo) -> str:
        distance = conftest_info["distance"]
        path_id = conftest_info["path"].replace("/", "-").replace(".py", "")
        return f"read-conftest-d{distance}-{path_id}"

    def _mark_todo_completed(self, todo_id: str) -> None:
        self.TODOS_DIR.mkdir(parents=True, exist_ok=True)
        todo_file = self.TODOS_DIR / f"{self.session_id}-agent-{self.session_id}.json"

        if not todo_file.exists():
            return

        try:
            todos = orjson.loads(todo_file.read_bytes())
        except (orjson.JSONDecodeError, OSError):
            return

        for todo in todos:
            if todo.get("id") == todo_id:
                if todo.get("status") != "completed":
                    todo["status"] = "completed"
                break

        try:
            _ = todo_file.write_bytes(orjson.dumps(todos, option=orjson.OPT_INDENT_2))
        except OSError:
            pass

    def _check_and_complete_existing_todos(self, conftest_path: Path) -> None:
        todo_file = self.TODOS_DIR / f"{self.session_id}-agent-{self.session_id}.json"

        if not todo_file.exists():
            return

        try:
            todos = orjson.loads(todo_file.read_bytes())
        except (orjson.JSONDecodeError, OSError):
            return

        if not isinstance(todos, list):
            return

        modified = False
        conftest_path_str = str(conftest_path.resolve())

        for todo in todos:
            todo_id = todo.get("id", "")
            if not todo_id.startswith("read-conftest-"):
                continue

            if todo.get("status") == "completed":
                continue

            todo_content = todo.get("content", "")
            if conftest_path_str in todo_content:
                todo["status"] = "completed"
                modified = True

        if modified:
            try:
                _ = todo_file.write_bytes(orjson.dumps(todos, option=orjson.OPT_INDENT_2))
            except OSError:
                pass

    def _add_todo_item(self, conftest_info: ConftestInfo) -> None:
        self.TODOS_DIR.mkdir(parents=True, exist_ok=True)
        todo_file = self.TODOS_DIR / f"{self.session_id}-agent-{self.session_id}.json"

        try:
            if todo_file.exists():
                todos = orjson.loads(todo_file.read_bytes())
            else:
                todos = []
        except (orjson.JSONDecodeError, OSError):
            todos = []

        full_path = self.project_root / conftest_info["path"]
        todo_id = self._generate_todo_id(conftest_info)

        todo_item = {
            "content": f"Read conftest: {full_path}",
            "status": "pending",
            "priority": "high",
            "id": todo_id,
        }

        for existing_todo in todos:
            if existing_todo.get("id") == todo_item["id"]:
                return

        _ = todos.append(todo_item)

        conftest_todos = [t for t in todos if t.get("id", "").startswith("read-conftest-d")]
        other_todos = [t for t in todos if not t.get("id", "").startswith("read-conftest-d")]

        def extract_distance(todo: dict[str, str]) -> int:
            todo_id = todo.get("id", "")
            parts = todo_id.split("-")
            if len(parts) >= 3 and parts[2].startswith("d"):
                try:
                    return int(parts[2][1:])
                except ValueError:
                    return 0
            return 0

        conftest_todos.sort(key=extract_distance, reverse=True)

        todos[:] = other_todos + conftest_todos

        try:
            _ = todo_file.write_bytes(orjson.dumps(todos, option=orjson.OPT_INDENT_2))
        except OSError:
            pass

    async def check_and_inject(
        self, conftest_info: ConftestInfo, already_read: tuple[dict[str, str], set[str]]
    ) -> str:
        path = conftest_info["path"]

        full_path = self.project_root / path
        if not full_path.exists():
            return ""

        real_path = str(full_path.resolve())
        already_read_paths, already_read_hashes = already_read

        if real_path in already_read_paths:
            if already_read_paths[real_path] == conftest_info["hash"]:
                todo_id = self._generate_todo_id(conftest_info)
                self._mark_todo_completed(todo_id)
                return ""

        if conftest_info["hash"] in already_read_hashes:
            todo_id = self._generate_todo_id(conftest_info)
            self._mark_todo_completed(todo_id)
            return ""

        self._add_todo_item(conftest_info)

        warning_message = (
            f"ACTION REQUIRED: Use Read tool to read CONFTEST immediately. READ NOW.\n"
            f"You MUST read the following conftest file before proceeding with the test:\n"
            f"{full_path}\n\n"
            f"[Todo added to ~/.claude/todos/{self.session_id}-agent-{self.session_id}.json]\n"
        )

        return warning_message


class HookHandler:
    def __init__(self) -> None:
        self.test_detector = TestFileDetector()

    async def handle(self) -> None:
        hook_filename = Path(__file__).stem.replace("_", "-")

        try:
            input_raw = sys.stdin.read()
            if not input_raw:
                print(f"[{hook_filename}] Skipping: No input provided")
                sys.exit(0)

            data: PostToolUseInput = orjson.loads(input_raw)
        except (orjson.JSONDecodeError, KeyError, TypeError):
            print(f"[{hook_filename}] Skipping: Invalid input format")
            sys.exit(0)

        tool_name = data["tool_name"]
        tool_input = data["tool_input"]

        if tool_name != "Read":
            print(f"[{hook_filename}] Skipping: Tool {tool_name} not relevant")
            sys.exit(0)

        file_path = tool_input.get("file_path", "")

        if not file_path:
            print(f"[{hook_filename}] Skipping: No file path provided")
            sys.exit(0)

        if Path(file_path).resolve() == Path(__file__).resolve():
            print(f"[{hook_filename}] Skipping: Self-reference detected")
            sys.exit(0)

        if Path(file_path).name == "conftest.py":
            session_id = data["session_id"]
            transcript_path = data["transcript_path"]
            cwd = data["cwd"]

            conftest_path = Path(file_path).resolve()
            injector = ConftestInjector(conftest_path.parent, transcript_path, session_id)
            injector._check_and_complete_existing_todos(conftest_path)

            print(f"[{hook_filename}] Success: Conftest todos updated")
            sys.exit(0)

        if not self.test_detector.is_test_file(file_path):
            print(f"[{hook_filename}] Skipping: Not a test file")
            sys.exit(0)

        cwd = data["cwd"]
        transcript_path = data["transcript_path"]
        finder = ConftestFinder(file_path, cwd)

        if not finder.project_root:
            print(f"[{hook_filename}] Skipping: No project root found")
            sys.exit(0)

        conftest_infos = await finder.find_conftests()

        if not conftest_infos:
            print(f"[{hook_filename}] Success: No conftest files found")
            sys.exit(0)

        session_id = data["session_id"]
        injector = ConftestInjector(finder.project_root, transcript_path, session_id)

        analyzer = TranscriptAnalyzer(Path(transcript_path))
        already_read = await analyzer.get_already_read_contents([".py"])

        tasks = [injector.check_and_inject(info, already_read) for info in conftest_infos]
        messages = await asyncio.gather(*tasks)

        messages_to_inject = [msg for msg in messages if msg]

        if messages_to_inject:
            combined_message = "\n\n".join(messages_to_inject)
            print(combined_message, file=sys.stderr)
            sys.exit(2)

        print(f"[{hook_filename}] Success: All conftest files already in context")
        sys.exit(0)


async def main() -> None:
    hook_filename = Path(__file__).stem.replace("_", "-")
    print(f"\n[{hook_filename}]", file=sys.stderr)

    handler = HookHandler()
    await handler.handle()


if __name__ == "__main__":
    asyncio.run(main())
