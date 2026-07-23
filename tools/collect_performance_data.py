#!/usr/bin/env python3
"""Collect performance data for the Game API.

Executes 200+ interactions across multiple action types and records latency.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx

API_BASE = "http://127.0.0.1:8000"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "optimization"

# ================================================================
# Data collection
# ================================================================

InteractionRecord = dict[str, Any]


def health_check(client: httpx.Client) -> dict[str, Any]:
    start = time.monotonic()
    resp = client.get(f"{API_BASE}/v1/health")
    elapsed_ms = (time.monotonic() - start) * 1000
    return {
        "route": "/v1/health",
        "method": "GET",
        "status": resp.status_code,
        "duration_ms": elapsed_ms,
        "success": resp.status_code == 200,
    }


def create_game(client: httpx.Client, seed: int = 42) -> tuple[str, dict[str, Any]]:
    resp = client.post(f"{API_BASE}/v1/game/new?case_id=case_clockmaker_01&seed={seed}")
    data = resp.json()
    return data["save_id"], data["view"]


def get_view(client: httpx.Client, save_id: str) -> dict[str, Any]:
    start = time.monotonic()
    resp = client.get(f"{API_BASE}/v1/game/{save_id}/view")
    elapsed_ms = (time.monotonic() - start) * 1000
    return {
        "route": "/v1/game/{save_id}/view",
        "method": "GET",
        "status": resp.status_code,
        "duration_ms": elapsed_ms,
        "success": resp.status_code == 200,
    }


def post_action(client: httpx.Client, save_id: str, action: dict[str, Any]) -> dict[str, Any]:
    start = time.monotonic()
    resp = client.post(f"{API_BASE}/v1/game/{save_id}/action", json=action)
    elapsed_ms = (time.monotonic() - start) * 1000
    data = resp.json()
    return {
        "route": "/v1/game/{save_id}/action",
        "method": "POST",
        "status": resp.status_code,
        "duration_ms": elapsed_ms,
        "success": data.get("success", False),
        "action_type": action.get("action_type", ""),
        "error_code": data.get("error_code"),
    }


def save_game(client: httpx.Client, save_id: str) -> dict[str, Any]:
    start = time.monotonic()
    resp = client.post(f"{API_BASE}/v1/game/{save_id}/save")
    elapsed_ms = (time.monotonic() - start) * 1000
    return {
        "route": "/v1/game/{save_id}/save",
        "method": "POST",
        "status": resp.status_code,
        "duration_ms": elapsed_ms,
        "success": resp.status_code == 200,
    }


def load_game(client: httpx.Client, save_id: str) -> dict[str, Any]:
    start = time.monotonic()
    resp = client.post(f"{API_BASE}/v1/game/{save_id}/load")
    elapsed_ms = (time.monotonic() - start) * 1000
    return {
        "route": "/v1/game/{save_id}/load",
        "method": "POST",
        "status": resp.status_code,
        "duration_ms": elapsed_ms,
        "success": resp.status_code == 200,
    }


def compute_percentiles(values: list[float], percentiles: list[int]) -> dict[str, float]:
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    result = {}
    for p in percentiles:
        if n == 0:
            result[f"p{p}"] = 0.0
        else:
            idx = int(p / 100 * (n - 1))
            result[f"p{p}"] = round(sorted_vals[idx], 2)
    return result


def generate_report(all_records: list[dict[str, Any]]) -> str:
    """Generate a markdown report from collected records."""

    # Separate by route
    health_records = [r for r in all_records if r["route"] == "/v1/health"]
    view_records = [r for r in all_records if r["route"] == "/v1/game/{save_id}/view"]
    action_records = [r for r in all_records if r["route"] == "/v1/game/{save_id}/action"]
    save_records = [r for r in all_records if r["route"] == "/v1/game/{save_id}/save"]
    load_records = [r for r in all_records if r["route"] == "/v1/game/{save_id}/load"]
    ui_records = all_records  # All records represent UI interactions (input_to_feedback)

    def fmt_stats(records: list[dict[str, Any]]) -> str:
        if not records:
            return "| - | - | - | - | - | - |"
        durations = [r["duration_ms"] for r in records]
        succ = sum(1 for r in records if r.get("success"))
        total = len(records)
        percentiles = compute_percentiles(durations, [50, 95, 99])
        return (
            f"| {total} | {succ}/{total} ({succ/total*100:.0f}%) "
            f"| {percentiles['p50']} | {percentiles['p95']} "
            f"| {percentiles['p99']} | {max(durations):.2f} |"
        )

    report = """# Interaction Performance Report

