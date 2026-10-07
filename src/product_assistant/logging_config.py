"""Application logging configuration."""

from __future__ import annotations

import logging
import os
import sys


DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configure_logging() -> None:
    """Configure process-wide logging to stderr.

    stderr is required for the MCP stdio transport because stdout is reserved
    for protocol messages.
    """

    configured_level = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).strip().upper()
    level = getattr(logging, configured_level, None)
    if not isinstance(level, int):
        raise ValueError(
            f"Unsupported LOG_LEVEL '{configured_level}'. "
            "Choose DEBUG, INFO, WARNING, ERROR, or CRITICAL."
        )

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        stream=sys.stderr,
        force=True,
    )
