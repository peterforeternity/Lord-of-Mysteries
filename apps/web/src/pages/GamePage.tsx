import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useGameStore } from "../store";
import PlayerStatus from "../components/PlayerStatus";
import LocationPanel from "../components/LocationPanel";
import ClueList from "../components/ClueList";
import EventLog from "../components/EventLog";
import HypothesisPanel from "../components/HypothesisPanel";
import NpcDialogue from "../components/NpcDialogue";
import type { ClueInfo, NpcInfo, ActionInfo } from "../types";

export default function GamePage() {
  const navigate = useNavigate();
  const {
    view,
    loading,
    error,
    executeAction,
    fetchView,
    saveGame,
    pendingActions,
    saveId,
  } = useGameStore();
  const [dialogueNpc, setDialogueNpc] = useState<NpcInfo | null>(null);
  const [selectedClue, setSelectedClue] = useState<ClueInfo | null>(null);

  // A7: Navigation state machine — redirect based on game state
  useEffect(() => {
    if (!saveId) {
      navigate("/case-select", { replace: true });
      return;
    }
    if (!view && !loading) {
      navigate("/case-select", { replace: true });
      return;
    }
    if (view?.game_over) {
      navigate(`/ending?save_id=${encodeURIComponent(saveId)}`, {
        replace: true,
      });
      return;
    }
  }, [view, saveId, loading, navigate]);

  // A7: Fetch view on mount if saveId exists but view is null
  useEffect(() => {
    if (saveId && !view && !loading) {
      fetchView();
    }
  }, [saveId, view, loading, fetchView]);

  // A4: Handle action using ActionInfo from backend
  const handleAction = useCallback(
    (action: ActionInfo) => {
      if (pendingActions[action.action_id]) return;
      executeAction(
        {
          action_type: action.action_type,
          target_id: action.target_id ?? undefined,
          expected_version: action.expected_version,
        },
        action.action_id
      );
    },
    [executeAction, pendingActions]
  );

  if (!view) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-mystic-text-dim">
          {loading ? "加载中..." : "返回主页开始新游戏"}
        </p>
      </div>
    );
  }

  const handleSave = async () => {
    await saveGame();
  };

  const currentLocation = view.player.current_location_name;
  const visitedLocations = view.player.visited_locations;
  const currentLocationInfo = visitedLocations.find(
    (l) => l.location_id === view.player.current_location_id
  );

  return (
    <div className="flex-1 flex flex-col lg:flex-row gap-4 p-4 lg:p-6 max-w-7xl mx-auto w-full">
      {/* ========== LEFT COLUMN ========== */}
      <aside className="lg:w-72 shrink-0 hidden lg:block">
        <PlayerStatus status={view.player} />
        {currentLocationInfo && (
          <LocationPanel
            currentLocation={currentLocationInfo}
            locations={visitedLocations}
          />
        )}

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
                  key={item.item_id}
                  className="text-xs text-mystic-text flex items-center justify-between py-1 px-2 rounded hover:bg-white/5"
                >
                  <span>{item.name}</span>
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
              {view.current_scene}
            </h3>
            <span className="text-xs text-mystic-text-dim">
              {currentLocation}
            </span>
          </div>
          <p className="text-sm text-mystic-text leading-relaxed">
            {view.current_description}
          </p>
        </div>

        {/* A4+A6: Actions rendered from backend available_actions */}
        <div className="card mb-4">
          <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
            行动
          </h3>
          <div className="grid gap-2 sm:grid-cols-2">
            {view.available_actions.map((action) => {
              const isPending = pendingActions[action.action_id];
              return (
                <button
                  key={action.action_id}
                  onClick={() => handleAction(action)}
                  disabled={!action.enabled || isPending}
                  title={
                    !action.enabled && action.disabled_reason
                      ? action.disabled_reason
                      : undefined
                  }
                  className="btn-secondary text-left text-sm relative"
                >
                  <span className="font-medium">{action.label}</span>
                  {isPending && (
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-mystic-text-dim">
                      ...
                    </span>
                  )}
                </button>
              );
            })}
            {view.available_actions.length === 0 && (
              <p className="text-mystic-text-dim text-xs italic col-span-full">
                当前没有可用行动
              </p>
            )}
          </div>
        </div>

        {/* Mobile: Player Status (visible only on mobile) */}
        <div className="lg:hidden mb-4">
          <PlayerStatus status={view.player} />
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
                  key={npc.npc_id}
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

        {/* Global Loading */}
        {loading && (
          <div className="text-center py-2">
            <span className="text-mystic-text-dim text-sm">处理中...</span>
          </div>
        )}
      </div>

      {/* ========== RIGHT COLUMN ========== */}
      <aside className="lg:w-80 shrink-0 hidden lg:block">
        {/* Clue List */}
        <ClueList clues={view.clues} onClueClick={setSelectedClue} />

        {/* NPCs in sidebar */}
        {view.npcs.length > 0 && (
          <div className="card mb-4">
            <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
              NPC
            </h3>
            <div className="flex flex-wrap gap-2">
              {view.npcs.map((npc) => (
                <button
                  key={npc.npc_id}
                  onClick={() => setDialogueNpc(npc)}
                  className="btn-secondary text-xs"
                >
                  {npc.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Event Log */}
        <EventLog entries={view.event_log} />

        {/* Hypothesis Panel */}
        <HypothesisPanel hypotheses={view.hypotheses} />

        {/* Sidebar Navigation */}
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
            onClick={() => navigate("/tutorial")}
            className="btn-ghost w-full text-sm"
          >
            帮助
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
                {selectedClue.display_name}
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
                <p>来源：{selectedClue.source_type}</p>
                {selectedClue.is_new && (
                  <p className="text-mystic-accent">新发现的线索</p>
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
