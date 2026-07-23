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
  /** Tracks pending state per action_id to prevent duplicate submissions */
  pendingActions: Record<string, boolean>;

  newGame: (caseId: string, seed?: number) => Promise<void>;
  executeAction: (action: ActionRequestInput, actionId?: string) => Promise<void>;
  saveGame: () => Promise<void>;
  loadGame: (saveId: string) => Promise<void>;
  fetchView: () => Promise<void>;
  clearError: () => void;
  setActionPending: (actionId: string) => void;
  clearActionPending: (actionId: string) => void;
}

export const useGameStore = create<GameState>((set, get) => ({
  saveId: null,
  view: null,
  loading: false,
  error: null,
  pendingActions: {},

  clearError: () => set({ error: null }),

  setActionPending: (actionId: string) => {
    set((s) => ({
      pendingActions: { ...s.pendingActions, [actionId]: true },
    }));
  },

  clearActionPending: (actionId: string) => {
    set((s) => {
      const next = { ...s.pendingActions };
      delete next[actionId];
      return { pendingActions: next };
    });
  },

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

  executeAction: async (action: ActionRequestInput, actionId?: string) => {
    const { saveId, view } = get();
    if (!saveId) return;

    // Mark this action as pending if actionId is provided
    if (actionId) {
      get().setActionPending(actionId);
    }

    const actionWithVersion: ActionRequest = {
      ...action,
      expected_version: action.expected_version ?? (view?.state_version ?? 0),
    } as ActionRequest;
    set({ error: null });
    try {
      const res = await api.executeAction(saveId, actionWithVersion, saveId);
      if (res.success && res.view) {
        set({ view: res.view });
      } else {
        set({
          error: res.error_detail || res.error_code || "操作失败",
        });
      }
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "执行操作失败",
      });
    } finally {
      if (actionId) {
        get().clearActionPending(actionId);
      }
    }
  },

  saveGame: async () => {
    const { saveId } = get();
    if (!saveId) return;
    set({ loading: true, error: null });
    try {
      await api.saveGame(saveId, saveId);
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
      const view = await api.loadGame(sid, sid);
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
      const view = await api.getView(saveId, saveId);
      set({ view, loading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "获取游戏状态失败",
        loading: false,
      });
    }
  },
}));
