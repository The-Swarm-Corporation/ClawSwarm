# ClawSwarm

![Banner image](images/bg.png)

**A smaller, lighter-weight version of [OpenClaw](https://github.com/openclaw/openclaw)**—natively multi-agent, compiles to Rust, and built on the **[Swarms](https://github.com/kyegomez/swarms) framework** and Swarms ecosystem. One API, unified messaging across Telegram, Discord, and WhatsApp with optional Claude-powered reasoning. Production-ready: gRPC gateway, prompts in code (`claw_swarm.prompts`), and 24/7 operation. Dockerfile included (Python 3.12).

---

## Overview

ClawSwarm is a streamlined, multi-agent alternative to OpenClaw. It delivers **natively multi-agent** AI that responds to users on Telegram, Discord, and WhatsApp through a centralized **Messaging Gateway**. The gateway normalizes incoming messages; the **ClawSwarm Agent** (Swarms framework, configurable system prompt, Claude as a tool) processes each message and replies via a **Replier** back to the originating channel. Built on the Swarms ecosystem for reliability, security, and minimal operational overhead—with a path to **compile to Rust** for performance and deployment flexibility.

**Key capabilities**

- **Lighter than OpenClaw** — Smaller footprint and simpler stack; same multi-channel vision without the full OpenClaw surface area.
- **Natively multi-agent** — Designed from the ground up for multi-agent orchestration on the Swarms framework and Swarms ecosystem.
- **Unified ingestion** — One gRPC API for all supported channels; add or remove platforms without changing agent logic.
- **Swarms-native agent** — Industry-standard orchestration, configurable model and system prompt, Claude available as a tool for deep reasoning and code.
- **Compiles to Rust** — Build path to Rust for performance and deployment flexibility.
- **Prompts in code** — Agent and Claude-tool prompts are Python strings in `claw_swarm.prompts`; override via `create_agent(system_prompt=...)` or edit the module.
- **Production-ready** — Optional TLS, environment-based configuration, long-running agent loop suitable for systemd, Docker, or managed runtimes.

---

## Architecture

```
     Telegram    Discord    WhatsApp
          \        |        /
           \       v       /
            +--------------+
            |   Gateway    |   unified ingest (gRPC)
            +------+-------+
                   |
                   v
            +--------------+
            |    Agent     |   Swarms + Claude tool
            +------+-------+
                   |
                   v
            +--------------+
            |   Replier    |   send back to each channel
            +------+-------+
                   |
     Telegram    Discord    WhatsApp
```

**Flow:** User messages arrive on any channel → Gateway normalizes and exposes via gRPC → Agent processes (optionally calling Claude) → Replier sends the response to the correct channel.

### Relationship to OpenClaw

[OpenClaw](https://github.com/openclaw/openclaw) is a full-featured personal AI assistant (gateway, many channels, voice, canvas, nodes, skills). **ClawSwarm** is a smaller, lighter-weight take on that vision: natively multi-agent, built on the Swarms framework and Swarms ecosystem, with a path to compile to Rust. Use ClawSwarm when you want a lean, multi-agent messaging layer; use OpenClaw when you need the full product (companion apps, voice, canvas, etc.).

---

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt` (no version pins; use a venv and pin locally if needed)
- [Swarms](https://github.com/kyegomez/swarms) framework and Swarms ecosystem; [Claude Code](https://docs.anthropic.com/en/docs/build-with-claude/claude-code) (for the Claude tool)
- Platform credentials for the channels you enable: Telegram Bot Token, Discord Bot Token and Channel IDs, and/or WhatsApp Cloud API credentials

---

## Installation

```bash
git clone https://github.com/YOUR_ORG/ClawSwarm.git
cd ClawSwarm
pip install -r requirements.txt
```

---

## Quick Start

**1. Set environment variables** for the channels you use (e.g. `TELEGRAM_BOT_TOKEN`, `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_IDS`).

**2. Run the full stack** (gateway + agent in one process group):

```bash
./run.sh
```

Or run each component in a separate terminal:

```bash
python -m claw_swarm.gateway    # terminal 1
python -m claw_swarm.main       # terminal 2
```

Use Ctrl+C to stop; `run.sh` stops both processes. For 24/7 operation, run under systemd or Docker.

**Docker:**

```bash
docker build -t clawswarm .
docker run --env-file .env clawswarm
```

Pass channel tokens and `AGENT_MODEL` via `--env-file .env` or `-e`.

---

## Configuration

### Gateway

| Variable | Purpose |
|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token |
| `DISCORD_BOT_TOKEN` | Discord bot token |
| `DISCORD_CHANNEL_IDS` | Comma-separated channel IDs |
| `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp Cloud API |
| `GATEWAY_HOST`, `GATEWAY_PORT` | Bind address (default `[::]:50051`) |
| `GATEWAY_TLS`, `GATEWAY_TLS_CERT_FILE`, `GATEWAY_TLS_KEY_FILE` | TLS for production |

Omit a platform’s credentials to disable that channel.

### Agent

| Variable | Purpose |
|----------|---------|
| `GATEWAY_HOST`, `GATEWAY_PORT` | Gateway endpoint (default `localhost:50051`) |
| `AGENT_MODEL` | Swarms agent model (default `gpt-4o-mini`) |

Replies use the same platform tokens as the gateway.

---

## Agent and Prompts

The main agent is a **Swarms Agent** with system prompt and Claude-tool prompt defined in `claw_swarm.prompts`. Override with `create_agent(system_prompt=...)` or edit the strings in that module.

**Programmatic use:**

```python
from claw_swarm import create_agent

agent = create_agent()
response = agent.run("What are the key benefits of multi-agent systems?")
```

Override model or prompt via arguments or environment (`AGENT_MODEL`).

---

## Claude Utilities (library)

For one-off or custom pipelines, use the Claude agent directly:

```python
from claw_swarm import run_claude_agent

responses = run_claude_agent(
    name="CodeReviewer",
    description="Reviews Python code.",
    prompt="Respond in bullet points. Flag security issues.",
    tasks="Review the authentication logic in auth.py",
)
```

Async and streaming are available via `run_claude_agent_async` and `stream_claude_agent`.

---

## Gateway API

gRPC service:

- **PollMessages** — Fetch messages since a timestamp (used by the agent runner).
- **StreamMessages** — Server-streaming delivery of new messages.
- **Health** — Liveness and version.

Messages are normalized to a single schema: `UnifiedMessage` (id, platform, channel_id, thread_id, sender, text, attachments, timestamp). Use TLS and restrict network access in production.

---

## Security and Operations

- **Secrets** — Do not commit tokens or API keys. Use environment variables or a secrets manager.
- **Transport** — Enable gateway TLS in production (`GATEWAY_TLS=1` and valid certificate and key).
- **Access control** — Restrict which clients can reach the gRPC port (firewall, VPC, or mTLS as required).

---

## License

See the repository LICENSE for terms of use.
