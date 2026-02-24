# ClawSwarm Configuration Reference

This document covers the `claw_config.yaml` configuration file and the full `clawswarm` CLI. For installation and quick-start steps see the [main README](../README.md).

---

## Table of contents

- [Overview](#overview)
- [Creating the config file](#creating-the-config-file)
- [Full schema reference](#full-schema-reference)
  - [agent](#agent)
  - [worker](#worker)
  - [gateway](#gateway)
  - [api](#api)
  - [runtime](#runtime)
- [Config precedence](#config-precedence)
- [What goes where](#what-goes-where)
- [CLI reference](#cli-reference)
  - [clawswarm onboarding](#clawswarm-onboarding)
  - [clawswarm run](#clawswarm-run)
  - [clawswarm settings](#clawswarm-settings)
- [Production configuration examples](#production-configuration-examples)
  - [Minimal local setup](#minimal-local-setup)
  - [Public server with auth](#public-server-with-auth)
  - [TLS-enabled gateway](#tls-enabled-gateway)
  - [Docker / Railway](#docker--railway)
- [Environment variable mapping](#environment-variable-mapping)
- [Troubleshooting](#troubleshooting)

---

## Overview

ClawSwarm uses two configuration sources that serve different purposes and are intentionally kept separate:

| File | Purpose | Commit to git? |
|------|---------|----------------|
| `claw_config.yaml` | Non-secret runtime configuration (ports, model names, agent identity) | Yes — safe to commit |
| `.env` | Secrets (API keys, bot tokens, TLS paths) | **No** — add to `.gitignore` |

`claw_config.yaml` is loaded on every `clawswarm` command. If it does not exist, the first `clawswarm run` (or an explicit `clawswarm onboarding`) will launch an interactive wizard to create it. All fields have built-in defaults so the file is entirely optional for local development.

---

## Creating the config file

Run the interactive setup wizard:

```bash
clawswarm onboarding
```

The wizard walks through five labelled sections. Press **Enter** at any prompt to accept the shown default. When all prompts are complete the file is written atomically to the project root.

```
🦀  Setup Wizard
────────────────────────────── Agent ──────────────────────────────
  ❯ Agent name [ClawSwarm]:
  ❯ Agent description [A hierarchical swarm...]:

────────────────────────────── Worker ─────────────────────────────
  ❯ Worker model name [gpt-4o-mini]:

────────────────────────── Gateway (gRPC) ─────────────────────────
  ❯ Bind host [[::]] :
  ❯ Bind port [50051]:
  ❯ Enable TLS? [y/N]:

─────────────────────────────── HTTP API ──────────────────────────
  ❯ API port [8080]:
  ❯ API key (leave blank for open access) []:

─────────────────────────────── Runtime ───────────────────────────
  ❯ Enable verbose logging? [y/N]:
```

To overwrite an existing file:

```bash
clawswarm onboarding --force
```

---

## Full schema reference

Below is the complete annotated structure with every field, its type, default value, and the environment variable it maps to.

```yaml
agent:
  name: ClawSwarm
  description: A hierarchical swarm of agents that can handle complex tasks

worker:
  model_name: gpt-4o-mini

gateway:
  host: "[::]"
  port: 50051
  tls: false

api:
  port: 8080
  key: ""

runtime:
  verbose: false
```

### `agent`

Configuration for the top-level director agent that orchestrates the swarm.

| Field | Type | Default | Env var | Description |
|-------|------|---------|---------|-------------|
| `agent.name` | string | `ClawSwarm` | `CLAWSWARM_AGENT_NAME` | Display name of the director agent. Used in logs, the HTTP API banner, and as the `HierarchicalSwarm` name. |
| `agent.description` | string | `A hierarchical swarm of agents that can handle complex tasks` | `CLAWSWARM_AGENT_DESCRIPTION` | Short description passed to the swarm constructor. Appears in Swagger UI and startup logs. |

### `worker`

Configuration for the specialist worker agents spawned by the director.

| Field | Type | Default | Env var | Description |
|-------|------|---------|---------|-------------|
| `worker.model_name` | string | `gpt-4o-mini` | `WORKER_MODEL_NAME` | OpenAI model identifier used by all worker agents (Response, Search, TokenLaunch, Developer). Overrides `AGENT_MODEL` for workers. Common values: `gpt-4o-mini`, `gpt-4o`, `gpt-4.1`. |

### `gateway`

Configuration for the gRPC Messaging Gateway that bridges Telegram, Discord, and WhatsApp into a unified message queue.

| Field | Type | Default | Env var | Description |
|-------|------|---------|---------|-------------|
| `gateway.host` | string | `[::]` | `GATEWAY_HOST` | Bind address for the gRPC server. `[::]` binds all IPv4 and IPv6 interfaces. Use `0.0.0.0` for IPv4-only. In most single-host deployments the gateway and agent run on the same machine so the default is fine. |
| `gateway.port` | integer | `50051` | `GATEWAY_PORT` | TCP port the gRPC server listens on. Must be open/reachable by the agent process. Change this if port 50051 is already in use. |
| `gateway.tls` | boolean | `false` | `GATEWAY_TLS` | When `true`, the gateway requires a TLS connection. You must also set `GATEWAY_TLS_CERT_FILE` and `GATEWAY_TLS_KEY_FILE` in your environment or `.env`. Recommended for any deployment that exposes the gRPC port to the internet. |

**TLS environment variables** (set in `.env`, not in `claw_config.yaml`):

| Variable | Description |
|----------|-------------|
| `GATEWAY_TLS_CERT_FILE` | Absolute path to the PEM-encoded TLS certificate |
| `GATEWAY_TLS_KEY_FILE` | Absolute path to the PEM-encoded private key |

### `api`

Configuration for the optional HTTP API server (FastAPI/uvicorn), started when `clawswarm run --api` is used.

| Field | Type | Default | Env var | Description |
|-------|------|---------|---------|-------------|
| `api.port` | integer | `8080` | `API_PORT` | Port the HTTP API server binds to on `0.0.0.0`. The startup banner prints the exact public URL (`http://<public-ip>:<port>/docs`) so you know what to share or expose in your firewall. |
| `api.key` | string | `""` (empty) | `API_KEY` | When non-empty, every request to `/v1/*` must include the header `X-API-Key: <value>`. Requests without the header or with a wrong key receive `401 Unauthorized`. Leave blank for open (unauthenticated) access — only do this on private networks. |

> **Security note:** If you set `api.key` in `claw_config.yaml` and commit that file, the key is visible in your repository history. For production deployments, set `API_KEY` in `.env` instead and leave `api.key` empty in the YAML.

### `runtime`

General runtime behaviour flags.

| Field | Type | Default | Env var | Description |
|-------|------|---------|---------|-------------|
| `runtime.verbose` | boolean | `false` | `CLAWSWARM_VERBOSE` | When `true`, the agent runner and gateway emit detailed debug output: raw gRPC payloads, worker agent outputs before summarization, memory reads/writes, and tool call traces. Useful during development; avoid in production as output volume is high. |

---

## Config precedence

Configuration values are resolved in the following order. Higher entries win.

```
1. CLI flags          (--gw-port, --api-key, etc.)
2. Environment vars   (GATEWAY_PORT, API_KEY, etc.)
3. .env file          (loaded automatically from project root)
4. claw_config.yaml   (loaded from project root)
5. Built-in defaults  (hard-coded in ClawConfig dataclass)
```

**Examples:**

```bash
# Uses gateway.port from claw_config.yaml (e.g. 50051)
clawswarm run

# Overrides gateway.port at the CLI level, ignores claw_config.yaml value
clawswarm run --gw-port 50052

# GATEWAY_PORT=50053 in .env overrides claw_config.yaml but loses to --gw-port
GATEWAY_PORT=50053 clawswarm run --gw-port 50052  # effective port: 50052
```

**Env var precedence detail:**

`apply_config_to_env` uses `os.environ.setdefault`, which means it only sets an env var if it is not already present. This guarantees that any value already in the environment (from a shell export or `.env`) is never silently overwritten by the config file.

---

## What goes where

Use this table to decide where to put each setting.

| Setting | Recommended location | Reason |
|---------|---------------------|--------|
| Agent name and description | `claw_config.yaml` → `agent` | Non-secret; safe to commit |
| Worker model name | `claw_config.yaml` → `worker` | Non-secret; same model across environments |
| Gateway host and port | `claw_config.yaml` → `gateway` | Infrastructure config; non-secret |
| TLS toggle | `claw_config.yaml` → `gateway.tls` | Non-secret; cert paths stay in `.env` |
| TLS cert and key paths | `.env` | May be server-specific; keep out of git |
| HTTP API port | `claw_config.yaml` → `api` | Non-secret; port is not sensitive |
| HTTP API auth key | `.env` as `API_KEY` | Secret; never commit |
| Verbose mode | `claw_config.yaml` → `runtime` | Dev preference; safe to commit |
| OpenAI / Anthropic API keys | `.env` | Secret |
| Telegram bot token | `.env` | Secret |
| Discord bot token and channel IDs | `.env` | Secret |
| WhatsApp access token and phone number ID | `.env` | Secret |

---

## CLI reference

### `clawswarm onboarding`

Create or regenerate `claw_config.yaml` using an interactive prompt wizard.

```
Usage: clawswarm onboarding [--force]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--force` | Overwrite an existing `claw_config.yaml`. Without this flag the command is a no-op if the file already exists. |

**Examples:**

```bash
# First-time setup — create the file
clawswarm onboarding

# Re-run the wizard to change settings
clawswarm onboarding --force
```

**Behaviour:**

1. If `claw_config.yaml` exists and `--force` is not set, a warning panel is printed and the command exits without prompting.
2. Otherwise the wizard renders a welcome banner and five section dividers, one per config group.
3. Each prompt shows the current default in brackets. Press **Enter** to accept it or type a new value.
4. After all prompts a summary table is displayed before writing the file.
5. The file is written to the project root (`pyproject.toml` or `.git` directory is used to locate it; falls back to the current working directory).

---

### `clawswarm run`

Start the ClawSwarm stack: gRPC gateway, agent loop, and optionally the HTTP API server.

```
Usage: clawswarm run [--api] [--port PORT] [--gw-host HOST]
                     [--gw-port PORT] [--gw-tls] [--api-key KEY]
```

**What always starts:**

- **Messaging Gateway** — gRPC server (subprocess) that ingests messages from Telegram, Discord, and WhatsApp adapters and normalises them into a unified queue.
- **Agent loop** — runs in the main process; polls the gateway, passes each message through the hierarchical swarm, and sends the reply back via the Replier.

**What starts with `--api`:**

- **HTTP API server** — FastAPI/uvicorn bound to `0.0.0.0:<api.port>`. On startup it fetches and prints the machine's public IP so you have the exact URL to share. Accepts tasks via REST; processes them through the same swarm.

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--api` | flag | off | Start the FastAPI/uvicorn HTTP API server alongside the agent. |
| `--port PORT` | integer | `8080` | HTTP API listen port. Overrides `api.port` in `claw_config.yaml` and the `API_PORT` env var. |
| `--gw-host HOST` | string | from config | gRPC gateway bind host. Overrides `gateway.host` in `claw_config.yaml`. |
| `--gw-port PORT` | integer | from config | gRPC gateway port. Overrides `gateway.port` in `claw_config.yaml`. |
| `--gw-tls` | flag | from config | Enable TLS on the gRPC gateway. Overrides `gateway.tls`. Requires `GATEWAY_TLS_CERT_FILE` and `GATEWAY_TLS_KEY_FILE` to be set. |
| `--api-key KEY` | string | from config | Require `X-API-Key: KEY` on all `/v1/*` requests. Overrides `api.key` in `claw_config.yaml` and `API_KEY` env var. |

**HTTP API endpoints** (available when `--api` is used):

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/agent/completions` | Submit a task asynchronously. Returns `job_id` immediately. |
| `POST` | `/v1/agent/completions/sync` | Submit a task and wait for the result (up to `timeout` seconds, default 300). |
| `GET` | `/v1/agent/jobs/{job_id}` | Poll job status and fetch result when done. |
| `GET` | `/v1/agent/jobs` | List recent jobs (most recent `limit`, default 50). |
| `GET` | `/docs` | Swagger UI — interactive API explorer. |
| `GET` | `/health` | Liveness check. Returns `{"status": "ok"}`. |

**Examples:**

```bash
# Messaging platforms only (Telegram, Discord, WhatsApp)
clawswarm run

# Add the public REST API on port 8080
clawswarm run --api

# REST API on a custom port
clawswarm run --api --port 9000

# Override gateway port at runtime without editing claw_config.yaml
clawswarm run --gw-port 50052

# Lock the REST API with an auth key
clawswarm run --api --api-key my-secret-key

# Full production flags
clawswarm run --api --port 443 --gw-tls --api-key $API_KEY
```

---

### `clawswarm settings`

Display the current live configuration, merged from `claw_config.yaml`, `.env`, and the shell environment.

```
Usage: clawswarm settings
```

Output is grouped into four Rich panels:

| Panel | Variables shown |
|-------|----------------|
| **Gateway** | `GATEWAY_HOST`, `GATEWAY_PORT`, `GATEWAY_TLS` |
| **API** | `API_PORT`, `API_KEY` |
| **Models** | `AGENT_MODEL`, `WORKER_MODEL_NAME` |
| **Platforms** | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_IDS`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` |

Secret values (anything ending in `_KEY`, `_TOKEN`, or `ACCESS_TOKEN`) are masked: only the first 8 characters are shown followed by `...`. Unset variables display `(not set)`.

```bash
clawswarm settings
```

---

## Production configuration examples

### Minimal local setup

For local development with default ports and no auth:

```yaml
# claw_config.yaml
agent:
  name: MyBot
  description: My personal AI assistant

worker:
  model_name: gpt-4o-mini

gateway:
  host: "[::]"
  port: 50051
  tls: false

api:
  port: 8080
  key: ""

runtime:
  verbose: true
```

```bash
# .env
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=...
```

```bash
clawswarm run --api
```

---

### Public server with auth

For a VPS or cloud instance where the HTTP API is exposed to the internet:

```yaml
# claw_config.yaml
agent:
  name: ProductionBot
  description: Production ClawSwarm deployment

worker:
  model_name: gpt-4o

gateway:
  host: "[::]"
  port: 50051
  tls: false       # gateway is on localhost; no external TLS needed

api:
  port: 8080
  key: ""          # set API_KEY in .env — never commit the key

runtime:
  verbose: false
```

```bash
# .env
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=...
DISCORD_BOT_TOKEN=...
API_KEY=your-strong-random-key-here
```

```bash
clawswarm run --api
```

Clients authenticate with:

```http
POST /v1/agent/completions
X-API-Key: your-strong-random-key-here
Content-Type: application/json

{"task": "Summarise the latest news on AI agents"}
```

---

### TLS-enabled gateway

For deployments where the gRPC gateway is accessed by an external client (not just the local agent loop):

```yaml
# claw_config.yaml
gateway:
  host: "[::]"
  port: 50051
  tls: true
```

```bash
# .env
GATEWAY_TLS_CERT_FILE=/etc/ssl/clawswarm/server.crt
GATEWAY_TLS_KEY_FILE=/etc/ssl/clawswarm/server.key
```

```bash
clawswarm run --api
```

> In most single-host deployments the gateway and agent run on the same machine. TLS is only necessary if remote clients connect to the gRPC port directly.

---

### Docker / Railway

Pass `claw_config.yaml` as a volume-mounted file or set env vars directly. Env vars override the config file so you can bake defaults into the YAML and override secrets at runtime.

**Docker:**

```bash
docker run \
  --env-file .env \
  -v $(pwd)/claw_config.yaml:/app/claw_config.yaml \
  -v $(pwd)/agent_memory.md:/app/agent_memory.md \
  -p 8080:8080 \
  clawswarm
```

**Railway** — commit `claw_config.yaml` to your repo (it contains no secrets) and add all secrets in the Railway dashboard under *Variables*. The config file is picked up automatically on deploy.

---

## Environment variable mapping

Every `claw_config.yaml` field maps to an environment variable. Env vars always take precedence over the file.

| YAML path | Environment variable | Type | Default |
|-----------|---------------------|------|---------|
| `agent.name` | `CLAWSWARM_AGENT_NAME` | string | `ClawSwarm` |
| `agent.description` | `CLAWSWARM_AGENT_DESCRIPTION` | string | `A hierarchical swarm...` |
| `worker.model_name` | `WORKER_MODEL_NAME` | string | `gpt-4o-mini` |
| `gateway.host` | `GATEWAY_HOST` | string | `[::]` |
| `gateway.port` | `GATEWAY_PORT` | integer | `50051` |
| `gateway.tls` | `GATEWAY_TLS` | `0` or `1` | `0` |
| `api.port` | `API_PORT` | integer | `8080` |
| `api.key` | `API_KEY` | string | `""` |
| `runtime.verbose` | `CLAWSWARM_VERBOSE` | `0` or `1` | `0` |

---

## Troubleshooting

**`claw_config.yaml` not found / wizard runs every time**

The config loader walks up from the current working directory looking for a `pyproject.toml` or `.git` directory to identify the project root. Run `clawswarm` commands from the project root, or run `clawswarm onboarding` once to create the file there.

**My changes to `claw_config.yaml` are being ignored**

Check if an environment variable with the same name is already set in your shell or `.env` — env vars take precedence over the file. Run `clawswarm settings` to see the resolved values.

**Gateway port already in use**

Change the port in `claw_config.yaml` under `gateway.port`, or override at runtime:

```bash
clawswarm run --gw-port 50052
```

**API key is set but requests still go through without it**

`api.key` in `claw_config.yaml` is applied via `os.environ.setdefault`, so if `API_KEY` is already set (e.g. to an empty string) in your environment it takes precedence and disables auth. Run `clawswarm settings` to verify `API_KEY` shows the expected value. Set it explicitly in `.env` to be certain.

**TLS fails to start**

Ensure both `GATEWAY_TLS_CERT_FILE` and `GATEWAY_TLS_KEY_FILE` are set and point to readable files. The certificate must be signed by a CA trusted by any connecting clients (or use `--insecure` in your gRPC client for self-signed certs during development).

**`onboarding --force` did not update my running instance**

The running `clawswarm run` process loaded the config at startup. Restart the process after regenerating the file for changes to take effect.
