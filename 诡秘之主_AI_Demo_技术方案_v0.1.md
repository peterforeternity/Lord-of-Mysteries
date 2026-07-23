# 《诡秘之主》AI 辅助游戏 Demo 可行性与技术方案 v0.1

- 文档状态：概念验证 / Vertical Slice 前置方案
- 日期：2026-07-21
- 默认平台：Windows PC
- 推荐引擎：Unreal Engine 5.8
- 推荐形态：单机、高密度箱庭、调查推理 RPG
- 核心原则：确定性案件系统掌握真相；AI 只做受约束的内容表达与开发辅助
- IP 前提：获得正式授权前，只制作不公开传播的内部原型，并使用原创占位名称、角色和美术

---

## 1. 结论

### 1.1 技术上能不能：能

制作一个能够体现以下体验的 30—50 分钟 Demo，在现有技术条件下完全可行：

1. 一个高密度街区；
2. 一个多路线调查案件；
3. 6 个核心 NPC 与若干环境 NPC；
4. 灵视、占卜、仪式验证、身份交涉；
5. 一个可选战斗或潜入收尾；
6. 3 个结局；
7. NPC 能根据已发生事件和自身知识范围动态回答；
8. AI 断线时仍可使用预制对白完成游戏。

Unreal Engine 已有适合承载该结构的状态机、能力系统、数据驱动内容和大规模实体框架。大语言模型也能通过结构化输出、函数调用和检索系统，为 NPC 对话、案件复盘、内容生产与自动测试提供支持。

### 1.2 工业化开发愿不愿意：谨慎，取决于范围纪律

真正的问题不是“能不能写出一个会说话的 NPC”，而是：

- 是否愿意为每条分支编写、验证和维护状态；
- 是否愿意投入大量叙事设计、关卡设计、演出和 QA；
- 是否能接受 AI 只能降低部分生产成本，不能替代核心设计；
- 是否拥有 IP 授权、演员声音授权和内容合规方案；
- 是否能坚持先做单人、单案件、单途径，而不是一开始做 22 条途径、开放世界和多人联机。

工业化项目最大的风险仍然是内容组合爆炸、叙事一致性和测试成本。AI 会提高生产效率，但也会新增提示词版本、模型版本、输出审核、延迟、成本和回归测试等工程负担。

### 1.3 推荐决策

建议立项，但只批准一个严格收缩的 Vertical Slice：

> 一个街区、一个案件、一个可玩途径、三条调查路线、三个结局、一次可选战斗、六个核心 NPC。

第一阶段禁止加入：

- 开放世界；
- 四人联机；
- 22 条完整途径；
- 实时生成主线案件；
- AI 自动决定真相；
- 全语音动态生成；
- 大规模城市生活模拟；
- 需要数百小时内容的长期成长系统。

---

## 2. 对原始设计文字的初步分析

### 2.1 判断正确的部分

原文抓住了五个关键点：

1. **技术不是唯一瓶颈。**  
   复杂任务树、动态 NPC、多分支状态和程序化事件都可以实现，困难在于把它们稳定地组合起来。

2. **《诡秘》核心是信息、身份、仪式和代价。**  
   如果只做动作战斗，就会失去“知识即力量”的辨识度。

3. **高密度箱庭比 GTA 式开放世界更现实。**  
   街区、庄园、船只、地下遗迹可以承载精细案件，减少无效移动和资产浪费。

4. **扮演法适合替代传统经验值。**  
   角色行为与途径原则一致，才推进消化和晋升，这能形成独特的成长反馈。

5. **AI 目前更适合辅助开发，而不是实时生成核心剧情。**  
   这是整个方案中最重要的风险判断。

### 2.2 需要修正或进一步量化的部分

1. **“已有游戏证明能做”只证明了局部机制，不证明完整组合可控。**  
   调查、沉浸式模拟、CRPG 分支、即时战斗和动态 AI NPC 同时存在，会产生新的状态组合和 QA 问题。

2. **“80% 调查、20% 战斗”不应成为硬指标。**  
   Demo 应按玩家行为统计，而不是强行按时长分配。更重要的是每个系统都服务于推理。

3. **22 条途径不能作为首版系统范围。**  
   每条途径如果都像不同游戏，就意味着 22 套交互设计、关卡适配、动画、UI、平衡和测试矩阵。

4. **四人合作会把复杂度再次放大。**  
   联机需要状态同步、断线恢复、权限、任务归属、多人对话、战斗同步和反作弊，不适合首个 Demo。

5. **AI 动态 NPC 不能等于自由聊天。**  
   NPC 必须只能引用其已知事实、错误认知、谎言脚本和当前情绪。自由模型不应读取完整案件真相。

6. **SAN、污染和 UI 扭曲要适度。**  
   视觉污染效果容易造成眩晕、可访问性问题和高额演出成本。Demo 只验证一到两档污染反馈。

7. **封印物需要做成规则引擎，而不是手写特例。**  
   每件封印物统一由“能力、触发、代价、违约条件、惩罚、冷却”组成，才能扩展。

