# ClawSwarm 1.0.0 — Hierarchical Swarms, gRPC Gateway, Web Scraping, HTTP API, and Persistent Memory

## Overview

Across 49 commits the project went from an empty scaffold to a deployable, containerized system. The core hierarchical swarm architecture was established early and refined through several iterations. Four specialized worker agents were built out — response, search, token launch, and developer — each with its own tool set. A gRPC messaging gateway was added to normalize Telegram, Discord, and WhatsApp into a shared queue. A FastAPI HTTP server introduced async job tracking for external access. A typed configuration system replaced scattered environment variable reads, backed by an interactive onboarding wizard and a three-subcommand CLI. Cross-platform memory persistence was added so the agent retains context across restarts and platforms. Web scraping was integrated into the search agent, giving it full page content rather than just search metadata. The CI pipeline was established with GitHub Actions and kept current through automated Dependabot updates, and the stack was containerized with Docker and wired for one-command Railway deploys.

---

## Usage

**Install**

```bash
pip install claw-swarm
```

**Run the onboarding wizard**

Creates `claw_config.yaml` in the project root. Walk through agent identity, worker model, gateway host/port/TLS, API port/key, and verbose logging. Press Enter to accept defaults.

```bash
clawswarm onboarding

# Overwrite an existing config
clawswarm onboarding --force
```

**Start the full stack**

Starts the gRPC gateway and the agent polling loop. Add `--api` to also start the HTTP API server.

```bash
clawswarm run

# With the HTTP API server on the default port (8080)
clawswarm run --api

# Custom ports and gateway overrides
clawswarm run --api --port 9000 --gw-port 50052 --gw-tls --api-key mysecret
```

**Inspect active configuration**

```bash
clawswarm settings
```

**Run the gateway and agent as separate processes**

```bash
clawswarm-gateway     # gRPC gateway only
clawswarm-agent       # agent polling loop only
```

**Use the swarm directly in Python**

```python
from claw_swarm.agent import create_agent, hierarchical_swarm

# One-shot convenience wrapper
result = hierarchical_swarm("What are the latest developments in AI agents?")

# Full control — create once, call many times
swarm = create_agent()
result = swarm.run("Summarize the top Hacker News posts today")
```

**Submit a task over HTTP**

```bash
# Async — returns job_id immediately
curl -X POST http://localhost:8080/v1/agent/completions \
  -H "Content-Type: application/json" \
  -d '{"task": "Search for the latest Python 3.13 release notes"}'

# Sync — blocks until done (default timeout: 300s)
curl -X POST http://localhost:8080/v1/agent/completions/sync \
  -H "Content-Type: application/json" \
  -d '{"task": "Explain how gRPC streaming works"}'

# Poll a job
curl http://localhost:8080/v1/agent/jobs/<job_id>

# With API key authentication
curl -X POST http://localhost:8080/v1/agent/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: mysecret" \
  -d '{"task": "Launch a token named ResearchBot with ticker RBT"}'
```

**Use worker agents directly**

```python
from claw_swarm.agent.worker_agents import (
    create_search_agent,
    create_developer_agent,
    create_token_launch_agent,
    create_response_agent,
)

search = create_search_agent()
result = search.run("Latest news on multi-agent frameworks 2025")

dev = create_developer_agent()
result = dev.run("Add a retry decorator to the fetch_user function in api.py")

token = create_token_launch_agent()
result = token.run("Launch a token named ResearchBot, ticker RBT")
```

**Use the web scraper directly**

```python
from claw_swarm.tools.web_scraper import scrape_url, scrape_urls

text = scrape_url("https://example.com/article")

# Multiple URLs — list or comma-separated string
text = scrape_urls(["https://example.com/a", "https://example.com/b"])
```

**Use the Claude Code tool directly**

```python
from claw_swarm.tools.claude_code_tool import run_claude_agent

responses = run_claude_agent(
    name="Reviewer",
    description="Reviews Python code for correctness",
    prompt="You are a senior Python engineer. Review the code and suggest improvements.",
    tasks="Review the auth module in src/auth.py for security issues",
)
print("\n".join(responses))
```

**Read and write agent memory**

```python
from claw_swarm.agent.memory import read_memory, append_interaction

# Read the current memory context
print(read_memory())

# Manually append an interaction
append_interaction(
    platform="API",
    channel_id="http",
    thread_id="",
    sender_handle="user",
    user_text="What is ClawSwarm?",
    reply_text="ClawSwarm is a hierarchical multi-agent framework.",
)
```

