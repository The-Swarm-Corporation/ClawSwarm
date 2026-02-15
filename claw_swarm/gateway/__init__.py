"""
Messaging gateway: unified gRPC API for Telegram, Discord, and WhatsApp.
Secure protocol (gRPC with optional TLS); single schema for all platforms.
"""

from claw_swarm.gateway.adapters import (
    DiscordAdapter,
    MessageAdapter,
    TelegramAdapter,
    WhatsAppAdapter,
)
from claw_swarm.gateway.schema import Platform, UnifiedMessage
from claw_swarm.gateway.server import MessagingGatewayServicer, run_server

__all__ = [
    "DiscordAdapter",
    "MessageAdapter",
    "MessagingGatewayServicer",
    "Platform",
    "TelegramAdapter",
    "UnifiedMessage",
    "WhatsAppAdapter",
    "run_server",
]
