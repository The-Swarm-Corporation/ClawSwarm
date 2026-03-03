# ClawSwarm: Every Feature, How It Was Added, and How It Works

This document walks through every meaningful commit in ClawSwarm's history and maps each one to the actual code it produced. For each feature you get: what was added, where to find it, and how the implementation works at a technical level.

---

## 1. Hierarchical Multi-Agent Architecture
**Commits:** `main agent architecture`, `functional hierarchical`, `improved architecture`
**File:** `claw_swarm/agent/main.py`

The core of ClawSwarm is a `HierarchicalSwarm` from the `swarms` library. The `create_agent()` function at `agent/main.py:71` assembles the swarm:

```python
return HierarchicalSwarm(
    name=name,
    description=desc,
    agents=WORKER_AGENTS,           # [response, developer, search, token_launch]
    director_name=name,
    director_model_name=director_model,
    director_system_prompt=director_system_prompt,
    director_feedback_on=False,
    director=None,
)
```

The director agent receives the full task, decides which worker agents to dispatch subtasks to, and aggregates their results. The four worker agents are instantiated at module load time (`agent/main.py:24-29`) as a module-level list `WORKER_AGENTS`, so they are shared across all swarm instances in a process.

The public entry point `hierarchical_swarm(task)` at `agent/main.py:123` is a thin wrapper: it calls `create_agent().run(task)` inside a try/except that logs and returns `None` on failure, so callers never have to handle swarm exceptions themselves.

---

## 2. Four Specialized Worker Agents
**Commit:** `functional hierarchical`, `re organize agents and memory file in agents folder`
**File:** `claw_swarm/agent/worker_agents.py`

Each worker is a factory function that returns a `swarms.Agent` instance. They all follow the same pattern: build a full system prompt by calling `build_agent_system_prompt()`, resolve the model name via `resolve_model()`, and pass tool functions directly in the `tools=` argument.

**Response agent** (`create_response_agent`, line 229) — no tools, `max_loops=1`, used for greetings, clarifications, and simple factual answers. Deployed with `output_type="final"` so only the last message in a turn is returned.

**Search agent** (`create_search_agent`, line 266) — registered with three tools: `exa_search`, `scrape_url`, and `scrape_urls`. The system prompt at line 58 instructs it to start with `exa_search` for discovery, then call `scrape_url`/`scrape_urls` to read the full content of relevant links. If a URL is provided directly, it skips the search step.

**Token launch agent** (`create_token_launch_agent`, line 308) — tools are `launch_token` and `claim_fees`. The prompt guards against accidental launches: "Do not launch tokens or claim fees without explicit user intent."

**Developer agent** (`create_developer_agent`, line 350) — has a single tool `_run_claude_developer` (line 207), which itself calls `run_claude_agent()` from `claude_code_tool.py`. This means the developer agent delegates to a live Claude Code session that has access to `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`, and up to 120 turns.

---

## 3. Claude Code as a Developer Tool
**Commit:** `main agent architecture`
**File:** `claw_swarm/tools/claude_code_tool.py`

This is the bridge between the swarms framework and the Claude Agent SDK. Three functions are exported:

- `run_claude_agent(name, description, prompt, tasks)` — synchronous, blocks until done
- `run_claude_agent_async(...)` — async version, returns `list[str]`
- `stream_claude_agent(...)` — async generator, yields text blocks as they arrive

All three converge on `stream_claude_agent` (line 49), which builds a `ClaudeAgentOptions` with `tools={"type": "preset", "preset": "claude_code"}` and calls the SDK's `query()`. This gives every session access to the full Claude Code tool preset. The synchronous wrapper uses `anyio.run()` to block until the async generator is exhausted (line 140).

The system prompt injected into every Claude Code session is assembled by `build_agent_system_prompt()`, which prepends agent name and description to the caller-supplied prompt, ensuring the inner Claude Code session knows its identity and constraints.

---

