from __future__ import annotations

import json
import random
from datetime import UTC, datetime
from pathlib import Path

from .models import (
    NPC,
    AnomalousItem,
    Case,
    CaseEvent,
    Claim,
    Clue,
    DivinationInput,
    DivinationResult,
    Ending,
    EndingType,
    Fact,
    Hypothesis,
    HypothesisStatus,
    PlayerCaseState,
    Ritual,
    SaveData,
)


class CaseLoader:
    """Loads case data from JSON files."""

    def __init__(self, case_dir: Path) -> None:
        self.case_dir = case_dir

    def load_case(self) -> Case:
        case_path = self.case_dir / "case.json"
        facts_path = self.case_dir / "facts.secret.json"
        claims_path = self.case_dir / "claims.json"
        clues_path = self.case_dir / "clues.json"
        hypotheses_path = self.case_dir / "hypotheses.json"
        npcs_path = self.case_dir / "npcs.json"

        with open(case_path) as f:
            case_data = json.load(f)
        with open(facts_path) as f:
            facts_data = json.load(f)
        with open(claims_path) as f:
            claims_data = json.load(f)
        with open(clues_path) as f:
            clues_data = json.load(f)
        with open(hypotheses_path) as f:
            hypotheses_data = json.load(f)
        with open(npcs_path) as f:
            npcs_data = json.load(f)

        # Load optional files
        rituals: list[Ritual] = []
        items: list[AnomalousItem] = []
        rituals_path = self.case_dir / "rituals.json"
        items_path = self.case_dir / "items.json"
        if rituals_path.exists():
            with open(rituals_path) as f:
                rituals_data = json.load(f)
            rituals = [Ritual(**r) for r in rituals_data]
        if items_path.exists():
            with open(items_path) as f:
                items_data = json.load(f)
            items = [AnomalousItem(**i) for i in items_data]

        case = Case(
            case_id=case_data["case_id"],
            title=case_data["title"],
            description=case_data.get("description", ""),
            version=case_data.get("version", "0.1.0"),
            facts=[Fact(**f) for f in facts_data],
            claims=[Claim(**c) for c in claims_data],
            clues=[Clue(**c) for c in clues_data],
            npcs=[NPC(**n) for n in npcs_data],
            hypotheses=[Hypothesis(**h) for h in hypotheses_data],
            endings=[Ending(**e) for e in case_data.get("endings", [])],
            rituals=rituals,
            items=items,
            initial_scene_id=case_data.get("initial_scene_id", ""),
        )
        return case


class ClueDiscoveryService:
    """Handles clue discovery logic."""

    @staticmethod
    def discover_clue(
        case: Case, state: PlayerCaseState, clue_id: str
    ) -> tuple[bool, CaseEvent | None]:
        if clue_id in state.discovered_clue_ids:
            return False, None

        clue = next((c for c in case.clues if c.clue_id == clue_id), None)
        if clue is None:
            return False, None

        # Check required tags
        if clue.requires_any_tags and not any(
            tag in state.completed_events for tag in clue.requires_any_tags
        ):
            return False, None

        state.discovered_clue_ids.append(clue_id)

        # Reveal related facts
        for fact_id in clue.reveals_fact_ids:
            if fact_id not in state.discovered_fact_ids:
                state.discovered_fact_ids.append(fact_id)

        event = CaseEvent(
            event_id=(f"evt_discover_{clue_id}_" f"{datetime.now(UTC).timestamp()}"),
            case_id=case.case_id,
            event_type="clue_discovered",
            description=f"Discovered clue: {clue.display_name}",
            involved_clue_ids=[clue_id],
        )
        return True, event


