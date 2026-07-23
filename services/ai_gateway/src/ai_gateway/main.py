from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI(
    title="诡秘之主 - AI Gateway",
    version="0.1.0",
    description="Constrained AI dialogue gateway for investigation RPG",
)

from .router import ERROR_CODES, init_services, router

app.include_router(router)

# Try to init with default case path
CASE_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "content"
    / "cases"
    / "case_clockmaker_01"
)
if CASE_DIR.exists():
    init_services(CASE_DIR)


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    error_code = ERROR_CODES.get("INTERNAL_ERROR", "ERR_INTERNAL")
    if exc.status_code == 404:
        error_code = "ERR_NOT_FOUND"
    elif exc.status_code == 422:
        error_code = "ERR_VALIDATION_FAILED"
    elif exc.status_code == 429:
        error_code = "ERR_RATE_LIMITED"
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
            "error_code": "ERR_INTERNAL",
            "detail": str(exc) if exc else "Internal server error",
            "path": str(request.url.path),
        },
    )