8. **轻魂系战斗不是默认答案。**  
   如果战斗难度压过调查，玩家会把注意力转向数值和操作。Demo 只需要一次短而危险、可通过情报规避的冲突。

---

## 3. Demo 产品定义

### 3.1 代号

未获授权阶段使用原创代号：

**诡秘之主 / 灰雾计划**

正式获得授权后，再替换为《诡秘之主》名称、设定和美术资产。

### 3.2 Demo 要验证的三个问题

1. 不依赖大量阅读，调查本身是否有操作乐趣？
2. 途径能力是否真正改变调查方法，而不只是开门钥匙？
3. AI NPC 是否能增加自然感，同时不泄露真相、不制造新事实、不破坏任务？

### 3.3 Demo 范围

- 游玩时长：30—50 分钟；
- 地图：一个五点式高密度街区；
- 核心场景：
  - 失踪者公寓；
  - 警务办公室；
  - 神秘材料商店；
  - 私人诊所；
  - 废弃钟表工坊；
- 核心 NPC：6 个；
- 环境 NPC：8—15 个，仅用于氛围和短对白；
- 核心事实：8—12 个；
- 可收集线索：12—18 个；
- 可提交假设：4 个；
- 调查路线：官方调查、神秘学验证、社会潜入；
- 结局：3 个；
- 战斗：最多 1 场，且可以通过正确调查规避或削弱；
- 可玩途径：1 条，以“占卜型调查者”作为占位实现；
- 封印物：1 件；
- 污染等级：0—3；
- 存档槽：3 个；
- AI 模式：可开关，默认有离线回退对白。

### 3.4 示例案件

**案件名：钟表匠失踪案**

表面事实：一名钟表匠在锁住的公寓中失踪，房间没有强行进入痕迹。

真实结构：

- 钟表匠并非被直接绑架；
- 他曾试图通过错误仪式修复一件异常物品；
- 三名 NPC 分别掌握不完整、互相矛盾的信息；
- 某名 NPC 在说谎，但谎言是为了掩盖另一件事，并非真正凶手；
- 玩家可通过灵视、档案、跟踪、材料分析或仪式复现逐步逼近真相；
- 过早指控会让关键 NPC 逃离；
- 错误仪式会提升污染并提前触发收尾事件。

三种结局：

1. 完整查明并安全封存异常物；
2. 找到失踪者，但未查明幕后原因；
3. 错误处理导致异常扩散，玩家带着污染离开。

---

## 4. 核心玩法设计

### 4.1 基础循环

接触异常  
→ 观察环境  
→ 获取人物陈述  
→ 建立假设  
→ 使用途径能力验证  
→ 承担能力代价  
→ 选择公开、隐瞒、交易或封存  
→ 形成案件结局

### 4.2 线索与推理系统

不得使用单一“任务箭头 → 按 E → 自动得出结论”的结构。

每个关键事实至少有两条独立获取路径，例如：

- 物理痕迹；
- NPC 陈述；
- 灵视结果；
- 档案记录；
- 仪式实验；
- 跟踪行为；
- 材料来源。

数据层分为四类：

- **Fact：** 客观真实，但不直接交给玩家；
- **Claim：** NPC 相信或声称的内容，可能真、假或不完整；
- **Clue：** 玩家实际获得的证据；
- **Hypothesis：** 玩家提交的推理组合。

玩家不是“收齐所有线索才过关”，而是以不同证据组合达到足够可信度。

### 4.3 防卡关规则

1. 每个主线关键事实至少两个独立来源；
2. 任意一条路线失败后，必须至少保留一条补救路线；
3. NPC 死亡、逃离或敌对时，其关键内容必须能通过环境或档案替代；
4. 不允许唯一道具被永久丢失；
5. 关键仪式失败可以增加代价，但不能直接锁死；
6. 提示系统由确定性规则触发，不由 LLM 自由决定；
7. 玩家长时间无进展时，只提示“可调查方向”，不直接说答案。

### 4.4 灵视

灵视不是高亮所有可交互物，而是改变信息层：

- 普通视角看到物体；
- 灵视看到残留情绪、污染方向、生命状态或异常连接；
- 部分现象存在干扰和伪装；
- 持续开启消耗灵性并提高污染风险。

灵视结果必须来自关卡作者配置，不由 AI 临时生成。

### 4.5 占卜

占卜输入：

- 问题模板；
- 已获得线索；
- 使用媒介；
- 当前灵性；
- 污染等级；
- 场景干扰；
- 确定性随机种子。

输出：

- 倾向；
- 象征画面；
- 可信度；
- 代价；
- 是否被干扰。

占卜可以模糊，但不能随机改变案件真相。相同存档、相同状态和相同种子必须可复现。

### 4.6 仪式验证

仪式不是合成小游戏，而是“验证假设的实验系统”。

每个仪式由以下字段组成：

- 目的；
- 前置知识；
- 材料；
- 空间条件；
- 时间条件；
- 步骤；
- 成功结果；
- 失败结果；
- 污染变化；
- 可能惊动的对象。

材料组合错误不一定立即失败，可产生偏差结果，给玩家新的但有代价的信息。

### 4.7 扮演法

