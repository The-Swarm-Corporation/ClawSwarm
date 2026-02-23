"""
Simple CLI for ClawSwarm: run (gateway + agent) and settings.

Usage:
  clawswarm --help
  clawswarm run                    # gateway + agent only
  clawswarm run --api              # gateway + agent + public HTTP API
  clawswarm run --api --port 9000  # custom HTTP API port
  clawswarm settings
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

from dotenv import load_dotenv


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

    gw_host = os.environ.get("GATEWAY_HOST", "[::]")
    gw_port = int(os.environ.get("GATEWAY_PORT", "50051"))
    api_port = int(os.environ.get("API_PORT", str(args.port)))

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
    keys = [
        "GATEWAY_HOST",
        "GATEWAY_PORT",
        "GATEWAY_TLS",
        "API_PORT",
        "API_KEY",
        "AGENT_MODEL",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "DISCORD_BOT_TOKEN",
        "DISCORD_CHANNEL_IDS",
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_PHONE_NUMBER_ID",
    ]
    print("ClawSwarm settings (from .env / environment):")
    print("-" * 50)
    for key in keys:
        val = os.environ.get(key, "")
        if val and key.endswith(
            ("_TOKEN", "_KEY", "ACCESS_TOKEN", "API_KEY")
        ):
            val = val[:8] + "..." if len(val) > 8 else "***"
        print(f"  {key}={val or '(not set)'}")
    print("-" * 50)
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
            "ClawSwarm — hierarchical multi-agent swarm for Telegram, "
            "Discord, WhatsApp, and HTTP.\n"
            "\n"
            "Quick start:\n"
            "  clawswarm run               # messaging platforms only\n"
            "  clawswarm run --api         # + public REST API on :8080\n"
            "  clawswarm run --api --port 9000\n"
            "  clawswarm settings          # show current config\n"
        ),
        epilog=(
            "Docs: https://github.com/The-Swarm-Corporation/ClawSwarm"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # ── run ──────────────────────────────────────────────────────────────
    run_p = subparsers.add_parser(
        "run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Start the gRPC gateway and swarm agent",
        description=(
            "Start the ClawSwarm stack.\n"
            "\n"
            "Always starts:\n"
            "  • Messaging Gateway  — gRPC server that bridges Telegram /\n"
            "                         Discord / WhatsApp into a unified queue\n"
            "  • Agent loop         — polls the gateway, runs the hierarchical\n"
            "                         swarm, and sends replies back\n"
            "\n"
            "With --api also starts:\n"
            "  • HTTP API Server    — FastAPI/uvicorn on 0.0.0.0:PORT\n"
            "                         Prints your public IP on startup so\n"
            "                         you know the exact URL to share.\n"
            "\n"
            "Key env vars (set in .env or environment):\n"
            "  GATEWAY_HOST    gRPC bind host        (default: [::])\n"
            "  GATEWAY_PORT    gRPC port             (default: 50051)\n"
            "  API_PORT        HTTP API port         (default: 8080)\n"
            "  API_KEY         Lock the API behind   X-API-Key: <value>\n"
            "  OPENAI_API_KEY  Required for the swarm director (gpt-4.1)\n"
            "\n"
            "HTTP API endpoints (when --api is used):\n"
            "  POST /v1/agent/completions        submit task (async)\n"
            "  POST /v1/agent/completions/sync   submit task and wait\n"
            "  GET  /v1/agent/jobs/{id}          poll job status / result\n"
            "  GET  /v1/agent/jobs               list recent jobs\n"
            "  GET  /docs                        Swagger UI\n"
        ),
    )
    run_p.add_argument(
        "--api",
        action="store_true",
        default=False,
        help=(
            "Start the public HTTP API server alongside the agent. "
            "Your public IP is printed on startup."
        ),
    )
    run_p.add_argument(
        "--port",
        type=int,
        default=8080,
        metavar="PORT",
        help="HTTP API port — default 8080 (overrides API_PORT env var)",
    )
    run_p.set_defaults(func=cmd_run)

    # ── settings ─────────────────────────────────────────────────────────
    set_p = subparsers.add_parser(
        "settings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Print current configuration (env / .env)",
        description=(
            "Print all ClawSwarm configuration keys loaded from the "
            "environment or a .env file.\n"
            "Secret values (tokens, API keys) are truncated for safety."
        ),
    )
    set_p.set_defaults(func=cmd_settings)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
