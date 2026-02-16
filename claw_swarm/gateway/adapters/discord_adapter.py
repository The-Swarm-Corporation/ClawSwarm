"""
Discord adapter: fetches messages via Bot API and normalizes to UnifiedMessage.
Configure with DISCORD_BOT_TOKEN env var; without it, fetch_messages returns [].
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from claw_swarm.gateway.adapters.base import MessageAdapter
from claw_swarm.gateway.schema import Platform, UnifiedMessage

if TYPE_CHECKING:
    pass


class DiscordAdapter(MessageAdapter):
    """Poll Discord channels for new messages (requires channel IDs or gateway)."""

    def __init__(
        self,
        bot_token: str | None = None,
        channel_ids: list[str] | None = None,
    ) -> None:
        self._token = bot_token or os.environ.get("DISCORD_BOT_TOKEN")
        self._channel_ids = channel_ids or _channel_ids_from_env()

    @property
    def platform_name(self) -> str:
        return "discord"

    async def fetch_messages(
        self,
        since_timestamp_utc_ms: int = 0,
        max_messages: int = 100,
    ) -> list[UnifiedMessage]:
        if not self._token or not self._channel_ids:
            return []
        try:
            import aiohttp
        except ImportError:
            return []
        out: list[UnifiedMessage] = []
        per_channel = max(1, max_messages // len(self._channel_ids))
        base = "https://discord.com/api/v10"
        headers = {
            "Authorization": f"Bot {self._token}",
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession() as session:
            for channel_id in self._channel_ids[:20]:
                url = f"{base}/channels/{channel_id}/messages?limit={per_channel}"
                if since_timestamp_utc_ms:
                    # Discord uses snowflake; approximate filter by time
                    url += f"&after={_ms_to_discord_snowflake(since_timestamp_utc_ms)}"
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                for msg in data:
                    if msg.get("type") != 0:
                        continue
                    ts = _discord_snowflake_to_ms(msg["id"])
                    if since_timestamp_utc_ms and ts <= since_timestamp_utc_ms:
                        continue
                    author = msg.get("author", {})
                    attachments = [
                        a.get("url", "")
                        for a in msg.get("attachments", [])
                        if a.get("url")
                    ]
                    out.append(
                        UnifiedMessage(
                            id=msg["id"],
                            platform=Platform.DISCORD,
                            channel_id=str(msg.get("channel_id", "")),
                            thread_id=(
                                str(msg.get("thread", {}).get("id", ""))
                                if isinstance(msg.get("thread"), dict)
                                else ""
                            ),
                            sender_id=author.get("id", ""),
                            sender_handle=author.get("username", "")
                            or author.get("global_name", ""),
                            text=msg.get("content", ""),
                            attachment_urls=attachments,
                            timestamp_utc_ms=ts,
                        )
                    )
                if len(out) >= max_messages:
                    break
        return sorted(out, key=lambda m: m.timestamp_utc_ms)[:max_messages]


def _channel_ids_from_env() -> list[str]:
    raw = os.environ.get("DISCORD_CHANNEL_IDS", "")
    return [x.strip() for x in raw.split(",") if x.strip()]


def _discord_snowflake_to_ms(snowflake: str) -> int:
    try:
        return (int(snowflake) >> 22) + 1420070400000
    except (ValueError, TypeError):
        return 0


def _ms_to_discord_snowflake(ms: int) -> str:
    return str(((ms - 1420070400000) << 22))
