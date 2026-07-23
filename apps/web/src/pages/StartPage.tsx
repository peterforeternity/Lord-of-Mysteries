import { useNavigate } from "react-router-dom";

export default function StartPage() {
  const navigate = useNavigate();

  const isDev =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";

  return (
    <div className="flex-1 flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        {/* Title */}
        <h1 className="text-4xl md:text-5xl font-serif font-bold text-mystic-gold mb-4 tracking-widest">
          灰雾调查录
        </h1>
        <p className="text-mystic-text-dim text-sm mb-10">
          在灰雾笼罩的世界中，揭开隐藏的真相
        </p>

        {/* Main buttons */}
        <div className="space-y-3 mb-8">
          <button
            onClick={() => navigate("/case-select")}
            className="btn-primary w-full py-3 text-base"
          >
            新游戏
          </button>

          <button
            onClick={() => navigate("/save-load")}
            className="btn-secondary w-full py-3 text-base"
          >
            继续游戏
          </button>

          <button
            onClick={() => navigate("/case-select")}
            className="btn-secondary w-full py-3 text-base"
          >
            案件选择
          </button>

          <button
            onClick={() => navigate("/settings")}
            className="btn-ghost w-full py-2 text-sm"
          >
            设置
          </button>

          <button
            onClick={() => navigate("/tutorial")}
            className="btn-ghost w-full py-2 text-sm text-mystic-accent-dim"
          >
            新手教程
          </button>
        </div>

        {/* Theme atmosphere */}
        <div className="divider" />
        <p className="text-mystic-text-dim/40 text-xs italic">
          &ldquo;在每一片灰雾之后，都藏着一个不愿被述说的真相。&rdquo;
        </p>

        {/* Developer mode badge */}
        {isDev && (
          <div className="mt-6 inline-block px-3 py-1 rounded-full bg-mystic-card/50 border border-mystic-accent/20">
            <span className="text-mystic-accent-dim text-[10px]">
              🛠 开发者模式 — 本地环境
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
