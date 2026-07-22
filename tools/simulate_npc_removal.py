"""Simulate NPC removal and check if the case can still be solved.

For each core NPC, simulates that NPC being removed (all their claims
become unavailable) and checks whether at least one hypothesis can still
be achieved.

Usage:
    uv run python tools/simulate_npc_removal.py

Exits with code 0 if the case remains solvable after every individual NPC
removal, 1 if any removal makes the case unsolvable.
"""

import sys
from pathlib import Path

from investigation_core import CaseLoader
from investigation_core.models import PlayerCaseState
from investigation_core.services import HypothesisEvaluationService

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = PROJECT_ROOT / "content" / "cases" / "case_clockmaker_01"


def get_clues_blocked_by_npc_removal(case, npc_id: str) -> set[str]:
    """Return the set of clue_ids that become unavailable because they
    are only revealed through claims made by the given NPC.

    A clue is 'blocked' by an NPC removal if:
      - The clue's source_type is 'npc_statement', AND
      - All facts it reveals are ONLY revealed by clues that come from
        this NPC, OR the clue itself is directly dependent on this NPC's
        claims.

    For simplicity, we consider an NPC's removal to block any clue whose
    reveals_fact_ids includes facts that have no other clue source besides
    clues originating from this NPC.
    """
    # Build a map: fact_id -> set of clue_ids (across ALL NPCs)
    fact_sources: dict[str, set[str]] = {}
    for clue in case.clues:
        for fid in clue.reveals_fact_ids:
            fact_sources.setdefault(fid, set()).add(clue.clue_id)

    # Build a map: npc_id -> set of clue_ids that come from this NPC's
    # claims (clues with source_type='npc_statement')
    npc_clues: dict[str, set[str]] = {}
    clue_npc_map: dict[str, str] = {}
    for npc in case.npcs:
        npc_clues[npc.npc_id] = set()

    # A clue is associated with an NPC if the facts it reveals can only
    # be obtained through that NPC's claims
    for clue in case.clues:
        if clue.source_type.value == "npc_statement":
            # Find which NPC's claims lead to this clue
            # Match by checking if the clue's reveals_fact_ids overlap with
            # the facts that the NPC's claims contribute to
            for npc in case.npcs:
                if npc.npc_id == npc_id:
                    # Simple heuristic: if this npc_statement clue exists
                    # in the same location as the NPC, it's linked
                    if clue.location_id == npc.initial_location_id:
                        npc_clues.setdefault(npc.npc_id, set()).add(clue.clue_id)
                        clue_npc_map[clue.clue_id] = npc.npc_id

    # For the given NPC, find which facts become unreachable because
    # all their clue sources are blocked by this NPC's removal
    removed_clues = npc_clues.get(npc_id, set())

    # Additionally, check which clues are in the same location as the NPC
    # and are npc_statement type
    npc_obj = next((n for n in case.npcs if n.npc_id == npc_id), None)
    if npc_obj:
        for clue in case.clues:
            if (
                clue.source_type.value == "npc_statement"
                and clue.location_id == npc_obj.initial_location_id
            ):
                removed_clues.add(clue.clue_id)

    return removed_clues


def get_blocked_facts(case, removed_clues: set[str]) -> set[str]:
    """Return facts that become undiscoverable because all their clue
    sources are in removed_clues."""
    fact_sources: dict[str, set[str]] = {}
    for clue in case.clues:
        for fid in clue.reveals_fact_ids:
            fact_sources.setdefault(fid, set()).add(clue.clue_id)

    blocked: set[str] = set()
    for fid, sources in fact_sources.items():
        if sources and sources.issubset(removed_clues):
            blocked.add(fid)
    return blocked


