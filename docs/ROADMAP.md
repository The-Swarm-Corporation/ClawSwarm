# ClawSwarm Feature Roadmap

What ClawSwarm has today: a hierarchical swarm (director + 4 workers) connected
to Telegram, Discord, and WhatsApp via a gRPC gateway, a FastAPI HTTP API, flat
markdown memory, SQLite message logging, and a CLI. Every proposed feature below
is scoped to what the codebase actually lacks — no duplicates of existing work.

---

## 1. Per-User Conversation Memory

**What:** Separate memory contexts per `sender_id` instead of one global
`agent_memory.md`. Each user gets their own sliding window of history.

**Why it matters:** Right now every user on every platform shares the same
memory file. User A's conversation bleeds into User B's context. At any
meaningful scale this produces confused, cross-contaminated replies.

**Where to build it:**
- `claw_swarm/agent/memory.py` — `append_interaction` and `read_memory`
  accept a `sender_id` argument; store to `memory/{platform}_{sender_id}.md`
- `agent_runner.py:_process_message` — pass `msg.sender_id` through

**New CLI hook:** `clawswarm memory clear --user <sender_id>` — lets an
operator wipe one user's history without touching everyone else's.

---

## 2. Streaming Responses Back to Telegram / Discord

**What:** Send the agent reply token-by-token (or in chunks) as it arrives,
editing the same message in Telegram or posting incremental updates in Discord.

**Why it matters:** The swarm can take 15-30 seconds on complex tasks. Users
staring at silence assume the bot is broken. Streaming makes latency feel
acceptable.

**Where to build it:**
- `claw_swarm/tools/claude_code_tool.py` already has `stream_claude_agent()`
  — an async generator that yields text blocks
- `claw_swarm/replier.py` — add `stream_message_async(platform, channel_id,
  text_gen)` that calls the Telegram `editMessageText` API on each chunk
- `agent_runner.py:_process_message` — switch from `agent.run()` to a
  streaming variant when the platform supports edit-in-place

---

## 3. Vision / Image Input

**What:** When a user attaches a photo, pass it to a vision-capable model
(GPT-4o or Claude) instead of ignoring it.

**Why it matters:** `UnifiedMessage` already has `attachment_urls: list[str]`.
The field is populated but never consumed by any worker. Image messages today
fall through as `(no text)`.

**Where to build it:**
- New worker: `create_vision_agent` in `worker_agents.py` — uses
  `gpt-4o` or `claude-opus-4-6`, receives image URLs via the task string
- `agent_runner.py:_process_message` — if `msg.attachment_urls` is non-empty,
  prepend `[Attached images]: <urls>` to the task context
- Director system prompt — describe when to route to the vision worker

---

## 4. Voice Message Transcription

**What:** When a Telegram voice note or Discord audio file arrives, transcribe
it with Whisper before passing the text to the agent.

**Why it matters:** Voice messages are the dominant input format on Telegram
for many user demographics. Ignoring audio makes the bot feel half-functional
on mobile.

**Where to build it:**
- New tool: `claw_swarm/tools/transcribe.py` — calls OpenAI Whisper API
  (`POST /v1/audio/transcriptions`) with the audio URL downloaded via httpx
- `agent_runner.py:_process_message` — detect audio `attachment_urls` by
  extension (`.ogg`, `.mp3`, `.wav`, `.m4a`), transcribe, prepend
  `[Transcribed voice]: <text>` to the task

---

## 5. Plugin / Custom Tool Registry

**What:** Let operators drop a Python file into a `plugins/` directory and have
its functions automatically discovered and registered as agent tools, without
touching the core source.

**Why it matters:** Today adding a tool means editing `worker_agents.py` and
`tools/__init__.py`. This couples user customization to the library itself.
A plugin system lets the project grow without a fork for every custom tool.

**Where to build it:**
- `claw_swarm/plugins.py` — scan `./plugins/*.py` at startup, import each
  module, collect callables decorated with `@clawswarm_tool`, add them to
  a `PLUGIN_TOOLS` list
- `claw_swarm/agent/worker_agents.py` — pass `PLUGIN_TOOLS` into the
  response agent (or a new generic "plugin worker") at creation time
- CLI: `clawswarm plugins list` — print discovered tools and their docstrings

---

## 6. Per-Platform and Per-User Rate Limiting

