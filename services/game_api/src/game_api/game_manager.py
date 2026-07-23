"""Game session manager — wraps investigation_core with web API semantics.

Each session is identified by a save_id string.
The manager handles:
- Game creation from case data
- Action execution via CaseStateMachine
- State version tracking for conflict detection
- View generation for the client
- Save/load serialization
"""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from investigation_core import CaseLoader, CaseStateMachine
from investigation_core.models import CaseEvent, PlayerCaseState

from .database import GameDatabase
from .models import (
    ERROR_GAME_ALREADY_FINISHED,
    ERROR_INTERNAL,
    ERROR_INVALID_TARGET,
    ERROR_RESOURCE_INSUFFICIENT,
    ERROR_STATE_VERSION_CONFLICT,
    ERROR_TARGET_NOT_AVAILABLE,
    ActionInfo,
    ActionType,
    ClaimInfo,
    ClueInfo,
    EndingInfo,
    EventLogEntry,
    GameAction,
    GameView,
    HypothesisInfo,
    ItemInfo,
    LocationInfo,
    NpcInfo,
    PlayerStatus,
    RitualInfo,
)

CASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "content" / "cases"


# Human-readable labels for location IDs
LOCATION_LABELS: dict[str, str] = {
    "apartment": "失踪者公寓",
    "police_office": "警务办公室",
    "clinic": "私人诊所",
    "mystic_shop": "神秘材料商店",
    "workshop": "废弃钟表工坊",
}

LOCATION_DESCRIPTIONS: dict[str, str] = {
    "apartment": (
        "一间整洁但略带压抑的单人公寓。墙上挂着几幅风景画，"
        "书桌上散落着钟表修理的图纸和工具。空气中弥漫着淡淡的机油味。"
    ),
    "police_office": (
        "繁忙的警务办公室，文件堆积如山。墙上的告示板贴着几张通缉令和寻人启事。"
        "角落里有一张专门处理异常案件的办公桌。"
    ),
    "clinic": (
        "一间明亮的私人诊所，消毒水的气味很浓。"
        "候诊室里有几张旧椅子，墙角堆着几本过期的医学杂志。"
    ),
    "mystic_shop": (
        "昏暗的商店里摆满了各种神秘的瓶瓶罐罐。"
        "空气中飘着草药和薰香的味道。店主在柜台后面静静地看着你。"
    ),
    "workshop": (
        "钟表工坊内一片狼藉。墙上的钟全部停在同一个时刻——11:47。"
        "地面上有奇怪的焦痕，空气中仍然残留着一丝不寻常的能量波动。"
    ),
}

LOCATION_ACTIONS: dict[str, list[str]] = {
    "apartment": ["inspect", "talk", "use_spirit_vision"],
    "police_office": ["inspect", "talk"],
    "clinic": ["inspect", "talk"],
    "mystic_shop": ["inspect", "talk", "perform_ritual", "use_item"],
    "workshop": ["inspect", "use_spirit_vision", "perform_divination", "perform_ritual"],
}


