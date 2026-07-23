# Phase A 优化 — 基线调研报告

> 生成时间：2026-07-23
> 用途：为 available_actions 优化提供基线数据

---

## 1. 基线数据

### 1.1 Commit SHA

```
7be6fbe (HEAD -> feat/demo-optimization-v1, origin/main, main)
feat: add newbie tutorial page with game mechanics guide
```

### 1.2 页面和路由清单

来源：`apps/web/src/App.tsx`，共 **9 个路由**（均包裹在 `<Layout />` 内）：

| 路径 | 页面组件 | 说明 |
|------|----------|------|
| `/` | `StartPage` | 主页 |
| `/tutorial` | `TutorialPage` | 新手教程 |
| `/case-select` | `CaseSelectPage` | 案件选择 |
| `/game` | `GamePage` | 游戏主界面 |
| `/deduction` | `DeductionBoardPage` | 推理板 |
| `/ritual` | `RitualPage` | 仪式 |
| `/save-load` | `SaveLoadPage` | 存档管理 |
| `/ending` | `EndingPage` | 结局 |
| `/settings` | `SettingsPage` | 设置 |

### 1.3 Game API 路由清单

来源：`services/game_api/src/game_api/routes.py`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/v1/health` | 健康检查 |
| GET | `/v1/cases` | 列出可用案件 |
| GET | `/v1/cases/{case_id}/metadata` | 获取案件元数据 |
| POST | `/v1/game/new` | 创建新游戏会话 |
| POST | `/v1/game/{save_id}/action` | 执行动作 |
| GET | `/v1/game/{save_id}/view` | 获取当前视图 |
| POST | `/v1/game/{save_id}/save` | 保存游戏 |
| POST | `/v1/game/{save_id}/load` | 加载游戏 |
| PUT | `/v1/game/{save_id}/view` | 视图兼容别名 |
| GET | `/v1/saves` | 列出所有存档 |

### 1.4 数据库

- **类型**：SQLite（WAL 模式，线程安全 via `threading.Lock`）
- **文件位置**：`data/game_saves.db`
- **表结构**（`saves` 表）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `save_id` | TEXT PK | 存档ID |
| `case_id` | TEXT NOT NULL | 案件ID |
| `seed` | INTEGER | 随机种子 |
| `state_version` | INTEGER | 状态版本号 |
| `game_over` | INTEGER | 是否结束 |
| `player_state` | TEXT | 玩家状态 JSON |
| `event_log` | TEXT | 事件日志 JSON |
| `view_cache` | TEXT | 视图缓存 JSON |
| `created_at` | TEXT | 创建时间 |
| `updated_at` | TEXT | 更新时间 |

### 1.5 测试数量

**前端测试（Vitest）**：**86 个测试**通过（4 个测试文件）

| 文件 | 测试数 |
|------|--------|
| `GameStore.test.tsx` | — |
| `GamePage.test.tsx` | — |
| `Pages.test.tsx` | — |
| `Components.test.tsx` | — |
| **合计** | **86** |

**后端测试（pytest）**：**311 个测试** collected

### 1.6 E2E 测试数量

- **文件**：`apps/web/e2e/game-flow.spec.ts`（1 个文件）
- **测试用例**：8 个（Playwright）
  1. `new_game_starts_successfully`
  2. `browser_true_ending`
  3. `browser_partial_ending`
  4. `browser_bad_ending`
  5. `save_resume`
  6. `rapid_clicks_state_version`
  7. `deduction_board_navigation`
  8. `mobile_viewport_basic_flow`

### 1.7 Playthrough 数量

- **playthrough_\*.py 文件**：0 个（目录中无匹配文件）
- **tools/ 目录下工具**：
  - `run_playthrough.py` — 剧本式跑通系统入口
  - `check_clue_reachability.py` — 线索可达性检查
  - `enumerate_endings.py` — 结局枚举
  - `validate_content.py` — 内容验证
  - `simulate_npc_removal.py` — NPC 移除模拟
- 无 `playthrough_*.json` 数据文件

---

## 2. 后端代码调研

### 2.1 GameView 数据模型（`models.py:151-180`）

```python
class GameView(BaseModel):
    state_version: int
    player: PlayerStatus          # spirituality, corruption, stability, location, visited_locations
    current_scene: str            # 当前场景 ID
    current_description: str      # 当前场景描述文本
    available_actions: list[str]  # 可用动作字符串列表
    clues: list[ClueInfo]
    npcs: list[NpcInfo]
    hypotheses: list[HypothesisInfo]
    endings: list[EndingInfo]
    items: list[ItemInfo]
    rituals: list[RitualInfo]
    event_log: list[EventLogEntry]
    game_over: bool
    final_ending: EndingInfo | None
    ai_enabled: bool              # 占位字段，始终为 False
