from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import DialogueRequest


class ContextAssembler:
    """Assembles minimal necessary context for LLM."""

    def __init__(self, case_dir: Path | None = None) -> None:
        self.case_dir = case_dir
        self._claims: list[dict[str, Any]] = []
        self._npcs: list[dict[str, Any]] = []
        if case_dir:
            claims_path = case_dir / "claims.json"
            npcs_path = case_dir / "npcs.json"
            if claims_path.exists():
                with open(claims_path) as f:
                    self._claims = json.load(f)
            if npcs_path.exists():
                with open(npcs_path) as f:
                    self._npcs = json.load(f)

    def assemble(self, request: DialogueRequest) -> dict[str, Any]:
        """Assemble context. Never includes full case truth."""
        npc = next((n for n in self._npcs if n.get("npc_id") == request.npc_id), None)

        # Get NPC's allowed claims
        allowed_claim_ids: list[str] = []
        if npc:
            allowed_claim_ids = npc.get("known_claim_ids", [])

        # Get allowed claims (filtered by whitelist)
        allowed_claims = [c for c in self._claims if c.get("claim_id") in allowed_claim_ids]

        context = {
            "npc_id": request.npc_id,
            "npc_name": npc.get("name", "Unknown") if npc else "Unknown",
            "player_utterance": request.player_utterance,
            "current_scene": request.current_scene_id,
            "allowed_claim_ids": allowed_claim_ids,
            "allowed_claims_count": len(allowed_claims),
            "relationship": request.relationship_state,
            "emotion": request.emotion_state,
            "public_events": request.current_public_event_ids[:5],  # limit
        }

        return context
