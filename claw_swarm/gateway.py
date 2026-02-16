"""
Gateway entrypoint: run the Messaging Gateway gRPC server.

Checks for messages from Telegram, Discord, and WhatsApp over a unified schema
and secure gRPC protocol (TLS optional).

How to start:
  cp .env.example .env   # edit with your tokens
  python -m claw_swarm.gateway

Or set env vars and run:
  export TELEGRAM_BOT_TOKEN=...
  python -m claw_swarm.gateway

Env vars (see .env.example for all):
  GATEWAY_HOST, GATEWAY_PORT  - bind address (default [::]:50051)
  GATEWAY_TLS=1               - enable TLS (set GATEWAY_TLS_CERT_FILE, GATEWAY_TLS_KEY_FILE)
  TELEGRAM_BOT_TOKEN         - optional
  DISCORD_BOT_TOKEN, DISCORD_CHANNEL_IDS - optional
  WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID - optional
"""

from __future__ import annotations

import asyncio
import os


def main() -> None:
    from claw_swarm.gateway import (
        DiscordAdapter,
        TelegramAdapter,
        WhatsAppAdapter,
        run_server,
    )

    adapters = [
        TelegramAdapter(),
        DiscordAdapter(),
        WhatsAppAdapter(),
    ]
    host = os.environ.get("GATEWAY_HOST", "[::]")
    port = int(os.environ.get("GATEWAY_PORT", "50051"))
    use_tls = os.environ.get("GATEWAY_TLS", "").strip().lower() in ("1", "true", "yes")
    server_credentials = None
    if use_tls:
        cert_file = os.environ.get("GATEWAY_TLS_CERT_FILE")
        key_file = os.environ.get("GATEWAY_TLS_KEY_FILE")
        if cert_file and key_file:
            with open(cert_file, "rb") as f:
                cert = f.read()
            with open(key_file, "rb") as f:
                key = f.read()
            import grpc

            server_credentials = grpc.ssl_server_credentials(
                ((key, cert),)
            )  # (private_key, cert_chain)

    async def serve() -> None:
        srv = await run_server(
            adapters,
            host=host,
            port=port,
            use_tls=use_tls,
            server_credentials=server_credentials,
        )
        print(
            f"Messaging Gateway gRPC server listening on {host}:{port} (TLS={use_tls})"
        )
        await srv.wait_for_termination()

    asyncio.run(serve())


if __name__ == "__main__":
    main()
