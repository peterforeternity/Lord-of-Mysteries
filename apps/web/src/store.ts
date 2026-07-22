// ============================================================
// Zustand Game State Store — Grey Fog (灰雾调查录)
// ============================================================

import { create } from "zustand";
import type { GameView } from "./types";
import * as api from "./api";

interface GameState {
  saveId: string | null;
  view: GameView | null;
  loading: boolean;
  error: string | null;

  newGame: (caseId: string) => Promise<void>;
  executeAction: (actionId: string, params?: Record<string, unknown>) => Promise<void>;
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

  newGame: async (caseId: string) => {
    set({ loading: true, error: null });
    try {
      const res = await api.newGame({ case_id: caseId });
      set({ saveId: res.save_id, view: res.view, loading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "创建游戏失败",
        loading: false,
      });
    }
  },

  executeAction: async (
    actionId: string,
    params?: Record<string, unknown>
  ) => {
    const { saveId } = get();
    if (!saveId) return;
    set({ loading: true, error: null });
    try {
      const res = await api.executeAction(saveId, {
        action_id: actionId,
        parameters: params,
      });
      set({ view: res.view, loading: false });
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
      const res = await api.loadGame(sid);
      set({ saveId: sid, view: res.view, loading: false });
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
