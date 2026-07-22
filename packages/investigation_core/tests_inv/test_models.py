from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from investigation_core.models import (
    NPC,
    AnomalousItem,
    Case,
    CaseEvent,
    Claim,
    Clue,
    ClueSourceType,
    DialogueAct,
    DialogueResponse,
    DivinationInput,
    DivinationResult,
    Emotion,
    Ending,
    EndingType,
    Fact,
    Hypothesis,
    HypothesisStatus,
    NPCMemory,
    NPCPersonality,
    PlayerCaseState,
    Ritual,
    SaveData,
    SecrecyLevel,
    TruthStatus,
)


class TestEnums:
    """Test all enum types."""

    def test_truth_status_values(self):
        assert TruthStatus.TRUE.value == "true"
        assert TruthStatus.FALSE.value == "false"
        assert TruthStatus.PARTIAL.value == "partial"
        assert TruthStatus.MISLEADING.value == "misleading"

    def test_secrecy_level_values(self):
        assert SecrecyLevel.PUBLIC.value == "public"
        assert SecrecyLevel.RESTRICTED.value == "restricted"
        assert SecrecyLevel.CORE_SECRET.value == "core_secret"

    def test_clue_source_type_values(self):
        assert ClueSourceType.ENVIRONMENT.value == "environment"
        assert ClueSourceType.NPC_STATEMENT.value == "npc_statement"
        assert ClueSourceType.DOCUMENT.value == "document"
        assert ClueSourceType.EXPERIMENT.value == "experiment"
        assert ClueSourceType.DEDUCTION.value == "deduction"

    def test_ending_type_values(self):
        assert EndingType.TRUE_ENDING.value == "true_ending"
        assert EndingType.PARTIAL_ENDING.value == "partial_ending"
        assert EndingType.BAD_ENDING.value == "bad_ending"

    def test_dialogue_act_values(self):
        assert DialogueAct.ANSWER.value == "answer"
        assert DialogueAct.REFUSE.value == "refuse"
        assert DialogueAct.GREET.value == "greet"

    def test_emotion_values(self):
        assert Emotion.NEUTRAL.value == "neutral"
        assert Emotion.HOSTILE.value == "hostile"
        assert Emotion.SURPRISED.value == "surprised"

    def test_hypothesis_status_values(self):
        assert HypothesisStatus.UNSUBMITTED.value == "unsubmitted"
        assert HypothesisStatus.CONFIRMED.value == "confirmed"
        assert HypothesisStatus.REJECTED.value == "rejected"


class TestFact:
    """Test Fact model."""

    def test_create_fact(self):
        fact = Fact(
            fact_id="f1",
            case_id="c1",
            summary="A fact",
            truth=True,
            secrecy=SecrecyLevel.CORE_SECRET,
        )
        assert fact.fact_id == "f1"
        assert fact.case_id == "c1"
        assert fact.summary == "A fact"
        assert fact.truth is True
        assert fact.secrecy == SecrecyLevel.CORE_SECRET

    def test_fact_defaults(self):
        fact = Fact(fact_id="f1", case_id="c1", summary="A fact", truth=False)
        assert fact.secrecy == SecrecyLevel.RESTRICTED
        assert fact.prerequisite_fact_ids == []
        assert fact.revealed_by_clue_ids == []

    def test_fact_serialization(self):
        fact = Fact(
            fact_id="f1",
            case_id="c1",
            summary="A fact",
            truth=True,
            secrecy=SecrecyLevel.CORE_SECRET,
            prerequisite_fact_ids=["f0"],
            revealed_by_clue_ids=["c1", "c2"],
        )
        data = fact.model_dump()
        assert data["fact_id"] == "f1"
        assert data["secrecy"] == "core_secret"
        assert data["prerequisite_fact_ids"] == ["f0"]
        restored = Fact(**data)
        assert restored == fact

    def test_fact_requires_ids(self):
        with pytest.raises(ValidationError):
            Fact()  # type: ignore[call-arg]