class GameSession:
    """A single game session wrapping a CaseStateMachine."""

    def __init__(
        self,
        session_id: str,
        case_id: str,
        state_machine: CaseStateMachine,
        seed: int,
    ) -> None:
        self.session_id = session_id
        self.case_id = case_id
        self.sm = state_machine
        self.seed = seed
        self.state_version = 0
        self.game_over = False
        self.final_ending: str | None = None

    def _get_available_actions(self) -> list[ActionInfo]:
        """Generate structured available actions for the current state."""
        ps = self.sm.player_state
        current_loc = ps.current_location_id
        version = self.state_version
        actions: list[ActionInfo] = []

        # --- Travel: one per reachable location ---
        for lid, label in LOCATION_LABELS.items():
            if lid == current_loc:
                continue
            actions.append(
                ActionInfo(
                    action_id=f"action_travel_{lid}_{version}",
                    action_type="travel",
                    target_id=lid,
                    label=f"前往{label}",
                    enabled=True,
                    disabled_reason=None,
                    expected_version=version,
                    parameters_schema={"location_id": {"type": "string", "description": label}},
                )
            )

        # --- Inspect: one per undiscovered clue at current location ---
        available_clues = self.sm.get_available_clues()
        for clue in available_clues:
            if clue.location_id != current_loc:
                continue
            if clue.clue_id in ps.discovered_clue_ids:
                continue
            actions.append(
                ActionInfo(
                    action_id=f"action_inspect_{clue.clue_id}_{version}",
                    action_type="inspect",
                    target_id=clue.clue_id,
                    label=f"调查{clue.display_name}",
                    enabled=True,
                    disabled_reason=None,
                    expected_version=version,
                    parameters_schema={
                        "clue_id": {"type": "string", "description": clue.display_name}
                    },
                )
            )

        # --- Talk: one per available NPC at current location ---
        current_npcs = self.sm.get_available_npcs()
        for npc in current_npcs:
            npc_label = NPC_NAMES.get(npc.npc_id, npc.name)
            actions.append(
                ActionInfo(
                    action_id=f"action_talk_{npc.npc_id}_{version}",
                    action_type="talk",
                    target_id=npc.npc_id,
                    label=f"与{npc_label}交谈",
                    enabled=True,
                    disabled_reason=None,
                    expected_version=version,
                    parameters_schema={"npc_id": {"type": "string", "description": npc_label}},
                )
            )

        # --- Use Spirit Vision ---
        if "use_spirit_vision" in LOCATION_ACTIONS.get(current_loc, []):
            enabled = ps.spirituality >= 1
            actions.append(
                ActionInfo(
                    action_id=f"action_use_spirit_vision_{version}",
                    action_type="use_spirit_vision",
                    target_id=None,
                    label="使用灵视",
                    enabled=enabled,
                    disabled_reason="灵性不足" if not enabled else None,
                    expected_version=version,
                    parameters_schema={},
                )
            )

        # --- Perform Divination ---
        if "perform_divination" in LOCATION_ACTIONS.get(current_loc, []):
            actions.append(
                ActionInfo(
                    action_id=f"action_perform_divination_{version}",
                    action_type="perform_divination",
                    target_id=None,
                    label="进行占卜",
                    enabled=True,
                    disabled_reason=None,
                    expected_version=version,
                    parameters_schema={"question": {"type": "string", "description": "占卜问题"}},
                )
            )

        # --- Perform Ritual: one per performable ritual ---
        for ritual in self.sm.case.rituals:
            can_perform = (
                all(kid in ps.discovered_fact_ids for kid in ritual.required_knowledge_ids)
                and ps.current_location_id == ritual.space_condition
            )
            actions.append(
                ActionInfo(
                    action_id=f"action_perform_ritual_{ritual.ritual_id}_{version}",
                    action_type="perform_ritual",
                    target_id=ritual.ritual_id,
                    label=f"执行仪式：{ritual.name}",
                    enabled=can_perform,
                    disabled_reason="条件不满足" if not can_perform else None,
                    expected_version=version,
                    parameters_schema={
                        "ritual_id": {"type": "string"},
                        "materials": {"type": "array", "items": {"type": "string"}},
                    },
                )
            )

        # --- Use Item ---
        if "use_item" in LOCATION_ACTIONS.get(current_loc, []) and self.sm.case.items:
            for item in self.sm.case.items:
                actions.append(
                    ActionInfo(
                        action_id=f"action_use_item_{item.item_id}_{version}",
                        action_type="use_item",
                        target_id=item.item_id,
                        label=f"使用{item.name}",
                        enabled=True,
                        disabled_reason=None,
                        expected_version=version,
                        parameters_schema={"item_id": {"type": "string"}},
                    )
                )

        # --- Submit Hypothesis: one per submittable hypothesis ---
        for hypothesis in self.sm.case.hypotheses:
            can_submit = (
                all(cid in ps.discovered_clue_ids for cid in hypothesis.required_clue_ids)
                and hypothesis.hypothesis_id not in ps.confirmed_hypothesis_ids
                and hypothesis.hypothesis_id not in ps.rejected_hypothesis_ids
            )
            actions.append(
                ActionInfo(
                    action_id=f"action_submit_hypothesis_{hypothesis.hypothesis_id}_{version}",
                    action_type="submit_hypothesis",
                    target_id=hypothesis.hypothesis_id,
                    label=f"提交假设：{hypothesis.title}",
                    enabled=can_submit,
                    disabled_reason="线索不足" if not can_submit else None,
                    expected_version=version,
                    parameters_schema={"hypothesis_id": {"type": "string"}},
                )
            )

        # --- Rest ---
        actions.append(
            ActionInfo(
                action_id=f"action_rest_{version}",
                action_type="rest",
                target_id=None,
                label="休息恢复灵性",
                enabled=True,
                disabled_reason=None,
                expected_version=version,
                parameters_schema={},
            )
        )

        # --- Save ---
        actions.append(
            ActionInfo(
                action_id=f"action_save_{version}",
                action_type="save",
                target_id=None,
                label="保存游戏",
                enabled=True,
                disabled_reason=None,
                expected_version=version,
                parameters_schema={},
            )
        )

        return actions

    def _make_view(self) -> GameView:
        """Generate the current game view from state machine state."""
        ps = self.sm.player_state

        # Locations
        all_location_ids = sorted(
            set(
                [ps.current_location_id]
                + list(ps.visited_location_ids)
                + list(LOCATION_LABELS.keys())
            )
        )
        locations: list[LocationInfo] = []
        for lid in all_location_ids:
            label = LOCATION_LABELS.get(lid, lid)
            desc = LOCATION_DESCRIPTIONS.get(lid, "")
            clue_infos = [
                ClueInfo(
                    clue_id=c.clue_id,
                    display_name=c.display_name,
                    description=c.description,
                    source_type=c.source_type.value,
                    is_new=c.clue_id
                    in [
                        last_id
                        for e in self.sm.event_log.get_events(self.case_id)[-3:]
                        for last_id in (e.involved_clue_ids[-1:] if e.involved_clue_ids else [])
                    ],
                )
                for c in self.sm.get_available_clues()
                if c.location_id == lid
            ]
            npc_ids = [
                n.npc_id
                for n in self.sm.case.npcs
                if n.initial_location_id == lid and ps.npc_available.get(n.npc_id, True)
            ]
            locations.append(
                LocationInfo(
                    location_id=lid,
                    display_name=label,
                    description=desc,
                    is_current=lid == ps.current_location_id,
                    has_been_visited=lid in ps.visited_location_ids,
                    available_clues=clue_infos,
                    available_npcs=npc_ids,
                )
            )

        # Clues (discovered)
        clues = [
            ClueInfo(
                clue_id=c.clue_id,
                display_name=c.display_name,
                description=c.description,
                source_type=c.source_type.value,
            )
            for c in self.sm.get_discovered_clues()
        ]

        # NPCs at current location
        current_npcs = self.sm.get_available_npcs()
        npcs: list[NpcInfo] = []
        for n in current_npcs:
            claims = [
                ClaimInfo(
                    claim_id=c.claim_id,
                    content=c.content,
                    is_lie=c.claim_id in n.lie_claim_ids,
                    speaker_believes_it=c.speaker_believes_it,
                )
                for c in self.sm.get_npc_claims(n.npc_id)
            ]
            npcs.append(
                NpcInfo(
                    npc_id=n.npc_id,
                    name=n.name,
                    description=n.description,
                    emotion=(
                        n.default_emotion.value
                        if hasattr(n.default_emotion, "value")
                        else "neutral"
                    ),
                    current_location_id=n.initial_location_id,
                    available_claims=claims,
                )
            )

        # Hypotheses
        hypotheses: list[HypothesisInfo] = []
        for h in self.sm.case.hypotheses:
            found_clues = sum(1 for cid in h.required_clue_ids if cid in ps.discovered_clue_ids)
            hypotheses.append(
                HypothesisInfo(
                    hypothesis_id=h.hypothesis_id,
                    title=h.title,
                    description=h.description,
                    status=h.status.value,
                    min_confidence=h.min_confidence,
                    required_clue_count=len(h.required_clue_ids),
                    found_clue_count=found_clues,
                    can_submit=all(cid in ps.discovered_clue_ids for cid in h.required_clue_ids)
                    and h.hypothesis_id not in ps.confirmed_hypothesis_ids
                    and h.hypothesis_id not in ps.rejected_hypothesis_ids,
                )
            )

        # Endings
        endings = [
            EndingInfo(
                ending_id=e.ending_id,
                title=e.title,
                description=e.description,
                ending_type=e.ending_type.value,
            )
            for e in self.sm.case.endings
        ]

        # Items
        items = [
            ItemInfo(
                item_id=i.item_id,
                name=i.name,
                description=i.description,
                active_ability=i.active_ability,
                holding_cost=i.holding_cost,
            )
            for i in self.sm.case.items
        ]

        # Rituals
        rituals = [
            RitualInfo(
                ritual_id=r.ritual_id,
                name=r.name,
                purpose=r.purpose,
                required_materials=r.required_materials,
                space_condition=r.space_condition,
                steps=r.steps,
                can_perform=all(kid in ps.discovered_fact_ids for kid in r.required_knowledge_ids)
                and ps.current_location_id == r.space_condition,
            )
            for r in self.sm.case.rituals
        ]

        # Event log
        event_log = [
            EventLogEntry(
                event_id=e.event_id,
                event_type=e.event_type,
                description=e.description,
                timestamp=(
                    e.timestamp.isoformat()
                    if hasattr(e.timestamp, "isoformat")
                    else str(e.timestamp)
                ),
            )
            for e in self.sm.get_event_log()
        ]

        # Available actions — now structured
        available_actions = self._get_available_actions()

        # Final ending
        final_ending: EndingInfo | None = None
        if self.game_over and self.final_ending:
            found = next(
                (e for e in self.sm.case.endings if e.ending_id == self.final_ending),
                None,
            )
            if found:
                final_ending = EndingInfo(
                    ending_id=found.ending_id,
                    title=found.title,
                    description=found.description,
                    ending_type=found.ending_type.value,
                )

        return GameView(
            state_version=self.state_version,
            player=PlayerStatus(
                spirituality=ps.spirituality,
                corruption=ps.corruption_level,
                stability=ps.stability,
                current_location_id=ps.current_location_id,
                current_location_name=LOCATION_LABELS.get(
                    ps.current_location_id, ps.current_location_id
                ),
                visited_locations=locations,
            ),
            current_scene=ps.current_location_id,
            current_description=LOCATION_DESCRIPTIONS.get(
                ps.current_location_id,
                "你站在一个陌生地方。",
            ),
            available_actions=available_actions,
            clues=clues,
            npcs=npcs,
            hypotheses=hypotheses,
            endings=endings,
            items=items,
            rituals=rituals,
            event_log=event_log,
            game_over=self.game_over,
            final_ending=final_ending,
            ai_enabled=False,
        )

    def _validate_action_target(self, action: GameAction) -> str | None:
        """Returns an error code if the action's target is not in available_actions, else None."""
        available = self._get_available_actions()
        action_type = action.action_type.value
        target_id = action.target_id or ""

        for a in available:
            if a.action_type != action_type:
                continue
            # Match by target_id — empty-string target matches actions without a target
            if (a.target_id is None and not target_id) or (a.target_id == target_id):
                if a.enabled:
                    return None
                return ERROR_TARGET_NOT_AVAILABLE
        return ERROR_INVALID_TARGET

    def execute_action(
        self, action: GameAction
    ) -> tuple[bool, str | None, list[dict[str, Any]], str | None]:
        """Execute a game action.

        Returns (success, error_code, events, ending_id).
        """
        if self.game_over:
            return False, ERROR_GAME_ALREADY_FINISHED, [], None

        if action.expected_version != self.state_version:
            return False, ERROR_STATE_VERSION_CONFLICT, [], None

        # Validate target against available_actions
        target_error = self._validate_action_target(action)
        if target_error is not None:
            return False, target_error, [], None

        events: list[dict[str, Any]] = []

        try:
            if action.action_type == ActionType.TRAVEL:
                location_id = action.target_id or action.parameters.get("location_id", "")
                if not location_id:
                    return False, ERROR_INVALID_TARGET, [], None
                self.sm.move_to_location(location_id)
                self.state_version += 1
                events.append(
                    {
                        "event_type": "travel",
                        "description": f"移动到了{LOCATION_LABELS.get(location_id, location_id)}",
                    }
                )

            elif action.action_type == ActionType.INSPECT:
                clue_id = action.target_id or action.parameters.get("clue_id", "")
                if not clue_id:
                    return False, ERROR_INVALID_TARGET, [], None
                success, event = self.sm.discover_clue(clue_id)
                if success and event:
                    self.state_version += 1
                    events.append(
                        {
                            "event_type": "clue_discovered",
                            "description": event.description,
                            "involved_clue_ids": [clue_id],
                        }
                    )
                elif not success:
                    return False, ERROR_TARGET_NOT_AVAILABLE, [], None

            elif action.action_type == ActionType.TALK:
                npc_id = action.target_id or action.parameters.get("npc_id", "")
                action.parameters.get("claim_id", "")
                if npc_id:
                    claims = self.sm.get_npc_claims(npc_id)
                    for c in claims:
                        if c.claim_id not in self.sm.player_state.revealed_claim_ids:
                            self.sm.player_state.revealed_claim_ids.append(c.claim_id)
                    self.state_version += 1
                    events.append(
                        {
                            "event_type": "talked_to_npc",
                            "description": f"与{NPC_NAMES.get(npc_id, npc_id)}交谈",
                            "involved_npc_ids": [npc_id],
                        }
                    )

            elif action.action_type == ActionType.USE_SPIRIT_VISION:
                action.target_id or action.parameters.get("target_id", "")
                if self.sm.player_state.spirituality < 1:
                    return False, ERROR_RESOURCE_INSUFFICIENT, [], None
                self.sm.player_state.spirituality = max(0, self.sm.player_state.spirituality - 1)
                event_id = "evt_spirit_vision"
                if event_id not in self.sm.player_state.completed_events:
                    self.sm.player_state.completed_events.append(event_id)
                # Check for spirit vision clue
                for clue in self.sm.case.clues:
                    if (
                        clue.requires_any_tags
                        and "evt_spirit_vision" in clue.requires_any_tags
                        and clue.clue_id not in self.sm.player_state.discovered_clue_ids
                    ):
                        success, event = self.sm.discover_clue(clue.clue_id)
                        if success and event:
                            events.append(
                                {
                                    "event_type": "clue_discovered",
                                    "description": event.description,
                                    "involved_clue_ids": [clue.clue_id],
                                }
                            )
                self.state_version += 1
                events.append(
                    {
                        "event_type": "spirit_vision",
                        "description": "你使用了灵视。灰雾之中，隐藏的痕迹渐渐显现……",
                    }
                )

            elif action.action_type == ActionType.PERFORM_DIVINATION:
                question = action.parameters.get("question", "寻求指引")
                result = self.sm.perform_divination(question, self.seed + self.state_version)
                self.state_version += 1
                events.append(
                    {
                        "event_type": "divination",
                        "description": f"占卜结果：{result.symbolic_image}",
                        "divination_result": result.model_dump(),
                    }
                )

            elif action.action_type == ActionType.PERFORM_RITUAL:
                ritual_id = action.target_id or action.parameters.get("ritual_id", "")
                materials = action.parameters.get("materials", [])
                if not ritual_id:
                    return False, ERROR_INVALID_TARGET, [], None
                success, message, corruption = self.sm.perform_ritual(
                    ritual_id, materials, self.seed + self.state_version
                )
                self.state_version += 1
                events.append(
                    {
                        "event_type": "ritual",
                        "description": message,
                        "success": success,
                        "corruption_change": corruption,
                    }
                )

            elif action.action_type == ActionType.USE_ITEM:
                item_id = action.target_id or action.parameters.get("item_id", "")
                if not item_id:
                    return False, ERROR_INVALID_TARGET, [], None
                item = next((i for i in self.sm.case.items if i.item_id == item_id), None)
                if item is None:
                    return False, ERROR_TARGET_NOT_AVAILABLE, [], None
                # Use item ability - simplified for MVP
                self.state_version += 1
                events.append(
                    {
                        "event_type": "item_used",
                        "description": f"使用了{item.name}：{item.active_ability}",
                    }
                )

            elif action.action_type == ActionType.SUBMIT_HYPOTHESIS:
                hypothesis_id = action.target_id or action.parameters.get("hypothesis_id", "")
                if not hypothesis_id:
                    return False, ERROR_INVALID_TARGET, [], None
                success, event, ending_id = self.sm.submit_hypothesis(hypothesis_id)
                if success:
                    self.state_version += 1
                    events.append(
                        {
                            "event_type": "hypothesis_submitted",
                            "description": event.description if event else "提交了假设",
                        }
                    )
                    if ending_id:
                        self.game_over = True
                        self.final_ending = ending_id
                        ending_obj = next(
                            (e for e in self.sm.case.endings if e.ending_id == ending_id),
                            None,
                        )
                        if ending_obj:
                            events.append(
                                {
                                    "event_type": "game_over",
                                    "description": f"结局：{ending_obj.title}",
                                    "ending_id": ending_id,
                                }
                            )
                    return True, None, events, ending_id
                else:
                    return False, ERROR_TARGET_NOT_AVAILABLE, [], None

            elif action.action_type == ActionType.REST:
                self.sm.player_state.spirituality = min(5, self.sm.player_state.spirituality + 2)
                self.state_version += 1
                events.append(
                    {
                        "event_type": "rest",
                        "description": "你停下来休息，灵性得到了一些恢复。",
                    }
                )

            elif action.action_type == ActionType.SAVE:
                # Save is handled at the route level
                events.append(
                    {
                        "event_type": "save",
                        "description": "游戏已保存。",
                    }
                )

            elif action.action_type == ActionType.LOAD:
                # Load is handled at the route level
                pass

            else:
                return False, "UNKNOWN_ACTION", [], None

        except Exception as e:
            return False, ERROR_INTERNAL, [], str(e)

        return True, None, events, None

    def to_save_dict(self) -> dict[str, Any]:
        """Serialize session to dict for SQLite storage."""
        return {
            "save_id": self.session_id,
            "case_id": self.case_id,
            "seed": self.seed,
            "state_version": self.state_version,
            "game_over": self.game_over,
            "final_ending": self.final_ending,
            "player_state": self._serialize_player_state(),
            "event_log": self._serialize_event_log(),
        }

    def _serialize_player_state(self) -> str:
        raw = self.sm.player_state.model_dump(mode="json")
        return json.dumps(raw, ensure_ascii=False)

    def _serialize_event_log(self) -> str:
        raw = [e.model_dump(mode="json") for e in self.sm.get_event_log()]
        return json.dumps(raw, ensure_ascii=False)

    @classmethod
    def from_save_dict(
        cls,
        data: dict[str, Any],
        state_machine: CaseStateMachine,
    ) -> GameSession:
        """Restore session from a save dict."""
        session = cls(
            session_id=data["save_id"],
            case_id=data["case_id"],
            state_machine=state_machine,
            seed=data.get("seed", 0),
        )
        session.state_version = data.get("state_version", 0)
        session.game_over = bool(data.get("game_over", False))
        session.final_ending = data.get("final_ending")

        # Restore player state
        player_raw = data.get("player_state", "{}")
        player_dict = json.loads(player_raw) if isinstance(player_raw, str) else player_raw
        session.sm.player_state = PlayerCaseState(**player_dict)

        # Restore event log
        log_raw = data.get("event_log", "[]")
        log_list = json.loads(log_raw) if isinstance(log_raw, str) else log_raw
        session.sm.event_log.clear()
        for e_data in log_list:
            session.sm.event_log.add_event(CaseEvent(**e_data))

        return session


