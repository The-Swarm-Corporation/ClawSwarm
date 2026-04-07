"""
SQLite message logger for ClawSwarm.

Logs every agent input (incoming user message) and output (agent reply)
to a SQLite database.  Defaults to an in-memory database (:memory:) so
no files are written; set the MESSAGE_LOG_DB environment variable to a
file path (e.g. "messages.db") to persist across restarts.

Usage
-----
    from claw_swarm.db import log_input, log_output, get_db, init_db
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
from typing import Optional

_DB_PATH = os.environ.get("MESSAGE_LOG_DB", ":memory:")

_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at_ms  INTEGER NOT NULL,
    message_id    TEXT,
    platform      TEXT,
    channel_id    TEXT,
    thread_id     TEXT,
    sender_id     TEXT,
    sender_handle TEXT,
    direction     TEXT NOT NULL CHECK(direction IN ('input', 'output')),
    text          TEXT
);
"""

_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_messages_logged_at
    ON messages (logged_at_ms);
"""


def _connect() -> sqlite3.Connection:
    """Open (or reuse) the module-level SQLite connection."""
    global _conn
    with _lock:
        if _conn is None:
            _conn = sqlite3.connect(
                _DB_PATH,
                check_same_thread=False,
            )
            _conn.row_factory = sqlite3.Row
            _conn.execute("PRAGMA journal_mode=WAL;")
            _conn.execute(_CREATE_TABLE)
            _conn.execute(_CREATE_INDEX)
            _conn.commit()
        return _conn


def init_db() -> None:
    """Explicitly initialise the database (called on startup)."""
    _connect()


def get_db() -> sqlite3.Connection:
    """Return the shared database connection, initialising it if needed."""
    return _connect()


def _insert(
    direction: str,
    text: str,
    message_id: str = "",
    platform: str = "",
    channel_id: str = "",
    thread_id: str = "",
    sender_id: str = "",
    sender_handle: str = "",
) -> None:
    conn = _connect()
    with _lock:
        conn.execute(
            """
            INSERT INTO messages
                (logged_at_ms, message_id, platform, channel_id,
                 thread_id, sender_id, sender_handle, direction, text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(time.time() * 1000),
                message_id,
                platform,
                channel_id,
                thread_id,
                sender_id,
                sender_handle,
                direction,
                text,
            ),
        )
        conn.commit()


def log_input(
    text: str,
    message_id: str = "",
    platform: str = "",
    channel_id: str = "",
    thread_id: str = "",
    sender_id: str = "",
    sender_handle: str = "",
) -> None:
    """Log an incoming user message."""
    _insert(
        direction="input",
        text=text,
        message_id=message_id,
        platform=platform,
        channel_id=channel_id,
        thread_id=thread_id,
        sender_id=sender_id,
        sender_handle=sender_handle,
    )


def log_output(
    text: str,
    message_id: str = "",
    platform: str = "",
    channel_id: str = "",
    thread_id: str = "",
    sender_handle: str = "",
) -> None:
    """Log an outgoing agent reply."""
    _insert(
        direction="output",
        text=text,
        message_id=message_id,
        platform=platform,
        channel_id=channel_id,
        thread_id=thread_id,
        sender_handle=sender_handle,
    )


def fetch_stats() -> dict:
    """
    Return aggregate statistics over the messages table.

    Keys returned
    -------------
    total           int   — total rows
    inputs          int   — direction='input' rows
    outputs         int   — direction='output' rows
    platforms       dict  — {platform: count} for inputs only
    top_channels    list  — [{"channel_id", "exchanges"}] top 5 by exchange count
    avg_input_len   float — average character length of input texts
    avg_output_len  float — average character length of output texts
    first_ms        int   — oldest logged_at_ms (0 if empty)
    last_ms         int   — newest logged_at_ms (0 if empty)
    per_day         dict  — {"YYYY-MM-DD": count} of input messages
    """
    conn = _connect()
    with _lock:

        def _scalar(sql: str, params: tuple = ()) -> int | float:
            row = conn.execute(sql, params).fetchone()
            return row[0] if row and row[0] is not None else 0

        total = _scalar("SELECT COUNT(*) FROM messages")
        inputs = _scalar(
            "SELECT COUNT(*) FROM messages WHERE direction='input'"
        )
        outputs = _scalar(
            "SELECT COUNT(*) FROM messages WHERE direction='output'"
        )

        # per-platform breakdown (inputs only)
        platform_rows = conn.execute(
            "SELECT COALESCE(platform,'unknown'), COUNT(*)"
            " FROM messages WHERE direction='input'"
            " GROUP BY platform ORDER BY COUNT(*) DESC"
        ).fetchall()
        platforms = {r[0]: r[1] for r in platform_rows}

        # top 5 channels by number of input messages (= exchanges)
        chan_rows = conn.execute(
            "SELECT COALESCE(channel_id,'unknown'), COUNT(*) AS n"
            " FROM messages WHERE direction='input'"
            " GROUP BY channel_id ORDER BY n DESC LIMIT 5"
        ).fetchall()
        top_channels = [
            {"channel_id": r[0], "exchanges": r[1]} for r in chan_rows
        ]

        avg_input_len = _scalar(
            "SELECT AVG(LENGTH(text)) FROM messages"
            " WHERE direction='input'"
        )
        avg_output_len = _scalar(
            "SELECT AVG(LENGTH(text)) FROM messages"
            " WHERE direction='output'"
        )

        first_ms = _scalar("SELECT MIN(logged_at_ms) FROM messages")
        last_ms = _scalar("SELECT MAX(logged_at_ms) FROM messages")

        # messages per calendar day (UTC) for inputs
        day_rows = conn.execute(
            "SELECT DATE(logged_at_ms / 1000, 'unixepoch') AS d,"
            " COUNT(*) FROM messages WHERE direction='input'"
            " GROUP BY d ORDER BY d"
        ).fetchall()
        per_day = {r[0]: r[1] for r in day_rows}

    return {
        "total": total,
        "inputs": inputs,
        "outputs": outputs,
        "platforms": platforms,
        "top_channels": top_channels,
        "avg_input_len": round(float(avg_input_len), 1),
        "avg_output_len": round(float(avg_output_len), 1),
        "first_ms": int(first_ms),
        "last_ms": int(last_ms),
        "per_day": per_day,
    }


def fetch_recent(limit: int = 0) -> list[sqlite3.Row]:
    """Return rows ordered newest-first.  0 (default) means all rows."""
    conn = _connect()
    with _lock:
        if limit and limit > 0:
            cur = conn.execute(
                "SELECT * FROM messages"
                " ORDER BY logged_at_ms DESC LIMIT ?",
                (limit,),
            )
        else:
            cur = conn.execute(
                "SELECT * FROM messages ORDER BY logged_at_ms DESC"
            )
        return cur.fetchall()
