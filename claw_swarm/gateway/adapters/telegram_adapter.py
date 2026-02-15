"""
Telegram adapter: fetches messages via Bot API and normalizes to UnifiedMessage.
Configure with TELEGRAM_BOT_TOKEN env var; without it, fetch_messages returns [].
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

from claw_swarm.gateway.adapters.base import MessageAdapter
from claw_swarm.gateway.schema import Platform, UnifiedMessage

if TYPE_CHECKING:
    pass


class TelegramAdapter(MessageAdapter):
    """Poll Telegram for updates (getUpdates) and normalize to UnifiedMessage."""

    def __init__(self, bot_token: str | None = None) -> None:
        self._token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self._offset: int | None = None

    @property
    def platform_name(self) -> str:
        return "telegram"

    async def fetch_messages(
        self,
        since_timestamp_utc_ms: int = 0,
        max_messages: int = 100,
    ) -> list[UnifiedMessage]:
        if not self._token:
            return []
        try:
            import aiohttp
        except ImportError:
            return []
        out: list[UnifiedMessage] = []
        url = f"https://api.telegram.org/bot{self._token}/getUpdates"
        params: dict = {"limit": min(max_messages, 100), "timeout": 10}
        if self._offset is not None:
            params["offset"] = self._offset
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return out
                data = await resp.json()
        for u in data.get("result", []):
            self._offset = u["update_id"] + 1
            msg = u.get("message") or u.get("channel_post")
            if not msg:
                continue
            ts = msg.get("date", 0) * 1000
            if since_timestamp_utc_ms and ts <= since_timestamp_utc_ms:
                continue
            from_ = msg.get("from", {})
            chat = msg.get("chat", {})
            text = msg.get("text") or ""
            attachments: list[str] = []
            for key in ("photo", "document", "audio", "voice", "video"):
                if key in msg:
                    # Telegram returns file_id; optional: resolve to URL via getFile
                    attachments.append(msg[key][-1].get("file_id", "") if isinstance(msg[key], list) else str(msg[key]))
            out.append(
                UnifiedMessage(
                    id=str(msg["message_id"]),
                    platform=Platform.TELEGRAM,
                    channel_id=str(chat.get("id", "")),
                    thread_id=str(chat.get("message_thread_id", "")),
                    sender_id=str(from_.get("id", "")),
                    sender_handle=from_.get("username", "") or from_.get("first_name", ""),
                    text=text,
                    attachment_urls=attachments,
                    timestamp_utc_ms=ts,
                )
            )
            if len(out) >= max_messages:
                break
        return out
