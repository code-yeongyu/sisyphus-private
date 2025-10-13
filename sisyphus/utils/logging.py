"""Logging utilities for Sisyphus."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path


class LoggerFactory:
    """Logger factory for creating agent/session-specific loggers."""

    @staticmethod
    def create_logger(
        agent_type: str,
        session_id: str | None = None,
        log_dir: Path = Path("./logs"),
    ) -> logging.Logger:
        """
        Create agent/session-specific logger.

        Args:
            agent_type: Type of agent (claude, opencode)
            session_id: Optional session ID for session-specific logging
            log_dir: Directory to store log files

        Returns:
            Configured logger instance

        Notes:
            - File handler: DEBUG level
            - Console handler: INFO level
            - Log file format: {agent}_{timestamp}_{tz}.log
            - If session_id is provided, uses it in log filename
        """
        # Create log directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)

        # Generate logger name
        if session_id:
            logger_name = f"sisyphus.{agent_type}.{session_id}"
        else:
            logger_name = f"sisyphus.{agent_type}"

        # Get or create logger
        logger = logging.getLogger(logger_name)

        # Avoid duplicate handlers if logger already exists
        if logger.handlers:
            return logger

        logger.setLevel(logging.DEBUG)

        # Generate log filename with timestamp
        now = datetime.now(UTC)
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        tz_str = now.strftime("%Z")

        if session_id:
            log_filename = f"{agent_type}_{session_id}_{timestamp}_{tz_str}.log"
        else:
            log_filename = f"{agent_type}_{timestamp}_{tz_str}.log"

        log_path = log_dir / log_filename

        # File handler (DEBUG level)
        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console handler (INFO level)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(levelname)s - %(message)s",
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # Prevent propagation to root logger
        logger.propagate = False

        return logger