**Override the worker model at runtime**

```bash
WORKER_MODEL_NAME=gpt-4.1 clawswarm run --api
```

**Run tests**

```bash
pytest
```

---

## Features

- **Hierarchical Swarm Architecture** — A director agent receives tasks and dispatches subtasks to four specialized worker agents (response, search, token launch, developer), aggregating their results before replying.

- **Response Agent** — A tool-free worker that handles greetings, clarifications, and simple factual questions without invoking search, code, or blockchain tools.

- **Search Agent** — A worker equipped with `exa_search`, `scrape_url`, and `scrape_urls`. Discovers sources via semantic search then reads the full text of the most relevant pages before summarizing.

- **Developer Agent** — A worker that spawns a live Claude Code session (up to 120 turns) with access to Read, Write, Edit, Bash, Grep, and Glob. Handles implementation, refactoring, debugging, and code explanation.

- **Token Launch Agent** — A worker with `launch_token` and `claim_fees` tools. Launches agent tokens on Solana via the Swarms World API (~0.04 SOL per launch) and claims accumulated fees by contract address.

- **Claude Code SDK Integration** — Three entry points into the Claude Agent SDK: `run_claude_agent` (sync), `run_claude_agent_async` (async), and `stream_claude_agent` (async generator). All use the `claude_code` tool preset.

- **Web Scraping** — `scrape_url` and `scrape_urls` fetch and extract readable text from web pages using a minimal stdlib HTML parser with no additional dependencies. Tags like `script`, `style`, and `svg` are stripped; entities are unescaped and whitespace collapsed.

- **Tools Registry** — A single `tools` list in `claw_swarm/tools/__init__.py` exports all eight callable tools (`claim_fees`, `launch_token`, `run_claude_agent`, `run_claude_agent_async`, `stream_claude_agent`, `exa_search`, `scrape_url`, `scrape_urls`) from one import point.

- **gRPC Messaging Gateway** — A gRPC server that normalizes Telegram, Discord, and WhatsApp messages into a unified `UnifiedMessage` schema. Platform adapters handle each channel; the agent runner polls via `PollMessages(since_timestamp_utc_ms)` so no message is delivered twice.

- **Persistent Cross-Platform Memory** — Every message exchange (across Telegram, Discord, WhatsApp, and HTTP) is appended to `agent_memory.md` with timestamp, platform, channel, sender, and reply. Memory is injected between the system prompt and the current message on every request. Size is capped at 100,000 characters by default.

- **HTTP API Server** — A FastAPI server with a FIFO `asyncio.Queue` and a single background worker. Exposes `POST /v1/agent/completions` (async, returns job ID), `POST /v1/agent/completions/sync` (blocks until done), `GET /v1/agent/jobs/{id}` (poll status), and `GET /v1/agent/jobs` (list recent jobs).

- **Onboarding Wizard** — `clawswarm onboarding` runs an interactive Rich-based setup wizard that writes `claw_config.yaml`. Covers agent identity, worker model, gateway host/port/TLS, API port/key, and verbose logging. Port prompts validate integer input in a loop. A summary table is shown before writing. Supports `--force` to overwrite.

- **ClawConfig** — A typed dataclass covering all runtime settings (agent name/description, worker model, gateway host/port/TLS, API port/key, verbose). Loaded from `claw_config.yaml`, serialized with `to_dict()`, and applied to the environment via `apply_config_to_env()`.

- **`clawswarm run`** — Starts the gRPC gateway and optionally the HTTP API server as subprocesses, then runs the agent polling loop in the main process. Accepts `--gw-host`, `--gw-port`, `--gw-tls`, and `--api-key` flags that override config and environment at runtime.

- **`clawswarm settings`** — Prints all active configuration grouped into four Rich panels (Gateway, API, Models, Platforms) with secret values masked.

- **Unit Test Suite** — Tests covering agent main, agent runner, CLI, gateway adapters, gateway schema, gateway server, memory, prompts, replier, and launch tokens. Run automatically on every push via GitHub Actions.

- **Dockerfile** — Containerizes the full stack for deployment.

- **Railway Deployment** — Configuration for one-command deploys to Railway with an externally accessible HTTPS endpoint.

---

## Improvements

