"""FastAPI route handlers for Game API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from .database import GameDatabase
from .game_manager import GameManager
from .models import (
    ActionResponse,
    CaseList,
    CaseMetadata,
    GameAction,
    GameView,
    NewGameResponse,
)

router = APIRouter()
manager: GameManager | None = None

ERROR_CODES: dict[str, str] = {
    "NOT_FOUND": "ERR_NOT_FOUND",
    "INVALID_TARGET": "ERR_INVALID_TARGET",
    "INVALID_ACTION": "ERR_INVALID_ACTION",
    "STATE_VERSION_CONFLICT": "ERR_STATE_VERSION_CONFLICT",
    "SAVE_NOT_FOUND": "ERR_SAVE_NOT_FOUND",
    "GAME_ALREADY_OVER": "ERR_GAME_OVER",
    "INTERNAL_ERROR": "ERR_INTERNAL",
}


def init_manager(db: GameDatabase) -> None:
    global manager
    manager = GameManager(db)


@router.get("/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "game-api"}


@router.get("/v1/cases", response_model=CaseList)
async def list_cases() -> CaseList:
    if manager is None:
        raise HTTPException(500, detail="Service not initialized")
    cases_data = manager.list_cases()
    cases = [CaseMetadata(**c) for c in cases_data]
    return CaseList(cases=cases)


@router.get("/v1/cases/{case_id}/metadata", response_model=CaseMetadata)
async def get_case_metadata(case_id: str) -> CaseMetadata:
    if manager is None:
        raise HTTPException(500, detail="Service not initialized")
    metadata = manager.get_case_metadata(case_id)
    if metadata is None:
        raise HTTPException(404, detail=f"Case not found: {case_id}")
    return CaseMetadata(**metadata)


@router.post("/v1/game/new", response_model=NewGameResponse)
async def new_game(case_id: str = "case_clockmaker_01", seed: int | None = None) -> NewGameResponse:
    """Create a new game session."""
    if manager is None:
        raise HTTPException(500, detail="Service not initialized")
    try:
        session = manager.create_game(case_id, seed=seed)
        view = session._make_view()
        return NewGameResponse(
            save_id=session.session_id,
            case_id=session.case_id,
            view=view,
        )
    except ValueError as e:
        raise HTTPException(404, detail=str(e)) from e


@router.post("/v1/game/{save_id}/action", response_model=ActionResponse)
async def handle_action(save_id: str, action: GameAction) -> ActionResponse:
    """Execute a game action for the given save."""
    if manager is None:
        raise HTTPException(500, detail="Service not initialized")
    session = manager.get_session(save_id) or manager.load_session(save_id)
    if session is None:
        raise HTTPException(404, detail=f"Save not found: {save_id}")

    success, error_code, events, ending_id = session.execute_action(action)
    mapped_error = ERROR_CODES.get(error_code, error_code) if error_code else None
    view = session._make_view() if success else None

    return ActionResponse(
        success=success,
        state_version=session.state_version if success else 0,
        events=events,
        view=view,
        error_code=mapped_error,
        error_detail=None,
    )


@router.get("/v1/game/{save_id}/view", response_model=GameView)
async def get_view(save_id: str) -> GameView:
    """Get the current game view without executing an action."""
    if manager is None:
        raise HTTPException(500, detail="Service not initialized")
    session = manager.get_session(save_id) or manager.load_session(save_id)
    if session is None:
        raise HTTPException(404, detail=f"Save not found: {save_id}")
    return session._make_view()


@router.post("/v1/game/{save_id}/save")
async def save_game(save_id: str) -> dict[str, bool | str]:
    """Persist the current game state to SQLite."""
    if manager is None:
        raise HTTPException(500, detail="Service not initialized")
    session = manager.get_session(save_id)
    if session is None:
        raise HTTPException(404, detail=f"Save not found: {save_id}")
    success = manager.save_session(save_id)
    if not success:
        raise HTTPException(500, detail="Failed to save game")
    return {"success": True, "save_id": save_id}


@router.post("/v1/game/{save_id}/load", response_model=GameView)
async def load_game(save_id: str) -> GameView:
    """Load game state from SQLite into memory."""
    if manager is None:
        raise HTTPException(500, detail="Service not initialized")
    session = manager.load_session(save_id)
    if session is None:
        raise HTTPException(404, detail=f"Save not found: {save_id}")
    return session._make_view()


@router.put("/v1/game/{save_id}/view")
async def update_view(save_id: str, _view: GameView) -> GameView:
    """Alias for /view - kept for route compatibility."""
    return await get_view(save_id)


@router.get("/v1/saves")
async def list_saves(case_id: str | None = None) -> dict[str, list[dict[str, Any]]]:
    """List all saved games."""
    if manager is None:
        raise HTTPException(500, detail="Service not initialized")
    saves = manager.list_saves(case_id)
    return {"saves": saves}
