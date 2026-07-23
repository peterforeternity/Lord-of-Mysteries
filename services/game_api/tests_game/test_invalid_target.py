"""Tests for invalid target handling in Game API.

Covers 15 scenarios:
1.  Nonexistent target_id returns INVALID_TARGET
2.  Location change makes old location targets unavailable
3.  Old state_version returns STATE_VERSION_CONFLICT
4.  Save/load cycle restores game state
5.  Duplicate inspect (after success) fails
6.  target_id is null
7.  target_id is empty string
8.  target_id uses display name instead of ID
9.  Nonexistent action_type
10. Game over blocks subsequent actions
11. Rapid double-click of same action
12. Rapid double-click of two different actions
13. Browser back with stale action
14. Get view after API timeout
15. Error response doesn't crash the page
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from investigation_core import CaseLoader

import game_api.routes as routes

# ---------------------------------------------------------------------------
# Test 1: 不存在 target_id 返回 INVALID_TARGET
# ---------------------------------------------------------------------------


def test_1_nonexistent_target_id(client: TestClient):
    """提交一个当前地点 available_actions 中没有的 target_id 应返回 INVALID_TARGET."""
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    save_id = resp.json()["save_id"]

    action = {
        "action_type": "inspect",
        "target_id": "nonexistent_clue",
        "expected_version": 0,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error_code"] == "INVALID_TARGET"


# ---------------------------------------------------------------------------
# Test 2: 地点切换后旧地点 target 不可用
# ---------------------------------------------------------------------------


def test_2_target_unavailable_after_location_change(client: TestClient):
    """切换到新地点后旧地点的 target 应不可用."""
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    save_id = resp.json()["save_id"]

    # Travel to a different location
    action = {
        "action_type": "travel",
        "target_id": "police_office",
        "expected_version": 0,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    version = data["state_version"]

    # Try to inspect an apartment clue (no longer at current location)
    action = {
        "action_type": "inspect",
        "target_id": "clue_material_receipt",
        "expected_version": version,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error_code"] in ("INVALID_TARGET", "TARGET_NOT_VISIBLE")


# ---------------------------------------------------------------------------
# Test 3: 使用旧 state_version 返回 STATE_VERSION_CONFLICT
# ---------------------------------------------------------------------------


def test_3_old_state_version_conflict(client: TestClient):
    """用旧 version 提交 action 应返回 STATE_VERSION_CONFLICT."""
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    save_id = resp.json()["save_id"]

    # Execute a successful action so version increments from 0 to 1
    action = {
        "action_type": "rest",
        "expected_version": 0,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    # Use the old version (0) — should conflict
    action = {
        "action_type": "rest",
        "expected_version": 0,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error_code"] == "STATE_VERSION_CONFLICT"


# ---------------------------------------------------------------------------
# Test 4: 读档后可恢复
# ---------------------------------------------------------------------------


def test_4_save_load_restores_game(client: TestClient):
    """读档后游戏状态应正确恢复."""
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    save_id = resp.json()["save_id"]

    # Travel to a location
    action = {
        "action_type": "travel",
        "target_id": "clinic",
        "expected_version": 0,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    version = data["state_version"]

    # Save the game
    resp = client.post(f"/v1/game/{save_id}/save")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Load the game
    resp = client.post(f"/v1/game/{save_id}/load")
    assert resp.status_code == 200
    view = resp.json()
    assert view["player"]["current_location_id"] == "clinic"
    assert view["state_version"] == version


# ---------------------------------------------------------------------------
# Test 5: Action 成功后旧按钮立即失效
# ---------------------------------------------------------------------------


def test_5_duplicate_inspect_fails(client: TestClient, case_dir: Path):
    """成功 inspect 后再次 inspect 同一个线索应失败."""
    loader = CaseLoader(case_dir)
    case = loader.load_case()

    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    save_id = resp.json()["save_id"]

    # Find a clue at the starting location (apartment)
    apartment_clues = [c for c in case.clues if c.location_id == "apartment"]
    assert len(apartment_clues) > 0, "No clues at starting location"
    clue_id = apartment_clues[0].clue_id

    # First inspect — should succeed
    action = {
        "action_type": "inspect",
        "target_id": clue_id,
        "expected_version": 0,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    version = data["state_version"]

    # Second inspect of the same clue — should fail (clue already discovered)
    action = {
        "action_type": "inspect",
        "target_id": clue_id,
        "expected_version": version,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error_code"] in ("INVALID_TARGET", "TARGET_NOT_AVAILABLE", "TARGET_NOT_VISIBLE")


# ---------------------------------------------------------------------------
# Test 6: target_id 为 null
# ---------------------------------------------------------------------------


def test_6_target_id_null(client: TestClient):
    """target_id 为 null 时，需要 target 的 action 应返回 INVALID_TARGET."""
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    save_id = resp.json()["save_id"]

    # inspect with null target_id — should fail validation or return INVALID_TARGET
    action = {
        "action_type": "inspect",
        "target_id": None,
        "expected_version": 0,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    if resp.status_code == 200:
        # Pydantic may coerce null to "", in which case inspect fails
        data = resp.json()
        assert data["success"] is False
        assert data["error_code"] == "INVALID_TARGET"
    else:
        # Pydantic v2 strict mode may reject null for a str field
        assert resp.status_code == 422

    # Rest with null target_id should still succeed (no target needed)
    action = {
        "action_type": "rest",
        "target_id": None,
        "expected_version": 0,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    if resp.status_code == 200:
        data = resp.json()
        assert data["success"] is True
    else:
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test 7: target_id 为空字符串
# ---------------------------------------------------------------------------


def test_7_target_id_empty_string(client: TestClient):
    """target_id 为空字符串时，需要 target 的 action 应返回 INVALID_TARGET."""
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    save_id = resp.json()["save_id"]

    # inspect with empty target_id — should fail
    action = {
        "action_type": "inspect",
        "target_id": "",
        "expected_version": 0,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error_code"] == "INVALID_TARGET"

    # Rest with empty target_id should succeed
    action = {
        "action_type": "rest",
        "target_id": "",
        "expected_version": 0,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


# ---------------------------------------------------------------------------
# Test 8: target_id 使用显示名称而非 ID
# ---------------------------------------------------------------------------


def test_8_target_id_uses_display_name(client: TestClient):
    """使用显示名称而非 ID 作为 target_id 应返回 INVALID_TARGET."""
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    save_id = resp.json()["save_id"]

    # Use a display name instead of the actual clue_id
    action = {
        "action_type": "inspect",
        "target_id": "神秘材料收据",
        "expected_version": 0,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error_code"] == "INVALID_TARGET"


# ---------------------------------------------------------------------------
# Test 9: 不存在的 action_type
# ---------------------------------------------------------------------------


def test_9_nonexistent_action_type(client: TestClient):
    """不存在的 action_type 应返回错误."""
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    save_id = resp.json()["save_id"]

    action = {
        "action_type": "fly",
        "target_id": "",
        "expected_version": 0,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    # FastAPI's enum validation should reject an invalid action_type
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test 10: game_over 后再次提交 Action
# ---------------------------------------------------------------------------


def test_10_game_over_blocks_actions(client: TestClient):
    """game_over 后提交任意 action 应返回 GAME_ALREADY_FINISHED."""
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    data = resp.json()
    save_id = data["save_id"]
    version = data["view"]["state_version"]

    # Directly set game_over on the session (simulating hypothesis ending)
    mgr = routes.manager
    assert mgr is not None, "Manager should be initialized by client fixture"
    session = mgr.get_session(save_id)
    assert session is not None
    session.game_over = True
    session.final_ending = "ending_normal_disappearance"

    # Submit any action — should fail
    action = {
        "action_type": "rest",
        "expected_version": version,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error_code"] == "GAME_ALREADY_FINISHED"


# ---------------------------------------------------------------------------
# Test 11: 快速连续点击同一 Action
# ---------------------------------------------------------------------------


def test_11_rapid_same_action(client: TestClient):
    """快速连续用相同参数发送两次请求，第二次应基于最新 version."""
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    save_id = resp.json()["save_id"]

    # First request
    action = {
        "action_type": "rest",
        "expected_version": 0,
    }
    resp1 = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp1.status_code == 200
    data1 = resp1.json()

    # Second request with the same (now stale) version
    resp2 = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp2.status_code == 200
    data2 = resp2.json()

    if data1["success"]:
        # First succeeded, second with old version should conflict
        assert data2["success"] is False
        assert data2["error_code"] == "STATE_VERSION_CONFLICT"
    else:
        # If first failed (unlikely for rest), second may also fail
        assert data2["success"] is False


# ---------------------------------------------------------------------------
# Test 12: 快速点击两个不同 Action
# ---------------------------------------------------------------------------


def test_12_rapid_different_actions(client: TestClient):
    """连续发送两个不同的 action，两个都应得到合理响应."""
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    save_id = resp.json()["save_id"]

    # First action: travel
    action1 = {
        "action_type": "travel",
        "target_id": "police_office",
        "expected_version": 0,
    }
    resp1 = client.post(f"/v1/game/{save_id}/action", json=action1)
    assert resp1.status_code == 200
    data1 = resp1.json()

    version = data1["state_version"] if data1["success"] else 0  # fallback

    # Second action: talk with correct version
    action2 = {
        "action_type": "talk",
        "target_id": "npc_landlord",
        "expected_version": version,
    }
    resp2 = client.post(f"/v1/game/{save_id}/action", json=action2)
    assert resp2.status_code == 200
    data2 = resp2.json()

    # Both should have valid responses
    assert "success" in data1
    assert "error_code" in data1 or data1["success"] is True
    assert "success" in data2
    assert "error_code" in data2 or data2["success"] is True


# ---------------------------------------------------------------------------
# Test 13: 浏览器后退后提交过期 Action
# ---------------------------------------------------------------------------


def test_13_browser_back_stale_action(client: TestClient):
    """用旧 version 提交 action 应返回 STATE_VERSION_CONFLICT."""
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    save_id = resp.json()["save_id"]

    # Execute one action to advance version
    action = {
        "action_type": "rest",
        "expected_version": 0,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    # Simulate browser back: use version 0 again
    action = {
        "action_type": "rest",
        "expected_version": 0,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error_code"] == "STATE_VERSION_CONFLICT"


# ---------------------------------------------------------------------------
# Test 14: API 超时后重新获取 View
# ---------------------------------------------------------------------------


def test_14_get_view_after_actions(client: TestClient):
    """执行 action 后调用 get_view 应返回最新的 state_version."""
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    data = resp.json()
    save_id = data["save_id"]

    # Execute an action
    action = {
        "action_type": "travel",
        "target_id": "clinic",
        "expected_version": 0,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    expected_version = data["state_version"]

    # Get view
    resp = client.get(f"/v1/game/{save_id}/view")
    assert resp.status_code == 200
    view = resp.json()
    assert view["state_version"] == expected_version
    assert view["player"]["current_location_id"] == "clinic"


# ---------------------------------------------------------------------------
# Test 15: INVALID_TARGET 后页面不崩溃
# ---------------------------------------------------------------------------


def test_15_invalid_target_response_does_not_crash(client: TestClient):
    """INVALID_TARGET 后 response 应包含必要字段，且 get_view 仍正常工作."""
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01")
    assert resp.status_code == 200
    data = resp.json()
    save_id = data["save_id"]
    version = data["view"]["state_version"]

    # Submit an invalid target
    action = {
        "action_type": "inspect",
        "target_id": "nonexistent_clue",
        "expected_version": version,
    }
    resp = client.post(f"/v1/game/{save_id}/action", json=action)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error_code"] == "INVALID_TARGET"
    # Verify required error fields
    assert "error_code" in data
    assert "recoverable" in data
    assert isinstance(data["recoverable"], bool)
    # The state_version should still be reported
    assert "state_version" in data

    # Verify the view is still accessible and correct
    resp = client.get(f"/v1/game/{save_id}/view")
    assert resp.status_code == 200
    view = resp.json()
    assert view["player"]["current_location_id"] == "apartment"
    assert view["state_version"] >= 0
    # Available actions should still be present
    assert len(view["available_actions"]) > 0
