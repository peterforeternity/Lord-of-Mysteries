"""Tests for KnowledgeBoundaryFilter."""

from __future__ import annotations

from ai_gateway.knowledge_boundary import KnowledgeBoundaryFilter


class TestGetAllowedClaimIds:
    def test_known_npc_returns_claims(self, knowledge_filter):
        ids = knowledge_filter.get_allowed_claim_ids("npc_test")
        assert ids == ["claim_npc1_hello", "claim_npc1_secret"]

    def test_other_npc_returns_claims(self, knowledge_filter):
        ids = knowledge_filter.get_allowed_claim_ids("npc_other")
        assert ids == ["claim_npc2_other"]

    def test_unknown_npc_returns_empty(self, knowledge_filter):
        ids = knowledge_filter.get_allowed_claim_ids("npc_does_not_exist")
        assert ids == []

    def test_empty_npc_id(self, knowledge_filter):
        ids = knowledge_filter.get_allowed_claim_ids("")
        assert ids == []


class TestFilterReferencedClaims:
    def test_all_allowed(self, knowledge_filter):
        result = knowledge_filter.filter_referenced_claims(
            "npc_test", ["claim_npc1_hello", "claim_npc1_secret"]
        )
        assert result == ["claim_npc1_hello", "claim_npc1_secret"]

    def test_partial_allowed(self, knowledge_filter):
        result = knowledge_filter.filter_referenced_claims(
            "npc_test", ["claim_npc1_hello", "claim_npc2_other"]
        )
        assert result == ["claim_npc1_hello"]

    def test_none_allowed(self, knowledge_filter):
        result = knowledge_filter.filter_referenced_claims(
            "npc_test", ["claim_npc2_other", "claim_nonexistent"]
        )
        assert result == []

    def test_empty_referenced_ids(self, knowledge_filter):
        result = knowledge_filter.filter_referenced_claims("npc_test", [])
        assert result == []

    def test_unknown_npc_all_ids_filtered(self, knowledge_filter):
        """Unknown NPC has no allowed claims, so all referenced IDs are filtered."""
        result = knowledge_filter.filter_referenced_claims("npc_unknown", ["claim_npc1_hello"])
        assert result == []

    def test_no_case_dir(self):
        """Filter without case dir returns empty for all."""
        kf = KnowledgeBoundaryFilter()
        result = kf.filter_referenced_claims("npc_test", ["claim_npc1_hello"])
        assert result == []
