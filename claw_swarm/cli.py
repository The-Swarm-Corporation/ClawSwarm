"""
Simple CLI for ClawSwarm: run (gateway + agent) and settings.

Usage:
  clawswarm --help
  clawswarm run
  clawswarm settings
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
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


def cmd_run(_args: argparse.Namespace) -> int:
    """
    Run the gateway and agent together.

    Starts the Messaging Gateway gRPC server in a subprocess, then runs the
    ClawSwarm agent in this process. The agent connects to the local gateway.
    On exit (e.g. Ctrl+C), the gateway subprocess is terminated.

    Returns:
        Exit code: 0 on normal agent exit, non-zero if the gateway fails
        to start or the agent errors.
    """
    _ensure_dotenv()
    if _args.config:
        os.environ["CLAWSWARM_CONFIG"] = _args.config
    host = os.environ.get("GATEWAY_HOST", "[::]")
    port = int(os.environ.get("GATEWAY_PORT", "50051"))
    env = os.environ.copy()
    env["GATEWAY_HOST"] = host
    env["GATEWAY_PORT"] = str(port)
    # Start gateway as subprocess
    proc = subprocess.Popen(
        [sys.executable, "-m", "claw_swarm.gateway"],
        env=env,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    # Give gateway time to bind
    time.sleep(1.5)
    if proc.poll() is not None:
        print("clawswarm: gateway exited early.", file=sys.stderr)
        return proc.returncode or 1

    def kill_gateway() -> None:
        """Terminate the gateway subprocess; kill it if it does not exit in 5s."""
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    # Agent in this process must connect to local gateway
    os.environ["GATEWAY_HOST"] = "127.0.0.1"
    os.environ["GATEWAY_PORT"] = str(port)
    try:
        # Run agent in this process (blocks until Ctrl+C)
        from claw_swarm.agent_runner import main as agent_main

        return agent_main()
    finally:
        kill_gateway()


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


def _prompt_text(prompt: str, default: str = "") -> str:
    raw = input(prompt).strip()
    return raw if raw else default


def _upsert_env_file(path: Path, values: dict[str, str]) -> None:
    existing_lines: list[str] = []
    if path.is_file():
        existing_lines = path.read_text().splitlines()

    updated: dict[str, str] = {}
    for line in existing_lines:
        if "=" not in line or line.strip().startswith("#"):
            continue
        key, val = line.split("=", 1)
        updated[key.strip()] = val.strip()

    updated.update(values)

    out_lines = [f"{key}={value}" for key, value in sorted(updated.items())]
    path.write_text("\n".join(out_lines) + "\n")


def cmd_init(_args: argparse.Namespace) -> int:
    """Interactive onboarding flow for first-time setup."""
    _ensure_dotenv()
    print("Welcome to ClawSwarm!")
    print("Let's get you set up.\n")

    name = _prompt_text("Agent Name [ClawSwarm]: ", "ClawSwarm")
    description = _prompt_text("Agent Description: ", "")

    models = [
        "gpt-4o",
        "gpt-4o-mini",
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
        "Other",
    ]
    print("\nSelect Model:")
    for i, model in enumerate(models, start=1):
        suffix = " (default)" if model == "gpt-4o-mini" else ""
        print(f"  {i}. {model}{suffix}")
    choice = _prompt_text("Choice [2]: ", "2")
    model = "gpt-4o-mini"
    if choice in {"1", "2", "3", "4"}:
        model = models[int(choice) - 1]
    elif choice == "5":
        model = _prompt_text("Custom model id: ", "gpt-4o-mini")

    print("\nChecking environment variables...")
    required = ["OPENAI_API_KEY"]
    optional = [
        "ANTHROPIC_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "DISCORD_BOT_TOKEN",
        "WHATSAPP_ACCESS_TOKEN",
    ]
    gateway = ["GATEWAY_HOST", "GATEWAY_PORT"]

    for key in required:
        status = "Set" if os.environ.get(key) else "Not set"
        mark = "✓" if status == "Set" else "✗"
        print(f"{mark} {key}: {status}")
    for key in optional:
        status = "Set" if os.environ.get(key) else "Not set (optional)"
        mark = "✓" if "Set" in status and "optional" not in status else "✗"
        print(f"{mark} {key}: {status}")
    for key in gateway:
        val = os.environ.get(
            key, "[::]" if key == "GATEWAY_HOST" else "50051"
        )
        print(f"✓ {key}: Set to {val}")

    env_values = {
        "AGENT_NAME": name,
        "AGENT_DESCRIPTION": description,
        "AGENT_MODEL": model,
        "GATEWAY_HOST": os.environ.get("GATEWAY_HOST", "[::]"),
        "GATEWAY_PORT": os.environ.get("GATEWAY_PORT", "50051"),
    }

    env_path = Path(os.getcwd()) / ".env"
    _upsert_env_file(env_path, env_values)
    print("\nConfiguration saved to .env")
    print("Setup complete! Run 'clawswarm run' to start your agent.")
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
        description="ClawSwarm CLI: run the messaging gateway and agent.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")

    run_p = subparsers.add_parser(
        "run", help="Run gateway and agent (gateway in subprocess)"
    )
    run_p.add_argument(
        "--config",
        default=None,
        help="Path to optional ClawSwarm TOML config file",
    )
    run_p.set_defaults(func=cmd_run)

    set_p = subparsers.add_parser(
        "settings", help="Show current settings (env / .env)"
    )
    set_p.set_defaults(func=cmd_settings)

    init_p = subparsers.add_parser(
        "init",
        aliases=["onboard"],
        help="Run interactive first-time setup",
    )
    init_p.set_defaults(func=cmd_init)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
