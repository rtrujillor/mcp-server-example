"""Local LangChain agent that consumes the Product Assistant MCP server."""

import argparse
import asyncio
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

from model_providers import ModelSettings, create_model
from product_assistant.config import MCPSettings
from product_assistant.logging_config import configure_logging


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chat with a local model about the Product Assistant catalog."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Optional first message; subsequent messages are read interactively.",
    )
    return parser.parse_args()


def build_mcp_connection(
    settings: MCPSettings, project_root: Path
) -> dict[str, dict[str, Any]]:
    """Build the client connection for the selected MCP transport."""

    if settings.transport == "stdio":
        return {
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

    headers = {}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"
    return {
        "product_assistant": {
            "transport": "streamable_http",
            "url": settings.server_url,
            "headers": headers,
        }
    }


async def create_product_agent(
    model_settings: ModelSettings,
    mcp_settings: MCPSettings,
) -> Any:
    """Create one stateful agent for the lifetime of the console chat."""

    project_root = Path(__file__).resolve().parents[1]

    # stdio launches the server as a child process. Streamable HTTP connects to
    # an already-running server and never starts another server process.
    mcp_client = MultiServerMCPClient(
        build_mcp_connection(mcp_settings, project_root)
    )
    logger.info("Connecting to Product Assistant transport=%s", mcp_settings.transport)

    # MCP tools become ordinary LangChain tools. Resources are read separately
    # and supplied as grounded catalog context because models cannot call MCP
    # resources as tools by themselves.
    tools, resources = await asyncio.gather(
        mcp_client.get_tools(server_name="product_assistant"),
        mcp_client.get_resources("product_assistant"),
    )
    catalog = "\n\n".join(resource.as_string() for resource in resources)
    logger.info(
        "Loaded MCP capabilities tools=%d resources=%d",
        len(tools),
        len(resources),
    )

    model = create_model(model_settings)
    return create_agent(
        model=model,
        tools=tools,
        checkpointer= InMemorySaver(),
        system_prompt=(
            "You are a product assistant. Answer only from the MCP catalog below. "
            "Use the MCP tools for every cost estimate or formal quote; never do "
            "pricing arithmetic yourself. If required details are missing, ask a "
            "short follow-up question. Explain any invalid plan limits.\n\n"
            f"MCP catalog:\n{catalog}"
        ),
    )


async def stream_response(agent: Any, prompt: str, thread_id: str) -> None:
    """Stream one answer and persist the turn in the agent checkpoint."""

    logger.info("Invoking model prompt_length=%d", len(prompt))
    logger.debug("Prompt:\n%s", prompt)
    wrote_output = False
    async for message_chunk, _metadata in agent.astream(
        {"messages": [{"role": "user", "content": prompt}]},
        config={"configurable": {"thread_id": thread_id}},
        stream_mode="messages",
    ):
        text = message_chunk.text
        if text:
            print(text, end="", flush=True)
            wrote_output = True

    if wrote_output:
        print()
    logger.info("Model invocation completed")


async def run_chat(
    initial_prompt: str | None,
    model_settings: ModelSettings,
    mcp_settings: MCPSettings,
) -> None:
    """Read prompts and stream answers until the user exits."""

    agent = await create_product_agent(model_settings, mcp_settings)
    thread_id = str(uuid4())
    pending_prompt = initial_prompt

    print("Product Assistant chat. Type /quit or /exit to leave.")
    while True:
        try:
            if pending_prompt is not None:
                prompt = pending_prompt
                pending_prompt = None
                print(f"You: {prompt}")
            else:
                prompt = await asyncio.to_thread(input, "\nYou: ")
        except EOFError:
            print("\nGoodbye!")
            return

        prompt = prompt.strip()
        if not prompt:
            continue
        if prompt.lower() in {"/quit", "/exit"}:
            print("Goodbye!")
            return

        print("Assistant: ", end="", flush=True)
        await stream_response(agent, prompt, thread_id)


async def main() -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    configure_logging()
    args = parse_args()
    try:
        settings = ModelSettings.from_env()
        mcp_settings = MCPSettings.from_env()
        await run_chat(args.prompt, settings, mcp_settings)
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as exc:
        logger.exception("Client failed")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    asyncio.run(main())
