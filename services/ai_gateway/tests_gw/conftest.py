"""Test fixtures for AI Gateway tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from ai_gateway.context_assembler import ContextAssembler
from ai_gateway.fact_leak import FactLeakValidator
from ai_gateway.fallback import FallbackDialogueService
from ai_gateway.knowledge_boundary import KnowledgeBoundaryFilter
from ai_gateway.metrics import RequestMetrics
from ai_gateway.mock_provider import MockLLMProvider
from ai_gateway.models import (
    CaseRecapRequest,
    ClassifyIntentRequest,
    DialogueRequest,
)
from ai_gateway.prompt_builder import DialoguePromptBuilder
from ai_gateway.prompt_registry import PromptVersionRegistry
from ai_gateway.validator import StructuredOutputValidator

# ---------------------------------------------------------------------------
# Temporary directory and mock data
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def case_data_dir(temp_dir):
    """Create mock case data directory with all required JSON files."""
    case_dir = temp_dir / "case_test"
    case_dir.mkdir(parents=True)

    # facts.secret.json
    facts = [
        {
            "fact_id": "fact_secret_1",
            "case_id": "test",
            "summary": "Core secret",
            "truth": True,
            "secrecy": "core_secret",
            "revealed_by_clue_ids": ["clue_a"],
        },
        {
            "fact_id": "fact_normal_1",
            "case_id": "test",
            "summary": "Normal fact",
            "truth": True,
            "secrecy": "public",
            "revealed_by_clue_ids": [],
        },
    ]
    with open(case_dir / "facts.secret.json", "w") as f:
        json.dump(facts, f, indent=2)

    # claims.json
    claims = [
        {
            "claim_id": "claim_npc1_hello",
            "speaker_npc_id": "npc_test",
            "content": "NPC says hello",
            "truth_status": "true",
            "speaker_believes_it": True,
        },
        {
            "claim_id": "claim_npc1_secret",
            "speaker_npc_id": "npc_test",
            "content": "NPC knows a secret",
            "truth_status": "partial",
            "speaker_believes_it": True,
        },
        {
            "claim_id": "claim_npc2_other",
            "speaker_npc_id": "npc_other",
            "content": "Other NPC info",
            "truth_status": "true",
            "speaker_believes_it": True,
        },
    ]
    with open(case_dir / "claims.json", "w") as f:
        json.dump(claims, f, indent=2)

    # npcs.json
    npcs = [
        {
            "npc_id": "npc_test",
            "name": "Test NPC",
            "description": "A test NPC",
            "role": "core",
            "known_claim_ids": ["claim_npc1_hello", "claim_npc1_secret"],
            "lie_claim_ids": [],
            "forbidden_fact_ids": ["fact_secret_1"],
            "personality": {"formality": 0.5, "anxiety": 0.3, "aggression": 0.2},
            "initial_location_id": "loc_1",
        },
        {
            "npc_id": "npc_other",
            "name": "Other NPC",
            "description": "Another NPC",
            "role": "core",
            "known_claim_ids": ["claim_npc2_other"],
            "lie_claim_ids": [],
            "forbidden_fact_ids": [],
            "personality": {"formality": 0.7, "anxiety": 0.2, "aggression": 0.1},
            "initial_location_id": "loc_2",
        },
    ]
    with open(case_dir / "npcs.json", "w") as f:
        json.dump(npcs, f, indent=2)

    # fallback_dialogue.json
    fallback = [
        {
            "npc_id": "npc_test",
            "trigger": "greeting",
            "utterance": "Hello there.",
            "dialogue_act": "greet",
            "referenced_claim_ids": ["claim_npc1_hello"],
            "emotion": "neutral",
            "requests_world_action": False,
            "safety_flags": [],
        },
        {
            "npc_id": "npc_test",
            "trigger": "ask_case",
            "utterance": "I can tell you what I know.",
            "dialogue_act": "answer",
            "referenced_claim_ids": ["claim_npc1_secret"],
            "emotion": "neutral",
            "requests_world_action": False,
            "safety_flags": [],
        },
        {
            "npc_id": "npc_test",
            "trigger": "unknowable",
            "utterance": "I don't know about that.",
            "dialogue_act": "refuse",
            "referenced_claim_ids": [],
            "emotion": "neutral",
            "requests_world_action": False,
            "safety_flags": [],
        },
        {
            "npc_id": "npc_other",
            "trigger": "greeting",
            "utterance": "Hi.",
            "dialogue_act": "greet",
            "referenced_claim_ids": ["claim_npc2_other"],
            "emotion": "neutral",
            "requests_world_action": False,
            "safety_flags": [],
        },
        {
            "npc_id": "npc_other",
            "trigger": "unknowable",
            "utterance": "I know nothing.",
            "dialogue_act": "refuse",
            "referenced_claim_ids": [],
            "emotion": "neutral",
            "requests_world_action": False,
            "safety_flags": [],
        },
    ]
    with open(case_dir / "fallback_dialogue.json", "w") as f:
        json.dump(fallback, f, indent=2)

    return case_dir


# ---------------------------------------------------------------------------
# Service fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_provider(case_data_dir):
    return MockLLMProvider(case_data_dir / "fallback_dialogue.json")


@pytest.fixture
def context_assembler(case_data_dir):
    return ContextAssembler(case_data_dir)


@pytest.fixture
def knowledge_filter(case_data_dir):
    return KnowledgeBoundaryFilter(case_data_dir)


@pytest.fixture
def fact_leak(case_data_dir):
    return FactLeakValidator(case_data_dir / "facts.secret.json")


@pytest.fixture
def fallback_service(case_data_dir):
    return FallbackDialogueService(case_data_dir / "fallback_dialogue.json")


@pytest.fixture
def prompt_builder():
    return DialoguePromptBuilder()


@pytest.fixture
def validator():
    return StructuredOutputValidator()


@pytest.fixture
def registry():
    return PromptVersionRegistry()


@pytest.fixture
def metrics():
    return RequestMetrics()


# ---------------------------------------------------------------------------
# Sample request fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_request():
    return DialogueRequest(
        npc_id="npc_test",
        player_utterance="Hello, what do you know?",
        current_scene_id="loc_1",
        relationship_state="neutral",
        emotion_state="neutral",
    )


@pytest.fixture
def sample_request_other():
    return DialogueRequest(
        npc_id="npc_other",
        player_utterance="Hi there.",
        current_scene_id="loc_2",
        relationship_state="neutral",
        emotion_state="neutral",
    )


@pytest.fixture
def sample_classify_request():
    return ClassifyIntentRequest(
        player_utterance="Hello",
        context="greeting",
    )


@pytest.fixture
def sample_recap_request():
    return CaseRecapRequest(
        case_id="case_test",
        player_events=["visited_workshop", "talked_to_npc"],
        discovered_facts=["fact_normal_1"],
    )
