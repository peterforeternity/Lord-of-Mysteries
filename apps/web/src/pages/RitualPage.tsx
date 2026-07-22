import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useGameStore } from "../store";

export default function RitualPage() {
  const navigate = useNavigate();
  const { view, executeAction, loading } = useGameStore();
  const [selectedRitual, setSelectedRitual] = useState<string | null>(null);

  if (!view) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-mystic-text-dim">没有活跃的游戏</p>
      </div>
    );
  }

  const rituals = view.rituals || [];

  const handlePerformRitual = async (ritualId: string) => {
    await executeAction("perform_ritual", { ritual_id: ritualId });
    setSelectedRitual(null);
  };

  return (
    <div className="flex-1 p-4 md:p-8 max-w-4xl mx-auto w-full">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-serif font-bold text-mystic-gold tracking-wider">
          仪式
        </h2>
        <button onClick={() => navigate("/game")} className="btn-ghost text-sm">
          返回调查
        </button>
      </div>

      {/* Spirituality warning */}
      <div className="card border-purple-800/30 bg-purple-900/5 mb-6">
        <p className="text-sm text-purple-300">
          灵性：{view.player_status.spirituality}/
          {view.player_status.max_spirituality}
        </p>
        <p className="text-xs text-purple-400/60 mt-1">
          进行仪式将消耗灵性，请谨慎选择
        </p>
      </div>

      {rituals.length === 0 ? (
        <div className="card text-center py-10">
          <p className="text-mystic-text-dim text-sm">
            当前没有可用的仪式
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {rituals.map((ritual) => (
            <div
              key={ritual.id}
              className={`card ${
                selectedRitual === ritual.id
                  ? "border-purple-500 bg-purple-900/10"
                  : "hover:border-purple-800/40"
              } ${!ritual.is_available ? "opacity-50" : ""}`}
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-mystic-gold font-bold">{ritual.name}</h3>
                {!ritual.is_available && (
                  <span className="text-xs text-mystic-text-dim bg-mystic-card px-2 py-0.5 rounded">
                    不可用
                  </span>
                )}
              </div>
              <p className="text-mystic-text-dim text-sm mb-3">
                {ritual.description}
              </p>

              {/* Required materials */}
              <div className="mb-3">
                <h4 className="text-xs text-mystic-accent font-bold mb-1">
                  所需材料
                </h4>
                <ul className="space-y-1">
                  {ritual.required_materials.map((mat) => (
                    <li
                      key={mat.item_id}
                      className={`text-xs flex items-center justify-between ${
                        mat.has_enough
                          ? "text-green-400"
                          : "text-red-400"
                      }`}
                    >
                      <span>
                        {mat.item_name} x{mat.quantity}
                      </span>
                      <span>{mat.has_enough ? "✓" : "✗"}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <button
                onClick={() => handlePerformRitual(ritual.id)}
                disabled={!ritual.is_available || loading}
                className={`btn w-full text-sm ${
                  ritual.is_available
                    ? "bg-purple-700 text-white hover:bg-purple-600"
                    : "btn-secondary opacity-50"
                }`}
              >
                {loading ? "进行中..." : "执行仪式"}
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6">
        <button onClick={() => navigate("/game")} className="btn-primary">
          返回调查
        </button>
      </div>
    </div>
  );
}
