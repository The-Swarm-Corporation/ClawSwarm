"""
Gateway entrypoint for: python -m claw_swarm.gateway
"""

from __future__ import annotations

import asyncio
import os
import time

import grpc
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich import box

from claw_swarm.gateway import (
    DiscordAdapter,
    TelegramAdapter,
    WhatsAppAdapter,
    run_server,
)
from claw_swarm.gateway.adapters.base import MessageAdapter

console = Console()

_BANNER = r"""
   ___  _                _____                    
  / __\| | __ _ __  __  / ___ \__      ____ _ _ __ ____ 
 / /   | |/ _` |\ \/ / /__\// \ \ /\ / / _` | '__/ _  |
/ /___ | | (_| | >  < / \/  \  \ V  V / (_| | | | | | |
\____/ |_|\__,_|/_/\_\\_____/   \_/\_/ \__,_|_|  |_| |_|
"""


def _print_banner(version: str) -> None:
    banner_text = Text(_BANNER, style="bold cyan", justify="center")
    subtitle = Text(
        f"Messaging Gateway  ·  gRPC Server  ·  v{version}",
        style="dim white",
        justify="center",
    )
    combined = Text.assemble(banner_text, "\n", subtitle)
    console.print(
        Panel(
            combined,
            border_style="cyan",
            padding=(0, 2),
        )
    )


def _print_init_step(
    icon: str, label: str, value: str, style: str = "green"
) -> None:
    console.print(
        f"  {icon}  [dim]{label}[/dim]  [bold {style}]{value}[/bold {style}]"
    )


def _print_ready_table(
    host: str,
    port: int,
    use_tls: bool,
    adapter_names: list[str],
) -> None:
    table = Table(
        box=box.ROUNDED,
        border_style="cyan",
        show_header=False,
        padding=(0, 2),
        expand=False,
    )
    table.add_column("key", style="dim white", no_wrap=True)
    table.add_column("value", style="bold white", no_wrap=True)

    table.add_row(
        "Listening on",
        f"[bold cyan]{host}:{port}[/bold cyan]",
    )
    table.add_row(
        "Transport",
        (
            "[bold green]TLS[/bold green]"
            if use_tls
            else "[yellow]Insecure (no TLS)[/yellow]"
        ),
    )
    table.add_row(
        "Adapters",
        "  ".join(
            f"[bold magenta]{n}[/bold magenta]" for n in adapter_names
        )
        or "[dim]none[/dim]",
    )
    console.print(table)


def _detect_models() -> tuple[str, list[str], list[str]]:
    """
    Inspect environment for model-related configuration.

    Returns:
        agent_model: The configured AGENT_MODEL (or default).
        available: Human labels for providers with non-empty keys.
        missing: Human labels for providers without keys set.
    """
    agent_model = os.environ.get("AGENT_MODEL", "gpt-4o-mini")
    providers: list[tuple[str, str]] = [
        ("OpenAI", "OPENAI_API_KEY"),
        ("Anthropic", "ANTHROPIC_API_KEY"),
    ]
    available: list[str] = []
    missing: list[str] = []
    for label, env_key in providers:
        if os.environ.get(env_key):
            available.append(label)
        else:
            missing.append(label)
    return agent_model, available, missing


def main() -> None:
    version = os.environ.get("GATEWAY_VERSION", "0.1.0")

    _print_banner(version)
    console.print()
    console.print(
        Rule("[dim cyan]Initializing[/dim cyan]", style="cyan")
    )
    console.print()

    # --- resolve config ---
    with console.status(
        "[cyan]Loading configuration…[/cyan]", spinner="dots"
    ):
        time.sleep(0.3)
        host = os.environ.get("GATEWAY_HOST", "[::]")
        port = int(os.environ.get("GATEWAY_PORT", "50051"))
        use_tls = os.environ.get(
            "GATEWAY_TLS", ""
        ).strip().lower() in ("1", "true", "yes")

    _print_init_step("⚙", "Host", host)
    _print_init_step("⚙", "Port", str(port))
    _print_init_step(
        "⚙",
        "TLS",
        "enabled" if use_tls else "disabled",
        style="green" if use_tls else "yellow",
    )
    agent_model, available_models, missing_models = _detect_models()
    _print_init_step("⚙", "Agent model", agent_model)
    if available_models:
        _print_init_step(
            "⚙",
            "Model providers",
            ", ".join(available_models),
        )
    else:
        console.print(
            "  [dim]–  Model providers  "
            "(no model API keys found; set OPENAI_API_KEY or ANTHROPIC_API_KEY)[/dim]"
        )
    if missing_models and available_models:
        console.print(
            f"  [dim]–  Missing model providers  {', '.join(missing_models)}[/dim]"
        )
    console.print()

    # --- load TLS credentials ---
    server_credentials = None
    if use_tls:
        with console.status(
            "[cyan]Loading TLS credentials…[/cyan]", spinner="dots"
        ):
            time.sleep(0.2)
            cert_file = os.environ.get("GATEWAY_TLS_CERT_FILE")
            key_file = os.environ.get("GATEWAY_TLS_KEY_FILE")
            if cert_file and key_file:
                with open(cert_file, "rb") as f:
                    cert = f.read()
                with open(key_file, "rb") as f:
                    key = f.read()
                server_credentials = grpc.ssl_server_credentials(
                    ((key, cert),)
                )
        _print_init_step("🔒", "Credentials", "loaded")
        console.print()

    # --- build adapters (only those with credentials present) ---
    with console.status(
        "[cyan]Checking platform adapters…[/cyan]", spinner="dots"
    ):
        time.sleep(0.3)
        candidates: list[tuple[MessageAdapter, bool]] = [
            (
                TelegramAdapter(),
                bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
            ),
            (
                DiscordAdapter(),
                bool(os.environ.get("DISCORD_BOT_TOKEN")),
            ),
            (
                WhatsAppAdapter(),
                bool(
                    os.environ.get("WHATSAPP_ACCESS_TOKEN")
                    and os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
                ),
            ),
        ]
        adapters = [a for a, ok in candidates if ok]

    for adapter, ok in candidates:
        if ok:
            _print_init_step(
                "✔",
                "Adapter",
                adapter.platform_name,
                style="magenta",
            )
        else:
            console.print(
                f"  [dim]–  Adapter  {adapter.platform_name}"
                "  (no credentials, skipped)[/dim]"
            )
    console.print()

    # --- start gRPC server ---
    async def serve() -> None:
        with console.status(
            "[cyan]Starting gRPC server…[/cyan]",
            spinner="bouncingBar",
        ):
            srv = await run_server(
                adapters,
                host=host,
                port=port,
                use_tls=use_tls,
                server_credentials=server_credentials,
            )

        console.print(
            Rule(
                "[bold green]Server Ready[/bold green]", style="green"
            )
        )
        console.print()
        _print_ready_table(
            host=host,
            port=port,
            use_tls=use_tls,
            adapter_names=[a.platform_name for a in adapters],
        )
        console.print()
        console.print(
            "  [dim]Press[/dim] [bold]Ctrl+C[/bold] [dim]to stop.[/dim]"
        )
        console.print()

        await srv.wait_for_termination()

    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        console.print()
        console.print(
            Rule("[dim]Shutting down[/dim]", style="dim cyan")
        )
        console.print(
            "  [dim cyan]ClawSwarm gateway stopped.[/dim cyan]"
        )
        console.print()


if __name__ == "__main__":
    main()
