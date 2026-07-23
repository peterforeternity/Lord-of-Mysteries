"""Tests for idempotency_key support.

Tests cover:
- Same save_id + same key + same action → cached on second call
- Cached response state_version does not increase
- Different save_ids with same key do not interfere
- Same key + different action → IDEMPOTENCY_CONFLICT
- Requests without idempotency_key still work normally
- Failed actions are not cached
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create_game(client: TestClient) -> str:
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    return resp.json()["save_id"]


def test_same_key_same_action_returns_cached(client: TestClient):
    """Same save_id + same idempotency_key + same action:
    first call succeeds, second call returns cached response."""
    save_id = _create_game(client)

    action = {
        "action_type": "travel",
        "target_id": "police_office",
        "expected_version": 0,
        "idempotency_key": "travel-police-1",
    }

    # First call: should execute and succeed
    resp1 = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["success"] is True
    assert data1["view"]["player"]["current_location_id"] == "police_office"

    # Second call: should return cached (same key, same action)
    resp2 = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["success"] is True
    assert data2["view"]["player"]["current_location_id"] == "police_office"

    # Both responses should be identical
    assert data1 == data2


def test_cached_response_state_version_not_increased(client: TestClient):
    """Cached response's state_version should not increase
    because no actual execution happened."""
    save_id = _create_game(client)

    action = {
        "action_type": "travel",
        "target_id": "police_office",
        "expected_version": 0,
        "idempotency_key": "travel-police-v2",
    }

    # First call
    resp1 = client.post(f"/v1/game/{save_id}/action", json=action)
    data1 = resp1.json()
    assert data1["state_version"] == 1

    # Second call (cached): state_version should still be 1
    resp2 = client.post(f"/v1/game/{save_id}/action", json=action)
    data2 = resp2.json()
    assert data2["state_version"] == data1["state_version"]


def test_different_save_ids_no_interference(client: TestClient):
    """Different save_ids with the same idempotency_key should
    not interfere with each other."""
    save_id1 = _create_game(client)
    save_id2 = _create_game(client)

    action1 = {
        "action_type": "travel",
        "target_id": "police_office",
        "expected_version": 0,
        "idempotency_key": "same-key",
    }
    action2 = {
        "action_type": "travel",
        "target_id": "clinic",
        "expected_version": 0,
        "idempotency_key": "same-key",
    }

    resp1 = client.post(f"/v1/game/{save_id1}/action", json=action1)
    assert resp1.status_code == 200
    assert resp1.json()["view"]["player"]["current_location_id"] == "police_office"

    resp2 = client.post(f"/v1/game/{save_id2}/action", json=action2)
    assert resp2.status_code == 200
    assert resp2.json()["view"]["player"]["current_location_id"] == "clinic"


def test_same_key_different_action_conflict(client: TestClient):
    """Same save_id + same idempotency_key but different action
    → IDEMPOTENCY_CONFLICT."""
    save_id = _create_game(client)

    action_first = {
        "action_type": "travel",
        "target_id": "police_office",
        "expected_version": 0,
        "idempotency_key": "conflict-key",
    }

    # First action
    resp1 = client.post(f"/v1/game/{save_id}/action", json=action_first)
    assert resp1.status_code == 200
    assert resp1.json()["success"] is True

    # Same key, different action
    action_second = {
        "action_type": "travel",
        "target_id": "clinic",
        "expected_version": 0,
        "idempotency_key": "conflict-key",
    }
    resp2 = client.post(f"/v1/game/{save_id}/action", json=action_second)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["success"] is False
    assert data2["error_code"] == "IDEMPOTENCY_CONFLICT"
    assert data2["recoverable"] is False


def test_without_idempotency_key_still_works(client: TestClient):
    """Requests without idempotency_key should execute normally."""
    save_id = _create_game(client)

    action = {
        "action_type": "travel",
        "target_id": "police_office",
        "expected_version": 0,
    }

    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["view"]["player"]["current_location_id"] == "police_office"


def test_failed_action_not_cached(client: TestClient):
    """A failed action with idempotency_key should NOT be cached,
    so retrying with the same key should re-execute (and may succeed
    or fail on its own merits)."""
    save_id = _create_game(client)

    # Use wrong expected_version to trigger a failure
    action = {
        "action_type": "travel",
        "target_id": "police_office",
        "expected_version": 99,
        "idempotency_key": "fail-and-retry",
    }

    resp1 = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["success"] is False
    assert data1["error_code"] == "STATE_VERSION_CONFLICT"

    # Retry with correct expected_version: should execute fresh (not cached)
    action["expected_version"] = 0
    resp2 = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["success"] is True
    assert data2["view"]["player"]["current_location_id"] == "police_office"
