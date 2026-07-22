# Project Grey Fog

High-density investigation RPG headless core and AI dialogue gateway.

## Quick Start

```bash
# Install dependencies (no PYTHONPATH needed)
uv sync

# Run all checks
uv run ruff check .
uv run black --check .
uv run mypy .
uv run pytest --cov --cov-report=term-missing --cov-fail-under=90

# Run CLI Demo
uv run python -m investigation_core

# Run AI Gateway
uv run uvicorn ai_gateway.main:app

# Content validation tools
uv run python tools/validate_content.py content/cases/case_clockmaker_01
uv run python tools/check_clue_reachability.py content/cases/case_clockmaker_01
uv run python tools/enumerate_endings.py content/cases/case_clockmaker_01
uv run python tools/simulate_npc_removal.py content/cases/case_clockmaker_01
uv run python tools/run_playthrough.py --all
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/health` | Health check |
| GET | `/v1/prompt-version` | Current prompt & model version |
| POST | `/v1/dialogue/respond` | NPC dialogue response |
| POST | `/v1/dialogue/classify-intent` | Classify player intent |
| POST | `/v1/case/recap` | Case investigation recap |
| GET | `/v1/metrics` | Request metrics summary |

All errors return stable `error_code` in the response body.

## Project Structure

```
├── docs/                          # Architecture & design docs
├── schemas/                       # JSON Schema definitions
├── content/cases/case_clockmaker_01/  # Original case "The Clockmaker's Disappearance"
├── packages/investigation_core/   # Domain engine (deterministic)
├── services/ai_gateway/           # FastAPI AI Gateway with MockLLMProvider
├── tools/                         # Content validation, CI, and playthrough tools
├── .github/workflows/             # CI configuration
└── unreal/                        # UE5.8 integration (future)
```

## Phase 1 Scope (Completed)

- Headless Investigation Core (Fact, Claim, Clue, Hypothesis, Ending)
- Original case "The Clockmaker's Disappearance" (4 hypotheses, 5 endings)
- Dual-source validation for all core secret facts
- Hypothesis contradiction mechanism (contradicting facts auto-reject, contradicting clues reduce confidence)
- 7 deterministic playthroughs (true, partial, bad, AI-disabled, save/resume, ritual failure recovery, NPC removal recovery)
- AI Gateway with 15+ safety boundary tests
  - Prompt injection detection (JSON/XML/Markdown/code blocks)
  - Fact leak prevention
  - Claim whitelist enforcement
  - World action restriction (requests_world_action always False)
  - Timeout and disconnect resilience
- 290+ automated tests with 98.95% coverage
- CI pipeline (ruff, black, mypy, pytest, content validation, playthrough)

## Principles

1. **Deterministic Core** - Same state + same seed = same result
2. **AI Read-Only** - LLM never writes game state
3. **No Secret in Client** - All credentials on server only
4. **Fail Closed** - AI errors fall back gracefully
5. **Dual Source** - Every critical fact has ≥2 independent clue paths
