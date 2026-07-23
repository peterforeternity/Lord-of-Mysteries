# Project Grey Fog 文游版需求与开发规范 v0.2

## 0. 项目定位

项目名称：Project Grey Fog / 灰雾调查录  
产品形态：浏览器单机调查推理文游  
目标设备：Mac M1 8GB、普通 Windows 笔记本、手机浏览器  
技术目标：复用现有 Python Investigation Core 和 AI Gateway，不依赖 Unreal Engine  
IP 原则：未取得正式授权前，全部使用原创占位人物、地点、组织、能力和文本，不直接复制《诡秘之主》原文、角色、专有地点、声音和美术。

## 1. 为什么先做文游

当前项目最核心的价值不是 3D 场景，而是：

- 信息是否能成为真正的游戏资源；
- 调查、占卜、仪式和推理是否有趣；
- NPC 是否能在知识边界内自然回应；
- 玩家是否会因为错误判断承担代价；
- 多条调查路线是否都能完成案件；
- AI 关闭时游戏是否仍然成立。

这些问题全部可以先用浏览器文游验证。

文游版的优势：

1. 不需要 UE5；
2. 不需要高配置电脑；
3. 可以直接复用已完成的案件核心和自动化测试；
4. 能快速加入第二个案件；
5. 能更快测试推理、污染、扮演和异常物品系统；
6. 后续可作为 UE5 版本的内容编辑器和调试前端。

## 2. MVP 目标

制作一个可在浏览器完整游玩的 40—60 分钟调查案件。

MVP 必须包含：

- 一个完整案件；
- 五个地点；
- 六个核心 NPC；
- 十五条左右线索；
- 四个推理假设；
- 五个结局；
- 灵视；
- 占卜；
- 仪式；
- 污染；
- 灵性；
- 一件带副作用的异常物品；
- NPC 对话；
- 调查日志；
- 推理板；
- 保存与读取；
- AI 开关；
- AI 断网回退；
- 完整事件日志；
- 可重复游玩。

## 3. 核心体验

玩家不是通过“点击黄色感叹号”自动获得答案，而是：

进入地点  
→ 阅读环境描述  
→ 选择调查对象  
→ 获得物证或陈述  
→ 判断信息是否可信  
→ 使用灵视、占卜或仪式验证  
→ 在推理板提交假设  
→ 承担灵性消耗、污染或异常物品代价  
→ 选择公开、隐瞒、交易、封存或逃离  
→ 进入不同结局。

## 4. 游戏内容

### 4.1 示例案件

案件名称：钟表匠失踪案

表面事件：

一名钟表匠在锁住的公寓中失踪。房间没有强行进入痕迹，桌上的茶仍然温热，墙上的钟全部停在同一时刻。

案件核心：

- 钟表匠曾修复一件异常钟表；
- 他使用了错误仪式；
- 数名 NPC 各自掌握不完整的信息；
- 一名 NPC 在说谎，但说谎并非因为他是真凶；
- 玩家过早指控会导致关键人物逃离；
- 错误仪式会增加污染；
- 正确调查可以避免最终冲突。

### 4.2 地点

1. 失踪者公寓；
2. 警务办公室；
3. 私人诊所；
4. 神秘材料商店；
5. 废弃钟表工坊。

每个地点包含：

- 地点描述；
- 可调查物；
- 可交谈 NPC；
- 可使用能力；
- 地点状态；
- 已发现线索；
- 隐藏前置条件；
- 可能触发的事件。

### 4.3 NPC

六个核心 NPC：

- 房东；
- 医生；
- 材料商人；
- 邻居；
- 调查员；
- 收藏家。

每个 NPC 必须包含：

- NPC ID；
- 显示名称；
- 身份；
- 个性；
- 当前状态；
- 已知 Claim；
- 谎言 Claim；
- 禁止知道的 Fact；
- 对玩家关系；
- 情绪；
- 可用预制对白；
- AI 对话边界；
- 逃离、敌对或被移除后的替代线索路径。

## 5. 页面结构

### 5.1 开始页

显示：

- 新游戏；
- 继续游戏；
- 案件选择；
- AI 对话开关；
- 设置；
- 开发者模式，仅本地开发环境显示。

### 5.2 主游戏页

推荐三栏结构。

左侧：

- 当前地点；
- 可前往地点；
- 角色状态；
- 灵性；
- 污染；
- 稳定度；
- 当前持有物品。

中间：

- 场景描述；
- 对话记录；
- 调查结果；
- 仪式反馈；
- 选项按钮；
- 自由输入框，仅 NPC 对话时出现。

右侧：

- 当前任务提示；
- 最近线索；
- 调查日志；
- 推理板入口；
- 保存按钮；
- 设置。

手机端改为底部标签页：