**What:** Cap how many messages a single `sender_id` can send per minute/hour.
Return a friendly hold-on message instead of hammering the LLM.

**Why it matters:** One power user (or a bot) can monopolize the agent,
exhausting API credits and introducing latency for everyone else.

**Where to build it:**
- New module: `claw_swarm/rate_limiter.py` — an in-memory token-bucket
  keyed on `(platform, sender_id)`. Configurable via env vars:
  `RATE_LIMIT_RPM` (requests per minute), `RATE_LIMIT_RPH`
- `agent_runner.py:_process_message` — check the limiter before processing;
  if throttled, send the rate-limit message and return early
- Include a bypass list (`RATE_LIMIT_BYPASS_IDS`) for trusted admins

---

## 7. Allowlist / Blocklist for Users and Channels

**What:** Restrict the agent to a defined set of `sender_id`s or `channel_id`s,
or explicitly ban specific users.

**Why it matters:** Deploying to production without access control means the
bot is open to anyone who finds the Telegram handle. A simple flat-file or
env-var gate prevents unexpected usage.

**Where to build it:**
- `claw_swarm/access.py` — load `CLAWSWARM_ALLOWLIST` and
  `CLAWSWARM_BLOCKLIST` env vars (comma-separated IDs); expose
  `is_allowed(sender_id, channel_id) -> bool`
- `agent_runner.py:run_agent_loop` — call `is_allowed` before
  `_process_message`; silently drop blocked messages or send a single
  rejection notice

---

## 8. `clawswarm test` — Direct Agent Prompt from CLI

**What:** Run a single task through the full agent stack from the terminal and
print the reply, without starting the gateway or any platform adapter.

**Why it matters:** The current dev loop requires starting gateway + agent,
sending a real Telegram message, and reading the reply in the chat. A direct
CLI test command cuts that to one command with instant output.

**Where to build it:**
- `cli.py` — new `test` subcommand: `clawswarm test "your prompt here"`
- Calls `create_agent().run(task)` directly (no gRPC, no gateway), prints
  the raw and summarized output
- Flags: `--raw` (skip summarization), `--no-memory` (skip memory injection),
  `--worker search|developer|response|token` (bypass director, target one worker)

---

## 9. `clawswarm stats` — Message Statistics from the DB

**What:** Query the SQLite message log and print summary stats: total messages,
breakdown by platform and direction, average response length, most active
channels, messages per day.

**Why it matters:** The `logs` dump command exports raw rows. Stats gives
operators a quick health-check view without opening a markdown file.

**Where to build it:**
- `cli.py` — new `stats` subcommand
- `db.py` — add `fetch_stats() -> dict` that runs aggregate SQL queries
- Rich table output in the terminal; optional `--json` flag for scripting

Example output:
```
Total messages:   1,482  (741 input / 741 output)
Platforms:        telegram 1,100 | discord 320 | api 62
Most active:      channel 8823721 (432 exchanges)
Period:           2025-03-01 → 2025-04-07  (38 days)
Avg reply length: 284 chars
```

---

## 10. Vector Memory (Semantic Search over Past Conversations)

**What:** Replace the sliding-window markdown file with a local vector store
(e.g. ChromaDB or sqlite-vec). On each message, retrieve the top-k most
semantically relevant past exchanges rather than the most recent N characters.

**Why it matters:** The current memory system is purely recency-based.
If a user asked something important three weeks ago and there have been 500
exchanges since, that context is gone. Vector retrieval surfaces relevant
history regardless of when it happened.

**Where to build it:**
- `claw_swarm/agent/memory.py` — add `append_vector` and `query_memory(text,
  top_k)` functions using ChromaDB's persistent client
- `agent_runner.py:_process_message` — replace `read_memory()` with
  `query_memory(task, top_k=10)` to inject only relevant past context
- Fallback: if ChromaDB is not installed, silently fall back to the
  existing file-based memory
- New dep: `chromadb` (optional, in `[tool.poetry.dependencies]` as optional)

---

## 11. Webhook Mode (Push Instead of Poll)

**What:** Instead of the agent runner polling the gRPC gateway every 5 seconds,
let platforms push messages to a webhook endpoint and process them immediately.

**Why it matters:** Polling introduces up to 5 seconds of latency on every
message. Webhooks give near-instant response times and eliminate the gRPC
gateway process entirely for simple single-platform deployments.

