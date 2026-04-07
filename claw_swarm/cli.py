"""
CLI for ClawSwarm: run, settings, onboarding.

Usage:
  clawswarm run                        # gateway + agent
  clawswarm run --api                  # + HTTP API on :8080
  clawswarm run --api --port 9000      # custom API port
  clawswarm run --gw-port 50052        # custom gateway port
  clawswarm run --gw-tls               # enable gateway TLS
  clawswarm run --api-key secret       # lock API with a key
  clawswarm settings                   # show live config
  clawswarm onboarding                 # create claw_config.yaml
  clawswarm onboarding --force         # overwrite existing config
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import time

from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from claw_swarm.config import (
    ensure_config_interactive,
    onboarding_interactive,
)

_console = Console()


def _find_dotenv_path() -> str | None:
    """
    Find the path to a .env file by checking the current directory and parents.

    Looks for a directory that contains .env or pyproject.toml (project root)
    so that running `clawswarm run` from any subdirectory still loads .env.
    """
    cwd = os.path.abspath(os.getcwd())
    for _ in range(10):
        if os.path.isfile(os.path.join(cwd, ".env")):
            return os.path.join(cwd, ".env")
        if os.path.isfile(os.path.join(cwd, "pyproject.toml")):
            env_path = os.path.join(cwd, ".env")
            if os.path.isfile(env_path):
                return env_path
        parent = os.path.dirname(cwd)
        if parent == cwd:
            break
        cwd = parent
    return None


def _ensure_dotenv() -> None:
    """
    Load environment variables from a .env file.

    Searches the current directory and parent directories for .env or
    project root (pyproject.toml) so env vars work regardless of cwd.
    """
    path = _find_dotenv_path()
    if path:
        load_dotenv(path)
    else:
        load_dotenv()


def _terminate(proc: subprocess.Popen, name: str) -> None:
    """Gracefully terminate a subprocess; SIGKILL after 5 s."""
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        print(
            f"clawswarm: {name} did not stop; killing.",
            file=sys.stderr,
        )
        proc.kill()


def cmd_run(args: argparse.Namespace) -> int:
    """
    Run the ClawSwarm stack: gateway, agent, and optionally the HTTP API.

    Always starts:
      1. Messaging Gateway  – gRPC server (subprocess)
      2. Agent loop         – polls gateway, runs swarm, sends replies (this process)

    With --api also starts:
      3. HTTP API Server    – FastAPI/uvicorn on 0.0.0.0:API_PORT (subprocess)
         On startup it prints your machine's public IP so you have the exact
         URL to share: http://<public-ip>:<port>/docs

    Relevant env vars
    -----------------
    GATEWAY_HOST   gRPC bind host (default: [::])
    GATEWAY_PORT   gRPC port      (default: 50051)
    API_PORT       HTTP API port  (default: 8080)  [only used with --api]
    API_KEY        If set, /v1/* requests must send X-API-Key: <value>

    Returns:
        0 on normal exit, non-zero if a subprocess fails to start.
    """
    _ensure_dotenv()
    # Load claw_config.yaml; applies defaults to env via setdefault.
    ensure_config_interactive()

    # CLI flags override config / env (explicit > config > default).
    if args.gw_host:
        os.environ["GATEWAY_HOST"] = args.gw_host
    if args.gw_port is not None:
        os.environ["GATEWAY_PORT"] = str(args.gw_port)
    if args.gw_tls:
        os.environ["GATEWAY_TLS"] = "1"
    if args.api_key:
        os.environ["API_KEY"] = args.api_key
    # --port always wins over API_PORT from config
    if args.port != 8080 or not os.environ.get("API_PORT"):
        os.environ["API_PORT"] = str(args.port)
    # Model overrides — write to env so agent_runner picks them up
    if args.model:
        os.environ["AGENT_MODEL"] = args.model
    if args.worker_model:
        os.environ["WORKER_MODEL_NAME"] = args.worker_model

    gw_host = os.environ.get("GATEWAY_HOST", "[::]")
    gw_port = int(os.environ.get("GATEWAY_PORT", "50051"))
    api_port = int(os.environ.get("API_PORT", "8080"))

    env = os.environ.copy()
    env["GATEWAY_HOST"] = gw_host
    env["GATEWAY_PORT"] = str(gw_port)
    env["API_PORT"] = str(api_port)

    # ── 1. Start Messaging Gateway ──────────────────────────────────────
    gw_proc = subprocess.Popen(
        [sys.executable, "-m", "claw_swarm.gateway"],
        env=env,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    # ── 2. (Optional) Start HTTP API Server ─────────────────────────────
    api_proc: subprocess.Popen | None = None
    if args.api:
        api_proc = subprocess.Popen(
            [sys.executable, "-m", "claw_swarm.api"],
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    # Give servers a moment to bind before the agent connects
    time.sleep(2.0)

    if gw_proc.poll() is not None:
        print("clawswarm: gateway exited early.", file=sys.stderr)
        if api_proc is not None:
            _terminate(api_proc, "api-server")
        return gw_proc.returncode or 1

    if api_proc is not None and api_proc.poll() is not None:
        print(
            "clawswarm: API server exited early. "
            "Is fastapi/uvicorn installed? "
            "Run: pip install fastapi 'uvicorn[standard]'",
            file=sys.stderr,
        )
        _terminate(gw_proc, "gateway")
        return api_proc.returncode or 1

    def _kill_all() -> None:
        if api_proc is not None:
            _terminate(api_proc, "api-server")
        _terminate(gw_proc, "gateway")

    # ── 3. Agent loop in this process ───────────────────────────────────
    os.environ["GATEWAY_HOST"] = "127.0.0.1"
    os.environ["GATEWAY_PORT"] = str(gw_port)

    try:
        from claw_swarm.agent_runner import main as agent_main

        return agent_main()
    finally:
        _kill_all()


def cmd_settings(_args: argparse.Namespace) -> int:
    """
    Print current ClawSwarm settings to stdout.

    Loads .env if present, then prints the main configuration keys
    (gateway, agent model, platform tokens). Secret values are masked.

    Returns:
        0 always.
    """
    _ensure_dotenv()

    _SECTIONS = {
        "Gateway": [
            "GATEWAY_HOST",
            "GATEWAY_PORT",
            "GATEWAY_TLS",
        ],
        "API": ["API_PORT", "API_KEY"],
        "Models": ["AGENT_MODEL", "WORKER_MODEL_NAME"],
        "Platforms": [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "TELEGRAM_BOT_TOKEN",
            "DISCORD_BOT_TOKEN",
            "DISCORD_CHANNEL_IDS",
            "WHATSAPP_ACCESS_TOKEN",
            "WHATSAPP_PHONE_NUMBER_ID",
        ],
    }

    _SECRET_SUFFIXES = (
        "_TOKEN",
        "_KEY",
        "ACCESS_TOKEN",
        "API_KEY",
    )

    def _mask(key: str, val: str) -> str:
        if val and key.endswith(_SECRET_SUFFIXES):
            return val[:8] + "..." if len(val) > 8 else "***"
        return val or "[dim](not set)[/dim]"

    _console.print()
    for section, keys in _SECTIONS.items():
        table = Table(
            box=box.ROUNDED,
            border_style="cyan",
            show_header=False,
            padding=(0, 1),
        )
        table.add_column(style="bold", justify="right")
        table.add_column(style="cyan")
        for key in keys:
            val = _mask(key, os.environ.get(key, ""))
            table.add_row(key, val)
        _console.print(
            Panel(
                table,
                title=f"[bold cyan]{section}[/bold cyan]",
                border_style="cyan",
                padding=(0, 1),
            )
        )
        _console.print()
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """
    Print aggregate statistics from the SQLite message log.

    Reads the same database used during agent runtime (controlled by the
    MESSAGE_LOG_DB env var).  Use --json to get machine-readable output.

    Returns:
        0 on success, 1 on error.
    """
    _ensure_dotenv()

    try:
        from claw_swarm.db import fetch_stats, init_db

        init_db()
        s = fetch_stats()
    except Exception as exc:
        _console.print(
            f"[red]Failed to read database:[/red] {exc}",
            highlight=False,
        )
        return 1

    if s["total"] == 0:
        _console.print("[yellow]No messages logged yet.[/yellow]")
        return 0

    if args.json:
        _console.print(json.dumps(s, indent=2))
        return 0

    def _ms_to_date(ms: int) -> str:
        if not ms:
            return "—"
        return datetime.datetime.fromtimestamp(
            ms / 1000, tz=datetime.timezone.utc
        ).strftime("%Y-%m-%d %H:%M UTC")

    # ── Overview panel ───────────────────────────────────────────────
    overview = Table(
        box=box.ROUNDED,
        border_style="cyan",
        show_header=False,
        padding=(0, 1),
    )
    overview.add_column(style="bold", justify="right")
    overview.add_column(style="cyan")

    overview.add_row("Total messages", str(s["total"]))
    overview.add_row(
        "Input / Output",
        f"{s['inputs']} input  /  {s['outputs']} output",
    )
    overview.add_row(
        "Avg input length",
        f"{s['avg_input_len']} chars",
    )
    overview.add_row(
        "Avg reply length",
        f"{s['avg_output_len']} chars",
    )
    overview.add_row("First message", _ms_to_date(s["first_ms"]))
    overview.add_row("Last message", _ms_to_date(s["last_ms"]))

    _console.print()
    _console.print(
        Panel(
            overview,
            title="[bold cyan]Overview[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
        )
    )

    # ── Platform breakdown ───────────────────────────────────────────
    if s["platforms"]:
        plat_table = Table(
            box=box.ROUNDED,
            border_style="cyan",
            show_header=True,
            padding=(0, 1),
        )
        plat_table.add_column(
            "Platform", style="bold", justify="left"
        )
        plat_table.add_column(
            "Messages", style="cyan", justify="right"
        )
        plat_table.add_column("Share", style="dim", justify="right")
        total_inputs = s["inputs"] or 1
        for platform, count in s["platforms"].items():
            pct = f"{count / total_inputs * 100:.1f}%"
            plat_table.add_row(platform, str(count), pct)

        _console.print(
            Panel(
                plat_table,
                title="[bold cyan]By Platform (inputs)[/bold cyan]",
                border_style="cyan",
                padding=(0, 1),
            )
        )

    # ── Top channels ─────────────────────────────────────────────────
    if s["top_channels"]:
        chan_table = Table(
            box=box.ROUNDED,
            border_style="cyan",
            show_header=True,
            padding=(0, 1),
        )
        chan_table.add_column(
            "Channel ID", style="bold", justify="left"
        )
        chan_table.add_column(
            "Exchanges", style="cyan", justify="right"
        )
        for entry in s["top_channels"]:
            chan_table.add_row(
                entry["channel_id"], str(entry["exchanges"])
            )

        _console.print(
            Panel(
                chan_table,
                title="[bold cyan]Top Channels[/bold cyan]",
                border_style="cyan",
                padding=(0, 1),
            )
        )

    # ── Messages per day ─────────────────────────────────────────────
    if s["per_day"]:
        day_table = Table(
            box=box.ROUNDED,
            border_style="cyan",
            show_header=True,
            padding=(0, 1),
        )
        day_table.add_column(
            "Date (UTC)", style="bold", justify="left"
        )
        day_table.add_column(
            "Input messages", style="cyan", justify="right"
        )
        # Show the most recent 14 days only to keep output compact
        recent_days = list(s["per_day"].items())[-14:]
        for date, count in recent_days:
            day_table.add_row(date, str(count))
        title_suffix = (
            " (last 14 days)" if len(s["per_day"]) > 14 else ""
        )

        _console.print(
            Panel(
                day_table,
                title=f"[bold cyan]Messages per Day{title_suffix}"
                "[/bold cyan]",
                border_style="cyan",
                padding=(0, 1),
            )
        )

    _console.print()
    return 0


def cmd_logs(args: argparse.Namespace) -> int:
    """
    Dump all logged messages from the SQLite database to a file.

    Writes every input/output row to *output* (default: message_logs.md
    or message_logs.txt depending on --format).  Format is inferred from
    the output file extension when --output is given; --format overrides.

    Returns:
        0 on success, 1 on error.
    """
    _ensure_dotenv()

    # Determine format: explicit flag > file extension > default md
    fmt = (args.format or "").lower()
    output_path: str = args.output or ""
    if not fmt:
        if output_path.endswith(".txt"):
            fmt = "txt"
        else:
            fmt = "md"
    if not output_path:
        output_path = (
            "message_logs.md" if fmt == "md" else "message_logs.txt"
        )

    try:
        from claw_swarm.db import fetch_recent, init_db

        init_db()
        rows = fetch_recent(limit=args.limit or 0)
    except Exception as exc:
        _console.print(
            f"[red]Failed to read database:[/red] {exc}",
            highlight=False,
        )
        return 1

    if not rows:
        _console.print("[yellow]No messages logged yet.[/yellow]")
        return 0

    lines: list[str] = []
    if fmt == "md":
        lines.append("# ClawSwarm Message Logs\n")
        lines.append(f"_Exported {len(rows)} record(s)_\n")
        lines.append(
            "| # | Timestamp (ms) | Direction | Platform"
            " | Channel | Thread | Sender | Message ID | Text |\n"
        )
        lines.append(
            "|---|---------------|-----------|---------|"
            "---------|--------|--------|------------|------|\n"
        )
        for i, row in enumerate(rows, 1):
            text = (
                (row["text"] or "")
                .replace("|", "\\|")
                .replace("\n", " ")
            )
            lines.append(
                f"| {i} | {row['logged_at_ms']} "
                f"| **{row['direction']}** "
                f"| {row['platform'] or ''} "
                f"| {row['channel_id'] or ''} "
                f"| {row['thread_id'] or ''} "
                f"| {row['sender_handle'] or row['sender_id'] or ''} "
                f"| {row['message_id'] or ''} "
                f"| {text} |\n"
            )
    else:  # txt
        lines.append(
            f"ClawSwarm Message Logs — {len(rows)} record(s)\n"
        )
        lines.append("=" * 72 + "\n")
        for i, row in enumerate(rows, 1):
            lines.append(f"[{i}] {row['logged_at_ms']} ms\n")
            lines.append(f"  direction : {row['direction']}\n")
            lines.append(f"  platform  : {row['platform'] or '—'}\n")
            lines.append(
                f"  channel   : {row['channel_id'] or '—'}\n"
            )
            lines.append(f"  thread    : {row['thread_id'] or '—'}\n")
            lines.append(
                f"  sender    : "
                f"{row['sender_handle'] or row['sender_id'] or '—'}\n"
            )
            lines.append(
                f"  msg_id    : {row['message_id'] or '—'}\n"
            )
            lines.append(
                f"  text      : {(row['text'] or '').strip()}\n"
            )
            lines.append("-" * 72 + "\n")

    try:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.writelines(lines)
    except OSError as exc:
        _console.print(
            f"[red]Could not write {output_path}:[/red] {exc}",
            highlight=False,
        )
        return 1

    _console.print(
        f"[green]Wrote {len(rows)} record(s) → {output_path}[/green]"
    )
    return 0


def cmd_onboarding(args: argparse.Namespace) -> int:
    """
    Interactive onboarding wizard that creates ``claw_config.yaml``.

    Use --force to overwrite an existing config file.
    """
    _ensure_dotenv()
    onboarding_interactive(force=bool(args.force))
    return 0


def main() -> int:
    """
    CLI entry point: parse subcommand and dispatch.

    With no arguments or --help, prints help. Otherwise runs the chosen
    command (run, settings) and returns its exit code.

    Returns:
        Exit code for the process (0 for success).
    """
    parser = argparse.ArgumentParser(
        prog="clawswarm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "ClawSwarm — hierarchical multi-agent swarm for\n"
            "Telegram, Discord, WhatsApp, and HTTP.\n"
            "\n"
            "Quick start:\n"
            "  clawswarm onboarding             "
            "# create claw_config.yaml\n"
            "  clawswarm run                              "
            "# gateway + agent (cloud model)\n"
            "  clawswarm run --model vllm/Qwen/Qwen-7B-Chat "
            "# local vLLM model\n"
            "  clawswarm run --model hf/microsoft/phi-2   "
            "# local HuggingFace model\n"
            "  clawswarm run --api                        "
            "# + REST API on :8080\n"
            "  clawswarm settings                         "
            "# show live config\n"
            "  clawswarm logs                             "
            "# dump message logs to file\n"
            "  clawswarm stats                            "
            "# show message statistics\n"
        ),
        epilog=(
            "Config file: claw_config.yaml  (run 'onboarding' to create)\n"
            "Env file:    .env              (secrets: API keys, tokens)\n"
            "Docs:        https://github.com/The-Swarm-Corporation/ClawSwarm"
        ),
    )
    subparsers = parser.add_subparsers(
        dest="command", metavar="COMMAND"
    )

    # ── run ──────────────────────────────────────────────────────────────
    run_p = subparsers.add_parser(
        "run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Start the gRPC gateway and swarm agent",
        description=(
            "Start the ClawSwarm stack.\n"
            "\n"
            "Always starts:\n"
            "  • Messaging Gateway  — gRPC server bridging Telegram /\n"
            "                         Discord / WhatsApp into a unified\n"
            "                         message queue\n"
            "  • Agent loop         — polls the gateway, runs the\n"
            "                         hierarchical swarm, sends replies\n"
            "\n"
            "With --api also starts:\n"
            "  • HTTP API Server    — FastAPI/uvicorn on 0.0.0.0:PORT\n"
            "                         Prints your public IP on startup\n"
            "\n"
            "Config precedence (highest → lowest):\n"
            "  CLI flags  >  env vars / .env  >  claw_config.yaml\n"
            "\n"
            "claw_config.yaml keys (run 'onboarding' to set):\n"
            "  gateway.host     gRPC bind host   (default: [::])\n"
            "  gateway.port     gRPC port        (default: 50051)\n"
            "  gateway.tls      enable TLS       (default: false)\n"
            "  api.port         HTTP API port    (default: 8080)\n"
            "  api.key          API auth key     (default: open)\n"
            "  worker.model_name                 (default: gpt-4o-mini)\n"
            "\n"
            "Env vars (secrets; set in .env or shell):\n"
            "  OPENAI_API_KEY       required for the swarm director\n"
            "  ANTHROPIC_API_KEY    optional Claude reasoning layer\n"
            "  TELEGRAM_BOT_TOKEN   Telegram platform adapter\n"
            "  DISCORD_BOT_TOKEN    Discord platform adapter\n"
            "  DISCORD_CHANNEL_IDS  comma-separated channel IDs\n"
            "  WHATSAPP_ACCESS_TOKEN / WHATSAPP_PHONE_NUMBER_ID\n"
            "\n"
            "HTTP API endpoints (when --api is used):\n"
            "  POST /v1/agent/completions        submit task (async)\n"
            "  POST /v1/agent/completions/sync   submit task and wait\n"
            "  GET  /v1/agent/jobs/{id}          poll job status\n"
            "  GET  /v1/agent/jobs               list recent jobs\n"
            "  GET  /docs                        Swagger UI\n"
        ),
    )
    run_p.add_argument(
        "--api",
        action="store_true",
        default=False,
        help=(
            "Start the public HTTP API server alongside the agent "
            "(FastAPI/uvicorn). Public IP is printed on startup."
        ),
    )
    run_p.add_argument(
        "--port",
        type=int,
        default=8080,
        metavar="PORT",
        help=(
            "HTTP API listen port (default: 8080). "
            "Overrides api.port in claw_config.yaml and API_PORT env var."
        ),
    )
    run_p.add_argument(
        "--gw-host",
        metavar="HOST",
        default=None,
        help=(
            "Gateway gRPC bind host (e.g. 0.0.0.0). "
            "Overrides gateway.host in claw_config.yaml."
        ),
    )
    run_p.add_argument(
        "--gw-port",
        type=int,
        metavar="PORT",
        default=None,
        help=(
            "Gateway gRPC port (default: 50051). "
            "Overrides gateway.port in claw_config.yaml."
        ),
    )
    run_p.add_argument(
        "--gw-tls",
        action="store_true",
        default=False,
        help=(
            "Enable TLS on the gRPC gateway. "
            "Overrides gateway.tls in claw_config.yaml."
        ),
    )
    run_p.add_argument(
        "--api-key",
        metavar="KEY",
        default=None,
        help=(
            "Require X-API-Key: <KEY> on all /v1/* requests. "
            "Overrides api.key in claw_config.yaml and API_KEY env var."
        ),
    )
    run_p.add_argument(
        "--model",
        metavar="MODEL",
        default=None,
        help=(
            "Director (main) agent model. Accepts cloud model names "
            "(e.g. gpt-4o-mini) or local prefixes:\n"
            "  vllm/<model>          local vLLM engine (requires GPU + pip install vllm)\n"
            "  vllm-server/<model>   vLLM OpenAI-compatible HTTP server\n"
            "  hf/<model>            HuggingFace Transformers pipeline\n"
            "Examples:\n"
            "  --model vllm/mistralai/Mistral-7B-Instruct-v0.1\n"
            "  --model vllm-server/meta-llama/Llama-2-7b-chat-hf\n"
            "  --model hf/microsoft/phi-2\n"
            "Overrides AGENT_MODEL env var."
        ),
    )
    run_p.add_argument(
        "--worker-model",
        metavar="MODEL",
        default=None,
        help=(
            "Worker agents model. Same prefix scheme as --model.\n"
            "When omitted, workers use --model / WORKER_MODEL_NAME / AGENT_MODEL.\n"
            "Examples:\n"
            "  --worker-model hf/microsoft/phi-2\n"
            "  --worker-model vllm/Qwen/Qwen-7B-Chat\n"
            "Overrides WORKER_MODEL_NAME env var."
        ),
    )
    run_p.set_defaults(func=cmd_run)

    # ── settings ─────────────────────────────────────────────────────────
    set_p = subparsers.add_parser(
        "settings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Show live configuration (config file + env)",
        description=(
            "Display all active ClawSwarm configuration values.\n"
            "\n"
            "Merges claw_config.yaml → .env → environment variables\n"
            "and prints them grouped by section. Secret values\n"
            "(tokens, API keys) are masked for safety.\n"
            "\n"
            "Sections shown:\n"
            "  Gateway   — gRPC host, port, TLS\n"
            "  API       — HTTP port, auth key\n"
            "  Models    — director and worker model names\n"
            "  Platforms — Telegram, Discord, WhatsApp credentials\n"
        ),
    )
    set_p.set_defaults(func=cmd_settings)

    # ── onboarding ───────────────────────────────────────────────────────
    on_p = subparsers.add_parser(
        "onboarding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Create or update claw_config.yaml interactively",
        description=(
            "Run an interactive setup wizard to create\n"
            "claw_config.yaml in the project root.\n"
            "\n"
            "Configures five sections:\n"
            "  Agent    — name and description of the director agent\n"
            "  Worker   — model name for worker agents (e.g. gpt-4o-mini)\n"
            "  Gateway  — gRPC bind host, port, TLS toggle\n"
            "  HTTP API — listen port, optional auth key\n"
            "  Runtime  — verbose logging toggle\n"
            "\n"
            "All values have sensible defaults — just press Enter\n"
            "to accept them. The file is written atomically once\n"
            "all prompts are complete.\n"
            "\n"
            "Use --force to overwrite an existing claw_config.yaml.\n"
        ),
    )
    on_p.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Overwrite claw_config.yaml if it already exists",
    )
    on_p.set_defaults(func=cmd_onboarding)

    # ── logs ─────────────────────────────────────────────────────────────
    logs_p = subparsers.add_parser(
        "logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Dump all SQL message logs to a .md or .txt file",
        description=(
            "Export every logged input/output message from the\n"
            "SQLite database to a Markdown or plain-text file.\n"
            "\n"
            "Examples:\n"
            "  clawswarm logs                      "
            "# → message_logs.md\n"
            "  clawswarm logs --format txt         "
            "# → message_logs.txt\n"
            "  clawswarm logs --output chat.md     "
            "# custom file name\n"
            "  clawswarm logs --limit 500          "
            "# most recent 500 rows\n"
            "\n"
            "Format is inferred from --output extension when given;\n"
            "--format always takes precedence.\n"
            "\n"
            "Set MESSAGE_LOG_DB env var to the same path used when\n"
            "the agent was running (default: in-memory, so start the\n"
            "agent with MESSAGE_LOG_DB=messages.db to persist logs).\n"
        ),
    )
    logs_p.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        default=None,
        help=(
            "Output file path. "
            "Defaults to message_logs.md or message_logs.txt."
        ),
    )
    logs_p.add_argument(
        "--format",
        "-f",
        choices=["md", "txt"],
        default=None,
        help="Output format: md (default) or txt.",
    )
    logs_p.add_argument(
        "--limit",
        "-n",
        type=int,
        default=0,
        metavar="N",
        help="Max rows to export (0 = all, default).",
    )
    logs_p.set_defaults(func=cmd_logs)

    # ── stats ─────────────────────────────────────────────────────────────
    stats_p = subparsers.add_parser(
        "stats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Show message statistics from the SQL log",
        description=(
            "Print aggregate statistics from the SQLite message log:\n"
            "total messages, platform breakdown, top channels,\n"
            "average lengths, and daily message counts.\n"
            "\n"
            "Examples:\n"
            "  clawswarm stats\n"
            "  clawswarm stats --json\n"
            "\n"
            "Set MESSAGE_LOG_DB to the same path used when the agent\n"
            "was running (default: in-memory, lost on process exit).\n"
        ),
    )
    stats_p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output raw JSON instead of Rich tables.",
    )
    stats_p.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