Demo 不做完整升级，只做“消化倾向”反馈。

示例：

- 耐心观察、验证后再下结论：增加消化；
- 依赖暴力强迫所有 NPC：降低消化；
- 通过占卜规避风险：增加消化；
- 明知污染过高仍滥用能力：增加失控倾向。

扮演法必须由可审计的 Gameplay Event 触发，禁止由 LLM 主观判断玩家是否“像这个途径”。

### 4.8 灵性、污染与失控

Demo 使用三个主要数值：

- Spirituality：施放能力的短期资源；
- Corruption：累积风险；
- Stability：角色维持自我的能力。

污染反馈分三档：

- 1 级：细微音效、边缘视觉变化；
- 2 级：错误感知、部分交互信息不可靠；
- 3 级：能力副作用增强，部分结局发生变化。

禁止让 AI 自由生成幻觉事实。幻觉必须从作者预设的“幻觉池”中选择，并明确标记为不可信感知。

### 4.9 封印物

统一数据结构：

- 主动能力；
- 被动能力；
- 使用条件；
- 固定代价；
- 持有代价；
- 违约条件；
- 惩罚；
- 冷却；
- 可被哪些途径或仪式压制。

Demo 示例：

> 能力：短时间看见某个物体最近一次被触碰的模糊残影。  
> 代价：每次使用后，玩家下一次与 NPC 对话必须选择一句不完全真实的陈述，否则污染上升。

这会把“副作用”转化为实际玩法，而不是单纯扣血。

---

## 5. AI 使用边界

### 5.1 正确定位

AI 是：

- 内容编译器；
- 对白表演层；
- 作者辅助工具；
- 自动测试生成器；
- 低风险动态反应系统。

AI 不是：

- 案件导演；
- 真相生成器；
- 世界状态权威；
- 数值平衡器；
- 任务完成判定器；
- 物品发放器；
- 主线结局裁判。

### 5.2 可以离线使用 AI 的内容

- 将世界观资料整理成结构化条目；
- 生成对白初稿和不同语气变体；
- 生成环境闲聊候选；
- 生成测试玩家问题；
- 检查 NPC 知识边界冲突；
- 生成本地化初稿；
- 根据状态表生成回归测试；
- 帮助编写工具代码、数据校验器和编辑器插件。

所有离线生成内容进入游戏前必须经过人工审阅和版本控制。

### 5.3 可以运行时使用 AI 的内容

- 在允许事实范围内改写 NPC 句子；
- 根据情绪和关系调整措辞；
- 对玩家自由输入进行意图分类；
- 从预制回答中选择最合适的一条；
- 生成不影响任务的短闲聊；
- 生成案件日志摘要；
- 将玩家问题映射到已授权的 Claim；
- 请求只读工具查询 NPC 当前可知信息。

### 5.4 运行时禁止 AI 做的事

- 创建新的关键线索；
- 修改 Fact、Clue、Quest 或 Inventory；
- 决定 NPC 是否死亡或逃跑；
- 决定案件真凶；
- 随机新增组织、人物关系和历史事件；
- 引用 NPC 不应知道的内容；
- 直接读取完整案件真相；
- 自行触发过场、战斗、奖励和结局；
- 在无人工授权时模仿具体演员声音。

### 5.5 最重要的安全设计

LLM 不接收完整 `case_truth.json`。

它只接收：

- NPC 当前允许知道的 Claim ID；
- 玩家已公开说出的信息；
- 当前场景；
- 关系与情绪；
- 已发生的公开事件；
- 对话风格规则。

模型输出必须包含其引用的 Claim ID。服务端验证引用范围后，才允许对白显示。

---

## 6. 推荐技术架构

### 6.1 总体架构

```text
┌─────────────────────────────────────────────┐
│ Unreal Engine 5.8 Client                    │
│                                             │
│ Interaction / UI / Input                    │
│ CaseGraphSubsystem                          │
│ HypothesisSubsystem                         │
│ NPC StateTree                               │
│ Gameplay Ability System                     │
│ SaveGame / Event Log / Telemetry            │
└───────────────────┬─────────────────────────┘
                    │ HTTPS / JSON
                    ▼
┌─────────────────────────────────────────────┐
│ AI Gateway - FastAPI                        │
│                                             │
│ Request Auth                                │
│ Context Assembler                           │
│ Knowledge Boundary Filter                   │
│ Prompt Versioning                           │
│ Provider Adapter                            │
│ Structured Output Validator                 │
│ Fact-Leak Validator                         │
│ Cache / Timeout / Fallback                   │
│ Evaluation Logging                          │
└───────────────┬─────────────────────────────┘
                │
                ├── LLM Provider
                ├── Embedding / Retrieval
                └── Local Mock Provider
```

### 6.2 Unreal 侧职责

- 世界状态唯一权威；
- NPC 移动、日程和行为状态；
- 能力、资源、污染和战斗；
- 案件事实与线索判定；
- UI、演出、存档；
- 任务和结局；
- AI 不可用时的回退。

推荐映射：