## 4. Tools Registry
**Commit:** `tools registry, launch token and claim fees`
**File:** `claw_swarm/tools/__init__.py`

The registry is a flat list `tools` at module level:

```python
tools = [
    claim_fees, launch_token,
    run_claude_agent, run_claude_agent_async, stream_claude_agent,
    exa_search,
    scrape_url, scrape_urls,
]
```

This single import point means any code that needs all available tools can do `from claw_swarm.tools import tools` rather than importing from four separate modules. Individual worker agents still import their specific tools directly, but the registry exists for cases where a caller wants to enumerate or introspect all available capabilities.

---

## 5. Token Launch and Fee Claiming
**Commit:** `tools registry, launch token and claim fees`
**File:** `claw_swarm/tools/launch_tokens.py`

`launch_token(name, description, ticker, image?, image_path?)` at line 138 posts to `https://swarms.world/api/token/launch`. It branches on `image_path`: if a local file path is given, the request is sent as `multipart/form-data` with the raw bytes; otherwise it sends JSON with an optional `image` field for a URL or base64 string.

Both API key and wallet private key are pulled from environment variables (`SWARMS_API_KEY`, `WALLET_PRIVATE_KEY`). The key loader at line 27 strips surrounding quotes to handle common `.env` formatting mistakes. On any 4xx/5xx response, `_log_api_error()` at line 71 emits a structured log entry with the exact error shape (field errors for 400, rate limit reset time for 429, etc.) before re-raising as `httpx.HTTPStatusError`.

`claim_fees(ca)` at line 308 is simpler: it POSTs the token contract address and private key to `/api/product/claimfees`. No API key is required for this endpoint — only the wallet key for signing. Return value is a JSON string with `success`, `signature`, `amountClaimedSol`, and `fees`.

---

## 6. Web Scraping for the Search Agent
**Commit:** `[FEAT][web scraping for the search agent]`
**File:** `claw_swarm/tools/web_scraper.py`

Two public functions are exposed as agent tools:

`scrape_url(url)` at line 93 calls internal `_fetch_text()`, which uses `httpx` with `follow_redirects=True` and a custom `User-Agent` header. Content-type detection at line 79 branches on whether the response is HTML/text (parse it) or something else (return raw text).

HTML parsing is done with a minimal stdlib `HTMLParser` subclass `_TextExtractor` at line 37. It tracks a `_skip_depth` counter — incremented on open tags from `_SKIP_TAGS` (script, style, noscript, head, meta, link, iframe, svg, path) and decremented on close tags. Text nodes are only collected when `_skip_depth == 0`. After collection, `get_text()` at line 57 joins parts, unescapes HTML entities, collapses whitespace, and normalizes runs of blank lines. No external dependency is needed beyond `httpx`, which is already in the project.

`scrape_urls(urls)` at line 114 accepts either a list or a newline/comma-separated string. It iterates, calls `scrape_url` for each, and returns all results delimited by `=== <url> ===` headers. Errors are prefixed with `ERROR:` so the agent's system prompt can instruct it to skip failed URLs and move to the next source.

---

## 7. Persistent Agent Memory
**Commit:** `memory section for readme`, `re organize agents and memory file in agents folder`
**File:** `claw_swarm/agent/memory.py`

`append_interaction()` at line 47 appends a markdown block to `agent_memory.md` at the project root. Each block records: UTC timestamp, platform (Telegram/Discord/WhatsApp/API), channel ID, optional thread ID, sender handle, the user's message, and the agent's reply.

`read_memory()` at line 30 reads the file and trims to the last `MAX_MEMORY_CHARS` characters (default 100,000, overridable via `AGENT_MEMORY_MAX_CHARS`). The agent runner at `agent_runner.py:116` injects this into every task context between the system prompt and the current message:

```
[Your system instructions - follow these]
<CLAWSWARM_SYSTEM>

[Previous conversation context from memory]
<read_memory()>

[Current message to answer]
<user text>
```

