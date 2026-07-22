"""Tests for StructuredOutputValidator."""

from __future__ import annotations

import json

from ai_gateway.models import DialogueAct, DialogueResponse


class TestValidate:
    def test_valid_json(self, validator):
        """Valid JSON string that matches DialogueResponse schema."""
        raw = json.dumps(
            {
                "utterance": "Hello there",
                "dialogue_act": "greet",
                "referenced_claim_ids": ["claim_1"],
                "emotion": "neutral",
                "requests_world_action": False,
            }
        )
        result = validator.validate(raw)
        assert isinstance(result, DialogueResponse)
        assert result.utterance == "Hello there"
        assert result.dialogue_act == DialogueAct.GREET
        assert result.requests_world_action is False

    def test_invalid_json_returns_none(self, validator):
        """Malformed JSON string returns None."""
        result = validator.validate("{invalid json}")
        assert result is None

    def test_valid_json_missing_required_field(self, validator):
        """Valid JSON but missing required 'utterance' field."""
        raw = json.dumps({"dialogue_act": "greet"})
        result = validator.validate(raw)
        assert result is None

    def test_valid_json_wrong_enum_value(self, validator):
        """Valid JSON with invalid enum value returns None."""
        raw = json.dumps(
            {
                "utterance": "Hello",
                "dialogue_act": "invalid_act",
            }
        )
        result = validator.validate(raw)
        assert result is None

    def test_empty_string(self, validator):
        result = validator.validate("")
        assert result is None


class TestValidateDict:
    def test_valid_dict(self, validator):
        data = {
            "utterance": "Hello",
            "dialogue_act": "greet",
            "referenced_claim_ids": ["claim_1"],
            "emotion": "neutral",
            "requests_world_action": False,
        }
        result = validator.validate_dict(data)
        assert isinstance(result, DialogueResponse)
        assert result.utterance == "Hello"

    def test_dict_missing_utterance(self, validator):
        data = {"dialogue_act": "greet"}
        result = validator.validate_dict(data)
        assert result is None

    def test_dict_missing_dialogue_act(self, validator):
        data = {"utterance": "Hello"}
        result = validator.validate_dict(data)
        assert result is None

    def test_dict_extra_fields(self, validator):
        """Extra fields should be ignored (pydantic behaviour)."""
        data = {
            "utterance": "Hello",
            "dialogue_act": "greet",
            "extra_field": "should be ignored",
        }
        result = validator.validate_dict(data)
        assert isinstance(result, DialogueResponse)
        assert result.utterance == "Hello"

    def test_dict_empty(self, validator):
        result = validator.validate_dict({})
        assert result is None