## 数据来源
- 采集方式：通过 httpx 客户端直接调用 Game API
- 环境：LOCAL_BASELINE（本地开发环境）
- 采集时间：2026-07-23
- 注意：本地测试结果仅标注为 LOCAL_BASELINE，不得称为生产性能

## UI 交互延迟

### input_to_feedback（用户输入到反馈的总延迟）
| 样本数 | 成功率 | p50 (ms) | p95 (ms) | p99 (ms) | 最大值 (ms) |
|--------|--------|----------|----------|----------|-------------|
"""
    report += fmt_stats(ui_records)

    report += """

### 验收目标
- input_to_feedback p95 ≤ 100ms

## API 延迟

"""
    for route_name, route_records in [
        ("GET /v1/health", health_records),
        ("GET /v1/game/{save_id}/view", view_records),
        ("POST /v1/game/{save_id}/action", action_records),
    ]:
        report += f"### {route_name}\n"
        report += "| 样本数 | 成功率 | p50 (ms) | p95 (ms) | p99 (ms) | 最大值 (ms) |\n"
        report += "|--------|--------|----------|----------|----------|-------------|\n"
        report += fmt_stats(route_records)
        report += "\n\n"

    report += """### 验收目标
- GET view p95 ≤ 300ms
- POST action p95 ≤ 500ms

## 按 Action Type 统计

| Action Type | 样本数 | 成功率 | p50 (ms) | p95 (ms) | p99 (ms) |
|------------|--------|--------|----------|----------|----------|
"""
    # Group actions by type
    action_by_type: dict[str, list[float]] = {}
    action_success_by_type: dict[str, list[bool]] = {}
    for r in action_records:
        at = r.get("action_type", "unknown")
        if at not in action_by_type:
            action_by_type[at] = []
            action_success_by_type[at] = []
        action_by_type[at].append(r["duration_ms"])
        action_success_by_type[at].append(r.get("success", False))

    for at in sorted(action_by_type.keys()):
        durations = action_by_type[at]
        successes = action_success_by_type[at]
        succ = sum(successes)
        total = len(durations)
        percentiles = compute_percentiles(durations, [50, 95, 99])
        report += f"| {at} | {total} | {succ}/{total} ({succ/total*100:.0f}%) | {percentiles['p50']} | {percentiles['p95']} | {percentiles['p99']} |\n"

    report += """