- 场景；
- 线索；
- 推理；
- 状态；
- 设置。

### 5.3 推理板

显示：

- 已获得线索；
- NPC 陈述；
- 占卜结果；
- 仪式结果；
- 当前四个 Hypothesis；
- 支持证据；
- 矛盾证据；
- 当前可信度；
- 提交按钮。

禁止自动告诉玩家正确答案。

### 5.4 案件结算页

显示：

- 最终结局；
- 已发现真相比例；
- 错过的线索类别，不直接泄露内容；
- 污染结果；
- 扮演评价；
- 关键选择；
- 是否保存新周目知识；
- 重新开始。

## 6. 系统设计

### 6.1 Fact、Claim、Clue、Hypothesis

Fact：

- 客观真相；
- 玩家不能直接看到；
- AI 不得读取完整 Fact 集合。

Claim：

- NPC 的认知或陈述；
- 可以是真、假、部分正确或误导；
- AI 只能引用当前 NPC 被授权的 Claim。

Clue：

- 玩家实际获得的证据；
- 来源包括环境、档案、NPC、灵视、占卜和仪式；
- 关键 Fact 至少有两个独立来源。

Hypothesis：

- 玩家提交的推理；
- 必须包含支持线索、矛盾线索和可信度；
- 错误假设也必须产生合理后果，而不是简单提示“答错”。

### 6.2 角色资源

Spirituality 灵性：

- 使用能力时消耗；
- 可以通过休息、道具或安全仪式恢复；
- 灵性不足时能力失败或产生偏差。

Corruption 污染：

- 使用危险能力、失败仪式、接触异常物时增加；
- 污染影响文本、可选项和结局；
- 污染不得由 AI 自由生成。

Stability 稳定度：

- 代表角色维持自我的能力；
- 可以缓冲污染后果；
- 某些错误行为降低稳定度。

### 6.3 灵视

玩家在指定场景使用灵视后：

- 消耗灵性；
- 揭示预设异常痕迹；
- 可能获得 Clue；
- 可能提高污染；
- 灵视结果来自确定性数据，不由 LLM 临时编造。

### 6.4 占卜

玩家选择：

- 问题；
- 媒介；
- 已有线索；
- 投入灵性。

系统根据固定 Seed 输出：

- 象征画面；
- 倾向；
- 可信度；
- 干扰程度；
- 代价。

相同存档、相同输入、相同 Seed 必须获得相同结果。

### 6.5 仪式

仪式包含：

- 目的；
- 前置知识；
- 材料；
- 步骤；
- 环境条件；
- 成功结果；
- 失败结果；
- 污染变化；
- 是否惊动 NPC 或异常实体。

仪式页面需要让玩家自己选择材料和顺序。

### 6.6 异常物品

MVP 一件异常物品。

能力：

- 查看物体最近一次被触碰时的模糊残影。

代价：

- 使用后，玩家下一次与 NPC 对话必须选择一句不完全真实的陈述；
- 若拒绝承担代价，污染增加。

副作用必须进入真实交互，不只是扣数值。

### 6.7 扮演倾向

MVP 不升级序列，只记录扮演倾向。

加分：

- 先观察后判断；
- 验证信息；
- 用能力规避风险；
- 保持克制。

减分：

- 无证据指控；
- 滥用能力；
- 依赖暴力；
- 明知污染过高仍继续冒险。

所有判断由 Gameplay Event 触发，不由 LLM 主观评分。

## 7. AI 对话

### 7.1 AI 可以做

- 将预制 Claim 改写成自然语言；
- 根据情绪调整语气；
- 判断玩家问题意图；
- 从允许的 Claim 中选择回答；
- 生成不影响案件的短闲聊；
- 生成对话摘要。

### 7.2 AI 禁止做

- 新增关键人物；
- 新增组织；
- 新增案件事实；
- 创建线索；
- 修改任务；
- 发放物品；
- 改变 NPC 状态；
- 决定结局；
- 引用 NPC 不知道的 Fact；
- 读取完整案件真相。

### 7.3 AI 回退

以下情况使用 fallback dialogue：

- AI 开关关闭；
- API 超时；
- 网络断开；
- 非法 JSON；
- 引用未授权 Claim；
- 泄露 Fact；
- 请求世界写操作；
- 输出过长；
- Prompt injection。

游戏主线不得依赖 AI。

## 8. 技术方案

### 8.1 前端

推荐：

- React 18；
- TypeScript；
- Vite；
- Zustand；
- React Router；
- Tailwind CSS；
- Zod；
- Vitest；
- Playwright。

M1 8GB 可以正常运行。

### 8.2 后端

复用现有：

- Python 3.12；
- FastAPI；
- Pydantic v2；
- Investigation Core；
- AI Gateway；
- SQLite；
- MockLLMProvider；
- pytest。

### 8.3 接口

