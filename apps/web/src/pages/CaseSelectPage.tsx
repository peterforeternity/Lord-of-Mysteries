import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useGameStore } from "../store";
import { listCases } from "../api";
import type { CaseMeta } from "../types";

export default function CaseSelectPage() {
  const navigate = useNavigate();
  const { newGame, loading } = useGameStore();
  const [cases, setCases] = useState<CaseMeta[]>([]);
  const [selectedCase, setSelectedCase] = useState<string | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    listCases()
      .then((res) => setCases(res.cases))
      .catch((err) =>
        setFetchError(err instanceof Error ? err.message : "获取案件列表失败")
      );
  }, []);

  const handleStart = async () => {
    if (!selectedCase) return;
    await newGame(selectedCase);
    navigate("/game");
  };

  return (
    <div className="flex-1 p-4 md:p-8 max-w-4xl mx-auto w-full">
      <h2 className="text-xl font-serif font-bold text-mystic-gold mb-6 tracking-wider">
        案件选择
      </h2>

      {fetchError && (
        <div className="card border-red-800 bg-red-900/10 mb-6">
          <p className="text-red-400 text-sm">{fetchError}</p>
          <button
            onClick={() => {
              setFetchError(null);
              listCases()
                .then((res) => setCases(res.cases))
                .catch((err) =>
                  setFetchError(
                    err instanceof Error ? err.message : "获取案件列表失败"
                  )
                );
            }}
            className="btn-ghost text-xs mt-2"
          >
            重试
          </button>
        </div>
      )}

      {cases.length === 0 && !fetchError && (
        <div className="card text-center py-10">
          <p className="text-mystic-text-dim text-sm">
            {loading ? "加载中..." : "暂无可用的案件"}
          </p>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {cases.map((c) => (
          <button
            key={c.case_id}
            onClick={() => setSelectedCase(c.case_id)}
            className={`card text-left transition-all no-underline ${
              selectedCase === c.case_id
                ? "border-mystic-accent bg-mystic-accent/5"
                : "hover:border-mystic-accent/40"
            } ${!c.is_available ? "opacity-50" : ""}`}
            disabled={!c.is_available}
          >
            <div className="flex items-start justify-between mb-2">
              <h3 className="text-mystic-gold font-bold">{c.title}</h3>
              {!c.is_available && (
                <span className="text-xs text-mystic-text-dim bg-mystic-card px-2 py-0.5 rounded">
                  未开放
                </span>
              )}
            </div>
            <p className="text-mystic-text-dim text-sm mb-3">
              {c.description}
            </p>
            <div className="flex items-center gap-3 text-xs text-mystic-text-dim">
              <span>
                难度：{" "}
                <span
                  className={
                    c.difficulty === "简单"
                      ? "text-green-400"
                      : c.difficulty === "中等"
                      ? "text-yellow-400"
                      : "text-red-400"
                  }
                >
                  {c.difficulty}
                </span>
              </span>
              <span>预计：{c.estimated_hours}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Bottom Actions */}
      <div className="flex items-center gap-3 mt-8">
        <button
          onClick={handleStart}
          disabled={!selectedCase || loading}
          className="btn-primary py-3 px-8 text-base"
        >
          {loading ? "创建中..." : "开始调查"}
        </button>
        <button onClick={() => navigate("/")} className="btn-ghost">
          返回
        </button>
      </div>
    </div>
  );
}
