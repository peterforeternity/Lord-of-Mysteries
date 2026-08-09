"""Tests for the public proxy server (scripts/serve_public.py).

Uses httpx ASGI transport to test the proxy logic through Starlette.
``httpx.AsyncClient`` is mocked to avoid needing a real upstream server.

All tests use a ``tmp_path``-based dist directory so they never depend
on a local frontend build.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

# Ensure the scripts directory is on sys.path so we can import serve_public
SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import serve_public  # noqa: E402  -- import after sys.path setup

# Save the real AsyncClient before any patches — fixtures that patch
# serve_public.httpx.AsyncClient will also affect httpx.AsyncClient
# in this module (they are the same attribute).  Tests that need to
# create an ASGI transport client must use this saved reference.
_real_async_client = httpx.AsyncClient


class MockAsyncClient:
    """Mock httpx.AsyncClient that records calls and returns canned responses."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self._responses: dict[str, httpx.Response] = {}
        self._raise_connect_error: bool = False

    def set_response(self, method: str, path: str, response: httpx.Response) -> None:
        key = f"{method.upper()} {path}"
        self._responses[key] = response

    async def _do_request(self, method: str, url: str, **kwargs: dict) -> httpx.Response:
        if self._raise_connect_error:
            raise httpx.ConnectError("Connection refused")
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        path = url.split("?", 1)[0]
        return self._responses.get(
            f"{method.upper()} {path}", httpx.Response(200, json={"ok": True})
        )

    async def get(self, url: str, **kwargs: dict) -> httpx.Response:
        return await self._do_request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: dict) -> httpx.Response:
        return await self._do_request("POST", url, **kwargs)

    async def aclose(self) -> None:
        pass


@pytest.fixture
def client(tmp_path):
    """``httpx.AsyncClient`` using ASGI transport — no real HTTP needed.

    The app is created with ``tmp_path`` as the dist directory so tests
    do not depend on a local frontend build.
    """
    app = serve_public.create_app(dist_dir=tmp_path)
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
    return _real_async_client(transport=transport, base_url="http://test")


@pytest.fixture
def mock_httpx():
    """Patch ``serve_public.httpx.AsyncClient`` with a mock that returns canned responses."""
    mock_client = MockAsyncClient()

    def _factory(*args: object, **kwargs: object) -> MockAsyncClient:
        return mock_client

    patcher = patch("serve_public.httpx.AsyncClient", side_effect=_factory)
    patcher.start()
    yield mock_client
    patcher.stop()