保留：

- GET /v1/health
- GET /v1/prompt-version
- POST /v1/dialogue/respond
- POST /v1/dialogue/classify-intent
- POST /v1/case/recap

新增：

- POST /v1/game/new
- GET /v1/game/{save_id}
- POST /v1/game/{save_id}/action
- POST /v1/game/{save_id}/save
- POST /v1/game/{save_id}/load
- GET /v1/game/{save_id}/view
- GET /v1/cases
- GET /v1/cases/{case_id}/metadata

推荐游戏动作：

```json
{
  "action_type": "inspect",
  "target_id": "clue_burn_pattern",
  "parameters": {},
  "expected_version": 12
}
```

返回：

```json
{
  "success": true,
  "state_version": 13,
  "events": [],
  "view": {},
  "error_code": null
}
```

前端不得直接修改世界状态。

### 8.4 状态版本

每次 Action 增加 `state_version`。

前端提交动作时必须携带 `expected_version`。

版本不一致时返回：

- `STATE_VERSION_CONFLICT`

避免重复点击、并发请求或浏览器恢复导致状态错乱。

### 8.5 存档

使用 SQLite。

存档内容：

- save_id；
- case_id；
- seed；
- state_version；
- 当前地点；
- 已发现 Clue；
- 已揭示 Fact；
- Claim；
- Hypothesis 状态；
- NPC 状态；
- 灵性；
- 污染；
- 稳定度；
- 物品；
- 事件日志；
- 创建和更新时间。

不要保存 AI 自由生成的事实。

## 9. 建议仓库结构

```text
Lord-of-Mysteries/
├── apps/
│   └── web/
├── packages/
│   └── investigation_core/
├── services/
│   ├── ai_gateway/
│   └── game_api/
├── content/
├── schemas/
├── tools/
├── docs/
└── unreal/
```

Unreal 目录保留，但文游开发期间不继续扩展。

## 10. 开发阶段

### 阶段一：可玩无 AI 版本

实现：

- 新游戏；
- 五个地点；
- 调查；
- 对话选项；
- 灵视；
- 占卜；
- 仪式；
- 推理板；
- 五个结局；
- 保存读取。

验收：

- AI 完全关闭；
- 从开始到五个结局全部可达；
- 现有 7 条 Playthrough 可以通过 Game API 重放；
- 手机和电脑浏览器可操作。

### 阶段二：AI 对话

实现：

- 自由输入；
- Claim 白名单；
- Fact Leak 检查；
- fallback；
- 对话摘要；
- AI 开关。

验收：

- 事实泄漏为 0；
- AI 关闭不影响通关；
- AI 超时不阻塞页面；
- Prompt injection 全部回退。

### 阶段三：表现完善

实现：

- 背景图；
- NPC 头像；
- 音效；
- 打字机效果；
- 污染视觉效果；
- 响应式布局；
- 新手引导；
- 案件结算。

正式美术可以晚做，MVP 使用占位图和 CSS 即可。

## 11. 开发规范

1. 现有 Python Core 是世界状态权威；
2. 前端只提交 Action；
3. 所有动作必须经过后端验证；
4. AI 不得直接写状态；
5. 核心案件数据不得硬编码在 React；
6. 所有随机使用显式 Seed；
7. 所有 API 使用稳定 error_code；
8. 所有状态更新写入 EventLog；
9. 保存必须可重放；
10. 新增功能必须有测试；
11. 不允许降低现有 90% 覆盖率要求；
12. 不修改已经冻结的 v0.1.0-headless 逻辑，新增功能通过兼容层实现；
13. 不调用真实付费模型进行测试；
14. 不提交密钥、Token、`.env` 和数据库文件；
15. 未获得授权前不使用原著原文和正式素材。

## 12. Definition of Done

文游 MVP 完成必须满足：

- 新玩家能在浏览器完成一个案件；
- 五个结局均可达；
- 关键 Fact 至少两个来源；
- 无唯一线索软锁；
- AI 关闭时可通关；
- 断网时可通关；
- 保存和加载状态一致；
- 相同 Seed 可重放；
- 手机端可使用；
- 现有测试继续通过；
- 新增前端和 Game API 测试通过；
- GitHub Actions 全绿；
- README 有完整启动说明。

# 可直接交给 Trae / Codex 的开发指令

