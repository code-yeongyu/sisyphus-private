#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "orjson",
# ]
# ///
# pyright: reportMissingImports=false, reportMissingModuleSource=false, reportUnreachable=false, reportImplicitRelativeImport=false

from __future__ import annotations

import asyncio
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict, cast

import orjson

sys.path.insert(0, str(Path(__file__).parent))
from _shared_transcript_analyzer import TranscriptAnalyzer


class EditOperation(TypedDict):
    old_string: str
    new_string: str


class WriteToolInput(TypedDict):
    file_path: str
    content: str


class MultiEditToolInput(TypedDict):
    file_path: str
    edits: list[EditOperation]


class EditToolInput(TypedDict):
    file_path: str
    old_string: str
    new_string: str


class NotebookEditToolInput(TypedDict):
    notebook_path: str
    new_source: str


class PostToolUseInput(TypedDict):
    session_id: str
    tool_name: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    tool_input: WriteToolInput | EditToolInput | MultiEditToolInput | NotebookEditToolInput
    tool_response: dict[str, Any]


class KnowledgeInfo(TypedDict):
    path: str
    distance: int
    type: str
    hash: str
    last_modified: str


class KnowledgeFinder:
    KNOWLEDGE_FILES = ["readme.md"]

    def __init__(self, file_path: str, cwd: str) -> None:
        self.file_path = Path(file_path).resolve()
        self.project_root = Path(cwd).resolve()

    async def find_knowledge_files(self) -> list[KnowledgeInfo]:
        if not self.project_root:
            return []

        try:
            _ = self.file_path.relative_to(self.project_root)
        except ValueError:
            return []

        knowledge_infos: list[KnowledgeInfo] = []
        seen_files: set[str] = set()
        current_dir = self.file_path.parent
        distance = 0

        while current_dir >= self.project_root and current_dir != current_dir.parent:
            for file in current_dir.iterdir():
                if file.is_file() and file.name.lower() in self.KNOWLEDGE_FILES:
                    try:
                        relative_path = file.relative_to(self.project_root)
                        path_str = str(relative_path)
                    except ValueError:
                        path_str = str(file)

                    normalized_path = path_str.lower()
                    if normalized_path not in seen_files:
                        seen_files.add(normalized_path)
                        file_type = "readme"

                        try:
                            content_hash = await self._hash_file_content(file)
                            last_modified = datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                        except OSError:
                            content_hash = "unknown"
                            last_modified = "unknown"

                        knowledge_infos.append(
                            KnowledgeInfo(
                                path=path_str,
                                distance=distance,
                                type=file_type,
                                hash=content_hash,
                                last_modified=last_modified,
                            )
                        )

            if current_dir == self.project_root:
                break

            current_dir = current_dir.parent
            distance += 1

        return sorted(knowledge_infos, key=lambda x: x["distance"])

    @staticmethod
    async def _hash_file_content(file_path: Path) -> str:
        try:
            content = file_path.read_text(encoding="utf-8")
            stripped = content.strip()
            return hashlib.sha256(stripped.encode("utf-8")).hexdigest()[:16]
        except OSError:
            return "error"


