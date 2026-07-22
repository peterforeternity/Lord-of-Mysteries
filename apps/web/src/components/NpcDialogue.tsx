import type { Npc } from "../types";

interface Props {
  npc: Npc;
  onClose: () => void;
}

export default function NpcDialogue({ npc, onClose }: Props) {
  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-mystic-surface border border-mystic-card rounded-lg w-full max-w-lg max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-mystic-card">
          <h2 className="text-mystic-gold font-bold">{npc.name}</h2>
          <button
            onClick={onClose}
            className="text-mystic-text-dim hover:text-mystic-text text-lg leading-none"
          >
            ✕
          </button>
        </div>

        {/* Description */}
        <div className="p-4 border-b border-mystic-card/40">
          <p className="text-mystic-text-dim text-sm">{npc.description}</p>
        </div>

        {/* Statements */}
        <div className="p-4">
          <h3 className="text-mystic-accent text-sm font-bold mb-3">
            证词
          </h3>
          {npc.statements.length === 0 ? (
            <p className="text-mystic-text-dim text-xs italic">
              暂无证词记录
            </p>
          ) : (
            <ul className="space-y-3">
              {npc.statements.map((stmt, idx) => (
                <li
                  key={idx}
                  className="text-sm text-mystic-text pl-3 border-l-2 border-mystic-accent/40"
                >
                  {stmt}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Close button */}
        <div className="p-4 border-t border-mystic-card/40">
          <button onClick={onClose} className="btn-primary w-full">
            关闭
          </button>
        </div>
      </div>
    </div>
  );
}
