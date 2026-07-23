"""FastAPI route handlers for Game API."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response

from .database import GameDatabase
from .game_manager import GameManager
from .logging import RequestTimer, log_event
from .models import (
    ERROR_GAME_ALREADY_FINISHED,
    ERROR_INTERNAL,
    ERROR_INVALID_TARGET,
    ERROR_SESSION_NOT_FOUND,
    ERROR_STATE_VERSION_CONFLICT,
    ActionResponse,
    CaseList,
    CaseMetadata,
    GameAction,
    GameErrorResponse,
    GameView,
    NewGameResponse,
    RecoveryInfo,
)

router = APIRouter()
manager: GameManager | None = None


def _get_request_id(request: Request) -> str:
    """Get or generate X-Request-ID."""
    return request.headers.get("X-Request-ID", uuid.uuid4().hex)


def _get_session_id(request: Request, save_id: str = "") -> str:
    """Get X-Session-ID from headers or fall back to save_id."""
    return request.headers.get("X-Session-ID", save_id)


def _unify_error(
    error_code: str,
    message: str,
    request_id: str,
    recoverable: bool = False,
    latest_state_version: int = 0,
) -> GameErrorResponse:
    """Build a unified error response model."""
    recovery: RecoveryInfo | None = None
    if recoverable:
        recovery = RecoveryInfo(refresh_view=True, latest_state_version=latest_state_version)
    return GameErrorResponse(
        error_code=error_code,
        message=message,
        request_id=request_id,
        recoverable=recoverable,
        recovery=recovery,
    )


def init_manager(db: GameDatabase) -> None:
    global manager
    manager = GameManager(db)


@router.get("/v1/health")
async def health(request: Request, response: Response) -> dict[str, str]:
    request_id = _get_request_id(request)
    timer = RequestTimer()
    timer.start()
    response.headers["X-Request-ID"] = request_id
    log_event(
        level="INFO",
        request_id=request_id,
        route="/v1/health",
        method="GET",
        status_code=200,
        duration_ms=timer.elapsed_ms(),
        message="Health check",
    )
    return {"status": "ok", "service": "game-api"}


@router.get("/v1/cases", response_model=CaseList)
async def list_cases(request: Request, response: Response) -> CaseList:
    request_id = _get_request_id(request)
    timer = RequestTimer()
    timer.start()
    response.headers["X-Request-ID"] = request_id
    if manager is None:
        log_event(
            level="ERROR",
            request_id=request_id,
            route="/v1/cases",
            method="GET",
            status_code=500,
            duration_ms=timer.elapsed_ms(),
            error_code=ERROR_INTERNAL,
            message="Service not initialized",
        )
        raise HTTPException(500, detail="Service not initialized")
    cases_data = manager.list_cases()
    cases = [CaseMetadata(**c) for c in cases_data]
    log_event(
        level="INFO",
        request_id=request_id,
        route="/v1/cases",
        method="GET",
        status_code=200,
        duration_ms=timer.elapsed_ms(),
        message=f"Listed {len(cases)} cases",
    )
    return CaseList(cases=cases)


@router.get("/v1/cases/{case_id}/metadata", response_model=CaseMetadata)
async def get_case_metadata(case_id: str, request: Request, response: Response) -> CaseMetadata:
    request_id = _get_request_id(request)
    timer = RequestTimer()
    timer.start()
    response.headers["X-Request-ID"] = request_id
    if manager is None:
        raise HTTPException(500, detail="Service not initialized")
    metadata = manager.get_case_metadata(case_id)
    if metadata is None:
        raise HTTPException(404, detail=f"Case not found: {case_id}")
    log_event(
        level="INFO",
        request_id=request_id,
        route=f"/v1/cases/{case_id}/metadata",
        method="GET",
        status_code=200,
        duration_ms=timer.elapsed_ms(),
    )
    return CaseMetadata(**metadata)


@router.post("/v1/game/new", response_model=NewGameResponse)
async def new_game(
    request: Request,
    response: Response,
    case_id: str = "case_clockmaker_01",
    seed: int | None = None,
) -> NewGameResponse:
    """Create a new game session."""
    request_id = _get_request_id(request)
    timer = RequestTimer()
    timer.start()
    response.headers["X-Request-ID"] = request_id
    if manager is None:
        raise HTTPException(500, detail="Service not initialized")
    try:
        session = manager.create_game(case_id, seed=seed)
        view = session._make_view()
        log_event(
            level="INFO",
            request_id=request_id,
            session_id=session.session_id,
            route="/v1/game/new",
            method="POST",
            status_code=200,
            duration_ms=timer.elapsed_ms(),
            message=f"Created game {session.session_id}",
        )
        return NewGameResponse(
            save_id=session.session_id,
            case_id=session.case_id,
            view=view,
        )
    except ValueError as e:
        error_resp = _unify_error(
            error_code=ERROR_INVALID_TARGET,
            message=str(e),
            request_id=request_id,
        )
        log_event(
            level="WARNING",
            request_id=request_id,
            route="/v1/game/new",
            method="POST",
            status_code=404,
            duration_ms=timer.elapsed_ms(),
            error_code=ERROR_INVALID_TARGET,
            message=str(e),
        )
        raise HTTPException(404, detail=error_resp.model_dump()) from e


@router.post("/v1/game/{save_id}/action", response_model=ActionResponse)
async def handle_action(
    save_id: str,
    action: GameAction,
    request: Request,
    response: Response,
) -> ActionResponse:
    """Execute a game action for the given save."""
    request_id = _get_request_id(request)
    session_id = _get_session_id(request, save_id)
    timer = RequestTimer()
    timer.start()
    response.headers["X-Request-ID"] = request_id

    if manager is None:
        log_event(
            level="ERROR",
            request_id=request_id,
            session_id=session_id,
            route=f"/v1/game/{save_id}/action",
            method="POST",
            status_code=500,
            duration_ms=timer.elapsed_ms(),
            error_code=ERROR_INTERNAL,
            message="Service not initialized",
        )
        raise HTTPException(500, detail="Service not initialized")

    session = manager.get_session(save_id) or manager.load_session(save_id)
    if session is None:
        error_resp = _unify_error(
            error_code=ERROR_SESSION_NOT_FOUND,
            message=f"Save not found: {save_id}",
            request_id=request_id,
        )
        log_event(
            level="WARNING",
            request_id=request_id,
            session_id=session_id,
            route=f"/v1/game/{save_id}/action",
            method="POST",
            status_code=404,
            duration_ms=timer.elapsed_ms(),
            error_code=ERROR_SESSION_NOT_FOUND,
            message=f"Save not found: {save_id}",
        )
        raise HTTPException(404, detail=error_resp.model_dump())

    success, error_code, events, ending_id = session.execute_action(action)
    view = session._make_view() if success else None

    # Determine if recoverable
    recoverable = error_code in (
        ERROR_STATE_VERSION_CONFLICT,
        ERROR_INVALID_TARGET,
        ERROR_GAME_ALREADY_FINISHED,
    )

    recovery: RecoveryInfo | None = None
    if recoverable:
        recovery = RecoveryInfo(refresh_view=True, latest_state_version=session.state_version)

    log_event(
        level="INFO" if success else "WARNING",
        request_id=request_id,
        session_id=session_id,
        route=f"/v1/game/{save_id}/action",
        method="POST",
        status_code=200,
        duration_ms=timer.elapsed_ms(),
        action_type=action.action_type.value,
        target_id=action.target_id,
        state_version=session.state_version,
        error_code=error_code or "",
        message=f"Action {action.action_type.value}: {'success' if success else 'failed'}",
    )

    return ActionResponse(
        success=success,
        state_version=session.state_version,
        events=events,
        view=view,
        error_code=error_code,
        error_detail=None,
        request_id=request_id,
        recoverable=recoverable,
        recovery=recovery,
    )


@router.get("/v1/game/{save_id}/view", response_model=GameView)
async def get_view(
    save_id: str,
    request: Request,
    response: Response,
) -> GameView:
    """Get the current game view without executing an action."""
    request_id = _get_request_id(request)
    session_id = _get_session_id(request, save_id)
    timer = RequestTimer()
    timer.start()
    response.headers["X-Request-ID"] = request_id

    if manager is None:
        raise HTTPException(500, detail="Service not initialized")
    session = manager.get_session(save_id) or manager.load_session(save_id)
    if session is None:
        error_resp = _unify_error(
            error_code=ERROR_SESSION_NOT_FOUND,
            message=f"Save not found: {save_id}",
            request_id=request_id,
        )
        raise HTTPException(404, detail=error_resp.model_dump())

    log_event(
        level="INFO",
        request_id=request_id,
        session_id=session_id,
        route=f"/v1/game/{save_id}/view",
        method="GET",
        status_code=200,
        duration_ms=timer.elapsed_ms(),
        message="Get view",
    )
    return session._make_view()


@router.post("/v1/game/{save_id}/save")
async def save_game(
    save_id: str,
    request: Request,
    response: Response,
) -> dict[str, bool | str]:
    """Persist the current game state to SQLite."""
    request_id = _get_request_id(request)
    session_id = _get_session_id(request, save_id)
    timer = RequestTimer()
    timer.start()
    response.headers["X-Request-ID"] = request_id

    if manager is None:
        raise HTTPException(500, detail="Service not initialized")
    session = manager.get_session(save_id)
    if session is None:
        error_resp = _unify_error(
            error_code=ERROR_SESSION_NOT_FOUND,
            message=f"Save not found: {save_id}",
            request_id=request_id,
        )
        raise HTTPException(404, detail=error_resp.model_dump())
    success = manager.save_session(save_id)
    if not success:
        error_resp = _unify_error(
            error_code=ERROR_INTERNAL,
            message="Failed to save game",
            request_id=request_id,
        )
        raise HTTPException(500, detail=error_resp.model_dump())

    log_event(
        level="INFO",
        request_id=request_id,
        session_id=session_id,
        route=f"/v1/game/{save_id}/save",
        method="POST",
        status_code=200,
        duration_ms=timer.elapsed_ms(),
        message="Game saved",
    )
    return {"success": True, "save_id": save_id, "request_id": request_id}


@router.post("/v1/game/{save_id}/load", response_model=GameView)
async def load_game(
    save_id: str,
    request: Request,
    response: Response,
) -> GameView:
    """Load game state from SQLite into memory."""
    request_id = _get_request_id(request)
    session_id = _get_session_id(request, save_id)
    timer = RequestTimer()
    timer.start()
    response.headers["X-Request-ID"] = request_id

    if manager is None:
        raise HTTPException(500, detail="Service not initialized")
    session = manager.load_session(save_id)
    if session is None:
        error_resp = _unify_error(
            error_code=ERROR_SESSION_NOT_FOUND,
            message=f"Save not found: {save_id}",
            request_id=request_id,
        )
        raise HTTPException(404, detail=error_resp.model_dump())

    log_event(
        level="INFO",
        request_id=request_id,
        session_id=session_id,
        route=f"/v1/game/{save_id}/load",
        method="POST",
        status_code=200,
        duration_ms=timer.elapsed_ms(),
        message="Game loaded",
    )
    return session._make_view()


@router.put("/v1/game/{save_id}/view")
async def update_view(
    save_id: str,
    _view: GameView,
    request: Request,
    response: Response,
) -> GameView:
    """Alias for /view - kept for route compatibility."""
    return await get_view(save_id, request, response)


@router.get("/v1/saves")
async def list_saves(
    request: Request,
    response: Response,
    case_id: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """List all saved games."""
    request_id = _get_request_id(request)
    timer = RequestTimer()
    timer.start()
    response.headers["X-Request-ID"] = request_id

    if manager is None:
        raise HTTPException(500, detail="Service not initialized")
    saves = manager.list_saves(case_id)

    log_event(
        level="INFO",
        request_id=request_id,
        route="/v1/saves",
        method="GET",
        status_code=200,
        duration_ms=timer.elapsed_ms(),
        message=f"Listed {len(saves)} saves",
    )
    return {"saves": saves}
