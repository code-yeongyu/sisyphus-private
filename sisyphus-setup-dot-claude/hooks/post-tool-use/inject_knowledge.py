#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "orjson",
# ]
# ///
# pyright: reportMissingImports=false, reportUnknownArgumentType=false, reportUnreachable=false

from __future__ import annotations

import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict, cast

import orjson


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


class ToolUseBlock(TypedDict):
    type: Literal["tool_use"]
    name: Literal["Read"] | str
    id: str
    input: dict[str, Any]


class ToolResultBlock(TypedDict):
    type: Literal["tool_result"]
    tool_use_id: str
    content: str | list[dict[str, Any]]
    is_error: NotRequired[bool]


class TextBlock(TypedDict):
    type: Literal["text"]
    text: str


ContentBlock = ToolUseBlock | ToolResultBlock | TextBlock


class AssistantMessage(TypedDict):
    role: Literal["assistant"]
    content: list[ContentBlock]


class UserMessage(TypedDict):
    role: Literal["user"]
    content: str | list[ContentBlock]


class TranscriptEntry(TypedDict):
    type: Literal["user", "assistant"]
    message: AssistantMessage | UserMessage
    timestamp: NotRequired[str]


class RawTranscriptEntry(TypedDict):
    type: str
    message: dict[str, Any]
    timestamp: NotRequired[str]


class KnowledgeInfo(TypedDict):
    path: str
    distance: int
    type: str
    hash: str
    last_modified: str


class KnowledgeFinder:
    KNOWLEDGE_FILES = ["claude.md", "agents.md"]

    def __init__(self, file_path: str, cwd: str | None = None) -> None:
        self.file_path = Path(file_path).resolve()
        self.project_root = Path(cwd).resolve() if cwd else self._find_project_root()

    def _find_project_root(self) -> Path:
        markers = [".git", "pyproject.toml", "package.json", ".venv"]
        current = self.file_path.parent

        while current != current.parent:
            for marker in markers:
                if (current / marker).exists():
                    return current
            current = current.parent

        return self.file_path.parent

    def find_knowledge_files(self) -> list[KnowledgeInfo]:
        if not self.project_root:
            return []

        try:
            _ = self.file_path.relative_to(self.project_root)
        except ValueError:
            return []

        # === PHASE 1: Collect all candidate files with distances ===
        candidates: list[tuple[Path, int]] = []
        current_dir = self.file_path.parent
        distance = 0

        while current_dir >= self.project_root and current_dir != current_dir.parent:
            # Skip project root as it's automatically read by the system
            if current_dir != self.project_root:
                for file in current_dir.iterdir():
                    if file.is_file() and file.name.lower() in self.KNOWLEDGE_FILES:
                        candidates.append((file, distance))

            if current_dir == self.project_root:
                break

            current_dir = current_dir.parent
            distance += 1

        # === PHASE 2: Deduplicate by resolved path (symlink deduplication) ===
        # Key: resolved path string, Value: (original path, distance)
        unique_by_realpath: dict[str, tuple[Path, int]] = {}

        for file_path, dist in candidates:
            try:
                real_path = file_path.resolve()
                real_path_str = str(real_path)

                if real_path_str in unique_by_realpath:
                    existing_path, existing_dist = unique_by_realpath[real_path_str]

                    # Keep the better one based on:
                    # 1. Closer distance
                    # 2. Same distance but has "agents" in name
                    should_replace = False

                    if dist < existing_dist:
                        should_replace = True
                    elif dist == existing_dist:
                        # Prefer agents.md
                        has_agents = "agents" in file_path.name.lower()
                        existing_has_agents = "agents" in existing_path.name.lower()
                        if has_agents and not existing_has_agents:
                            should_replace = True

                    if should_replace:
                        unique_by_realpath[real_path_str] = (file_path, dist)
                else:
                    unique_by_realpath[real_path_str] = (file_path, dist)

            except OSError:
                # Skip files that can't be resolved (circular symlinks, etc.)
                continue

        # === PHASE 3: Group by content hash ===
        # Key: SHA256 hash of stripped content
        # Value: list of (original_path, distance, resolved_path_str)
        content_groups: dict[str, list[tuple[Path, int, str]]] = {}

        for real_path_str, (file_path, dist) in unique_by_realpath.items():
            try:
                # Read from the real file
                real_path = Path(real_path_str)
                content = real_path.read_text(encoding="utf-8").strip()
                content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

                if content_hash not in content_groups:
                    content_groups[content_hash] = []

                content_groups[content_hash].append((file_path, dist, real_path_str))

            except OSError:
                # Skip files that can't be read
                continue

        # === PHASE 4: Select one file per content group ===
        selected_files: list[tuple[Path, int, str]] = []

        for content_hash, group in content_groups.items():
            # Sort by priority:
            # 1. Has "agents" in filename (descending - True first)
            # 2. Distance (ascending - smaller first)
            def priority_key(item: tuple[Path, int, str]) -> tuple[bool, int]:
                file_path, dist, _ = item
                has_agents = "agents" in file_path.name.lower()
                return (not has_agents, dist)  # not has_agents: False < True, so agents comes first

            group.sort(key=priority_key)
            selected_files.append(group[0])  # Pick the best one

        # === PHASE 5: Create KnowledgeInfo objects ===
        knowledge_infos: list[KnowledgeInfo] = []

        for file_path, dist, real_path_str in selected_files:
            try:
                relative_path = file_path.relative_to(self.project_root)
                path_str = str(relative_path)
            except ValueError:
                path_str = str(file_path)

            # Determine file type from filename
            file_type = "claude" if "claude" in file_path.name.lower() else "agents"

            # Read metadata
            try:
                real_path = Path(real_path_str)
                file_content = real_path.read_bytes()
                file_hash = hashlib.sha256(file_content).hexdigest()[:16]
                last_modified = datetime.fromtimestamp(real_path.stat().st_mtime).isoformat()
            except OSError:
                file_hash = "unknown"
                last_modified = "unknown"

            knowledge_infos.append(
                KnowledgeInfo(
                    path=path_str,
                    distance=dist,
                    type=file_type,
                    hash=file_hash,
                    last_modified=last_modified,
                )
            )

        return sorted(knowledge_infos, key=lambda x: x["distance"])


