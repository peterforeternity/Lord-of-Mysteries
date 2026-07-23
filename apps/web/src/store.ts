import { create } from "zustand";
import type { GameView, ActionRequest } from "./types";
import * as api from "./api";

/** Action request that can omit expected_version (store fills it in) */
export type ActionRequestInput = Omit<ActionRequest, "expected_version"> & {
  expected_version?: number;
};

interface GameState {
  saveId: string | null;
  view: GameView | null;
  loading: boolean;
  error: string | null;

  newGame: (caseId: string, seed?: number) => Promise<void>;
  executeAction: (action: ActionRequestInput) => Promise<void>;
  saveGame: () => Promise<void>;
  loadGame: (saveId: string) => Promise<void>;
  fetchView: () => Promise<void>;
  clearError: () => void;
}

export const useGameStore = create<GameState>((set, get) => ({
  saveId: null,
  view: null,
  loading: false,
  error: null,

  clearError: () => set({ error: null }),

  newGame: async (caseId: string, seed?: number) => {
    set({ loading: true, error: null });
    try {
      const res = await api.newGame(caseId, seed);
      set({ saveId: res.save_id, view: res.view, loading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "创建游戏失败",
        loading: false,
      });
    }
  },

  executeAction: async (action: ActionRequestInput) => {
    const { saveId, view } = get();
    if (!saveId) return;
    const actionWithVersion: ActionRequest = {
      ...action,
      expected_version: action.expected_version ?? (view?.state_version ?? 0),
    } as ActionRequest;
    set({ loading: true, error: null });
    try {
      const res = await api.executeAction(saveId, actionWithVersion);
      if (res.success && res.view) {
        set({ view: res.view, loading: false });
      } else {
        set({
          error: res.error_detail || res.error_code || "操作失败",
          loading: false,
        });
      }
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "执行操作失败",
        loading: false,
      });
    }
  },

  saveGame: async () => {
    const { saveId } = get();
    if (!saveId) return;
    set({ loading: true, error: null });
    try {
      await api.saveGame(saveId);
      set({ loading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "保存游戏失败",
        loading: false,
      });
    }
  },

  loadGame: async (sid: string) => {
    set({ loading: true, error: null });
    try {
      const view = await api.loadGame(sid);
      set({ saveId: sid, view, loading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "加载游戏失败",
        loading: false,
      });
    }
  },

  fetchView: async () => {
    const { saveId } = get();
    if (!saveId) return;
    set({ loading: true, error: null });
    try {
      const view = await api.getView(saveId);
      set({ view, loading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "获取游戏状态失败",
        loading: false,
      });
    }
  },
}));
