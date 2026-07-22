"""Validate content data file integrity and consistency.

Usage:
    uv run python tools/validate_content.py

Exits with code 0 if all checks pass, 1 if any check fails.
"""

import json
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = PROJECT_ROOT / "content" / "cases" / "case_clockmaker_01"


# ── Helpers ────────────────────────────────────────────────────────────────
def _load_json(name: str) -> list | dict:
    path = CASE_DIR / name
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _id_set(items: list, id_field: str = "id") -> set[str]:
    return {item[id_field] for item in items}


# ── Checks ─────────────────────────────────────────────────────────────────
errors: list[str] = []


def check_case_id_consistency(
    facts: list, claims: list, clues: list, hypotheses: list, npcs: list, case_data: dict
) -> None:
    expected = case_data["case_id"]
    # Only files with a case_id field are facts, clues, and hypotheses
    for label, items, id_field in [
        ("facts", facts, "fact_id"),
        ("clues", clues, "clue_id"),
        ("hypotheses", hypotheses, "hypothesis_id"),
    ]:
        for item in items:
            if item.get("case_id") != expected:
                errors.append(
                    f"[case_id] {label}:{item[id_field]} has case_id="
                    f"'{item.get('case_id')}', expected '{expected}'"
                )


def check_fact_clue_refs(facts: list, clue_ids: set[str]) -> None:
    for f in facts:
        for cid in f.get("revealed_by_clue_ids", []):
            if cid not in clue_ids:
                errors.append(
                    f"[Fact->Clue] fact '{f['fact_id']}' references " f"unknown clue '{cid}'"
                )


def check_claim_npc_refs(claims: list, npc_ids: set[str]) -> None:
    for c in claims:
        if c.get("speaker_npc_id") not in npc_ids:
            errors.append(
                f"[Claim->NPC] claim '{c['claim_id']}' references "
                f"unknown npc '{c.get('speaker_npc_id')}'"
            )


def check_clue_fact_refs(clues: list, fact_ids: set[str]) -> None:
    for c in clues:
        for fid in c.get("reveals_fact_ids", []):
            if fid not in fact_ids:
                errors.append(
                    f"[Clue->Fact] clue '{c['clue_id']}' references " f"unknown fact '{fid}'"
                )


def check_hypothesis_refs(
    hypotheses: list,
    clue_ids: set[str],
    fact_ids: set[str],
    ending_ids: set[str],
) -> None:
    for h in hypotheses:
        for cid in h.get("required_clue_ids", []):
            if cid not in clue_ids:
                errors.append(
                    f"[Hypothesis->Clue] hypothesis '{h['hypothesis_id']}' "
                    f"references unknown clue '{cid}'"
                )
        for fid in h.get("required_fact_ids", []):
            if fid not in fact_ids:
                errors.append(
                    f"[Hypothesis->Fact] hypothesis '{h['hypothesis_id']}' "
                    f"references unknown fact '{fid}'"
                )
        eid = h.get("leads_to_ending_id", "")
        if eid and eid not in ending_ids:
            errors.append(
                f"[Hypothesis->Ending] hypothesis '{h['hypothesis_id']}' "
                f"references unknown ending '{eid}'"
            )


def check_npc_claim_refs(npcs: list, claim_ids: set[str]) -> None:
    for n in npcs:
        for cid in n.get("known_claim_ids", []):
            if cid not in claim_ids:
                errors.append(
                    f"[NPC->Claim] npc '{n['npc_id']}' known_claim_ids "
                    f"references unknown claim '{cid}'"
                )
        for cid in n.get("lie_claim_ids", []):
            if cid not in claim_ids:
                errors.append(
                    f"[NPC->Claim] npc '{n['npc_id']}' lie_claim_ids "
                    f"references unknown claim '{cid}'"
                )


def check_npc_fact_refs(npcs: list, fact_ids: set[str]) -> None:
    for n in npcs:
        for fid in n.get("forbidden_fact_ids", []):
            if fid not in fact_ids:
                errors.append(
                    f"[NPC->Fact] npc '{n['npc_id']}' forbidden_fact_ids "
                    f"references unknown fact '{fid}'"
                )


def check_ending_hypothesis_refs(endings: list, hypothesis_ids: set[str]) -> None:
    for e in endings:
        hid = e.get("required_hypothesis_id", "")
        if hid and hid not in hypothesis_ids:
            errors.append(
                f"[Ending->Hypothesis] ending '{e['ending_id']}' "
                f"references unknown hypothesis '{hid}'"
            )


def check_fallback_npc_refs(fallback: list, npc_ids: set[str]) -> None:
    for entry in fallback:
        nid = entry.get("npc_id")
        if nid and nid not in npc_ids:
            errors.append(f"[FallbackDialogue->NPC] entry references " f"unknown npc '{nid}'")


def check_npc_lie_in_known(npcs: list) -> None:
    """Ensure every lie_claim_id is also in known_claim_ids."""
    for n in npcs:
        lies = set(n.get("lie_claim_ids", []))
        known = set(n.get("known_claim_ids", []))
        for cid in lies:
            if cid not in known:
                errors.append(
                    f"[NPC] npc '{n['npc_id']}' lie_claim_id '{cid}' " f"is not in known_claim_ids"
                )


def check_hypothesis_required_subsets(hypotheses: list) -> None:
    """Ensure no hypothesis has empty required_clue_ids or required_fact_ids."""
    for h in hypotheses:
        if not h.get("required_clue_ids"):
            errors.append(f"[Hypothesis] '{h['hypothesis_id']}' has empty required_clue_ids")
        if not h.get("required_fact_ids"):
            errors.append(f"[Hypothesis] '{h['hypothesis_id']}' has empty required_fact_ids")


def main() -> int:
    # Load data
    case_data = _load_json("case.json")
    if isinstance(case_data, list):
        case_data = case_data[0]

    facts = _load_json("facts.secret.json")
    claims = _load_json("claims.json")
    clues = _load_json("clues.json")
    hypotheses = _load_json("hypotheses.json")
    npcs = _load_json("npcs.json")

    fallback_path = CASE_DIR / "fallback_dialogue.json"
    fallback = []
    if fallback_path.exists():
        fallback = json.loads(fallback_path.read_text(encoding="utf-8"))

    endings = case_data.get("endings", [])

    # Build ID sets
    fact_ids = _id_set(facts, "fact_id")
    claim_ids = _id_set(claims, "claim_id")
    clue_ids = _id_set(clues, "clue_id")
    hypothesis_ids = _id_set(hypotheses, "hypothesis_id")
    npc_ids = _id_set(npcs, "npc_id")
    ending_ids = _id_set(endings, "ending_id")

    # Run checks
    check_case_id_consistency(facts, claims, clues, hypotheses, npcs, case_data)
    check_fact_clue_refs(facts, clue_ids)
    check_claim_npc_refs(claims, npc_ids)
    check_clue_fact_refs(clues, fact_ids)
    check_hypothesis_refs(hypotheses, clue_ids, fact_ids, ending_ids)
    check_npc_claim_refs(npcs, claim_ids)
    check_npc_fact_refs(npcs, fact_ids)
    check_ending_hypothesis_refs(endings, hypothesis_ids)
    check_fallback_npc_refs(fallback, npc_ids)
    check_npc_lie_in_known(npcs)
    check_hypothesis_required_subsets(hypotheses)

    # Report
    if errors:
        print("✗ Content validation failed:")
        for err in errors:
            print(f"  • {err}")
        return 1

    print("✓ All content validation checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
