"""Tests for AI Gateway data models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_gateway.models import (
    CaseRecapRequest,
    CaseRecapResponse,
    ClassifyIntentRequest,
    ClassifyIntentResponse,
    DialogueAct,
    DialogueRequest,
    DialogueResponse,
    Emotion,
    HealthResponse,
    PromptVersionResponse,
)


class TestDialogueAct:
    def test_enum_values(self):
        assert DialogueAct.ANSWER == "answer"
        assert DialogueAct.ANSWER_PARTIAL == "answer_partial"
        assert DialogueAct.ASK == "ask"
        assert DialogueAct.REFUSE == "refuse"
        assert DialogueAct.EVADE == "evade"
        assert DialogueAct.INSIST == "insist"
        assert DialogueAct.CHANGE_TOPIC == "change_topic"
        assert DialogueAct.GREET == "greet"
        assert DialogueAct.FAREWELL == "farewell"
        assert DialogueAct.FALLBACK == "fallback"

    def test_all_members(self):
        assert len(DialogueAct) == 10


class TestEmotion:
    def test_enum_values(self):
        assert Emotion.NEUTRAL == "neutral"
        assert Emotion.GUARDED == "guarded"
        assert Emotion.FRIENDLY == "friendly"
        assert Emotion.HOSTILE == "hostile"
        assert Emotion.ANXIOUS == "anxious"
        assert Emotion.SAD == "sad"
        assert Emotion.SURPRISED == "surprised"
        assert Emotion.ANGRY == "angry"

    def test_all_members(self):
        assert len(Emotion) == 8


class TestDialogueRequest:
    def test_minimal_creation(self):
        req = DialogueRequest(npc_id="npc_1", player_utterance="Hello")
        assert req.npc_id == "npc_1"
        assert req.player_utterance == "Hello"
        assert req.current_scene_id == ""
        assert req.current_public_event_ids == []
        assert req.player_revealed_claim_ids == []
        assert req.relationship_state == "neutral"
        assert req.emotion_state == "neutral"

    def test_full_creation(self):
        req = DialogueRequest(
            npc_id="npc_2",
            player_utterance="Tell me the truth",
            current_scene_id="loc_workshop",
            current_public_event_ids=["event_1"],
            player_revealed_claim_ids=["claim_1"],
            relationship_state="friendly",
            emotion_state="anxious",
        )
        assert req.npc_id == "npc_2"
        assert req.current_scene_id == "loc_workshop"
        assert req.current_public_event_ids == ["event_1"]
        assert req.player_revealed_claim_ids == ["claim_1"]

    def test_requires_npc_id(self):
        with pytest.raises(ValidationError):
            DialogueRequest(player_utterance="Hello")

    def test_requires_player_utterance(self):
        with pytest.raises(ValidationError):
            DialogueRequest(npc_id="npc_1")


class TestDialogueResponse:
    def test_minimal_creation(self):
        resp = DialogueResponse(utterance="Hello", dialogue_act=DialogueAct.GREET)
        assert resp.utterance == "Hello"
        assert resp.dialogue_act == DialogueAct.GREET
        assert resp.referenced_claim_ids == []
        assert resp.emotion == Emotion.NEUTRAL
        assert resp.animation_tag == ""
        assert resp.requests_world_action is False
        assert resp.safety_flags == []

    def test_requests_world_action_defaults_to_false(self):
        resp = DialogueResponse(utterance="Hi", dialogue_act=DialogueAct.GREET)
        assert resp.requests_world_action is False

    def test_requests_world_action_can_be_set(self):
        resp = DialogueResponse(
            utterance="Hi", dialogue_act=DialogueAct.GREET, requests_world_action=False
        )
        assert resp.requests_world_action is False

    def test_full_creation(self):
        resp = DialogueResponse(
            utterance="I know something",
            dialogue_act=DialogueAct.ANSWER,
            referenced_claim_ids=["claim_1"],
            emotion=Emotion.GUARDED,
            animation_tag="cross_arms",
            requests_world_action=False,
            safety_flags=["possible_leak:fact_secret_1"],
        )
        assert resp.dialogue_act == DialogueAct.ANSWER
        assert resp.referenced_claim_ids == ["claim_1"]
        assert resp.emotion == Emotion.GUARDED
        assert resp.safety_flags == ["possible_leak:fact_secret_1"]

    def test_requires_utterance(self):
        with pytest.raises(ValidationError):
            DialogueResponse(dialogue_act=DialogueAct.GREET)

    def test_requires_dialogue_act(self):
        with pytest.raises(ValidationError):
            DialogueResponse(utterance="Hello")


class TestClassifyIntentRequest:
    def test_minimal_creation(self):
        req = ClassifyIntentRequest(player_utterance="Hello")
        assert req.player_utterance == "Hello"
        assert req.context == ""

    def test_full_creation(self):
        req = ClassifyIntentRequest(player_utterance="What's the secret?", context="suspicious")
        assert req.context == "suspicious"


class TestClassifyIntentResponse:
    def test_defaults(self):
        resp = ClassifyIntentResponse()
        assert resp.intent == "unknown"
        assert resp.confidence == 0.0

    def test_custom_values(self):
        resp = ClassifyIntentResponse(intent="ask_secret", confidence=0.85)
        assert resp.intent == "ask_secret"
        assert resp.confidence == 0.85


class TestCaseRecapRequest:
    def test_minimal_creation(self):
        req = CaseRecapRequest(case_id="case_1")
        assert req.case_id == "case_1"
        assert req.player_events == []
        assert req.discovered_facts == []

    def test_full_creation(self):
        req = CaseRecapRequest(
            case_id="case_1",
            player_events=["event_1", "event_2"],
            discovered_facts=["fact_1"],
        )
        assert req.player_events == ["event_1", "event_2"]
        assert req.discovered_facts == ["fact_1"]


class TestCaseRecapResponse:
    def test_defaults(self):
        resp = CaseRecapResponse()
        assert resp.summary == ""
        assert resp.next_steps == []

    def test_custom_values(self):
        resp = CaseRecapResponse(summary="Done", next_steps=["step_1"])
        assert resp.summary == "Done"
        assert resp.next_steps == ["step_1"]


class TestHealthResponse:
    def test_defaults(self):
        resp = HealthResponse()
        assert resp.status == "ok"
        assert resp.version == "0.1.0"

    def test_custom_values(self):
        resp = HealthResponse(status="degraded", version="0.2.0")
        assert resp.status == "degraded"


class TestPromptVersionResponse:
    def test_defaults(self):
        resp = PromptVersionResponse()
        assert resp.prompt_version == "0.1.0"
        assert resp.model_version == "mock"

    def test_custom_values(self):
        resp = PromptVersionResponse(prompt_version="1.0.0", model_version="gpt-4")
        assert resp.prompt_version == "1.0.0"
        assert resp.model_version == "gpt-4"
