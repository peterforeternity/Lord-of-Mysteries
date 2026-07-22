from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class KnowledgeBoundaryFilter:
    """Ensures AI responses only reference NPC's allowed claims."""

    def __init__(self, case_dir: Path | None = None) -> None:
        self.case_dir = case_dir
        self._npcs: list[dict[str, Any]] = []
        if case_dir:
            npcs_path = case_dir / "npcs.json"
            if npcs_path.exists():
                with open(npcs_path) as f:
                    self._npcs = json.load(f)

    def get_allowed_claim_ids(self, npc_id: str) -> list[str]:
        npc = next((n for n in self._npcs if n.get("npc_id") == npc_id), None)
        if npc:
            return list(npc.get("known_claim_ids", []))
        return []

    def filter_referenced_claims(self, npc_id: str, referenced_ids: list[str]) -> list[str]:
        allowed = self.get_allowed_claim_ids(npc_id)
        filtered = [cid for cid in referenced_ids if cid in allowed]
        return filtered
