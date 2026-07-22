from __future__ import annotations

import enum
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class TruthStatus(str, enum.Enum):
    TRUE = "true"
    FALSE = "false"
    PARTIAL = "partial"
    MISLEADING = "misleading"


class SecrecyLevel(str, enum.Enum):
    PUBLIC = "public"
    RESTRICTED = "restricted"
    CORE_SECRET = "core_secret"


class ClueSourceType(str, enum.Enum):
    ENVIRONMENT = "environment"
    NPC_STATEMENT = "npc_statement"
    DOCUMENT = "document"
    EXPERIMENT = "experiment"
    DEDUCTION = "deduction"


class DialogueAct(str, enum.Enum):
    ANSWER = "answer"
    ANSWER_PARTIAL = "answer_partial"
    ASK = "ask"
    REFUSE = "refuse"
    EVADE = "evade"
    INSIST = "insist"
    CHANGE_TOPIC = "change_topic"
    GREET = "greet"
    FAREWELL = "farewell"
    FALLBACK = "fallback"


class Emotion(str, enum.Enum):
    NEUTRAL = "neutral"
    GUARDED = "guarded"
    FRIENDLY = "friendly"
    HOSTILE = "hostile"
    ANXIOUS = "anxious"
    SAD = "sad"
    SURPRISED = "surprised"
    ANGRY = "angry"


class EndingType(str, enum.Enum):
    TRUE_ENDING = "true_ending"
    PARTIAL_ENDING = "partial_ending"
    BAD_ENDING = "bad_ending"


class HypothesisStatus(str, enum.Enum):
    UNSUBMITTED = "unsubmitted"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class Fact(BaseModel):
    fact_id: str
    case_id: str
    summary: str
    truth: bool
    secrecy: SecrecyLevel = SecrecyLevel.RESTRICTED
    prerequisite_fact_ids: list[str] = Field(default_factory=list)
    revealed_by_clue_ids: list[str] = Field(default_factory=list)


class Claim(BaseModel):
    claim_id: str
    speaker_npc_id: str
    content: str
    truth_status: TruthStatus
    speaker_believes_it: bool = True
    available_when: list[str] = Field(default_factory=list)
    forbidden_when: list[str] = Field(default_factory=list)
    strength: int = Field(default=1, ge=1, le=3)


class Clue(BaseModel):
    clue_id: str
    case_id: str
    display_name: str
    description: str = ""
    source_type: ClueSourceType = ClueSourceType.ENVIRONMENT
    location_id: str = ""
    reveals_fact_ids: list[str] = Field(default_factory=list)
    requires_any_tags: list[str] = Field(default_factory=list)
    requires_all_tags: list[str] = Field(default_factory=list)
    strength: int = Field(default=1, ge=1, le=3)
    missable: bool = False


class NPCPersonality(BaseModel):
    formality: float = Field(default=0.5, ge=0.0, le=1.0)
    anxiety: float = Field(default=0.5, ge=0.0, le=1.0)
    aggression: float = Field(default=0.5, ge=0.0, le=1.0)


class NPC(BaseModel):
    npc_id: str
    name: str
    description: str = ""
    role: str = "core"
    known_claim_ids: list[str] = Field(default_factory=list)
    lie_claim_ids: list[str] = Field(default_factory=list)
    forbidden_fact_ids: list[str] = Field(default_factory=list)
    personality: NPCPersonality = Field(default_factory=NPCPersonality)
    initial_location_id: str = ""
    default_emotion: Emotion = Emotion.NEUTRAL


class Hypothesis(BaseModel):
    hypothesis_id: str
    case_id: str
    title: str
    description: str = ""
    required_clue_ids: list[str] = Field(default_factory=list)
    required_fact_ids: list[str] = Field(default_factory=list)
    supporting_fact_ids: list[str] = Field(default_factory=list)
    contradicting_clue_ids: list[str] = Field(default_factory=list)
    contradicting_fact_ids: list[str] = Field(default_factory=list)
    min_confidence: int = Field(default=1, ge=1, le=10)
    leads_to_ending_id: str = ""
    success_result: str = ""
    failure_result: str = ""
    status: HypothesisStatus = HypothesisStatus.UNSUBMITTED


