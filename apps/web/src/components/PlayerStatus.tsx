import type { PlayerStatus as PlayerStatusType } from "../types";

interface Props {
  status: PlayerStatusType;
}

function StatusBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  const pct = Math.min(Math.max(value, 0), 100);
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs mb-1">
        <span>{label}</span>
        <span className="text-mystic-text-dim">{value}</span>
      </div>
      <div className="status-bar">
        <div
          className="status-fill"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export default function PlayerStatus({ status }: Props) {
  return (
    <div className="card card-accent mb-4">
      <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
        状态
      </h3>
      <StatusBar label="灵性" value={status.spirituality} color="#3b82f6" />
      <StatusBar label="污染" value={status.corruption} color="#8b5cf6" />
      <StatusBar label="稳定度" value={status.stability} color="#10b981" />
    </div>
  );
}