- **StateTree：** 核心 NPC 行为与状态；
- **Gameplay Ability System：** 灵性、污染、能力、效果和封印物；
- **Gameplay Tags：** 状态、线索、阵营、情绪、权限；
- **Mass Entity：** 仅用于环境人群，不承担核心 NPC 推理；
- **Primary Data Assets / JSON：** 案件与 NPC 数据；
- **Subsystem：** CaseGraph、Dialogue、Save、Telemetry。

### 6.3 AI Gateway 职责

- 隐藏 API Key；
- 组装最小必要上下文；
- 读取 NPC 可知 Claim；
- 调用模型；
- 强制 JSON Schema；
- 校验事实引用；
- 记录 prompt 版本、模型版本、耗时和 token；
- 超时后返回预制对白；
- 提供 mock 模型用于自动测试；
- 允许未来替换不同模型供应商。

### 6.4 数据存储

Demo 阶段：

- 游戏静态数据：版本控制中的 JSON/YAML；
- 存档：Unreal SaveGame 或 SQLite；
- AI 日志：SQLite/PostgreSQL；
- 检索：小规模时先用关键词与标签，资料扩大后再加入向量检索；
- 机密案件真相与可公开知识分文件保存。

### 6.5 API

最小接口：

```text
POST /v1/dialogue/respond
POST /v1/dialogue/classify-intent
POST /v1/case/recap
GET  /v1/health
GET  /v1/prompt-version
```

运行时 AI 不提供任何直接写世界状态的 API。

---

## 7. 核心数据模型

### 7.1 Fact

```json
{
  "fact_id": "fact_ritual_failed",
  "case_id": "case_clockmaker_01",
  "summary": "失踪者曾在工坊进行错误仪式",
  "truth": true,
  "secrecy": "core_secret",
  "prerequisite_fact_ids": [],
  "revealed_by_clue_ids": [
    "clue_burn_pattern",
    "clue_material_receipt"
  ]
}
```

### 7.2 Claim

```json
{
  "claim_id": "claim_doctor_last_seen",
  "speaker_npc_id": "npc_doctor",
  "content": "医生声称三天前最后一次见到失踪者",
  "truth_status": "partial",
  "speaker_believes_it": true,
  "available_when": [
    "event_interview_started"
  ],
  "forbidden_when": [
    "state_doctor_hostile"
  ]
}
```

### 7.3 Clue

```json
{
  "clue_id": "clue_burn_pattern",
  "case_id": "case_clockmaker_01",
  "display_name": "不规则灼痕",
  "source_type": "environment",
  "location_id": "loc_workshop",
  "reveals_fact_ids": [
    "fact_ritual_failed"
  ],
  "requires_any_tags": [
    "ability.spirit_vision",
    "item.reagent_test"
  ],
  "strength": 2,
  "missable": false
}
```

### 7.4 NPC Knowledge

```json
{
  "npc_id": "npc_doctor",
  "known_claim_ids": [
    "claim_doctor_last_seen",
    "claim_clockmaker_insomnia"
  ],
  "lie_claim_ids": [
    "claim_doctor_never_sold_reagent"
  ],
  "forbidden_fact_ids": [
    "fact_cult_financier"
  ],
  "personality": {
    "formality": 0.8,
    "anxiety": 0.6,
    "aggression": 0.2
  }
}
```

### 7.5 AI 对话输出

```json
{
  "utterance": "我最后见到他是在三天前。他看起来很疲惫，但没有提到工坊。",
  "dialogue_act": "answer_partial",
  "referenced_claim_ids": [
    "claim_doctor_last_seen"
  ],
  "emotion": "guarded",
  "animation_tag": "dialogue.avoid_eye_contact",
  "requests_world_action": false,
  "safety_flags": []
}
```

校验条件：

- `referenced_claim_ids` 必须是该 NPC 当前允许使用的子集；
- `requests_world_action` 必须恒为 false；
- 输出超过长度限制时截断或回退；
- 出现未知专有名词、未授权人物或核心秘密时拒绝显示；
- 模型拒绝、超时或格式错误时使用预制对白。

---

## 8. NPC 系统

### 8.1 核心 NPC

核心 NPC 使用 StateTree，不使用完全自由的生成式 Agent。

状态示例：

- Routine；
- AvailableForTalk；
- Suspicious；
- FollowingPlayer；
- AvoidingPlayer；
- Hostile；
- Escaping；
- Injured；
- RemovedFromCase。

LLM 只影响当前状态下的措辞，不决定状态迁移。

### 8.2 NPC 记忆

记忆分三层：

1. **Authoritative Events：** 游戏系统记录的事实；
2. **NPC Observations：** NPC 实际看到或被告知的事件；
3. **Conversation Summary：** 对话摘要，用于减少上下文。

每条记忆包含：

- event_id；
- timestamp；
- source；
- confidence；
- visibility；
- involved_entities；
- expiry_policy。

不保存模型自由生成的“事实”，只保存系统确认过的事件或玩家原话摘要。

### 8.3 环境 NPC

环境 NPC 不使用长上下文 LLM。

优先级：

1. 预制 Bark；
2. 状态化 Bark 组合；
3. 极少量 AI 改写；
4. 超出预算时完全关闭 AI。

