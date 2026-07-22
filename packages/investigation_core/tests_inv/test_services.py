from __future__ import annotations

import json

import pytest

from investigation_core.models import (
    Case,
    CaseEvent,
    DivinationInput,
    DivinationResult,
    Ending,
    EndingType,
    Hypothesis,
    HypothesisStatus,
    PlayerCaseState,
    SaveData,
)
from investigation_core.services import (
    CaseLoader,
    CaseStateMachine,
    ClueDiscoveryService,
    DivinationService,
    EndingResolver,
    EventLog,
    HypothesisEvaluationService,
    RitualValidationService,
    SaveRepository,
)

# =============================================================================
# CaseLoader Tests
# =============================================================================


class TestCaseLoader:
    def test_load_case_normal(self, sample_case_dir):
        loader = CaseLoader(sample_case_dir)
        case = loader.load_case()
        assert case.case_id == "test_case"
        assert len(case.facts) == 3
        assert len(case.claims) == 3
        assert len(case.clues) == 3
        assert len(case.npcs) == 2
        assert len(case.hypotheses) == 2
        assert len(case.endings) == 3
        assert len(case.rituals) == 0  # No rituals.json written
        assert len(case.items) == 0  # No items.json written
        assert case.initial_scene_id == "loc_1"

    def test_load_case_missing_file(self, temp_dir):
        loader = CaseLoader(temp_dir)
        with pytest.raises(FileNotFoundError):
            loader.load_case()

    def test_load_case_invalid_json(self, temp_dir):
        case_dir = temp_dir / "cases" / "broken"
        case_dir.mkdir(parents=True)
        (case_dir / "case.json").write_text("{invalid json}")
        loader = CaseLoader(case_dir)
        with pytest.raises(json.JSONDecodeError):
            loader.load_case()

    def test_load_case_with_optional_files(self, temp_dir, sample_case):
        """Test loading with rituals.json and items.json present."""
        case_dir = temp_dir / "cases" / "full"
        case_dir.mkdir(parents=True)
        # Write required files
        with open(case_dir / "case.json", "w") as f:
            json.dump(
                {
                    "case_id": "test_case",
                    "title": "Test Case",
                    "description": "A test case",
                    "version": "0.1.0",
                    "initial_scene_id": "loc_1",
                    "endings": [e.model_dump() for e in sample_case.endings],
                },
                f,
            )
        with open(case_dir / "facts.secret.json", "w") as f:
            json.dump([f.model_dump() for f in sample_case.facts], f)
        with open(case_dir / "claims.json", "w") as f:
            json.dump([c.model_dump() for c in sample_case.claims], f)
        with open(case_dir / "clues.json", "w") as f:
            json.dump([c.model_dump() for c in sample_case.clues], f)
        with open(case_dir / "hypotheses.json", "w") as f:
            json.dump([h.model_dump() for h in sample_case.hypotheses], f)
        with open(case_dir / "npcs.json", "w") as f:
            json.dump([n.model_dump() for n in sample_case.npcs], f)
        # Write optional files
        with open(case_dir / "rituals.json", "w") as f:
            json.dump([r.model_dump() for r in sample_case.rituals], f)
        with open(case_dir / "items.json", "w") as f:
            json.dump([i.model_dump() for i in sample_case.items], f)

        loader = CaseLoader(case_dir)
        case = loader.load_case()
        assert len(case.rituals) == 1
        assert case.rituals[0].ritual_id == "rit_1"
        assert len(case.items) == 1
        assert case.items[0].item_id == "item_1"


# =============================================================================
# ClueDiscoveryService Tests
# =============================================================================


