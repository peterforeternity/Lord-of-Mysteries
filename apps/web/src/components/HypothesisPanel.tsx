import type { Hypothesis } from "../types";

interface Props {
  hypotheses: Hypothesis[];
}

function statusBadge(status: Hypothesis["status"]) {
  switch (status) {
    case "locked":
      return { label: "未解锁", className: "bg-gray-700 text-gray-400" };
    case "unlocked":
      return { label: "待验证", className: "bg-mystic-accent/20 text-mystic-gold" };
    case "confirmed":
      return { label: "已确认", className: "bg-green-900/30 text-green-400" };
    case "refuted":
      return { label: "已推翻", className: "bg-red-900/30 text-red-400" };
  }
}

export default function HypothesisPanel({ hypotheses }: Props) {
  if (hypotheses.length === 0) {
    return (
      <div className="card mb-4">
        <h3 className="text-mystic-gold text-sm font-bold mb-2 tracking-wider">
          推理假设
        </h3>
        <p className="text-mystic-text-dim text-xs italic">暂无假设</p>
      </div>
    );
  }

  return (
    <div className="card mb-4">
      <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
        推理假设
      </h3>
      <div className="space-y-2">
        {hypotheses.map((h) => {
          const badge = statusBadge(h.status);
          return (
            <div
              key={h.id}
              className={`rounded p-3 border text-sm ${
                h.status === "confirmed"
                  ? "hypothesis-confirmed"
                  : h.status === "refuted"
                  ? "hypothesis-refuted"
                  : h.status === "locked"
                  ? "hypothesis-locked"
                  : "hypothesis-unlocked"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-mystic-text">
                  {h.status === "locked" ? "???" : h.title}
                </span>
                <span
                  className={`text-xs px-1.5 py-0.5 rounded ${badge.className}`}
                >
                  {badge.label}
                </span>
              </div>
              {h.status !== "locked" && (
                <>
                  <p className="text-mystic-text-dim text-xs mb-2">
                    {h.description}
                  </p>
                  <div className="flex items-center gap-2">
                    <div className="status-bar flex-1">
                      <div
                        className="status-fill bg-mystic-accent"
                        style={{ width: `${h.progress}%` }}
                      />
                    </div>
                    <span className="text-xs text-mystic-text-dim">
                      {h.progress}%
                    </span>
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
