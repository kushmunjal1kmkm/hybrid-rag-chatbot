"""
core/memory.py — SQLite-backed conversation persistence for ChatMind.

Two separate concerns:
  1. Conversation METADATA (id, title, timestamps, stats) in a `conversations`
     table managed here directly.
  2. MESSAGE CONTENT stored by LangChain's SQLChatMessageHistory, keyed by
     session_id (= conversation id).
"""
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from langchain_community.chat_message_histories import SQLChatMessageHistory

import config

# SQLAlchemy connection string — use POSIX path for cross-platform safety
_DB_URL = "sqlite:///" + Path(config.SQLITE_DB_PATH).as_posix()


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.SQLITE_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# Schema init
# ─────────────────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create tables on first run. Safe to call on every startup."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id           TEXT PRIMARY KEY,
                title        TEXT NOT NULL DEFAULT 'New Conversation',
                created_at   TEXT NOT NULL,
                updated_at   TEXT NOT NULL,
                model        TEXT DEFAULT '',
                persona      TEXT DEFAULT '',
                total_tokens INTEGER DEFAULT 0,
                message_count INTEGER DEFAULT 0
            )
        """)
        conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Conversation CRUD
# ─────────────────────────────────────────────────────────────────────────────

def create_conversation(
    title: str = "New Conversation",
    model: str = "",
    persona: str = "",
) -> str:
    """Insert a new conversation row and return its UUID."""
    conv_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """INSERT INTO conversations
               (id, title, created_at, updated_at, model, persona)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (conv_id, title, now, now, model, persona),
        )
        conn.commit()
    return conv_id


def list_conversations() -> list[dict]:
    """Return all conversations ordered newest-first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_conversation(conv_id: str) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (conv_id,)
        ).fetchone()
    return dict(row) if row else None


def update_conversation_title(conv_id: str, title: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, now, conv_id),
        )
        conn.commit()


def update_conversation_meta(conv_id: str, model: str = "", persona: str = "") -> None:
    """Update model and persona metadata on a conversation row."""
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "UPDATE conversations SET model = ?, persona = ?, updated_at = ? WHERE id = ?",
            (model, persona, now, conv_id),
        )
        conn.commit()


def update_conversation_stats(conv_id: str, tokens_used: int = 0) -> None:
    """Increment turn count and token total after each exchange."""
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """UPDATE conversations
               SET total_tokens   = total_tokens + ?,
                   message_count  = message_count + 1,
                   updated_at     = ?
               WHERE id = ?""",
            (tokens_used, now, conv_id),
        )
        conn.commit()


def delete_conversation(conv_id: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Message History (LangChain integration)
# ─────────────────────────────────────────────────────────────────────────────

def get_message_history(session_id: str) -> SQLChatMessageHistory:
    """
    Return a LangChain-compatible message history backed by SQLite.
    Used as the `get_session_history` callable in RunnableWithMessageHistory.
    """
    return SQLChatMessageHistory(
        session_id=session_id,
        connection=_DB_URL,
    )


def clear_message_history(conv_id: str) -> None:
    """Erase all messages for a conversation without deleting metadata."""
    history = get_message_history(conv_id)
    history.clear()
    # Reset stats
    with _connect() as conn:
        conn.execute(
            "UPDATE conversations SET total_tokens = 0, message_count = 0 WHERE id = ?",
            (conv_id,),
        )
        conn.commit()
