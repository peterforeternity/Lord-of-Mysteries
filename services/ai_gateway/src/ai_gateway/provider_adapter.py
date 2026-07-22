from __future__ import annotations

from typing import Any

from .models import DialogueAct, DialogueRequest, DialogueResponse
from .protocol import ProviderProtocol


class OpenAICompatibleProvider(ProviderProtocol):
    """Adapter for OpenAI-compatible APIs. Never called in tests."""

    def __init__(self, api_key: str = "", base_url: str = "", model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def generate_dialogue(
        self, request: DialogueRequest, context: dict[str, Any]
    ) -> DialogueResponse:
        # Not implemented for testing - returns fallback
        return DialogueResponse(
            utterance="[API adapter not configured]",
            dialogue_act=DialogueAct.FALLBACK,
            requests_world_action=False,
        )

    async def classify_intent(self, player_utterance: str, context: str) -> tuple[str, float]:
        return "unknown", 0.0

    async def generate_recap(
        self, case_id: str, events: list[str], facts: list[str]
    ) -> tuple[str, list[str]]:
        return "Recap not available.", []