# NPC display names
NPC_NAMES: dict[str, str] = {
    "npc_landlord": "弗雷德里克（房东）",
    "npc_doctor": "塞巴斯蒂安医生",
    "npc_shopkeeper": "马尔科（材料店主）",
    "npc_neighbor": "安娜（邻居）",
    "npc_inspector": "哈罗德探员",
    "npc_collector": "阿尔德里奇（收藏家）",
}


class GameManager:
    """Manages multiple game sessions and provides the public API."""

    def __init__(self, db: GameDatabase) -> None:
        self.db = db
        self._sessions: dict[str, GameSession] = {}

    def list_cases(self) -> list[dict[str, str]]:
        """List available cases."""
        cases: list[dict[str, str]] = []
        if CASE_DIR.exists():
            for case_dir in sorted(CASE_DIR.iterdir()):
                case_file = case_dir / "case.json"
                if case_file.exists():
                    import json

                    with open(case_file) as f:
                        data = json.load(f)
                    cases.append(
                        {
                            "case_id": data.get("case_id", case_dir.name),
                            "title": data.get("title", case_dir.name),
                            "description": data.get("description", ""),
                            "version": data.get("version", "0.1.0"),
                        }
                    )
        return cases

    def get_case_metadata(self, case_id: str) -> dict[str, str] | None:
        """Get metadata for a specific case."""
        case_dir = CASE_DIR / case_id
        case_file = case_dir / "case.json"
        if not case_file.exists():
            return None
        import json

        with open(case_file) as f:
            data = json.load(f)
        return {
            "case_id": data.get("case_id", case_id),
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "version": data.get("version", "0.1.0"),
        }

    def create_game(self, case_id: str, seed: int | None = None) -> GameSession:
        """Create a new game session."""
        case_dir = CASE_DIR / case_id
        if not case_dir.exists():
            raise ValueError(f"Case not found: {case_id}")

        loader = CaseLoader(case_dir)
        case = loader.load_case()
        sm = CaseStateMachine(case)

        actual_seed = seed if seed is not None else random.randint(0, 2**31 - 1)
        sm.player_state.seed = actual_seed
        sm.player_state.spirituality = 5
        sm.player_state.corruption_level = 0
        sm.player_state.stability = 5

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        save_id = f"{case_id}_{timestamp}_{actual_seed % 10000:04d}"

        session = GameSession(save_id, case_id, sm, actual_seed)
        self._sessions[save_id] = session
        return session

    def get_session(self, save_id: str) -> GameSession | None:
        """Get a live session."""
        return self._sessions.get(save_id)

    def save_session(self, save_id: str) -> bool:
        """Persist session to SQLite."""
        session = self._sessions.get(save_id)
        if session is None:
            return False
        save_dict = session.to_save_dict()
        view_cache = json.dumps(session._make_view().model_dump(mode="json"), ensure_ascii=False)
        self.db.save_game(
            save_id=save_dict["save_id"],
            case_id=save_dict["case_id"],
            seed=save_dict["seed"],
            state_version=save_dict["state_version"],
            game_over=save_dict["game_over"],
            player_state_json=save_dict["player_state"],
            event_log_json=save_dict["event_log"],
            view_cache=view_cache,
        )
        return True

    def load_session(self, save_id: str) -> GameSession | None:
        """Load session from SQLite into memory."""
        row = self.db.load_game(save_id)
        if row is None:
            return None

        case_dir = CASE_DIR / row["case_id"]
        if not case_dir.exists():
            return None
        loader = CaseLoader(case_dir)
        case = loader.load_case()
        sm = CaseStateMachine(case)

        # Parse JSON fields
        player_state_str = row["player_state"]
        if isinstance(player_state_str, str):
            player_dict = json.loads(player_state_str)
        else:
            player_dict = player_state_str

        event_log_str = row["event_log"]
        log_list = json.loads(event_log_str) if isinstance(event_log_str, str) else event_log_str

        sm.player_state = PlayerCaseState(**player_dict)
        sm.player_state.seed = row.get("seed", 0)
        sm.event_log.clear()
        for e_data in log_list:
            sm.event_log.add_event(CaseEvent(**e_data))

        session = GameSession(
            session_id=row["save_id"],
            case_id=row["case_id"],
            state_machine=sm,
            seed=row.get("seed", 0),
        )
        session.state_version = row.get("state_version", 0)
        session.game_over = bool(row.get("game_over", False))

        self._sessions[save_id] = session
        return session

    def list_saves(self, case_id: str | None = None) -> list[dict[str, Any]]:
        """List all saves."""
        return self.db.list_saves(case_id)
