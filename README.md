# MCP Server Product Assistant

MCP Product Assistant is a MCP server for a SaaS sales use case.

It allows an agent/LLM to:
- query real data on plans, features, and pricing,
- calculate traceable quotes,
- estimate quick operational costs (what-if),
- and generate guided prompts for pitch and comparison.

Not a full chatbot: it's a layer of MCP capabilities (resources + tools + prompts).

## Features

- 3 read-only resources: `plans://all`, `features://by_plan`, `pricing://current`.
- 2 business tools: `generate_quote(...)` and `estimate_cost(...)`.
- 2 prompts: `sales_pitch(plan_id)` and `comparison_table()`.
- Seed data in JSON under `src/product_assistant/data/`.
- Unit tests for resources, tools, and prompts.

## Local execution

### Prerequisites

- Python `>= 3.14`
- `uv`

### Clone the repository

```bash
git clone https://github.com/rtrujillor/mcp-server-example

cd global-mcp-poc
```

### Installation

```bash
uv sync
```

### Run tests

```bash
uv run pytest -q
```

### Run MCP server

Inspector mode (development):

```bash
uv run mcp dev ./src/product_assistant/server.py
```

Installed script mode:

```bash
uv run product-assistant-mcp
```

The server transport is selected in `.env`:

```dotenv
# STDIO or STREAMABLE_HTTP
MCP_TRANSPORT=STDIO

# Used by the server only when STREAMABLE_HTTP is selected
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_PATH=/mcp

# Used by the client only when STREAMABLE_HTTP is selected
MCP_SERVER_URL=http://127.0.0.1:8000/mcp
MCP_API_KEY=
```

With `STDIO`, the LangChain client launches `product-assistant-mcp` as a child
process and communicates through its standard input and output. The server does
not listen on a network port.

With `STREAMABLE_HTTP`, start the server explicitly:

```bash
uv run product-assistant-mcp
```

The client connects to `MCP_SERVER_URL` and does not launch a server process.
For a deployed HTTPS endpoint, set an `https://` URL and normally terminate TLS
at a reverse proxy or load balancer. If `MCP_API_KEY` is set, the client sends
it as a bearer token; authentication must be enforced by the server, proxy, or
API gateway.

## LangChain client with a local LLM

The example in `examples/langchain_client.py` connects a LangChain Agent to this
MCP server using the transport selected by `MCP_TRANSPORT`. It can use either
LM Studio or Ollama as its model provider. LM Studio is the default. The client:

- loads the MCP catalog resources as grounded context,
- exposes `estimate_cost` and `generate_quote` to the agent as LangChain tools,
- and lets the model decide when a product question requires a tool call.

Install the optional client dependencies, load a tool-capable model in your
provider, and start its local server:

```bash
uv sync --group client
```

In another terminal, ask a question:

```bash
uv run --group client python examples/langchain_client.py \
  "We have 22 users, 5 projects, and 100000 API requests per month. Which plan fits and what is the monthly cost?"
```

The model must support tool calling. Provider selection and connection settings
live in the repository's `.env` file:

```dotenv
# Change only this flag to select the provider: LM or OLLAMA
MODEL_PROVIDER=LM

# LM Studio configuration
LM_STUDIO_MODEL=local-model
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_API_KEY=lm-studio

# Ollama configuration
OLLAMA_MODEL=llama3.1
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_API_KEY=
```

Both configuration blocks stay defined. To switch to Ollama, change only the
selector to `MODEL_PROVIDER=OLLAMA`. The client then reads the Ollama variables
and credentials; it does not use the LM Studio configuration.

For example, download and run an Ollama model before selecting it:

```bash
ollama pull llama3.1
```

Run the client normally after selecting the provider in `.env`:

```bash
uv run --group client python examples/langchain_client.py \
  "Create a yearly quote for 30 users on the professional plan."
```

`LM_STUDIO_API_KEY` and `OLLAMA_API_KEY` are independent. An empty
`OLLAMA_API_KEY` is appropriate for a local Ollama server; when populated, it
is sent as a bearer token. In `STDIO` mode, the LangChain MCP adapter launches
the server. In `STREAMABLE_HTTP` mode, start the server separately before
running the client.

## Quick architecture

![MCP Product Assistant architecture](docs/architecture.png)

The diagram follows the Ollama path selected by `MODEL_PROVIDER=OLLAMA`. The
same provider factory can create the LM Studio client instead, without changing
the agent or MCP integration. With `STDIO`, the client starts the MCP server as
a child process. With `STREAMABLE_HTTP`, it connects to the configured server
URL. In either mode, catalog resources become grounding context while MCP tools
remain callable operations chosen by the model.

The editable draw.io source is available at
[`docs/architecture.drawio`](docs/architecture.drawio). Open it in
[draw.io](https://app.diagrams.net/) to change the layout or export another
format.

- Entry point MCP: `src/product_assistant/server.py`
- Resources: `src/product_assistant/resources/`
- Tools: `src/product_assistant/tools/`
- Prompts: `src/product_assistant/prompts/`
- Typed models (Pydantic): `src/product_assistant/models/`
- Business rules (pricing/validation/discounts): `src/product_assistant/services/`

## Resources

### `plans://all`
Returns the catalog of plans with:
- `id`, `name`, `description`
- `limits` (users, projects, api_requests_per_month)
- `recommended_for`

### `features://by_plan`
Returns features by plan, grouped by category:
- `core_features`
- `analytics`
- `security`
- `support`
- `integrations`

### `pricing://current`
Returns current pricing with:
- `currency`, `billing_cycles`, `pricing_model`, `notes`
- per plan: `base_price`, `per_user_price`, `per_api_request_price`, limits, and discounts

## Tools

### `generate_quote(plan_id, users, billing_cycle)`

Calculates a formal and traceable quote.

Current behavior:
- Validates `users >= 1`.
- Checks for the existence of the plan in `plans://all` and `pricing://current`.
- Uses prices from the requested billing cycle (`monthly` or `yearly`).
- Applies volume discounts when applicable.
- Returns `valid_until` (today + 14 days), `trace`, and `notes`.
- If plan limits are exceeded, returns `valid=false` but keeps the calculation.
- If pricing is custom (e.g., enterprise), returns an explainable error.

Minimal example:

```json
{
  "plan_id": "professional",
  "users": 22,
  "billing_cycle": "monthly"
}
```

### `estimate_cost(plan, usage)`

Calculates a quick operational estimate (not a formal quote).

Current behavior:
- Always calculates with `monthly` cycle.
- Validates limits using `plans://all` (users/projects/api_requests_per_month).
- Calculates base lines + per user + (optional) per API request.
- Includes `trace`, `notes`, and `valid`.
- If pricing is custom, returns an explainable error.

Minimal example:

```json
{
  "plan": "professional",
  "usage": {
    "users": 22,
    "projects": 5,
    "api_requests_per_month": 100000
  }
}
```

## Prompts

### `sales_pitch(plan_id)`

Generates a prompt for the LLM to draft a brief sales pitch, with guardrails:
- use only data from `plans://all` and `features://by_plan`,
- do not invent capabilities,
- do not mention prices,
- redirect pricing inquiries to `generate_quote`.

### `comparison_table()`

Generates a prompt to enforce a Markdown comparison table of plans:
- fixed business columns,
- use only real data,
- missing values as `N/A` or `custom/contact sales`,
- close with a short conclusion.

## Example data

The PoC data is located in:
- `src/product_assistant/data/plans.json`
- `src/product_assistant/data/pricing.json`
- `src/product_assistant/data/features.json`

## Contribution

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).
