"""Utilities for managing git ignore patterns."""

from __future__ import annotations

from pathlib import Path


def is_duplicate_pattern(existing_content: str, pattern: str) -> bool:
    """Check if pattern already exists (exact match only).

    Args:
        existing_content: Full file content
        pattern: Pattern to check

    Returns:
        True if pattern exists, False otherwise
    """
    # Check exact line match (with or without trailing newline)
    lines = existing_content.splitlines()
    return pattern in lines or pattern.strip() in lines


def add_patterns_to_file(file_path: Path, patterns: list[str]) -> list[str]:
    """Add patterns to file, return list of added patterns.

    Args:
        file_path: Target file path
        patterns: List of patterns to add

    Returns:
        List of patterns that were actually added (excluding duplicates)
    """
    # Read existing content
    if file_path.exists():
        existing_content = file_path.read_text()
    else:
        existing_content = ""

    # Filter out duplicates
    new_patterns = [p for p in patterns if not is_duplicate_pattern(existing_content, p)]

    if not new_patterns:
        return []

    # Append new patterns (with newline before if file doesn't end with one)
    content_to_add = ""
    if existing_content and not existing_content.endswith("\n"):
        content_to_add = "\n"
    content_to_add += "\n".join(new_patterns) + "\n"

    file_path.write_text(existing_content + content_to_add)
    return new_patterns
