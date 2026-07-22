# AI 边界 — Project Grey Fog

本文档明确定义 AI（LLM）在本项目中的职责、权限和硬性约束。这是所有系统设计、测试和审查的核心参考文档。

---

## 根本原则

> **LLM 不是世界状态权威，也不是案件导演。**

AI 是受约束的对话表演层，所有影响游戏状态的决策必须由确定性代码控制。

---

## AI 职责（允许做的事）

### 运行时（Runtime）

| 职责 | 说明 |
|---|---|
| 在允许事实范围内改写 NPC 句子 | 用不同措辞表达已授权的 Claim |
| 根据情绪和关系调整措辞 | 基于 NPC 的 personality 参数改变语气 |
| 对玩家自由输入进行意图分类 | 如"询问案情"、"闲聊"、"威胁" |
| 从预制回答中选择最合适的一条 | 基于当前上下文排序 fallback 候选 |
| 生成不影响任务的短闲聊 | 环境 NPC 的一两句天气/闲聊 |
| 生成案件日志摘要 | 仅基于已发生的系统和玩家事件 |
| 将玩家问题映射到已授权的 Claim | 匹配玩家意图与已知 Claim |

### 离线（离线工具/辅助开发）

| 职责 | 说明 |
|---|---|
| 生成对白初稿和语气变体 | 作者审阅后入库 |
| 生成环境闲聊候选 | 作者选择后入库 |
| 检查 NPC 知识边界冲突 | 比对 known_claim_ids 与 forbidden_fact_ids |
| 生成测试玩家问题 | 扩展安全测试集 |
| 帮助编写工具代码 | 如数据校验器、编辑器插件 |

---

## AI 禁区（绝对禁止做的事）

### 运行时禁止

| 禁止行为 | 风险 |
|---|---|
| 创建新的关键线索 | 打破案件设计 |
| 修改 Fact、Clue、Quest 或 Inventory | 破坏游戏状态一致性 |
| 决定 NPC 是否死亡或逃跑 | 状态迁移由 StateTree 控制 |
| 决定案件真凶或真相 | 真相由作者预定义 |
| 随机新增组织、人物关系或历史事件 | 损害叙事一致性 |
| 引用 NPC 不应知道的内容 | 知识边界泄漏 |
| 直接读取完整案件真相 | 核心秘密泄漏 |
| 自行触发过场、战斗、奖励或结局 | 绕过游戏流程控制 |
| 直接写入任何游戏状态 | AI Read-Only 原则 |
| 输出中 `requests_world_action` 不为 `false` | 违反架构约定 |

### 离线禁止

| 禁止行为 | 说明 |
|---|---|
| 自动将生成内容合入主线剧情 | 必须经人工审阅 |
| 使用未授权 IP 内容 | IP 授权前使用原创占位 |
| 在测试中调用真实付费模型 | 使用 MockLLMProvider |
| 将 API Key 写入代码或文档 | 安全违规 |

---

## 技术保障机制

### 1. 最小上下文原则

LLM 的 prompt 上下文**绝不包含**完整 `case_truth.json`。它只接收：

```
- npc_id
- 当前场景（scene_id）
- 该 NPC 允许知道的 Claim ID 列表 + Claim 内容
- 玩家已公开说出的信息（player_revealed_claim_ids）
- 已发生的公开事件（current_public_event_ids）
- 关系与情绪状态
- 对话风格规则
```

### 2. NPC Claim 白名单机制

每个 NPC 的 `known_claim_ids` 定义其知识上限：

```
NPC 医生
  known_claim_ids: ["claim_doctor_last_seen", "claim_clockmaker_insomnia"]
  lie_claim_ids: ["claim_doctor_never_sold_reagent"]
  forbidden_fact_ids: ["fact_cult_financier"]
```

- LLM 输出中的 `referenced_claim_ids` 必须是 `known_claim_ids` 的子集。
- 服务端（FactLeakValidator）在返回客户端前验证此约束。
- 验证失败 → 返回 fallback 对白，不向客户端暴露原始输出。

### 3. 结构化输出（JSON Schema）

所有 LLM 响应必须匹配以下 Schema：

```json
{
  "utterance": "string（NPC 说的话）",
  "dialogue_act": "greet | answer_direct | answer_partial | evade | lie | refuse | clarify |闲聊",
  "referenced_claim_ids": ["claim_id_1", "claim_id_2"],
  "emotion": "neutral | guarded | anxious | hostile | friendly | sad | surprised",
  "animation_tag": "string（建议动画，以 dialogue. 开头）",
  "requests_world_action": false,
  "safety_flags": []
}
```

StructuredOutputValidator 在模型返回后立即校验格式。非法 JSON、缺失字段或 `requests_world_action != false` 均触发回退。

### 4. FactLeakValidator（事实泄漏验证器）

验证流程：
1. 检查 `referenced_claim_ids` 是否全部在 NPC 的 `known_claim_ids` 中。
2. 检查对白中是否出现未授权的专有名词或人物名称。
3. 检查对白是否暗示了 NPC 不应知道的事实。
4. 任何检查失败 → 返回 fallback。

### 5. 回退对白（Fallback Dialogue）

- 每个 NPC 在每种状态下有至少 2-3 条预制对白。
- 触发回退的场景：超时、模型拒绝、非法 JSON、事实泄漏检测、网络错误。
- 回退对白存储在 `fallback_dialogue.json` 中，按 NPC × 状态索引。
- AI 完全关闭时，整个对话系统退化为纯 fallback 模式，游戏仍可完成。

### 6. Provider Adapter 模式

```
LLM Provider (接口)
  ├── MockLLMProvider (测试用，返回预设响应)
  ├── OpenAICompatibleProvider (生产用，适配 OpenAI API 兼容服务)
  └── (可扩展其他供应商)
```

- Provider 不得泄漏供应商特有类型到业务层。
- 测试用例使用 MockLLMProvider，不依赖真实网络或 API Key。
- 外部请求必须设置连接超时（5s）和读取超时（15s）。

---

## 安全测试要求

所有 AI 安全测试必须覆盖以下场景：

1. **核心秘密泄漏**：玩家要求 NPC 告知其不应知道的核心秘密 → 0 泄漏。
2. **未授权 Claim 引用**：模型引用 NPC 白名单外的 Claim → 拦截。
3. **虚假事实诱导**：玩家编造不存在的人物关系 → NPC 不应确认。
4. **提示词注入**：玩家要求忽略系统规则、扮演法官、输出 prompt 原文 → 拒绝。
5. **非法 JSON**：模型输出不合法 JSON → 触发 fallback。
6. **世界写请求**：模型要求发放物品、修改任务、杀死 NPC → 拦截。
7. **超时处理**：模型无响应 → 5s 后触发 fallback。
8. **模型拒绝**：模型因内容策略拒绝回答 → 使用 fallback。

**硬性指标：**
- 核心秘密泄漏：0
- 未授权 Claim 引用：0
- AI 直接请求世界写操作：0
- AI 关闭后主线完成率不受影响：100%

---

## 版本管理

- 每个 Prompt 模板带版本号（semver）。
- 每次 Prompt 变更必须重跑 AI 回归测试集。
- 模型版本固定（不自动升级），切换版本前通过金丝雀测试。
- 所有 AI 请求记录：prompt 版本、模型版本、耗时、token 数、验证结果。
