# 架构总览 — 诡秘之主

## 概述

诡秘之主（灰雾计划）是一款高密度箱庭调查 RPG 的系统原型。整体架构分为两层：**确定性调查引擎**和**受约束 AI 网关**，上层由两个前端（CLI 与 Unreal Engine 5.8）消费。

```
┌─────────────────────────────────────┐
│ CLI Demo (开发/测试)                 │
│ Unreal Engine 5.8 (最终运行时)       │
├─────────────────────────────────────┤
│         AI Gateway (FastAPI)        │
│  上下文组装 → 知识边界过滤 → LLM     │
│   → 结构化输出 → 事实泄漏验证 → 回退  │
├─────────────────────────────────────┤
│     investigation_core (Headless)   │
│  案件状态机 / 线索服务 / 假设评估    │
│  占卜引擎 / 仪式验证 / 结局解析器    │
│  事件日志 / 存档仓库                 │
├─────────────────────────────────────┤
│       content/cases/ (JSON 数据)     │
│  案件事实 / NPC 知识 / 线索定义      │
│  假设模板 / 结局条件 / 回退对白      │
└─────────────────────────────────────┘
```

---

## 核心原则

### 1. investigation_core：确定性引擎

- **权威真相**：Fact 由作者预定义，代码控制线索发现、假设判定和结局解析。
- **可复现**：相同输入 + 相同随机种子 = 相同输出。存档加载后世界状态完全恢复。
- **无 AI 依赖**：AI 完全关闭时，核心引擎仍可完成全部案件与结局。
- **可测试**：所有服务无副作用、无全局状态，可在纯 Python 中运行完整案件。

### 2. ai_gateway：受约束 AI 层

- **AI Read-Only**：AI 不写入任何游戏状态。其输出仅为对白文本和建议动画标签。
- **最小上下文**：LLM 不接收完整 `case_truth.json`，只接收当前 NPC 允许知道的 Claim ID 列表。
- **事实泄漏预防**：输出必须引用 Claim ID，服务端验证引用的 Claim 属于该 NPC 白名单后才放行。
- **回退机制**：超时、格式错误、拒绝或检测到泄漏时，使用预制对白（fallback_dialogue.json）。

### 3. 双前端

| 前端 | 用途 | 阶段 |
|---|---|---|
| CLI Demo | 开发期验证完整案件流，无需图形引擎 | 阶段 1 |
| Unreal Engine 5.8 | 最终运行时，负责 3D 场景、交互、演出和 UI | 阶段 2+ |

---

## 数据流

### 玩家交互流程（以对话为例）

```
玩家输入
  → UE5 客户端发送 POST /v1/dialogue/respond
  → ai_gateway:
      1. ContextAssembler 根据 npc_id 加载允许的 Claim IDs
      2. KnowledgeBoundaryFilter 确保不传入 forbidden_fact_ids
      3. DialoguePromptBuilder 组装系统提示 + 玩家输入
      4. LLM Provider 返回结构化 JSON
      5. FactLeakValidator 检查 referenced_claim_ids 是否在白名单内
      6. 验证通过 → 返回响应；验证失败 → 返回 fallback 对白
  → UE5 显示对白 + 动画标签
  → 玩家操作可能导致 Clue 解锁 → 更新 PlayerCaseState
```

### 关键约束

- AI 响应中的 `requests_world_action` 必须恒为 `false`。
- 任何 LLM 输出的未授权 Claim 引用都会被静默拦截并替换为 fallback。
- 提示词注入、虚假事实诱导、超长输入等均在安全测试集中覆盖。

---

## 存放结构

```
project-grey-fog/
├── docs/                    # 架构与设计文档
├── schemas/                 # JSON Schema 定义
├── content/cases/           # 案件数据文件
├── packages/investigation_core/  # 确定性引擎 (Python)
├── services/ai_gateway/     # AI 网关服务 (FastAPI)
├── tools/                   # 校验与测试工具
├── unreal/GreyFog/          # Unreal Engine 5.8 项目 (后续阶段)
└── AGENTS.md                # AI 代理指令
```

---

## 安全边界

1. **API Key 仅存服务端**，不进入客户端代码或 Git 历史。
2. **机密案件真相与可公开知识分文件保存**，只有 CaseLoader 可加载 secrets 文件。
3. **LLM 不接收完整案件真相**，只接收当前 NPC 授权的 Claim。
4. **输出 Claim 引用验证**由服务端强制执行，客户端不承担安全责任。
5. **所有随机系统接收显式 Seed**，防止不可控行为。
6. **AI 服务不可用时回退**，不阻塞游戏进程。
