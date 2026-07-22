import json
import tempfile
from pathlib import Path

import pytest

from investigation_core.models import (
    NPC,
    AnomalousItem,
    Case,
    Claim,
    Clue,
    ClueSourceType,
    Ending,
    EndingType,
    Fact,
    Hypothesis,
    NPCPersonality,
    Ritual,
    SecrecyLevel,
    TruthStatus,
)
from investigation_core.services import (
    CaseStateMachine,
    SaveRepository,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_case():
    """Create a minimal test case."""
    facts = [
        Fact(
            fact_id="fact_1",
            case_id="test_case",
            summary="Test fact 1",
            truth=True,
            secrecy=SecrecyLevel.PUBLIC,
            revealed_by_clue_ids=["clue_1"],
        ),
        Fact(
            fact_id="fact_2",
            case_id="test_case",
            summary="Core secret fact",
            truth=True,
            secrecy=SecrecyLevel.CORE_SECRET,
            revealed_by_clue_ids=["clue_2", "clue_3"],
        ),
        Fact(
            fact_id="fact_3",
            case_id="test_case",
            summary="Test fact 3",
            truth=True,
            secrecy=SecrecyLevel.RESTRICTED,
            revealed_by_clue_ids=["clue_3"],
        ),
    ]
    claims = [
        Claim(
            claim_id="claim_1",
            speaker_npc_id="npc_1",
            content="NPC 1 says X",
            truth_status=TruthStatus.TRUE,
            available_when=["evt_start"],
        ),
        Claim(
            claim_id="claim_2",
            speaker_npc_id="npc_1",
            content="NPC 1 lies about Y",
            truth_status=TruthStatus.FALSE,
            speaker_believes_it=False,
        ),
        Claim(
            claim_id="claim_3",
            speaker_npc_id="npc_2",
            content="NPC 2 says Z",
            truth_status=TruthStatus.PARTIAL,
        ),
    ]
    clues = [
        Clue(
            clue_id="clue_1",
            case_id="test_case",
            display_name="Clue 1",
            source_type=ClueSourceType.ENVIRONMENT,
            location_id="loc_1",
            reveals_fact_ids=["fact_1"],
            strength=1,
        ),
        Clue(
            clue_id="clue_2",
            case_id="test_case",
            display_name="Clue 2",
            source_type=ClueSourceType.NPC_STATEMENT,
            location_id="loc_1",
            reveals_fact_ids=["fact_2"],
            strength=2,
        ),
        Clue(
            clue_id="clue_3",
            case_id="test_case",
            display_name="Clue 3",
            source_type=ClueSourceType.DOCUMENT,
            location_id="loc_2",
            reveals_fact_ids=["fact_2", "fact_3"],
            strength=3,
            requires_any_tags=["evt_spirit_vision"],
        ),
    ]
    npcs = [
        NPC(
            npc_id="npc_1",
            name="NPC One",
            description="First NPC",
            role="core",
            known_claim_ids=["claim_1", "claim_2"],
            lie_claim_ids=["claim_2"],
            forbidden_fact_ids=["fact_2"],
            personality=NPCPersonality(formality=0.5, anxiety=0.3, aggression=0.2),
            initial_location_id="loc_1",
        ),
        NPC(
            npc_id="npc_2",
            name="NPC Two",
            description="Second NPC",
            role="core",
            known_claim_ids=["claim_3"],
            lie_claim_ids=[],
            forbidden_fact_ids=[],
            personality=NPCPersonality(formality=0.8, anxiety=0.1, aggression=0.1),
            initial_location_id="loc_2",
        ),
    ]
    hypotheses = [
        Hypothesis(
            hypothesis_id="hyp_1",
            case_id="test_case",
            title="Hypothesis A",
            description="The truth hypothesis",
            required_clue_ids=["clue_1", "clue_2", "clue_3"],
            required_fact_ids=["fact_1", "fact_2"],
            supporting_fact_ids=[],
            contradicting_clue_ids=[],
            contradicting_fact_ids=[],
            min_confidence=3,
            leads_to_ending_id="end_true",
            success_result="Confirmed: Hypothesis A",
            failure_result="Insufficient evidence for Hypothesis A",
        ),
        Hypothesis(
            hypothesis_id="hyp_2",
            case_id="test_case",
            title="Hypothesis B",
            description="Simple hypothesis",
            required_clue_ids=["clue_1"],
            required_fact_ids=["fact_1"],
            supporting_fact_ids=[],
            contradicting_clue_ids=[],
            contradicting_fact_ids=[],
            min_confidence=1,
            leads_to_ending_id="end_partial",
            success_result="Confirmed: Hypothesis B",
            failure_result="",
        ),
    ]
    endings = [
        Ending(
            ending_id="end_true",
            case_id="test_case",
            title="True Ending",
            description="You solved it.",
            ending_type=EndingType.TRUE_ENDING,
            required_hypothesis_id="hyp_1",
        ),
        Ending(
            ending_id="end_partial",
            case_id="test_case",
            title="Partial Ending",
            description="Partial resolution.",
            ending_type=EndingType.PARTIAL_ENDING,
            required_hypothesis_id="hyp_2",
        ),
        Ending(
            ending_id="end_bad",
            case_id="test_case",
            title="Bad Ending",
            description="Everything went wrong.",
            ending_type=EndingType.BAD_ENDING,
            required_hypothesis_id="",
            corruption_threshold=3,
        ),
    ]
    rituals = [
        Ritual(
            ritual_id="rit_1",
            name="Test Ritual",
            purpose="Test",
            required_knowledge_ids=["fact_1"],
            required_materials=["herb", "candle"],
            space_condition="loc_1",
            time_condition="night",
            steps=["Step 1"],
            success_result="Success!",
            failure_result="Failed.",
            corruption_change=1,
        ),
    ]
    items = [
        AnomalousItem(
            item_id="item_1",
            name="Mystery Box",
            description="A strange box",
            active_ability="See visions",
            fixed_cost="1 spirituality",
            holding_cost="+1 corruption per hour",
            cooldown=3,
        ),
    ]
    return Case(
        case_id="test_case",
        title="Test Case",
        description="A test case",
        version="0.1.0",
        facts=facts,
        claims=claims,
        clues=clues,
        npcs=npcs,
        hypotheses=hypotheses,
        endings=endings,
        rituals=rituals,
        items=items,
        initial_scene_id="loc_1",
    )


@pytest.fixture
def state_machine(sample_case):
    return CaseStateMachine(sample_case)


@pytest.fixture
def sample_case_dir(temp_dir, sample_case):
    """Write sample case data to a temp directory."""
    case_dir = temp_dir / "cases" / "test_case"
    case_dir.mkdir(parents=True)

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
            indent=2,
        )
    with open(case_dir / "facts.secret.json", "w") as f:
        json.dump([f.model_dump() for f in sample_case.facts], f, indent=2)
    with open(case_dir / "claims.json", "w") as f:
        json.dump([c.model_dump() for c in sample_case.claims], f, indent=2)
    with open(case_dir / "clues.json", "w") as f:
        json.dump([c.model_dump() for c in sample_case.clues], f, indent=2)
    with open(case_dir / "hypotheses.json", "w") as f:
        json.dump([h.model_dump() for h in sample_case.hypotheses], f, indent=2)
    with open(case_dir / "npcs.json", "w") as f:
        json.dump([n.model_dump() for n in sample_case.npcs], f, indent=2)

    return case_dir


@pytest.fixture
def save_repo(temp_dir):
    return SaveRepository(temp_dir / "saves")