class TestClaim:
    """Test Claim model."""

    def test_create_claim(self):
        claim = Claim(
            claim_id="cl1",
            speaker_npc_id="npc_1",
            content="Testimony",
            truth_status=TruthStatus.TRUE,
        )
        assert claim.claim_id == "cl1"
        assert claim.truth_status == TruthStatus.TRUE

    def test_claim_defaults(self):
        claim = Claim(
            claim_id="cl1", speaker_npc_id="npc_1", content="Test", truth_status=TruthStatus.FALSE
        )
        assert claim.speaker_believes_it is True
        assert claim.available_when == []
        assert claim.forbidden_when == []
        assert claim.strength == 1

    def test_claim_lie(self):
        claim = Claim(
            claim_id="cl1",
            speaker_npc_id="npc_1",
            content="Lie",
            truth_status=TruthStatus.FALSE,
            speaker_believes_it=False,
        )
        assert claim.speaker_believes_it is False

    def test_claim_strength_bounds(self):
        with pytest.raises(ValidationError):
            Claim(
                claim_id="cl1",
                speaker_npc_id="npc_1",
                content="Bad",
                truth_status=TruthStatus.TRUE,
                strength=5,
            )
        with pytest.raises(ValidationError):
            Claim(
                claim_id="cl1",
                speaker_npc_id="npc_1",
                content="Bad",
                truth_status=TruthStatus.TRUE,
                strength=0,
            )


class TestClue:
    """Test Clue model."""

    def test_create_clue(self):
        clue = Clue(
            clue_id="c1",
            case_id="c1",
            display_name="Important Clue",
            source_type=ClueSourceType.DOCUMENT,
        )
        assert clue.clue_id == "c1"
        assert clue.display_name == "Important Clue"

    def test_clue_defaults(self):
        clue = Clue(clue_id="c1", case_id="c1", display_name="DC")
        assert clue.source_type == ClueSourceType.ENVIRONMENT
        assert clue.description == ""
        assert clue.location_id == ""
        assert clue.reveals_fact_ids == []
        assert clue.requires_any_tags == []
        assert clue.requires_all_tags == []
        assert clue.strength == 1
        assert clue.missable is False

    def test_clue_strength_bounds(self):
        with pytest.raises(ValidationError):
            Clue(clue_id="c1", case_id="c1", display_name="C", strength=4)
        with pytest.raises(ValidationError):
            Clue(clue_id="c1", case_id="c1", display_name="C", strength=0)


class TestNPC:
    """Test NPC model."""

    def test_create_npc(self):
        npc = NPC(npc_id="n1", name="John", description="A person")
        assert npc.npc_id == "n1"
        assert npc.name == "John"
        assert npc.description == "A person"

    def test_npc_defaults(self):
        npc = NPC(npc_id="n1", name="John")
        assert npc.role == "core"
        assert npc.known_claim_ids == []
        assert npc.lie_claim_ids == []
        assert npc.forbidden_fact_ids == []
        assert isinstance(npc.personality, NPCPersonality)
        assert npc.personality.formality == 0.5
        assert npc.initial_location_id == ""
        assert npc.default_emotion == Emotion.NEUTRAL

    def test_npc_personality_bounds(self):
        with pytest.raises(ValidationError):
            NPCPersonality(formality=1.5)
        with pytest.raises(ValidationError):
            NPCPersonality(anxiety=-0.1)


class TestHypothesis:
    """Test Hypothesis model."""

    def test_create_hypothesis(self):
        hyp = Hypothesis(
            hypothesis_id="h1",
            case_id="c1",
            title="Theory",
            description="A theory",
            required_clue_ids=["c1", "c2"],
            required_fact_ids=["f1"],
            min_confidence=2,
            leads_to_ending_id="e1",
        )
        assert hyp.hypothesis_id == "h1"
        assert hyp.status == HypothesisStatus.UNSUBMITTED

    def test_hypothesis_defaults(self):
        hyp = Hypothesis(hypothesis_id="h1", case_id="c1", title="T")
        assert hyp.description == ""
        assert hyp.required_clue_ids == []
        assert hyp.required_fact_ids == []
        assert hyp.min_confidence == 1
        assert hyp.leads_to_ending_id == ""
        assert hyp.status == HypothesisStatus.UNSUBMITTED


class TestEnding:
    """Test Ending model."""

    def test_create_ending(self):
        ending = Ending(
            ending_id="e1",
            case_id="c1",
            title="Good End",
            description="Happy ending",
            ending_type=EndingType.TRUE_ENDING,
        )
        assert ending.ending_id == "e1"
        assert ending.ending_type == EndingType.TRUE_ENDING

    def test_ending_defaults(self):
        ending = Ending(
            ending_id="e1",
            case_id="c1",
            title="Bad End",
            description="Sad",
            ending_type=EndingType.BAD_ENDING,
        )
        assert ending.required_hypothesis_id == ""
        assert ending.trigger_conditions == []
        assert ending.corruption_threshold is None

    def test_ending_with_corruption_threshold(self):
        ending = Ending(
            ending_id="e1",
            case_id="c1",
            title="Bad",
            description="Bad",
            ending_type=EndingType.BAD_ENDING,
            corruption_threshold=3,
        )
        assert ending.corruption_threshold == 3


