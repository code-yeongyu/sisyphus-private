"""Process management utilities for Sisyphus."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import anyio

from sisyphus.utils.errors import ProcessTimeoutError


class ProcessManager:
    """Subprocess management utility with timeout and graceful shutdown support."""

    @staticmethod
    async def run_with_timeout(
        cmd: list[str],
        timeout_seconds: float = 30.0,
    ) -> anyio.abc.Process:
        """
        Run a process with timeout.

        Args:
            cmd: Command and arguments to execute
            timeout_seconds: Timeout in seconds

        Returns:
            Started process instance

        Raises:
            ProcessTimeoutError: If process doesn't start within timeout
        """
        try:
            with anyio.fail_after(timeout_seconds):
                process = await anyio.open_process(cmd)
                return process
        except (TimeoutError, anyio.get_cancelled_exc_class()) as e:
            raise ProcessTimeoutError(f"Process did not start within {timeout_seconds}s: {cmd}") from e

    @staticmethod
    async def terminate_gracefully(
        process: anyio.abc.Process,
        timeout_seconds: float = 5.0,
    ) -> None:
        """
        Terminate process gracefully with SIGTERM, then SIGKILL if needed.

        Args:
            process: Process to terminate
            timeout_seconds: Time to wait for graceful termination before SIGKILL

        Raises:
            ProcessTimeoutError: If process doesn't terminate after SIGKILL
        """
        # Check if process already terminated
        if process.returncode is not None:
            return

        # Send SIGTERM
        try:
            process.terminate()
        except ProcessLookupError:
            # Process already terminated
            return

        # Wait for graceful termination
        with anyio.move_on_after(timeout_seconds) as scope:
            await process.wait()

        if not scope.cancel_called:
            return

        # Force kill with SIGKILL
        try:
            process.kill()
        except ProcessLookupError:
            # Process already terminated
            return

        # Wait for SIGKILL to take effect (with timeout)
        try:
            with anyio.fail_after(timeout_seconds):
                await process.wait()
        except (TimeoutError, anyio.get_cancelled_exc_class()) as e:
            raise ProcessTimeoutError(f"Process did not terminate after SIGKILL within {timeout_seconds}s") from e

    @staticmethod
    async def parse_jsonl_stream(
        stream: anyio.abc.ByteReceiveStream,
        max_line_size: int = 10_000_000,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Parse JSONL stream with error handling.

        Args:
            stream: Byte stream to parse
            max_line_size: Maximum line size in bytes

        Yields:
            Parsed JSON objects (dictionaries)

        Notes:
            - Skips lines that exceed max_line_size
            - Skips lines with invalid JSON
            - Handles partial lines at stream end
        """
        buffer = b""

        async for chunk in stream:
            buffer += chunk

            # Process complete lines
            while b"\n" in buffer:
                line_bytes, buffer = buffer.split(b"\n", 1)

                # Check line size
                if len(line_bytes) > max_line_size:
                    # Skip oversized line
                    continue

                # Skip empty lines
                if not line_bytes.strip():
                    continue

                # Parse JSON
                try:
                    line_str = line_bytes.decode("utf-8")
                    obj = json.loads(line_str)
                    if isinstance(obj, dict):
                        yield obj
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Skip invalid JSON or encoding errors
                    continue

        # Handle remaining buffer (incomplete line)
        if buffer.strip():
            if len(buffer) <= max_line_size:
                try:
                    line_str = buffer.decode("utf-8")
                    obj = json.loads(line_str)
                    if isinstance(obj, dict):
                        yield obj
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
