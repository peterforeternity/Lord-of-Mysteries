#!/bin/bash
# ============================================================
# Project Grey Fog Text Game MVP — Dev Startup Script
# ============================================================
# Starts both the Game API backend and React frontend.
# Kill with Ctrl+C (kills both processes).
# ============================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Project Grey Fog — Text Game MVP ==="
echo ""
echo "Starting services..."
echo ""

# Start Game API (port 8000)
echo "[1/2] Starting Game API on http://127.0.0.1:8000 ..."
cd "$PROJECT_ROOT"
uv run uvicorn game_api.main:app --host 127.0.0.1 --port 8000 &
GAME_API_PID=$!

# Wait for Game API to be ready
echo "  Waiting for Game API..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:8000/v1/health > /dev/null 2>&1; then
        echo "  Game API ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "  ERROR: Game API did not start in time"
        kill $GAME_API_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Start Frontend (port 5173)
echo "[2/2] Starting Frontend on http://127.0.0.1:5173 ..."
cd "$PROJECT_ROOT/apps/web"
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1 --port 5173 &
FRONTEND_PID=$!

echo ""
echo "=== All services started ==="
echo "  Game API:  http://127.0.0.1:8000"
echo "  Frontend:  http://127.0.0.1:5173"
echo "  API Docs:  http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services."
echo ""

# Trap Ctrl+C to kill both
trap "echo 'Stopping...'; kill $GAME_API_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

# Wait for either to exit
wait
