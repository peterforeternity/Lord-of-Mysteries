"""Tests for FallbackDialogueService."""

from __future__ import annotations

from ai_gateway.fallback import FallbackDialogueService
from ai_gateway.models import DialogueAct, Emotion


class TestGetFallback:
    def test_known_npc_known_trigger(self, fallback_service):
        """Known NPC with known trigger returns matching fallback."""
        response = fallback_service.get_fallback("npc_test", "greeting")
        assert response.utterance == "Hello there."
        assert response.dialogue_act == DialogueAct("greet")
        assert response.referenced_claim_ids == ["claim_npc1_hello"]
        assert response.emotion == Emotion.NEUTRAL
        assert response.requests_world_action is False

    def test_known_npc_unknown_trigger_falls_back_to_first(self, fallback_service):
        """Unknown trigger falls back to first available dialogue for NPC."""
        response = fallback_service.get_fallback("npc_test", "nonexistent_trigger")
        # Should return the first entry for npc_test
        assert response.utterance == "Hello there."

    def test_known_npc_unknowable_trigger(self, fallback_service):
        response = fallback_service.get_fallback("npc_test", "unknowable")
        assert response.utterance == "I don't know about that."
        assert response.dialogue_act == DialogueAct.REFUSE

    def test_unknown_npc_returns_empty_response(self, fallback_service):
        """Unknown NPC returns minimal fallback response."""
        response = fallback_service.get_fallback("npc_nonexistent", "greeting")
        assert response.utterance == "..."
        assert response.dialogue_act == DialogueAct.FALLBACK
        assert response.requests_world_action is False

    def test_empty_npc_id(self, fallback_service):
        response = fallback_service.get_fallback("", "greeting")
        assert response.utterance == "..."
        assert response.dialogue_act == DialogueAct.FALLBACK


class TestHasDialogueFor:
    def test_known_npc(self, fallback_service):
        assert fallback_service.has_dialogue_for("npc_test") is True

    def test_unknown_npc(self, fallback_service):
        assert fallback_service.has_dialogue_for("npc_nonexistent") is False

    def test_empty_npc_id(self, fallback_service):
        assert fallback_service.has_dialogue_for("") is False


class TestNoFile:
    def test_no_fallback_file(self, temp_dir):
        """Service without a file returns empty response for any NPC."""
        service = FallbackDialogueService(temp_dir / "nonexistent.json")
        response = service.get_fallback("npc_test", "greeting")
        assert response.utterance == "..."
        assert response.dialogue_act == DialogueAct.FALLBACK
        assert service.has_dialogue_for("npc_test") is False
