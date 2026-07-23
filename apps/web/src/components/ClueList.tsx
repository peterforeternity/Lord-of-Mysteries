import type { ClueInfo } from "../types";

interface Props {
  clues: ClueInfo[];
  onClueClick?: (clue: ClueInfo) => void;
}

export default function ClueList({ clues, onClueClick }: Props) {
  if (clues.length === 0) {
    return (
      <div className="card mb-4">
        <h3 className="text-mystic-gold text-sm font-bold mb-2 tracking-wider">
          线索记录
        </h3>
        <p className="text-mystic-text-dim text-xs italic">
          尚未发现任何线索
        </p>
      </div>
    );
  }

  const newClues = clues.filter((c) => c.is_new);
  const oldClues = clues.filter((c) => !c.is_new);

  return (
    <div className="card mb-4">
      <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
        线索记录 ({clues.length})
      </h3>
      {newClues.length > 0 && (
        <div className="mb-3">
          <h4 className="text-mystic-accent text-xs font-bold mb-1">
            新发现
          </h4>
          {newClues.map((clue) => (
            <button
              key={clue.clue_id}
              onClick={() => onClueClick?.(clue)}
              className="block w-full text-left text-xs py-1.5 px-2 rounded 
                         bg-mystic-accent/10 text-mystic-gold hover:bg-mystic-accent/20
                         mb-1 transition-colors border border-mystic-accent/20"
            >
              {clue.display_name}
            </button>
          ))}
        </div>
      )}
      <h4 className="text-mystic-text-dim text-xs font-bold mb-1">其他线索</h4>
      {oldClues.map((clue) => (
        <button
          key={clue.clue_id}
          onClick={() => onClueClick?.(clue)}
          className="block w-full text-left text-xs py-1.5 px-2 rounded 
                     text-mystic-text-dim hover:text-mystic-text hover:bg-white/5
                     mb-0.5 transition-colors"
        >
          {clue.display_name}
        </button>
      ))}
    </div>
  );
}