class KnowledgeInjector:
    TODOS_DIR = Path.home() / ".claude" / "todos"

    def __init__(self, project_root: Path, transcript_path: str, session_id: str) -> None:
        self.project_root = project_root
        self.transcript_path = Path(transcript_path)
        self.session_id = session_id

    def _generate_todo_id(self, knowledge_info: KnowledgeInfo) -> str:
        distance = knowledge_info["distance"]
        knowledge_type = knowledge_info["type"]
        path_id = knowledge_info["path"].replace("/", "-").replace(".md", "")
        return f"read-knowledge-d{distance}-{knowledge_type}-{path_id}"

    def _mark_todo_completed(self, todo_id: str) -> None:
        self.TODOS_DIR.mkdir(parents=True, exist_ok=True)
        todo_file = self.TODOS_DIR / f"{self.session_id}-agent-{self.session_id}.json"

        if not todo_file.exists():
            return

        try:
            todos: list[dict[str, Any]] = cast(list[dict[str, Any]], orjson.loads(todo_file.read_bytes()))
        except (orjson.JSONDecodeError, OSError):
            return

        for todo in todos:
            if todo.get("id") == todo_id:
                if todo.get("status") != "completed":
                    todo["status"] = "completed"
                break

        try:
            _ = todo_file.write_bytes(cast(bytes, orjson.dumps(todos, option=orjson.OPT_INDENT_2)))
        except OSError:
            pass

    def _check_and_complete_existing_todos(self, knowledge_path: Path) -> None:
        todo_file = self.TODOS_DIR / f"{self.session_id}-agent-{self.session_id}.json"

        if not todo_file.exists():
            return

        try:
            todos: list[dict[str, Any]] = cast(list[dict[str, Any]], orjson.loads(todo_file.read_bytes()))
        except (orjson.JSONDecodeError, OSError):
            return

        if not isinstance(todos, list):
            return

        modified = False
        knowledge_path_str = str(knowledge_path.resolve())

        for todo in todos:
            todo_id = todo.get("id", "")
            if not todo_id.startswith("read-knowledge-"):
                continue

            if todo.get("status") == "completed":
                continue

            todo_content = todo.get("content", "")
            if knowledge_path_str in todo_content:
                todo["status"] = "completed"
                modified = True

        if modified:
            try:
                _ = todo_file.write_bytes(cast(bytes, orjson.dumps(todos, option=orjson.OPT_INDENT_2)))
            except OSError:
                pass

    def _add_todo_item(self, knowledge_info: KnowledgeInfo) -> None:
        self.TODOS_DIR.mkdir(parents=True, exist_ok=True)
        todo_file = self.TODOS_DIR / f"{self.session_id}-agent-{self.session_id}.json"

        try:
            if todo_file.exists():
                todos: list[dict[str, Any]] = cast(list[dict[str, Any]], orjson.loads(todo_file.read_bytes()))
            else:
                todos = []
        except (orjson.JSONDecodeError, OSError):
            todos = []

        full_path = self.project_root / knowledge_info["path"]
        knowledge_type = knowledge_info["type"].upper()
        todo_id = self._generate_todo_id(knowledge_info)

        todo_item = {
            "content": f"Read {knowledge_type} knowledge: {full_path}",
            "status": "pending",
            "priority": "high",
            "id": todo_id,
        }

        for existing_todo in todos:
            if existing_todo.get("id") == todo_item["id"]:
                return

        _ = todos.append(todo_item)

        knowledge_todos = [t for t in todos if t.get("id", "").startswith("read-knowledge-d")]
        other_todos = [t for t in todos if not t.get("id", "").startswith("read-knowledge-d")]

        def extract_distance(todo: dict[str, str]) -> int:
            todo_id = todo.get("id", "")
            parts = todo_id.split("-")
            if len(parts) >= 3 and parts[2].startswith("d"):
                try:
                    return int(parts[2][1:])
                except ValueError:
                    return 0
            return 0

        knowledge_todos.sort(key=extract_distance, reverse=True)

        todos[:] = other_todos + knowledge_todos

        try:
            _ = todo_file.write_bytes(cast(bytes, orjson.dumps(todos, option=orjson.OPT_INDENT_2)))
        except OSError:
            pass

    async def check_and_inject(
        self, knowledge_info: KnowledgeInfo, already_read: tuple[dict[str, str], set[str]]
    ) -> str:
        path = knowledge_info["path"]
        knowledge_type = knowledge_info["type"]

        full_path = self.project_root / path
        if not full_path.exists():
            return ""

        real_path = str(full_path.resolve())
        already_read_paths, already_read_hashes = already_read

        if real_path in already_read_paths:
            if already_read_paths[real_path] == knowledge_info["hash"]:
                todo_id = self._generate_todo_id(knowledge_info)
                self._mark_todo_completed(todo_id)
                return ""

        if knowledge_info["hash"] in already_read_hashes:
            todo_id = self._generate_todo_id(knowledge_info)
            self._mark_todo_completed(todo_id)
            return ""

        self._add_todo_item(knowledge_info)

        file_type_display = knowledge_type.upper()

        warning_message = (
            f"ACTION REQUIRED: Use Read tool to read {file_type_display} knowledge immediately. READ NOW.\n"
            f"You MUST read the following knowledge file before proceeding:\n"
            f"{full_path}\n\n"
            f"[Todo added to ~/.claude/todos/{self.session_id}-agent-{self.session_id}.json]\n"
        )

        return warning_message


