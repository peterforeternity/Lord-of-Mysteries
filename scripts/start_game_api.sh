#!/bin/bash
# Start Game API server with uv (handles editable installs correctly)
cd "$(dirname "$0")/.."
exec uv run python -m uvicorn game_api.main:app --host 127.0.0.1 --port 8000