```

**关键发现**：`available_actions` 目前仅是一个 `list[str]`（纯字符串列表），不包含结构化信息（如 target_id、参数、描述、条件等）。前端仅将其作为按钮文本直接渲染。

### 2.2 execute_action 处理逻辑（`game_manager.py:312-514`）

每个 `action_type` 的处理方式：

| ActionType | target_id 用途 | parameters 用途 | 返回值 |
|-----------|----------------|-----------------|--------|
| `TRAVEL` | `location_id` | `location_id` 后备 | 成功/失败 |
| `INSPECT` | `clue_id` | `clue_id` 后备 | 成功/失败（CLUE_NOT_AVAILABLE） |
| `TALK` | `npc_id` | `npc_id`/`claim_id` 后备 | 始终成功 |
| `USE_SPIRIT_VISION` | 未使用 | `target_id` 后备 | 灵性不足返回 INSUFFICIENT_SPIRITUALITY |
| `PERFORM_DIVINATION` | 未使用 | `question` | 始终成功 |
| `PERFORM_RITUAL` | `ritual_id` | `ritual_id`/`materials` 后备 | 成功/失败 |
| `USE_ITEM` | `item_id` | `item_id` 后备 | 成功/ITEM_NOT_FOUND |
| `SUBMIT_HYPOTHESIS` | `hypothesis_id` | `hypothesis_id` 后备 | 成功/失败（HYPOTHESIS_FAILED） |
| `REST` | 不使用 | 不使用 | 始终成功 |
| `SAVE` | 路由层处理 | 路由层处理 | 始终成功 |
| `LOAD` | 路由层处理 | 路由层处理 | pass-through |

**模式**：`action.target_id or action.parameters.get("key", "")` — target_id 优先，parameters 做后备。

### 2.3 available_actions 的生成逻辑（`game_manager.py:262-266`）

```python
available_actions = ["travel", "inspect", "talk", "rest", "submit_hypothesis", "save"]
if ps.current_location_id in LOCATION_ACTIONS:
    available_actions.extend(LOCATION_ACTIONS[ps.current_location_id])

