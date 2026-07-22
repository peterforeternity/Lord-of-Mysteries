"""Tests for DialoguePromptBuilder."""

from __future__ import annotations

from ai_gateway.models import DialogueRequest


class TestDialoguePromptBuilder:
    def test_build_system_prompt(self, prompt_builder):
        prompt = prompt_builder.build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "NPC" in prompt
        assert "JSON" in prompt

    def test_build_user_prompt(self, prompt_builder, sample_request):
        context = {
            "npc_name": "Test NPC",
            "npc_id": "npc_test",
            "player_utterance": "Hello",
            "current_scene": "loc_1",
            "allowed_claim_ids": ["claim_1", "claim_2"],
            "allowed_claims_count": 2,
            "relationship": "neutral",
            "emotion": "neutral",
            "public_events": [],
        }
        prompt = prompt_builder.build_user_prompt(sample_request, context)
        assert "Test NPC" in prompt
        assert "loc_1" in prompt
        assert "Hello, what do you know?" in prompt
        assert "claim_1, claim_2" in prompt
        assert "neutral" in prompt

    def test_build_user_prompt_minimal_context(self, prompt_builder):
        request = DialogueRequest(
            npc_id="npc_unknown",
            player_utterance="Hi",
        )
        context = {}
        prompt = prompt_builder.build_user_prompt(request, context)
        assert "NPC" in prompt  # default name
        assert "Hi" in prompt
