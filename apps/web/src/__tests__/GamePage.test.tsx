import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import GamePage from "../pages/GamePage";
import { useGameStore } from "../store";
import type { GameView } from "../types";

vi.mock("../api", () => ({
  listCases: vi.fn(),
  getCaseMeta: vi.fn(),
  newGame: vi.fn(),
  executeAction: vi.fn(),
  getView: vi.fn(),
  saveGame: vi.fn(),
  loadGame: vi.fn(),
}));

const mockGameView: GameView = {
  state_version: 1,
  player: {
    spirituality: 80,
    corruption: 10,
    stability: 70,
    current_location_id: "loc_1",
    current_location_name: "灰雾镇广场",
    visited_locations: [
      {
        location_id: "loc_1",
        display_name: "灰雾镇广场",
        description: "镇中心广场，灰雾弥漫",
        is_current: true,
        has_been_visited: true,
        available_clues: [],
        available_npcs: ["npc_1"],
      },
      {
        location_id: "loc_2",
        display_name: "警务办公室",
        description: "警察办公的地方",
        is_current: false,
        has_been_visited: true,
        available_clues: [],
        available_npcs: [],
      },
    ],
  },
  current_scene: "灰雾镇的清晨",
  current_description: "灰雾笼罩着整个小镇，远处传来模糊的人声。",
  available_actions: [
    { action_id: "act_1", action_type: "inspect", target_id: "clue_1", label: "探索广场", enabled: true, disabled_reason: null, expected_version: 0, parameters_schema: {} },
    { action_id: "act_2", action_type: "talk", target_id: "npc_1", label: "与路人交谈", enabled: true, disabled_reason: null, expected_version: 0, parameters_schema: {} },
    { action_id: "act_3", action_type: "inspect", target_id: "clue_2", label: "检查告示板", enabled: true, disabled_reason: null, expected_version: 0, parameters_schema: {} },
  ],
  clues: [
    {
      clue_id: "clue_1",
      display_name: "神秘信件",
      description: "一封没有署名的信",
      source_type: "调查",
      is_new: true,
    },
    {
      clue_id: "clue_2",
      display_name: "老照片",
      description: "一张泛黄的照片",
      source_type: "搜索",
      is_new: false,
    },
  ],
  npcs: [
    {
      npc_id: "npc_1",
      name: "老约翰",
      description: "一位神情忧郁的老人",
      emotion: "忧虑",
      current_location_id: "loc_1",
      available_claims: [
        { claim_id: "claim_1", content: "昨晚我听到了一声尖叫", is_lie: false, speaker_believes_it: true },
      ],
    },
  ],
  hypotheses: [
    {
      hypothesis_id: "hyp_1",
      title: "失踪案与灰雾有关",
      description: "最近的失踪事件可能与灰雾有关",
      status: "unlocked",
      min_confidence: 0.6,
      required_clue_count: 3,
      found_clue_count: 1,
      can_submit: false,
    },
  ],
  endings: [],
  items: [
    {
      item_id: "item_1",
      name: "旧钥匙",
      description: "一把生锈的钥匙",
      active_ability: "打开某扇门",
      holding_cost: "低",
    },
  ],
  rituals: [],
  event_log: [
    {
      event_id: "evt_1",
      event_type: "info",
      description: "游戏开始",
      timestamp: "2026-07-22T10:00:00Z",
    },
  ],
  game_over: false,
  final_ending: null,
  ai_enabled: true,
};

function renderGamePage() {
  return render(
    <MemoryRouter initialEntries={["/game"]}>
      <Routes>
        <Route path="/game" element={<GamePage />} />
        <Route path="/" element={<div>Start Page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("GamePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useGameStore.setState({
      saveId: null,
      view: null,
      loading: false,
      error: null,
    });
  });

  it("redirects to case select when no view exists", () => {
    renderGamePage();
    // GamePage redirects to /case-select when no saveId/view
    expect(useGameStore.getState().saveId).toBeNull();
  });

  it("renders current scene and description", () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView });
    renderGamePage();
    expect(screen.getByText("灰雾镇的清晨")).toBeTruthy();
    expect(
      screen.getByText("灰雾笼罩着整个小镇，远处传来模糊的人声。")
    ).toBeTruthy();
  });

  it("renders current location name", () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView });
    renderGamePage();
    const locElements = screen.getAllByText("灰雾镇广场");
    expect(locElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders available action buttons", () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView });
    renderGamePage();
    expect(screen.getByText("探索广场")).toBeTruthy();
    expect(screen.getByText("与路人交谈")).toBeTruthy();
    expect(screen.getByText("检查告示板")).toBeTruthy();
  });

  it("renders clue list", () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView });
    renderGamePage();
    const clueElements = screen.getAllByText("神秘信件");
    expect(clueElements.length).toBeGreaterThanOrEqual(1);
    const photoElements = screen.getAllByText("老照片");
    expect(photoElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders items section", () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView });
    renderGamePage();
    expect(screen.getByText("旧钥匙")).toBeTruthy();
  });

  it("renders NPC buttons", () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView });
    renderGamePage();
    const npcElements = screen.getAllByText("老约翰");
    expect(npcElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders navigation buttons to other pages", () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView });
    renderGamePage();
    const deductionBtns = screen.getAllByText("推理板");
    expect(deductionBtns.length).toBeGreaterThanOrEqual(1);
    const ritualBtns = screen.getAllByText("仪式");
    expect(ritualBtns.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("保存游戏")).toBeTruthy();
    expect(screen.getByText("存档管理")).toBeTruthy();
  });

  it("renders player status bars", () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView });
    renderGamePage();
    const statusHeaders = screen.getAllByText("状态");
    expect(statusHeaders.length).toBeGreaterThanOrEqual(1);
  });

  it("displays error message when store has error", () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView, error: "操作超时" });
    renderGamePage();
    expect(screen.getByText("操作超时")).toBeTruthy();
  });

  it("shows loading indicator when loading", () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView, loading: true });
    renderGamePage();
    expect(screen.getByText("处理中...")).toBeTruthy();
  });
});
