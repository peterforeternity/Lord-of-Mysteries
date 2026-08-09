"""Combined public server — serves static frontend and proxies API calls.

Usage:
    python scripts/serve_public.py

Requires:
    - Game API running on 127.0.0.1:8000
    - Static frontend built at apps/web/dist/

The module-level ``app`` is created via ``create_app()`` at import time.
If ``apps/web/dist/assets`` does not exist, static assets are simply not
mounted — the API proxy works regardless.  This allows tests to import
this module without a frontend build.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

# Paths — these are safe to use at module level (no I/O at import time)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "apps" / "web" / "dist"
API_BASE = "http://127.0.0.1:8000"


async def api_proxy(request: Request) -> Response:
    """Proxy /v1/* requests to Game API.

    Forwards method, body, Content-Type, Content-Length, and query string.
    Removes hop-by-hop headers (host, connection, transfer-encoding)
    so the upstream receives a clean request on 8000, not the public port.
    """
    path = request.url.path
    query = request.url.query

    headers = dict(request.headers)
    for h in ("host", "connection", "transfer-encoding"):
        headers.pop(h, None)

    body: bytes | None = None
    if request.method == "POST":
        body = await request.body()
        if "content-type" in request.headers:
            headers["content-type"] = request.headers["content-type"]
        if "content-length" in request.headers:
            headers["content-length"] = request.headers["content-length"]

    client = httpx.AsyncClient(base_url=API_BASE, timeout=30.0)
    try:
        full_path = path + (f"?{query}" if query else "")
        if request.method == "GET":
            resp = await client.get(full_path, headers=headers)
        elif request.method == "POST":
            resp = await client.post(full_path, content=body, headers=headers)
        else:
            return JSONResponse({"error": "Method not allowed"}, status_code=405)

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
        )
    except httpx.ConnectError as e:
        return JSONResponse(
            {
                "error": "API_SERVER_UNAVAILABLE",
                "detail": f"Game API at {API_BASE} is not running: {e}",
            },
            status_code=503,
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return JSONResponse(
            {"error": "PROXY_ERROR", "detail": f"{type(e).__name__}: {e}"},
            status_code=502,
        )
    finally:
        await client.aclose()


async def health(_request: Request) -> JSONResponse:
    """Combined health check."""
    api_healthy = False
    async with httpx.AsyncClient(base_url=API_BASE, timeout=5.0) as client:
        try:
            r = await client.get("/v1/health")
            api_healthy = r.status_code == 200
        except Exception:
            pass

    return JSONResponse(
        {
            "status": "ok" if api_healthy else "degraded",
            "service": "public-demo",
            "api_backend": "healthy" if api_healthy else "unavailable",
            "frontend_built": (DIST_DIR / "index.html").exists(),
        }
    )


def create_app(
    *,
    dist_dir: Path = DIST_DIR,
) -> Starlette:
    """Create the Starlette application.

    Parameters
    ----------
    dist_dir : Path
        Directory containing ``index.html`` and ``assets/``
        (default ``apps/web/dist``).

    Static assets (``/assets``) are **only** mounted when the directory
    exists.  The API proxy (``/v1/*``) and health endpoint are always
    available, so tests can import this module without a frontend build.
    """
    index_html = dist_dir / "index.html"
    assets_dir = dist_dir / "assets"

    # Routes that are always available
    routes: list[Route | Mount] = [
        Route("/health", endpoint=health, methods=["GET"]),
        Route("/v1/{path:path}", endpoint=api_proxy, methods=["GET", "POST"]),
    ]

    # Static assets — only mount when the build output exists
    if assets_dir.is_dir():
        routes.append(
            Mount(
                "/assets",
                app=StaticFiles(directory=str(assets_dir)),
                name="assets",
            )
        )

    # SPA fallback — serve index.html or return a clear error
    async def spa_fallback(_request: Request) -> Response:
        if not index_html.exists():
            return JSONResponse(
                {
                    "error": "FRONTEND_NOT_BUILT",
                    "detail": "Run 'cd apps/web && npm run build' first",
                },
                status_code=503,
            )
        return FileResponse(str(index_html))

    routes.append(Route("/{path:path}", endpoint=spa_fallback, methods=["GET"]))
    routes.append(Route("/", endpoint=spa_fallback, methods=["GET"]))

    return Starlette(debug=False, routes=routes)


# Module-level app instance — safe because create_app() handles
# missing dist/assets gracefully.
app = create_app()


def main() -> None:
    import uvicorn

    port = int(os.environ.get("PUBLIC_PORT", "8080"))
    host = os.environ.get("PUBLIC_HOST", "127.0.0.1")

    if not DIST_DIR.exists():
        sys.stderr.write("Error: Frontend not built. Run: cd apps/web && npm run build\n")
        sys.exit(1)
    if not (DIST_DIR / "index.html").exists():
        sys.stderr.write(f"Error: {DIST_DIR / 'index.html'} not found. Check build output.\n")
        sys.exit(1)

    sys.stderr.write("Starting public demo server...\n")
    sys.stderr.write(f"  Frontend: file://{DIST_DIR}\n")
    sys.stderr.write(f"  API proxy: {API_BASE}\n")
    sys.stderr.write(f"  Listening: http://{host}:{port}\n")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
