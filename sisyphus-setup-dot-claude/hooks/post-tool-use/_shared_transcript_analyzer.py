#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "orjson",
#     "aiofiles",
# ]
# ///
# pyright: reportMissingImports=false, reportMissingModuleSource=false

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import aiofiles
import orjson

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


class TranscriptAnalyzer:
    """Shared transcript analyzer for hash-based content deduplication."""

    def __init__(self, transcript_path: Path) -> None:
        self.transcript_path = transcript_path
        self._read_contents_cache: tuple[dict[str, str], set[str]] | None = None

    async def get_already_read_contents(
        self, file_extensions: list[str] | None = None
    ) -> tuple[dict[str, str], set[str]]:
        """
        Get already-read file contents with hash-based deduplication.

        Args:
            file_extensions: Filter by extensions (e.g., [".md", ".mdc"]). None = no filter.

        Returns:
            - dict[realpath_str, content_hash]: Map of resolved paths to their content hashes
            - set[content_hash]: Set of all content hashes that have been read
        """
        if self._read_contents_cache is not None:
            return self._read_contents_cache

        if not self.transcript_path.exists():
            self._read_contents_cache = ({}, set())
            return ({}, set())

        read_files: dict[str, str] = {}
        read_hashes: set[str] = set()

        try:
            async with aiofiles.open(self.transcript_path, encoding="utf-8") as f:
                content = await f.read()

            for line in content.splitlines():
                if not line.strip():
                    continue

                try:
                    entry = orjson.loads(line)
                except orjson.JSONDecodeError:
                    continue

                if not isinstance(entry, dict) or entry.get("type") != "assistant":
                    continue

                message = entry.get("message", {})
                if message.get("role") != "assistant":
                    continue

                for block in message.get("content", []):
                    if not isinstance(block, dict):
                        continue

                    if block.get("type") != "tool_use" or block.get("name") != "Read":
                        continue

                    tool_input = block.get("input", {})
                    file_path = tool_input.get("file_path")

                    if not file_path:
                        continue

                    # Filter by extension if specified
                    if file_extensions is not None:
                        if not any(file_path.endswith(ext) for ext in file_extensions):
                            continue

                    try:
                        path = Path(file_path)
                        if path.exists():
                            real_path = path.resolve()
                            content_hash = await self._hash_file_content(real_path)
                            read_files[str(real_path)] = content_hash
                            read_hashes.add(content_hash)
                    except OSError:
                        pass

        except OSError:
            pass

        self._read_contents_cache = (read_files, read_hashes)
        return (read_files, read_hashes)

    @staticmethod
    async def _hash_file_content(file_path: Path, strip_frontmatter: bool = False) -> str:
        """
        Hash file content with normalization.

        Args:
            file_path: Path to file
            strip_frontmatter: Whether to strip YAML frontmatter before hashing

        Returns:
            16-char SHA256 hash of stripped content
        """
        try:
            async with aiofiles.open(file_path, encoding="utf-8") as f:
                content = await f.read()

            if strip_frontmatter:
                _, content = parse_frontmatter(content)

            stripped = content.strip()
            return hashlib.sha256(stripped.encode("utf-8")).hexdigest()[:16]
        except OSError:
            return "error"


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with optional frontmatter

    Returns:
        (metadata_dict, markdown_content)
    """
    match = FRONTMATTER_PATTERN.match(content)

    if not match:
        return ({}, content)

    # yaml_str = match.group(1)
    markdown = match.group(2)

    # Note: Not parsing YAML to avoid dependency bloat
    # If needed, add pyyaml dependency and parse yaml_str
    return ({}, markdown)


async def hash_file_content_sync(file_path: Path, strip_frontmatter: bool = False) -> str:
    """Synchronous wrapper for hash_file_content (for compatibility)."""
    analyzer = TranscriptAnalyzer(Path("/dev/null"))
    return await analyzer._hash_file_content(file_path, strip_frontmatter)
