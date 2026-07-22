import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useGameStore } from "../store";
import HypothesisPanel from "../components/HypothesisPanel";

export default function DeductionBoardPage() {
  const navigate = useNavigate();
  const { view } = useGameStore();

  if (!view) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-mystic-text-dim">没有活跃的游戏</p>
      </div>
    );
  }

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
        <h3 className="text-mystic-gold font-bold mb-1">{view.case_name}</h3>
        <p className="text-mystic-text-dim text-xs">
          当前章节：{view.chapter}
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
                  key={clue.id}
                  className={`p-3 rounded text-sm border ${
                    clue.is_key
                      ? "border-mystic-accent/40 bg-mystic-accent/5"
                      : "border-mystic-card/40 bg-mystic-bg/50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-mystic-text">
                      {clue.name}
                    </span>
                    {clue.is_key && (
                      <span className="text-[10px] text-mystic-accent px-1.5 py-0.5 rounded bg-mystic-accent/10">
                        关键
                      </span>
                    )}
                  </div>
                  <p className="text-mystic-text-dim text-xs">
                    {clue.description}
                  </p>
                  <p className="text-mystic-text-dim/50 text-[10px] mt-1">
                    来源：{clue.source}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: NPC Statements + Divination */}
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
                  <div key={npc.id}>
                    <h4 className="text-sm text-mystic-accent font-medium mb-1">
                      {npc.name}
                    </h4>
                    {npc.statements.length === 0 ? (
                      <p className="text-mystic-text-dim text-xs italic pl-3">
                        暂无证词
                      </p>
                    ) : (
                      <ul className="space-y-1">
                        {npc.statements.map((stmt, idx) => (
                          <li
                            key={idx}
                            className="text-xs text-mystic-text pl-3 border-l-2 border-mystic-card"
                          >
                            {stmt}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Divination Results */}
          {view.divination_results.length > 0 && (
            <div className="card">
              <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
                占卜结果
              </h3>
              <div className="space-y-2">
                {view.divination_results.map((dr) => (
                  <div key={dr.id} className="border border-purple-800/30 bg-purple-900/5 rounded p-3">
                    <p className="text-sm text-mystic-gold mb-1">
                      {dr.content}
                    </p>
                    <p className="text-xs text-mystic-text-dim">
                      {dr.interpretation}
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                      <span className="text-[10px] text-mystic-text-dim">
                        灵性强度：
                      </span>
                      <div className="status-bar flex-1 max-w-[100px]">
                        <div
                          className="status-fill bg-purple-500"
                          style={{ width: `${dr.potency}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-mystic-text-dim">
                        {dr.potency}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Hypotheses Section */}
      <div className="mt-6">
        <HypothesisPanel hypotheses={view.hypotheses} />
      </div>

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
