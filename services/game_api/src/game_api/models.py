"""Pydantic models for Game API request/response schemas."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Error codes (unified)
# ---------------------------------------------------------------------------

ERROR_INVALID_TARGET = "INVALID_TARGET"
ERROR_TARGET_NOT_VISIBLE = "TARGET_NOT_VISIBLE"
ERROR_TARGET_NOT_AVAILABLE = "TARGET_NOT_AVAILABLE"
ERROR_ACTION_NOT_ALLOWED = "ACTION_NOT_ALLOWED"
ERROR_STATE_VERSION_CONFLICT = "STATE_VERSION_CONFLICT"
ERROR_INVALID_PARAMETERS = "INVALID_PARAMETERS"
ERROR_RESOURCE_INSUFFICIENT = "RESOURCE_INSUFFICIENT"
ERROR_GAME_ALREADY_FINISHED = "GAME_ALREADY_FINISHED"
ERROR_SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
ERROR_RATE_LIMITED = "RATE_LIMITED"
ERROR_IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
ERROR_INTERNAL = "INTERNAL_ERROR"


class ActionType(str, Enum):
    TRAVEL = "travel"
    INSPECT = "inspect"
    TALK = "talk"
    USE_SPIRIT_VISION = "use_spirit_vision"
    PERFORM_DIVINATION = "perform_divination"
    PERFORM_RITUAL = "perform_ritual"
    USE_ITEM = "use_item"
    SUBMIT_HYPOTHESIS = "submit_hypothesis"
    REST = "rest"
    SAVE = "save"
    LOAD = "load"
    DISMISS_RESOLUTION = "dismiss_resolution_hint"


class ActionInfo(BaseModel):
    """Structured description of an available action for the client."""

    action_id: str
    action_type: str
    target_id: str | None = None
    label: str
    enabled: bool = True
    disabled_reason: str | None = None
    expected_version: int = 0
    parameters_schema: dict[str, Any] = Field(default_factory=dict)


class GameAction(BaseModel):
    """A player action submitted to the game engine."""

    action_type: ActionType
    target_id: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    expected_version: int = 0
    idempotency_key: str = ""


class RecoveryInfo(BaseModel):
    """Recovery hint returned with recoverable errors."""

    refresh_view: bool = True
    latest_state_version: int = 0


class ActionResponse(BaseModel):
    """Returned after every action attempt."""

    success: bool
    state_version: int = 0
    events: list[dict[str, Any]] = Field(default_factory=list)
    view: GameView | None = None
    error_code: str | None = None
    error_detail: str | None = None
    request_id: str = ""
    recoverable: bool = True
    recovery: RecoveryInfo | None = None


class GameErrorResponse(BaseModel):
    """Unified error response for non-action endpoints."""

    success: bool = False
    error_code: str
    message: str
    request_id: str
    recoverable: bool = False
    recovery: RecoveryInfo | None = None


class ClueInfo(BaseModel):
    """Public clue info for the view."""

    clue_id: str
    display_name: str
    description: str
    source_type: str
    is_new: bool = False


class NpcInfo(BaseModel):
    """Public NPC info for the view."""

    npc_id: str
    name: str
    description: str
    emotion: str
    current_location_id: str
    available_claims: list[ClaimInfo] = Field(default_factory=list)


class ClaimInfo(BaseModel):
    """Public claim info for the view."""

    claim_id: str
    content: str
    is_lie: bool = False
    speaker_believes_it: bool = True


class LocationInfo(BaseModel):
    """Public location info for the view."""

    location_id: str
    display_name: str
    description: str
    is_current: bool = False
    has_been_visited: bool = False
    available_clues: list[ClueInfo] = Field(default_factory=list)
    available_npcs: list[str] = Field(default_factory=list)


class HypothesisInfo(BaseModel):
    """Public hypothesis info for the view."""

    hypothesis_id: str
    title: str
    description: str
    status: str
    min_confidence: int
    required_clue_count: int
    found_clue_count: int
    can_submit: bool


class EndingInfo(BaseModel):
    """Public ending info."""

    ending_id: str
    title: str
    description: str
    ending_type: str


class ItemInfo(BaseModel):
    """Public item info for the view."""

    item_id: str
    name: str
    description: str
    active_ability: str
    holding_cost: str


class RitualInfo(BaseModel):
    """Public ritual info for the view."""

    ritual_id: str
    name: str
    purpose: str
    required_materials: list[str]
    space_condition: str
    steps: list[str]
    can_perform: bool = False


class PlayerStatus(BaseModel):
    """Player resource status."""

    spirituality: int
    corruption: int
    stability: int
    current_location_id: str
    current_location_name: str = ""
    visited_locations: list[LocationInfo] = Field(default_factory=list)


class EventLogEntry(BaseModel):
    """A single event in the event log."""

    event_id: str
    event_type: str
    description: str
    timestamp: str


class EvidenceDimension(BaseModel):
    """Status of a single evidence dimension."""

    dimension_id: str
    label: str
    total: int
    found: int
    status_label: str  # 尚无发现 / 出现疑点 / 线索增加 / 相互印证 / 基本明确


class InvestigationProgress(BaseModel):
    """Safe investigation progress summary for the client.

    Must NOT leak: ending_id, candidate_id, required_clues,
    missing_clues, correct_hypothesis, or unlock_conditions.
    """

    phase_level: int  # 0-3
    phase_label: str  # 迷雾初现 / 线索浮现 / 疑点交汇 / 接近真相
    evidence_dimensions: list[EvidenceDimension] = Field(default_factory=list)
    recent_discoveries: list[str] = Field(default_factory=list)  # up to 3 recent clue display names
    open_questions: list[str] = Field(default_factory=list)
    resolution_available: bool = False
    new_resolution_available: bool = False


class GameView(BaseModel):
    """The complete game state view returned to the client.

    The client must NOT derive authority from this view;
    all state mutations must go through actions.
    """

    state_version: int
    player: PlayerStatus = Field(
        default_factory=lambda: PlayerStatus(
            spirituality=5,
            corruption=0,
            stability=5,
            current_location_id="",
        )
    )
    current_scene: str = ""
    current_description: str = ""
    available_actions: list[ActionInfo] = Field(default_factory=list)
    clues: list[ClueInfo] = Field(default_factory=list)
    npcs: list[NpcInfo] = Field(default_factory=list)
    hypotheses: list[HypothesisInfo] = Field(default_factory=list)
    endings: list[EndingInfo] = Field(default_factory=list)
    items: list[ItemInfo] = Field(default_factory=list)
    rituals: list[RitualInfo] = Field(default_factory=list)
    event_log: list[EventLogEntry] = Field(default_factory=list)
    investigation_progress: InvestigationProgress | None = None
    game_over: bool = False
    final_ending: EndingInfo | None = None
    ai_enabled: bool = False


class CaseMetadata(BaseModel):
    """Public case metadata for case selection."""

    case_id: str
    title: str
    description: str
    version: str


class CaseList(BaseModel):
    """List of available cases."""

    cases: list[CaseMetadata]


class NewGameResponse(BaseModel):
    """Response after creating a new game."""

    save_id: str
    case_id: str
    view: GameView