class HypothesisEvaluationService:
    """Evaluates player-submitted hypotheses with contradiction handling."""

    @staticmethod
    def submit_hypothesis(
        case: Case, state: PlayerCaseState, hypothesis_id: str
    ) -> tuple[bool, CaseEvent | None, str | None]:
        hypothesis = next((h for h in case.hypotheses if h.hypothesis_id == hypothesis_id), None)
        if hypothesis is None:
            return False, None, None

        # Check required clues
        has_all_clues = all(
            cid in state.discovered_clue_ids for cid in hypothesis.required_clue_ids
        )
        if not has_all_clues:
            return False, None, None

        # Check required facts
        has_all_facts = all(
            fid in state.discovered_fact_ids for fid in hypothesis.required_fact_ids
        )
        if not has_all_facts:
            return False, None, None

        # Auto-reject if any contradicting fact is discovered
        for fid in hypothesis.contradicting_fact_ids:
            if fid in state.discovered_fact_ids:
                hypothesis.status = HypothesisStatus.REJECTED
                state.rejected_hypothesis_ids.append(hypothesis_id)
                event = CaseEvent(
                    event_id=(
                        f"evt_hypothesis_{hypothesis_id}_" f"{datetime.now(UTC).timestamp()}"
                    ),
                    case_id=case.case_id,
                    event_type="hypothesis_rejected",
                    description=(
                        f"Hypothesis rejected by contradictory fact: " f"{hypothesis.title}"
                    ),
                )
                return False, event, None

        # Compute confidence
        confidence = sum(
            next((c.strength for c in case.clues if c.clue_id == cid), 0)
            for cid in hypothesis.required_clue_ids
            if cid in state.discovered_clue_ids
        )

        # Add bonus for supporting facts
        for fid in hypothesis.supporting_fact_ids:
            if fid in state.discovered_fact_ids:
                confidence += 2

        # Subtract penalty for contradicting clues
        for cid in hypothesis.contradicting_clue_ids:
            if cid in state.discovered_clue_ids:
                clue = next((c for c in case.clues if c.clue_id == cid), None)
                if clue:
                    confidence -= clue.strength

        if confidence < hypothesis.min_confidence:
            return False, None, None

        hypothesis.status = HypothesisStatus.CONFIRMED
        state.confirmed_hypothesis_ids.append(hypothesis_id)

        event = CaseEvent(
            event_id=(f"evt_hypothesis_{hypothesis_id}_" f"{datetime.now(UTC).timestamp()}"),
            case_id=case.case_id,
            event_type="hypothesis_confirmed",
            description=(hypothesis.success_result or f"Confirmed hypothesis: {hypothesis.title}"),
        )
        return True, event, hypothesis.leads_to_ending_id


class DivinationService:
    """Performs deterministic divination."""

    @staticmethod
    def perform_divination(
        case: Case, state: PlayerCaseState, input_data: DivinationInput
    ) -> DivinationResult:
        rng = random.Random(input_data.seed)

        # Check if player has enough spirituality
        if input_data.current_spirituality <= 0:
            return DivinationResult(
                tendency="失败",
                symbolic_image="灵性耗尽，无法看到任何画面",
                confidence=1,
                cost=0,
                is_interfered=True,
            )

        # Check for interference
        has_interference = input_data.corruption_level >= 3 or input_data.scene_interference >= 2
        base_confidence = max(1, 5 - input_data.corruption_level - input_data.scene_interference)

        # Generate symbolic image based on discovered clues
        discovered = [c for c in case.clues if c.clue_id in state.discovered_clue_ids]
        if not discovered:
            return DivinationResult(
                tendency="迷雾",
                symbolic_image="灰雾弥漫，什么都看不清。你需要更多线索。",
                confidence=base_confidence,
                cost=1,
                is_interfered=has_interference,
            )

        # Pick a random clue for the vision
        chosen = rng.choice(discovered)
        tendency = "正确方向" if not has_interference else "受到干扰"
        symbolic_image = f"在灰雾中，你看到{chosen.display_name}的影像若隐若现。"

        if has_interference:
            symbolic_image += " 但画面扭曲不清，仿佛被某种力量污染。"

        return DivinationResult(
            tendency=tendency,
            symbolic_image=symbolic_image,
            confidence=base_confidence,
            cost=1,
            is_interfered=has_interference,
        )


