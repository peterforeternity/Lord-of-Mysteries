from __future__ import annotations

from pathlib import Path

from investigation_core.models import (
    Case,
    EndingType,
    SecrecyLevel,
)
from investigation_core.services import (
    CaseStateMachine,
    SaveRepository,
)


class TestFullPlaythrough:
    """End-to-end game flow tests."""

    def test_full_game_flow(self, sample_case):
        """Complete playthrough: discover clues -> submit hypothesis -> reach ending."""
        sm = CaseStateMachine(sample_case)

        # Move to loc_1 and discover clues
        sm.move_to_location("loc_1")
        success, event = sm.discover_clue("clue_1")
        assert success is True

        success, event = sm.discover_clue("clue_2")
        assert success is True

        # Move to loc_2
        sm.move_to_location("loc_2")
        # Need to complete required event for clue_3
        sm.player_state.completed_events.append("evt_spirit_vision")
        success, event = sm.discover_clue("clue_3")
        assert success is True

        # Verify all clues discovered
        assert len(sm.player_state.discovered_clue_ids) == 3

        # Submit hypothesis - hyp_2 only needs clue_1 and fact_1
        success, event, ending_id = sm.submit_hypothesis("hyp_2")
        assert success is True
        assert ending_id == "end_partial"

        # Check event log
        log = sm.get_event_log()
        assert len(log) == 4  # 3 discoveries + 1 submission
        event_types = [e.event_type for e in log]
        assert event_types.count("clue_discovered") == 3
        assert event_types.count("hypothesis_confirmed") == 1

        # Resolve ending
        ending = sm.resolve_ending()
        assert ending is not None
        assert ending.ending_id == "end_partial"
        assert ending.ending_type == EndingType.PARTIAL_ENDING

    def test_true_ending_path(self, sample_case):
        """Path to true ending requires all clues and correct hypothesis."""
        sm = CaseStateMachine(sample_case)

        # Discover all clues
        sm.move_to_location("loc_1")
        sm.discover_clue("clue_1")
        sm.discover_clue("clue_2")
        sm.move_to_location("loc_2")
        sm.player_state.completed_events.append("evt_spirit_vision")
        sm.discover_clue("clue_3")

        # Submit the correct hypothesis
        success, event, ending_id = sm.submit_hypothesis("hyp_1")
        assert success is True
        assert ending_id == "end_true"

        ending = sm.resolve_ending()
        assert ending is not None
        assert ending.ending_id == "end_true"
        assert ending.ending_type == EndingType.TRUE_ENDING

    def test_corruption_bad_ending_flow(self, sample_case):
        """High corruption leads to bad ending during play."""
        sm = CaseStateMachine(sample_case)
        sm.player_state.corruption_level = 3

        ending = sm.resolve_ending()
        assert ending is not None
        assert ending.ending_id == "end_bad"
        assert ending.ending_type == EndingType.BAD_ENDING

    def test_save_and_load_continuity(self, sample_case):
        """Test that saving and loading preserves game state."""
        sm = CaseStateMachine(sample_case)

        # Make progress
        sm.move_to_location("loc_1")
        sm.discover_clue("clue_1")
        sm.discover_clue("clue_2")

        # Use a real temp dir for save
        import tempfile

        from investigation_core.models import SaveData

        save_dir = Path(tempfile.mkdtemp())
        repo = SaveRepository(save_dir)

        save_data = SaveData(
            save_id="integration_test",
            player_state=sm.player_state,
            event_log=sm.get_event_log(),
            seed=sm.player_state.seed,
        )
        repo.save(save_data, slot=0)

        # Create a new state machine
        sm2 = CaseStateMachine(sample_case)

        # Load the save
        loaded = repo.load(slot=0)
        assert loaded is not None
        sm2.player_state = loaded.player_state
        sm2.event_log.clear()
        for e in loaded.event_log:
            sm2.event_log.add_event(e)

        # Verify state restored
        assert len(sm2.player_state.discovered_clue_ids) == 2
        assert "clue_1" in sm2.player_state.discovered_clue_ids
        assert sm2.player_state.current_location_id == "loc_1"
        assert len(sm2.get_event_log()) == 2

        # Continue playing
        sm2.move_to_location("loc_2")
        sm2.player_state.completed_events.append("evt_spirit_vision")
        sm2.discover_clue("clue_3")
        assert len(sm2.player_state.discovered_clue_ids) == 3

    def test_determinism_across_runs(self, sample_case):
        """Same sequence of operations should produce identical results."""

        def run_sequence(seed: int) -> tuple:
            sm = CaseStateMachine(sample_case)
            sm.player_state.seed = seed
            sm.move_to_location("loc_1")
            sm.discover_clue("clue_1")
            sm.discover_clue("clue_2")
            sm.move_to_location("loc_2")
            sm.player_state.completed_events.append("evt_spirit_vision")
            sm.discover_clue("clue_3")
            success, event, ending_id = sm.submit_hypothesis("hyp_1")
            ending = sm.resolve_ending()
            log_count = len(sm.get_event_log())
            return (
                success,
                ending_id,
                ending.ending_id if ending else None,
                tuple(sm.player_state.discovered_clue_ids),
                tuple(sm.player_state.confirmed_hypothesis_ids),
                log_count,
            )

        r1 = run_sequence(42)
        r2 = run_sequence(42)
        assert r1 == r2

    def test_dual_source_rule(self, sample_case):
        """Core secret facts should be revealed by at least 2 clues."""
        core_secret_facts = [f for f in sample_case.facts if f.secrecy == SecrecyLevel.CORE_SECRET]
        for fact in core_secret_facts:
            assert (
                len(fact.revealed_by_clue_ids) >= 2
            ), f"Core secret fact {fact.fact_id} only has {len(fact.revealed_by_clue_ids)} clue(s)"

    def test_empty_case_flow(self):
        """Test playthrough with an empty case (no clues, no NPCs)."""
        case = Case(case_id="empty", title="Empty", description="Empty")
        sm = CaseStateMachine(case)

        assert sm.get_available_clues() == []
        assert sm.get_available_npcs() == []
        ending = sm.resolve_ending()
        assert ending is None

        sm.move_to_location("somewhere")
        assert sm.player_state.current_location_id == "somewhere"

    def test_invalid_hypothesis_submission_during_play(self, sample_case):
        """Test that invalid hypothesis doesn't crash the flow."""
        sm = CaseStateMachine(sample_case)
        sm.move_to_location("loc_1")
        sm.discover_clue("clue_1")

        # Try submitting wrong hypothesis ID
        success, event, ending_id = sm.submit_hypothesis("nonexistent_hyp")
        assert success is False
        assert event is None
        assert ending_id is None
        # State shouldn't have changed
        assert sm.player_state.confirmed_hypothesis_ids == []

    def test_ritual_during_playthrough(self, sample_case):
        """Execute a ritual during a playthrough session."""
        sm = CaseStateMachine(sample_case)
        sm.move_to_location("loc_1")
        sm.discover_clue("clue_1")

        # Get the knowledge from the clue
        sm.player_state.discovered_fact_ids = ["fact_1"]

        success, message, corruption = sm.perform_ritual("rit_1", ["herb", "candle"], seed=42)
        # Ritual correctness already tested in test_services
        # This validates the state machine wiring
        assert isinstance(success, bool)
        assert isinstance(message, str)

    def test_divination_during_playthrough(self, sample_case):
        """Use divination during a playthrough, verify state updates."""
        sm = CaseStateMachine(sample_case)
        initial_spirituality = sm.player_state.spirituality

        sm.discover_clue("clue_1")
        result = sm.perform_divination("Where is the truth?", seed=123)

        assert isinstance(result.tendency, str)
        assert result.cost >= 0
        assert sm.player_state.spirituality <= initial_spirituality
