#!/usr/bin/env python3
"""CLI Demo for 诡秘之主 - The Clockmaker's Disappearance."""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from investigation_core.models import (
    EndingType,
    SaveData,
)
from investigation_core.services import (
    CaseLoader,
    CaseStateMachine,
    SaveRepository,
)

CASE_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "content"
    / "cases"
    / "case_clockmaker_01"
)

LOCATION_NAMES = {
    "apartment": "公寓 - 失踪者住所",
    "police_office": "警务办公室",
    "mystic_shop": "神秘材料商店",
    "clinic": "私人诊所",
    "workshop": "废弃钟表工坊",
}

LOCATIONS = list(LOCATION_NAMES.keys())

FALLBACK_DIALOGUE_PATH = CASE_DIR / "fallback_dialogue.json"


def load_fallback_dialogue() -> dict[str, list[dict[str, Any]]]:
    """Load fallback dialogue organized by npc_id."""
    with open(FALLBACK_DIALOGUE_PATH) as f:
        entries = json.load(f)
    result: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        npc_id = entry["npc_id"]
        if npc_id not in result:
            result[npc_id] = []
        result[npc_id].append(entry)
    return result


def print_header(state_machine: CaseStateMachine) -> None:
    state = state_machine.player_state
    location = LOCATION_NAMES.get(state.current_location_id, state.current_location_id)
    print("\n" + "═" * 50)
    print(f"  [当前位置] {location}")
    print(
        f"  [灵性] {state.spirituality}/10  [污染] {state.corruption_level}  [稳定性] {state.stability}"
    )
    discovered = state_machine.get_discovered_clues()
    if discovered:
        print(f"  已发现线索: {len(discovered)} 个")
        for c in discovered:
            print(f"    - {c.display_name}")
    else:
        print("  已发现线索: 无")
    print("═" * 50)


def cmd_move(state_machine: CaseStateMachine) -> None:
    print("\n--- 移动 ---")
    print("可前往的地点:")
    for i, loc in enumerate(LOCATIONS, 1):
        marker = " ← 当前位置" if loc == state_machine.player_state.current_location_id else ""
        print(f"  {i}. {LOCATION_NAMES[loc]}{marker}")
    print("  0. 返回")

    try:
        choice = int(input("请选择: "))
        if choice == 0:
            return
        if 1 <= choice <= len(LOCATIONS):
            loc = LOCATIONS[choice - 1]
            state_machine.move_to_location(loc)
            print(f"已移动到 {LOCATION_NAMES[loc]}")
    except ValueError:
        print("无效输入")


def cmd_investigate(state_machine: CaseStateMachine) -> None:
    print("\n--- 调查 ---")
    available = state_machine.get_available_clues()
    if not available:
        print("当前地点没有可发现的线索。")
        return

    print("可调查的线索:")
    for i, clue in enumerate(available, 1):
        print(f"  {i}. {clue.display_name} - {clue.description}")

    try:
        choice = int(input("请选择要调查的线索 (0返回): "))
        if choice == 0:
            return
        if 1 <= choice <= len(available):
            clue = available[choice - 1]
            success, event = state_machine.discover_clue(clue.clue_id)
            if success:
                print(f"\n  发现: {clue.display_name}")
                print(f"  {clue.description}")
                # Show revealed facts
                for fact_id in clue.reveals_fact_ids:
                    fact = next((f for f in state_machine.case.facts if f.fact_id == fact_id), None)
                    if fact:
                        print(f"  → 推断出: {fact.summary}")
            else:
                print("无法发现该线索。")
    except ValueError:
        print("无效输入")


