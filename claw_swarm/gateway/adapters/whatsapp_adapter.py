"""
WhatsApp adapter: fetches messages via Cloud API / Business API and normalizes to UnifiedMessage.
Configure with WhatsApp credentials (e.g. CLOUDS_API_TOKEN, PHONE_NUMBER_ID); without them, returns [].
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from claw_swarm.gateway.adapters.base import MessageAdapter
from claw_swarm.gateway.schema import Platform, UnifiedMessage

if TYPE_CHECKING:
    pass


class WhatsAppAdapter(MessageAdapter):
    """Poll WhatsApp Cloud API for new messages (webhook alternative: use your own HTTP endpoint)."""

    def __init__(
        self,
        access_token: str | None = None,
        phone_number_id: str | None = None,
    ) -> None:
        self._token = access_token or os.environ.get("WHATSAPP_ACCESS_TOKEN")
        self._phone_number_id = phone_number_id or os.environ.get(
            "WHATSAPP_PHONE_NUMBER_ID"
        )

    @property
    def platform_name(self) -> str:
        return "whatsapp"

    async def fetch_messages(
        self,
        since_timestamp_utc_ms: int = 0,
        max_messages: int = 100,
    ) -> list[UnifiedMessage]:
        # WhatsApp Cloud API does not support polling; messages are delivered via webhooks.
        # This adapter either (1) returns [] when used in poll mode, or (2) you run a
        # small webhook server that pushes into a queue and this adapter reads from it.
        # Here we return [] so the gateway works; implement webhook + queue for production.
        if not self._token or not self._phone_number_id:
            return []
        # Optional: read from a shared queue populated by your webhook handler
        queue_key = os.environ.get("WHATSAPP_QUEUE_PATH")
        if queue_key:
            return await _drain_queue(
                queue_key, since_timestamp_utc_ms, max_messages, Platform.WHATSAPP
            )
        return []


async def _drain_queue(
    queue_path: str,
    since_timestamp_utc_ms: int,
    max_messages: int,
    platform: Platform,
) -> list[UnifiedMessage]:
    """Drain messages from a file-based or Redis queue (stub). Extend for your queue backend."""
    # Stub: no actual queue implementation; integrate with your webhook store (Redis, DB, file).
    return []