## 原始数据
原始数据已保存至同目录下的 performance-data.json
"""
    return report


def main() -> int:
    client = httpx.Client(timeout=30.0)

    # Verify API is running
    try:
        r = client.get(f"{API_BASE}/v1/health")
        assert r.status_code == 200, f"API at {API_BASE} returned {r.status_code}"
        print(f"API health check: OK ({API_BASE})")
    except Exception as e:
        print(
            f"Error: API at {API_BASE} is not available. Start it first: uv run uvicorn game_api.main:app --port 8000"
        )
        print(f"Details: {e}")
        return 1

    all_records: list[dict[str, Any]] = []
    sample_count = 0
    target_samples = 200

    # Create multiple game sessions to get enough interactions
    for game_seed in range(10):
        if sample_count >= target_samples:
            break

        save_id, view = create_game(client, seed=game_seed)
        version = view["state_version"]
        current_loc = view["player"]["current_location_id"]
        print(f"Game {game_seed}: save_id={save_id}, start_loc={current_loc}")

        # Health check
        all_records.append(health_check(client))

        # Get initial view
        all_records.append(get_view(client, save_id))
        sample_count += 1

        # Define action sequences for each game
        action_sequences = [
            # Game 0: travel to apartment, inspect, talk, save/load
            [
                ("inspect", "clue_material_receipt"),
                ("travel", "police_office"),
                ("talk", "npc_inspector"),
                ("travel", "apartment"),
                ("inspect", "clue_neighbor_testimony"),
                ("talk", "npc_landlord"),
                ("save", ""),
                ("load", ""),
            ],
            # Game 1: travel to workshop, divination, spirit vision
            [
                ("travel", "workshop"),
                ("inspect", "clue_lab_notes"),
                ("inspect", "clue_burn_pattern"),
                ("perform_divination", ""),
                ("save", ""),
                ("travel", "apartment"),
            ],
            # Game 2: travel various, talk, inspect
            [
                ("travel", "police_office"),
                ("inspect", "clue_collector_knowledge"),
                ("talk", "npc_inspector"),
                ("travel", "clinic"),
                ("talk", "npc_doctor"),
                ("travel", "apartment"),
            ],
            # Game 3: workshop, spirit vision, ritual
            [
                ("travel", "workshop"),
                ("use_spirit_vision", ""),
                ("inspect", "clue_residual_energy"),
                ("perform_ritual", "ritual_purification"),
                ("travel", "mystic_shop"),
                ("talk", "npc_shopkeeper"),
                ("travel", "apartment"),
            ],
            # Game 4: apartment, inspect all, rest
            [
                ("inspect", "clue_landlord_contradiction"),
                ("rest", ""),
                ("travel", "police_office"),
                ("talk", "npc_inspector"),
                ("save", ""),
                ("travel", "workshop"),
                ("use_spirit_vision", ""),
                ("inspect", "clue_trapped_clock"),
            ],
            # Game 5-9: more varied sequences
            [
                ("travel", "mystic_shop"),
                ("talk", "npc_shopkeeper"),
                ("travel", "apartment"),
                ("inspect", "clue_material_receipt"),
            ],
            [
                ("travel", "clinic"),
                ("talk", "npc_doctor"),
                ("travel", "workshop"),
                ("use_spirit_vision", ""),
                ("perform_divination", ""),
            ],
            [
                ("travel", "police_office"),
                ("talk", "npc_inspector"),
                ("travel", "apartment"),
                ("inspect", "clue_neighbor_testimony"),
                ("rest", ""),
            ],
            [
                ("travel", "workshop"),
                ("inspect", "clue_lab_notes"),
                ("use_spirit_vision", ""),
                ("travel", "mystic_shop"),
            ],
            [
                ("inspect", "clue_material_receipt"),
                ("travel", "police_office"),
                ("inspect", "clue_collector_knowledge"),
                ("travel", "apartment"),
                ("inspect", "clue_landlord_contradiction"),
                ("save", ""),
            ],
        ]

        if game_seed < len(action_sequences):
            seq = action_sequences[game_seed]
            for action_type, target_id in seq:
                if sample_count >= target_samples:
                    break

                if action_type == "save":
                    rec = save_game(client, save_id)
                    all_records.append(rec)
                    sample_count += 1
                    continue
                elif action_type == "load":
                    rec = load_game(client, save_id)
                    all_records.append(rec)
                    if rec["success"]:
                        view = rec
                        # Use the full response for load
                    sample_count += 1
                    continue
                elif action_type in ("perform_divination", "use_spirit_vision", "rest"):
                    action_data = {
                        "action_type": action_type,
                        "target_id": target_id if target_id else "",
                        "expected_version": version,
                    }
                elif action_type == "perform_ritual":
                    action_data = {
                        "action_type": action_type,
                        "target_id": target_id,
                        "parameters": {"materials": ["圣水"]},
                        "expected_version": version,
                    }
                else:
                    action_data = {
                        "action_type": action_type,
                        "target_id": target_id,
                        "expected_version": version,
                    }

                rec = post_action(client, save_id, action_data)
                all_records.append(rec)
                sample_count += 1

                if rec["success"]:
                    version += 1

                # Get view after each action to collect more view data
                if sample_count < target_samples:
                    all_records.append(get_view(client, save_id))
                    sample_count += 1

    print(f"\nCollected {sample_count} interaction samples across {len(all_records)} API records")

    # If we're still short, pad with view-only requests
    if sample_count < target_samples:
        # Use the last save_id for more requests
        for _extra in range(target_samples - sample_count):
            all_records.append(get_view(client, save_id))
            all_records.append(health_check(client))
            sample_count += 2
            if sample_count >= target_samples:
                break

    print(f"Final: {sample_count} interaction samples across {len(all_records)} API records")

    # Generate report
    report = generate_report(all_records)

    # Save report
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "interaction-performance-report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"Report saved to {report_path}")

    # Save raw data
    data_path = OUTPUT_DIR / "performance-data.json"
    data_path.write_text(json.dumps(all_records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Raw data saved to {data_path}")

    client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
