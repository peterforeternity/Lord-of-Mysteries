"""Combined public server — serves static frontend and proxies API calls.

Usage:
    python scripts/serve_public.py

Requires:
    - Game API running on 127.0.0.1:8000
    - Static frontend built at apps/web/dist/
"""

import os
import sys
from pathlib import Path

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "apps" / "web" / "dist"
API_BASE = "http://127.0.0.1:8000"

INDEX_HTML = DIST_DIR / "index.html"


async def api_proxy(request: Request) -> Response:
    """Proxy /v1/* requests to Game API."""
    path = request.url.path
    query = request.url.query

    # Extract and forward headers
    headers = dict(request.headers)
    # Remove hop-by-hop headers
    for h in ("host", "connection", "transfer-encoding"):
        headers.pop(h, None)

    client = httpx.AsyncClient(base_url=API_BASE, timeout=30.0)
    try:
        if request.method == "GET":
            resp = await client.get(
                path + (f"?{query}" if query else ""),
                headers=headers,
            )
        elif request.method == "POST":
            body = await request.body()
            resp = await client.post(
                path + (f"?{query}" if query else ""),
                content=body,
                headers=dict(request.headers),
            )
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
        return JSONResponse(
            {"error": "PROXY_ERROR", "detail": str(e)},
            status_code=502,
        )
    finally:
        await client.aclose()


async def serve_index(_request: Request) -> Response:
    """Serve index.html for SPA routes."""
    if not INDEX_HTML.exists():
        return JSONResponse(
            {
                "error": "FRONTEND_NOT_BUILT",
                "detail": "Run 'cd apps/web && npm run build' first",
            },
            status_code=500,
        )
    return FileResponse(str(INDEX_HTML))


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
            "frontend_built": INDEX_HTML.exists(),
        }
    )


# Routes
routes = [
    Route("/health", endpoint=health, methods=["GET"]),
    Route("/v1/health", endpoint=api_proxy, methods=["GET"]),
    # API routes
    Route("/v1/game/{path:path}", endpoint=api_proxy, methods=["GET", "POST"]),
    # Static assets
    Mount(
        "/assets",
        app=StaticFiles(directory=str(DIST_DIR / "assets")),
        name="assets",
    ),
    # All other routes → index.html (SPA fallback)
    Route("/{path:path}", endpoint=serve_index, methods=["GET"]),
    Route("/", endpoint=serve_index, methods=["GET"]),
]

app = Starlette(debug=False, routes=routes)


def main() -> None:
    import uvicorn

    port = int(os.environ.get("PUBLIC_PORT", "8080"))
    host = os.environ.get("PUBLIC_HOST", "127.0.0.1")

    if not DIST_DIR.exists():
        sys.stderr.write("Error: Frontend not built. Run: cd apps/web && npm run build\n")
        sys.exit(1)
    if not INDEX_HTML.exists():
        sys.stderr.write(f"Error: {INDEX_HTML} not found. Check build output.\n")
        sys.exit(1)

    sys.stderr.write("Starting public demo server...\n")
    sys.stderr.write(f"  Frontend: file://{DIST_DIR}\n")
    sys.stderr.write(f"  API proxy: {API_BASE}\n")
    sys.stderr.write(f"  Listening: http://{host}:{port}\n")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
