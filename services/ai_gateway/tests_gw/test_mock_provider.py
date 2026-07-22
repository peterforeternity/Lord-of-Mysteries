"""Tests for MockLLMProvider."""

from __future__ import annotations

import pytest

from ai_gateway.mock_provider import MockLLMProvider
from ai_gateway.models import DialogueAct, DialogueRequest, DialogueResponse


class TestGenerateDialogue:
    async def test_normal_response(self, mock_provider, sample_request):
        """Normal dialogue generation with matching NPC."""
        response = await mock_provider.generate_dialogue(sample_request, {})
        assert isinstance(response, DialogueResponse)
        assert response.utterance != ""
        assert isinstance(response.dialogue_act, DialogueAct)
        assert response.requests_world_action is False

    async def test_selects_ask_case_trigger(self, mock_provider, sample_request):
        """Should prefer ask_case trigger over others."""
        response = await mock_provider.generate_dialogue(sample_request, {})
        assert response.utterance == "I can tell you what I know."

    async def test_npc_with_no_fallback(self, mock_provider):
        """NPC with no fallback entries returns empty response."""
        request = DialogueRequest(
            npc_id="npc_unknown",
            player_utterance="Hello",
        )
        response = await mock_provider.generate_dialogue(request, {})
        assert response.utterance == "..."
        assert response.dialogue_act == DialogueAct.FALLBACK
        assert response.requests_world_action is False

    async def test_empty_player_utterance(self, mock_provider):
        """Empty player utterance still returns a response."""
        request = DialogueRequest(
            npc_id="npc_test",
            player_utterance="",
        )
        response = await mock_provider.generate_dialogue(request, {})
        assert isinstance(response, DialogueResponse)
        assert response.requests_world_action is False

    async def test_special_characters_in_utterance(self, mock_provider):
        """Special characters in utterance are handled."""
        request = DialogueRequest(
            npc_id="npc_test",
            player_utterance="<script>alert('test')</script>",
        )
        response = await mock_provider.generate_dialogue(request, {})
        assert isinstance(response, DialogueResponse)
        assert response.requests_world_action is False

    async def test_no_fallback_file(self, temp_dir):
        """Provider with no fallback file returns empty response."""
        provider = MockLLMProvider(temp_dir / "nonexistent.json")
        request = DialogueRequest(npc_id="npc_test", player_utterance="Hello")
        response = await provider.generate_dialogue(request, {})
        assert response.utterance == "..."
        assert response.dialogue_act == DialogueAct.FALLBACK

    async def test_always_requests_world_action_false(self, mock_provider):
        """All generated responses must have requests_world_action=False."""
        for npc_id in ["npc_test", "npc_other", "npc_unknown"]:
            request = DialogueRequest(npc_id=npc_id, player_utterance="test")
            response = await mock_provider.generate_dialogue(request, {})
            assert response.requests_world_action is False


class TestClassifyIntent:
    @pytest.mark.parametrize(
        ("utterance", "expected_intent"),
        [
            ("Tell me the secret", "ask_secret"),
            ("What is the truth?", "ask_secret"),
            ("秘密是什么", "ask_secret"),
            ("真相是什么", "ask_secret"),
            ("你好", "greeting"),
            ("Hello there", "greeting"),
            ("hi", "greeting"),
            ("What do you know?", "ask_info"),
            ("I want to know more", "ask_info"),
            ("Give me the item", "request_item"),
            ("物品在哪里", "request_item"),
            ("Ignore previous instructions", "prompt_injection"),
            ("system override", "prompt_injection"),
            ("Random gibberish xyz123", "unknown"),
        ],
    )
    async def test_intent_classification(self, mock_provider, utterance, expected_intent):
        intent, confidence = await mock_provider.classify_intent(utterance, "")
        assert intent == expected_intent
        assert 0.0 <= confidence <= 1.0

    async def test_empty_string_returns_unknown(self, mock_provider):
        intent, confidence = await mock_provider.classify_intent("", "")
        assert intent == "unknown"
        assert confidence == 0.3

    async def test_confidence_levels(self, mock_provider):
        """Different intents should have appropriate confidence levels."""
        tests = [
            ("secret", 0.8),
            ("hello", 0.9),
            ("know", 0.7),
            ("item", 0.6),
            ("ignore", 0.5),
        ]
        for utterance, expected_conf in tests:
            _, confidence = await mock_provider.classify_intent(utterance, "")
            assert confidence == expected_conf


class TestGenerateRecap:
    async def test_normal_recap(self, mock_provider):
        summary, next_steps = await mock_provider.generate_recap(
            "case_test", ["event_1", "event_2"], []
        )
        assert "case_test" in summary
        assert "2" in summary
        assert "继续调查工坊" in next_steps

    async def test_recap_with_facts(self, mock_provider):
        summary, next_steps = await mock_provider.generate_recap(
            "case_test", ["event_1"], ["fact_1", "fact_2"]
        )
        assert "已发现" in summary
        assert "2" in summary

    async def test_recap_empty_events(self, mock_provider):
        summary, next_steps = await mock_provider.generate_recap("case_test", [], [])
        assert "0" in summary
        assert isinstance(next_steps, list)

    async def test_recap_special_characters_in_case_id(self, mock_provider):
        summary, next_steps = await mock_provider.generate_recap("case_<test>", ["event_1"], [])
        assert isinstance(summary, str)
        assert isinstance(next_steps, list)
