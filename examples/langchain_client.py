"""Local LangChain agent that consumes the Product Assistant MCP server."""

import argparse
import asyncio
import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv

from model_providers import ModelSettings, create_model


DEFAULT_PROMPT = (
    "We have 22 users, 5 projects, and about 100,000 API requests per month. "
    "Which product plan fits us, and what would it cost monthly?"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ask a local model about the Product Assistant catalog."
    )
    parser.add_argument("prompt", nargs="?", default=DEFAULT_PROMPT)
    return parser.parse_args()


async def run(prompt: str, settings: ModelSettings) -> str:
    project_root = Path(__file__).resolve().parents[1]

    # The adapter launches the MCP server as a child process over stdio. Using
    # ``uv run`` means the server gets the same locked environment as this repo.
    mcp_client = MultiServerMCPClient(
        {
            "product_assistant": {
                "transport": "stdio",
                "command": "uv",
                "args": [
                    "--directory",
                    str(project_root),
                    "run",
                    "product-assistant-mcp",
                ],
            }
        }
    )

    # MCP tools become ordinary LangChain tools. Resources are read separately
    # and supplied as grounded catalog context because models cannot call MCP
    # resources as tools by themselves.
    tools, resources = await asyncio.gather(
        mcp_client.get_tools(server_name="product_assistant"),
        mcp_client.get_resources("product_assistant"),
    )
    catalog = "\n\n".join(resource.as_string() for resource in resources)

    model = create_model(settings)
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=(
            "You are a product assistant. Answer only from the MCP catalog below. "
            "Use the MCP tools for every cost estimate or formal quote; never do "
            "pricing arithmetic yourself. If required details are missing, ask a "
            "short follow-up question. Explain any invalid plan limits.\n\n"
            f"MCP catalog:\n{catalog}"
        ),
    )

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": prompt}]}
    )
    return str(result["messages"][-1].content)


async def main() -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    args = parse_args()
    try:
        settings = ModelSettings.from_env()
        answer = await run(args.prompt, settings)
    except Exception as exc:
        print(f"Client failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())
