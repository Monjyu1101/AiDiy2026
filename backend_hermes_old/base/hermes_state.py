"""AiDiy Hermes session state store.

旧 Hermes の ``hermes_state.py`` 互換として、セッション検索と dashboard が
参照する読み取り中心 API だけを提供する軽量 SQLite ラッパー。
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from base.hermes_constants import get_hermes_home


DEFAULT_DB_PATH = get_hermes_home() / "state.db"


class SessionDB:
    """SQLite-backed session storage compatible with legacy callers."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "SessionDB":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                source TEXT DEFAULT 'cli',
                user_id TEXT,
                model TEXT,
                model_config TEXT,
                system_prompt TEXT,
                parent_session_id TEXT,
                started_at REAL NOT NULL,
                ended_at REAL,
                end_reason TEXT,
                message_count INTEGER DEFAULT 0,
                tool_call_count INTEGER DEFAULT 0,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                title TEXT,
                api_call_count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                tool_call_id TEXT,
                tool_calls TEXT,
                tool_name TEXT,
                timestamp REAL NOT NULL,
                token_count INTEGER,
                finish_reason TEXT,
                reasoning TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at DESC);
            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);
            """
        )
        self._conn.commit()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row | None) -> Optional[Dict[str, Any]]:
        return dict(row) if row is not None else None

    def create_session(
        self,
        session_id: str,
        source: str = "cli",
        model: str = "",
        system_prompt: str = "",
        **extra: Any,
    ) -> str:
        now = time.time()
        self._conn.execute(
            """
            INSERT OR IGNORE INTO sessions
                (id, source, model, system_prompt, parent_session_id, started_at, title)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                source,
                model,
                system_prompt,
                extra.get("parent_session_id"),
                now,
                extra.get("title"),
            ),
        )
        self._conn.commit()
        return session_id

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str = "",
        **extra: Any,
    ) -> int:
        cur = self._conn.execute(
            """
            INSERT INTO messages
                (session_id, role, content, tool_call_id, tool_calls, tool_name, timestamp, token_count, finish_reason, reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                content,
                extra.get("tool_call_id"),
                json.dumps(extra.get("tool_calls"), ensure_ascii=False)
                if isinstance(extra.get("tool_calls"), (list, dict))
                else extra.get("tool_calls"),
                extra.get("tool_name"),
                extra.get("timestamp") or time.time(),
                extra.get("token_count"),
                extra.get("finish_reason"),
                extra.get("reasoning"),
            ),
        )
        self._conn.execute(
            "UPDATE sessions SET message_count = message_count + 1 WHERE id = ?",
            (session_id,),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return self._row_to_dict(row)

    def get_session_title(self, session_id: str) -> Optional[str]:
        row = self._conn.execute("SELECT title FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return row["title"] if row else None

    def get_compression_tip(self, _session_id: str) -> Optional[str]:
        return None

    def search_sessions(self, source: Optional[str] = None, limit: int = 20, **_kw) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM sessions"
        params: list[Any] = []
        if source:
            sql += " WHERE source = ?"
            params.append(source)
        sql += " ORDER BY started_at DESC LIMIT ?"
        params.append(int(limit))
        return [dict(row) for row in self._conn.execute(sql, params).fetchall()]

    def list_sessions_rich(
        self,
        limit: int = 50,
        offset: int = 0,
        exclude_sources: Optional[List[str]] = None,
        **_kw,
    ) -> List[Dict[str, Any]]:
        where = []
        params: list[Any] = []
        if exclude_sources:
            where.append("source NOT IN (%s)" % ",".join("?" for _ in exclude_sources))
            params.extend(exclude_sources)
        sql = "SELECT * FROM sessions"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY started_at DESC LIMIT ? OFFSET ?"
        params.extend([int(limit), int(offset)])
        sessions = [dict(row) for row in self._conn.execute(sql, params).fetchall()]
        for session in sessions:
            session["last_active"] = session.get("ended_at") or session.get("started_at")
            preview_row = self._conn.execute(
                "SELECT content FROM messages WHERE session_id = ? ORDER BY timestamp ASC LIMIT 1",
                (session["id"],),
            ).fetchone()
            session["preview"] = (preview_row["content"] if preview_row else "") or ""
        return sessions

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC, id ASC",
            (session_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_messages_as_conversation(self, session_id: str) -> List[Dict[str, Any]]:
        return self.get_messages(session_id)

    def search_messages(
        self,
        query: str,
        role_filter: Optional[List[str]] = None,
        exclude_sources: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
        **_kw,
    ) -> List[Dict[str, Any]]:
        where = ["m.content LIKE ?"]
        params: list[Any] = [f"%{query}%"]
        if role_filter:
            where.append("m.role IN (%s)" % ",".join("?" for _ in role_filter))
            params.extend(role_filter)
        if exclude_sources:
            where.append("s.source NOT IN (%s)" % ",".join("?" for _ in exclude_sources))
            params.extend(exclude_sources)
        sql = (
            "SELECT m.*, s.title, s.source, s.parent_session_id, s.started_at "
            "FROM messages m JOIN sessions s ON s.id = m.session_id "
            "WHERE " + " AND ".join(where) +
            " ORDER BY m.timestamp DESC LIMIT ? OFFSET ?"
        )
        params.extend([int(limit), int(offset)])
        return [dict(row) for row in self._conn.execute(sql, params).fetchall()]

    def delete_session(self, session_id: str, **_kw) -> bool:
        self._conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cur = self._conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self._conn.commit()
        return cur.rowcount > 0
