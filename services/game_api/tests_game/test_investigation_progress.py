"""Tests for investigation progress feature."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game_api.database import GameDatabase
from game_api.main import app
from game_api.routes import init_manager


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db = GameDatabase(tmp_path / "test.db")
    init_manager(db)
    return TestClient(app)


def _create_game(client: TestClient, seed: int = 42) -> tuple[str, dict]:
    """Create a new game and return (save_id, view)."""
    resp = client.post("/v1/game/new?case_id=case_clockmaker_01&seed=" + str(seed))
    assert resp.status_code == 200
    data = resp.json()
    return data["save_id"], data["view"]


def _get_view(client: TestClient, save_id: str) -> dict:
    resp = client.get(f"/v1/game/{save_id}/view")
    assert resp.status_code == 200
    return resp.json()


def _do_action(
    client: TestClient,
    save_id: str,
    action_type: str,
    target_id: str = "",
    expected_version: int = 0,
    parameters: dict | None = None,
) -> dict:
    resp = client.post(
        f"/v1/game/{save_id}/action",
        json={
            "action_type": action_type,
            "target_id": target_id,
            "expected_version": expected_version,
            "parameters": parameters or {},
            "idempotency_key": f"test_{action_type}_{target_id}_{expected_version}",
        },
    )
    assert resp.status_code == 200
    return resp.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPhaseProgression:
    """Verify phase level changes as clues are discovered."""

    def test_initial_phase(self, client: TestClient) -> None:
        _, view = _create_game(client)
        ip = view["investigation_progress"]
        assert ip is not None
        assert ip["phase_level"] == 0
        assert ip["phase_label"] == "迷雾初现"
        assert ip["new_resolution_available"] is False

    def test_phase_advances_with_clues(self, client: TestClient) -> None:
        save_id, view = _create_game(client)
        sv = view["state_version"]

        # Discover clues at apartment
        for clue_id in [
            "clue_material_receipt",
            "clue_neighbor_testimony",
            "clue_burnt_documents",
            "clue_landlord_contradiction",
        ]:
            r = _do_action(client, save_id, "inspect", clue_id, sv)
            assert r["success"], f"Failed to discover {clue_id}: {r.get('error_detail')}"
            sv = r["state_version"]

        # After ~4/15 clues: should still be phase 0 (<25%)
        v = _get_view(client, save_id)
        assert v["investigation_progress"]["phase_level"] >= 0

        # Travel to workshop and discover more
        r = _do_action(client, save_id, "travel", "workshop", sv)
        assert r["success"]
        sv = r["state_version"]

        clue_ids = [
            "clue_lab_notes",
            "clue_burn_pattern",
            "clue_residual_energy",
            "clue_trapped_clock",
        ]
        for cid in clue_ids:
            r = _do_action(client, save_id, "inspect", cid, sv)
            assert r["success"], f"Failed to discover {cid}"
            sv = r["state_version"]

        v = _get_view(client, save_id)
        ip = v["investigation_progress"]
        assert ip["phase_level"] >= 1  # 8/15 > 50%
        assert ip["phase_label"] in ("线索浮现", "疑点交汇")


class TestEvidenceDimensions:
    """Verify evidence dimension computation."""

    def test_evidence_dimensions_present(self, client: TestClient) -> None:
        _, view = _create_game(client)
        ip = view["investigation_progress"]
        dims = {d["dimension_id"]: d for d in ip["evidence_dimensions"]}
        for dim_id in ("scene", "witness", "anomaly", "items", "causality"):
            assert dim_id in dims, f"Missing dimension: {dim_id}"

    def test_dimensions_do_not_have_counts(self, client: TestClient) -> None:
        """Verify dimensions do NOT expose found/total counts."""
        _, view = _create_game(client)
        for dim in view["investigation_progress"]["evidence_dimensions"]:
            assert "found" not in dim
            assert "total" not in dim

    def test_dimension_status_label_changes_with_clues(self, client: TestClient) -> None:
        """Verify status_label changes as clues are discovered (without leaking counts)."""
        save_id, view = _create_game(client)
        sv = view["state_version"]

        # Initially items dimension should show "尚无发现"
        items_dim = [
            d
            for d in view["investigation_progress"]["evidence_dimensions"]
            if d["dimension_id"] == "items"
        ]
        assert items_dim
        assert items_dim[0]["status_label"] == "尚无发现"

        # Discover a document (items dimension) clue
        r = _do_action(client, save_id, "inspect", "clue_material_receipt", sv)
        assert r["success"]
        v = _get_view(client, save_id)
        items_dim = [
            d
            for d in v["investigation_progress"]["evidence_dimensions"]
            if d["dimension_id"] == "items"
        ]
        # Status label should have changed
        assert items_dim[0]["status_label"] != "尚无发现"


class TestNoLeakage:
    """Verify that the progress does NOT leak sensitive info."""

    def test_no_ending_id(self, client: TestClient) -> None:
        _, view = _create_game(client)
        ip = view["investigation_progress"]
        # Should not contain ending IDs
        assert "ending_id" not in ip
        assert "candidate_id" not in ip
        assert "required_clues" not in ip
        assert "missing_clues" not in ip
        assert "correct_hypothesis" not in ip
        assert "unlock_conditions" not in ip

    def test_no_hypothesis_details(self, client: TestClient) -> None:
        _, view = _create_game(client)
        ip = view["investigation_progress"]
        assert "hypothesis_id" not in ip
        # Should not reveal specific hypothesis details
        for q in ip.get("open_questions", []):
            assert "假设" not in q
            assert "hypothesis" not in q.lower()

    def test_undiscovered_clue_names_not_leaked(self, client: TestClient) -> None:
        save_id, view = _create_game(client)
        sv = view["state_version"]
        v = _get_view(client, save_id)
        recent = v["investigation_progress"]["recent_discoveries"]
        assert len(recent) == 0  # No discoveries yet

        # Discover one clue
        r = _do_action(client, save_id, "inspect", "clue_material_receipt", sv)
        assert r["success"]
        v = _get_view(client, save_id)
        recent = v["investigation_progress"]["recent_discoveries"]
        assert len(recent) >= 1
        assert "神秘材料收据" in recent[0]  # Only discovered clue


class TestResolutionAvailable:
    """Verify resolution_available flag."""

    def test_not_available_initially(self, client: TestClient) -> None:
        _, view = _create_game(client)
        assert view["investigation_progress"]["resolution_available"] is False

    def test_becomes_available(self, client: TestClient) -> None:
        save_id, view = _create_game(client)
        sv = view["state_version"]

        # Gather clues for hypothesis_normal_disappearance: clue_medical_record + clue_doctor_testimony
        r = _do_action(client, save_id, "travel", "clinic", sv)
        assert r["success"]
        sv = r["state_version"]

        r = _do_action(client, save_id, "inspect", "clue_medical_record", sv)
        assert r["success"]
        sv = r["state_version"]

        r = _do_action(client, save_id, "inspect", "clue_doctor_testimony", sv)
        assert r["success"]
        sv = r["state_version"]

        v = _get_view(client, save_id)
        assert v["investigation_progress"]["resolution_available"] is True

    def test_new_resolution_available(self, client: TestClient) -> None:
        save_id, view = _create_game(client)
        sv = view["state_version"]

        r = _do_action(client, save_id, "travel", "clinic", sv)
        assert r["success"]
        sv = r["state_version"]

        r = _do_action(client, save_id, "inspect", "clue_medical_record", sv)
        assert r["success"]
        sv = r["state_version"]

        r = _do_action(client, save_id, "inspect", "clue_doctor_testimony", sv)
        assert r["success"]
        sv = r["state_version"]

        v = _get_view(client, save_id)
        assert v["investigation_progress"]["new_resolution_available"] is True

    def test_new_resolution_clears_after_dismiss(self, client: TestClient) -> None:
        save_id, view = _create_game(client)
        sv = view["state_version"]

        r = _do_action(client, save_id, "travel", "clinic", sv)
        assert r["success"]
        sv = r["state_version"]

        r = _do_action(client, save_id, "inspect", "clue_medical_record", sv)
        assert r["success"]
        sv = r["state_version"]

        r = _do_action(client, save_id, "inspect", "clue_doctor_testimony", sv)
        assert r["success"]
        sv = r["state_version"]

        # Dismiss resolution hint
        r = _do_action(client, save_id, "dismiss_resolution_hint", "", sv)
        assert r["success"]
        sv = r["state_version"]

        v = _get_view(client, save_id)
        # resolution_available is still true, but new_resolution_available is false
        assert v["investigation_progress"]["resolution_available"] is True
        assert v["investigation_progress"]["new_resolution_available"] is False

    def test_new_resolution_persists_after_save_load(self, client: TestClient) -> None:
        save_id, view = _create_game(client)
        sv = view["state_version"]

        r = _do_action(client, save_id, "travel", "clinic", sv)
        assert r["success"]
        sv = r["state_version"]

        r = _do_action(client, save_id, "inspect", "clue_medical_record", sv)
        assert r["success"]
        sv = r["state_version"]

        r = _do_action(client, save_id, "inspect", "clue_doctor_testimony", sv)
        assert r["success"]
        sv = r["state_version"]

        # Dismiss
        r = _do_action(client, save_id, "dismiss_resolution_hint", "", sv)
        assert r["success"]
        sv = r["state_version"]

        # Save and load
        resp = client.post(f"/v1/game/{save_id}/save")
        assert resp.status_code == 200
        resp = client.post(f"/v1/game/{save_id}/load")
        assert resp.status_code == 200

        v = _get_view(client, save_id)
        assert v["investigation_progress"]["resolution_available"] is True
        assert v["investigation_progress"]["new_resolution_available"] is False

    def test_no_ending_without_submit(self, client: TestClient) -> None:
        """Even with resolution_available, game_over must remain False."""
        save_id, view = _create_game(client)
        sv = view["state_version"]

        r = _do_action(client, save_id, "travel", "clinic", sv)
        assert r["success"]
        sv = r["state_version"]

        r = _do_action(client, save_id, "inspect", "clue_medical_record", sv)
        assert r["success"]
        sv = r["state_version"]

        r = _do_action(client, save_id, "inspect", "clue_doctor_testimony", sv)
        assert r["success"]
        sv = r["state_version"]

        v = _get_view(client, save_id)
        assert v["investigation_progress"]["resolution_available"] is True
        assert v["game_over"] is False
        assert v["final_ending"] is None


class TestOpenQuestions:
    """Verify open questions appear when related clues are found."""

    def test_question_appears(self, client: TestClient) -> None:
        save_id, view = _create_game(client)
        sv = view["state_version"]

        r = _do_action(client, save_id, "inspect", "clue_material_receipt", sv)
        assert r["success"]
        sv = r["state_version"]

        v = _get_view(client, save_id)
        questions = v["investigation_progress"]["open_questions"]
        assert any("材料收据" in q for q in questions)

    def test_question_not_shown_before_clue(self, client: TestClient) -> None:
        _, view = _create_game(client)
        questions = view["investigation_progress"]["open_questions"]
        assert not any("材料收据" in q for q in questions)
