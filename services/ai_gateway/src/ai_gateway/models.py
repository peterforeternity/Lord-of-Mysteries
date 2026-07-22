from __future__ import annotations

import enum

from pydantic import BaseModel, Field


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


class DialogueRequest(BaseModel):
    npc_id: str
    player_utterance: str
    current_scene_id: str = ""
    current_public_event_ids: list[str] = Field(default_factory=list)
    player_revealed_claim_ids: list[str] = Field(default_factory=list)
    relationship_state: str = "neutral"
    emotion_state: str = "neutral"


class DialogueResponse(BaseModel):
    utterance: str
    dialogue_act: DialogueAct
    referenced_claim_ids: list[str] = Field(default_factory=list)
    emotion: Emotion = Emotion.NEUTRAL
    animation_tag: str = ""
    requests_world_action: bool = False
    safety_flags: list[str] = Field(default_factory=list)


class ClassifyIntentRequest(BaseModel):
    player_utterance: str
    context: str = ""


class ClassifyIntentResponse(BaseModel):
    intent: str = "unknown"
    confidence: float = 0.0


class CaseRecapRequest(BaseModel):
    case_id: str
    player_events: list[str] = Field(default_factory=list)
    discovered_facts: list[str] = Field(default_factory=list)


class CaseRecapResponse(BaseModel):
    summary: str = ""
    next_steps: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    services_ready: bool = False


class PromptVersionResponse(BaseModel):
    prompt_version: str = "0.1.0"
    model_version: str = "mock"


class ErrorResponse(BaseModel):
    error_code: str
    detail: str
    path: str = ""