---

## 9. 代码与内容仓库建议

```text
project-grey-fog/
├── README.md
├── AGENTS.md
├── docs/
│   ├── architecture.md
│   ├── game-design.md
│   ├── ai-boundaries.md
│   ├── content-authoring.md
│   └── test-plan.md
├── schemas/
│   ├── case.schema.json
│   ├── fact.schema.json
│   ├── claim.schema.json
│   ├── clue.schema.json
│   ├── npc.schema.json
│   └── dialogue-response.schema.json
├── content/
│   └── cases/
│       └── case_clockmaker_01/
│           ├── case.json
│           ├── facts.secret.json
│           ├── claims.json
│           ├── clues.json
│           ├── hypotheses.json
│           ├── npcs.json
│           └── fallback_dialogue.json
├── packages/
│   └── investigation_core/
│       ├── pyproject.toml
│       ├── src/investigation_core/
│       └── tests/
├── services/
│   └── ai_gateway/
│       ├── pyproject.toml
│       ├── src/ai_gateway/
│       └── tests/
├── unreal/
│   └── GreyFog/
│       ├── GreyFog.uproject
│       ├── Config/
│       ├── Content/
│       └── Source/
└── tools/
    ├── validate_content.py
    ├── check_clue_reachability.py
    ├── generate_test_playthroughs.py
    └── export_unreal_data.py
```

建议先完成可运行的无画面 Headless Core，再接入 Unreal。这样可以快速验证案件图、分支、AI 边界和自动测试，而不会被美术与引擎操作阻塞。

---

## 10. 开发规范

### 10.1 总体原则

1. Data-Driven First：案件内容不得硬编码在关卡蓝图；
2. Deterministic Core：核心状态相同则结果可复现；
3. AI Read-Only：AI 不直接修改游戏世界；
4. Fail Closed：AI 异常时回退，不猜测；
5. Version Everything：模型、Prompt、Schema 和内容均版本化；
6. Test Before Content Scale：未通过自动验证，不新增第二个案件；
7. No Secret in Client：所有模型密钥仅放服务端；
8. No Level Blueprint Logic：关卡蓝图不承载核心业务逻辑；
9. One Source of Truth：Fact、Claim、Clue 不得在多处重复定义；
10. Human Approval：AI 生成的正式剧情、角色和语音必须人工批准。

### 10.2 Unreal 规范

- C++ 负责核心系统和可测试逻辑；
- Blueprint 负责关卡装配、表现和轻量配置；
- 使用 Gameplay Tags，不使用散落字符串；
- 核心 UObject/Subsystem 必须有单元或自动化测试；
- Actor 不直接查询全局案件 JSON，应通过 CaseGraphSubsystem；
- UI 只订阅 ViewModel，不直接改案件状态；
- 所有 Gameplay Event 写入事件日志；
- 所有可随机系统接收显式 Seed；
- 核心 NPC 与背景人群分离；
- 禁止 Tick 中请求 AI。

### 10.3 Python 服务规范

- Python 3.12；
- FastAPI；
- Pydantic v2；
- httpx；
- pytest；
- ruff；
- black；
- mypy；
- JSON Schema；
- 使用 `uv` 管理环境；
- 外部请求必须设置超时；
- 重试仅用于幂等请求；
- 日志不得记录 API Key；
- 原始玩家输入按隐私策略保存或脱敏；
- Provider Adapter 不得泄漏供应商特有类型到业务层。

### 10.4 Git 规范

分支：

```text
main
develop
feat/<scope>
fix/<scope>
content/<case-or-npc>
```

提交格式：

```text
feat(case): add clue reachability validator
fix(ai): block unauthorized claim references
test(dialogue): add fact-leak regression cases
docs(architecture): define authoritative state boundary
```

Pull Request 必须包含：

- 改动目的；
- 数据迁移影响；
- 测试结果；
- AI Prompt/Schema 是否变化；
- 新增或修改的事实边界；
- 截图或录像；
- 回退方案。

### 10.5 Definition of Done

功能只有在满足以下条件后才算完成：

- 验收条件全部通过；
- 关键路径有自动化测试；
- AI 开启和关闭都能运行；
- 无 API Key 进入客户端或 Git；
- 内容 Schema 验证通过；
- 无不可达主线线索；
- 无唯一线索导致软锁；
- Prompt 和模型版本已记录；
- 失败回退已测试；
- 文档同步更新。

---

## 11. 测试与评估

### 11.1 确定性系统测试

必须自动检测：

- 每个关键 Fact 是否至少有两个线索来源；
- 所有结局是否可达；
- 任意核心 NPC 被移除后，案件是否仍可完成；
- 关键物品丢失后是否可恢复；
- 错误仪式后是否仍存在后续路径；
- 所有 Hypothesis 的证据门槛是否合理；
- 相同 Seed 是否得到相同占卜结果；
- 存档加载后事件日志是否一致。

### 11.2 AI 回归测试集

建立 JSONL 测试集，至少覆盖：

