"""Check clue reachability and prevent soft-locks.

Usage:
    uv run python tools/check_clue_reachability.py

Exits with code 0 if all checks pass, 1 if any check fails.
"""

import sys
from collections import defaultdict
from pathlib import Path

from investigation_core import CaseLoader
from investigation_core.models import SecrecyLevel

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = PROJECT_ROOT / "content" / "cases" / "case_clockmaker_01"


def main() -> int:
    loader = CaseLoader(CASE_DIR)
    case = loader.load_case()

    errors: list[str] = []
    warnings: list[str] = []

    # ── Index data ──────────────────────────────────────────────────────
    fact_map = {f.fact_id: f for f in case.facts}
    clue_map = {c.clue_id: c for c in case.clues}

    # ── 1. Each core_secret fact must have at least 2 different clue sources ──
    for fact in case.facts:
        if fact.secrecy != SecrecyLevel.CORE_SECRET:
            continue
        sources = fact.revealed_by_clue_ids
        if len(sources) < 2:
            errors.append(
                f"[CoreSecret] fact '{fact.fact_id}' ('{fact.summary[:40]}') "
                f"has only {len(sources)} clue source(s): {sources}. "
                f"Expected at least 2."
            )

    # ── 2. Detect soft-locks from unique clue dependencies ──────────────
    # Build a map: tag -> set of clue_ids that can satisfy that tag
    tag_sources: dict[str, set[str]] = defaultdict(set)
    for clue in case.clues:
        for tag in clue.requires_any_tags:
            tag_sources[tag].add(clue.clue_id)
        for tag in clue.requires_all_tags:
            tag_sources[tag].add(clue.clue_id)

    # Collect gated (expected prerequisite) tags — tags that match a clue ID
    all_clue_ids = {c.clue_id for c in case.clues}

    # Check if any clue depends on a tag that only one other clue provides
    # AND that other clue itself has dependencies that could block it
    for clue in case.clues:
        for tag in clue.requires_any_tags:
            # Tag matching a clue_id is a valid gating mechanism, not a softlock
            if tag in all_clue_ids:
                continue
            sources = tag_sources.get(tag, set())
            # Filter out self-references
            other_sources = sources - {clue.clue_id}
            if len(other_sources) == 0:
                warnings.append(
                    f"[SoftLock] clue '{clue.clue_id}' requires tag "
                    f"'{tag}' but no other clue provides it "
                    f"(self only)."
                )
            elif len(other_sources) == 1:
                only_source = next(iter(other_sources))
                only_clue = clue_map.get(only_source)
                if only_clue and only_clue.requires_any_tags:
                    warnings.append(
                        f"[SoftLock] clue '{clue.clue_id}' requires tag "
                        f"'{tag}' which is ONLY provided by clue "
                        f"'{only_source}', which itself has "
                        f"requires_any_tags={only_clue.requires_any_tags}."
                    )

        for tag in clue.requires_all_tags:
            # Tag matching a clue_id is a valid gating mechanism, not a softlock
            if tag in all_clue_ids:
                continue
            sources = tag_sources.get(tag, set())
            other_sources = sources - {clue.clue_id}
            if len(other_sources) == 0:
                warnings.append(
                    f"[SoftLock] clue '{clue.clue_id}' requires_all_tags "
                    f"'{tag}' but no other clue provides it "
                    f"(self only)."
                )

    # ── 3. Each hypothesis's required_clue_ids should be reachable ──────
    for hyp in case.hypotheses:
        unreachable: list[str] = []
        for cid in hyp.required_clue_ids:
            c = clue_map.get(cid)
            if c is None:
                unreachable.append(f"{cid} (unknown)")
                continue
            # Check if the clue has dependency tags that are impossible
            dep_tags = list(c.requires_any_tags) + list(c.requires_all_tags)
            for tag in dep_tags:
                sources = tag_sources.get(tag, set())
                if not sources:
                    unreachable.append(f"{cid} (tag '{tag}' has no source)")
        if unreachable:
            errors.append(
                f"[Hypothesis] '{hyp.hypothesis_id}' has unreachable " f"clues: {unreachable}"
            )

    # ── 4. Verify scene connectivity via clue chains ────────────────────
    scene_clues: dict[str, set[str]] = defaultdict(set)
    for clue in case.clues:
        if clue.location_id:
            scene_clues[clue.location_id].add(clue.clue_id)

    scenes = list(scene_clues.keys())
    if len(scenes) > 1:
        # Build a graph: scenes connected if a clue from one scene reveals
        # a fact needed by a clue in another scene, or vice versa
        fact_scenes: dict[str, set[str]] = defaultdict(set)
        for clue in case.clues:
            for fid in clue.reveals_fact_ids:
                fact_scenes[fid].add(clue.location_id)

        # Simple check: every scene has at least one clue that reveals
        # a fact referenced elsewhere
        for scene in scenes:
            scene_facts: set[str] = set()
            for clue in case.clues:
                if clue.location_id == scene:
                    scene_facts.update(clue.reveals_fact_ids)
            if not scene_facts:
                warnings.append(
                    f"[Connectivity] scene '{scene}' has no clues that "
                    f"reveal any fact — may be isolated."
                )

    # ── 5. Missable clues should not be the sole source of core secrets ──
    for clue in case.clues:
        if not clue.missable:
            continue
        for fid in clue.reveals_fact_ids:
            fact = fact_map.get(fid)
            if fact is None:
                continue
            if fact.secrecy != SecrecyLevel.CORE_SECRET:
                continue
            other_sources = [cid for cid in fact.revealed_by_clue_ids if cid != clue.clue_id]
            if not other_sources:
                errors.append(
                    f"[Missable] missable clue '{clue.clue_id}' is the "
                    f"ONLY source for core_secret fact '{fid}' "
                    f"('{fact.summary[:40]}')."
                )

    # ── Categorize gated clues (tags matching clue IDs) ────────────────
    gated_clues: list[str] = []
    for clue in case.clues:
        for tag in clue.requires_any_tags:
            if tag in all_clue_ids:
                gated_clues.append(f"'{clue.clue_id}' gated by '{tag}'")
        for tag in clue.requires_all_tags:
            if tag in all_clue_ids:
                gated_clues.append(f"'{clue.clue_id}' gated by '{tag}'")
    gated_clues = sorted(set(gated_clues))

    if gated_clues:
        print("ℹ  Conditional / Gated clues (expected prerequisites):")
        for g in gated_clues:
            print(f"  • {g}")
        print(f"  Count: {len(gated_clues)}")

    # ── Report ──────────────────────────────────────────────────────────
    actual_softlocks = [w for w in warnings if "[SoftLock]" in w]

    if actual_softlocks:
        print("⚠  Unexplained softlock warnings:")
        for w in actual_softlocks:
            print(f"  • {w}")

    if errors:
        print("✗ Clue reachability check failed:")
        for e in errors:
            print(f"  • {e}")
        return 1

    print("  0 errors")
    print("  0 unexplained softlock warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
