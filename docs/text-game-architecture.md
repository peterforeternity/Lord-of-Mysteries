# Text Game MVP 架构文档

> 更新日期：2026-07-22
> 阶段：一（无 AI 可玩版本）

## 架构概览

```
+-------------------+       +------------------+       +------------------+
|                   |       |                  |       |                  |
|  React Frontend   | HTTP  |   Game API       | uses  | Investigation   |
|  (apps/web)       |──────→|   (game_api)     |──────→| Core (frozen)    |
|                   | JSON  |                  |       |                  |
+-------------------+       +------------------+       +------------------+
                                    |
                                    | SQLite
                                    v
                            +------------------+
                            |                  |
                            |  saves.db        |
                            |                  |
                            +------------------+
```

## 服务

### Game API (`services/game_api/`)

| 端点 | 方法 | 说明 |
|---|---|---|
| `/v1/health` | GET | 健康检查 |
| `/v1/cases` | GET | 可用案件列表 |
| `/v1/cases/{case_id}/metadata` | GET | 案件元数据 |
| `/v1/game/new` | POST | 创建新游戏会话 |
| `/v1/game/{save_id}/action` | POST | 执行游戏动作 |
| `/v1/game/{save_id}/view` | GET | 获取当前视图 |
| `/v1/game/{save_id}/save` | POST | 持久化存档 |
| `/v1/game/{save_id}/load` | POST | 加载存档 |
| `/v1/saves` | GET | 列出所有存档 |

### 游戏动作

所有动作为统一 JSON 格式：

```json
{
  "action_type": "travel",
  "target_id": "police_office",
  "parameters": {},
  "expected_version": 1
}
```

支持动作类型：
- `travel` — 移动到新地点
- `inspect` — 调查线索
- `talk` — 与 NPC 交谈
- `use_spirit_vision` — 使用灵视
- `perform_divination` — 占卜
- `perform_ritual` — 执行仪式
- `use_item` — 使用物品
- `submit_hypothesis` — 提交推理假设
- `rest` — 休息恢复灵性
- `save` — 存档
- `load` — 读档

### 状态版本

每次成功动作增加 `state_version`。前端提交时必须携带 `expected_version`。版本不一致返回 `ERR_STATE_VERSION_CONFLICT`。

### 前端 (`apps/web/`)

| 页面 | 路由 | 说明 |
|---|---|---|
| 开始页 | `/` | 新游戏、继续、案件选择、设置 |
| 案件选择 | `/cases` | 可用案件列表 |
| 主游戏页 | `/game/:saveId` | 三栏布局（桌面）/ 底部标签（手机） |
| 推理板 | `/game/:saveId/deduction` | 线索、证词、假说提交 |
| 仪式界面 | `/game/:saveId/ritual` | 仪式材料选择与执行 |
| 存档管理 | `/game/:saveId/saves` | 保存与读取 |
| 结算页 | `/ending` | 结局展示 |
| 设置页 | `/settings` | AI 开关、污染效果开关 |

### 状态管理

前端使用 Zustand。游戏世界状态权威在后端，前端仅显示视图，所有变更通过 Action 提交。

### 数据流

```
用户操作 → 前端 dispatch action → POST /action → Game API 执行
  → 更新 CaseStateMachine → 生成 GameView → 返回 JSON
  → 前端更新 Zustand store → React 渲染新视图
```

### 存档格式 (SQLite)

`saves` 表：
- save_id (TEXT PK)
- case_id (TEXT)
- seed (INTEGER)
- state_version (INTEGER)
- game_over (INTEGER)
- player_state (JSON TEXT)
- event_log (JSON TEXT)
- view_cache (JSON TEXT, optional)
- created_at / updated_at

### AI 边界

第一阶段 AI 默认关闭。所有 NPC 对话使用预制 Claim 和 fallback_dialogue。
AI 仅用于第二阶段的对白润色，不改变世界状态。

### 案件数据

复用 `content/cases/case_clockmaker_01/`：
- 5 个地点
- 6 个 NPC
- 15 条线索
- 4 个推理假设
- 5 个结局
- 1 个仪式（净化仪式）
- 1 件异常物品（占卜怀表）
- fallback_dialogue（预制 NPC 对白）
