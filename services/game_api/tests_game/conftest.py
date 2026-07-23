"""Test fixtures for game_api."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game_api.database import GameDatabase
from game_api.main import app
from game_api.routes import init_manager


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def db_path(temp_dir):
    return temp_dir / "test_saves.db"


@pytest.fixture
def game_db(db_path):
    return GameDatabase(db_path)


@pytest.fixture
def client(temp_dir):
    """Create a test client with a temp database."""
    db_dir = temp_dir
    db = GameDatabase(db_dir / "test_saves.db")
    init_manager(db)
    return TestClient(app)


@pytest.fixture
def playthrough_dir():
    """Path to the playthrough JSON directory."""
    return (
        Path(__file__).resolve().parent.parent.parent.parent
        / "content"
        / "cases"
        / "case_clockmaker_01"
        / "playthroughs"
    )


@pytest.fixture
def case_dir():
    """Path to the case data directory."""
    return (
        Path(__file__).resolve().parent.parent.parent.parent
        / "content"
        / "cases"
        / "case_clockmaker_01"
    )
