# ClawSwarm

ClawSwarm is a production-ready system that connects a **Swarms-based AI agent** (ClawSwarm prompt + Claude as a tool) to **Telegram, Discord, and WhatsApp** through a unified **Messaging Gateway**. Users message the bot on any platform; the agent processes messages and replies on the same channel. The agent runs 24/7 and is designed for consistent orchestration and multi-channel aggregation behind a single, secure API.

---

## Architecture Overview

```
                                    EXTERNAL PLATFORMS
    +----------------+    +----------------+    +----------------+
    |   TELEGRAM     |    |    DISCORD     |    |   WHATSAPP     |
    |  (Bot API)     |    |  (Bot API)     |    | (Cloud API)    |
    +-------+--------+    +--------+-------+    +--------+-------+
            |                     |                      |
            | getUpdates          | channels/messages    | webhook/queue
            v                     v                      v
    +----------------------------------------------------------------------+
    |                    MESSAGING GATEWAY (gRPC Server)                   |
    |  claw_swarm.gateway  |  python -m claw_swarm.gateway                 |
    |                                                                      |
    |  +----------------+  +----------------+  +----------------+             |
    |  | TelegramAdapter|  | DiscordAdapter |  | WhatsAppAdapter|             |
    |  | fetch_messages |  | fetch_messages |  | fetch_messages |             |
    |  +-------┬--------+  +--------┬-------+  +--------┬-------+             |
    |          |                    |                    |                    |
    |          +--------------------+--------------------+                    |
    |                           |                                            |
    |                    UnifiedMessage                                      |
    |              (id, platform, channel_id, thread_id,                     |
    |               sender_id, sender_handle, text, attachments, ts)         |
    |                           |                                            |
    |  RPC: PollMessages()  StreamMessages()  Health()                        |
    +----------------------------------------------------------------------+
            |
            | gRPC (client)
            v
    +----------------------------------------------------------------------+
    |                     AGENT RUNNER (24/7 loop)                          |
    |  claw_swarm.agent_runner  |  python -m claw_swarm.main                |
    |                                                                      |
    |   loop:  PollMessages() --> for each UnifiedMessage:                |
    |             |                                                        |
    |             v                                                        |
    |  +----------------------------------------------------------------+  |
    |  |              CLAWSWARM AGENT (Swarms Agent)                    |  |
    |  |  claw_swarm.agent.create_agent()                               |  |
    |  |                                                                |  |
    |  |  System prompt:  prompts/clawswarm.md                          |  |
    |  |  Model:          AGENT_MODEL (e.g. gpt-4o-mini, Claude)       |  |
    |  |  Tools:          [ call_claude ]  <---------------------------|--+----+
    |  |                                                                |  |    |
    |  |  agent.run(user_message) --> reply_text                        |  |    |
    |  +----------------------------------------------------------------+  |    |
    |             |                                                        |    |
    |             v                                                        |    |
    |  +----------------------+                                            |    |
    |  | REPLIER              |  send_message_async(platform, channel_id,  |    |
    |  | claw_swarm.replier   |  thread_id, reply_text)                   |    |
    |  +----------+-----------+                                            |    |
    |             |                                                         |    |
    +-------------|---------------------------------------------------------+    |
                  |                                                              |
                  | HTTP (Telegram/Discord/WhatsApp send APIs)                   |
                  v                                                              |
    +----------------+    +----------------+    +----------------+                |
    |   TELEGRAM     |    |    DISCORD     |    |   WHATSAPP     |                |
    | sendMessage    |    | POST /messages |    | POST /messages|                |
    +----------------+    +----------------+    +----------------+                |
                                                                                 |
    +----------------------------------------------------------------------------+
    |  CLAUDE AS TOOL (when agent calls call_claude(task))                        |
    |  claw_swarm.tools.run_claude_agent()                                        |
    |  System prompt:  prompts/claude_tool.md                                     |
    |  Claude Code preset (read, write, edit, bash, grep, etc.)                    |
    |  Returns full response string to agent --> agent summarizes/quotes for user|
    +----------------------------------------------------------------------------+
```

### Component Summary

| Component | Role |
|-----------|------|
| **Messaging Gateway** | gRPC server; adapters poll Telegram/Discord/WhatsApp and normalize to `UnifiedMessage`. Exposes `PollMessages`, `StreamMessages`, `Health`. |
| **Agent Runner** | Long-lived process that polls the gateway, runs the ClawSwarm agent on each message, and sends replies via the replier. Entrypoint: `python -m claw_swarm.main`. |
| **ClawSwarm Agent** | Swarms `Agent` with system prompt from `prompts/clawswarm.md`, configurable LLM (`AGENT_MODEL`), and a single tool `call_claude` for deep reasoning/code. |
| **Claude tool** | `call_claude(task)` runs Claude (via `claw_swarm.tools.run_claude_agent`) with `prompts/claude_tool.md`; returns text to the agent for summarizing or quoting in chat. |
| **Replier** | Sends reply text back to the correct channel/thread on Telegram, Discord, or WhatsApp using the same env tokens as the gateway. |

### Data Flow (one message)

1. User sends a message on Telegram, Discord, or WhatsApp.
2. Gateway adapters fetch it; servicer normalizes to `UnifiedMessage` and serves via gRPC.
3. Agent runner polls `PollMessages()`, gets the message.
4. Runner calls `agent.run(message.text)` (Swarms agent; may call `call_claude` internally).
5. Agent returns `reply_text`; runner calls `send_message_async(platform, channel_id, thread_id, reply_text)`.
6. Replier posts to the platform’s send API; user sees the reply.