class TestRitual:
    """Test Ritual model."""

    def test_create_ritual(self):
        ritual = Ritual(
            ritual_id="r1",
            name="Summon",
            purpose="Summon entity",
            required_knowledge_ids=["k1"],
            required_materials=["herb"],
            steps=["Draw circle", "Chant"],
        )
        assert ritual.ritual_id == "r1"
        assert len(ritual.steps) == 2

    def test_ritual_defaults(self):
        ritual = Ritual(ritual_id="r1", name="Test", purpose="Test")
        assert ritual.required_knowledge_ids == []
        assert ritual.required_materials == []
        assert ritual.space_condition == ""
        assert ritual.time_condition == ""
        assert ritual.corruption_change == 0
        assert ritual.may_alert_entities == []


class TestAnomalousItem:
    """Test AnomalousItem model."""

    def test_create_item(self):
        item = AnomalousItem(
            item_id="i1",
            name="Strange Box",
            description="A box",
            active_ability="See visions",
            cooldown=3,
        )
        assert item.item_id == "i1"
        assert item.cooldown == 3

    def test_item_defaults(self):
        item = AnomalousItem(item_id="i1", name="Box", description="A box")
        assert item.active_ability == ""
        assert item.passive_ability == ""
        assert item.use_condition == ""
        assert item.fixed_cost == ""
        assert item.holding_cost == ""
        assert item.violation_condition == ""
        assert item.penalty == ""
        assert item.cooldown == 0


class TestPlayerCaseState:
    """Test PlayerCaseState model."""

    def test_create_state(self):
        state = PlayerCaseState(case_id="c1")
        assert state.case_id == "c1"
        assert state.current_location_id == ""

    def test_state_defaults(self):
        state = PlayerCaseState(case_id="c1")
        assert state.discovered_clue_ids == []
        assert state.confirmed_hypothesis_ids == []
        assert state.rejected_hypothesis_ids == []
        assert state.visited_location_ids == []
        assert state.npc_relationship == {}
        assert state.npc_available == {}
        assert state.corruption_level == 0
        assert state.spirituality == 5
        assert state.stability == 5
        assert state.completed_events == []
        assert state.seed == 0
        assert state.revealed_claim_ids == []
        assert state.discovered_fact_ids == []

    def test_state_serialization(self):
        state = PlayerCaseState(
            case_id="c1",
            discovered_clue_ids=["c1"],
            corruption_level=2,
            spirituality=3,
            seed=42,
        )
        data = state.model_dump()
        restored = PlayerCaseState(**data)
        assert restored.discovered_clue_ids == ["c1"]
        assert restored.corruption_level == 2
        assert restored.seed == 42


class TestDivinationIO:
    """Test DivinationInput and DivinationResult models."""

    def test_divination_input_defaults(self):
        inp = DivinationInput(question_template="What?")
        assert inp.obtained_clue_ids == []
        assert inp.medium == ""
        assert inp.current_spirituality == 5
        assert inp.corruption_level == 0
        assert inp.scene_interference == 0
        assert inp.seed == 0

    def test_divination_input_with_values(self):
        inp = DivinationInput(
            question_template="Truth?",
            obtained_clue_ids=["c1"],
            current_spirituality=3,
            corruption_level=2,
            scene_interference=1,
            seed=42,
        )
        assert inp.current_spirituality == 3
        assert inp.corruption_level == 2

    def test_divination_result_defaults(self):
        result = DivinationResult(tendency="迷雾", symbolic_image="灰雾弥漫", confidence=3)
        assert result.cost == 1
        assert result.is_interfered is False

    def test_divination_result_confidence_bounds(self):
        with pytest.raises(ValidationError):
            DivinationResult(tendency="T", symbolic_image="I", confidence=0)
        with pytest.raises(ValidationError):
            DivinationResult(tendency="T", symbolic_image="I", confidence=6)


class TestDialogueResponse:
    """Test DialogueResponse model."""

    def test_create_response(self):
        resp = DialogueResponse(
            utterance="Hello",
            dialogue_act=DialogueAct.GREET,
            referenced_claim_ids=["c1"],
            emotion=Emotion.FRIENDLY,
        )
        assert resp.utterance == "Hello"
        assert resp.dialogue_act == DialogueAct.GREET

    def test_response_defaults(self):
        resp = DialogueResponse(utterance="Hi", dialogue_act=DialogueAct.GREET)
        assert resp.referenced_claim_ids == []
        assert resp.emotion == Emotion.NEUTRAL
        assert resp.animation_tag == ""
        assert resp.requests_world_action is False
        assert resp.safety_flags == []


