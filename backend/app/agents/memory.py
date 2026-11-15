"""SQLite-backed long-term memory for agent workflows."""

import json
import logging
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

logger = logging.getLogger(__name__)


class LongTermMemoryAgent:
    """Persist JSON-compatible agent memories across application restarts."""

    def __init__(
        self,
        vector_store_path: str = "./vector_store",
        embedding_model: str = "all-MiniLM-L6-v2",
        database_path: Optional[str] = None,
    ):
        del embedding_model
        configured_path = database_path or os.getenv("MEMORY_DB_PATH")
        self._database_path = Path(
            configured_path or Path(vector_store_path) / "memory.sqlite3"
        )
        self._initialized = False

    def _connect(self) -> sqlite3.Connection:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    async def initialize(self) -> None:
        first_initialization = not self._initialized
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    ttl INTEGER,
                    access_count INTEGER NOT NULL DEFAULT 0,
                    last_accessed REAL NOT NULL
                )
                """
            )
        self._initialized = True
        if first_initialization:
            logger.info("SQLite memory store ready at %s", self._database_path)

    async def store(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        await self.initialize()
        serialized = json.dumps(value, ensure_ascii=False)
        now = time.time()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO memories (key, value, created_at, ttl, last_accessed)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    created_at = excluded.created_at,
                    ttl = excluded.ttl,
                    access_count = 0,
                    last_accessed = excluded.last_accessed
                """,
                (key, serialized, now, ttl, now),
            )
        return True

    async def retrieve(self, key: str) -> Any:
        await self.initialize()
        now = time.time()
        with self._connection() as connection:
            row = connection.execute(
                "SELECT value, created_at, ttl FROM memories WHERE key = ?",
                (key,),
            ).fetchone()
            if row is None:
                return None

            if row["ttl"] is not None and now - row["created_at"] > row["ttl"]:
                connection.execute("DELETE FROM memories WHERE key = ?", (key,))
                return None

            connection.execute(
                """
                UPDATE memories SET access_count = access_count + 1,
                    last_accessed = ? WHERE key = ?
                """,
                (now, key),
            )
            return json.loads(row["value"])

    async def query(
        self, query: str, session_id: Optional[str] = None
    ) -> dict[str, Any]:
        await self.initialize()
        started = time.perf_counter()
        now = time.time()
        query_lower = query.casefold()
        matches = []

        with self._connection() as connection:
            connection.execute(
                "DELETE FROM memories WHERE ttl IS NOT NULL AND ? - created_at > ttl",
                (now,),
            )
            rows = connection.execute(
                "SELECT key, value FROM memories ORDER BY last_accessed DESC"
            ).fetchall()
            for row in rows:
                value = json.loads(row["value"])
                if query_lower and query_lower not in row["key"].casefold() \
                        and query_lower not in row["value"].casefold():
                    continue
                matches.append(
                    {
                        "key": row["key"],
                        "type": "exact_match" if row["key"] == query else "pattern_match",
                        "value": value,
                        "score": 1.0 if row["key"] == query else 0.8,
                    }
                )
            if matches:
                connection.executemany(
                    "UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE key = ?",
                    [(now, match["key"]) for match in matches],
                )

        return {
            "query": query,
            "session_id": session_id,
            "matches": matches[:10],
            "total_matches": len(matches),
            "agent": "memory",
            "query_time_ms": round((time.perf_counter() - started) * 1000, 2),
        }

    async def remove(self, key: str) -> bool:
        await self.initialize()
        with self._connection() as connection:
            cursor = connection.execute("DELETE FROM memories WHERE key = ?", (key,))
        return cursor.rowcount > 0

    async def clear(self) -> bool:
        await self.initialize()
        with self._connection() as connection:
            connection.execute("DELETE FROM memories")
        return True

    async def list_keys(self, prefix: Optional[str] = None) -> list[str]:
        await self.initialize()
        with self._connection() as connection:
            if prefix:
                rows = connection.execute(
                    "SELECT key FROM memories WHERE key LIKE ? ORDER BY key",
                    (f"{prefix}%",),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT key FROM memories ORDER BY key"
                ).fetchall()
        return [row["key"] for row in rows]

    def is_ready(self) -> bool:
        return self._initialized


_memory_agent: Optional[LongTermMemoryAgent] = None


def get_memory_agent() -> LongTermMemoryAgent:
    global _memory_agent
    if _memory_agent is None:
        _memory_agent = LongTermMemoryAgent()
    return _memory_agent