# 最终去重
available_actions = list(set(available_actions))
```

**LOCATION_ACTIONS 硬编码映射**（`game_manager.py:75-81`）：

| 地点 | 扩展动作 |
|------|---------|
| `apartment` | inspect, talk, use_spirit_vision |
| `police_office` | inspect, talk |
| `clinic` | inspect, talk |
| `mystic_shop` | inspect, talk, perform_ritual, use_item |
| `workshop` | inspect, use_spirit_vision, perform_divination, perform_ritual |

**问题**：当前 available_actions 完全基于硬编码的地点映射 + 固定基础列表生成，**未考虑**：
- 玩家当前是否已获得该地点的所有线索（inspect 在无可用线索时不应显示）
- 灵性是否足够使用灵视（use_spirit_vision）
- 是否持有可用道具（use_item）
- 假设是否可提交（submit_hypothesis 永远显示，尽管 can_submit 标识存在）
- NPC 是否在当前地点（talk 即使无 NPC 也显示）

### 2.4 state_version 冲突检测

- **检测位置**：`game_manager.py:322` — `if action.expected_version != self.state_version`
- **递增时机**：每个成功的状态变更动作后 `self.state_version += 1`（TRAVEL/INSPECT/TALK/USE_SPIRIT_VISION/PERFORM_DIVINATION/PERFORM_RITUAL/USE_ITEM/SUBMIT_HYPOTHESIS/REST）
- **不变更版本的动作**：SAVE（路由层处理，不涉及状态变更）
- **前端配合**：Zustand store 在每次 `executeAction` 前自动填充 `expected_version` 为当前 `view.state_version`

### 2.5 错误码清单

**内部码 → API 映射**（`routes.py:23-31` 的 ERROR_CODES 字典）：

| 内部码 | API 返回码 | 说明 |
|--------|-----------|------|
| `NOT_FOUND` | `ERR_NOT_FOUND` | 资源未找到 |
| `INVALID_TARGET` | `ERR_INVALID_TARGET` | 无效目标 |
| `INVALID_ACTION` | `ERR_INVALID_ACTION` | 无效动作 |
| `STATE_VERSION_CONFLICT` | `ERR_STATE_VERSION_CONFLICT` | 版本冲突 |
| `SAVE_NOT_FOUND` | `ERR_SAVE_NOT_FOUND` | 存档未找到 |
| `GAME_ALREADY_OVER` | `ERR_GAME_OVER` | 游戏已结束 |
| `INTERNAL_ERROR` | `ERR_INTERNAL` | 内部错误 |

**未通过 ERROR_CODES 映射、从 execute_action 直接返回的码**：
- `CLUE_NOT_AVAILABLE`
- `INSUFFICIENT_SPIRITUALITY`
- `HYPOTHESIS_FAILED`
- `UNKNOWN_ACTION`

**HTTP 异常**（`main.py`）：
- `404` → `ERR_NOT_FOUND`
- `422` → `ERR_VALIDATION_FAILED`
- `500` → `ERR_INTERNAL`

---

## 3. 前端代码调研

### 3.1 前端如何获取 available_actions

**来源**：从 `GameView.available_actions`（`list[str]`）直接获取

**流程**：
```
后端 _make_view() → GameView.available_actions → JSON → Zustand store (view) → GamePage 渲染
```

**渲染**（`GamePage.tsx:106-115`）：
```tsx
{view.available_actions.map((action) => (
  <button key={action} onClick={() => handleAction(action)} disabled={loading}>
    <span className="font-medium">{action}</span>
  </button>
))}
```

**关键发现**：
- available_actions 是纯字符串列表，前端不做任何过滤/分类
- 按钮文本直接使用 action 的字符串值（英文，如 `"travel"`、`"inspect"`）
- 无中文显示标签映射
- 前端不知道每个 action 需要什么 target_id 或参数

### 3.2 前端如何拼接 target_id

**GamePage（通用动作按钮）**：
```tsx
const handleAction = (actionType: string) => {
  executeAction({ action_type: actionType });
};
// ❸ 不传 target_id 和 parameters
```

**DeductionBoardPage（提交假设）**：
```tsx
const handleSubmitHypothesis = async (hypothesisId: string) => {
  await executeAction({
    action_type: "submit_hypothesis",
    target_id: hypothesisId,  // ✅ 传了 target_id
  });
};
```

**E2E 测试中**（直接调用 API）：
```typescript
// rapid_clicks_state_version 测试通过 UI 按钮点击
// 其他测试通过 page.evaluate 直接调 API 拼接完整 payload
body: JSON.stringify({
  action_type: actionType,
  target_id: targetId,
  parameters,
  expected_version: expectedVersion,
})
```

**结论**：GamePage 的通用动作按钮 `handleAction` 只传 `action_type`，**不传 target_id**。这导致 `travel`、`inspect`、`talk`、`use_item`、`perform_ritual` 等需要 target 的动作在 UI 层面无法直接工作。实际的游戏流程操作是通过 API 直接调用（E2E 测试模式）或通过 NPC 对话弹窗等子组件间接实现的。

### 3.3 防重复提交实现

**全局 loading 锁**（Zustand store）：
```typescript
// store.ts: 每个 async action 入口 set({ loading: true, error: null })
// 出口 set({ loading: false })
```

**GamePage 按钮 disabled**：
```tsx
onClick={() => handleAction(action)}
disabled={loading}  // 全局 loading 锁
```

**DeductionBoardPage 的 per-action 锁**：
```tsx
const [submitting, setSubmitting] = useState<string | null>(null);
onClick={() => handleSubmitHypothesis(h.hypothesis_id)}
disabled={loading || submitting === h.hypothesis_id}
```

**问题**：
- 全局 `loading` 锁粒度太粗：一个请求未完成时，所有按钮都被禁用
- 使用 `loading` 而非 `submitting` 状态时，用户看不到具体是哪个动作在加载
- **Zustand store 没有请求队列/取消机制**，网络慢时连续点击会并发请求，可能导致 state_version 冲突

### 3.4 导航跳转逻辑

| 页面 | 导航行为 |
|------|----------|
| GamePage | 无 view 时 redirect → `/`；侧边栏按钮 → `/deduction`、`/ritual`、`/save-load`、`/tutorial`、`/ending` |
| DeductionBoardPage | 无 view 时显示"没有活跃的游戏"；"返回调查" → `/game` |
| SaveLoadPage | 加载存档后 `navigate("/game")`；"返回" → `navigate(-1)` 后退 |
| EndingPage | 预期通过 URL 参数 `?save_id=` 获取 saveId 显示结局 |

**Zustand store 状态生命周期**：
- `newGame` → 设置 `saveId` + `view`
- `executeAction` → 成功后更新 `view`
- `loadGame` → 设置 `saveId` + `view`
- `saveGame` → 只保存，不更新状态
- `fetchView` → 刷新 `view`
- **页面刷新后 store 状态丢失**，需要 reload 或进入 `/save-load` 从 SQLite 加载

---

## 4. 优化建议摘要（供 Phase A 参考）

1. **available_actions 结构化**：从 `list[str]` 改为包含 `{action_type, label, target_required, condition, disabled_reason}` 的结构化数据
2. **语义化过滤**：根据玩家状态（灵性、已有线索、持有物品、NPC 位置、假设完成度）动态过滤可用动作
3. **前端 target_id 补全**：为需要 target 的动作（inspect、travel、talk、use_item、perform_ritual）提供上下文关联的 target 选择
4. **防重复提交加强**：考虑请求队列或 per-action loading 状态
5. **中文显示映射**：动作按钮显示中文标签而非英文 action_type
6. **错误码覆盖**：`CLUE_NOT_AVAILABLE`、`INSUFFICIENT_SPIRITUALITY` 等内部码应注册到 ERROR_CODES