class TestSaveData:
    """Test SaveData model."""

    def test_create_save_data(self):
        state = PlayerCaseState(case_id="c1")
        save = SaveData(save_id="s1", player_state=state)
        assert save.save_id == "s1"
        assert save.player_state.case_id == "c1"
        assert save.event_log == []
        assert save.seed == 0
        assert isinstance(save.timestamp, datetime)

    def test_save_data_serialization(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.discovered_clue_ids = ["clue_1"]
        event = CaseEvent(
            event_id="evt_1",
            case_id="test_case",
            event_type="test",
            description="Test event",
        )
        save = SaveData(save_id="s1", player_state=state, event_log=[event], seed=42)
        data = save.model_dump(mode="json")
        restored = SaveData(**data)
        assert restored.save_id == "s1"
        assert restored.player_state.discovered_clue_ids == ["clue_1"]
        assert len(restored.event_log) == 1
        assert restored.event_log[0].event_type == "test"


class TestCase:
    """Test Case model."""

    def test_create_case(self, sample_case):
        assert sample_case.case_id == "test_case"
        assert len(sample_case.facts) == 3
        assert len(sample_case.claims) == 3
        assert len(sample_case.clues) == 3
        assert len(sample_case.npcs) == 2
        assert len(sample_case.hypotheses) == 2
        assert len(sample_case.endings) == 3
        assert len(sample_case.rituals) == 1
        assert len(sample_case.items) == 1

    def test_case_defaults(self):
        case = Case(case_id="c1", title="T", description="D")
        assert case.version == "0.1.0"
        assert case.facts == []
        assert case.claims == []
        assert case.clues == []
        assert case.npcs == []
        assert case.hypotheses == []
        assert case.endings == []
        assert case.rituals == []
        assert case.items == []
        assert case.initial_scene_id == ""

    def test_case_serialization(self, sample_case):
        data = sample_case.model_dump()
        restored = Case(**data)
        assert restored.case_id == sample_case.case_id
        assert len(restored.facts) == len(sample_case.facts)
        assert restored.facts[0].fact_id == sample_case.facts[0].fact_id
        assert len(restored.clues) == len(sample_case.clues)
        assert restored.clues[0].display_name == sample_case.clues[0].display_name

    def test_case_empty_lists(self):
        """Edge case: case with empty lists."""
        case = Case(case_id="c1", title="Empty", description="Empty case")
        assert len(case.facts) == 0
        assert len(case.clues) == 0
        assert len(case.npcs) == 0


class TestNPCMemory:
    """Test NPCMemory model."""

    def test_create_memory(self):
        mem = NPCMemory(memory_id="m1", npc_id="n1")
        assert mem.memory_id == "m1"
        assert mem.npc_id == "n1"

    def test_memory_defaults(self):
        mem = NPCMemory(memory_id="m1", npc_id="n1")
        assert mem.event_id == ""
        assert isinstance(mem.timestamp, datetime)
        assert mem.source == ""
        assert mem.confidence == 1.0
        assert mem.visibility == "public"
        assert mem.involved_entities == []


class TestCaseEvent:
    """Test CaseEvent model."""

    def test_create_event(self):
        event = CaseEvent(
            event_id="e1", case_id="c1", event_type="discovery", description="Found clue"
        )
        assert event.event_id == "e1"
        assert event.event_type == "discovery"

    def test_event_defaults(self):
        event = CaseEvent(event_id="e1", case_id="c1", event_type="test", description="Test")
        assert isinstance(event.timestamp, datetime)
        assert event.involved_npc_ids == []
        assert event.involved_clue_ids == []


class TestEdgeCases:
    """Test edge cases across models."""

    def test_fact_empty_revealed_by(self):
        fact = Fact(fact_id="f1", case_id="c1", summary="S", truth=False)
        assert fact.revealed_by_clue_ids == []

    def test_clue_missable_flag(self):
        clue = Clue(
            clue_id="c1",
            case_id="c1",
            display_name="Missable",
            missable=True,
        )
        assert clue.missable is True

    def test_npc_empty_lists(self):
        npc = NPC(npc_id="n1", name="Nobody")
        assert npc.known_claim_ids == []
        assert npc.lie_claim_ids == []
        assert npc.forbidden_fact_ids == []

    def test_hypothesis_boundary_min_confidence(self):
        hyp = Hypothesis(hypothesis_id="h1", case_id="c1", title="T", min_confidence=5)
        assert hyp.min_confidence == 5

    def test_ritual_no_steps(self):
        ritual = Ritual(ritual_id="r1", name="Simple", purpose="Simple")
        assert ritual.steps == []

    def test_divination_result_interfered(self):
        result = DivinationResult(
            tendency="干扰", symbolic_image="模糊", confidence=2, cost=2, is_interfered=True
        )
        assert result.is_interfered is True
        assert result.cost == 2