This gives the agent cross-session and cross-platform memory without touching the model's context window on initial load — memory is only fetched at message processing time. The `OSError` catch at line 77 means a full disk or read-only filesystem silently skips the write rather than crashing the agent loop.

---

## 8. HTTP API Server
**Commit:** `[FEAT][API server for claw-swarm agent]`
**File:** `claw_swarm/api/server.py`

A FastAPI application with a FIFO job queue. On startup, `_lifespan()` at line 269 spawns a single background coroutine `_worker()` that drains `_job_queue` one job at a time. This intentional serialization prevents concurrent swarm calls from racing over shared agent state.

The agent is instantiated once inside `_worker()` and reused across jobs (line 167-168). Each job runs `agent.run()` in a thread pool via `asyncio.to_thread()` so the event loop stays unblocked.

Two task submission endpoints:

- `POST /v1/agent/completions` (line 384) — enqueues the task, returns `job_id` and a `poll_url` immediately with HTTP 202. The caller polls `GET /v1/agent/jobs/{job_id}` until `status` is `done` or `failed`.
- `POST /v1/agent/completions/sync` (line 411) — enqueues and waits on an `asyncio.Event` with a configurable timeout (default 300s). Returns the result inline.

Authentication is an `_verify_api_key` dependency at line 109 applied to all `/v1/*` routes. If `API_KEY` is set in the environment, every request must include a matching `X-API-Key` header. If `API_KEY` is empty, the API is open.

On startup the server fetches the machine's public IP from three fallback URLs (`ipify.org`, `checkip.amazonaws.com`, `icanhazip.com`) and prints both local and public URLs in a Rich panel so you immediately know the address to share.

---

## 9. Environment-Based Model Name Override
**Commit:** `[FEAT][Env fetch worker model name from env]`
**File:** `claw_swarm/agent/model_config.py`

`resolve_model(model_name, default)` at line 6 implements a four-level precedence chain:

1. Explicit argument to the factory function
2. `WORKER_MODEL_NAME` environment variable
3. `AGENT_MODEL` environment variable
4. Hardcoded default (typically `"gpt-4o-mini"`)

Every worker agent factory calls this when resolving its model. This means you can swap all worker agents to a different model at deploy time without touching source code — just set `WORKER_MODEL_NAME=gpt-4.1` in your environment.

---

## 10. ClawConfig and the Configuration System
**Commit:** `[feat][rich onboarding wizard for claw_config.yaml]`
**File:** `claw_swarm/config.py`

`ClawConfig` at line 32 is a `dataclass` with eight fields organized into five logical sections: agent (name, description), worker (model_name), gateway (host, port, tls), api (port, key), and runtime (verbose). All fields have defaults so an empty `ClawConfig()` is always valid.

`from_dict()` at line 49 parses a nested YAML dict. Each section is read with `.get()` and a fallback default, so partial YAML files are safe. `to_dict()` at line 76 is the inverse — used when writing the config from the onboarding wizard.

`apply_config_to_env()` at line 131 uses `os.environ.setdefault()` for all fields except `verbose`, which is always written. `setdefault` means already-set environment variables win over the config file, establishing the precedence: shell env > config file > code defaults.

`_find_project_root()` at line 96 walks up the directory tree (max 10 levels) looking for `pyproject.toml` or `.git`, so the config file is always resolved relative to the project root regardless of which subdirectory the CLI is invoked from.

---

## 11. Interactive Onboarding Wizard
**Commit:** `[feat][rich onboarding wizard for claw_config.yaml]`
**File:** `claw_swarm/config.py:189`

`onboarding_interactive()` walks the user through five sections (Agent, Worker, Gateway, HTTP API, Runtime) using Rich's `Prompt.ask()` and `Confirm.ask()`. Port fields use `_prompt_int()` at line 163, which loops until the user enters a valid integer rather than crashing on bad input.

After all prompts are answered, a Rich table summarizes every setting — API keys are truncated to 8 characters plus `...` so they are visible but not fully exposed. Once the user sees the summary, the config is written atomically to `claw_config.yaml` via standard file open in write mode.