**Where to build it:**
- `claw_swarm/api/server.py` — add `POST /webhook/telegram`,
  `POST /webhook/discord` endpoints that parse the platform payload,
  construct a `UnifiedMessage`, and call `_process_message()` directly
- `cli.py` — `clawswarm run --webhook` flag that skips the gateway subprocess
  and registers the webhook with the platform's API on startup
- Telegram: call `setWebhook` with the public URL on startup;
  Discord: verify the interaction signature header

---

## 12. Slack Adapter

**What:** Add Slack as a fourth supported platform alongside Telegram, Discord,
and WhatsApp.

**Why it matters:** Slack is the primary messaging platform for engineering
teams — the most likely internal deployment environment for ClawSwarm. It is a
larger gap than it appears: the existing adapters cover consumer chat; Slack
covers professional/enterprise use.

**Where to build it:**
- `claw_swarm/gateway/adapters/slack_adapter.py` — implement
  `MessageAdapter` using the Slack Web API (`channels.history`) for polling
  and Slack's Events API for webhook mode
- `claw_swarm/replier.py` — add `Platform.SLACK = 4` case, call
  `chat.postMessage`
- `gateway/proto/messaging_gateway.proto` — add `SLACK = 4` to the
  `Platform` enum; regenerate protobuf files
- New env vars: `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_IDS`

---

## 13. Response Caching

**What:** Cache agent replies for identical inputs for a configurable TTL.
Return the cached answer instantly without hitting any LLM.

