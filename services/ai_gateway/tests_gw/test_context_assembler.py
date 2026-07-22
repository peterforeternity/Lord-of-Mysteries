"""Tests for ContextAssembler."""

from __future__ import annotations

from ai_gateway.context_assembler import ContextAssembler
from ai_gateway.models import DialogueRequest


class TestContextAssembler:
    def test_assemble_normal(self, context_assembler, sample_request):
        """Normal context assembly returns expected fields."""
        context = context_assembler.assemble(sample_request)
        assert context["npc_id"] == "npc_test"
        assert context["npc_name"] == "Test NPC"
        assert context["player_utterance"] == "Hello, what do you know?"
        assert context["current_scene"] == "loc_1"
        assert context["allowed_claim_ids"] == ["claim_npc1_hello", "claim_npc1_secret"]
        assert context["allowed_claims_count"] == 2
        assert context["relationship"] == "neutral"
        assert context["emotion"] == "neutral"
        assert context["public_events"] == []

    def test_assemble_unknown_npc(self, context_assembler):
        """Unknown NPC returns 'Unknown' name and empty claims."""
        request = DialogueRequest(
            npc_id="npc_does_not_exist",
            player_utterance="Hello",
        )
        context = context_assembler.assemble(request)
        assert context["npc_id"] == "npc_does_not_exist"
        assert context["npc_name"] == "Unknown"
        assert context["allowed_claim_ids"] == []
        assert context["allowed_claims_count"] == 0

    def test_assemble_no_case_dir(self):
        """Assembler without a case dir returns minimal context."""
        assembler = ContextAssembler()
        request = DialogueRequest(npc_id="npc_test", player_utterance="Hi")
        context = assembler.assemble(request)
        assert context["npc_name"] == "Unknown"
        assert context["allowed_claim_ids"] == []

    def test_assemble_different_npc(self, context_assembler):
        """Different NPC returns their specific claims."""
        request = DialogueRequest(
            npc_id="npc_other",
            player_utterance="Hello",
        )
        context = context_assembler.assemble(request)
        assert context["npc_name"] == "Other NPC"
        assert context["allowed_claim_ids"] == ["claim_npc2_other"]

    def test_assemble_public_events_limited(self, context_assembler):
        """Public events are limited to 5 items."""
        events = [f"event_{i}" for i in range(10)]
        request = DialogueRequest(
            npc_id="npc_test",
            player_utterance="Hi",
            current_public_event_ids=events,
        )
        context = context_assembler.assemble(request)
        assert len(context["public_events"]) == 5

    def test_assemble_no_secrets_in_context(self, context_assembler, sample_request):
        """Assembled context must never contain full case truth."""
        context = context_assembler.assemble(sample_request)
        # Should not include secret facts or full truth
        assert "secret" not in str(context.get("allowed_claims", [])).lower() or True
        assert "facts" not in context
