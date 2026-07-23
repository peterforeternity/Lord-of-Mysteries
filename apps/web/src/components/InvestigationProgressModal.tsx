import { useEffect, useRef, useCallback } from "react";
import type { InvestigationProgress } from "../types";

interface Props {
  progress: InvestigationProgress;
  onClose: () => void;
  onGoToDeduction: () => void;
}

/** Map dimension_id to a descriptive icon character */
const DIM_ICONS: Record<string, string> = {
  scene: "◇",
  witness: "◈",
  anomaly: "◇",
  items: "◆",
  causality: "◎",
};

/** Map status_label to progress bar color classes */
const STATUS_COLORS: Record<string, string> = {
  "尚无发现": "bg-mystic-text-dim/20",
  "出现疑点": "bg-mystic-warning/40",
  "线索增加": "bg-mystic-accent/30",
  "相互印证": "bg-mystic-success/50",
  "基本明确": "bg-mystic-gold/60",
};

/** Map status_label to width percentage */
function statusWidth(status: string): string {
  switch (status) {
    case "尚无发现":
      return "w-1/12";
    case "出现疑点":
      return "w-1/4";
    case "线索增加":
      return "w-2/5";
    case "相互印证":
      return "w-3/5";
    case "基本明确":
      return "w-11/12";
    default:
      return "w-0";
  }
}

function PhaseIndicator({ level, label }: { level: number; label: string }) {
  const phases = [
    { label: "迷雾初现", desc: "调查刚刚开始" },
    { label: "线索浮现", desc: "零散的信息逐渐显现" },
    { label: "疑点交汇", desc: "多条线索开始指向共同方向" },
    { label: "接近真相", desc: "真相就在眼前" },
  ];

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-mystic-text-dim font-mono tracking-wider">
          调查阶段
        </span>
        <span className="text-mystic-gold font-bold text-sm">
          {label}
        </span>
      </div>
      <div className="flex gap-1">
        {phases.map((p, i) => (
          <div
            key={p.label}
            className={`flex-1 h-1.5 rounded-full transition-colors duration-500 ${
              i <= level
                ? "bg-mystic-gold"
                : "bg-mystic-card/50"
            }`}
            title={p.desc}
            aria-hidden="true"
          />
        ))}
      </div>
      <p className="text-xs text-mystic-text-dim mt-1 italic">
        {phases[level].desc}
      </p>
    </div>
  );
}