def cmd_talk(state_machine: CaseStateMachine, fallback: dict[str, list[dict[str, Any]]]) -> None:
    print("\n--- 对话 ---")
    npcs = state_machine.get_available_npcs()
    if not npcs:
        print("当前地点没有可对话的 NPC。")
        return

    print("可对话的 NPC:")
    for i, npc in enumerate(npcs, 1):
        print(f"  {i}. {npc.name} - {npc.description}")

    try:
        choice = int(input("请选择要对话的 NPC (0返回): "))
        if choice == 0:
            return
        if 1 <= choice <= len(npcs):
            npc = npcs[choice - 1]
            print(f"\n--- 与 {npc.name} 对话 ---")

            # Show fallback dialogue options
            npc_dialogue = fallback.get(npc.npc_id, [])
            dialogue_options = [d for d in npc_dialogue]

            print("选择对话内容:")
            options = []
            for d in dialogue_options:
                if d["trigger"] == "greeting":
                    options.append(("打招呼", d))
                elif d["trigger"] == "ask_case":
                    options.append(("询问案件", d))
                elif d["trigger"] == "unknowable":
                    options.append(("询问敏感问题", d))

            for i, (label, _) in enumerate(options, 1):
                print(f"  {i}. {label}")
            print("  0. 结束对话")

            d_choice = int(input("请选择: "))
            if d_choice == 0:
                return
            if 1 <= d_choice <= len(options):
                _, entry = options[d_choice - 1]
                print(f"\n  {entry['utterance']}")

                # Track revealed claims
                if "referenced_claim_ids" in entry:
                    for cid in entry["referenced_claim_ids"]:
                        if cid not in state_machine.player_state.revealed_claim_ids:
                            state_machine.player_state.revealed_claim_ids.append(cid)
    except ValueError:
        print("无效输入")


def cmd_divination(state_machine: CaseStateMachine) -> None:
    print("\n--- 占卜 ---")
    if state_machine.player_state.spirituality <= 0:
        print("灵性不足，无法进行占卜。")
        return

    question = input("请输入你的问题: ").strip()
    if not question:
        question = "真相是什么？"

    # Use deterministic seed from state
    seed = state_machine.player_state.seed
    state_machine.player_state.seed += 1

    result = state_machine.perform_divination(question, seed)

    print(f"\n  倾向: {result.tendency}")
    print(f"  象征画面: {result.symbolic_image}")
    print(f"  可信度: {result.confidence}/5")
    print(f"  消耗灵性: {result.cost}")
    if result.is_interfered:
        print("  ⚠ 占卜受到干扰，结果可能不可靠")


def cmd_ritual(state_machine: CaseStateMachine) -> None:
    print("\n--- 仪式 ---")
    rituals = state_machine.case.rituals
    if not rituals:
        print("没有可用的仪式。")
        return

    print("可用的仪式:")
    for i, r in enumerate(rituals, 1):
        print(f"  {i}. {r.name} - {r.purpose}")
        print(f"     所需材料: {', '.join(r.required_materials)}")

    try:
        choice = int(input("请选择仪式 (0返回): "))
        if choice == 0:
            return
        if 1 <= choice <= len(rituals):
            ritual = rituals[choice - 1]
            materials_input = input("请输入你准备的材料 (用逗号分隔): ").strip()
            materials = [m.strip() for m in materials_input.split(",") if m.strip()]

            seed = state_machine.player_state.seed
            state_machine.player_state.seed += 1

            success, message, corruption = state_machine.perform_ritual(
                ritual.ritual_id, materials, seed
            )

            print(f"\n  结果: {message}")
            print(f"  污染变化: {corruption:+d}")
    except ValueError:
        print("无效输入")


