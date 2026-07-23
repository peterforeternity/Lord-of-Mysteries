# 领域模型 — 诡秘之主

本文档定义 investigation_core 中的核心领域对象及其关系。

---

## 概览

```
                   ┌──────────┐
                   │   Case   │
                   └────┬─────┘
                        │ contains
          ┌─────────────┼──────────────┬──────────────┐
          ▼             ▼              ▼              ▼
       ┌──────┐    ┌───────┐     ┌────────┐     ┌──────────┐
       │ Fact │    │ Claim │     │  Clue  │     │Hypothesis│
       └──────┘    └───────┘     └────────┘     └──────────┘
          │             │              │              │
          │             │              │              │
          ▼             ▼              ▼              ▼
       ┌─────────────────────────────────────────────────┐
       │               EndingResolver                     │
       │     评估 Hypothesis 是否满足 Ending 条件          │
       └─────────────────────────────────────────────────┘
```

---

## 核心模型

### Fact（事实）

- **定义**：案件中的客观真相，由作者预先定义，是唯一权威的真实来源。
- **可见性**：玩家不可直接查看 Fact。Fact 仅通过 Clue 间接揭示。
- **属性**：
  - `fact_id`：唯一标识
  - `summary`：摘要描述
  - `truth`：始终为 `true`（Fact 不存在"假"）
  - `secrecy`：保密等级（`core_secret` / `hidden` / `public`）
  - `prerequisite_fact_ids`：前置 Fact（玩家需要先知道什么）
  - `revealed_by_clue_ids`：哪些 Clue 可以揭示该 Fact
- **规则**：每个关键 Fact 必须至少有两个独立的 Clue 可揭示（双来源规则）。AI 永远不会创建或修改 Fact。

### Claim（陈述）

- **定义**：NPC 说出的陈述或持有的认知。可能为真、假或不完整。
- **属性**：
  - `claim_id`：唯一标识
  - `speaker_npc_id`：发声的 NPC
  - `content`：陈述内容
  - `truth_status`：与事实的关系（`true` / `false` / `partial` / `unverifiable`）
  - `speaker_believes_it`：NPC 自己是否相信该陈述
  - `available_when` / `forbidden_when`：条件性可用性
- **规则**：AI 只能引用 NPC 白名单中的 Claim。NPC 可以有目的地撒谎（`lie_claim_ids`）。

### Clue（线索）

- **定义**：玩家在调查过程中实际获得的证据。是突破案件的关键。
- **属性**：
  - `clue_id`：唯一标识
  - `display_name`：玩家可见的名称
  - `source_type`：来源类型（`environment` / `npc_dialogue` / `divination` / `ritual` / `document` ）
  - `reveals_fact_ids`：该线索能揭示的事实
  - `requires_any_tags`：获取前置条件（能力、道具等）
  - `strength`：证据强度（1-3），影响 Hypothesis 评分
  - `missable`：是否可能错过
- **规则**：AI 永远不会创建或修改 Clue。每个关键 Fact 至少有两条独立 Clue。

### Hypothesis（假设）

- **定义**：玩家提交的推理组合，由已获得的 Clue 构成。
- **属性**：
  - `hypothesis_id`：唯一标识
  - `required_clue_ids`：该假设依赖的线索
  - `alternative_clue_ids`：替代线索（满足部分即可）
  - `required_fact_ids`：该假设意图揭示的事实
  - `min_strength`：最低证据强度要求
  - `excludes_hypothesis_ids`：互斥假设
- **规则**：Hypothesis 是玩家与 EndingResolver 交互的唯一入口。AI 不参与评估。

### NPC（非玩家角色）

- **定义**：案件中的角色，拥有独立的知识边界和行为状态。
- **属性**：
  - `npc_id`：唯一标识
  - `known_claim_ids`：该 NPC 知道的 Claim 列表（LLM 能引用的上限）
  - `lie_claim_ids`：NPC 故意说谎的 Claim（subset of known_claim_ids）
  - `forbidden_fact_ids`：禁止 NPC 接触的事实（即使 NPC 间接知道也不能说）
  - `personality`：人格参数（`formality` / `anxiety` / `aggression`）
- **规则**：LLM 永远不知道完整案件真相，只知道自己被授权的 Claim。

### NPC Knowledge（NPC 知识边界）

- NPC 的知识由 `known_claim_ids` 显式定义。
- LLM 上下文组装时只传入这些 Claim 的内容和 `speaker_believes_it`。
- 即使 NPC 在故事逻辑中"可能知道"某个事物，如果未出现在 `known_claim_ids` 中，LLM 也不得提及。
- `forbidden_fact_ids` 是硬边界——即使玩家诱导，NPC 也必须回避。

---

## 支撑服务

### EventLog（事件日志）

- **用途**：记录游戏中所有关键事件的不可变审计跟踪。
- **每条记录包含**：`event_id`、`timestamp`（UTC）、`event_type`、`source`、`entity_ids`、`payload`。
- **规则**：EventLog 是存档的核心组成部分。AI 不写入 EventLog。

### SaveRepository（存档仓库）

- **用途**：确定性保存和加载游戏状态。
- **规则**：
  - 存档包含：PlayerCaseState、EventLog、当前 Seed。
  - 加载存档后，相同操作序列必须产生相同结果。
  - 支持 3 个存档槽位。
- **规则**：存档文件不包含 AI 生成的任何内容（对白历史可以存，但不会影响游戏状态）。

### EndingResolver（结局解析器）

- **用途**：根据玩家已提交的 Hypothesis 和已揭示的 Fact，判断最终结局。
- **属性**：
  - `ending_id`：唯一标识
  - `conditions`：条件列表（需满足的 Hypothesis、已揭示的 Fact、是否触发特定事件等）
  - `summary`：结局描述
- **规则**：
  - Ending 评估完全由代码执行，不涉及 AI。
  - 每个案件至少 3 个结局（完整查明、部分查明、错误处理导致异常扩散）。
  - 所有结局必须在案件数据中显式定义，AI 不参与结局判定。
