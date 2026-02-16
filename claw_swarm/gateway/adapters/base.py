"""
Base adapter interface for messaging platforms.
Each platform (Telegram, Discord, WhatsApp) implements this and returns UnifiedMessage list.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from claw_swarm.gateway.schema import UnifiedMessage


class MessageAdapter(ABC):
    """Abstract adapter: fetch new messages and normalize to UnifiedMessage."""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """e.g. 'telegram', 'discord', 'whatsapp'."""
        ...

    @abstractmethod
    async def fetch_messages(
        self,
        since_timestamp_utc_ms: int = 0,
        max_messages: int = 100,
    ) -> list[UnifiedMessage]:
        """
        Poll for new messages. Returns list of unified messages (may be empty).
        """
        ...

    async def stream_messages(self):
        """
        Optional: yield messages as they arrive (long-lived).
        Default implementation just repeatedly calls fetch_messages with backoff.
        Override for true push/websocket where available.
        """
        since_ms = 0
        while True:
            batch = await self.fetch_messages(
                since_timestamp_utc_ms=since_ms,
                max_messages=50,
            )
            for msg in batch:
                yield msg
                if msg.timestamp_utc_ms > since_ms:
                    since_ms = msg.timestamp_utc_ms
            if not batch:
                import asyncio

                await asyncio.sleep(5)
