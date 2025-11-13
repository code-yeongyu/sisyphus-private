"""Tests for logging utilities."""

from __future__ import annotations

import logging
from pathlib import Path

from sisyphus.utils.logging import LoggerFactory


def test_create_logger_basic(tmp_path: Path) -> None:
    """Test basic logger creation."""
    # given
    agent_type = "test_agent"
    log_dir = tmp_path / "logs"

    # when
    logger = LoggerFactory.create_logger(agent_type, log_dir=log_dir)

    # then
    assert logger is not None
    assert logger.name == "sisyphus.test_agent"
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 2


def test_create_logger_with_session_id(tmp_path: Path) -> None:
    """Test logger creation with session ID."""
    # given
    agent_type = "claude"
    session_id = "test-session-123"
    log_dir = tmp_path / "logs"

    # when
    logger = LoggerFactory.create_logger(agent_type, session_id=session_id, log_dir=log_dir)

    # then
    assert logger is not None
    assert logger.name == "sisyphus.claude.test-session-123"


def test_create_logger_creates_directory(tmp_path: Path) -> None:
    """Test that logger creation creates log directory."""
    # given
    log_dir = tmp_path / "nested" / "log" / "dir"
    assert not log_dir.exists()

    # when
    LoggerFactory.create_logger("test_agent", log_dir=log_dir)

    # then
    assert log_dir.exists()
    assert log_dir.is_dir()


def test_create_logger_file_handler(tmp_path: Path) -> None:
    """Test file handler configuration."""
    # given
    log_dir = tmp_path / "logs"

    # when
    logger = LoggerFactory.create_logger("test_agent", log_dir=log_dir)

    # then
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) == 1

    file_handler = file_handlers[0]
    assert file_handler.level == logging.DEBUG


def test_create_logger_console_handler(tmp_path: Path) -> None:
    """Test console handler configuration."""
    # given
    log_dir = tmp_path / "logs"

    # when
    logger = LoggerFactory.create_logger("test_agent", log_dir=log_dir)

    # then
    console_handlers = [
        h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
    ]
    assert len(console_handlers) == 1

    console_handler = console_handlers[0]
    assert console_handler.level == logging.INFO


def test_create_logger_no_propagation(tmp_path: Path) -> None:
    """Test that logger doesn't propagate to root logger."""
    # given
    log_dir = tmp_path / "logs"

    # when
    logger = LoggerFactory.create_logger("test_agent", log_dir=log_dir)

    # then
    assert logger.propagate is False


def test_create_logger_reuses_existing(tmp_path: Path) -> None:
    """Test that calling create_logger twice returns same logger."""
    # given
    log_dir = tmp_path / "logs"

    # when
    logger1 = LoggerFactory.create_logger("test_agent", log_dir=log_dir)
    logger2 = LoggerFactory.create_logger("test_agent", log_dir=log_dir)

    # then
    assert logger1 is logger2
    # Should not duplicate handlers
    assert len(logger1.handlers) == 2


def test_create_logger_log_file_created(tmp_path: Path) -> None:
    """Test that log file is created with correct name pattern."""
    # given
    agent_type = "opencode"
    log_dir = tmp_path / "logs"

    # when
    logger = LoggerFactory.create_logger(agent_type, log_dir=log_dir)
    logger.debug("Test message")

    # then
    log_files = list(log_dir.glob("opencode_*.log"))
    assert len(log_files) >= 1

    # Verify log file contains message
    log_content = log_files[0].read_text()
    assert "Test message" in log_content


def test_create_logger_with_session_log_file(tmp_path: Path) -> None:
    """Test log file naming with session ID."""
    # given
    agent_type = "opencode"
    session_id = "ses_abc123"
    log_dir = tmp_path / "logs"

    # when
    logger = LoggerFactory.create_logger(agent_type, session_id=session_id, log_dir=log_dir)
    logger.info("Session log message")

    # then
    log_files = list(log_dir.glob(f"opencode_{session_id}_*.log"))
    assert len(log_files) >= 1


def test_create_logger_different_agents_separate_loggers(tmp_path: Path) -> None:
    """Test that different agents get separate loggers."""
    # given
    log_dir = tmp_path / "logs"

    # when
    logger1 = LoggerFactory.create_logger("claude", log_dir=log_dir)
    logger2 = LoggerFactory.create_logger("opencode", log_dir=log_dir)

    # then
    assert logger1 is not logger2
    assert logger1.name != logger2.name


def test_create_logger_file_handler_append_mode(tmp_path: Path) -> None:
    """Test that file handler uses append mode."""
    # given
    log_dir = tmp_path / "logs"

    # when
    logger = LoggerFactory.create_logger("test_agent", log_dir=log_dir)

    # then
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    file_handler = file_handlers[0]
    assert file_handler.mode == "a"