def cmd_hypothesis(state_machine: CaseStateMachine) -> None:
    print("\n--- 提交假设 ---")
    hypotheses = [
        h
        for h in state_machine.case.hypotheses
        if h.hypothesis_id not in state_machine.player_state.confirmed_hypothesis_ids
    ]
    if not hypotheses:
        print("所有假设已提交。")
        return

    print("可提交的假设:")
    for i, h in enumerate(hypotheses, 1):
        required = len(h.required_clue_ids)
        has = sum(
            1
            for cid in h.required_clue_ids
            if cid in state_machine.player_state.discovered_clue_ids
        )
        print(f"  {i}. {h.title}")
        print(f"     描述: {h.description}")
        print(f"     证据: {has}/{required}")

    try:
        choice = int(input("请选择要提交的假设 (0返回): "))
        if choice == 0:
            return
        if 1 <= choice <= len(hypotheses):
            hypothesis = hypotheses[choice - 1]
            success, event, ending_id = state_machine.submit_hypothesis(hypothesis.hypothesis_id)

            if success:
                print(f"\n  假设 '{hypothesis.title}' 已确认!")
                if ending_id:
                    ending = next(
                        (e for e in state_machine.case.endings if e.ending_id == ending_id), None
                    )
                    if ending:
                        print(f"\n  ╔══ 结局: {ending.title} ══╗")
                        print(f"  {ending.description}")
                        print(f"  ╚{'═' * 40}╝")

                        # Check if game should end
                        print("\n案件已结束。输入 0 退出游戏。")
                        # Mark the ending in player state via completed_events
                        if f"ending_{ending_id}" not in state_machine.player_state.completed_events:
                            state_machine.player_state.completed_events.append(
                                f"ending_{ending_id}"
                            )
            else:
                print("假设提交失败 - 证据不足或条件不满足。")
                print(f"提示: 需要 {hypothesis.min_confidence} 点证据可信度")
    except ValueError:
        print("无效输入")


def cmd_status(state_machine: CaseStateMachine) -> None:
    state = state_machine.player_state
    print("\n--- 详细状态 ---")
    print(f"  案件: {state_machine.case.title}")
    print(f"  当前位置: {LOCATION_NAMES.get(state.current_location_id, state.current_location_id)}")
    print(f"  已访问地点: {len(state.visited_location_ids)}/{len(LOCATIONS)}")
    print(f"  灵性: {state.spirituality}/10")
    print(f"  污染: {state.corruption_level}")
    print(f"  稳定性: {state.stability}")

    discovered = state_machine.get_discovered_clues()
    print(f"\n  已发现线索 ({len(discovered)}):")
    for c in discovered:
        print(f"    - {c.display_name}")

    available = state_machine.get_available_clues()
    if available:
        print(f"  当前可调查线索 ({len(available)}):")
        for c in available:
            print(f"    - {c.display_name}")

    print(f"\n  已确认假设: {state.confirmed_hypothesis_ids}")
    print(f"  已触发事件: {len(state.completed_events)}")


def cmd_log(state_machine: CaseStateMachine) -> None:
    print("\n--- 事件日志 ---")
    events = state_machine.get_event_log()
    if not events:
        print("尚无事件记录。")
        return
    for i, event in enumerate(events, 1):
        print(f"  {i}. [{event.event_type}] {event.description}")


def cmd_save(state_machine: CaseStateMachine, save_repo: SaveRepository) -> None:
    print("\n--- 保存游戏 ---")
    print("可用的存档槽位: 0, 1, 2")
    try:
        slot = int(input("请选择存档槽位: "))
        if slot < 0 or slot > 2:
            print("无效槽位")
            return
        save_data = SaveData(
            save_id=f"save_{slot}_{datetime.now(UTC).timestamp()}",
            player_state=state_machine.player_state,
            event_log=state_machine.get_event_log(),
            seed=state_machine.player_state.seed,
        )
        path = save_repo.save(save_data, slot)
        print(f"已保存到 {path}")
    except ValueError:
        print("无效输入")


def cmd_load(state_machine: CaseStateMachine, save_repo: SaveRepository) -> None:
    print("\n--- 加载游戏 ---")
    saves = save_repo.list_saves()
    if not saves:
        print("没有存档。")
        return
    print(f"可用存档: {saves}")
    try:
        slot = int(input("请选择存档槽位: "))
        save_data = save_repo.load(slot)
        if save_data:
            state_machine.player_state = save_data.player_state
            state_machine.event_log.clear()
            for event in save_data.event_log:
                state_machine.event_log.add_event(event)
            print(f"已加载存档 {slot}")
        else:
            print("存档不存在。")
    except ValueError:
        print("无效输入")