---

## Requirements

- Python 3.10+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/build-with-claude/claude-code) (for the Claude tool) and appropriate API access
- [Swarms](https://github.com/kyegomez/swarms) (installed via `requirements.txt`)
- For the gateway and replier: bot tokens or API credentials for the platforms you enable (Telegram, Discord, WhatsApp)

---

## Installation

```bash
git clone https://github.com/YOUR_ORG/ClawSwarm.git
cd ClawSwarm
pip install -r requirements.txt
```

For an editable install:

```bash
pip install -e .
```

---

## Quick Start: Run 24/7

1. **Configure environment** (tokens for the platforms you use):

   ```bash
   export TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   export DISCORD_BOT_TOKEN=your_discord_bot_token
   export DISCORD_CHANNEL_IDS=channel_id1,channel_id2
   # Optional: WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID
   ```

2. **Start the Messaging Gateway** (ingests messages from Telegram/Discord/WhatsApp):

   ```bash
   python -m claw_swarm.gateway
   ```

3. **Start the agent** (polls gateway, runs ClawSwarm, sends replies):

   ```bash
   python -m claw_swarm.main
   ```

Keep both processes running (or run under systemd, Docker, or a process manager for 24/7). The agent loop runs until interrupted (Ctrl+C or SIGTERM).

---

## ClawSwarm Agent and Prompts

The main agent is a **Swarms Agent** with:

- **System prompt:** `claw_swarm/prompts/clawswarm.md` (identity, chat guidelines, when to use Claude).
- **Claude as a tool:** `call_claude(task)` uses `claw_swarm/tools.run_claude_agent` with `claw_swarm/prompts/claude_tool.md`.

All prompts live in `claw_swarm/prompts/`; edit those files to change behavior without touching agent code.

### Creating the agent in code

```python
from claw_swarm import create_agent

agent = create_agent()
response = agent.run("What are the key benefits of multi-agent systems?")
print(response)
```

Override model or prompt:

```python
agent = create_agent(
    model_name="claude-3-5-sonnet-20241022",
    system_prompt="Custom system prompt...",
)
```

Environment:

- `AGENT_MODEL` — LLM for the main agent (default: `gpt-4o-mini`).

---

## Claude Agent Utilities (library use)

For one-off or custom flows you can call the Claude agent directly via `claw_swarm.tools`.

### Blocking run

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

async def run():
    texts = await run_claude_agent_async(
        name="Summarizer",
        description="Summarizes long documents.",
        prompt="Keep summaries under 200 words.",
        tasks="Summarize the attached report.",
    )
    return texts

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

---

## Messaging Gateway

The gateway exposes a gRPC API for polling and streaming messages from Telegram, Discord, and WhatsApp. All messages are normalized to a single `UnifiedMessage` schema (id, platform, channel_id, thread_id, sender_id, sender_handle, text, attachments, timestamp).

### Configuration

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

Omit a platform’s token to disable that adapter (it will return no messages).

### Running the gateway

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
        use_tls=False,
    )
    await server.wait_for_termination()

asyncio.run(main())
```

### gRPC methods

- **PollMessages** — Request messages since a timestamp; returns a sorted list of `UnifiedMessage` (used by the agent runner).
- **StreamMessages** — Server-streaming RPC that delivers new messages as they are fetched.
- **Health** — Returns server health and version.

Use TLS and valid certificates in production.

---

## Agent Runner Configuration

| Variable | Description |
|----------|-------------|
| `GATEWAY_HOST` | Gateway host (default: `localhost`) |
| `GATEWAY_PORT` | Gateway port (default: `50051`) |
| `AGENT_MODEL` | Swarms agent model (default: `gpt-4o-mini`) |

The replier uses the same platform tokens as the gateway (`TELEGRAM_BOT_TOKEN`, `DISCORD_BOT_TOKEN`, etc.) to send replies.

---

## Project Layout

```
claw_swarm/
├── __init__.py           # create_agent, run_claude_agent, ...
├── main.py                # Entrypoint: python -m claw_swarm.main
├── agent_runner.py        # 24/7 poll loop, agent.run(), replier
├── agent/
│   └── __init__.py        # create_agent(), Claude tool, prompt loading
├── prompts/
│   ├── clawswarm.md       # Main agent system prompt
│   └── claude_tool.md    # Claude-as-tool system prompt
├── tools.py               # run_claude_agent, run_claude_agent_async, stream_claude_agent
├── replier.py             # send_message_async (Telegram/Discord/WhatsApp)
├── gateway.py             # Entrypoint: python -m claw_swarm.gateway
└── gateway/
    ├── server.py          # gRPC servicer (PollMessages, StreamMessages, Health)
    ├── schema.py          # UnifiedMessage, Platform
    ├── proto/             # Protobuf and gRPC definitions
    └── adapters/          # TelegramAdapter, DiscordAdapter, WhatsAppAdapter
```

---

## Security

- Do not commit bot tokens or API keys. Use environment variables or a secrets manager.
- In production, run the gateway with TLS (`GATEWAY_TLS=1` and valid cert/key). Restrict bind address and port as needed.
- Ensure only authorized clients can reach the gRPC port (firewall, network policies, or mTLS if required).

---

## License

See the repository’s LICENSE file for terms of use.