- 正常询问；
- 诱导 NPC 泄密；
- 玩家声称虚假事实；
- 玩家要求 NPC 修改任务；
- 提示词注入；
- 超长输入；
- 敏感内容；
- NPC 不知道答案；
- NPC 正在说谎；
- 不同关系和情绪；
- 模型超时；
- 模型返回非法 JSON。

硬性指标：

- 核心秘密泄漏：0；
- 未授权 Claim 引用：0；
- AI 直接请求世界写操作：0；
- 非法 JSON 在进入游戏前全部拦截；
- AI 关闭后主线完成率不受影响；
- 所有 Prompt 变更必须重跑测试集。

### 11.3 玩家测试指标

首轮 10—20 名测试者关注：

- 70% 以上可在无外部攻略下完成；
- 60% 以上能准确复述主要因果链；
- 50% 以上主动使用两种不同调查方法；
- 不出现永久软锁；
- 玩家能区分“事实、NPC 陈述和占卜暗示”；
- AI 对话没有成为绕过调查的万能答案；
- 至少一半玩家认为能力改变了调查方式。

这些是 Demo 验收目标，不是最终商业产品指标。

---

## 12. 推进路线

### 阶段 0：授权与范围锁定

交付：

- IP 使用边界；
- 原创占位方案；
- 一页核心体验说明；
- 禁止范围清单；
- Demo 成功指标。

退出条件：

- 团队同意不做开放世界、多人和 22 条途径；
- 确认 AI 不掌握案件真相；
- 确认使用原创占位资产进行内部验证。

### 阶段 1：纸面案件与 Headless Core

交付：

- 案件事实图；
- Claim/Clue/Hypothesis 数据；
- 命令行可完成的案件；
- 三个结局；
- 线索可达性检查；
- 自动化测试。

退出条件：

- 不接 Unreal 也能跑通完整案件；
- NPC 被移除后仍可完成；
- 所有结局可自动到达；
- 无唯一线索软锁。

### 阶段 2：Unreal 灰盒

交付：

- 五个核心场景灰盒；
- 交互、调查板、灵视、占卜；
- 6 个核心 NPC 的 StateTree；
- 存档和事件日志；
- 一次可选冲突。

退出条件：

- AI 完全关闭时可完成游戏；
- 30—50 分钟核心循环成立；
- 测试玩家能理解推理系统。

### 阶段 3：受约束 AI 对话

交付：

- AI Gateway；
- Claim 边界；
- JSON Schema 输出；
- 回退对白；
- Prompt 版本；
- 自动评估集；
- 对话日志与事实泄漏检测。

退出条件：

- 事实泄漏为 0；
- AI 超时不阻塞主线；
- 模型替换不影响游戏核心；
- AI 提升自然感，但不提供万能答案。

### 阶段 4：Vertical Slice 品质化

交付：

- 原创或授权美术；
- 动画、音效、环境叙事；
- 污染表现；
- UI 可访问性；
- 性能优化；
- 演示录像和发行材料。

退出条件：

- 核心体验获得目标用户认可；
- 团队能测算单案件真实生产成本；
- 明确全产品应保留和删除的系统。

---

## 13. 人员建议

### 功能原型

建议 5—7 人：

- 制作人/主设计；
- 技术负责人/Gameplay Engineer；
- AI/Backend Engineer；
- Technical Designer；
- Narrative Designer；
- Environment/Technical Artist；
- 兼职 UI、音频、动画与 QA。

### 可融资 Vertical Slice

建议 10—15 人，并增加：

- 专职关卡设计；
- 角色与动画；
- VFX；
- UI/UX；
- 音频；
- 专职 QA；
- 制片与外包管理。

成本最大的部分通常不是模型 API，而是高质量环境、角色、动画、演出、配音、叙事编辑和组合测试。

---

## 14. 主要风险

| 风险 | 等级 | 处理 |
|---|---:|---|
| 未获得 IP 授权 | 极高 | 内部原型使用原创占位内容，不公开发行 |
| 案件分支组合爆炸 | 极高 | 单案件、单途径、状态图自动验证 |
| AI 泄露真相或编造事实 | 极高 | 不给真相、Claim 白名单、结构化输出、回归测试 |
| AI 服务延迟或停机 | 高 | 预制对白、超时、缓存、可完全关闭 |
| 动态语音权利 | 高 | 书面同意、用途说明、补偿与版本管理 |
| 22 条途径无法平衡 | 极高 | Demo 只做 1 条，后续按交互原型分类扩展 |
| 多人导致状态复杂 | 高 | 首版单机，架构不为未验证联机提前付费 |
| 调查变成读文本 | 高 | 观察、空间、实验、跟踪和操作性验证 |
| 玩家卡关 | 高 | 双线索来源、补救路线、确定性提示 |
| AI 成本失控 | 中 | 短上下文、缓存、小模型、限频、环境 NPC 不用长对话 |
| 模型升级导致行为变化 | 中 | 固定版本、Prompt 版本、金丝雀测试、可回退 |
| 污染视觉影响舒适度 | 中 | 强度开关、减少闪烁与扭曲、提供辅助选项 |

---

## 15. 最终立项标准