```text
Project Grey Fog 现在转向浏览器文游 MVP。

当前电脑是 Mac M1 8GB，不继续进行 Unreal Engine 开发。保留 unreal/ 目录，但暂停扩展 UE 代码。

目标：
在现有 Investigation Core 和 AI Gateway 基础上，制作一个可在浏览器完整游玩的单机调查推理文游。

不得修改已经冻结的 v0.1.0-headless 核心行为。新增功能使用 game_api 服务和 web 前端。

【技术栈】

前端：
- React 18
- TypeScript
- Vite
- Zustand
- React Router
- Tailwind CSS
- Zod
- Vitest
- Playwright

后端：
- Python 3.12
- FastAPI
- Pydantic v2
- SQLite
- 现有 investigation_core
- 现有 ai_gateway
- pytest

【第一阶段：无 AI 可玩版本】

创建：
- apps/web
- services/game_api
- docs/text-game-architecture.md
- schemas/game-action.schema.json
- schemas/game-view.schema.json

必须实现：

1. GET /v1/cases
2. GET /v1/cases/{case_id}/metadata
3. POST /v1/game/new
4. GET /v1/game/{save_id}
5. GET /v1/game/{save_id}/view
6. POST /v1/game/{save_id}/action
7. POST /v1/game/{save_id}/save
8. POST /v1/game/{save_id}/load

动作统一为：

{
  "action_type": "inspect",
  "target_id": "clue_id",
  "parameters": {},
  "expected_version": 1
}

支持动作：

- travel
- inspect
- talk
- use_spirit_vision
- perform_divination
- perform_ritual
- use_item
- submit_hypothesis
- rest
- save
- load

所有动作必须由后端执行，前端不得直接修改案件状态。

每次成功动作增加 state_version。
expected_version 不一致返回 STATE_VERSION_CONFLICT。

【页面】

1. 开始页
2. 案件选择页
3. 主游戏页
4. NPC 对话界面
5. 推理板
6. 仪式界面
7. 保存读取界面
8. 案件结算页
9. 设置页

主游戏页必须显示：

- 当前地点
- 场景描述
- 可调查目标
- 可交谈 NPC
- 可前往地点
- 灵性
- 污染
- 稳定度
- 已持有物品
- 最近线索
- 调查日志

【案件】

复用 case_clockmaker_01。

必须在浏览器中完整支持：

- 五个地点
- 六个核心 NPC
- 15 条线索
- 四个 Hypothesis
- 五个 Ending
- 灵视
- 占卜
- 仪式
- 异常物品代价
- 污染
- 保存加载

【AI 边界】

第一阶段默认关闭 AI。
NPC 使用 fallback_dialogue 和预制 Claim 完成全部剧情。

第二阶段才接入：
- POST /v1/dialogue/respond
- POST /v1/dialogue/classify-intent
- POST /v1/case/recap

AI 只负责对白表达，不得改变世界状态。

【UI 规范】

- 深色、低饱和神秘风格
- 不使用受版权保护的原著素材
- CSS 和简单占位图即可
- 支持桌面和手机
- 不做复杂动画
- 污染效果必须可以关闭
- 不使用三栏固定宽度导致手机溢出

【测试】

后端：
- 所有 Action 单元测试
- state_version 冲突测试
- 保存加载测试
- 五个结局可达测试
- AI 关闭通关测试
- 断网回退测试
- 相同 Seed 重放测试

前端：
- 主要页面渲染测试
- 状态管理测试
- API 错误测试
- 推理板测试
- 保存加载测试

E2E：
- true ending
- partial ending
- bad ending
- ai disabled
- save resume
- ritual failure recovery
- npc removed recovery

尽量复用现有 playthrough JSON。

【质量命令】

必须通过：

uv sync --frozen
uv run ruff check .
uv run black --check .
uv run mypy .
uv run pytest --cov --cov-report=term-missing --cov-fail-under=90
uv run python tools/run_playthrough.py --all

前端必须通过：

npm install
npm run lint
npm run typecheck
npm run test
npm run build
npm run test:e2e

不要声称运行了未运行的命令。

【禁止】

- 不继续添加 UE 功能
- 不安装 UE
- 不使用 WebSocket
- 不使用动态语音
- 不调用真实付费模型
- 不做多人
- 不做账号系统
- 不做商城
- 不做第二个案件
- 不做正式美术
- 不直接复制《诡秘之主》原文、角色、地点和声音
- 不修改世界状态权威边界

【执行顺序】

1. 检查现有仓库
2. 创建 game_api
3. 创建 Action 和 View Schema
4. 实现 SQLite 存档
5. 复用现有 Playthrough
6. 编写后端测试
7. 创建 React 前端
8. 实现无 AI 完整案件
9. 编写前端测试
10. 编写 E2E
11. 运行全部质量门禁
12. 更新 README
13. 提交到新分支 feat/text-game-mvp
14. 推送并等待 GitHub Actions

完成后报告：

- 创建和修改的文件
- Game API 路径
- 页面清单
- 五个结局复现步骤
- 测试数量
- 覆盖率
- 前端 build 结果
- E2E 结果
- Commit SHA
- GitHub Actions 状态
- 未完成事项

现在开始第一阶段：无 AI 浏览器文游版本。
```