**Why it matters:** Repeated FAQ-style questions ("what can you do?", "what's
the price of X?") hit the LLM every time. Caching them cuts latency to
milliseconds and meaningfully reduces API costs on high-traffic deployments.

**Where to build it:**
- `claw_swarm/cache.py` — SHA-256 hash of the task text as cache key;
  store in the existing SQLite DB in a `response_cache` table with
  `(key, reply, expires_at_ms)`
- `agent_runner.py:_process_message` — check cache before `agent.run()`;
  write to cache after a successful reply
- Env vars: `CACHE_TTL_SECONDS` (default 3600), `CACHE_ENABLED` (default off)

---

## 14. Multi-Language Auto-Detection and Response

**What:** Detect the language of each incoming message and instruct the agent
to reply in the same language, without any user configuration.

**Why it matters:** ClawSwarm is deployed across Telegram communities that are
frequently multilingual. Forcing English replies on non-English speakers
dramatically reduces usefulness.

**Where to build it:**
- `agent_runner.py:_process_message` — use `langdetect` (stdlib-sized, no
  API calls) to detect `msg.text` language; append to task context:
  `[Reply in: Spanish]`
- Director system prompt update — add instruction to respect the language tag
- Env var: `FORCE_REPLY_LANGUAGE=en` to override detection globally

---

## 15. Scheduled / Cron Tasks

**What:** Let users (or operators) schedule recurring tasks — "summarize the
latest news every morning at 9am", "remind channel X about the standup every
Monday".

**Why it matters:** ClawSwarm can already do the work (search agent, response
agent) — it just has no way to trigger tasks on a schedule. This unlocks a
whole category of proactive agent behavior without building a separate system.

**Where to build it:**
- `claw_swarm/scheduler.py` — async task loop; load schedule from
  `claw_config.yaml` under a `schedules:` key (cron strings + task text +
  target platform/channel)
- `agent_runner.py:run_agent_loop` — start scheduler coroutine alongside the
  poll loop
- CLI: `clawswarm schedule add --cron "0 9 * * *" --task "morning news brief"
  --platform telegram --channel <id>`
- Dep: `croniter` for cron string parsing (lightweight, no daemon required)

---

## 16. Agent Persona per Channel

**What:** Configure different agent names, system prompts, and personalities
for different channels or platforms — one channel gets a formal enterprise
assistant, another gets a casual community helper.

**Why it matters:** The current system uses one global `CLAWSWARM_SYSTEM`
prompt for all channels. Multi-tenant deployments (one ClawSwarm instance
serving multiple communities or brands) need isolated identities.

**Where to build it:**
- `claw_config.yaml` — add an optional `personas:` section mapping
  `channel_id` or `platform` to overrides: `name`, `system_prompt`, `model`
- `claw_swarm/config.py` — `get_persona(platform, channel_id)` resolves
  the most specific matching persona, falling back to global defaults
- `agent_runner.py:_process_message` — call `get_persona` and use the
  returned system prompt instead of the global `CLAWSWARM_SYSTEM`

---

## Summary Table

| # | Feature | Impact | Effort | Where |
|---|---------|--------|--------|-------|
| 1 | Per-user memory | High | Low | `agent/memory.py`, `agent_runner.py` |
| 2 | Streaming responses | High | Medium | `replier.py`, `agent_runner.py` |
| 3 | Vision / image input | High | Low | `worker_agents.py`, `agent_runner.py` |
| 4 | Voice transcription | Medium | Low | new `tools/transcribe.py` |
| 5 | Plugin system | High | Medium | new `plugins.py` |
| 6 | Rate limiting | High | Low | new `rate_limiter.py` |
| 7 | Allowlist / blocklist | Medium | Low | new `access.py` |
| 8 | `clawswarm test` CLI | High | Low | `cli.py` |
| 9 | `clawswarm stats` CLI | Medium | Low | `cli.py`, `db.py` |
| 10 | Vector memory | High | Medium | `agent/memory.py` |
| 11 | Webhook mode | High | Medium | `api/server.py`, platform adapters |
| 12 | Slack adapter | High | Medium | new `adapters/slack_adapter.py` |
| 13 | Response caching | Medium | Low | new `cache.py` |
| 14 | Auto-language detection | Medium | Low | `agent_runner.py` |
| 15 | Scheduled / cron tasks | High | Medium | new `scheduler.py` |
| 16 | Per-channel persona | Medium | Medium | `config.py`, `agent_runner.py` |

---

## Deep Analysis: Bugs, Structural Gaps, and Hardening Work

The section above describes new capabilities. This section covers what needs
to be fixed or hardened in code that already exists. Every item below is
grounded in a specific file and line range.

---

### 17. Agent Execution Timeout + Circuit Breaker

**The problem:**
`agent_runner.py:135` — `await asyncio.to_thread(agent.run, task_with_context)`
runs with no timeout. A single stuck LLM call (hung network socket, stalled
tool execution) blocks the entire poll loop forever. All subsequent messages
queue up behind it. The agent effectively freezes.

**What to build:**

- Wrap `agent.run` in `asyncio.wait_for(..., timeout=AGENT_TIMEOUT_SECONDS)`
  where the timeout is configurable via `AGENT_TIMEOUT_SECONDS` env var
  (sensible default: 120s).
- Add a circuit breaker: track consecutive failures per worker type. After
  N failures in a rolling window, stop routing to that worker and reply with
  a degraded-service message. Reset after a cooldown.
- Log the full traceback on timeout, not just `str(e)` (fixes the silent
  swallowing at `agent_runner.py:149`).

**Files:** `agent_runner.py:123–150`, new `claw_swarm/circuit_breaker.py`

---

### 18. Concurrency Semaphore on Message Processing

**The problem:**
`agent_runner.py:195–221` — the poll loop calls `await _process_message()` for
each incoming message in order, but each message runs `agent.run()` in a thread.
Under burst traffic (20 messages in one poll), 20 threads hit the swarm and
downstream LLM APIs simultaneously. OpenAI and Anthropic have per-minute token
and request limits; concurrent bursts cause cascading 429 errors.

**What to build:**

- Add a module-level `asyncio.Semaphore(MAX_CONCURRENT_AGENTS)` in
  `agent_runner.py` (default: 3, configurable via `MAX_CONCURRENT_AGENTS`).
- Acquire the semaphore at the top of `_process_message()`, release in
  `finally`. Messages beyond the limit queue up naturally because the poll
  loop is async.
- Expose current semaphore occupancy in `clawswarm stats`.

**Files:** `agent_runner.py:100–161`

---

### 19. WhatsApp Adapter: Webhook Queue

**The problem:**
`gateway/adapters/whatsapp_adapter.py:45–57` — `fetch_messages()` returns `[]`
unconditionally. The `_drain_queue()` method at line 62 is a stub that returns
`[]`. WhatsApp's Cloud API is push-only (webhooks); polling does not exist.
WhatsApp messages are silently dropped right now.

**What to build:**

- Replace the polling stub with an in-process queue: expose a
  `POST /webhook/whatsapp` route in `api/server.py` that validates the
  WhatsApp webhook signature, parses the payload, and appends a
  `UnifiedMessage` to a `collections.deque` held by the adapter instance.
- `fetch_messages()` drains the deque up to `max_messages` and returns the
  list — making it compatible with the existing poll loop with no other
  changes required.
- On startup (when `WHATSAPP_ACCESS_TOKEN` is set), register the webhook URL
  with the WhatsApp Cloud API via `POST /{phone-number-id}/subscribed_apps`.

**Files:** `gateway/adapters/whatsapp_adapter.py`, `api/server.py`,
`gateway/__main__.py`

---

### 20. Retry + Exponential Backoff for All External Calls

**The problem:**
Every outbound HTTP call in the codebase fails permanently on the first error:

- `replier.py:35–40` — no retry on send failure; the user never gets a reply.
- `tools/launch_tokens.py:259` — 429 on token launch raises immediately.
- `tools/web_scraper.py:104` — transient ECONNRESET causes task failure.
- `gateway/adapters/telegram_adapter.py:77` — API error returns empty list.

**What to build:**

- A shared `claw_swarm/retry.py` module with a single decorator/context
  manager: `@with_retry(max_attempts=3, backoff_base=1.5, retryable_status={429, 500, 502, 503, 504})`.
- Apply it to: `send_message_async` in `replier.py`, `_post_request` in
  `launch_tokens.py`, `_fetch_text` in `web_scraper.py`, and the `getUpdates`
  call in `telegram_adapter.py`.
- On 429, respect the `Retry-After` response header if present.

**Files:** new `claw_swarm/retry.py`, `replier.py`, `tools/launch_tokens.py`,
`tools/web_scraper.py`, `gateway/adapters/telegram_adapter.py`

---

### 21. Long Message Splitting (Replace Silent Truncation)

**The problem:**
`replier.py:128` — Discord replies are truncated to 2000 chars with
`text[:2000]`. `replier.py:188` — WhatsApp truncates to 4096 chars. No
warning is sent. For a developer agent or search agent the reply is often
3000–8000 characters. The user sees a cut-off answer with no indication that
content was lost.

**What to build:**

- A `_split_message(text, limit)` function that splits on paragraph boundaries
  (double newlines), then sentence boundaries, then hard-cuts only as a last
  resort. Returns a `list[str]` where each chunk is within the platform limit.
- In `send_message_async`, iterate the chunks and send each as a separate
  message with a `(1/3)`, `(2/3)` prefix so the user knows there are more
  parts.
- Apply platform-specific limits: Discord 2000, Telegram 4096, WhatsApp 4096.

**Files:** `replier.py:60–205`

---

### 22. Thread-Safe Memory with File Locking

**The problem:**
`agent/memory.py:47–78` — `append_interaction()` opens the file in `"a"` mode
with no locking. The agent runner processes messages in threads
(`asyncio.to_thread`). If two messages finish at the same time, both calls to
`append_interaction()` open the file simultaneously; one write clobbers or
interleaves with the other.

**What to build:**

- Wrap the file write in `agent/memory.py` with `fcntl.flock(fd, LOCK_EX)`
  on Unix and `msvcrt.locking` on Windows (use a try/except `ImportError` to
  branch).
- Also apply this to `read_memory()` with `LOCK_SH` to prevent reading a
  partially-written file.
- Alternatively, introduce a module-level `threading.Lock` (already used in
  `db.py`) as a simpler cross-platform approach since all writes happen in the
  same process.

**Files:** `agent/memory.py:30–85`

---

### 23. Persistent API Job Store

**The problem:**
`api/server.py:90` — `_jobs: Dict[str, JobRecord] = {}` is a plain dict in
process memory. Every API server restart loses all job history. A client that
submits a task, gets a `job_id`, and then polls after the server restarts
receives a 404. At any scale, jobs also accumulate without bound — there is no
cleanup and no maximum size.

**What to build:**

- Back the job store with the existing SQLite database (`db.py`). Add a
  `jobs` table: `(job_id, task, status, result, error, created_at_ms,
  completed_at_ms, metadata)`.
- Add `db.py` functions: `upsert_job`, `get_job`, `list_jobs(limit)`,
  `delete_jobs_older_than(days)`.
- In `api/server.py`, replace all `_jobs[job_id]` reads/writes with the DB
  functions. The in-memory `_job_events` dict (for `asyncio.Event` wakeups)
  stays in memory — it only needs to survive the duration of a sync request.
- Add a startup cleanup: delete jobs older than `JOB_RETENTION_DAYS`
  (default: 7, configurable).

**Files:** `api/server.py:75–233`, `db.py`

---

### 24. Telegram File/Attachment Resolution

**The problem:**
`gateway/adapters/telegram_adapter.py:104` — attachment URLs stored in
`UnifiedMessage.attachment_urls` are raw Telegram `file_id` strings, not
downloadable URLs. The comment on that line reads: "optional: resolve to URL
via getFile". The worker agents receive `file_id=AgACAgIAA...` which they
cannot do anything with. Vision support (feature 3) and voice transcription
(feature 4) both depend on this being fixed first.

**What to build:**

- In `telegram_adapter.py`, after building the `attachment_urls` list, call
  `GET https://api.telegram.org/bot{token}/getFile?file_id={id}` for each
  attachment, then construct the CDN URL:
  `https://api.telegram.org/file/bot{token}/{file_path}`.
- Cache resolved URLs for the session lifetime (file_ids are stable).
- Gate this behind a check: only resolve if `TELEGRAM_RESOLVE_ATTACHMENTS=1`
  to avoid extra API calls for text-only deployments.

**Files:** `gateway/adapters/telegram_adapter.py:90–115`

---

### 25. Discord Pagination and Thread Support

**The problem (two issues):**

1. `gateway/adapters/discord_adapter.py:51` — `self._channel_ids[:20]` silently
   caps at 20 channels. Any channel after the 20th is never polled. No warning
   is emitted.

2. `discord_adapter.py:61` — `if msg.get("type") != 0: continue` drops all
   non-default message types. Type 19 is a reply-to-message; type 21 is a
   thread starter. Threaded conversations are ignored entirely.

**What to build:**

1. Remove the `:20` hard cap. If more than 20 channels are configured, emit a
   startup warning. Optionally parallelize the per-channel `GET
   /channels/{id}/messages` calls with `asyncio.gather` so polling 50 channels
   doesn't take 50× longer.

2. Accept message types `[0, 19, 21]`. For type 19 (reply), populate
   `UnifiedMessage.thread_id` with the referenced message's `channel_id` so
   reply context is preserved. For type 21, populate `thread_id` with the
   thread channel ID.

**Files:** `gateway/adapters/discord_adapter.py:48–80`

---

### 26. Telegram Offset Persistence

**The problem:**
`gateway/adapters/telegram_adapter.py` — `self._offset` is only stored in
memory. If the gateway process restarts (crash, redeploy, `clawswarm run`),
`_offset` resets to `0`. The next `getUpdates` call returns up to 100 buffered
messages, all of which are replayed through the agent. Users receive duplicate
replies to messages they sent hours ago.

**What to build:**

- Persist `_offset` to the SQLite database (`db.py`) in a `kv_store` table:
  `(key TEXT PRIMARY KEY, value TEXT)`.
- On adapter init, read `telegram_offset` from the table (default 0).
- After each successful `getUpdates`, write the new offset back.
- Same pattern should apply to the Discord adapter's `_last_message_ids` dict.

**Files:** `gateway/adapters/telegram_adapter.py:44–80`, `db.py`

---

### 27. Structured Logging with Full Tracebacks

**The problem:**
`agent_runner.py:149` — `except Exception as e: reply_text = f"Sorry, something
went wrong: {e!s}"`. The exception string is sent to the user but the traceback
is discarded. Debugging production failures requires guessing. The same pattern
appears in `api/server.py:222`, `agent/main.py:131`, and `tools/launch_tokens.py`.

`loguru` is already in `pyproject.toml` but is never imported in these modules.

**What to build:**

- Import `loguru.logger` in `agent_runner.py`, `api/server.py`, and all tool
  files. Replace `except Exception as e: print(...)` with
  `logger.exception("message processing failed")` which automatically captures
  the full traceback.
- Add a startup call to configure loguru: `logger.add("clawswarm.log",
  rotation="10 MB", retention="7 days", level="WARNING")` so production logs
  are written to a rotating file, not only stderr.
- Expose log level via `CLAWSWARM_LOG_LEVEL` env var.

**Files:** `agent_runner.py:149`, `api/server.py:222`, `agent/main.py:128–132`,
new logging setup in `cli.py:cmd_run`

---

### 28. Config Validation on Load

**The problem:**
`config.py:127` — `yaml.safe_load(f) or {}` silently turns an invalid or
empty YAML file into an empty dict, applying all defaults. A user who
accidentally corrupts `claw_config.yaml` (e.g., wrong indentation) gets no
error — the agent starts with default settings and behaves unexpectedly.

Port values are read with `int(gateway.get("port", 50051))` but never
range-checked. A port of `99999` or `0` is stored and passed to the gRPC
server, which fails at bind time with an unrelated-looking error.

**What to build:**

- After `yaml.safe_load`, validate the parsed dict against a schema. The
  simplest approach: a `_validate_config(data: dict) -> list[str]` function
  that checks port ranges (1–65535), that model names are non-empty strings,
  and that boolean fields are actually booleans. Return a list of error strings;
  print them as warnings and fall back to defaults per field.
- In `onboarding_interactive()`, validate the port input in `_prompt_int()`
  before accepting it (it currently only checks `int()` conversion, not range).

**Files:** `config.py:49–90`, `config.py:154–186`

---

### 29. API Rate Limiting

**The problem:**
`api/server.py` — the `/v1/agent/completions` endpoint has no rate limit.
Anyone with the API key (or without one if `API_KEY` is unset) can submit
tasks at arbitrary volume. The background worker queues all of them. At high
volume this exhausts memory (unbounded `_job_queue`) and downstream API
credits.

**What to build:**

- Add `slowapi` (a FastAPI-compatible rate limiter built on `limits`) as an
  optional dependency.
- Apply a default of 60 requests/minute per IP address on both completion
  endpoints. Configurable via `API_RATE_LIMIT` env var (format: `"60/minute"`).
- Add a max queue depth check: if `_job_queue.qsize() > MAX_QUEUE_DEPTH`
  (default: 100), return HTTP 503 with a `Retry-After: 30` header.

**Files:** `api/server.py:370–442`

---

### 30. Developer Agent Tool Sandboxing

**The problem:**
`tools/claude_code_tool.py:70–73` — the developer agent runs with
`tools={"type": "preset", "preset": "claude_code"}`, giving it access to
`Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep` with no restrictions. A user
can ask the agent to "delete all Python files" or "read my .env file" and the
agent will comply.

**What to build:**

- Add a configurable tool allowlist via `CLAUDE_CODE_ALLOWED_TOOLS` env var
  (comma-separated, default: `"Read,Grep,Glob,Bash"` — exclude Write and Edit
  for safety).
- Pass the allowlist as a `tools` override in `ClaudeAgentOptions`: use
  `{"type": "list", "tools": [...]}` instead of the preset.
- Add a working directory restriction: create a temporary directory per
  invocation, pass it as the `cwd` argument so file operations are scoped.
- Gate the full-access preset behind `CLAUDE_CODE_UNRESTRICTED=1` for users
  who explicitly want it.

**Files:** `tools/claude_code_tool.py:60–80`

---

## Deep Analysis Summary Table

| # | Issue | Severity | Effort | File(s) |
|---|-------|----------|--------|---------|
| 17 | Agent execution timeout + circuit breaker | Critical | Low | `agent_runner.py` |
| 18 | Concurrency semaphore on message processing | High | Low | `agent_runner.py` |
| 19 | WhatsApp webhook queue (adapter non-functional) | Critical | High | `adapters/whatsapp_adapter.py` |
| 20 | Retry + backoff for all external calls | High | Medium | `replier.py`, `tools/*`, adapters |
| 21 | Long message splitting (no silent truncation) | High | Low | `replier.py` |
| 22 | Thread-safe memory file locking | High | Low | `agent/memory.py` |
| 23 | Persistent API job store | High | Medium | `api/server.py`, `db.py` |
| 24 | Telegram attachment URL resolution | Medium | Low | `adapters/telegram_adapter.py` |
| 25 | Discord pagination + thread/reply support | Medium | Low | `adapters/discord_adapter.py` |
| 26 | Telegram/Discord offset persistence | High | Low | adapters, `db.py` |
| 27 | Structured logging with full tracebacks | High | Low | `agent_runner.py`, `api/server.py` |
| 28 | Config validation on load | Medium | Low | `config.py` |
| 29 | API rate limiting | High | Low | `api/server.py` |
| 30 | Developer agent tool sandboxing | High | Medium | `tools/claude_code_tool.py` |