def cmd_help() -> None:
    print("\n--- 帮助 ---")
    print("  1. 移动 - 前往不同的调查地点")
    print("  2. 调查 - 在当前地点搜索线索")
    print("  3. 对话 - 与当前位置的 NPC 交谈")
    print("  4. 占卜 - 消耗灵性获得调查方向提示")
    print("  5. 仪式 - 执行仪式验证假设")
    print("  6. 提交假设 - 提交推理假设触发结局")
    print("  7. 状态 - 查看角色详细状态")
    print("  8. 日志 - 查看事件日志")
    print("  9. 保存 - 保存游戏进度")
    print("  10. 加载 - 加载存档")
    print("  11. 帮助 - 显示此帮助")
    print("  0. 退出 - 结束游戏")


def main() -> None:
    print("╔══════════════════════════════════════╗")
    print("║        灰雾计划 - 调查终端            ║")
    print("║     案件：钟表匠失踪案               ║")
    print("╚══════════════════════════════════════╝")

    # Load case data
    loader = CaseLoader(CASE_DIR)
    case = loader.load_case()
    print(f"✓ 案件已加载: {case.title} v{case.version}")
    print(f"  {len(case.facts)} 个事实, {len(case.claims)} 个声明, {len(case.clues)} 条线索")
    print(f"  {len(case.npcs)} 个 NPC, {len(case.hypotheses)} 个假设, {len(case.endings)} 个结局")

    # Initialize state machine
    state_machine = CaseStateMachine(case)

    # Load fallback dialogue
    fallback = load_fallback_dialogue()

    # Initialize save repository in temp
    save_dir = Path(tempfile.mkdtemp(prefix="greyfog_save_"))
    save_repo = SaveRepository(save_dir)

    print("\n开始调查！输入 11 查看帮助。")

    while True:
        # Check if game ended
        if any(e.startswith("ending_") for e in state_machine.player_state.completed_events):
            print_header(state_machine)
            print("\n游戏已结束。输入 0 退出。")

        print_header(state_machine)

        # Check for bad ending via corruption
        if state_machine.player_state.corruption_level >= 3:
            ending = state_machine.resolve_ending()
            if ending and ending.ending_type == EndingType.BAD_ENDING:
                print(f"\n  ╔══ 结局: {ending.title} ══╗")
                print(f"  {ending.description}")
                print(f"  ╚{'═' * 40}╝")
                if "ending_bad" not in state_machine.player_state.completed_events:
                    state_machine.player_state.completed_events.append("ending_bad")
                break

        print("\n可用命令:")
        commands = [
            ("1. 移动", "前往其他地点"),
            ("2. 调查", "搜索线索"),
            ("3. 对话", "与NPC交谈"),
            ("4. 占卜", "使用占卜能力"),
            ("5. 仪式", "执行仪式"),
            ("6. 提交假设", "提交推理"),
            ("7. 状态", "查看详情"),
            ("8. 日志", "事件记录"),
            ("9. 保存", "保存进度"),
            ("10. 加载", "加载存档"),
            ("11. 帮助", "显示帮助"),
            ("0. 退出", "结束游戏"),
        ]
        for cmd, desc in commands:
            print(f"  {cmd:15s} - {desc}")

        try:
            choice = input("\n请输入命令编号: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出游戏。")
            break

        if choice == "0":
            print("退出游戏。")
            break
        elif choice == "1":
            cmd_move(state_machine)
        elif choice == "2":
            cmd_investigate(state_machine)
        elif choice == "3":
            cmd_talk(state_machine, fallback)
        elif choice == "4":
            cmd_divination(state_machine)
        elif choice == "5":
            cmd_ritual(state_machine)
        elif choice == "6":
            cmd_hypothesis(state_machine)
        elif choice == "7":
            cmd_status(state_machine)
        elif choice == "8":
            cmd_log(state_machine)
        elif choice == "9":
            cmd_save(state_machine, save_repo)
        elif choice == "10":
            cmd_load(state_machine, save_repo)
        elif choice == "11":
            cmd_help()
        else:
            print("无效命令，请输入 0-11。")


if __name__ == "__main__":
    main()