- **Worker Model Resolution** — `resolve_model()` implements a four-level precedence chain: explicit argument > `WORKER_MODEL_NAME` env > `AGENT_MODEL` env > hardcoded default. Setting `WORKER_MODEL_NAME` swaps all four workers at deploy time without code changes.

- **API Key Authentication** — The HTTP API applies an `_verify_api_key` FastAPI dependency to all `/v1/*` routes. If `API_KEY` is set, every request must include a matching `X-API-Key` header. If unset, the API is open.

- **Public IP Discovery on Startup** — The API server fetches the machine's public IP from three fallback endpoints on startup and prints both local and public URLs in a Rich panel.

- **`apply_config_to_env` Expansion** — Now propagates `GATEWAY_HOST`, `GATEWAY_PORT`, `GATEWAY_TLS`, `API_PORT`, and `API_KEY` in addition to the original worker model and agent identity fields. Uses `setdefault` so existing shell environment variables always win.

- **Project Root Detection** — `_find_project_root()` walks up to 10 parent directories looking for `pyproject.toml` or `.git`, so `claw_config.yaml` and `.env` resolve correctly regardless of which subdirectory the CLI is invoked from.

- **Reply Extraction** — `_extract_final_reply()` parses verbose `HierarchicalSwarm` output to isolate the final reply. Looks for a `[Current message to answer]` marker, then labeled reply sections (`**ClawSwarm:**`, `**Assistant:**`), then falls back to the last contiguous non-header block.

- **Telegram Summarizer** — Raw swarm output is passed through a lightweight summarizer agent (`gpt-4.1`, `max_loops=1`) that produces a concise, emoji-free reply suitable for chat platforms before falling back to `_extract_final_reply`.

- **Agent Identity via Environment** — Agent name and description are readable from `CLAWSWARM_AGENT_NAME` and `CLAWSWARM_AGENT_DESCRIPTION`, allowing the same binary to run under different identities across deployments.

- **Subprocess Lifecycle Management** — `clawswarm run` checks subprocess health 2 seconds after launch and tears down the full process tree on exit, with a 5-second graceful window before SIGKILL.

- **`cmd_settings` Rich Panels** — Rewritten to display configuration grouped by section (Gateway, API, Models, Platforms) using Rich panels instead of plain text output.

- **Structured API Error Logging** — `_log_api_error()` in the token tools emits tailored log messages per HTTP status: field errors for 400, key management URL for 401, rate-limit reset time for 429, server error body for 500.

- **CI Action Version Bumps** — `actions/setup-python` v5 to v6, `actions/checkout` v4 to v6, `actions/cache` v4 to v5, `github/codeql-action` v3 to v4, `ruff` widened to `<0.15.3`.

---

## Bug Fixes

- **Memory Write Fault Tolerance** — `append_interaction()` catches `OSError` and silently continues so a full disk or read-only filesystem does not crash the agent loop.

- **gRPC Reconnection** — The agent polling loop catches `UNAVAILABLE` gRPC errors and retries after the configured poll interval instead of exiting.

- **API Key Quote Stripping** — The token tool key loaders strip surrounding single and double quotes from environment variable values to handle common `.env` file formatting issues where editors leave literal quote characters in the value.

- **Subprocess Early-Exit Detection** — After spawning the gateway and API server, `clawswarm run` calls `poll()` on each process before starting the agent loop. If either exits early, the remaining processes are cleaned up and an actionable error is printed.

- **Memory Size Cap** — `read_memory()` trims to the last `MAX_MEMORY_CHARS` characters to prevent unbounded context growth from crashing the agent on long-running deployments.

---

## Conclusion

The two most significant recent additions are web scraping and the configuration overhaul. Web scraping extended the search agent from returning metadata to reading the full text of pages — `scrape_url` and `scrape_urls` are now first-class tools in the search agent's prompt, and the implementation adds no new dependencies by using Python's stdlib HTML parser alongside the existing `httpx` client. The configuration overhaul introduced `ClawConfig`, the `claw_config.yaml` file, the interactive onboarding wizard, and the expanded `apply_config_to_env` — together replacing scattered environment variable reads with a single typed object and a clear three-level precedence chain (CLI flags > config file > environment defaults). Combined with the HTTP API's async job queue, the gRPC gateway's platform normalization, and the cross-platform memory system, ClawSwarm now has the infrastructure needed to run as a long-lived, multi-channel agent backend rather than a script that needs to be restarted and reconfigured for each use.
