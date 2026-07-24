import type { HypothesisInfo } from "../types";

interface Props {
  hypotheses: HypothesisInfo[];
  resolutionAvailable?: boolean;
}

function statusBadge(status: HypothesisInfo["status"]) {
  switch (status) {
    case "locked":
      return { label: "未解锁", className: "bg-gray-700 text-gray-400" };
    case "unlocked":
      return { label: "待验证", className: "bg-mystic-accent/20 text-mystic-gold" };
    case "confirmed":
      return { label: "已确认", className: "bg-green-900/30 text-green-400" };
    case "refuted":
      return { label: "已推翻", className: "bg-red-900/30 text-red-400" };
    default:
      return { label: status, className: "bg-gray-700 text-gray-400" };
  }
}

/** Map clue_status to a descriptive label */
function clueStatusLabel(status: string): string {
  switch (status) {
    case "证据不足":
      return "证据不足";
    case "可以验证":
      return "可以验证";
    case "存在矛盾":
      return "存在矛盾";
    case "证据较充分":
      return "证据较充分";
    default:
      return status;
  }
}

/** Map clue_status to a visual indicator style */
const CLUE_STATUS_STYLES: Record<string, string> = {
  "证据不足": "bg-mystic-text-dim/20 w-1/4",
  "可以验证": "bg-mystic-accent/40 w-2/4",
  "存在矛盾": "bg-red-500/40 w-3/4",
  "证据较充分": "bg-mystic-success/50 w-11/12",
};

const CLUE_STATUS_COLORS: Record<string, string> = {
  "证据不足": "text-mystic-text-dim",
  "可以验证": "text-mystic-accent",
  "存在矛盾": "text-red-400",
  "证据较充分": "text-green-400",
};

export default function HypothesisPanel({ hypotheses, resolutionAvailable }: Props) {
  if (!resolutionAvailable) {
    return (
      <div className="card mb-4">
        <h3 className="text-mystic-gold text-sm font-bold mb-2 tracking-wider">
          推理假设
        </h3>
        <p className="text-mystic-text-dim text-xs italic">
          目前的证据还不足以形成稳定判断。
        </p>
      </div>
    );
  }

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
              key={h.hypothesis_id}
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
                        className={`status-fill ${CLUE_STATUS_STYLES[h.clue_status] || "bg-mystic-text-dim/20 w-0"}`}
                      />
                    </div>
                    <span
                      className={`text-xs ${CLUE_STATUS_COLORS[h.clue_status] || "text-mystic-text-dim"}`}
                    >
                      {clueStatusLabel(h.clue_status)}
                    </span>
                  </div>
                  {h.can_submit && (
                    <span className="text-xs text-mystic-accent mt-1 inline-block">
                      可提交
                    </span>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
