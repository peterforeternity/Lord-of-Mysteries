from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from .context_assembler import ContextAssembler
from .fact_leak import FactLeakValidator
from .fallback import FallbackDialogueService
from .knowledge_boundary import KnowledgeBoundaryFilter
from .metrics import RequestMetrics
from .mock_provider import MockLLMProvider
from .models import (
    CaseRecapRequest,
    CaseRecapResponse,
    ClassifyIntentRequest,
    ClassifyIntentResponse,
    DialogueRequest,
    DialogueResponse,
    HealthResponse,
    PromptVersionResponse,
)
from .prompt_builder import DialoguePromptBuilder
from .prompt_registry import PromptVersionRegistry
from .validator import StructuredOutputValidator

router = APIRouter()

# Standard error codes
ERROR_CODES = {
    "UNKNOWN_NPC": "ERR_NPC_NOT_FOUND",
    "UNKNOWN_CASE": "ERR_CASE_NOT_FOUND",
    "VALIDATION_FAILED": "ERR_VALIDATION_FAILED",
    "SERVICE_NOT_READY": "ERR_SERVICE_NOT_READY",
    "INTERNAL_ERROR": "ERR_INTERNAL",
    "PROMPT_INJECTION": "ERR_PROMPT_INJECTION",
    "UNAUTHORIZED_CLAIM": "ERR_UNAUTHORIZED_CLAIM",
    "FACT_LEAK": "ERR_FACT_LEAK",
    "RATE_LIMITED": "ERR_RATE_LIMITED",
}

# Lazy initialization
_provider: MockLLMProvider = MockLLMProvider()
_context_assembler: ContextAssembler = ContextAssembler()
_knowledge_filter: KnowledgeBoundaryFilter = KnowledgeBoundaryFilter()
_prompt_builder: DialoguePromptBuilder = DialoguePromptBuilder()
_validator: StructuredOutputValidator = StructuredOutputValidator()
_fact_leak: FactLeakValidator = FactLeakValidator()
_fallback: FallbackDialogueService = FallbackDialogueService()
_registry: PromptVersionRegistry = PromptVersionRegistry()
_metrics: RequestMetrics = RequestMetrics()
_services_initialized: bool = False


def init_services(case_dir: Path) -> None:
    global _context_assembler, _knowledge_filter, _fact_leak, _fallback, _provider, _services_initialized
    _context_assembler = ContextAssembler(case_dir)
    _knowledge_filter = KnowledgeBoundaryFilter(case_dir)

    secrets_path = case_dir / "facts.secret.json"
    _fact_leak = FactLeakValidator(secrets_path)

    fallback_path = case_dir / "fallback_dialogue.json"
    _fallback = FallbackDialogueService(fallback_path)
    _provider = MockLLMProvider(fallback_path)
    _services_initialized = True


@router.post("/v1/dialogue/respond", response_model=DialogueResponse)
async def dialogue_respond(request: DialogueRequest) -> DialogueResponse:
    start = time.time()

    try:
        # Assemble minimal context
        context = _context_assembler.assemble(request)

        # Try AI provider
        response = await _provider.generate_dialogue(request, context)

        # Validate output
        validated = _validator.validate_dict(response.model_dump())
        if validated is None:
            response = _fallback.get_fallback(request.npc_id, "unknowable")
            _metrics.record_request((time.time() - start) * 1000, False, True)
            return response

        # Filter referenced claims
        filtered_ids = _knowledge_filter.filter_referenced_claims(
            request.npc_id, validated.referenced_claim_ids
        )
        validated.referenced_claim_ids = filtered_ids

        # Check for fact leaks
        safety_flags = _fact_leak.check_leak(validated.utterance, validated.referenced_claim_ids)
        validated.safety_flags = safety_flags

        # Ensure no world actions
        validated.requests_world_action = False

        if safety_flags:
            response = _fallback.get_fallback(request.npc_id, "unknowable")
            _metrics.record_request((time.time() - start) * 1000, False, True)
            return response

        _metrics.record_request((time.time() - start) * 1000, True)
        return validated

    except Exception:
        response = _fallback.get_fallback(request.npc_id, "unknowable")
        _metrics.record_request((time.time() - start) * 1000, False, True)
        return response


@router.post("/v1/dialogue/classify-intent", response_model=ClassifyIntentResponse)
async def classify_intent(request: ClassifyIntentRequest) -> ClassifyIntentResponse:
    intent, confidence = await _provider.classify_intent(request.player_utterance, request.context)
    return ClassifyIntentResponse(intent=intent, confidence=confidence)


@router.post("/v1/case/recap", response_model=CaseRecapResponse)
async def case_recap(request: CaseRecapRequest) -> CaseRecapResponse:
    summary, next_steps = await _provider.generate_recap(
        request.case_id, request.player_events, request.discovered_facts
    )
    return CaseRecapResponse(summary=summary, next_steps=next_steps)


@router.get("/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok" if _services_initialized else "degraded",
        version="0.1.0",
        services_ready=_services_initialized,
    )


@router.get("/v1/prompt-version", response_model=PromptVersionResponse)
async def prompt_version() -> PromptVersionResponse:
    versions = _registry.get_versions()
    return PromptVersionResponse(
        prompt_version=versions["prompt_version"],
        model_version=versions["model_version"],
    )


@router.get("/v1/metrics")
async def get_metrics() -> dict[str, Any]:
    return _metrics.get_summary()