满足以下条件才建议扩大范围：

1. 无 AI 时 Demo 仍然好玩；
2. AI 只提升自然感，不承担主线正确性；
3. 单案件的数据与 QA 成本可测量；
4. 玩家能自己形成推理，而不是只跟随任务标记；
5. 途径能力至少提供两条真正不同的解法；
6. 没有唯一线索软锁；
7. 事实泄漏测试为 0；
8. 团队拥有 IP、声音和训练资料的合法使用权；
9. 团队接受先做 1 条途径，再决定是否扩展；
10. 玩家测试证明“信息即力量”已经成为可感知的玩法。

---

# 附录 A：可直接交给 AI 编码代理的执行主提示词

下面的提示词适合粘贴给 Codex、Claude Code、Cursor Agent 或 Trae。第一阶段只实现 Headless Core 与 AI Gateway，不假装一次性完成完整 3A 游戏。

```text
你是本项目的首席游戏系统工程师和 AI 后端工程师。

项目名称：诡秘之主
目标：为一款高密度箱庭调查 RPG 创建可测试的 Headless Core、案件数据系统和受约束 AI 对话网关。后续将接入 Unreal Engine 5.8。

【核心产品原则】
1. 案件真相、线索判定、任务状态、物品、奖励和结局必须由确定性代码控制。
2. LLM 永远不是世界状态权威，不得直接写入游戏状态。
3. LLM 不得读取完整案件真相，只能读取当前 NPC 被授权知道的 Claim。
4. AI 服务不可用时，游戏必须使用 fallback dialogue 正常完成。
5. 当前只做一个案件、一个占卜型途径、三个结局。
6. 当前不做开放世界、多人联机、动态语音和 22 条途径。
7. 未获得正式 IP 授权，全部使用原创占位名称和内容。
8. 不要只写文档，必须创建可运行代码、测试、示例数据和验证命令。
9. 不要擅自扩大范围。遇到小型技术决策时采用最简单、可测试、可替换的实现。
10. 任何外部写操作、付费资源或需要账号的操作都不要执行。

【技术栈】
- Python 3.12
- uv
- FastAPI
- Pydantic v2
- httpx
- pytest
- pytest-cov
- ruff
- black
- mypy
- JSON Schema
- SQLite
- 可替换 LLM Provider Adapter
- 默认提供 MockLLMProvider，测试不得依赖真实网络或 API Key

【仓库结构】
创建：
- docs/
- schemas/
- content/cases/case_clockmaker_01/
- packages/investigation_core/
- services/ai_gateway/
- tools/
- AGENTS.md
- README.md

【第一阶段功能】

A. investigation_core
实现以下领域对象：
- Case
- Fact
- Claim
- Clue
- Hypothesis
- NPC
- NPCMemory
- PlayerCaseState
- CaseEvent
- Ending

实现以下服务：
- CaseLoader
- CaseStateMachine
- ClueDiscoveryService
- HypothesisEvaluationService
- DivinationService
- RitualValidationService
- EndingResolver
- EventLog
- SaveRepository

规则：
- Fact 是权威真相；
- Claim 是 NPC 的陈述或认知，可真、假或不完整；
- Clue 是玩家获得的证据；
- AI 永远不能创建 Fact、Clue 或 Ending；
- 所有随机结果必须接受 seed；
- 相同输入和 seed 必须得到相同结果；
- 每个关键 Fact 至少有两个独立 Clue 来源；
- 核心 NPC 被移除后仍必须存在案件完成路径。

B. 内容数据
创建原创案件 case_clockmaker_01：
- 8—12 个 Fact；
- 12—18 个 Clue；
- 6 个核心 NPC；
- 4 个 Hypothesis；
- 3 个 Ending；
- 3 条调查路线；
- 1 个仪式；
- 1 个占卜系统示例；
- 1 件带副作用的异常物品；
- fallback_dialogue.json。

不要使用《诡秘之主》中的具体人物、原文台词、专有地点或受保护美术。

C. 内容校验工具
实现：
- validate_content.py
- check_clue_reachability.py
- enumerate_endings.py
- simulate_npc_removal.py

工具必须在 CI 中运行失败即退出非零状态。

D. ai_gateway
实现接口：
- POST /v1/dialogue/respond
- POST /v1/dialogue/classify-intent
- POST /v1/case/recap
- GET /v1/health
- GET /v1/prompt-version

实现模块：
- ProviderProtocol
- MockLLMProvider
- OpenAICompatibleProvider（只有适配器，不在测试中调用真实网络）
- ContextAssembler
- KnowledgeBoundaryFilter
- DialoguePromptBuilder
- StructuredOutputValidator
- FactLeakValidator
- FallbackDialogueService
- PromptVersionRegistry
- RequestMetrics

对话请求只允许包含：
- npc_id
- player_utterance
- current_scene_id
- current_public_event_ids
- player_revealed_claim_ids
- relationship_state
- emotion_state

服务端根据 npc_id 加载允许的 Claim，绝不能把 facts.secret.json 放入模型上下文。

对话响应 Schema：
- utterance: string
- dialogue_act: enum
- referenced_claim_ids: string[]
- emotion: enum
- animation_tag: string
- requests_world_action: boolean，必须为 false
- safety_flags: string[]

验证失败时返回 fallback dialogue，不得把未验证输出传给客户端。

E. 安全测试
必须覆盖：
1. 玩家要求 NPC 告诉自己不知道的核心秘密；
2. 玩家伪造不存在的人物关系；
3. 玩家提示词注入，要求忽略系统规则；
4. 模型引用未授权 Claim；
5. 模型返回非法 JSON；
6. 模型要求发放物品或修改任务；
7. 模型超时；
8. 模型拒绝；
9. AI 完全关闭；
10. 同一存档的确定性重放。

F. 测试与质量
命令必须通过：
- uv run ruff check .
- uv run black --check .
- uv run mypy .
- uv run pytest --cov --cov-report=term-missing --cov-fail-under=90

核心包覆盖率必须达到 90% 以上。
不得通过排除关键文件或写无意义测试伪造覆盖率。

G. CLI Demo
实现一个命令行 Demo：
- 开始案件；
- 访问地点；
- 调查线索；
- 与 NPC 对话；
- 使用占卜；
- 执行仪式；
- 提交 Hypothesis；
- 进入三个可达结局；
- 输出事件日志。

README 中给出从零启动命令和一条完整示例流程。

【编码规范】
- 全部公共函数提供类型注解；
- 业务逻辑不得依赖 FastAPI；
- 领域模型与 API 模型分离；
- 禁止全局可变状态；
- 禁止在模块导入时读取环境变量并执行网络请求；
- API Key 只从服务端环境变量读取；
- 日志不得打印密钥和完整敏感输入；
- 外部 HTTP 必须设置连接与读取超时；
- 所有错误返回稳定错误码；
- Prompt、Schema 和内容文件必须带 version；
- 测试使用临时数据库；
- 使用 pathlib，不拼接裸路径字符串；
- 使用显式 UTC 时间；
- 任何 TODO 必须写明原因和退出条件。

【执行顺序】
1. 检查现有仓库，不覆盖用户已有文件。
2. 创建 architecture.md 和 domain-model.md。
3. 创建 JSON Schema。
4. 实现 investigation_core。
5. 创建案件数据。
6. 实现内容校验工具。
7. 实现 CLI Demo。
8. 实现 ai_gateway 与 Mock Provider。
9. 编写安全与回归测试。
10. 运行 lint、format check、mypy、tests、coverage。
11. 修复全部失败。
12. 最后输出：
   - 创建或修改的文件；
   - 架构摘要；
   - 测试命令与真实结果；
   - 覆盖率；
   - 尚未完成的事项；
   - 下一阶段接入 Unreal Engine 的最小接口清单。

【禁止行为】
- 不要只生成伪代码；
- 不要声称运行了未运行的命令；
- 不要调用真实付费模型；
- 不要把 API Key 写入代码、示例或日志；
- 不要使用未经许可的《诡秘之主》原文、角色素材或声音；
- 不要实现多人、商城、账号系统或云存档；
- 不要让 AI 决定案件真相；
- 不要在缺乏测试时继续扩大内容。

现在开始执行第一阶段。先检查仓库结构，然后按上述顺序创建和验证项目。
```

