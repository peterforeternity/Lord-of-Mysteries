"""Tests for scripted playthrough system.

Each playthrough JSON exercises a specific scenario path through the case.
Tests verify that the expected ending, clues, and corruption constraints are met.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from investigation_core import CaseLoader, CaseStateMachine, SaveRepository
from investigation_core.models import SaveData

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CASE_DIR = PROJECT_ROOT / "content" / "cases" / "case_clockmaker_01"
PLAYTHROUGHS_DIR = CASE_DIR / "playthroughs"


def _run_playthrough(playthrough_path: Path) -> dict:
    """Execute a single playthrough and return results dict."""
    with open(playthrough_path) as f:
        config = json.load(f)

    seed = config.get("seed", 0)
    actions = config["actions"]
    expected_ending_id = config.get("expected_ending_id", "")
    expected_clue_ids = set(config.get("expected_clue_ids", []))
    expected_corruption_max = config.get("expected_corruption_max", 999)

    loader = CaseLoader(CASE_DIR)
    case = loader.load_case()
    sm = CaseStateMachine(case)
    sm.player_state.seed = seed

    save_dir = Path(tempfile.mkdtemp(prefix=f"save_{config['id']}_"))
    save_repo = SaveRepository(save_dir)

    for action in actions:
        action_type = action["action"]

        if action_type == "travel":
            sm.move_to_location(action["location_id"])

        elif action_type == "inspect":
            sm.discover_clue(action["clue_id"])

        elif action_type == "talk":
            for cid in action.get("claim_ids", []):
                if cid not in sm.player_state.revealed_claim_ids:
                    sm.player_state.revealed_claim_ids.append(cid)

        elif action_type == "use_ability":
            event_id = action["event"]
            if event_id not in sm.player_state.completed_events:
                sm.player_state.completed_events.append(event_id)

        elif action_type == "perform_divination":
            sm.perform_divination(
                action.get("question", ""),
                action.get("seed", seed),
            )

        elif action_type == "perform_ritual":
            sm.perform_ritual(
                action["ritual_id"],
                action.get("materials", []),
                action.get("seed", seed),
            )

        elif action_type == "submit_hypothesis":
            sm.submit_hypothesis(action["hypothesis_id"])

        elif action_type == "save":
            save_data = SaveData(
                save_id=f"{config['id']}_slot{action.get('slot', 0)}",
                player_state=sm.player_state.model_copy(deep=True),
                event_log=sm.event_log.get_events(),
                seed=seed,
            )
            save_repo.save(save_data, action.get("slot", 0))

        elif action_type == "load":
            save_data = save_repo.load(action.get("slot", 0))
            if save_data is not None:
                sm.player_state = save_data.player_state
                sm.event_log.clear()
                for evt in save_data.event_log:
                    sm.event_log.add_event(evt)

    ending = sm.resolve_ending()
    return {
        "ending_id": ending.ending_id if ending else None,
        "expected_ending_id": expected_ending_id,
        "discovered_clue_ids": set(sm.player_state.discovered_clue_ids),
        "expected_clue_ids": expected_clue_ids,
        "corruption": sm.player_state.corruption_level,
        "expected_corruption_max": expected_corruption_max,
    }


def _get_playthroughs() -> list[tuple[str, Path]]:
    """Return sorted list of (playthrough_id, path) tuples."""
    if not PLAYTHROUGHS_DIR.exists():
        return []
    files = sorted(PLAYTHROUGHS_DIR.glob("*.json"))
    result = []
    for f in files:
        with open(f) as fh:
            config = json.load(fh)
        result.append((config["id"], f))
    return result


class TestPlaythroughAll:
    """Parameterized tests that run every playthrough JSON."""

    @pytest.mark.parametrize(
        "playthrough_id,playthrough_path",
        _get_playthroughs(),
        ids=[p[0] for p in _get_playthroughs()],
    )
    def test_playthrough(self, playthrough_id: str, playthrough_path: Path) -> None:
        result = _run_playthrough(playthrough_path)
        errors: list[str] = []

        if result["expected_ending_id"] and result["ending_id"] != result["expected_ending_id"]:
            errors.append(
                f"Ending mismatch: expected '{result['expected_ending_id']}', "
                f"got '{result['ending_id']}'"
            )

        if result["expected_clue_ids"]:
            missing = result["expected_clue_ids"] - result["discovered_clue_ids"]
            if missing:
                errors.append(f"Missing expected clues ({len(missing)}): {sorted(missing)}")

        if result["corruption"] > result["expected_corruption_max"]:
            errors.append(
                f"Corruption too high: {result['corruption']} > "
                f"{result['expected_corruption_max']}"
            )

        if errors:
            pytest.fail("\n".join(errors))
