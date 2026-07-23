import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function SettingsPage() {
  const navigate = useNavigate();
  const [aiEnabled, setAiEnabled] = useState(true);
  const [pollutionEffects, setPollutionEffects] = useState(true);

  return (
    <div className="flex-1 p-4 md:p-8 max-w-2xl mx-auto w-full">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-serif font-bold text-mystic-gold tracking-wider">
          设置
        </h2>
        <button onClick={() => navigate(-1)} className="btn-ghost text-sm">
          返回
        </button>
      </div>

      <div className="space-y-4">
        {/* AI Toggle */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-mystic-text font-medium text-sm">
                AI 叙事生成
              </h3>
              <p className="text-mystic-text-dim text-xs mt-1">
                启用 AI 驱动的动态叙事和对话生成
              </p>
            </div>
            <button
              onClick={() => setAiEnabled(!aiEnabled)}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                aiEnabled ? "bg-mystic-accent" : "bg-mystic-card"
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                  aiEnabled ? "translate-x-6" : "translate-x-0"
                }`}
              />
            </button>
          </div>
        </div>

        {/* Pollution Effects Toggle */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-mystic-text font-medium text-sm">
                污染效果显示
              </h3>
              <p className="text-mystic-text-dim text-xs mt-1">
                在界面中显示污染相关的视觉效果和描述
              </p>
            </div>
            <button
              onClick={() => setPollutionEffects(!pollutionEffects)}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                pollutionEffects ? "bg-mystic-accent" : "bg-mystic-card"
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                  pollutionEffects ? "translate-x-6" : "translate-x-0"
                }`}
              />
            </button>
          </div>
        </div>

        {/* About */}
        <div className="card">
          <h3 className="text-mystic-text font-medium text-sm mb-2">
            关于
          </h3>
          <div className="text-xs text-mystic-text-dim space-y-1">
            <p>诡秘之主</p>
            <p>版本 0.1.0</p>
            <p className="italic mt-2">
              这是一个基于文本的调查解谜游戏。在灰雾笼罩的世界中，您将扮演调查员，揭开关联神秘事件的真相。
            </p>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="card border-mystic-card/30">
          <h3 className="text-mystic-text font-medium text-sm mb-2">
            免责声明
          </h3>
          <p className="text-xs text-mystic-text-dim/50 leading-relaxed">
            本游戏为原创作品，所有角色、事件、地点均为虚构。如有雷同，纯属巧合。
            游戏内容不涉及任何现实政治、历史事件或人物。
          </p>
        </div>
      </div>
    </div>
  );
}
