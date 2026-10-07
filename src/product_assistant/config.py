"""Environment-backed configuration shared by the MCP server and clients."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_project_env() -> None:
    """Load the repository configuration without overriding process variables."""

    load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class MCPSettings:
    """MCP transport settings used by both ends of the connection."""

    transport: Literal["stdio", "streamable-http"]
    host: str
    port: int
    path: str
    server_url: str
    api_key: str

    @classmethod
    def from_env(cls) -> MCPSettings:
        load_project_env()

        configured_transport = os.getenv("MCP_TRANSPORT", "STDIO").strip().upper()
        transports: dict[str, Literal["stdio", "streamable-http"]] = {
            "STDIO": "stdio",
            "STREAMABLE_HTTP": "streamable-http",
            "STREAMABLE-HTTP": "streamable-http",
        }
        if configured_transport not in transports:
            raise ValueError(
                f"Unsupported MCP_TRANSPORT '{configured_transport}'. "
                "Choose STDIO or STREAMABLE_HTTP."
            )

        path = os.getenv("MCP_PATH", "/mcp").strip()
        if not path.startswith("/"):
            raise ValueError("MCP_PATH must start with '/'.")

        try:
            port = int(os.getenv("MCP_PORT", "8000"))
        except ValueError as exc:
            raise ValueError("MCP_PORT must be an integer.") from exc
        if not 1 <= port <= 65535:
            raise ValueError("MCP_PORT must be between 1 and 65535.")

        host = os.getenv("MCP_HOST", "127.0.0.1").strip()
        default_url = f"http://{host}:{port}{path}"
        return cls(
            transport=transports[configured_transport],
            host=host,
            port=port,
            path=path,
            server_url=os.getenv("MCP_SERVER_URL", default_url).strip(),
            api_key=os.getenv("MCP_API_KEY", "").strip(),
        )
