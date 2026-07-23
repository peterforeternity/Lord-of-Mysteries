# 诡秘之主

High-density investigation RPG — headless core, AI dialogue gateway, and browser-based text game MVP.

## Quick Start

```bash
# Quick dev start (both Game API + Frontend)
bash scripts/dev_text_game.sh

# Or start manually:

# Install dependencies
uv sync
cd apps/web && npm ci && cd ..

# Run all Python checks
uv run ruff check .
uv run black --check .
uv run mypy .
uv run pytest --cov --cov-report=term-missing --cov-fail-under=90

# Run all playthroughs
uv run python tools/run_playthrough.py --all

# Start Game API (text game backend)
uv run uvicorn game_api.main:app --host 127.0.0.1 --port 8000

# Start AI Gateway (if needed, disabled by default in MVP)
uv run uvicorn ai_gateway.main:app --host 127.0.0.1 --port 8001

# Start Frontend (in another terminal)
cd apps/web && VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1 --port 5173
```

## Text Game MVP

The browser-based text game is at `apps/web/` (React + TypeScript + Vite).

**Pages:**
- Start page (new/continue/case select/settings)
- Main game page (3-column desktop, tab-based mobile)
- Deduction board
- Ritual interface
- Save/Load
- Case conclusion

**Game API** at `services/game_api/` provides:
- `POST /v1/game/new` — Create new game
- `POST /v1/game/{save_id}/action` — Execute action
- `GET /v1/game/{save_id}/view` — Get game view
- `POST /v1/game/{save_id}/save` — Save game
- `POST /v1/game/{save_id}/load` — Load game
- `GET /v1/cases` — List available cases

Actions: `travel`, `inspect`, `talk`, `use_spirit_vision`, `perform_divination`, `perform_ritual`, `use_item`, `submit_hypothesis`, `rest`, `save`, `load`

AI is disabled by default in Phase 1. All NPC dialogue uses pre-made claims and fallback dialogue.

## API Endpoints

| Method | Path | Service | Description |
|--------|------|---------|-------------|
| GET | `/v1/health` | game_api | Health check |
| GET | `/v1/cases` | game_api | List available cases |
| POST | `/v1/game/new` | game_api | Create new game session |
| POST | `/v1/game/{id}/action` | game_api | Execute game action |
| GET | `/v1/game/{id}/view` | game_api | Get current game view |
| POST | `/v1/game/{id}/save` | game_api | Save game |
| POST | `/v1/game/{id}/load` | game_api | Load game |
| GET | `/v1/health` | ai_gateway | AI Gateway health check |
| POST | `/v1/dialogue/respond` | ai_gateway | NPC dialogue response |

## Project Structure

```
├── apps/web/                      # React + TypeScript frontend
├── docs/                          # Architecture & design docs
├── schemas/                       # JSON Schema definitions
├── content/cases/case_clockmaker_01/  # Case data
├── packages/investigation_core/   # Domain engine (deterministic, frozen)
├── services/
│   ├── ai_gateway/                # FastAPI AI Gateway
│   └── game_api/                  # FastAPI Game API (SQLite saves)
├── tools/                         # Validation & CI tools
├── .github/workflows/             # CI configuration
└── unreal/                        # UE5.8 integration (paused)
```

## Phase 1 (Completed)

- Headless Investigation Core (Fact, Claim, Clue, Hypothesis, Ending)
- Original case "The Clockmaker's Disappearance" (5 locations, 6 NPCs, 4 hypotheses, 5 endings)
- Dual-source validation for all core secret facts
- 7 deterministic playthroughs
- AI Gateway with safety boundary tests
- 311 automated tests with 96.9% coverage
- CI pipeline (ruff, black, mypy, pytest, playthrough)

## Principles

1. **Deterministic Core** — Same state + same seed = same result
2. **AI Read-Only** — LLM never writes game state
3. **No Secret in Client** — All credentials on server only
4. **Fail Closed** — AI errors fall back gracefully
5. **Dual Source** — Every critical fact has ≥2 independent clue paths
6. **No Pixel Love** — MVP uses CSS-only visuals
