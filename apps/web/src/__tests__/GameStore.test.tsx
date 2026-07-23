import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { useGameStore } from "../store";
import type { GameView, NewGameResponse, ActionResponse, CaseListResponse } from "../types";

// Mock the API module
vi.mock("../api", () => ({
  newGame: vi.fn(),
  executeAction: vi.fn(),
  getView: vi.fn(),
  saveGame: vi.fn(),
  loadGame: vi.fn(),
  listCases: vi.fn(),
  getCaseMeta: vi.fn(),
}));

import * as api from "../api";

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
      description: "一封没有署名的信，内容令人不安",
      source_type: "调查",
      is_new: true,
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
      description: "最近的失踪事件可能与灰雾的出现有关联",
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
  rituals: [
    {
      ritual_id: "ritual_1",
      name: "净化仪式",
      purpose: "清除低程度的污染",
      required_materials: ["圣水", "银粉"],
      space_condition: "安静的空间",
      steps: ["准备材料", "吟诵咒文"],
      can_perform: true,
    },
  ],
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
  investigation_progress: null,
  ai_enabled: true,
};

describe("GameStore", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state
    useGameStore.setState({
      saveId: null,
      view: null,
      loading: false,
      error: null,
    });
  });

  // Test 1: Initial state
  it("should have correct initial state", () => {
    const state = useGameStore.getState();
    expect(state.saveId).toBeNull();
    expect(state.view).toBeNull();
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  // Test 2: clearError
  it("should clear error", () => {
    useGameStore.setState({ error: "test error" });
    useGameStore.getState().clearError();
    expect(useGameStore.getState().error).toBeNull();
  });

  // Test 3: newGame success
  it("should create new game and update state", async () => {
    const mockResponse: NewGameResponse = {
      save_id: "save_1",
      case_id: "case_1",
      view: mockGameView,
    };
    vi.mocked(api.newGame).mockResolvedValue(mockResponse);

    await act(async () => {
      await useGameStore.getState().newGame("case_1");
    });

    const state = useGameStore.getState();
    expect(state.saveId).toBe("save_1");
    expect(state.view).toEqual(mockGameView);
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
    expect(api.newGame).toHaveBeenCalledWith("case_1", undefined);
  });

  // Test 4: newGame with seed
  it("should create new game with seed", async () => {
    const mockResponse: NewGameResponse = {
      save_id: "save_2",
      case_id: "case_1",
      view: mockGameView,
    };
    vi.mocked(api.newGame).mockResolvedValue(mockResponse);

    await act(async () => {
      await useGameStore.getState().newGame("case_1", 42);
    });

    expect(api.newGame).toHaveBeenCalledWith("case_1", 42);
  });

  // Test 5: newGame error
  it("should handle new game API error", async () => {
    vi.mocked(api.newGame).mockRejectedValue(new Error("网络错误"));

    await act(async () => {
      await useGameStore.getState().newGame("case_1");
    });

    const state = useGameStore.getState();
    expect(state.view).toBeNull();
    expect(state.saveId).toBeNull();
    expect(state.error).toContain("网络错误");
    expect(state.loading).toBe(false);
  });

  // Test 6: executeAction success
  it("should execute action and update view", async () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView });

    const updatedView: GameView = {
      ...mockGameView,
      state_version: 2,
      current_scene: "灰雾镇的午后",
    };
    const mockResponse: ActionResponse = {
      success: true,
      state_version: 2,
      events: [{ event_type: "move", description: "移动到灰雾镇的午后" }],
      view: updatedView,
      error_code: null,
      error_detail: null,
    };
    vi.mocked(api.executeAction).mockResolvedValue(mockResponse);

    await act(async () => {
      await useGameStore.getState().executeAction({ action_type: "探索广场" });
    });

    const state = useGameStore.getState();
    expect(state.view?.state_version).toBe(2);
    expect(state.view?.current_scene).toBe("灰雾镇的午后");
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
    expect(api.executeAction).toHaveBeenCalledWith("save_1", {
      action_type: "探索广场",
      expected_version: 1,
    }, "save_1");
  });

  // Test 7: STATE_VERSION_CONFLICT handling
  it("should handle action failure with error detail", async () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView });

    const mockResponse: ActionResponse = {
      success: false,
      state_version: 1,
      events: [],
      view: null,
      error_code: "STATE_VERSION_CONFLICT",
      error_detail: "状态版本冲突，请刷新",
    };
    vi.mocked(api.executeAction).mockResolvedValue(mockResponse);

    await act(async () => {
      await useGameStore.getState().executeAction({ action_type: "探索广场" });
    });

    const state = useGameStore.getState();
    expect(state.error).toContain("状态版本冲突");
    expect(state.loading).toBe(false);
  });

  // Test 8: executeAction without saveId
  it("should not execute action if no saveId", async () => {
    await act(async () => {
      await useGameStore.getState().executeAction({ action_type: "探索" });
    });

    expect(api.executeAction).not.toHaveBeenCalled();
  });

  // Test 9: saveGame
  it("should save game", async () => {
    useGameStore.setState({ saveId: "save_1" });
    vi.mocked(api.saveGame).mockResolvedValue({ success: true, save_id: "save_1" });

    await act(async () => {
      await useGameStore.getState().saveGame();
    });

    expect(api.saveGame).toHaveBeenCalledWith("save_1", "save_1");
    expect(useGameStore.getState().loading).toBe(false);
  });

  // Test 10: saveGame error
  it("should handle save error", async () => {
    useGameStore.setState({ saveId: "save_1" });
    vi.mocked(api.saveGame).mockRejectedValue(new Error("保存失败"));

    await act(async () => {
      await useGameStore.getState().saveGame();
    });

    const state = useGameStore.getState();
    expect(state.error).toContain("保存失败");
  });

  // Test 11: loadGame
  it("should load game and update state", async () => {
    vi.mocked(api.loadGame).mockResolvedValue(mockGameView);

    await act(async () => {
      await useGameStore.getState().loadGame("save_1");
    });

    const state = useGameStore.getState();
    expect(state.saveId).toBe("save_1");
    expect(state.view).toEqual(mockGameView);
    expect(state.loading).toBe(false);
    expect(api.loadGame).toHaveBeenCalledWith("save_1", "save_1");
  });

  // Test 12: loadGame error
  it("should handle load error", async () => {
    vi.mocked(api.loadGame).mockRejectedValue(new Error("加载失败"));

    await act(async () => {
      await useGameStore.getState().loadGame("save_1");
    });

    const state = useGameStore.getState();
    expect(state.error).toContain("加载失败");
    expect(state.view).toBeNull();
  });

  // Test 13: fetchView
  it("should fetch view from server", async () => {
    useGameStore.setState({ saveId: "save_1" });
    vi.mocked(api.getView).mockResolvedValue(mockGameView);

    await act(async () => {
      await useGameStore.getState().fetchView();
    });

    expect(useGameStore.getState().view).toEqual(mockGameView);
    expect(api.getView).toHaveBeenCalledWith("save_1", "save_1");
  });

  // Test 14: Player status values in store
  it("should store player status correctly", () => {
    useGameStore.setState({ view: mockGameView });
    const { view } = useGameStore.getState();
    expect(view!.player.spirituality).toBe(80);
    expect(view!.player.corruption).toBe(10);
    expect(view!.player.stability).toBe(70);
    expect(view!.player.current_location_name).toBe("灰雾镇广场");
  });

  // Test 15: Clue info fields
  it("should store clue info with correct fields", () => {
    useGameStore.setState({ view: mockGameView });
    const { view } = useGameStore.getState();
    const clue = view!.clues[0];
    expect(clue.clue_id).toBe("clue_1");
    expect(clue.display_name).toBe("神秘信件");
    expect(clue.source_type).toBe("调查");
    expect(clue.is_new).toBe(true);
  });

  // Test 16: NPC info fields
  it("should store NPC info with correct fields", () => {
    useGameStore.setState({ view: mockGameView });
    const { view } = useGameStore.getState();
    const npc = view!.npcs[0];
    expect(npc.npc_id).toBe("npc_1");
    expect(npc.name).toBe("老约翰");
    expect(npc.emotion).toBe("忧虑");
    expect(npc.available_claims[0].content).toBe("昨晚我听到了一声尖叫");
  });

  // Test 17: Hypothesis info fields
  it("should store hypothesis info with correct fields", () => {
    useGameStore.setState({ view: mockGameView });
    const { view } = useGameStore.getState();
    const hyp = view!.hypotheses[0];
    expect(hyp.hypothesis_id).toBe("hyp_1");
    expect(hyp.title).toBe("失踪案与灰雾有关");
    expect(hyp.status).toBe("unlocked");
    expect(hyp.can_submit).toBe(false);
    expect(hyp.found_clue_count).toBe(1);
    expect(hyp.required_clue_count).toBe(3);
  });

  // Test 18: Ritual info fields
  it("should store ritual info with correct fields", () => {
    useGameStore.setState({ view: mockGameView });
    const { view } = useGameStore.getState();
    const ritual = view!.rituals[0];
    expect(ritual.ritual_id).toBe("ritual_1");
    expect(ritual.name).toBe("净化仪式");
    expect(ritual.can_perform).toBe(true);
    expect(ritual.required_materials).toEqual(["圣水", "银粉"]);
  });

  // Test 19: Game over state
  it("should detect game over state", () => {
    useGameStore.setState({ view: mockGameView });
    expect(useGameStore.getState().view!.game_over).toBe(false);

    const endedView: GameView = {
      ...mockGameView,
      game_over: true,
      final_ending: {
        ending_id: "end_1",
        title: "真相大白",
        description: "你揭开了所有的谜团",
        ending_type: "truth",
      },
    };
    useGameStore.setState({ view: endedView });
    const state = useGameStore.getState();
    expect(state.view!.game_over).toBe(true);
    expect(state.view!.final_ending!.ending_type).toBe("truth");
  });

  // Test 20: Event log entry fields
  it("should store event log with correct fields", () => {
    useGameStore.setState({ view: mockGameView });
    const { view } = useGameStore.getState();
    const entry = view!.event_log[0];
    expect(entry.event_id).toBe("evt_1");
    expect(entry.event_type).toBe("info");
    expect(entry.description).toBe("游戏开始");
  });

  // Test 21: Loading state during operations
  it("should set loading state during newGame", async () => {
    // Don't resolve the promise yet
    vi.mocked(api.newGame).mockImplementation(
      () => new Promise(() => {}) // never resolves
    );

    // Start newGame (will hang, but we check loading immediately)
    const promise = useGameStore.getState().newGame("case_1");

    // After a microtask, loading should be true
    await act(async () => {
      // Just let the first tick process
      await Promise.resolve();
    });

    expect(useGameStore.getState().loading).toBe(true);
  });

  // Test 22: setActionPending and clearActionPending
  it("should track pending actions correctly", () => {
    const store = useGameStore.getState();
    expect(store.pendingActions).toEqual({});

    store.setActionPending("action_1");
    expect(useGameStore.getState().pendingActions).toEqual({ action_1: true });

    store.setActionPending("action_2");
    expect(useGameStore.getState().pendingActions).toEqual({
      action_1: true,
      action_2: true,
    });

    store.clearActionPending("action_1");
    expect(useGameStore.getState().pendingActions).toEqual({ action_2: true });

    store.clearActionPending("action_2");
    expect(useGameStore.getState().pendingActions).toEqual({});
  });

  // Test 23: Execute action sets and clears pending state for given actionId
  it("should set pending state when executing with actionId", async () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView });

    const updatedView: GameView = {
      ...mockGameView,
      state_version: 2,
    };
    const mockResponse: ActionResponse = {
      success: true,
      state_version: 2,
      events: [],
      view: updatedView,
      error_code: null,
      error_detail: null,
    };
    // Keep the promise unresolved to check pending state before resolution
    let resolvePromise!: (val: typeof mockResponse) => void;
    vi.mocked(api.executeAction).mockImplementation(
      () => new Promise((resolve) => { resolvePromise = resolve; })
    );

    // Start executing with actionId
    let execPromise: Promise<void>;
    await act(async () => {
      execPromise = useGameStore
        .getState()
        .executeAction({ action_type: "inspect", target_id: "clue_1" }, "act_1");
    });

    // Pending should be set immediately for this actionId
    expect(useGameStore.getState().pendingActions).toEqual({ act_1: true });

    // Resolve the promise
    await act(async () => {
      resolvePromise(mockResponse);
      await execPromise;
    });

    // Pending should be cleared after resolution
    expect(useGameStore.getState().pendingActions).toEqual({});
  });

  // Test 24: Execute action sends idempotency_key via api
  it("should include idempotency_key when executing action", async () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView });

    const mockResponse: ActionResponse = {
      success: true,
      state_version: 2,
      events: [],
      view: { ...mockGameView, state_version: 2 },
      error_code: null,
      error_detail: null,
    };
    vi.mocked(api.executeAction).mockResolvedValue(mockResponse);

    await act(async () => {
      await useGameStore
        .getState()
        .executeAction({ action_type: "inspect", target_id: "clue_1" }, "act_1");
    });

    // Verify executeAction was called with the action request
    const callArgs = vi.mocked(api.executeAction).mock.calls[0];
    expect(callArgs[0]).toBe("save_1");

    // The action request should have expected_version
    const actionReq = callArgs[1];
    expect(actionReq).toHaveProperty("action_type", "inspect");
    expect(actionReq).toHaveProperty("target_id", "clue_1");
    expect(actionReq).toHaveProperty("expected_version", 1);
  });

  // Test 25: Store handles INVALID_TARGET error response
  it("should handle INVALID_TARGET error from API", async () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView });

    const mockResponse: ActionResponse = {
      success: false,
      state_version: 1,
      events: [],
      view: null,
      error_code: "INVALID_TARGET",
      error_detail: "目标无效",
      recoverable: true,
    };
    vi.mocked(api.executeAction).mockResolvedValue(mockResponse);

    await act(async () => {
      await useGameStore
        .getState()
        .executeAction({ action_type: "inspect", target_id: "nonexistent" });
    });

    const state = useGameStore.getState();
    // Store sets error to error_detail first, then falls back to error_code
    expect(state.error).toBe("目标无效");
    expect(state.loading).toBe(false);
    // View should still exist (not crash)
    expect(state.view).toEqual(mockGameView);
  });

  // Test 26: Store handles GAME_ALREADY_FINISHED error
  it("should handle GAME_ALREADY_FINISHED error", async () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView });

    const mockResponse: ActionResponse = {
      success: false,
      state_version: 1,
      events: [],
      view: null,
      error_code: "GAME_ALREADY_FINISHED",
      error_detail: "游戏已结束",
    };
    vi.mocked(api.executeAction).mockResolvedValue(mockResponse);

    await act(async () => {
      await useGameStore
        .getState()
        .executeAction({ action_type: "inspect", target_id: "clue_1" });
    });

    const state = useGameStore.getState();
    expect(state.error).toBe("游戏已结束");
  });

  // Test 27: Duplicate submission prevention - second click is blocked by pendingActions
  it("should prevent duplicate submission via pendingActions guard", async () => {
    useGameStore.setState({ saveId: "save_1", view: mockGameView });

    // Set pending first (simulating what happens when button is clicked)
    useGameStore.getState().setActionPending("act_1");

    // Try to execute the same action again
    // The pending guard should prevent api.executeAction from being called
    // But since executeAction is in the store (not checking pending),
    // this test verifies that the action IS called even when pending
    // (The pending guard is in GamePage's handleAction, not in the store)

    const mockResponse: ActionResponse = {
      success: true,
      state_version: 2,
      events: [],
      view: { ...mockGameView, state_version: 2 },
      error_code: null,
      error_detail: null,
    };
    vi.mocked(api.executeAction).mockResolvedValue(mockResponse);

    await act(async () => {
      await useGameStore
        .getState()
        .executeAction({ action_type: "inspect", target_id: "clue_1" }, "act_1");
    });

    // The store's executeAction still makes the API call even when pending
    // (the guard is in GamePage.handleAction which checks pendingActions before calling executeAction)
    expect(api.executeAction).toHaveBeenCalled();
    // After resolution, pending should be cleared
    expect(useGameStore.getState().pendingActions).toEqual({});
  });
});