class Ending(BaseModel):
    ending_id: str
    case_id: str
    title: str
    description: str
    ending_type: EndingType
    required_hypothesis_id: str = ""
    trigger_conditions: list[str] = Field(default_factory=list)
    corruption_threshold: int | None = None


class Ritual(BaseModel):
    ritual_id: str
    name: str
    purpose: str
    required_knowledge_ids: list[str] = Field(default_factory=list)
    required_materials: list[str] = Field(default_factory=list)
    space_condition: str = ""
    time_condition: str = ""
    steps: list[str] = Field(default_factory=list)
    success_result: str = ""
    failure_result: str = ""
    corruption_change: int = 0
    may_alert_entities: list[str] = Field(default_factory=list)


class DivinationInput(BaseModel):
    question_template: str
    obtained_clue_ids: list[str] = Field(default_factory=list)
    medium: str = ""
    current_spirituality: int = 5
    corruption_level: int = 0
    scene_interference: int = 0
    seed: int = 0


class DivinationResult(BaseModel):
    tendency: str
    symbolic_image: str
    confidence: int = Field(ge=1, le=5)
    cost: int = 1
    is_interfered: bool = False


class AnomalousItem(BaseModel):
    item_id: str
    name: str
    description: str
    active_ability: str = ""
    passive_ability: str = ""
    use_condition: str = ""
    fixed_cost: str = ""
    holding_cost: str = ""
    violation_condition: str = ""
    penalty: str = ""
    cooldown: int = 0


class NPCMemory(BaseModel):
    memory_id: str
    npc_id: str
    event_id: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    visibility: str = "public"
    involved_entities: list[str] = Field(default_factory=list)


class CaseEvent(BaseModel):
    event_id: str
    case_id: str
    event_type: str
    description: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    involved_npc_ids: list[str] = Field(default_factory=list)
    involved_clue_ids: list[str] = Field(default_factory=list)


class PlayerCaseState(BaseModel):
    case_id: str
    discovered_clue_ids: list[str] = Field(default_factory=list)
    confirmed_hypothesis_ids: list[str] = Field(default_factory=list)
    rejected_hypothesis_ids: list[str] = Field(default_factory=list)
    current_location_id: str = ""
    visited_location_ids: list[str] = Field(default_factory=list)
    npc_relationship: dict[str, str] = Field(default_factory=dict)
    npc_available: dict[str, bool] = Field(default_factory=dict)
    corruption_level: int = 0
    spirituality: int = 5
    stability: int = 5
    completed_events: list[str] = Field(default_factory=list)
    seed: int = 0
    revealed_claim_ids: list[str] = Field(default_factory=list)
    discovered_fact_ids: list[str] = Field(default_factory=list)


class Case(BaseModel):
    case_id: str
    title: str
    description: str
    version: str = "0.1.0"
    facts: list[Fact] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    clues: list[Clue] = Field(default_factory=list)
    npcs: list[NPC] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    endings: list[Ending] = Field(default_factory=list)
    rituals: list[Ritual] = Field(default_factory=list)
    items: list[AnomalousItem] = Field(default_factory=list)
    initial_scene_id: str = ""


class DialogueResponse(BaseModel):
    utterance: str
    dialogue_act: DialogueAct
    referenced_claim_ids: list[str] = Field(default_factory=list)
    emotion: Emotion = Emotion.NEUTRAL
    animation_tag: str = ""
    requests_world_action: bool = False
    safety_flags: list[str] = Field(default_factory=list)


class SaveData(BaseModel):
    save_id: str
    player_state: PlayerCaseState
    event_log: list[CaseEvent] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    seed: int = 0
