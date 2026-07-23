"""SQLite persistence for game saves."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any


class GameDatabase:
    """SQLite-backed save storage.

    Thread-safe via per-connection locking and WAL mode.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS saves (
                        save_id TEXT PRIMARY KEY,
                        case_id TEXT NOT NULL,
                        seed INTEGER NOT NULL DEFAULT 0,
                        state_version INTEGER NOT NULL DEFAULT 0,
                        game_over INTEGER NOT NULL DEFAULT 0,
                        resolution_notified INTEGER NOT NULL DEFAULT 0,
                        player_state TEXT NOT NULL,
                        event_log TEXT NOT NULL DEFAULT '[]',
                        view_cache TEXT,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    );
                    CREATE INDEX IF NOT EXISTS idx_saves_case ON saves(case_id);
                    CREATE TABLE IF NOT EXISTS idempotency_results (
                        cache_key TEXT PRIMARY KEY,
                        action_fingerprint TEXT NOT NULL,
                        response_json TEXT NOT NULL,
                        expires_at TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_idempotency_expires
                        ON idempotency_results(expires_at);
                """)
                conn.commit()
            finally:
                conn.close()

    def save_game(
        self,
        save_id: str,
        case_id: str,
        seed: int,
        state_version: int,
        game_over: bool,
        player_state_json: str,
        event_log_json: str,
        view_cache: str | None = None,
        resolution_notified: bool = False,
    ) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """INSERT OR REPLACE INTO saves
                       (save_id, case_id, seed, state_version, game_over,
                        resolution_notified, player_state, event_log, view_cache, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                    (
                        save_id,
                        case_id,
                        seed,
                        state_version,
                        1 if game_over else 0,
                        1 if resolution_notified else 0,
                        player_state_json,
                        event_log_json,
                        view_cache,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

    def load_game(self, save_id: str) -> dict[str, Any] | None:
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute("SELECT * FROM saves WHERE save_id = ?", (save_id,)).fetchone()
                if row is None:
                    return None
                return dict(row)
            finally:
                conn.close()

    def list_saves(self, case_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                if case_id:
                    rows = conn.execute(
                        "SELECT save_id, case_id, state_version, game_over, "
                        "created_at, updated_at FROM saves WHERE case_id = ? "
                        "ORDER BY updated_at DESC",
                        (case_id,),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT save_id, case_id, state_version, game_over, "
                        "created_at, updated_at FROM saves "
                        "ORDER BY updated_at DESC"
                    ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    def get_idempotency_result(self, cache_key: str) -> dict[str, Any] | None:
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute(
                    "SELECT * FROM idempotency_results WHERE cache_key = ? AND expires_at > datetime('now')",
                    (cache_key,),
                ).fetchone()
                if row is None:
                    return None
                return dict(row)
            finally:
                conn.close()

    def set_idempotency_result(
        self,
        cache_key: str,
        action_fingerprint: str,
        response_json: str,
        ttl_seconds: int = 30,
    ) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """INSERT OR REPLACE INTO idempotency_results
                       (cache_key, action_fingerprint, response_json, expires_at)
                       VALUES (?, ?, ?, datetime('now', '+' || ? || ' seconds'))""",
                    (cache_key, action_fingerprint, response_json, ttl_seconds),
                )
                conn.commit()
            finally:
                conn.close()

    def clean_expired_idempotency(self) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("DELETE FROM idempotency_results WHERE expires_at <= datetime('now')")
                conn.commit()
            finally:
                conn.close()

    def delete_save(self, save_id: str) -> bool:
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.execute("DELETE FROM saves WHERE save_id = ?", (save_id,))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()
