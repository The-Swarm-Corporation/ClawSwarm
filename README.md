# ClawSwarm

ClawSwarm provides programmatic access to Claude-based agents and a unified messaging gateway for production integrations. It is designed for teams that need consistent agent orchestration and multi-channel message aggregation behind a single, secure API.

---

## Overview

ClawSwarm consists of two main components:

1. **Claude agent utilities** — Run Claude Code agents with configurable identity (name, description, system prompt) and tasks. Supports synchronous execution, async, and streaming. Suitable for automation pipelines, batch processing, and embedding agent workflows into existing services.

2. **Messaging Gateway** — A gRPC service that aggregates incoming messages from Telegram, Discord, and WhatsApp into a single schema. Clients poll or stream messages over one protocol, with optional TLS. Intended for bot backends, support tooling, and unified inbox implementations.

Both components are library- and service-friendly: no mandatory UI, configuration via environment variables and code, and interfaces that integrate with standard Python async runtimes and gRPC tooling.

---

## Requirements

- Python 3.10+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/build-with-claude/claude-code) (for agent utilities) and appropriate API access
- For the gateway: bot tokens or API credentials for the platforms you enable (Telegram, Discord, WhatsApp)

---

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/YOUR_ORG/ClawSwarm.git
cd ClawSwarm
pip install -r requirements.txt
```

For editable development installs, install the package in place:

```bash
pip install -e .
```

*(Requires a `pyproject.toml` or `setup.py` in the repository.)*

---

## Claude Agent Utilities

The public API is in `claw_swarm.tools`.

### One-off run (blocking)

```python
from claw_swarm import run_claude_agent

responses = run_claude_agent(
    name="CodeReviewer",
    description="Reviews Python code for style and correctness.",
    prompt="Respond in bullet points. Flag security issues.",
    tasks="Review the authentication logic in auth.py",
)
for text in responses:
    print(text)
```

### Async and streaming

```python
import asyncio
from claw_swarm import run_claude_agent_async, stream_claude_agent

# Collect all responses asynchronously
async def run():
    texts = await run_claude_agent_async(
        name="Summarizer",
        description="Summarizes long documents.",
        prompt="Keep summaries under 200 words.",
        tasks="Summarize the attached report.",
    )
    return texts

# Or stream assistant text as it arrives
async def stream():
    async for block in stream_claude_agent(
        name="Helper",
        description="Answers questions concisely.",
        prompt="Be precise and cite sources when possible.",
        tasks="What are the main risks in this contract?",
    ):
        print(block, end="")

asyncio.run(stream())
```

Agents use the Claude Code preset (e.g. read, write, edit, bash, grep) and a configurable turn limit. Each call is a new session; no conversation history is retained across calls.

---

## Messaging Gateway

The gateway exposes a gRPC API for polling and streaming messages from Telegram, Discord, and WhatsApp. All messages are normalized to a single `UnifiedMessage` schema (id, platform, channel, sender, text, attachments, timestamp).

### Configuration

Configure via environment variables. Omit a platform’s token to disable that adapter (it will return no messages).

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token |
| `DISCORD_BOT_TOKEN` | Discord bot token |
| `DISCORD_CHANNEL_IDS` | Comma-separated Discord channel IDs to read |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Cloud API access token |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp phone number ID |
| `GATEWAY_HOST` | Bind host (default: `[::]`) |
| `GATEWAY_PORT` | Bind port (default: `50051`) |
| `GATEWAY_TLS` | Set to `1`, `true`, or `yes` to enable TLS |
| `GATEWAY_TLS_CERT_FILE` | Path to server certificate (PEM) when TLS is enabled |
| `GATEWAY_TLS_KEY_FILE` | Path to private key (PEM) when TLS is enabled |

### Running the server

From the project root:

```bash
python -m claw_swarm.gateway
```

Or programmatically:

```python
import asyncio
from claw_swarm.gateway import (
    DiscordAdapter,
    TelegramAdapter,
    WhatsAppAdapter,
    run_server,
)

async def main():
    adapters = [
        TelegramAdapter(),
        DiscordAdapter(),
        WhatsAppAdapter(),
    ]
    server = await run_server(
        adapters,
        host="[::]",
        port=50051,
        use_tls=False,  # Use True and server_credentials in production
    )
    await server.wait_for_termination()

asyncio.run(main())
```

gRPC methods:

- **PollMessages** — Request messages since a timestamp, optionally filtered by platform. Returns a sorted list of `UnifiedMessage` up to a specified limit.
- **StreamMessages** — Server-streaming RPC that delivers new messages as they are fetched from the configured adapters.
- **Health** — Returns server health and version.

Use TLS and valid certificates in production. Provide `server_credentials` from `grpc.ssl_server_credentials()` when calling `run_server(..., use_tls=True, server_credentials=...)`.

---

## Architecture

- **Adapters** — Each platform (Telegram, Discord, WhatsApp) implements the `MessageAdapter` interface: `platform_name` and `fetch_messages(since_timestamp_utc_ms, max_messages)`. Optional `stream_messages()` can be overridden for push-style backends.
- **Schema** — `UnifiedMessage` (Pydantic) and `Platform` enum are defined in `claw_swarm.gateway.schema`. They mirror the gRPC definitions and provide `to_grpc()` / `from_grpc()` for serialization.
- **Protocol** — Protobuf and gRPC definitions live under `claw_swarm.gateway.proto`. Generate client code with your standard gRPC toolchain for your language.

Extending the gateway with a new platform means implementing `MessageAdapter` and registering it in the adapter list passed to `run_server`.

---

## Security

- Do not commit bot tokens or API keys. Use environment variables or a secrets manager.
- In production, run the gateway with TLS (`GATEWAY_TLS=1` and valid `GATEWAY_TLS_CERT_FILE` / `GATEWAY_TLS_KEY_FILE`). Restrict bind address and port as needed.
- Ensure only authorized clients can reach the gRPC port (network policies, firewall, or mTLS if required).

---

## License

See the repository’s LICENSE file for terms of use.