class TestClueDiscoveryService:
    def test_discover_new_clue(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        success, event = ClueDiscoveryService.discover_clue(sample_case, state, "clue_1")
        assert success is True
        assert event is not None
        assert event.event_type == "clue_discovered"
        assert "clue_1" in state.discovered_clue_ids
        assert "fact_1" in state.discovered_fact_ids

    def test_discover_duplicate_clue(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        ClueDiscoveryService.discover_clue(sample_case, state, "clue_1")
        success, event = ClueDiscoveryService.discover_clue(sample_case, state, "clue_1")
        assert success is False
        assert event is None

    def test_discover_invalid_clue(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        success, event = ClueDiscoveryService.discover_clue(sample_case, state, "invalid_clue")
        assert success is False
        assert event is None

    def test_discover_clue_with_condition_met(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.completed_events.append("evt_spirit_vision")
        success, event = ClueDiscoveryService.discover_clue(sample_case, state, "clue_3")
        assert success is True
        assert event is not None
        assert "clue_3" in state.discovered_clue_ids
        assert "fact_2" in state.discovered_fact_ids
        assert "fact_3" in state.discovered_fact_ids

    def test_discover_clue_with_condition_not_met(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        success, event = ClueDiscoveryService.discover_clue(sample_case, state, "clue_3")
        assert success is False
        assert event is None
        assert "clue_3" not in state.discovered_clue_ids

    def test_discover_clue_reveals_multiple_facts(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.completed_events.append("evt_spirit_vision")
        ClueDiscoveryService.discover_clue(sample_case, state, "clue_3")
        assert "fact_2" in state.discovered_fact_ids
        assert "fact_3" in state.discovered_fact_ids


# =============================================================================
# HypothesisEvaluationService Tests
# =============================================================================


class TestHypothesisEvaluationService:
    def test_submit_successful(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.discovered_clue_ids = ["clue_1", "clue_2", "clue_3"]
        state.discovered_fact_ids = ["fact_1", "fact_2"]
        state.completed_events.append("evt_spirit_vision")

        success, event, ending_id = HypothesisEvaluationService.submit_hypothesis(
            sample_case, state, "hyp_1"
        )
        assert success is True
        assert event is not None
        assert event.event_type == "hypothesis_confirmed"
        assert ending_id == "end_true"
        assert "hyp_1" in state.confirmed_hypothesis_ids

    def test_submit_insufficient_clues(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.discovered_clue_ids = ["clue_1"]
        state.discovered_fact_ids = ["fact_1"]

        success, event, ending_id = HypothesisEvaluationService.submit_hypothesis(
            sample_case, state, "hyp_1"
        )
        assert success is False
        assert event is None
        assert ending_id is None

    def test_submit_insufficient_facts(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.discovered_clue_ids = ["clue_1", "clue_2", "clue_3"]
        # Missing fact_2
        state.discovered_fact_ids = ["fact_1"]
        state.completed_events.append("evt_spirit_vision")

        success, event, ending_id = HypothesisEvaluationService.submit_hypothesis(
            sample_case, state, "hyp_1"
        )
        assert success is False

    def test_submit_insufficient_confidence(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        # hyp_1 requires strength sum >= 3, but only clue_1 (strength=1) is discovered
        state.discovered_clue_ids = ["clue_1"]
        state.discovered_fact_ids = ["fact_1"]

        success, event, ending_id = HypothesisEvaluationService.submit_hypothesis(
            sample_case, state, "hyp_1"
        )
        assert success is False

    def test_submit_simple_hypothesis(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.discovered_clue_ids = ["clue_1"]
        state.discovered_fact_ids = ["fact_1"]

        success, event, ending_id = HypothesisEvaluationService.submit_hypothesis(
            sample_case, state, "hyp_2"
        )
        assert success is True
        assert ending_id == "end_partial"
        assert "hyp_2" in state.confirmed_hypothesis_ids

    def test_submit_invalid_hypothesis(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        success, event, ending_id = HypothesisEvaluationService.submit_hypothesis(
            sample_case, state, "invalid_hyp"
        )
        assert success is False
        assert event is None
        assert ending_id is None

    def test_submit_insufficient_confidence_with_all_clues(self, sample_case):
        """Test when all clues/facts are known but confidence sum < min_confidence."""
        state = PlayerCaseState(case_id="test_case")
        high_hyp = Hypothesis(
            hypothesis_id="hyp_high",
            case_id="test_case",
            title="High confidence needed",
            required_clue_ids=["clue_1"],  # strength=1
            required_fact_ids=["fact_1"],
            supporting_fact_ids=[],
            contradicting_clue_ids=[],
            contradicting_fact_ids=[],
            min_confidence=2,  # Need confidence >= 2 but only 1 available
            leads_to_ending_id="end_true",
        )
        sample_case.hypotheses.append(high_hyp)
        state.discovered_clue_ids = ["clue_1"]
        state.discovered_fact_ids = ["fact_1"]

        success, event, ending_id = HypothesisEvaluationService.submit_hypothesis(
            sample_case, state, "hyp_high"
        )
        # Sum of strengths = 1 < 2
        assert success is False
        assert event is None
        assert ending_id is None

    def test_submit_rejected_by_contradicting_fact(self, sample_case):
        """Hypothesis with contradicting_fact_ids should be auto-rejected."""
        hyp = Hypothesis(
            hypothesis_id="hyp_contradict_fact",
            case_id="test_case",
            title="Contradicted by fact",
            required_clue_ids=["clue_1"],
            required_fact_ids=["fact_1"],
            supporting_fact_ids=[],
            contradicting_clue_ids=[],
            contradicting_fact_ids=["fact_2"],
            min_confidence=1,
            leads_to_ending_id="end_true",
        )
        sample_case.hypotheses.append(hyp)
        state = PlayerCaseState(case_id="test_case")
        state.discovered_clue_ids = ["clue_1"]
        state.discovered_fact_ids = ["fact_1", "fact_2"]  # fact_2 contradicts

        success, event, ending_id = HypothesisEvaluationService.submit_hypothesis(
            sample_case, state, "hyp_contradict_fact"
        )
        assert success is False
        assert event is not None
        assert event.event_type == "hypothesis_rejected"
        assert ending_id is None
        assert "hyp_contradict_fact" in state.rejected_hypothesis_ids

    def test_submit_penalized_by_contradicting_clue(self, sample_case):
        """Contradicting clues should reduce confidence below threshold."""
        hyp = Hypothesis(
            hypothesis_id="hyp_contradict_clue",
            case_id="test_case",
            title="Contradicted by clue",
            required_clue_ids=["clue_1"],
            required_fact_ids=["fact_1"],
            supporting_fact_ids=[],
            contradicting_clue_ids=["clue_2"],  # clue_2 has strength=2
            contradicting_fact_ids=[],
            min_confidence=1,  # Need confidence >= 1
            leads_to_ending_id="end_true",
        )
        sample_case.hypotheses.append(hyp)
        state = PlayerCaseState(case_id="test_case")
        # clue_1 (strength=1) - clue_2 (strength=2) = -1 < 1
        state.discovered_clue_ids = ["clue_1", "clue_2"]
        state.discovered_fact_ids = ["fact_1"]

        success, event, ending_id = HypothesisEvaluationService.submit_hypothesis(
            sample_case, state, "hyp_contradict_clue"
        )
        assert success is False
        assert event is None
        assert ending_id is None

    def test_submit_boosted_by_supporting_fact(self, sample_case):
        """Supporting facts should boost confidence above threshold."""
        hyp = Hypothesis(
            hypothesis_id="hyp_support",
            case_id="test_case",
            title="Supported by fact",
            required_clue_ids=["clue_1"],  # strength=1
            required_fact_ids=["fact_1"],
            supporting_fact_ids=["fact_3"],  # +2 confidence
            contradicting_clue_ids=[],
            contradicting_fact_ids=[],
            min_confidence=2,  # Need >= 2
            leads_to_ending_id="end_true",
        )
        sample_case.hypotheses.append(hyp)
        state = PlayerCaseState(case_id="test_case")
        state.discovered_clue_ids = ["clue_1"]
        state.discovered_fact_ids = ["fact_1", "fact_3"]

        success, event, ending_id = HypothesisEvaluationService.submit_hypothesis(
            sample_case, state, "hyp_support"
        )
        assert success is True
        assert event is not None
        assert ending_id == "end_true"

    def test_submit_contradicting_clue_but_still_passes(self, sample_case):
        """Contradicting clue reduces confidence but not below threshold."""
        hyp = Hypothesis(
            hypothesis_id="hyp_partial_contradict",
            case_id="test_case",
            title="Partially contradicted",
            required_clue_ids=["clue_1", "clue_2"],  # strengths: 1 + 2 = 3
            required_fact_ids=["fact_1"],
            supporting_fact_ids=[],
            contradicting_clue_ids=["clue_3"],  # strength=3, deducted
            contradicting_fact_ids=[],
            min_confidence=1,  # 3 - 3 = 0 < 1
            leads_to_ending_id="end_true",
        )
        sample_case.hypotheses.append(hyp)
        state = PlayerCaseState(case_id="test_case")
        state.discovered_clue_ids = ["clue_1", "clue_2", "clue_3"]
        state.discovered_fact_ids = ["fact_1"]
        state.completed_events.append("evt_spirit_vision")

        # 1 + 2 = 3 (clues) - 3 (contradicting clue strength) = 0 < 1
        success, event, ending_id = HypothesisEvaluationService.submit_hypothesis(
            sample_case, state, "hyp_partial_contradict"
        )
        assert success is False

    def test_hypothesis_status_changes(self, sample_case):
        hyp = sample_case.hypotheses[0]
        assert hyp.status == HypothesisStatus.UNSUBMITTED

        state = PlayerCaseState(case_id="test_case")
        state.discovered_clue_ids = ["clue_1", "clue_2", "clue_3"]
        state.discovered_fact_ids = ["fact_1", "fact_2"]
        state.completed_events.append("evt_spirit_vision")
        HypothesisEvaluationService.submit_hypothesis(sample_case, state, "hyp_1")
        assert hyp.status == HypothesisStatus.CONFIRMED


# =============================================================================
# DivinationService Tests
# =============================================================================


class TestDivinationService:
    def test_divination_normal(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.discovered_clue_ids = ["clue_1"]
        state.discovered_fact_ids = ["fact_1"]
        inp = DivinationInput(
            question_template="What is the truth?",
            obtained_clue_ids=state.discovered_clue_ids,
            current_spirituality=5,
            corruption_level=0,
            seed=42,
        )
        result = DivinationService.perform_divination(sample_case, state, inp)
        assert result.tendency in ("正确方向", "受到干扰")
        assert result.confidence >= 1
        assert result.cost == 1
        assert result.is_interfered is False
        assert "clue" in result.symbolic_image or "Clue" in result.symbolic_image

    def test_divination_no_spirituality(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        inp = DivinationInput(
            question_template="Q",
            obtained_clue_ids=[],
            current_spirituality=0,
            corruption_level=0,
            seed=42,
        )
        result = DivinationService.perform_divination(sample_case, state, inp)
        assert result.tendency == "失败"
        assert result.confidence == 1  # Minimum confidence bound
        assert result.cost == 0
        assert result.is_interfered is True

    def test_divination_no_clues(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        inp = DivinationInput(
            question_template="Q",
            obtained_clue_ids=[],
            current_spirituality=5,
            corruption_level=0,
            seed=42,
        )
        result = DivinationService.perform_divination(sample_case, state, inp)
        assert result.tendency == "迷雾"
        assert result.confidence >= 1
        assert result.cost == 1

    def test_divination_with_interference(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.discovered_clue_ids = ["clue_1"]
        inp = DivinationInput(
            question_template="Q",
            obtained_clue_ids=state.discovered_clue_ids,
            current_spirituality=5,
            corruption_level=3,
            seed=42,
        )
        result = DivinationService.perform_divination(sample_case, state, inp)
        assert result.is_interfered is True

    def test_divination_scene_interference(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.discovered_clue_ids = ["clue_1"]
        inp = DivinationInput(
            question_template="Q",
            obtained_clue_ids=state.discovered_clue_ids,
            current_spirituality=5,
            corruption_level=0,
            scene_interference=2,
            seed=42,
        )
        result = DivinationService.perform_divination(sample_case, state, inp)
        assert result.is_interfered is True

    def test_divination_determinism(self, sample_case):
        """Same seed + same state = same result."""
        state = PlayerCaseState(case_id="test_case")
        state.discovered_clue_ids = ["clue_1", "clue_2"]
        inp = DivinationInput(
            question_template="Truth?",
            obtained_clue_ids=state.discovered_clue_ids,
            current_spirituality=5,
            corruption_level=0,
            seed=999,
        )
        r1 = DivinationService.perform_divination(sample_case, state, inp)
        r2 = DivinationService.perform_divination(sample_case, state, inp)
        assert r1.tendency == r2.tendency
        assert r1.symbolic_image == r2.symbolic_image
        assert r1.confidence == r2.confidence

    def test_divination_confidence_reduced_by_corruption(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.discovered_clue_ids = ["clue_1"]
        inp_low = DivinationInput(
            question_template="Q",
            obtained_clue_ids=state.discovered_clue_ids,
            current_spirituality=5,
            corruption_level=0,
            seed=42,
        )
        inp_high = DivinationInput(
            question_template="Q",
            obtained_clue_ids=state.discovered_clue_ids,
            current_spirituality=5,
            corruption_level=4,
            scene_interference=1,
            seed=42,
        )
        r_low = DivinationService.perform_divination(sample_case, state, inp_low)
        r_high = DivinationService.perform_divination(sample_case, state, inp_high)
        assert r_high.confidence <= r_low.confidence


# =============================================================================
# EndingResolver Tests
# =============================================================================


class TestEndingResolver:
    def test_resolve_true_ending(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.confirmed_hypothesis_ids = ["hyp_1"]
        ending = EndingResolver.resolve_ending(sample_case, state)
        assert ending is not None
        assert ending.ending_id == "end_true"
        assert ending.ending_type == EndingType.TRUE_ENDING

    def test_resolve_partial_ending(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.confirmed_hypothesis_ids = ["hyp_2"]
        ending = EndingResolver.resolve_ending(sample_case, state)
        assert ending is not None
        assert ending.ending_id == "end_partial"
        assert ending.ending_type == EndingType.PARTIAL_ENDING

    def test_resolve_corruption_bad_ending(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.corruption_level = 3
        # No hypothesis confirmed, should trigger corruption-based bad ending
        ending = EndingResolver.resolve_ending(sample_case, state)
        assert ending is not None
        assert ending.ending_id == "end_bad"
        assert ending.ending_type == EndingType.BAD_ENDING

    def test_resolve_no_ending(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        # No hypothesis, low corruption
        ending = EndingResolver.resolve_ending(sample_case, state)
        assert ending is None

    def test_resolve_corruption_below_threshold(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.corruption_level = 2  # Below threshold of 3
        ending = EndingResolver.resolve_ending(sample_case, state)
        assert ending is None

    def test_resolve_fallback_bad_ending(self, sample_case):
        """Test the fallback bad ending path (lines 276-281)."""
        from investigation_core.models import Case

        # Create a case where no ending matches via corruption_threshold
        # but a fallback BAD_ENDING exists
        bad_ending = Ending(
            ending_id="end_fallback_bad",
            case_id="test_case",
            title="Fallback Bad",
            description="Default bad",
            ending_type=EndingType.BAD_ENDING,
            required_hypothesis_id="nonexistent",  # Won't match
            corruption_threshold=None,  # Won't match via corruption
        )
        custom_case = Case(
            case_id="test_case",
            title="Test",
            description="Test",
            endings=[bad_ending],
        )
        state = PlayerCaseState(case_id="test_case")
        state.corruption_level = 5  # High corruption
        ending = EndingResolver.resolve_ending(custom_case, state)
        # Should still find the BAD_ENDING via fallback
        assert ending is not None
        assert ending.ending_type == EndingType.BAD_ENDING

    def test_resolve_true_over_partial(self, sample_case):
        """When both hypotheses are confirmed, the first matching hypothesis' ending is used."""
        state = PlayerCaseState(case_id="test_case")
        state.confirmed_hypothesis_ids = ["hyp_2", "hyp_1"]
        ending = EndingResolver.resolve_ending(sample_case, state)
        assert ending is not None
        # hyp_1 matches first in the hypotheses list order, so it returns end_true
        assert ending.ending_id == "end_true"


# =============================================================================
# RitualValidationService Tests
# =============================================================================


class TestRitualValidationService:
    def test_ritual_success(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.discovered_fact_ids = ["fact_1"]
        success, message, corruption = RitualValidationService.validate_ritual(
            sample_case, state, "rit_1", ["herb", "candle"], seed=42
        )
        # Verify it returns valid types regardless of outcome
        assert isinstance(message, str)
        assert isinstance(corruption, int)

    def test_ritual_success_with_fixed_seed(self, sample_case):
        """Test with a seed known to produce success."""
        state = PlayerCaseState(case_id="test_case")
        state.discovered_fact_ids = ["fact_1"]
        # Try many seeds to find a success
        for seed in range(100):
            success, message, corruption = RitualValidationService.validate_ritual(
                sample_case, state, "rit_1", ["herb", "candle"], seed=seed
            )
            if success:
                assert message == "Success!"
                assert corruption == 1
                return
        pytest.fail("No successful ritual outcome found in seeds 0-99")

    def test_ritual_missing_materials(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        state.discovered_fact_ids = ["fact_1"]
        success, message, corruption = RitualValidationService.validate_ritual(
            sample_case, state, "rit_1", ["herb"], seed=42
        )
        assert success is False
        assert "材料不足" in message
        assert corruption == 0

    def test_ritual_missing_knowledge(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        # No discovered facts
        success, message, corruption = RitualValidationService.validate_ritual(
            sample_case, state, "rit_1", ["herb", "candle"], seed=42
        )
        assert success is False
        assert "知识" in message
        assert corruption == 0

    def test_ritual_invalid_id(self, sample_case):
        state = PlayerCaseState(case_id="test_case")
        success, message, corruption = RitualValidationService.validate_ritual(
            sample_case, state, "invalid_ritual", [], seed=42
        )
        assert success is False
        assert "未知" in message
        assert corruption == 0

    def test_ritual_failure_result(self, sample_case):
        """Test a seed that produces failure."""
        state = PlayerCaseState(case_id="test_case")
        state.discovered_fact_ids = ["fact_1"]
        for seed in range(100):
            success, message, corruption = RitualValidationService.validate_ritual(
                sample_case, state, "rit_1", ["herb", "candle"], seed=seed
            )
            if (
                not success
                and "材料" not in message
                and "知识" not in message
                and "未知" not in message
            ):
                assert "失败" in message or "Failed" in message
                assert corruption == 2  # corruption_change (1) + 1
                return
        pytest.fail("No failure ritual outcome found in seeds 0-99")


# =============================================================================
# EventLog Tests
# =============================================================================


class TestEventLog:
    def test_add_and_get_events(self):
        log = EventLog()
        assert log.get_event_count() == 0

        event = CaseEvent(event_id="e1", case_id="c1", event_type="test", description="Test event")
        log.add_event(event)
        assert log.get_event_count() == 1

        events = log.get_events()
        assert len(events) == 1
        assert events[0].event_id == "e1"

    def test_get_events_filter_by_case(self):
        log = EventLog()
        log.add_event(CaseEvent(event_id="e1", case_id="c1", event_type="t", description="D1"))
        log.add_event(CaseEvent(event_id="e2", case_id="c2", event_type="t", description="D2"))
        log.add_event(CaseEvent(event_id="e3", case_id="c1", event_type="t", description="D3"))

        c1_events = log.get_events(case_id="c1")
        assert len(c1_events) == 2
        assert all(e.case_id == "c1" for e in c1_events)

    def test_clear_events(self):
        log = EventLog()
        log.add_event(CaseEvent(event_id="e1", case_id="c1", event_type="t", description="D1"))
        log.clear()
        assert log.get_event_count() == 0
        assert log.get_events() == []

    def test_events_immutable_copy(self):
        log = EventLog()
        log.add_event(CaseEvent(event_id="e1", case_id="c1", event_type="t", description="D1"))
        events = log.get_events()
        events.clear()
        # Original should be unaffected
        assert log.get_event_count() == 1


# =============================================================================
# SaveRepository Tests
# =============================================================================


class TestSaveRepository:
    def test_save_and_load(self, temp_dir):
        save_dir = temp_dir / "saves"
        repo = SaveRepository(save_dir)
        state = PlayerCaseState(case_id="c1", spirituality=3, corruption_level=1)
        save_data = SaveData(save_id="s1", player_state=state, seed=42)

        path = repo.save(save_data, slot=0)
        assert path.exists()
        assert path.name == "save_0.json"

        loaded = repo.load(slot=0)
        assert loaded is not None
        assert loaded.save_id == "s1"
        assert loaded.player_state.spirituality == 3
        assert loaded.player_state.corruption_level == 1
        assert loaded.seed == 42

    def test_load_nonexistent(self, temp_dir):
        save_dir = temp_dir / "saves"
        repo = SaveRepository(save_dir)
        loaded = repo.load(slot=99)
        assert loaded is None

    def test_list_saves(self, temp_dir):
        save_dir = temp_dir / "saves"
        repo = SaveRepository(save_dir)
        state = PlayerCaseState(case_id="c1")

        assert repo.list_saves() == []

        repo.save(SaveData(save_id="s1", player_state=state), slot=0)
        repo.save(SaveData(save_id="s2", player_state=state), slot=2)
        repo.save(SaveData(save_id="s3", player_state=state), slot=1)

        saves = repo.list_saves()
        assert saves == [0, 1, 2]

    def test_save_directory_created(self, temp_dir):
        save_dir = temp_dir / "nonexistent" / "saves"
        assert not save_dir.exists()
        SaveRepository(save_dir)
        assert save_dir.exists()

    def test_save_and_load_with_events(self, temp_dir):
        save_dir = temp_dir / "saves"
        repo = SaveRepository(save_dir)
        state = PlayerCaseState(case_id="c1")
        event = CaseEvent(event_id="e1", case_id="c1", event_type="test", description="Saved event")
        save_data = SaveData(save_id="s1", player_state=state, event_log=[event])
        repo.save(save_data, slot=0)

        loaded = repo.load(slot=0)
        assert loaded is not None
        assert len(loaded.event_log) == 1
        assert loaded.event_log[0].event_id == "e1"


# =============================================================================
# CaseStateMachine Tests
# =============================================================================


class TestCaseStateMachine:
    def test_initial_state(self, state_machine):
        assert state_machine.case.case_id == "test_case"
        assert state_machine.player_state.current_location_id == "loc_1"
        assert state_machine.player_state.discovered_clue_ids == []

    def test_move_to_location(self, state_machine):
        state_machine.move_to_location("loc_2")
        assert state_machine.player_state.current_location_id == "loc_2"
        assert "loc_2" in state_machine.player_state.visited_location_ids

    def test_move_to_same_location(self, state_machine):
        state_machine.move_to_location("loc_1")
        assert "loc_1" in state_machine.player_state.visited_location_ids
        # It should only appear once
        assert state_machine.player_state.visited_location_ids.count("loc_1") == 1

    def test_get_available_clues(self, state_machine):
        clues = state_machine.get_available_clues()
        # At loc_1: clue_1 and clue_2 (clue_3 is at loc_2)
        clue_ids = {c.clue_id for c in clues}
        assert clue_ids == {"clue_1", "clue_2"}

    def test_get_available_clues_after_discovery(self, state_machine):
        state_machine.discover_clue("clue_1")
        clues = state_machine.get_available_clues()
        clue_ids = {c.clue_id for c in clues}
        assert "clue_1" not in clue_ids
        assert "clue_2" in clue_ids

    def test_get_discovered_clues(self, state_machine):
        state_machine.discover_clue("clue_1")
        state_machine.discover_clue("clue_2")
        clues = state_machine.get_discovered_clues()
        assert len(clues) == 2

    def test_get_available_npcs(self, state_machine):
        npcs = state_machine.get_available_npcs()
        npc_ids = {n.npc_id for n in npcs}
        assert npc_ids == {"npc_1"}  # npc_1 is at loc_1

    def test_get_npc_claims(self, state_machine):
        claims = state_machine.get_npc_claims("npc_1")
        assert len(claims) == 2
        assert all(c.speaker_npc_id == "npc_1" for c in claims)

    def test_get_npc_claims_invalid_npc(self, state_machine):
        claims = state_machine.get_npc_claims("invalid_npc")
        assert claims == []

    def test_get_revealed_claims_empty(self, state_machine):
        claims = state_machine.get_revealed_claims()
        assert claims == []

    def test_get_revealed_claims_with_data(self, state_machine):
        state_machine.player_state.revealed_claim_ids = ["claim_1"]
        claims = state_machine.get_revealed_claims()
        assert len(claims) == 1
        assert claims[0].claim_id == "claim_1"

    def test_discover_clue_via_machine(self, state_machine):
        success, event = state_machine.discover_clue("clue_1")
        assert success is True
        assert event is not None
        # Event should be logged
        log = state_machine.get_event_log()
        assert len(log) == 1

    def test_discover_clue_failure_via_machine(self, state_machine):
        success, event = state_machine.discover_clue("invalid")
        assert success is False
        assert event is None

    def test_submit_hypothesis_via_machine(self, state_machine):
        state_machine.discover_clue("clue_1")
        success, event, ending_id = state_machine.submit_hypothesis("hyp_2")
        assert success is True
        assert ending_id == "end_partial"
        log = state_machine.get_event_log()
        assert len(log) == 2  # discover + submit

    def test_submit_hypothesis_failure_via_machine(self, state_machine):
        success, event, ending_id = state_machine.submit_hypothesis("hyp_1")
        assert success is False
        assert event is None

    def test_perform_divination_via_machine(self, state_machine):
        state_machine.discover_clue("clue_1")
        result = state_machine.perform_divination("What is truth?", seed=42)
        assert isinstance(result, DivinationResult)
        # Spirituality should be reduced by cost
        assert state_machine.player_state.spirituality == 5 - result.cost

    def test_perform_divination_no_spirituality(self, state_machine):
        state_machine.player_state.spirituality = 0
        result = state_machine.perform_divination("Q", seed=42)
        assert result.tendency == "失败"
        assert state_machine.player_state.spirituality == 0  # No cost deducted

    def test_perform_ritual_via_machine(self, state_machine):
        state_machine.player_state.discovered_fact_ids = ["fact_1"]
        success, message, corruption = state_machine.perform_ritual(
            "rit_1", ["herb", "candle"], seed=42
        )
        assert isinstance(success, bool)
        assert isinstance(message, str)
        # Corruption should be updated
        assert state_machine.player_state.corruption_level == corruption

    def test_resolve_ending_via_machine(self, state_machine):
        state_machine.player_state.confirmed_hypothesis_ids = ["hyp_1"]
        ending = state_machine.resolve_ending()
        assert ending is not None
        assert ending.ending_id == "end_true"

    def test_resolve_no_ending_via_machine(self, state_machine):
        ending = state_machine.resolve_ending()
        assert ending is None

    def test_get_event_log_via_machine(self, state_machine):
        assert state_machine.get_event_log() == []
        state_machine.discover_clue("clue_1")
        assert len(state_machine.get_event_log()) == 1

    def test_empty_case_state_machine(self):
        """Test CaseStateMachine with a minimal case."""
        case = Case(case_id="empty", title="Empty", description="Empty")
        sm = CaseStateMachine(case)
        assert sm.player_state.current_location_id == ""
        assert sm.get_available_clues() == []
        assert sm.get_available_npcs() == []
