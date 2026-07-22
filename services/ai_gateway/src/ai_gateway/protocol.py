from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import DialogueRequest, DialogueResponse


class ProviderProtocol(ABC):
    @abstractmethod
    async def generate_dialogue(
        self, request: DialogueRequest, context: dict[str, Any]
    ) -> DialogueResponse: ...

    @abstractmethod
    async def classify_intent(self, player_utterance: str, context: str) -> tuple[str, float]: ...

    @abstractmethod
    async def generate_recap(
        self, case_id: str, events: list[str], facts: list[str]
    ) -> tuple[str, list[str]]: ...
