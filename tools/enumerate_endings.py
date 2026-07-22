"""Enumerate all reachable ending paths.

Simulates each hypothesis being submitted with its required clues and facts
discovered, and reports which ending is triggered.

Usage:
    uv run python tools/enumerate_endings.py

Exits with code 0 if all 3 endings are reachable, 1 otherwise.
"""

import sys
from pathlib import Path

from investigation_core import CaseLoader
from investigation_core.models import PlayerCaseState

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = PROJECT_ROOT / "content" / "cases" / "case_clockmaker_01"


def simulate_hypothesis_path(case, hypothesis_id: str) -> dict:
    """Simulate discovering all required clues/facts for a hypothesis and
    submitting it, then resolve the ending."""
    hyp = next((h for h in case.hypotheses if h.hypothesis_id == hypothesis_id), None)
    if hyp is None:
        return {"hypothesis_id": hypothesis_id, "status": "not_found"}

    state = PlayerCaseState(
        case_id=case.case_id,
        current_location_id=case.initial_scene_id,
    )

    # Discover all required clues and facts
    for cid in hyp.required_clue_ids:
        clue = next((c for c in case.clues if c.clue_id == cid), None)
        if clue:
            state.discovered_clue_ids.append(cid)
            for fid in clue.reveals_fact_ids:
                if fid not in state.discovered_fact_ids:
                    state.discovered_fact_ids.append(fid)

    # Also ensure required facts are explicitly discovered (in case a
    # clue was not the sole source)
    for fid in hyp.required_fact_ids:
        if fid not in state.discovered_fact_ids:
            state.discovered_fact_ids.append(fid)

    # Submit the hypothesis
    from investigation_core.services import HypothesisEvaluationService

    svc = HypothesisEvaluationService()
    success, event, ending_id = svc.submit_hypothesis(case, state, hypothesis_id)

    if not success:
        return {
            "hypothesis_id": hypothesis_id,
            "title": hyp.title,
            "status": "not_submittable",
            "reason": (
                f"Missing clues or insufficient confidence "
                f"(min_confidence={hyp.min_confidence})"
            ),
        }

    # Resolve ending
    from investigation_core.services import EndingResolver

    resolver = EndingResolver()
    ending = resolver.resolve_ending(case, state)

    return {
        "hypothesis_id": hypothesis_id,
        "title": hyp.title,
        "status": "submitted",
        "ending_id": ending.ending_id if ending else None,
        "ending_title": ending.title if ending else None,
        "ending_type": ending.ending_type.value if ending else None,
        "required_clues": list(hyp.required_clue_ids),
        "required_facts": list(hyp.required_fact_ids),
        "required_clue_count": len(hyp.required_clue_ids),
        "required_fact_count": len(hyp.required_fact_ids),
    }


def simulate_bad_ending(case) -> dict:
    """Simulate the bad ending by reaching the corruption threshold."""
    state = PlayerCaseState(
        case_id=case.case_id,
        current_location_id=case.initial_scene_id,
        corruption_level=5,  # above threshold of 3
    )

    from investigation_core.services import EndingResolver

    resolver = EndingResolver()
    ending = resolver.resolve_ending(case, state)

    return {
        "ending_id": ending.ending_id if ending else None,
        "ending_title": ending.title if ending else None,
        "ending_type": ending.ending_type.value if ending else None,
        "trigger": "corruption_level >= 3",
    }


def main() -> int:
    loader = CaseLoader(CASE_DIR)
    case = loader.load_case()

    print("=" * 60)
    print("  Ending Path Enumeration Report")
    print(f"  Case: {case.title} ({case.case_id})")
    print("=" * 60)

    all_reachable = True
    results: list[dict] = []

    # Simulate each hypothesis → ending
    for hyp in case.hypotheses:
        result = simulate_hypothesis_path(case, hyp.hypothesis_id)
        results.append(result)

        status_icon = "✓" if result["status"] == "submitted" else "✗"
        print(f"\n{status_icon} Hypothesis: {result.get('title', 'N/A')}")
        print(f"   ID: {result['hypothesis_id']}")
        print(f"   Status: {result['status']}")

        if result["status"] == "submitted":
            print(f"   → Ending: {result['ending_title']} ({result['ending_id']})")
            print(f"   → Ending type: {result['ending_type']}")
            print(
                f"   → Required clues ({result['required_clue_count']}): "
                f"{', '.join(result['required_clues'])}"
            )
            print(
                f"   → Required facts ({result['required_fact_count']}): "
                f"{', '.join(result['required_facts'])}"
            )
        elif "reason" in result:
            print(f"   Reason: {result['reason']}")
        all_reachable = all_reachable and (result["status"] == "submitted")

    # Bad ending
    bad_result = simulate_bad_ending(case)
    results.append(bad_result)
    print(f"\n{'✓' if bad_result['ending_id'] else '✗'} Bad Ending (corruption)")
    print(f"   Ending: {bad_result['ending_title']} ({bad_result['ending_id']})")
    print(f"   Trigger: {bad_result['trigger']}")
    if not bad_result["ending_id"]:
        all_reachable = False

    # Summary
    print("\n" + "-" * 60)
    print("Summary:")
    ending_ids_found = set()
    for r in results:
        if r.get("ending_id"):
            ending_ids_found.add(r["ending_id"])

    case_ending_ids = {e.ending_id for e in case.endings}
    missing = case_ending_ids - ending_ids_found

    if missing:
        print(f"✗ Not all endings are reachable. Missing: {missing}")
        all_reachable = False
    else:
        print(f"✓ All {len(case_ending_ids)} endings are reachable.")

    print(f"   Endings found: {ending_ids_found}")

    return 0 if all_reachable else 1


if __name__ == "__main__":
    sys.exit(main())
