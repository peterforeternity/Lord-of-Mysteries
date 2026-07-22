from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import DialogueAct, DialogueResponse, Emotion


class FallbackDialogueService:
    """Provides fallback dialogue when AI is unavailable."""

    def __init__(self, fallback_path: Path | None = None) -> None:
        self._data: dict[str, list[dict[str, Any]]] = {}
        if fallback_path and fallback_path.exists():
            with open(fallback_path) as f:
                entries = json.load(f)
                for entry in entries:
                    npc_id = entry.get("npc_id", "")
                    if npc_id not in self._data:
                        self._data[npc_id] = []
                    self._data[npc_id].append(entry)

    def get_fallback(self, npc_id: str, trigger: str = "unknowable") -> DialogueResponse:
        npc_dialogues = self._data.get(npc_id, [])

        # Find matching trigger
        for d in npc_dialogues:
            if d.get("trigger") == trigger:
                return DialogueResponse(
                    utterance=d.get("utterance", "..."),
                    dialogue_act=DialogueAct(d.get("dialogue_act", "fallback")),
                    referenced_claim_ids=d.get("referenced_claim_ids", []),
                    emotion=Emotion.NEUTRAL,
                    requests_world_action=False,
                )

        # Fallback to first available
        if npc_dialogues:
            d = npc_dialogues[0]
            return DialogueResponse(
                utterance=d.get("utterance", "..."),
                dialogue_act=DialogueAct(d.get("dialogue_act", "fallback")),
                referenced_claim_ids=d.get("referenced_claim_ids", []),
                emotion=Emotion.NEUTRAL,
                requests_world_action=False,
            )

        return DialogueResponse(
            utterance="...",
            dialogue_act=DialogueAct.FALLBACK,
            emotion=Emotion.NEUTRAL,
            requests_world_action=False,
        )

    def has_dialogue_for(self, npc_id: str) -> bool:
        return npc_id in self._data