class EndingResolver:
    """Resolves ending based on player state."""

    @staticmethod
    def resolve_ending(case: Case, state: PlayerCaseState) -> Ending | None:
        # Check which hypothesis was confirmed
        confirmed_ending_id: str | None = None
        for h in case.hypotheses:
            if h.hypothesis_id in state.confirmed_hypothesis_ids:
                confirmed_ending_id = h.leads_to_ending_id
                break

        # Evaluate each ending
        possible_endings: list[Ending] = []
        for ending in case.endings:
            if (
                (confirmed_ending_id and ending.ending_id == confirmed_ending_id)
                or (
                    ending.required_hypothesis_id
                    and ending.required_hypothesis_id in state.confirmed_hypothesis_ids
                )
                or (
                    not ending.required_hypothesis_id
                    and not confirmed_ending_id
                    and ending.corruption_threshold is not None
                    and state.corruption_level >= ending.corruption_threshold
                )
            ):
                possible_endings.append(ending)

        if possible_endings:
            # Return the best match: confirmed > corruption-based
            for e in possible_endings:
                if e.ending_type == EndingType.TRUE_ENDING:
                    return e
            for e in possible_endings:
                if e.ending_type == EndingType.PARTIAL_ENDING:
                    return e
            return possible_endings[0]

        # Default: bad ending if high corruption
        if state.corruption_level >= 3:
            bad = next(
                (e for e in case.endings if e.ending_type == EndingType.BAD_ENDING),
                None,
            )
            if bad:
                return bad

        return None


class RitualValidationService:
    """Validates ritual execution."""

    @staticmethod
    def validate_ritual(
        case: Case,
        state: PlayerCaseState,
        ritual_id: str,
        provided_materials: list[str],
        seed: int,
    ) -> tuple[bool, str, int]:
        ritual = next((r for r in case.rituals if r.ritual_id == ritual_id), None)
        if ritual is None:
            return False, "未知的仪式", 0

        # Check materials
        has_all_materials = all(m in provided_materials for m in ritual.required_materials)
        if not has_all_materials:
            return (
                False,
                f"材料不足：需要 {', '.join(ritual.required_materials)}",
                0,
            )

        # Check knowledge
        has_knowledge = all(
            kid in state.discovered_fact_ids for kid in ritual.required_knowledge_ids
        )
        if not has_knowledge:
            return False, "缺少必要的知识来执行这个仪式", 0

        # Determine outcome
        rng = random.Random(seed)
        success = rng.random() > 0.3  # 70% base success rate

        if success:
            return True, ritual.success_result, ritual.corruption_change
        else:
            return (
                False,
                f"仪式失败。{ritual.failure_result}",
                ritual.corruption_change + 1,
            )


class EventLog:
    """Maintains an immutable event log."""

    def __init__(self) -> None:
        self._events: list[CaseEvent] = []

    def add_event(self, event: CaseEvent) -> None:
        self._events.append(event)

    def get_events(self, case_id: str | None = None) -> list[CaseEvent]:
        if case_id:
            return [e for e in self._events if e.case_id == case_id]
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()

    def get_event_count(self) -> int:
        return len(self._events)


class SaveRepository:
    """Manages save/load of game state."""

    def __init__(self, save_dir: Path) -> None:
        self.save_dir = save_dir
        save_dir.mkdir(parents=True, exist_ok=True)

    def save(self, save_data: SaveData, slot: int = 0) -> Path:
        path = self.save_dir / f"save_{slot}.json"
        with open(path, "w") as f:
            json.dump(save_data.model_dump(mode="json"), f, indent=2, default=str)
        return path

    def load(self, slot: int = 0) -> SaveData | None:
        path = self.save_dir / f"save_{slot}.json"
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        return SaveData(**data)

    def list_saves(self) -> list[int]:
        return sorted([int(p.stem.split("_")[1]) for p in self.save_dir.glob("save_*.json")])


