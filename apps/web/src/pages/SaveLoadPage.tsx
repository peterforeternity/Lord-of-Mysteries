import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useGameStore } from "../store";
import { loadGame, newGame } from "../api";
import type { SaveSlot } from "../types";

// Mock save slots for demo — in production these come from the backend
const DEMO_SLOTS: SaveSlot[] = [];

export default function SaveLoadPage() {
  const navigate = useNavigate();
  const {
    saveId,
    view,
    loading,
    error,
    saveGame,
    loadGame: loadFromStore,
  } = useGameStore();
  const [slots] = useState<SaveSlot[]>(DEMO_SLOTS);

  const handleSave = async () => {
    await saveGame();
  };

  const handleLoad = async (sid: string) => {
    await loadFromStore(sid);
    navigate("/game");
  };

  return (
    <div className="flex-1 p-4 md:p-8 max-w-2xl mx-auto w-full">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-serif font-bold text-mystic-gold tracking-wider">
          存档管理
        </h2>
        <button onClick={() => navigate(-1)} className="btn-ghost text-sm">
          返回
        </button>
      </div>

      {/* Current game info */}
      {view && (
        <div className="card card-accent mb-6">
          <h3 className="text-mystic-gold font-bold mb-1">当前游戏</h3>
          <p className="text-sm text-mystic-text-dim">
            {view.case_name} — {view.chapter}
          </p>
          <p className="text-xs text-mystic-text-dim/50 mt-1">
            存档ID: {saveId}
          </p>
          <div className="mt-3 flex items-center gap-3">
            <button
              onClick={handleSave}
              disabled={loading}
              className="btn-primary text-sm"
            >
              {loading ? "保存中..." : "快速保存"}
            </button>
            <button
              onClick={() => navigate("/game")}
              className="btn-secondary text-sm"
            >
              继续游戏
            </button>
          </div>
        </div>
      )}

      {!view && (
        <div className="card mb-6">
          <p className="text-mystic-text-dim text-sm">
            当前没有活跃的游戏。请先开始新游戏或加载存档。
          </p>
          <div className="mt-3 flex items-center gap-3">
            <button
              onClick={() => navigate("/case-select")}
              className="btn-primary text-sm"
            >
              新游戏
            </button>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card border-red-800 bg-red-900/10 mb-6">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Save slots */}
      <h3 className="text-mystic-text-dim text-sm font-bold mb-3 tracking-wider">
        存档列表
      </h3>

      {slots.length === 0 ? (
        <div className="card text-center py-10">
          <p className="text-mystic-text-dim text-sm italic">
            暂无存档
          </p>
          <p className="text-xs text-mystic-text-dim/50 mt-2">
            进行游戏后可以在此保存进度
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {slots.map((slot) => (
            <div
              key={slot.slot_id}
              className="card flex items-center justify-between"
            >
              <div>
                <p className="text-sm text-mystic-text font-medium">
                  {slot.case_name}
                </p>
                <p className="text-xs text-mystic-text-dim">
                  {slot.chapter} — {slot.location}
                </p>
                <p className="text-xs text-mystic-text-dim/50">
                  {new Date(slot.saved_at).toLocaleString("zh-CN")} · 游戏时长{" "}
                  {slot.play_time}
                </p>
              </div>
              <button
                onClick={() => handleLoad(slot.save_id)}
                disabled={loading}
                className="btn-secondary text-sm"
              >
                {loading ? "加载中..." : "加载"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