class HookHandler:
    async def handle(self) -> None:
        hook_filename = Path(__file__).stem.replace("_", "-")

        try:
            input_raw = sys.stdin.read()
            if not input_raw:
                print(f"[{hook_filename}] Skipping: No input provided")
                sys.exit(0)

            data: PostToolUseInput = cast(PostToolUseInput, orjson.loads(input_raw))
        except (orjson.JSONDecodeError, KeyError, TypeError):
            print(f"[{hook_filename}] Skipping: Invalid input format")
            sys.exit(0)

        tool_name = data["tool_name"]
        tool_input = data["tool_input"]

        if tool_name not in [
            "Read",
            "Write",
            "Edit",
            "MultiEdit",
            "NotebookEdit",
        ]:
            print(f"[{hook_filename}] Skipping: Tool {tool_name} not relevant")
            sys.exit(0)

        file_path = ""
        if "file_path" in tool_input:
            file_path = tool_input["file_path"]
        elif "notebook_path" in tool_input:
            file_path = tool_input["notebook_path"]

        if not file_path:
            print(f"[{hook_filename}] Skipping: No file path provided")
            sys.exit(0)

        if Path(file_path).resolve() == Path(__file__).resolve():
            print(f"[{hook_filename}] Skipping: Self-reference detected")
            sys.exit(0)

        if Path(file_path).name.lower() == "readme.md":
            session_id = data["session_id"]
            transcript_path = data["transcript_path"]
            cwd = data["cwd"]

            knowledge_path = Path(file_path).resolve()
            finder = KnowledgeFinder(file_path, cwd)
            injector = KnowledgeInjector(finder.project_root, transcript_path, session_id)
            injector._check_and_complete_existing_todos(knowledge_path)

            print(f"[{hook_filename}] Success: Knowledge todos updated")
            sys.exit(0)

        cwd = data["cwd"]
        transcript_path = data["transcript_path"]
        finder = KnowledgeFinder(file_path, cwd)

        knowledge_infos = await finder.find_knowledge_files()
        if not knowledge_infos:
            print(f"[{hook_filename}] Success: No knowledge files found")
            sys.exit(0)

        current_file = Path(file_path)
        try:
            project_root = finder.project_root
            current_relative = current_file.relative_to(project_root)
            current_path_str = str(current_relative)
        except ValueError:
            current_path_str = str(current_file)

        filtered_knowledge_infos = [
            info for info in knowledge_infos if info["path"].lower() != current_path_str.lower()
        ]

        if not filtered_knowledge_infos:
            print(f"[{hook_filename}] Success: No relevant knowledge files found")
            sys.exit(0)

        session_id = data["session_id"]
        injector = KnowledgeInjector(finder.project_root, transcript_path, session_id)

        analyzer = TranscriptAnalyzer(Path(transcript_path))
        already_read = await analyzer.get_already_read_contents([".md"])

        tasks = [injector.check_and_inject(info, already_read) for info in filtered_knowledge_infos]
        messages = await asyncio.gather(*tasks)

        messages_to_inject = [msg for msg in messages if msg]

        if messages_to_inject:
            combined_message = "\n\n".join(messages_to_inject)
            print(combined_message, file=sys.stderr)
            sys.exit(2)

        print(f"[{hook_filename}] Success: All knowledge files already in context")
        sys.exit(0)


async def main() -> None:
    hook_filename = Path(__file__).stem.replace("_", "-")
    print(f"\n[{hook_filename}]", file=sys.stderr)

    handler = HookHandler()
    await handler.handle()


if __name__ == "__main__":
    asyncio.run(main())
