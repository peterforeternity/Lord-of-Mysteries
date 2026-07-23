"""Game API — FastAPI application for 诡秘之主 text-based MVP."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="诡秘之主 - Game API",
    version="0.1.0",
    description="Browser-based investigation text game API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins in dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .database import GameDatabase
from .models import ERROR_INTERNAL, ERROR_SESSION_NOT_FOUND
from .routes import init_manager, router

app.include_router(router)

# Initialize with default database path
DB_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "game_saves.db"

db = GameDatabase(DB_PATH)
init_manager(db)


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    error_code = ERROR_INTERNAL
    if exc.status_code == 404:
        error_code = ERROR_SESSION_NOT_FOUND
    elif exc.status_code == 422:
        error_code = "VALIDATION_FAILED"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": error_code,
            "detail": exc.detail,
            "path": str(request.url.path),
        },
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error_code": ERROR_INTERNAL,
            "detail": str(exc) if exc else "Internal server error",
            "path": str(request.url.path),
        },
    )
