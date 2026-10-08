"""LUNA persistent memory manager - Phase 12.2."""

from __future__ import annotations

import re
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class MemoryManager:
    """Thread-safe persistent SQLite memory for LUNA.

    Supports arbitrary memory types, keyed memories, user identity,
    conversation history, search, and soft-delete/forget operations.
    """

    def __init__(self, db_path: Optional[str | Path] = None):
        if db_path is None:
            project_root = Path(__file__).resolve().parent.parent
            db_path = project_root / "data" / "memory" / "luna_memory.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.connection = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False,
        )
        self.connection.row_factory = sqlite3.Row
        self._closed = False
        self._create_tables()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _clean(value: str | None) -> str:
        if value is None:
            return ""
        return value.strip()

    @staticmethod
    def _safe_confidence(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _ensure_open(self) -> None:
        if self._closed or self.connection is None:
            raise RuntimeError("LUNA memory database is closed.")

    def _create_tables(self) -> None:
        with self._lock:
            self._ensure_open()
            cursor = self.connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    memory_key TEXT,
                    memory_value TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 1.0,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(memory_key)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_memories_active ON memories(active)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)"
            )
            self.connection.commit()

    # ------------------------------------------------------------------
    # LONG-TERM MEMORY
    # ------------------------------------------------------------------

    def remember(
        self,
        value: str,
        memory_type: str = "fact",
        key: Optional[str] = None,
        source: str = "user",
        confidence: float = 1.0,
    ) -> str:
        value = self._clean(value)
        if not value:
            raise ValueError("Memory value cannot be empty.")

        memory_id = str(uuid.uuid4())
        now = self._now()
        memory_type = self._clean(memory_type).lower() or "fact"
        source = self._clean(source).lower() or "user"
        confidence = self._safe_confidence(confidence)

        with self._lock:
            self._ensure_open()
            self.connection.execute(
                """
                INSERT INTO memories (
                    id, memory_type, memory_key, memory_value,
                    source, confidence, active, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    memory_id,
                    memory_type,
                    self._clean(key) or None,
                    value,
                    source,
                    confidence,
                    now,
                    now,
                ),
            )
            self.connection.commit()

        return memory_id

    def set_memory(
        self,
        key: str,
        value: str,
        memory_type: str = "fact",
        source: str = "user",
        confidence: float = 1.0,
    ) -> str:
        key = self._clean(key)
        value = self._clean(value)
        if not key:
            raise ValueError("Memory key cannot be empty.")
        if not value:
            raise ValueError("Memory value cannot be empty.")

        memory_type = self._clean(memory_type).lower() or "fact"
        source = self._clean(source).lower() or "user"
        confidence = self._safe_confidence(confidence)
        now = self._now()

        with self._lock:
            self._ensure_open()
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT id FROM memories
                WHERE memory_key = ? AND active = 1
                ORDER BY updated_at DESC LIMIT 1
                """,
                (key,),
            )
            row = cursor.fetchone()

            if row:
                memory_id = row["id"]
                cursor.execute(
                    """
                    UPDATE memories
                    SET memory_type = ?, memory_value = ?, source = ?,
                        confidence = ?, active = 1, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        memory_type,
                        value,
                        source,
                        confidence,
                        now,
                        memory_id,
                    ),
                )
            else:
                memory_id = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO memories (
                        id, memory_type, memory_key, memory_value,
                        source, confidence, active, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                    """,
                    (
                        memory_id,
                        memory_type,
                        key,
                        value,
                        source,
                        confidence,
                        now,
                        now,
                    ),
                )

            self.connection.commit()
            return memory_id

    def get_memory(self, key: str) -> Optional[dict[str, Any]]:
        key = self._clean(key)
        if not key:
            return None

        with self._lock:
            self._ensure_open()
            row = self.connection.execute(
                """
                SELECT id, memory_type, memory_key, memory_value,
                       source, confidence, created_at, updated_at
                FROM memories
                WHERE memory_key = ? AND active = 1
                ORDER BY updated_at DESC LIMIT 1
                """,
                (key,),
            ).fetchone()
            return dict(row) if row else None

    def list_memories(
        self,
        memory_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 500))

        with self._lock:
            self._ensure_open()
            if memory_type:
                rows = self.connection.execute(
                    """
                    SELECT id, memory_type, memory_key, memory_value,
                           source, confidence, created_at, updated_at
                    FROM memories
                    WHERE active = 1 AND memory_type = ?
                    ORDER BY updated_at DESC LIMIT ?
                    """,
                    (self._clean(memory_type).lower(), limit),
                ).fetchall()
            else:
                rows = self.connection.execute(
                    """
                    SELECT id, memory_type, memory_key, memory_value,
                           source, confidence, created_at, updated_at
                    FROM memories
                    WHERE active = 1
                    ORDER BY updated_at DESC LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            return [dict(row) for row in rows]

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        query = self._clean(query)
        if not query:
            return []
        limit = max(1, min(int(limit), 100))
        pattern = f"%{query}%"

        with self._lock:
            self._ensure_open()
            rows = self.connection.execute(
                """
                SELECT id, memory_type, memory_key, memory_value,
                       source, confidence, created_at, updated_at
                FROM memories
                WHERE active = 1
                  AND (
                      memory_key LIKE ? OR
                      memory_value LIKE ? OR
                      memory_type LIKE ?
                  )
                ORDER BY updated_at DESC LIMIT ?
                """,
                (pattern, pattern, pattern, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def forget_memory(
        self,
        memory_id: Optional[str] = None,
        key: Optional[str] = None,
    ) -> bool:
        now = self._now()
        with self._lock:
            self._ensure_open()
            if memory_id:
                cursor = self.connection.execute(
                    """
                    UPDATE memories
                    SET active = 0, updated_at = ?
                    WHERE id = ? AND active = 1
                    """,
                    (now, self._clean(memory_id)),
                )
            elif key:
                cursor = self.connection.execute(
                    """
                    UPDATE memories
                    SET active = 0, updated_at = ?
                    WHERE memory_key = ? AND active = 1
                    """,
                    (now, self._clean(key)),
                )
            else:
                raise ValueError("Provide memory_id or key.")
            self.connection.commit()
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # USER PROFILE / IDENTITY
    # ------------------------------------------------------------------

    def set_name(self, name: str, source: str = "user") -> str:
        name = re.sub(r"\s+", " ", self._clean(name))
        name = name.strip(" \t\r\n.,!?;:")
        if not name:
            raise ValueError("Name cannot be empty.")
        return self.set_memory(
            key="name",
            value=name,
            memory_type="profile",
            source=source,
            confidence=1.0,
        )

    def get_name(self) -> Optional[str]:
        memory = self.get_memory("name")
        if not memory:
            return None
        return str(memory["memory_value"])

    # ------------------------------------------------------------------
    # CONVERSATION HISTORY
    # ------------------------------------------------------------------

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> int:
        session_id = self._clean(session_id)
        role = self._clean(role).lower()
        content = self._clean(content)

        if not session_id:
            raise ValueError("session_id cannot be empty.")
        if role not in {"user", "assistant", "system"}:
            raise ValueError("role must be user, assistant, or system.")
        if not content:
            raise ValueError("content cannot be empty.")

        with self._lock:
            self._ensure_open()
            cursor = self.connection.execute(
                """
                INSERT INTO conversations (
                    session_id, role, content, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, self._now()),
            )
            self.connection.commit()
            return int(cursor.lastrowid)

    def get_recent_messages(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 100))
        with self._lock:
            self._ensure_open()
            rows = self.connection.execute(
                """
                SELECT id, session_id, role, content, created_at
                FROM conversations
                WHERE session_id = ?
                ORDER BY id DESC LIMIT ?
                """,
                (self._clean(session_id), limit),
            ).fetchall()
            rows = list(reversed(rows))
            return [dict(row) for row in rows]

    def get_recent_global_messages(self, limit: int = 10) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 100))
        with self._lock:
            self._ensure_open()
            rows = self.connection.execute(
                """
                SELECT id, session_id, role, content, created_at
                FROM conversations
                ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
            rows = list(reversed(rows))
            return [dict(row) for row in rows]

    def clear_session(self, session_id: str) -> int:
        with self._lock:
            self._ensure_open()
            cursor = self.connection.execute(
                "DELETE FROM conversations WHERE session_id = ?",
                (self._clean(session_id),),
            )
            self.connection.commit()
            return cursor.rowcount

    # ------------------------------------------------------------------
    # STATS / CLOSE
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, int]:
        with self._lock:
            self._ensure_open()
            memory_count = self.connection.execute(
                "SELECT COUNT(*) FROM memories WHERE active = 1"
            ).fetchone()[0]
            conversation_count = self.connection.execute(
                "SELECT COUNT(*) FROM conversations"
            ).fetchone()[0]
            return {
                "memories": int(memory_count),
                "conversation_messages": int(conversation_count),
            }

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            try:
                self.connection.commit()
            except Exception:
                pass
            try:
                self.connection.close()
            finally:
                self._closed = True
                self.connection = None

    def __enter__(self) -> "MemoryManager":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()