class CaseStateMachine:
    """Orchestrates overall case state transitions."""

    def __init__(self, case: Case) -> None:
        self.case = case
        self.player_state = PlayerCaseState(
            case_id=case.case_id,
            current_location_id=case.initial_scene_id,
            seed=0,
        )
        self.event_log = EventLog()
        self.clue_service = ClueDiscoveryService()
        self.hypothesis_service = HypothesisEvaluationService()
        self.divination_service = DivinationService()
        self.ritual_service = RitualValidationService()
        self.ending_resolver = EndingResolver()

    def get_available_clues(self) -> list[Clue]:
        """Return clues available at current location."""
        return [
            c
            for c in self.case.clues
            if c.location_id == self.player_state.current_location_id
            and c.clue_id not in self.player_state.discovered_clue_ids
        ]

    def get_discovered_clues(self) -> list[Clue]:
        """Return clues already discovered."""
        return [c for c in self.case.clues if c.clue_id in self.player_state.discovered_clue_ids]

    def get_available_npcs(self) -> list[NPC]:
        """Return NPCs available at current location."""
        return [
            n
            for n in self.case.npcs
            if n.initial_location_id == self.player_state.current_location_id
            and self.player_state.npc_available.get(n.npc_id, True)
        ]

    def get_npc_claims(self, npc_id: str) -> list[Claim]:
        """Return claims an NPC can share (whitelist)."""
        npc = next((n for n in self.case.npcs if n.npc_id == npc_id), None)
        if npc is None:
            return []
        return [
            c
            for c in self.case.claims
            if c.claim_id in npc.known_claim_ids and c.speaker_npc_id == npc_id
        ]

    def get_revealed_claims(self) -> list[Claim]:
        """Return claims the player has heard."""
        return [c for c in self.case.claims if c.claim_id in self.player_state.revealed_claim_ids]

    def move_to_location(self, location_id: str) -> bool:
        self.player_state.current_location_id = location_id
        if location_id not in self.player_state.visited_location_ids:
            self.player_state.visited_location_ids.append(location_id)
        return True

    def discover_clue(self, clue_id: str) -> tuple[bool, CaseEvent | None]:
        success, event = self.clue_service.discover_clue(self.case, self.player_state, clue_id)
        if event:
            self.event_log.add_event(event)
        return success, event

    def submit_hypothesis(self, hypothesis_id: str) -> tuple[bool, CaseEvent | None, str | None]:
        success, event, ending_id = self.hypothesis_service.submit_hypothesis(
            self.case, self.player_state, hypothesis_id
        )
        if event:
            self.event_log.add_event(event)
        return success, event, ending_id

    def perform_divination(self, question: str, seed: int) -> DivinationResult:
        input_data = DivinationInput(
            question_template=question,
            obtained_clue_ids=self.player_state.discovered_clue_ids,
            current_spirituality=self.player_state.spirituality,
            corruption_level=self.player_state.corruption_level,
            seed=seed,
        )
        result = self.divination_service.perform_divination(
            self.case, self.player_state, input_data
        )
        self.player_state.spirituality = max(0, self.player_state.spirituality - result.cost)
        return result

    def perform_ritual(
        self, ritual_id: str, materials: list[str], seed: int
    ) -> tuple[bool, str, int]:
        success, message, corruption = self.ritual_service.validate_ritual(
            self.case, self.player_state, ritual_id, materials, seed
        )
        self.player_state.corruption_level += corruption
        return success, message, corruption

    def resolve_ending(self) -> Ending | None:
        return self.ending_resolver.resolve_ending(self.case, self.player_state)

    def get_event_log(self) -> list[CaseEvent]:
        return self.event_log.get_events(self.case.case_id)