If the file already exists and `force=False`, the wizard prints a warning panel and returns the existing config without prompting. Pass `--force` to overwrite.

---

## 12. The `clawswarm` CLI
**Commit:** `[feat][rich onboarding wizard...]`
**File:** `claw_swarm/cli.py`

Three subcommands are registered:

`clawswarm run` (line 89) — starts the gRPC gateway as a subprocess, optionally starts the HTTP API server as a second subprocess, then runs the agent loop in the main process. It waits 2 seconds after launching subprocesses to give them time to bind, then checks `poll()` on each to catch immediate crashes before the agent loop begins. On exit (normal or exception), `_kill_all()` terminates both subprocesses with a 5-second graceful window before SIGKILL.

`clawswarm run` accepts `--gw-host`, `--gw-port`, `--gw-tls`, and `--api-key` flags that write directly to `os.environ` after config loading, making them override everything lower in the precedence chain (line 117-127).

`clawswarm settings` (line 192) — loads `.env`, groups all config keys into four Rich panels (Gateway, API, Models, Platforms), and masks any key ending in `_TOKEN` or `_KEY`.

`clawswarm onboarding` (line 260) — delegates to `onboarding_interactive()` with the `--force` flag passed through.

---

## 13. Messaging Gateway with Platform Adapters
**Files:** `claw_swarm/gateway/server.py`, `claw_swarm/gateway/adapters/`

The gateway is a gRPC server that normalizes messages from Telegram, Discord, and WhatsApp into a `UnifiedMessage` schema. Each platform has its own adapter (`discord_adapter.py`, `telegram_adapter.py`, `whatsapp_adapter.py`) inheriting from `adapters/base.py`. The agent runner connects to the gateway over an insecure gRPC channel, polls with `PollMessages(since_timestamp_utc_ms)`, and processes each `UnifiedMessage` independently.

---

## 14. Agent Bootup Sequence
**Commit:** `cool bootup sequence`

The agent runner at `agent_runner.py:235` prints a startup message to stderr before entering the polling loop. The API server prints a Rich panel on lifespan startup (server.py:279). Together these give operators immediate confirmation that both the gateway connection and the agent are live, and the API server's startup output includes the exact public URL to share.

---

## 15. CI/CD Pipeline
**Commits:** `github workflows`, Dependabot bumps for `setup-python`, `checkout`, `cache`, `codeql-action`
**Files:** `.github/workflows/`

GitHub Actions runs tests on push and pull requests. Dependabot keeps CI action versions current — `actions/setup-python` moved from v5 to v6, `actions/checkout` from v4 to v6, `actions/cache` from v4 to v5, and `github/codeql-action` from v3 to v4. CodeQL provides static security analysis on every push. The `ruff` linter was updated from `<0.14.15` to `<0.15.3` to track new Python syntax support.

---

## 16. Dockerfile and Railway Deployment
**Commits:** `dockerfile`, `rail way deployment`
**Files:** `Dockerfile`, `railway.toml` (or equivalent)

The Dockerfile packages the application for container deployments. Railway deployment configuration allows `git push`-triggered deploys to Railway's platform, providing an externally accessible URL without manual server management.

---

## Summary of the Call Stack for a Live Message

To ground all of the above in one flow: when a Telegram user sends a message, the platform adapter delivers it to the gRPC gateway. `agent_runner.run_agent_loop()` polls via `stub.PollMessages()`, deserializes the message into `UnifiedMessage`, and calls `_process_message()`. That function prepends the system prompt and memory context, then calls `agent.run()` in a thread pool. The `HierarchicalSwarm` director determines which worker agents to call (search, developer, token launch, or response), each of which calls its registered tool. The result is summarized by `summarize_for_telegram()`, persisted to `agent_memory.md` via `append_interaction()`, and sent back via `send_message_async()`. The same path is triggered over HTTP when a task is submitted to `POST /v1/agent/completions`.