@pytest.mark.asyncio
class TestPublicProxy:
    """Verify proxy behavior through the Starlette app."""

    async def test_upstream_unavailable(
        self, client: httpx.AsyncClient, mock_httpx: MockAsyncClient
    ):
        """When upstream raises ConnectError, proxy returns 503."""
        mock_httpx._raise_connect_error = True

        resp = await client.get("/v1/health")
        assert resp.status_code == 503
        data = resp.json()
        assert data["error"] == "API_SERVER_UNAVAILABLE"

    async def test_get_request_forwards_to_upstream(
        self, client: httpx.AsyncClient, mock_httpx: MockAsyncClient
    ):
        """GET request to /v1/game/{id}/view is proxied as GET."""
        mock_httpx.set_response(
            "GET",
            "/v1/game/test_001/view",
            httpx.Response(200, json={"state_version": 1, "game_id": "test_001"}),
        )
        resp = await client.get("/v1/game/test_001/view")
        assert resp.status_code == 200
        data = resp.json()
        assert data["game_id"] == "test_001"
        assert len(mock_httpx.calls) == 1
        assert mock_httpx.calls[0]["method"] == "GET"
        assert "test_001/view" in mock_httpx.calls[0]["url"]

    async def test_post_without_body(self, client: httpx.AsyncClient, mock_httpx: MockAsyncClient):
        """POST without body forwards to upstream."""
        mock_httpx.set_response(
            "POST",
            "/v1/game/test_002/save",
            httpx.Response(200, json={"success": True}),
        )
        resp = await client.post("/v1/game/test_002/save")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(mock_httpx.calls) == 1
        assert mock_httpx.calls[0]["method"] == "POST"

    async def test_post_with_json_body(
        self, client: httpx.AsyncClient, mock_httpx: MockAsyncClient
    ):
        """POST with JSON body forwards content and headers."""
        mock_httpx.set_response(
            "POST",
            "/v1/game/test_003/action",
            httpx.Response(200, json={"success": True, "state_version": 2}),
        )
        resp = await client.post(
            "/v1/game/test_003/action",
            json={"action_type": "inspect", "target_id": "clue_1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        # Verify content-type and content were forwarded
        sent = mock_httpx.calls[0]
        assert "content" in sent["kwargs"]
        request_body = json.loads(sent["kwargs"]["content"])
        assert request_body["action_type"] == "inspect"
        headers = sent["kwargs"].get("headers", {})
        # The forwarded headers dict should contain content-type
        assert headers.get("content-type") == "application/json"

    async def test_post_with_query(self, client: httpx.AsyncClient, mock_httpx: MockAsyncClient):
        """POST with query string preserves parameters."""
        mock_httpx.set_response(
            "POST",
            "/v1/game/new",
            httpx.Response(200, json={"save_id": "query_test_001"}),
        )
        resp = await client.post("/v1/game/new", params={"case_id": "case_clockmaker_01"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["save_id"] == "query_test_001"
        # Verify query string was forwarded in the URL
        sent_url = mock_httpx.calls[0]["url"]
        assert "case_id=case_clockmaker_01" in sent_url

    async def test_upstream_404(self, client: httpx.AsyncClient, mock_httpx: MockAsyncClient):
        """4xx from upstream is forwarded as-is."""
        mock_httpx.set_response(
            "GET",
            "/v1/game/nonexistent/view",
            httpx.Response(404, json={"error": "save_not_found"}),
        )
        resp = await client.get("/v1/game/nonexistent/view")
        assert resp.status_code == 404
        data = resp.json()
        assert data["error"] == "save_not_found"

    async def test_upstream_500(self, client: httpx.AsyncClient, mock_httpx: MockAsyncClient):
        """5xx from upstream is forwarded as-is."""
        mock_httpx.set_response(
            "GET",
            "/v1/game/error/view",
            httpx.Response(500, json={"error": "internal_error"}),
        )
        resp = await client.get("/v1/game/error/view")
        assert resp.status_code == 500
        data = resp.json()
        assert data["error"] == "internal_error"

    async def test_spa_fallback_without_frontend(self, client: httpx.AsyncClient):
        """Non-/v1/ paths return 503 when no frontend is built."""
        resp = await client.get("/some-random-path")
        assert resp.status_code == 503
        data = resp.json()
        assert data["error"] == "FRONTEND_NOT_BUILT"

    async def test_spa_fallback_root_without_frontend(self, client: httpx.AsyncClient):
        """Root path returns 503 when no frontend is built."""
        resp = await client.get("/")
        assert resp.status_code == 503
        data = resp.json()
        assert data["error"] == "FRONTEND_NOT_BUILT"

    async def test_host_header_stripped(
        self, client: httpx.AsyncClient, mock_httpx: MockAsyncClient
    ):
        """Host header is stripped (not forwarded) by the proxy."""
        mock_httpx.set_response(
            "GET",
            "/v1/game/test_005/view",
            httpx.Response(200, json={"ok": True}),
        )
        await client.get(
            "/v1/game/test_005/view",
            headers={"Host": "evil-proxy", "X-Custom": "keep-me"},
        )
        sent = mock_httpx.calls[0]
        headers = sent["kwargs"].get("headers", {})
        # Host should NOT be in forwarded headers key
        forwarded_host = headers.get("host")
        assert forwarded_host is None, f"Host header was forwarded: {forwarded_host}"
        # Custom headers should be forwarded
        assert headers.get("x-custom") == "keep-me"


class TestPublicProxyWithoutDist:
    """Verify the proxy module handles missing frontend dist gracefully."""

    def test_can_import_without_dist(self):
        """Creating app before import succeeds — module-level import already worked."""
        assert hasattr(serve_public, "create_app")

    def test_create_app_with_nonexistent_dist(self, tmp_path: Path):
        """``create_app()`` with a non-existent dist_dir does not crash."""
        app = serve_public.create_app(dist_dir=tmp_path / "nonexistent")
        assert app is not None

    @pytest.mark.asyncio
    async def test_proxy_works_without_dist(self, tmp_path: Path, mock_httpx: MockAsyncClient):
        """/v1/* proxying works even when no frontend dist exists."""
        app = serve_public.create_app(dist_dir=tmp_path / "nonexistent")
        transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
        mock_httpx.set_response(
            "GET",
            "/v1/health",
            httpx.Response(200, json={"status": "ok"}),
        )
        async with _real_async_client(transport=transport, base_url="http://test") as client:
            resp = await client.get("/v1/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_root_returns_503_without_dist(self, tmp_path: Path):
        """Accessing root without dist returns FRONTEND_NOT_BUILT."""
        app = serve_public.create_app(dist_dir=tmp_path / "nonexistent")
        transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
        async with _real_async_client(transport=transport, base_url="http://test") as client:
            resp = await client.get("/")
            assert resp.status_code == 503
            data = resp.json()
            assert data["error"] == "FRONTEND_NOT_BUILT"

    @pytest.mark.asyncio
    async def test_static_assets_mounted_when_dir_exists(self, tmp_path: Path):
        """Static assets mount correctly when the assets directory exists."""
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir(parents=True)
        (assets_dir / "test.css").write_text("body { color: red; }")
        app = serve_public.create_app(dist_dir=tmp_path)
        transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
        async with _real_async_client(transport=transport, base_url="http://test") as client:
            resp = await client.get("/assets/test.css")
            assert resp.status_code == 200
            assert "text/css" in resp.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_spa_returns_503_without_dist(self, tmp_path: Path):
        """Non-API paths without dist return 503, not a crash."""
        app = serve_public.create_app(dist_dir=tmp_path / "nonexistent")
        transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
        async with _real_async_client(transport=transport, base_url="http://test") as client:
            resp = await client.get("/some-random-path")
            assert resp.status_code == 503
            data = resp.json()
            assert data["error"] == "FRONTEND_NOT_BUILT"
