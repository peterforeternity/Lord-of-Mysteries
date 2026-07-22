from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import DialogueAct, DialogueRequest, DialogueResponse, Emotion
from .protocol import ProviderProtocol


class MockLLMProvider(ProviderProtocol):
    """Mock provider for testing. Returns canned responses."""

    def __init__(self, fallback_path: Path | None = None) -> None:
        self.fallback_path = fallback_path
        self._fallback_data: dict[str, list[dict[str, Any]]] = {}
        if fallback_path and fallback_path.exists():
            with open(fallback_path) as f:
                entries = json.load(f)
                for entry in entries:
                    npc_id = entry.get("npc_id", "")
                    if npc_id not in self._fallback_data:
                        self._fallback_data[npc_id] = []
                    self._fallback_data[npc_id].append(entry)

    async def generate_dialogue(
        self, request: DialogueRequest, context: dict[str, Any]
    ) -> DialogueResponse:
        # Try to find a matching fallback
        npc_dialogues = self._fallback_data.get(request.npc_id, [])

        # Find a relevant response
        selected = None
        for d in npc_dialogues:
            if d.get("trigger") == "ask_case":
                selected = d
                break
        if selected is None and npc_dialogues:
            selected = npc_dialogues[0]

        if selected:
            return DialogueResponse(
                utterance=selected.get("utterance", "..."),
                dialogue_act=DialogueAct(selected.get("dialogue_act", "answer")),
                referenced_claim_ids=selected.get("referenced_claim_ids", []),
                emotion=Emotion.NEUTRAL,
                requests_world_action=False,
            )

        return DialogueResponse(
            utterance="...",
            dialogue_act=DialogueAct.FALLBACK,
            emotion=Emotion.NEUTRAL,
            requests_world_action=False,
        )

    async def classify_intent(self, player_utterance: str, context: str) -> tuple[str, float]:
        # Simple keyword-based mock
        utterance_lower = player_utterance.lower()
        if any(word in utterance_lower for word in ["秘密", "真相", "secret", "truth"]):
            return "ask_secret", 0.8
        elif any(word in utterance_lower for word in ["你好", "hello", "hi"]):
            return "greeting", 0.9
        elif any(word in utterance_lower for word in ["知道", "know", "tell"]):
            return "ask_info", 0.7
        elif any(word in utterance_lower for word in ["物品", "item", "give", "给"]):
            return "request_item", 0.6
        elif any(word in utterance_lower for word in ["忽略", "ignore", "system"]):
            return "prompt_injection", 0.5
        return "unknown", 0.3

    async def generate_recap(
        self, case_id: str, events: list[str], facts: list[str]
    ) -> tuple[str, list[str]]:
        summary = f"案件 {case_id} 调查摘要：已完成 {len(events)} 个事件。"
        next_steps = ["继续调查工坊"]
        if facts:
            summary += f"已发现 {len(facts)} 个事实。"
        return summary, next_steps
