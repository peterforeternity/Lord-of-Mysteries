import { useNavigate } from "react-router-dom";

const sections = [
  {
    id: "overview",
    title: "游戏简介",
    content: (
      <p className="text-sm text-mystic-text leading-relaxed">
        《诡秘之主》是一款以维多利亚时代为背景的侦探推理文本游戏。
        你扮演一名神秘的调查员，在一座被灰雾笼罩的城市中调查离奇案件。
        通过收集线索、审问嫌疑人、运用神秘能力，揭开隐藏在表象之下的真相。
      </p>
    ),
  },
  {
    id: "stats",
    title: "角色状态",
    content: (
      <div className="space-y-2 text-sm text-mystic-text leading-relaxed">
        <p>
          <span className="text-mystic-gold font-medium">灵性</span>
          — 你的精神力储备。使用灵视、占卜等能力会消耗灵性。
          灵性不足时无法使用这些能力。休息可以恢复灵性。
        </p>
        <p>
          <span className="text-mystic-gold font-medium">污染</span>
          — 接触超自然力量积累的侵蚀。污染过高会触发坏结局。
          进行仪式失败会增加污染，某些特殊行动也可以降低污染。
        </p>
        <p>
          <span className="text-mystic-gold font-medium">稳定度</span>
          — 你的心理状态。遭遇恐怖事件或持续调查压力会降低稳定度。
          稳定度过低也会导致危险。
        </p>
      </div>
    ),
  },
  {
    id: "actions",
    title: "基础行动",
    content: (
      <div className="space-y-3 text-sm text-mystic-text">
        <div>
          <span className="text-mystic-accent font-medium">移动</span>
          <p className="leading-relaxed">
            在案件的不同地点之间移动。每个地点都有不同的线索和人物。
            注意：某些地点需要先解锁才能前往。
          </p>
        </div>
        <div>
          <span className="text-mystic-accent font-medium">调查</span>
          <p className="leading-relaxed">
            检查当前地点的物品、痕迹或文件。调查是获取线索的主要方式。
            点击线索名称即可查看详情。
          </p>
        </div>
        <div>
          <span className="text-mystic-accent font-medium">交谈</span>
          <p className="leading-relaxed">
            与案件相关的NPC对话，获取证词和情报。
            注意：有些NPC可能会撒谎，需要其他证据来验证。
          </p>
        </div>
        <div>
          <span className="text-mystic-accent font-medium">休息</span>
          <p className="leading-relaxed">
            恢复灵性和稳定度。在你感到疲惫或灵性不足时使用。
          </p>
        </div>
      </div>
    ),
  },
  {
    id: "abilities",
    title: "特殊能力",
    content: (
      <div className="space-y-3 text-sm text-mystic-text">
        <div>
          <span className="text-purple-400 font-medium">灵视</span>
          <p className="leading-relaxed">
            打开灵性视觉，发现隐藏的线索和灵体痕迹。
            消耗1点灵性。在某些场景中可以看到正常视觉无法发现的东西。
          </p>
        </div>
        <div>
          <span className="text-purple-400 font-medium">占卜</span>
          <p className="leading-relaxed">
            通过灵性占卜获取线索。可能会产生随机的启示或干扰。
            需要消耗灵性。
          </p>
        </div>
        <div>
          <span className="text-purple-400 font-medium">仪式</span>
          <p className="leading-relaxed">
            执行神秘的仪式，处理超自然实体或获取特殊效果。
            需要特定的知识、材料和场地条件。仪式可能成功也可能失败，
            失败会增加污染。
          </p>
        </div>
      </div>
    ),
  },
  {
    id: "clues",
    title: "线索与推理",
    content: (
      <div className="space-y-2 text-sm text-mystic-text leading-relaxed">
        <p>
          你发现的每条线索都会记录在线索列表中。线索有不同来源：
          调查现场、NPC证词、灵视发现等。关键线索是解开案件的核心。
        </p>
        <p className="mt-2">
          收集足够线索后，前往<span className="text-mystic-gold font-medium">推理板</span>，
          你可以查看已解锁的假设。每个假设需要特定的线索组合才能提交。
          提交正确的假设将推动案件走向结局。
        </p>
      </div>
    ),
  },
  {
    id: "save",
    title: "存档与读取",
    content: (
      <div className="space-y-2 text-sm text-mystic-text leading-relaxed">
        <p>
          游戏自动跟踪你的每一步操作。你也可以手动
          <span className="text-mystic-accent font-medium">保存</span>当前进度。
          存档管理页面可以查看所有存档、读取存档或删除不需要的存档。
        </p>
        <p className="mt-2">
          注意：<span className="text-yellow-400">每次操作都会增加状态版本号</span>。
          如果从旧状态继续操作，后端会检测到冲突并提示错误。
          请确保读取存档后再进行操作。
        </p>
      </div>
    ),
  },
  {
    id: "endings",
    title: "结局",
    content: (
      <div className="space-y-2 text-sm text-mystic-text leading-relaxed">
        <p>
          案件可以有多种结局，取决于你收集的线索和提交的假设：
        </p>
        <ul className="list-disc list-inside space-y-1 mt-1">
          <li>
            <span className="text-green-400">真相结局</span>
            — 发现全部关键线索，提交正确的假设
          </li>
          <li>
            <span className="text-yellow-400">部分真相</span>
            — 掌握部分线索，触及案件表面
          </li>
          <li>
            <span className="text-red-400">疯狂结局</span>
            — 污染过高或稳定度过低导致精神崩溃
          </li>
          <li>
            <span className="text-blue-400">逃脱结局</span>
            — 选择放弃调查离开
          </li>
        </ul>
      </div>
    ),
  },
  {
    id: "tips",
    title: "实用技巧",
    content: (
      <ul className="list-disc list-inside space-y-1 text-sm text-mystic-text leading-relaxed">
        <li>到达新地点后先调查所有可能的线索</li>
        <li>与每个NPC交谈获取证词</li>
        <li>灵性不足时及时休息</li>
        <li>注意污染值，不要盲目进行仪式</li>
        <li>定期保存进度</li>
        <li>推理板上的假设可以查看所需线索</li>
        <li>不同地点可能有隐藏线索需要特殊能力</li>
      </ul>
    ),
  },
];

export default function TutorialPage() {
  const navigate = useNavigate();

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-6">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-serif font-bold text-mystic-gold mb-2 tracking-widest">
            新手教程
          </h1>
          <div className="divider" />
          <p className="text-mystic-text-dim text-sm">
            了解游戏机制，成为合格的灰雾调查员
          </p>
        </div>

        {/* Sections */}
        <div className="space-y-6 mb-8">
          {sections.map((section) => (
            <div key={section.id} id={section.id} className="card">
              <h2 className="text-mystic-gold text-base font-bold mb-3 tracking-wider">
                {section.title}
              </h2>
              {section.content}
            </div>
          ))}
        </div>

        {/* Back button */}
        <div className="text-center pb-8">
          <button
            onClick={() => navigate(-1)}
            className="btn-primary px-8 py-3"
          >
            返回
          </button>
        </div>

        {/* Footer */}
        <div className="divider" />
        <p className="text-mystic-text-dim/30 text-xs text-center italic pb-4">
          诡秘之主 · 真相终将浮现
        </p>
      </div>
    </div>
  );
}
