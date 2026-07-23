import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useGameStore } from "../store";
import HypothesisPanel from "../components/HypothesisPanel";

export default function DeductionBoardPage() {
  const navigate = useNavigate();
  const { view, executeAction, loading, error } = useGameStore();
  const [submitting, setSubmitting] = useState<string | null>(null);

  if (!view) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-mystic-text-dim">没有活跃的游戏</p>
      </div>
    );
  }

  const handleSubmitHypothesis = async (hypothesisId: string) => {
    setSubmitting(hypothesisId);
    await executeAction({
      action_type: "submit_hypothesis",
      target_id: hypothesisId,
    });
    setSubmitting(null);
  };

  return (
    <div className="flex-1 p-4 md:p-8 max-w-5xl mx-auto w-full">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-serif font-bold text-mystic-gold tracking-wider">
          推理板
        </h2>
        <button onClick={() => navigate("/game")} className="btn-ghost text-sm">
          返回调查
        </button>
      </div>

      {/* Case Info */}
      <div className="card card-accent mb-6">
        <h3 className="text-mystic-gold font-bold mb-1">{view.current_scene}</h3>
        <p className="text-mystic-text-dim text-xs">
          当前位置：{view.player.current_location_name}
        </p>
      </div>

      {/* Layout: Clues + NPC Statements + Hypotheses */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Left Column: Discovered Clues */}
        <div className="card">
          <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
            已发现线索 ({view.clues.length})
          </h3>
          {view.clues.length === 0 ? (
            <p className="text-mystic-text-dim text-xs italic">
              尚未发现任何线索
            </p>
          ) : (
            <div className="space-y-2">
              {view.clues.map((clue) => (
                <div
                  key={clue.clue_id}
                  className="p-3 rounded text-sm border border-mystic-card/40 bg-mystic-bg/50"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-mystic-text">
                      {clue.display_name}
                    </span>
                    {clue.is_new && (
                      <span className="text-[10px] text-mystic-accent px-1.5 py-0.5 rounded bg-mystic-accent/10">
                        新
                      </span>
                    )}
                  </div>
                  <p className="text-mystic-text-dim text-xs">
                    {clue.description}
                  </p>
                  <p className="text-mystic-text-dim/50 text-[10px] mt-1">
                    来源：{clue.source_type}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: NPC Statements */}
        <div className="space-y-6">
          {/* NPC Statements */}
          <div className="card">
            <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
              证词记录
            </h3>
            {view.npcs.length === 0 ? (
              <p className="text-mystic-text-dim text-xs italic">
                尚未与任何NPC交谈
              </p>
            ) : (
              <div className="space-y-3">
                {view.npcs.map((npc) => (
                  <div key={npc.npc_id}>
                    <h4 className="text-sm text-mystic-accent font-medium mb-1">
                      {npc.name}
                    </h4>
                    {npc.available_claims.length === 0 ? (
                      <p className="text-mystic-text-dim text-xs italic pl-3">
                        暂无证词
                      </p>
                    ) : (
                      <ul className="space-y-1">
                        {npc.available_claims.map((claim) => (
                          <li
                            key={claim.claim_id}
                            className="text-xs text-mystic-text pl-3 border-l-2 border-mystic-card"
                          >
                            {claim.content}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Hypotheses Section */}
      <div className="mt-6">
        <HypothesisPanel hypotheses={view.hypotheses} />

        {/* Hypothesis Submission */}
        {view.hypotheses.some((h) => h.can_submit) && (
          <div className="card mt-4">
            <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
              提交假设
            </h3>
            <div className="space-y-2">
              {view.hypotheses
                .filter((h) => h.can_submit)
                .map((h) => (
                  <div
                    key={h.hypothesis_id}
                    className="flex items-center justify-between p-3 rounded border border-mystic-accent/30 bg-mystic-accent/5"
                  >
                    <div>
                      <p className="text-sm text-mystic-text font-medium">
                        {h.title}
                      </p>
                      <p className="text-xs text-mystic-text-dim">
                        线索 {h.found_clue_count}/{h.required_clue_count}
                      </p>
                    </div>
                    <button
                      onClick={() => handleSubmitHypothesis(h.hypothesis_id)}
                      disabled={loading || submitting === h.hypothesis_id}
                      className="btn-primary text-sm"
                    >
                      {submitting === h.hypothesis_id ? "提交中..." : "提交"}
                    </button>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="card border-red-800 bg-red-900/10 mt-4">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Bottom Actions */}
      <div className="flex items-center gap-3 mt-6">
        <button
          onClick={() => navigate("/game")}
          className="btn-primary"
        >
          返回调查
        </button>
      </div>
    </div>
  );
}
