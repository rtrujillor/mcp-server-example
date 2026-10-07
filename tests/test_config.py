import pytest

from product_assistant.config import MCPSettings


def test_mcp_settings_defaults_to_stdio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_TRANSPORT", "STDIO")

    settings = MCPSettings.from_env()

    assert settings.transport == "stdio"


def test_mcp_settings_loads_streamable_http(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_TRANSPORT", "STREAMABLE_HTTP")
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("MCP_PORT", "9000")
    monkeypatch.setenv("MCP_PATH", "/product-mcp")
    monkeypatch.setenv("MCP_SERVER_URL", "https://mcp.example.com/product-mcp")
    monkeypatch.setenv("MCP_API_KEY", "secret")

    settings = MCPSettings.from_env()

    assert settings.transport == "streamable-http"
    assert settings.host == "0.0.0.0"
    assert settings.port == 9000
    assert settings.path == "/product-mcp"
    assert settings.server_url == "https://mcp.example.com/product-mcp"
    assert settings.api_key == "secret"


def test_mcp_settings_rejects_unknown_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MCP_TRANSPORT", "SSE")

    with pytest.raises(ValueError, match="Choose STDIO or STREAMABLE_HTTP"):
        MCPSettings.from_env()