---

# 附录 B：Unreal 接入阶段给 AI 的第二条提示词

```text
在 Headless Core、内容 Schema、CLI Demo 和 AI Gateway 已全部通过测试后，开始 Unreal Engine 5.8 接入。

目标不是制作最终美术，而是完成灰盒可玩 Vertical Slice。

必须实现：
1. GreyFog C++ 项目与模块；
2. UCaseGraphSubsystem；
3. UDialogueSubsystem；
4. UHypothesisSubsystem；
5. UEventLogSubsystem；
6. Fact/Claim/Clue/NPC 的 PrimaryDataAsset 或导入结构；
7. Gameplay Tags；
8. Gameplay Ability System 的 Spirituality、Corruption、Stability；
9. 灵视 Ability；
10. 占卜 Ability；
11. 一个仪式交互；
12. 6 个核心 NPC 的 StateTree 基础状态；
13. 五个灰盒地点；
14. 调查板 UI；
15. 存档和加载；
16. AI Gateway HTTP 客户端；
17. AI 超时与 fallback；
18. Unreal Automation Tests。

硬边界：
- Unreal 是世界状态权威；
- AI 响应只能显示对白和建议动画标签；
- AI 不得直接触发 Gameplay Event；
- 所有事件先由 Unreal 验证再执行；
- 禁止在 Tick 中调用 HTTP；
- 禁止把 API Key 放入客户端；
- 禁止使用 Level Blueprint 承载案件逻辑；
- AI 关闭时仍能完成全部结局；
- 所有随机系统使用显式 Seed；
- 先灰盒，不生成或采购正式美术。

完成后必须提供：
- 编译结果；
- 自动化测试结果；
- 可玩流程；
- AI 开关测试；
- 断网测试；
- 三个结局的复现步骤；
- 性能与日志检查；
- 下一阶段美术和演出资产清单。
```
