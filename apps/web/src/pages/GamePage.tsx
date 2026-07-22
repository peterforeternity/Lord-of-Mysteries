import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useGameStore } from "../store";
import PlayerStatus from "../components/PlayerStatus";
import LocationPanel from "../components/LocationPanel";
import ClueList from "../components/ClueList";
import EventLog from "../components/EventLog";
import HypothesisPanel from "../components/HypothesisPanel";
import NpcDialogue from "../components/NpcDialogue";
import type { Clue, Npc, Action } from "../types";

export default function GamePage() {
  const navigate = useNavigate();
  const { view, loading, error, executeAction, fetchView, saveGame } =
    useGameStore();
  const [dialogueNpc, setDialogueNpc] = useState<Npc | null>(null);
  const [selectedClue, setSelectedClue] = useState<Clue | null>(null);

  useEffect(() => {
    if (!view) {
      navigate("/");
    }
  }, [view, navigate]);

  if (!view) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-mystic-text-dim">返回主页开始新游戏</p>
      </div>
    );
  }

  const handleAction = (action: Action) => {
    executeAction(action.id);
  };

  const handleSave = async () => {
    await saveGame();
  };

  return (
    <div className="flex-1 flex flex-col lg:flex-row gap-4 p-4 lg:p-6 max-w-7xl mx-auto w-full">
      {/* ========== LEFT COLUMN ========== */}
      <aside className="lg:w-72 shrink-0 hidden lg:block">
        <PlayerStatus status={view.player_status} />
        <LocationPanel
          currentLocation={view.current_location}
          locations={view.locations}
        />

        {/* Items */}
        <div className="card card-accent mb-4">
          <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
            物品
          </h3>
          {view.items.length === 0 ? (
            <p className="text-mystic-text-dim text-xs italic">
              背包为空
            </p>
          ) : (
            <ul className="space-y-1">
              {view.items.map((item) => (
                <li
                  key={item.id}
                  className="text-xs text-mystic-text flex items-center justify-between py-1 px-2 rounded hover:bg-white/5"
                >
                  <span>
                    {item.name}
                    {item.quantity > 1 && (
                      <span className="text-mystic-text-dim ml-1">
                        x{item.quantity}
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      {/* ========== CENTER COLUMN ========== */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Scene */}
        <div className="card card-accent mb-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-mystic-gold font-bold">
              {view.scene_name}
            </h3>
            <span className="text-xs text-mystic-text-dim">
              {view.chapter}
            </span>
          </div>
          <p className="text-sm text-mystic-text leading-relaxed">
            {view.scene_description}
          </p>
        </div>

        {/* Dialogue */}
        {view.dialogue_content && (
          <div className="card border-blue-800/50 bg-blue-900/5 mb-4">
            <p className="text-sm text-blue-200 leading-relaxed italic">
              {view.dialogue_content}
            </p>
            {view.dialogue_options.length > 0 && (
              <div className="mt-3 space-y-1">
                {view.dialogue_options.map((opt, idx) => (
                  <button
                    key={idx}
                    onClick={() =>
                      executeAction("dialogue_choice", { choice: idx })
                    }
                    className="btn-secondary w-full text-left text-xs"
                  >
                    {opt}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="card mb-4">
          <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
            行动
          </h3>
          <div className="grid gap-2 sm:grid-cols-2">
            {view.available_actions.map((action) => (
              <button
                key={action.id}
                onClick={() => handleAction(action)}
                disabled={loading}
                className="btn-secondary text-left text-sm"
              >
                <span className="font-medium">{action.name}</span>
                {action.description && (
                  <span className="block text-mystic-text-dim text-xs mt-0.5">
                    {action.description}
                  </span>
                )}
              </button>
            ))}
            {view.available_actions.length === 0 && (
              <p className="text-mystic-text-dim text-xs italic col-span-full">
                当前没有可用行动
              </p>
            )}
          </div>
        </div>

        {/* Mobile: Player Status (visible only on mobile) */}
        <div className="lg:hidden mb-4">
          <PlayerStatus status={view.player_status} />
        </div>

        {/* Mobile: Clues */}
        <div className="lg:hidden mb-4">
          <ClueList clues={view.clues} onClueClick={setSelectedClue} />
        </div>

        {/* NPCs */}
        {view.npcs.length > 0 && (
          <div className="card mb-4">
            <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
              NPC
            </h3>
            <div className="flex flex-wrap gap-2">
              {view.npcs.map((npc) => (
                <button
                  key={npc.id}
                  onClick={() => setDialogueNpc(npc)}
                  className="btn-secondary text-xs"
                >
                  {npc.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="card border-red-800 bg-red-900/10 mb-4">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="text-center py-2">
            <span className="text-mystic-text-dim text-sm">处理中...</span>
          </div>
        )}
      </div>

      {/* ========== RIGHT COLUMN ========== */}
      <aside className="lg:w-80 shrink-0 hidden lg:block">
        {/* Active Tasks */}
        <div className="card card-accent mb-4">
          <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
            当前任务
          </h3>
          {view.active_tasks.length === 0 ? (
            <p className="text-mystic-text-dim text-xs italic">
              暂无活跃任务
            </p>
          ) : (
            <ul className="space-y-2">
              {view.active_tasks.map((task) => (
                <li key={task.id} className="text-xs">
                  <div className="flex items-start gap-2">
                    <span
                      className={`mt-0.5 shrink-0 ${
                        task.status === "completed"
                          ? "text-green-400"
                          : task.status === "failed"
                          ? "text-red-400"
                          : "text-mystic-gold"
                      }`}
                    >
                      {task.status === "completed"
                        ? "✓"
                        : task.status === "failed"
                        ? "✗"
                        : "○"}
                    </span>
                    <div>
                      <p
                        className={`${
                          task.status === "completed"
                            ? "text-green-400 line-through"
                            : task.status === "failed"
                            ? "text-red-400"
                            : "text-mystic-text"
                        }`}
                      >
                        {task.title}
                      </p>
                      <p className="text-mystic-text-dim mt-0.5">
                        {task.description}
                      </p>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Clue List */}
        <ClueList clues={view.clues} onClueClick={setSelectedClue} />

        {/* Investigations / Divination */}
        {view.divination_results.length > 0 && (
          <div className="card mb-4">
            <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
              占卜结果
            </h3>
            {view.divination_results.map((dr) => (
              <div key={dr.id} className="mb-2 last:mb-0">
                <p className="text-xs text-mystic-gold">{dr.content}</p>
                <p className="text-xs text-mystic-text-dim mt-0.5">
                  {dr.interpretation}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Event Log */}
        <EventLog entries={view.event_log} />

        {/* Hypothesis Panel */}
        <HypothesisPanel hypotheses={view.hypotheses} />

        {/* Actions */}
        <div className="space-y-2">
          <button
            onClick={() => navigate("/deduction")}
            className="btn-secondary w-full text-sm"
          >
            推理板
          </button>
          <button
            onClick={() => navigate("/ritual")}
            className="btn-secondary w-full text-sm"
          >
            仪式
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="btn-primary w-full text-sm"
          >
            保存游戏
          </button>
          <button
            onClick={() => navigate("/save-load")}
            className="btn-ghost w-full text-sm"
          >
            存档管理
          </button>
        </div>
      </aside>

      {/* ========== NPC Dialogue Modal ========== */}
      {dialogueNpc && (
        <NpcDialogue
          npc={dialogueNpc}
          onClose={() => setDialogueNpc(null)}
        />
      )}

      {/* ========== Clue Detail Modal ========== */}
      {selectedClue && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-mystic-surface border border-mystic-card rounded-lg w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b border-mystic-card">
              <h2 className="text-mystic-gold font-bold">
                {selectedClue.name}
              </h2>
              <button
                onClick={() => setSelectedClue(null)}
                className="text-mystic-text-dim hover:text-mystic-text text-lg leading-none"
              >
                ✕
              </button>
            </div>
            <div className="p-4">
              <p className="text-sm text-mystic-text mb-3">
                {selectedClue.description}
              </p>
              <div className="text-xs text-mystic-text-dim space-y-1">
                <p>来源：{selectedClue.source}</p>
                <p>
                  发现时间：
                  {new Date(selectedClue.discovered_at).toLocaleString(
                    "zh-CN"
                  )}
                </p>
                {selectedClue.is_key && (
                  <p className="text-mystic-accent">关键线索</p>
                )}
              </div>
            </div>
            <div className="p-4 border-t border-mystic-card/40">
              <button
                onClick={() => setSelectedClue(null)}
                className="btn-primary w-full"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