def simulate_npc_removal(case, npc_id: str) -> dict:
    """Simulate the case after removing a specific NPC.

    Returns a report dict with:
      - npc_id, npc_name
      - blocked_clues: clues that become unavailable
      - blocked_facts: facts that become undiscoverable
      - solvable_hypotheses: hypotheses that can still be achieved
      - is_solvable: whether at least one hypothesis is achievable
    """
    npc_obj = next((n for n in case.npcs if n.npc_id == npc_id), None)
    npc_name = npc_obj.name if npc_obj else npc_id

    # Determine removed clues: npc_statement clues in the NPC's location
    removed_clues: set[str] = set()
    if npc_obj:
        for clue in case.clues:
            if (
                clue.source_type.value == "npc_statement"
                and clue.location_id == npc_obj.initial_location_id
            ):
                removed_clues.add(clue.clue_id)

    blocked_facts = get_blocked_facts(case, removed_clues)

    # For each hypothesis, check if it can still be submitted
    hypothesis_service = HypothesisEvaluationService()
    solvable: list[str] = []
    unsolvable: list[str] = []

    for hyp in case.hypotheses:
        state = PlayerCaseState(
            case_id=case.case_id,
            current_location_id=case.initial_scene_id,
        )

        # Discover all non-blocked clues
        for cid in hyp.required_clue_ids:
            if cid in removed_clues:
                continue
            clue = next((c for c in case.clues if c.clue_id == cid), None)
            if clue:
                state.discovered_clue_ids.append(cid)
                for fid in clue.reveals_fact_ids:
                    if fid not in state.discovered_fact_ids:
                        state.discovered_fact_ids.append(fid)

        # Ensure required facts are present
        can_meet_requirements = True
        for fid in hyp.required_fact_ids:
            if fid not in state.discovered_fact_ids:
                if fid in blocked_facts:
                    can_meet_requirements = False
                    break

        if not can_meet_requirements:
            unsolvable.append(hyp.hypothesis_id)
            continue

        # Try submitting
        success, _, _ = hypothesis_service.submit_hypothesis(case, state, hyp.hypothesis_id)
        if success:
            solvable.append(hyp.hypothesis_id)
        else:
            unsolvable.append(hyp.hypothesis_id)

    return {
        "npc_id": npc_id,
        "npc_name": npc_name,
        "blocked_clues": sorted(removed_clues),
        "blocked_facts": sorted(blocked_facts),
        "solvable_hypotheses": solvable,
        "unsolvable_hypotheses": unsolvable,
        "is_solvable": len(solvable) > 0,
        "impact_level": ("high" if not solvable else "medium" if unsolvable else "low"),
    }


def main() -> int:
    loader = CaseLoader(CASE_DIR)
    case = loader.load_case()

    core_npcs = [n for n in case.npcs if n.role == "core"]

    print("=" * 60)
    print("  NPC Removal Simulation Report")
    print(f"  Case: {case.title} ({case.case_id})")
    print("=" * 60)

    all_solvable = True

    for npc in core_npcs:
        report = simulate_npc_removal(case, npc.npc_id)

        impact_icons = {"high": "✗", "medium": "⚠", "low": "✓"}
        icon = impact_icons.get(report["impact_level"], "?")

        print(f"\n{icon} NPC: {report['npc_name']} ({report['npc_id']})")
        print(f"   Impact level: {report['impact_level']}")
        print(
            f"   Blocked clues ({len(report['blocked_clues'])}): "
            f"{', '.join(report['blocked_clues']) if report['blocked_clues'] else 'none'}"
        )
        print(
            f"   Blocked facts ({len(report['blocked_facts'])}): "
            f"{', '.join(report['blocked_facts']) if report['blocked_facts'] else 'none'}"
        )

        if report["solvable_hypotheses"]:
            print(f"   Solvable hypotheses: " f"{', '.join(report['solvable_hypotheses'])}")
        else:
            print("   Solvable hypotheses: none")

        if report["unsolvable_hypotheses"]:
            print(f"   Unsolvable hypotheses: " f"{', '.join(report['unsolvable_hypotheses'])}")

        if not report["is_solvable"]:
            all_solvable = False

    # Summary
    print("\n" + "-" * 60)
    if all_solvable:
        print("✓ Case remains solvable after every individual NPC removal.")
    else:
        print("✗ Some NPC removals make the case unsolvable!")

    return 0 if all_solvable else 1


if __name__ == "__main__":
    sys.exit(main())
