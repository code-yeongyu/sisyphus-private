#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "chardet>=5.2.0",
# ]
# ///
"""
Improved Corrupted encoding blocker hook for Claude Code.
Blocks edits that contain corrupted/broken encoding while supporting CJK languages.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any, NoReturn, NotRequired, TypedDict

import chardet  # pyright: ignore[reportMissingImports]


class Config:
    """Configuration constants for the hook."""

    EXIT_CODE_BLOCK_TOOL: int = 2
    TAB: str = "\t"
    REPLACEMENT_CHAR_THRESHOLD: int = 1  # Block if replacement char found
    TOTAL_REPLACEMENT_THRESHOLD: int = 5  # Reduced from 10 - more lenient for total count
    CONTROL_CHAR_THRESHOLD: int = 10  # Allow some control chars for ANSI codes
    MIN_CONFIDENCE_THRESHOLD: float = 0.3  # Minimum encoding confidence

    # Don't use HIGH_BYTE_RATIO check at all for CJK text
    HIGH_BYTE_RATIO_THRESHOLD: float = 0.98  # Only for non-CJK text


class Violation(TypedDict):
    line: int
    text: str
    issue_type: str
    full_line: str


class WriteToolInput(TypedDict):
    file_path: str
    content: str


class EditToolInput(TypedDict):
    file_path: str
    new_string: str
    old_string: NotRequired[str]


class EditEntry(TypedDict):
    new_string: str
    old_string: NotRequired[str]


class MultiEditToolInput(TypedDict):
    file_path: str
    edits: list[EditEntry]


class InputData(TypedDict):
    session_id: NotRequired[str]
    transcript_path: NotRequired[str]
    cwd: NotRequired[str]
    hook_event_name: NotRequired[str]
    tool_name: NotRequired[str]
    tool_input: NotRequired[WriteToolInput | EditToolInput | MultiEditToolInput]


def main() -> None:
    """Main entry point for the PreToolUse hook."""
    try:
        _execute_hook_pipeline()
    except Exception as e:
        _handle_hook_error(e)


def _execute_hook_pipeline() -> NoReturn:
    """Execute the main hook logic pipeline."""
    data = parse_input()
    if not should_process(data):
        sys.exit(0)

    violations = process_tool_input(data)
    file_path = extract_file_path(data)
    handle_findings(violations, file_path)


def parse_input() -> InputData:
    """Parse and validate stdin input."""
    input_raw = sys.stdin.read()
    if not input_raw.strip():
        sys.exit(0)

    try:
        parsed_data: InputData = json.loads(input_raw)
        return parsed_data
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error parsing input: {e}", file=sys.stderr)
        sys.exit(0)


def should_process(data: InputData) -> bool:
    """Determine if the input should be processed."""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input")

    if not tool_name or not tool_input:
        return False

    if not isinstance(tool_input, dict):
        return False

    # Only process Write, Edit, MultiEdit tools
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        return False

    # Process all file types for encoding issues
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return False

    return True


def process_tool_input(data: InputData) -> list[Violation]:
    """Process tool input and detect violations."""
    tool_name = data.get("tool_name", "")
    tool_input: Any = data.get("tool_input", {})

    if not isinstance(tool_input, dict):
        return []

    processors: dict[str, Any] = {
        "Write": _process_write_tool,
        "Edit": _process_edit_tool,
        "MultiEdit": _process_multiedit_tool,
    }

    processor = processors.get(tool_name)
    result: list[Violation] = processor(tool_input) if processor else []
    return result


def extract_file_path(data: InputData) -> str:
    """Extract file path from input data."""
    tool_input: Any = data.get("tool_input", {})
    if isinstance(tool_input, dict):
        file_path = tool_input.get("file_path", "")
        return file_path
    return ""


def handle_findings(violations: list[Violation], file_path: str) -> NoReturn:
    """Handle detected violations and exit appropriately."""
    if not violations:
        sys.exit(0)

    message = _build_error_message(violations, file_path)

    if message.strip():
        print(message, file=sys.stderr)
        sys.exit(Config.EXIT_CODE_BLOCK_TOOL)

    sys.exit(0)


def _build_error_message(violations: list[Violation], file_path: str) -> str:
    """Build error message for encoding violations."""
    if not violations:
        return ""

    display_path = _get_display_path(file_path)

    msg_parts: list[str] = []
    msg_parts.append("CRITICAL ERROR: CORRUPTED ENCODING DETECTED\n")
    msg_parts.append("=" * 60 + "\n\n")
    msg_parts.append(f"File: {display_path}\n")
    msg_parts.append(f"Encoding issues found: {len(violations)}\n\n")
    msg_parts.append("IMPORTANT: You are an LLM - use human-readable text!\n")
    msg_parts.append("Do not generate corrupted characters or broken encoding.\n")
    msg_parts.append("Write clean, properly encoded text that humans can read.\n\n")
    msg_parts.append("The content you're trying to write contains corrupted or broken encoding.\n")
    msg_parts.append("This usually happens when:\n")
    msg_parts.append("  • Text was copied from a source with different encoding\n")
    msg_parts.append("  • Characters were corrupted during file transfer\n")
    msg_parts.append("  • Mixed encodings in the same content\n")
    msg_parts.append("  • LLM generated malformed characters\n\n")

    msg_parts.append("DETECTED VIOLATIONS:\n")
    msg_parts.append("-" * 60 + "\n")

    for violation in violations[:10]:
        issue_descriptions: dict[str, str] = {
            "replacement_chars": "Replacement characters (�) detected",
            "control_chars": "Excessive control characters",
            "high_byte_ratio": "Suspicious high-byte ratio (non-CJK text)",
            "encoding_confidence": "Low encoding confidence",
            "mixed_encoding": "Mixed encoding detected",
            "excessive_replacement_total": "Excessive total replacement characters in file",
        }
        issue_desc = issue_descriptions.get(violation["issue_type"], "Encoding issue")

        msg_parts.append(f"\n📍 Line {violation['line']}: {issue_desc}\n")

        # Show full line content with special characters escaped
        if violation.get("full_line"):
            full_line = violation["full_line"]
            # Make special characters visible
            display_line = (
                full_line.replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t")
                .replace("\x1b", "\\x1b")  # ESC character
            )
            # Display control characters
            for i in range(32):
                if i not in [9, 10, 13]:  # exclude tab, newline, carriage return
                    display_line = display_line.replace(chr(i), f"\\x{i:02x}")

            msg_parts.append("   Full line content:\n")
            msg_parts.append(f"   >>> {display_line[:200]}")
            if len(display_line) > 200:
                msg_parts.append("...")
            msg_parts.append("\n")

            # Highlight problematic characters
            if violation["issue_type"] == "replacement_chars":
                replacement_count = full_line.count("�")
                msg_parts.append(f"   Found {replacement_count} replacement character(s) '�'\n")
            elif violation["issue_type"] == "control_chars":
                control_chars = [f"\\x{ord(c):02x}" for c in full_line if ord(c) < 32 and c not in "\t\r\n"]
                msg_parts.append(f"   Control characters found: {', '.join(control_chars[:10])}")
                if len(control_chars) > 10:
                    msg_parts.append(f" ... and {len(control_chars) - 10} more")
                msg_parts.append("\n")

        # Also show text field for compatibility
        if violation["text"] and violation["text"] != violation.get("full_line", "")[:100]:
            text = violation["text"][:100]
            text = text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
            msg_parts.append(f"   Sample: {text}\n")

    if len(violations) > 10:
        msg_parts.append(f"\n... and {len(violations) - 10} more issues\n\n")

    msg_parts.append("\n" + "-" * 60 + "\n")
    msg_parts.append("RECOMMENDATIONS FOR YOU (LLM):\n")
    msg_parts.append("\t1. Generate fresh, clean text - don't copy corrupted content\n")
    msg_parts.append("\t2. Use only UTF-8 compatible characters\n")
    msg_parts.append("\t3. Avoid generating replacement characters (�)\n")
    msg_parts.append("\t4. Write human-readable text without control characters\n")
    msg_parts.append("\t5. If you see corrupted text, regenerate it properly\n\n")
    msg_parts.append("This operation has been BLOCKED.\n")
    msg_parts.append("As an LLM, you must generate properly encoded, human-readable text.\n")

    return "".join(msg_parts)


def _get_display_path(file_path: str) -> str:
    """Get display-friendly path relative to cwd if possible."""
    cwd = Path.cwd()
    try:
        path_obj = Path(file_path).resolve()
        if path_obj.is_relative_to(cwd):
            relative_path = path_obj.relative_to(cwd)
            result = str(relative_path)
            return result
        return file_path
    except (ValueError, OSError):
        return file_path


def _handle_hook_error(e: Exception) -> NoReturn:
    """Handle errors in hook execution."""
    print(f"ERROR in hook: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(0)


def has_cjk_characters(text: str) -> bool:
    """Check if text contains CJK (Chinese, Japanese, Korean) characters."""
    for char in text:
        code = ord(char)
        # Korean Hangul
        if 0xAC00 <= code <= 0xD7AF:
            return True
        # Korean Jamo
        if 0x1100 <= code <= 0x11FF or 0x3130 <= code <= 0x318F or 0xA960 <= code <= 0xA97F:
            return True
        # CJK Unified Ideographs (Chinese/Japanese Kanji)
        if 0x4E00 <= code <= 0x9FFF:
            return True
        # Japanese Hiragana and Katakana
        if 0x3040 <= code <= 0x309F or 0x30A0 <= code <= 0x30FF:
            return True
        # CJK Extensions
        if 0x3400 <= code <= 0x4DBF or 0x20000 <= code <= 0x2A6DF:
            return True
    return False


def detect_encoding_issues(content: str) -> list[Violation]:
    """Detect encoding issues in the given content."""
    violations: list[Violation] = []
    lines = content.split("\n")

    # Check if content has CJK characters
    has_cjk = has_cjk_characters(content)

    # Track total replacement characters across entire file
    total_replacement_chars = 0

    for line_num, line in enumerate(lines, 1):
        # Check for replacement characters - even 1 is suspicious
        replacement_count = line.count("\ufffd")  # Unicode replacement character
        total_replacement_chars += replacement_count

        # Also check for UTF-8 byte sequence of replacement character as text
        # This catches cases where the bytes are written as escape sequences
        utf8_replacement_pattern_count = line.count(r"\xef\xbf\xbd")
        utf8_replacement_pattern_count += line.count("\\xef\\xbf\\xbd")

        # Check for common corrupted byte patterns that appear as text
        # These often appear when binary data is incorrectly decoded
        suspicious_patterns = [
            r"\x80",
            r"\x81",
            r"\x82",
            r"\x83",
            r"\x84",
            r"\x85",
            r"\xff\xfe",
            r"\xfe\xff",  # BOM markers
            "\\x80",
            "\\x81",
            "\\x82",
            "\\x83",
            "\\x84",
            "\\x85",
        ]
        suspicious_count = sum(line.count(pat) for pat in suspicious_patterns)

        if replacement_count >= Config.REPLACEMENT_CHAR_THRESHOLD:
            violations.append(
                Violation(
                    line=line_num,
                    text=line[:100],
                    issue_type="replacement_chars",
                    full_line=line,
                )
            )
        elif utf8_replacement_pattern_count > 0:
            violations.append(
                Violation(
                    line=line_num,
                    text=line[:100],
                    issue_type="replacement_chars",
                    full_line=line,
                )
            )
        elif suspicious_count >= 3:  # Multiple suspicious patterns
            violations.append(
                Violation(
                    line=line_num,
                    text=line[:100],
                    issue_type="replacement_chars",
                    full_line=line,
                )
            )

        # Check for excessive control characters (excluding tab, newline, carriage return)
        control_chars = sum(1 for c in line if ord(c) < 32 and c not in "\t\r\n")
        if control_chars > Config.CONTROL_CHAR_THRESHOLD:
            violations.append(
                Violation(
                    line=line_num,
                    text=line[:100],
                    issue_type="control_chars",
                    full_line=line,
                )
            )

    # Check total replacement characters across entire file
    if total_replacement_chars >= Config.TOTAL_REPLACEMENT_THRESHOLD:
        violations.append(
            Violation(
                line=1,
                text=f"Total replacement chars: {total_replacement_chars}",
                issue_type="excessive_replacement_total",
                full_line=lines[0] if lines else "",
            )
        )

    # Check overall content for encoding issues
    try:
        # Try to encode/decode to detect issues
        content_bytes = content.encode("utf-8")

        # SKIP high byte ratio check for CJK text completely
        if not has_cjk:
            # Only check high byte ratio for non-CJK text
            high_bytes = sum(1 for byte in content_bytes if byte > 127)
            if len(content_bytes) > 0:
                ratio = high_bytes / len(content_bytes)
                if ratio > Config.HIGH_BYTE_RATIO_THRESHOLD:
                    first_line = lines[0] if lines else ""
                    violations.append(
                        Violation(
                            line=1,
                            text=f"High-byte ratio: {ratio:.2%}",
                            issue_type="high_byte_ratio",
                            full_line=first_line,
                        )
                    )

        # Use chardet to check encoding confidence
        # But be more lenient with CJK text
        detection_result = chardet.detect(content_bytes)

        # For CJK text, only flag if confidence is VERY low
        min_confidence_for_cjk = 0.1
        min_confidence_for_non_cjk = Config.MIN_CONFIDENCE_THRESHOLD

        threshold = min_confidence_for_cjk if has_cjk else min_confidence_for_non_cjk

        if detection_result["confidence"] < threshold:
            first_line = lines[0] if lines else ""
            violations.append(
                Violation(
                    line=1,
                    text=f"Low confidence: {detection_result['confidence']:.2f}",
                    issue_type="encoding_confidence",
                    full_line=first_line,
                )
            )
    except UnicodeEncodeError as e:
        violations.append(
            Violation(
                line=1,
                text=str(e)[:100],
                issue_type="mixed_encoding",
                full_line=lines[0] if lines else "",
            )
        )

    return violations


def _process_write_tool(tool_input: dict[str, Any]) -> list[Violation]:
    """Process Write tool input."""
    content = tool_input.get("content", "")
    result = detect_encoding_issues(content) if content else []
    return result


def _process_edit_tool(tool_input: dict[str, Any]) -> list[Violation]:
    """Process Edit tool input."""
    new_string = tool_input.get("new_string", "")
    if not new_string:
        return []

    violations = detect_encoding_issues(new_string)
    return violations


def _process_multiedit_tool(tool_input: dict[str, Any]) -> list[Violation]:
    """Process MultiEdit tool input."""
    violations: list[Violation] = []
    edits = tool_input.get("edits", [])

    for edit in edits:
        if isinstance(edit, dict):
            new_string = edit.get("new_string", "")
            if new_string:
                detected_violations = detect_encoding_issues(new_string)
                violations.extend(detected_violations)

    return violations


if __name__ == "__main__":
    main()
