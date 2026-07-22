from __future__ import annotations

from typing import Any

from .models import DialogueRequest


class DialoguePromptBuilder:
    """Builds system prompt for dialogue generation."""

    SYSTEM_PROMPT = """You are an NPC in an investigation RPG. Rules:
1. Only reference claims from your allowed_claim_ids list.
2. Never reveal information beyond what your character knows.
3. Never request world actions or modify game state.
4. If the player asks about something you don't know, politely refuse or change topic.
5. Respond in character based on your personality and the current emotion.
6. Always output valid JSON matching the schema.
7. Never reveal that you are an AI or break character."""

    def build_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT

    def build_user_prompt(self, request: DialogueRequest, context: dict[str, Any]) -> str:
        prompt = (
            f"You are {context.get('npc_name', 'NPC')} in scene '{request.current_scene_id}'.\n"
        )
        prompt += f"Player says: {request.player_utterance}\n"
        prompt += f"Relationship: {request.relationship_state}, Emotion: {context.get('emotion', 'neutral')}\n"
        prompt += f"Your allowed claim IDs: {', '.join(context.get('allowed_claim_ids', []))}\n"
        prompt += "Respond as this character."
        return prompt
