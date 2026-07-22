"""Scripted playthrough system for investigation RPG.

Usage:
    uv run python tools/run_playthrough.py <path_to_playthrough.json>
    uv run python tools/run_playthrough.py --all

Exits with code 0 if expected ending matches, 1 otherwise.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from investigation_core import CaseLoader, CaseStateMachine, SaveRepository
from investigation_core.models import SaveData

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = PROJECT_ROOT / "content" / "cases" / "case_clockmaker_01"
PLAYTHROUGHS_DIR = CASE_DIR / "playthroughs"


def run_playthrough(playthrough_path: Path) -> int:
    """Run a single playthrough and return exit code (0 = pass, 1 = fail)."""
    with open(playthrough_path) as f:
        config = json.load(f)

    playthrough_id = config["id"]
    seed = config.get("seed", 0)
    actions = config["actions"]
    expected_ending_id = config.get("expected_ending_id", "")
    expected_clue_ids = set(config.get("expected_clue_ids", []))
    expected_corruption_max = config.get("expected_corruption_max", 999)

    print(f"\n{'='*60}")
    print(f"Playthrough: {playthrough_id}")
    print(f"  Description: {config.get('description', '')}")
    print(f"{'='*60}")

    # ── Load case and initialize state machine ──────────────────────
    loader = CaseLoader(CASE_DIR)
    case = loader.load_case()
    sm = CaseStateMachine(case)
    sm.player_state.seed = seed

    # Holds save/load data
    save_dir = Path(tempfile.mkdtemp(prefix=f"save_{playthrough_id}_"))
    save_repo = SaveRepository(save_dir)
    saves: dict[int, SaveData] = {}

    # ── Execute actions ─────────────────────────────────────────────
    action_index = 0
    for action in actions:
        action_type = action["action"]
        action_index += 1
        print(f"\n  [{action_index}] {action_type} → ", end="")

        if action_type == "travel":
            location_id = action["location_id"]
            sm.move_to_location(location_id)
            print(f"moved to '{location_id}'")

        elif action_type == "inspect":
            clue_id = action["clue_id"]
            success, event = sm.discover_clue(clue_id)
            if success:
                clue_name = _clue_name(case, clue_id)
                print(f"discovered '{clue_id}' ({clue_name})")
            else:
                _print_warning(f"FAILED to discover '{clue_id}'")

        elif action_type == "talk":
            claim_ids = action.get("claim_ids", [])
            for cid in claim_ids:
                if cid not in sm.player_state.revealed_claim_ids:
                    sm.player_state.revealed_claim_ids.append(cid)
            print(f"revealed claims: {claim_ids}")

        elif action_type == "use_ability":
            event_id = action["event"]
            if event_id not in sm.player_state.completed_events:
                sm.player_state.completed_events.append(event_id)
            print(f"completed event '{event_id}'")

        elif action_type == "perform_divination":
            question = action.get("question", "")
            div_seed = action.get("seed", seed)
            result = sm.perform_divination(question, div_seed)
            print(
                f"divination: tendency='{result.tendency}', "
                f"confidence={result.confidence}, "
                f"cost={result.cost}"
            )

        elif action_type == "perform_ritual":
            ritual_id = action["ritual_id"]
            materials = action.get("materials", [])
            ritual_seed = action.get("seed", seed)
            success, message, corruption_change = sm.perform_ritual(
                ritual_id, materials, ritual_seed
            )
            status = "SUCCESS" if success else "FAILED"
            print(
                f"ritual '{ritual_id}': {status}, "
                f"corruption_change={corruption_change}, "
                f"msg='{message}'"
            )

        elif action_type == "submit_hypothesis":
            hypothesis_id = action["hypothesis_id"]
            success, event, ending_id = sm.submit_hypothesis(hypothesis_id)
            if success:
                hyp_title = _hyp_title(case, hypothesis_id)
                print(f"submitted '{hypothesis_id}' ({hyp_title}) → " f"ending='{ending_id}'")
            else:
                _print_warning(
                    f"FAILED to submit '{hypothesis_id}' "
                    f"(missing clues/facts or contradictions)"
                )

        elif action_type == "save":
            slot = action.get("slot", 0)
            save_data = SaveData(
                save_id=f"{playthrough_id}_slot{slot}",
                player_state=sm.player_state.model_copy(deep=True),
                event_log=sm.event_log.get_events(),
                seed=seed,
            )
            save_repo.save(save_data, slot)
            saves[slot] = save_data
            print(f"saved to slot {slot}")

        elif action_type == "load":
            slot = action.get("slot", 0)
            save_data = save_repo.load(slot)
            if save_data is None:
                _print_warning(f"no save found in slot {slot}")
                continue
            sm.player_state = save_data.player_state
            sm.event_log.clear()
            for evt in save_data.event_log:
                sm.event_log.add_event(evt)
            print(f"loaded from slot {slot}")

        else:
            _print_warning(f"unknown action type '{action_type}'")
            continue

    # ── Resolve ending ──────────────────────────────────────────────
    print(f"\n  {'─'*40}")
    ending = sm.resolve_ending()
    final_ending_id = ending.ending_id if ending else None
    print(f"  Final ending: {final_ending_id}")
    if ending:
        print(f"  Title: {ending.title}")
        print(f"  Type: {ending.ending_type.value}")

    # ── Report state ────────────────────────────────────────────────
    discovered_clues = sorted(sm.player_state.discovered_clue_ids)
    corruption = sm.player_state.corruption_level
    spirituality = sm.player_state.spirituality
    print(f"  Discovered clues ({len(discovered_clues)}): {discovered_clues}")
    print(f"  Corruption: {corruption}")
    print(f"  Spirituality: {spirituality}")

    event_count = sm.event_log.get_event_count()
    print(f"  Events logged: {event_count}")

    # ── Verify expectations ─────────────────────────────────────────
    errors: list[str] = []

    if expected_ending_id and final_ending_id != expected_ending_id:
        errors.append(
            f"Ending mismatch: expected '{expected_ending_id}', " f"got '{final_ending_id}'"
        )

    if expected_clue_ids:
        missing = expected_clue_ids - set(sm.player_state.discovered_clue_ids)
        if missing:
            errors.append(f"Missing expected clues ({len(missing)}): {sorted(missing)}")

    if corruption > expected_corruption_max:
        errors.append(f"Corruption too high: {corruption} > {expected_corruption_max}")

    if errors:
        print("\n  ❌ FAILED:")
        for e in errors:
            print(f"    • {e}")
        return 1

    print("\n  ✅ PASSED")
    return 0


def _clue_name(case, clue_id: str) -> str:
    for c in case.clues:
        if c.clue_id == clue_id:
            return c.display_name
    return ""


def _hyp_title(case, hypothesis_id: str) -> str:
    for h in case.hypotheses:
        if h.hypothesis_id == hypothesis_id:
            return h.title
    return ""


def _print_warning(msg: str) -> None:
    print(f"⚠  {msg}")


def main() -> int:
    args = sys.argv[1:]

    if not args:
        print(f"Usage: uv run python {__file__} <playthrough.json> | --all")
        return 1

    if args[0] == "--all":
        playthrough_files = sorted(PLAYTHROUGHS_DIR.glob("*.json"))
        if not playthrough_files:
            print(f"No playthrough JSON files found in {PLAYTHROUGHS_DIR}")
            return 1
        print(f"Running all {len(playthrough_files)} playthroughs...")
        failures = 0
        for pf in playthrough_files:
            result = run_playthrough(pf)
            if result != 0:
                failures += 1
        total = len(playthrough_files)
        passed = total - failures
        print(f"\n{'='*60}")
        print(f"Results: {passed}/{total} passed")
        if failures:
            print(f"  {failures} playthrough(s) FAILED")
            return 1
        return 0

    playthrough_path = Path(args[0])
    if not playthrough_path.exists():
        print(f"Playthrough file not found: {playthrough_path}")
        return 1

    return run_playthrough(playthrough_path)


if __name__ == "__main__":
    sys.exit(main())