class KnowledgeInjector:
    TODOS_DIR = Path.home() / ".claude" / "todos"

    def __init__(self, project_root: Path, transcript_path: str, session_id: str) -> None:
        self.project_root = project_root
        self.transcript_path = Path(transcript_path)
        self.session_id = session_id

    def _generate_todo_id(self, knowledge_info: KnowledgeInfo) -> str:
        """Generate todo ID for a knowledge file."""
        distance = knowledge_info["distance"]
        knowledge_type = knowledge_info["type"]
        path_id = knowledge_info["path"].replace("/", "-").replace(".md", "")
        return f"read-knowledge-d{distance}-{knowledge_type}-{path_id}"

    def _mark_todo_completed(self, todo_id: str) -> None:
        """Mark an existing todo item as completed."""
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

        knowledge_original = str(knowledge_path)
        try:
            knowledge_resolved = str(knowledge_path.resolve())
        except OSError:
            knowledge_resolved = knowledge_original

        for todo in todos:
            todo_id = todo.get("id", "")
            if not todo_id.startswith("read-knowledge-"):
                continue

            if todo.get("status") == "completed":
                continue

            todo_content = todo.get("content", "")

            if knowledge_original in todo_content or knowledge_resolved in todo_content:
                todo["status"] = "completed"
                modified = True
                continue

            try:
                parts = todo_content.split(": ", 1)
                if len(parts) == 2:
                    todo_file_path = parts[1].strip()

                    try:
                        todo_file_resolved = str(Path(todo_file_path).resolve())

                        if todo_file_resolved == knowledge_resolved:
                            todo["status"] = "completed"
                            modified = True
                            continue
                    except OSError:
                        if todo_file_path == knowledge_original:
                            todo["status"] = "completed"
                            modified = True
                            continue
            except (ValueError, IndexError):
                pass

        if modified:
            try:
                _ = todo_file.write_bytes(orjson.dumps(todos, option=orjson.OPT_INDENT_2))
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

    def _has_knowledge_been_read(self, knowledge_path: Path) -> bool:
        if not self.transcript_path.exists():
            return False

        try:
            knowledge_original = str(knowledge_path)
            try:
                knowledge_resolved = str(knowledge_path.resolve())
            except OSError:
                knowledge_resolved = knowledge_original

            transcript_content = self.transcript_path.read_text(encoding="utf-8")

            for line in transcript_content.splitlines():
                if not line.strip():
                    continue

                try:
                    entry: RawTranscriptEntry = cast(RawTranscriptEntry, orjson.loads(line))
                except orjson.JSONDecodeError:
                    continue

                if not isinstance(entry, dict):
                    continue

                if entry.get("type") != "assistant":
                    continue

                message = entry.get("message")
                if not isinstance(message, dict):
                    continue

                if message.get("role") != "assistant":
                    continue

                content = message.get("content")
                if not isinstance(content, list):
                    continue

                for block in content:
                    if not isinstance(block, dict):
                        continue

                    if block.get("type") != "tool_use":
                        continue

                    if block.get("name") != "Read":
                        continue

                    tool_input = block.get("input")
                    if not isinstance(tool_input, dict):
                        continue

                    file_path_from_tool = tool_input.get("file_path")
                    if not file_path_from_tool:
                        continue

                    if file_path_from_tool == knowledge_original:
                        return True
                    if file_path_from_tool == knowledge_resolved:
                        return True

                    try:
                        tool_path_resolved = str(Path(file_path_from_tool).resolve())
                        if tool_path_resolved == knowledge_resolved:
                            return True
                    except OSError:
                        pass

            return False

        except OSError:
            return False

    def check_and_inject(self, knowledge_info: KnowledgeInfo) -> str:
        path = knowledge_info["path"]
        knowledge_type = knowledge_info["type"]

        full_path = self.project_root / path
        if not full_path.exists():
            return ""

        if self._has_knowledge_been_read(full_path):
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
    def handle(self) -> None:
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
            file_path = tool_input["file_path"]  # type: ignore[literal-required]
        elif "notebook_path" in tool_input:
            file_path = tool_input["notebook_path"]  # type: ignore[literal-required]

        if not file_path:
            print(f"[{hook_filename}] Skipping: No file path provided")
            sys.exit(0)

        if Path(file_path).resolve() == Path(__file__).resolve():
            print(f"[{hook_filename}] Skipping: Self-reference detected")
            sys.exit(0)

        if Path(file_path).name.lower() in ["claude.md", "agents.md"]:
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

        knowledge_infos = finder.find_knowledge_files()
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
        messages_to_inject: list[str] = []

        for knowledge_info in filtered_knowledge_infos:
            message = injector.check_and_inject(knowledge_info)
            if message:
                messages_to_inject.append(message)

        if messages_to_inject:
            combined_message = "\n\n".join(messages_to_inject)
            print(combined_message, file=sys.stderr)
            sys.exit(2)

        print(f"[{hook_filename}] Success: All knowledge files already in context")
        sys.exit(0)


def main() -> None:
    hook_filename = Path(__file__).stem.replace("_", "-")
    print(f"\n[{hook_filename}]", file=sys.stderr)

    handler = HookHandler()
    handler.handle()


if __name__ == "__main__":
    main()
