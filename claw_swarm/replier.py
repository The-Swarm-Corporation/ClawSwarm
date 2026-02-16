"""
Send replies back to Telegram, Discord, or WhatsApp using platform APIs.
Uses the same env vars as the gateway adapters (TELEGRAM_BOT_TOKEN, etc.).
The agent calls this after processing a message so the user gets a response.
"""

from __future__ import annotations

import os
from typing import Optional

from claw_swarm.gateway.schema import Platform


async def send_message_async(
    platform: Platform,
    channel_id: str,
    thread_id: str,
    text: str,
) -> tuple[bool, str]:
    """
    Send a text message to the given channel on the given platform.

    Returns:
        (success, error_message). error_message is empty when success is True.
    """
    if platform == Platform.TELEGRAM:
        return await _send_telegram(channel_id, thread_id, text)
    if platform == Platform.DISCORD:
        return await _send_discord(channel_id, thread_id, text)
    if platform == Platform.WHATSAPP:
        return await _send_whatsapp(channel_id, thread_id, text)
    return False, f"Unsupported platform: {platform}"


def send_message(
    platform: Platform,
    channel_id: str,
    thread_id: str,
    text: str,
) -> tuple[bool, str]:
    """Synchronous wrapper; runs the async send in an event loop."""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        send_message_async(platform, channel_id, thread_id, text)
    )


async def _send_telegram(channel_id: str, thread_id: str, text: str) -> tuple[bool, str]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token or not channel_id:
        return False, "TELEGRAM_BOT_TOKEN or channel_id missing"
    try:
        import aiohttp
    except ImportError:
        return False, "aiohttp required for Telegram send"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: dict = {"chat_id": channel_id, "text": text}
    if thread_id:
        payload["message_thread_id"] = int(thread_id) if thread_id.isdigit() else thread_id
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                body = await resp.text()
                return False, f"Telegram API {resp.status}: {body[:500]}"
            return True, ""


async def _send_discord(channel_id: str, thread_id: str, text: str) -> tuple[bool, str]:
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token or not channel_id:
        return False, "DISCORD_BOT_TOKEN or channel_id missing"
    try:
        import aiohttp
    except ImportError:
        return False, "aiohttp required for Discord send"
    # Discord: POST to /channels/{channel_id}/messages (optionally in a thread)
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
    payload: dict = {"content": text[:2000]}  # Discord limit 2000
    if thread_id:
        payload["message_reference"] = {"channel_id": channel_id, "message_id": thread_id}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status not in (200, 201):
                body = await resp.text()
                return False, f"Discord API {resp.status}: {body[:500]}"
            return True, ""


async def _send_whatsapp(channel_id: str, thread_id: str, text: str) -> tuple[bool, str]:
    token = os.environ.get("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    if not token or not phone_number_id:
        return False, "WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID missing"
    # channel_id is typically the recipient wa_id (user's WhatsApp ID) when replying
    to_wa_id = channel_id or thread_id
    if not to_wa_id:
        return False, "WhatsApp requires channel_id (recipient wa_id) to send"
    try:
        import aiohttp
    except ImportError:
        return False, "aiohttp required for WhatsApp send"
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to_wa_id.lstrip("+"),
        "type": "text",
        "text": {"body": text[:4096]},
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status not in (200, 201):
                body = await resp.text()
                return False, f"WhatsApp API {resp.status}: {body[:500]}"
            return True, ""