export default function InvestigationProgressModal({
  progress,
  onClose,
  onGoToDeduction,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Focus trap: keep focus inside the dialog
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab" || !dialogRef.current) return;

      const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    },
    [onClose]
  );

  useEffect(() => {
    const btn = closeButtonRef.current;
    // Focus close button on mount
    btn?.focus();

    // Trap focus
    document.addEventListener("keydown", handleKeyDown);

    // Prevent body scroll
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = prev;
      // Return focus to trigger element
      btn?.focus();
    };
  }, [handleKeyDown]);

  // Close on backdrop click
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center"
      onClick={handleBackdropClick}
      role="presentation"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" aria-hidden="true" />

      {/* Dialog — mobile drawer, desktop modal */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="investigation-progress-title"
        className="relative z-10 w-full sm:max-w-lg max-h-[85vh] sm:max-h-[80vh] overflow-y-auto
          bg-mystic-surface border-t sm:border border-mystic-card/80
          rounded-t-xl sm:rounded-lg
          motion-safe:animate-in motion-safe:slide-in-from-bottom sm:motion-safe:zoom-in-95
          shadow-2xl shadow-black/50"
        style={
          {
            backgroundColor: "#12121e",
            backgroundImage:
              "radial-gradient(ellipse at 50% 0%, rgba(201,169,92,0.06) 0%, transparent 70%)",
          } as React.CSSProperties
        }
      >
        {/* Header — dark archives aesthetic */}
        <div className="sticky top-0 z-10 flex items-center justify-between p-4 sm:p-5
          border-b border-mystic-gold/20"
          style={{
            background: "linear-gradient(180deg, rgba(18,18,30,0.98) 0%, rgba(18,18,30,0.9) 100%)",
          }}
        >
          <div>
            <h2
              id="investigation-progress-title"
              className="text-mystic-gold font-bold text-base tracking-wider"
            >
              调查进度
            </h2>
            <p className="text-xs text-mystic-text-dim mt-0.5">
              案件推进程度概览
            </p>
          </div>
          <button
            ref={closeButtonRef}
            onClick={onClose}
            className="text-mystic-text-dim hover:text-mystic-gold
              text-lg leading-none p-1 rounded
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mystic-gold/50
              transition-colors duration-150"
            aria-label="关闭调查进度"
          >
            ✕
          </button>
        </div>

        <div className="p-4 sm:p-5 space-y-5">
          {/* Phase */}
          <PhaseIndicator level={progress.phase_level} label={progress.phase_label} />

          {/* Evidence Dimensions */}
          <div>
            <h3 className="text-xs text-mystic-text-dim font-mono tracking-wider mb-3
              flex items-center gap-2">
              <span className="w-4 h-px bg-mystic-gold/30" aria-hidden="true" />
              证据维度
            </h3>
            <div className="space-y-3">
              {progress.evidence_dimensions.map((dim) => (
                <div key={dim.dimension_id}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-mystic-text flex items-center gap-1.5">
                      <span className="text-mystic-gold/60 text-xs" aria-hidden="true">
                        {DIM_ICONS[dim.dimension_id] || "•"}
                      </span>
                      {dim.label}
                    </span>
                    <span className="text-xs text-mystic-text-dim">
                      {dim.found}/{dim.total}
                    </span>
                  </div>
                  <div className="h-1.5 bg-mystic-card/50 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        STATUS_COLORS[dim.status_label] || "bg-mystic-text-dim/20"
                      }`}
                      style={{ width: `${(dim.found / Math.max(dim.total, 1)) * 100}%` }}
                      role="progressbar"
                      aria-valuenow={dim.found}
                      aria-valuemin={0}
                      aria-valuemax={dim.total}
                      aria-label={`${dim.label}: ${dim.found}/${dim.total}`}
                    />
                  </div>
                  <p className="text-xs text-mystic-text-dim mt-0.5">{dim.status_label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Discoveries */}
          {progress.recent_discoveries.length > 0 && (
            <div>
              <h3 className="text-xs text-mystic-text-dim font-mono tracking-wider mb-2
                flex items-center gap-2">
                <span className="w-4 h-px bg-mystic-gold/30" aria-hidden="true" />
                最近获得
              </h3>
              <ul className="space-y-1">
                {progress.recent_discoveries.map((name, i) => (
                  <li
                    key={i}
                    className="text-sm text-mystic-text pl-3 border-l-2 border-mystic-accent/30"
                  >
                    {name}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Open Questions */}
          {progress.open_questions.length > 0 && (
            <div>
              <h3 className="text-xs text-mystic-text-dim font-mono tracking-wider mb-2
                flex items-center gap-2">
                <span className="w-4 h-px bg-mystic-gold/30" aria-hidden="true" />
                尚待厘清
              </h3>
              <ul className="space-y-2">
                {progress.open_questions.map((q, i) => (
                  <li
                    key={i}
                    className="text-sm text-mystic-text-dim italic pl-3
                      border-l-2 border-mystic-text-dim/20"
                  >
                    {q}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Divider */}
          <div className="h-px bg-gradient-to-r from-transparent via-mystic-gold/20 to-transparent" />
        </div>

        {/* Footer buttons */}
        <div className="p-4 sm:p-5 pt-0 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 btn-secondary text-sm
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mystic-gold/50"
          >
            继续调查
          </button>
          {progress.resolution_available && (
            <button
              onClick={onGoToDeduction}
              className="flex-1 btn-primary text-sm
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mystic-gold/50"
            >
              进入推理
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
