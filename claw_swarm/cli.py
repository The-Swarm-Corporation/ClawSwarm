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
            "  clawswarm run                    "
            "# gateway + agent\n"
            "  clawswarm run --api              "
            "# + REST API on :8080\n"
            "  clawswarm run --api --port 9000  "
            "# custom API port\n"
            "  clawswarm settings               "
            "# show live config\n"
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

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
