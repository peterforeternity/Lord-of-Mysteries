"""Tests for idempotent SQLite schema migration.

Validates that an existing database missing the resolution_notified column
is correctly upgraded, old records are preserved, and the migration is
safe to run multiple times.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

from game_api.database import GameDatabase


def _create_legacy_db(db_path: Path) -> None:
    """Create a saves table *without* the resolution_notified column."""
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE saves (
                save_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                seed INTEGER NOT NULL DEFAULT 0,
                state_version INTEGER NOT NULL DEFAULT 0,
                game_over INTEGER NOT NULL DEFAULT 0,
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

        # Insert a legacy save record — no resolution_notified column
        conn.execute(
            """INSERT INTO saves
               (save_id, case_id, seed, state_version, game_over,
                player_state, event_log, view_cache)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "legacy_save_001",
                "case_clockmaker_01",
                42,
                3,
                0,
                json.dumps({"spirituality": 5}),
                "[]",
                None,
            ),
        )
        conn.commit()
    finally:
        conn.close()


class TestDatabaseMigration:
    def test_migration_adds_column(self) -> None:
        """Legacy db without resolution_notified gets the column after init."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test_legacy.db"
            _create_legacy_db(db_path)

            # Verify column does NOT exist before migration
            conn = sqlite3.connect(str(db_path))
            cols_before = {row[1] for row in conn.execute("PRAGMA table_info(saves)")}
            conn.close()
            assert "resolution_notified" not in cols_before

            # Initialise GameDatabase — triggers migration
            GameDatabase(db_path)

            # Verify column EXISTS after migration
            conn2 = sqlite3.connect(str(db_path))
            cols_after = {row[1] for row in conn2.execute("PRAGMA table_info(saves)")}
            conn2.close()
            assert "resolution_notified" in cols_after

    def test_legacy_record_preserved(self) -> None:
        """Old save records remain readable after migration."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test_preserve.db"
            _create_legacy_db(db_path)
            db = GameDatabase(db_path)  # triggers migration

            row = db.load_game("legacy_save_001")
            assert row is not None
            assert row["save_id"] == "legacy_save_001"
            assert row["case_id"] == "case_clockmaker_01"
            assert row["seed"] == 42
            assert row["state_version"] == 3
            assert row["game_over"] == 0

    def test_legacy_defaults_to_false(self) -> None:
        """Old records default resolution_notified to 0 (False)."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test_default.db"
            _create_legacy_db(db_path)
            db = GameDatabase(db_path)  # triggers migration

            row = db.load_game("legacy_save_001")
            assert row is not None
            assert row["resolution_notified"] == 0

    def test_save_updates_resolution_notified(self) -> None:
        """After migration, saving a record can set resolution_notified to True."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test_save.db"
            _create_legacy_db(db_path)
            db = GameDatabase(db_path)

            # Save with resolution_notified=True
            db.save_game(
                save_id="legacy_save_001",
                case_id="case_clockmaker_01",
                seed=42,
                state_version=4,
                game_over=False,
                player_state_json=json.dumps({"spirituality": 5}),
                event_log_json="[]",
                resolution_notified=True,
            )

            row = db.load_game("legacy_save_001")
            assert row is not None
            assert row["resolution_notified"] == 1  # SQLite stores bool as int

    def test_repeated_migration_is_idempotent(self) -> None:
        """Running init multiple times does not raise errors."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test_idempotent.db"
            _create_legacy_db(db_path)

            # Run migration 3 times
            GameDatabase(db_path)
            GameDatabase(db_path)
            db3 = GameDatabase(db_path)

            # All should be usable
            row = db3.load_game("legacy_save_001")
            assert row is not None
            assert row["save_id"] == "legacy_save_001"

    def test_new_database_includes_column(self) -> None:
        """A fresh database (no legacy table) still has the column."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test_fresh.db"
            GameDatabase(db_path)

            conn = sqlite3.connect(str(db_path))
            cols = {row[1] for row in conn.execute("PRAGMA table_info(saves)")}
            conn.close()
            assert "resolution_notified" in cols

    def test_save_load_cycle_after_migration(self) -> None:
        """Full save → load cycle works correctly on a migrated db."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test_cycle.db"
            _create_legacy_db(db_path)
            db = GameDatabase(db_path)

            # Save with resolution_notified=False
            db.save_game(
                save_id="legacy_save_001",
                case_id="case_clockmaker_01",
                seed=42,
                state_version=5,
                game_over=False,
                player_state_json=json.dumps({"spirituality": 10}),
                event_log_json="[]",
                resolution_notified=False,
            )

            row = db.load_game("legacy_save_001")
            assert row is not None
            assert row["state_version"] == 5
            assert row["resolution_notified"] == 0

            # Save with resolution_notified=True, then re-load
            db.save_game(
                save_id="legacy_save_001",
                case_id="case_clockmaker_01",
                seed=42,
                state_version=6,
                game_over=False,
                player_state_json=json.dumps({"spirituality": 10}),
                event_log_json="[]",
                resolution_notified=True,
            )

            row = db.load_game("legacy_save_001")
            assert row is not None
            assert row["resolution_notified"] == 1
