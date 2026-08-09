import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useGameStore } from "../store";
import PlayerStatus from "../components/PlayerStatus";
import LocationPanel from "../components/LocationPanel";
import ClueList from "../components/ClueList";
import EventLog from "../components/EventLog";
import HypothesisPanel from "../components/HypothesisPanel";
import NpcDialogue from "../components/NpcDialogue";
import InvestigationProgressModal from "../components/InvestigationProgressModal";
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
    initFromStorage,
    clearActiveSave,
  } = useGameStore();
  const [dialogueNpc, setDialogueNpc] = useState<NpcInfo | null>(null);
  const [selectedClue, setSelectedClue] = useState<ClueInfo | null>(null);
  const [showProgress, setShowProgress] = useState(false);
  const [showResolutionHint, setShowResolutionHint] = useState(false);
  const [initialised, setInitialised] = useState(false);
  const progressButtonRef = useRef<HTMLButtonElement>(null);
  const mobileProgressButtonRef = useRef<HTMLButtonElement>(null);
  const [progressTrigger, setProgressTrigger] = useState<"desktop" | "mobile" | null>(null);

  // Restore active game from localStorage on first mount
  useEffect(() => {
    if (!initialised) {
      setInitialised(true);
      initFromStorage();
    }
  }, [initialised, initFromStorage]);

  // A8: Show resolution hint when new_resolution_available is true
  useEffect(() => {
    if (view?.investigation_progress?.new_resolution_available) {
      setShowResolutionHint(true);
    }
  }, [view?.investigation_progress?.new_resolution_available]);

  // Dismiss resolution hint and mark it as seen
  const handleDismissResolution = useCallback(async () => {
    setShowResolutionHint(false);
    if (view) {
      // Find the dismiss action if available
      const dismissAction = view.available_actions.find(
        (a) => a.action_type === "dismiss_resolution_hint"
      );
      if (dismissAction) {
        await executeAction(
          {
            action_type: dismissAction.action_type,
            target_id: dismissAction.target_id ?? undefined,
            expected_version: dismissAction.expected_version,
          },
          dismissAction.action_id
        );
      } else {
        // Fallback: call dismiss directly via the API
        await executeAction(
          {
            action_type: "dismiss_resolution_hint",
            expected_version: view.state_version,
          }
        );
      }
    }
  }, [view, executeAction]);

  // Handle "进入推理" from progress modal
  const handleGoToDeduction = useCallback(() => {
    setShowProgress(false);
    setShowResolutionHint(false);
    navigate("/deduction");
  }, [navigate]);

  // Close progress modal and restore focus to the trigger button
  const handleCloseProgress = useCallback(() => {
    setShowProgress(false);
    // Restore focus to whichever "调查进度" button opened the modal
    requestAnimationFrame(() => {
      if (progressTrigger === "mobile") {
        mobileProgressButtonRef.current?.focus();
      } else {
        progressButtonRef.current?.focus();
      }
    });
  }, [progressTrigger]);

  // Open progress modal from desktop or mobile button
  const handleOpenProgress = useCallback((source: "desktop" | "mobile") => {
    setProgressTrigger(source);
    setShowProgress(true);
  }, []);

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
      clearActiveSave();
      navigate(`/ending?save_id=${encodeURIComponent(saveId)}`, {
        replace: true,
      });
      return;
    }
  }, [view, saveId, loading, navigate, clearActiveSave]);

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
        <HypothesisPanel
          hypotheses={view.hypotheses}
          resolutionAvailable={view.investigation_progress?.resolution_available}
        />

        {/* Sidebar Navigation */}
        <div className="space-y-2">
          <button
            ref={progressButtonRef}
            onClick={() => handleOpenProgress("desktop")}
            className="btn-secondary w-full text-sm"
          >
            调查进度
          </button>
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

      {/* ========== MOBILE-ONLY SECTION (below sidebar in DOM so desktop buttons come first) ========== */}
      <div className="lg:hidden space-y-4 w-full">
        <PlayerStatus status={view.player} />
        <ClueList clues={view.clues} onClueClick={setSelectedClue} />
        <button
          ref={mobileProgressButtonRef}
          onClick={() => handleOpenProgress("mobile")}
          className="btn-secondary w-full text-sm"
        >
          调查进度
        </button>
      </div>

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

      {/* ========== Investigation Progress Modal ========== */}
      {showProgress && view?.investigation_progress && (
        <InvestigationProgressModal
          progress={view.investigation_progress}
          onClose={handleCloseProgress}
          onGoToDeduction={handleGoToDeduction}
        />
      )}

      {/* ========== Resolution Hint Toast ========== */}
      {showResolutionHint && view?.investigation_progress?.resolution_available && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/50 cursor-pointer"
            onClick={handleDismissResolution}
            aria-hidden="true"
          />
          <div
            className="relative z-10 bg-mystic-surface border border-mystic-gold/40 rounded-lg
              w-full max-w-sm p-5 shadow-2xl shadow-black/50
              motion-safe:animate-in motion-safe:fade-in motion-safe:zoom-in-95"
            role="dialog"
            aria-modal="true"
            aria-labelledby="resolution-hint-title"
          >
            <h3
              id="resolution-hint-title"
              className="text-mystic-gold font-bold text-sm mb-3 tracking-wider"
            >
              新的判断正在形成
            </h3>
            <p className="text-mystic-text text-sm leading-relaxed mb-4">
              你掌握的证据已经足以支持某种解释，可以进入推理，也可以继续调查。
            </p>
            <div className="flex gap-3">
              <button
                onClick={handleDismissResolution}
                className="flex-1 btn-secondary text-sm
                  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mystic-gold/50"
              >
                继续调查
              </button>
              <button
                onClick={handleGoToDeduction}
                className="flex-1 btn-primary text-sm
                  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mystic-gold/50"
              >
                进入推理
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
