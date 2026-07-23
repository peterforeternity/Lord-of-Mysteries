import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useGameStore } from "../store";

export default function EndingPage() {
  const navigate = useNavigate();
  const { view, saveId, loading, fetchView } = useGameStore();

  useEffect(() => {
    if (view) return;
    if (saveId && !loading) {
      fetchView();
    }
  }, [view, saveId, loading, fetchView]);

  useEffect(() => {
    if (!view && !loading && !saveId) {
      navigate("/");
    }
  }, [view, navigate, loading, saveId]);

  if (!view || !view.game_over) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-mystic-text-dim">案件尚未结束</p>
      </div>
    );
  }

  const endingTypeLabels: Record<string, string> = {
    truth: "真相结局",
    madness: "疯狂结局",
    sacrifice: "牺牲结局",
    escape: "逃脱结局",
    unknown: "未知结局",
  };

  const endingTypeColors: Record<string, string> = {
    truth: "text-green-400 border-green-600",
    madness: "text-red-400 border-red-600",
    sacrifice: "text-purple-400 border-purple-600",
    escape: "text-blue-400 border-blue-600",
    unknown: "text-mystic-text-dim border-mystic-card",
  };

  const finalEnding = view.final_ending;
  const endingType = finalEnding?.ending_type || "unknown";
  const typeLabel = endingTypeLabels[endingType] || "未知结局";
  const colorClass = endingTypeColors[endingType] || endingTypeColors.unknown;

  return (
    <div className="flex-1 flex items-center justify-center p-4">
      <div className="max-w-lg w-full text-center">
        {/* Ending Card */}
        <div className={`card border-2 ${colorClass}`}>
          {/* Ending Header */}
          <div className="mb-6">
            <h2 className="text-2xl font-serif font-bold text-mystic-gold mb-2 tracking-widest">
              案件完结
            </h2>
            <div className="divider" />
            <span
              className={`inline-block px-4 py-1 rounded-full text-sm font-medium border ${colorClass} bg-black/20`}
            >
              {typeLabel}
            </span>
          </div>

          {/* Ending Description */}
          <div className="mb-6">
            <p className="text-mystic-text text-base leading-relaxed">
              {finalEnding?.description || "案件结束了，但真相究竟如何？"}
            </p>
          </div>

          {/* Case Summary */}
          <div className="card bg-mystic-bg/50 mb-6 text-left">
            <h3 className="text-mystic-gold text-sm font-bold mb-2">
              案件总结
            </h3>
            <div className="text-xs text-mystic-text-dim space-y-1">
              <p>场景：{view.current_scene}</p>
              <p>
                发现线索：{view.clues.length} 条
              </p>
              <p>
                假设进度：
                {view.hypotheses.filter((h) => h.status === "confirmed").length}
                /{view.hypotheses.length}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <button
              onClick={() => navigate("/case-select")}
              className="btn-primary w-full py-3"
            >
              开始新案件
            </button>
            <button
              onClick={() => navigate("/")}
              className="btn-ghost w-full"
            >
              返回主菜单
            </button>
          </div>
        </div>

        {/* Footer */}
        <p className="text-mystic-text-dim/30 text-xs mt-6 italic">
          灰雾调查录 · 真相终将浮现
        </p>
      </div>
    </div>
  );
}
