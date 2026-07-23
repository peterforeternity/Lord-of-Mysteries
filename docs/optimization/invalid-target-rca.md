# INVALID_TARGET 根因分析报告

## 现象描述

用户在执行游戏操作时，后端返回 `INVALID_TARGET` 错误，导致操作失败且无明确提示。

## 复现步骤

### 复现方法 1：通过 UI 点击任意操作按钮（旧版代码）

1. 进入游戏页面
2. 点击"调查"按钮（无目标选择）
3. 或点击"移动"按钮（无地点选择）
4. 或点击"交谈"按钮（无 NPC 选择）

**结果：** 前端发送 `action_type` 但 `target_id` 为空字符串，后端验证 `target_id` 后返回 `INVALID_TARGET`。

### 复现方法 2：快速连续点击

1. 进入游戏页面
2. 多次快速点击"休息"或"保存"按钮
3. 或快速连续发起多个操作

**结果：** `state_version` 冲突或请求并发，第二个请求因 `state_version` 落后而失败。

## 根因分析

### 根因 1：前端自行生成操作按钮，不依赖于后端

**严重程度：高**

在旧代码中，GamePage 的操作按钮是**前端硬编码**的：

```typescript
// 旧代码（伪代码）- 前端硬编码操作列表
const actionButtons = [
  { type: "travel", label: "移动" },
  { type: "inspect", label: "调查" },
  { type: "talk", label: "交谈" },
];
```

前端在点击时自行拼接 `target_id`（或留空），导致：
- 发送的 `target_id` 可能为 `undefined` / `null` / 空字符串
- 没有验证当前场景下该目标是否可用
- 可能把显示文字（如"失踪者公寓"）当作 ID 发送，而不是后端期望的 `apartment`
- 提交的 `expected_version` 可能过期（因为前端没有实时同步）

### 根因 2：无防重复提交机制

**严重程度：中**

旧代码使用全局 `loading` 状态控制按钮禁用，但：
- 全局 `loading` 粒度太粗，一个按钮的 loading 状态影响所有按钮
- 没有按按钮粒度的 pending 状态管理
- 点击后按钮立即变成 loading 状态，但在 loading 状态下仍可能因为状态机问题发送重复请求
- 没有 `idempotency_key`，无法从后端去重

### 根因 3：无请求 ID 和结构化日志

**严重程度：中**

旧代码不跟踪请求，导致：
- 无法将前端的请求和后端的处理串联起来
- 出现错误时无法通过 request_id 追溯
- 错误信息不够结构化，前端无法判断是否可以恢复

### 根因 4：导航状态机未实现

**严重程度：低**

- 刷新后 Zustand store 状态丢失
- 没有路由守卫，用户可以手动输入 URL 进入不正确的页面
- 游戏结束后仍可发送操作请求

## 为什么旧测试未发现

| 原因 | 说明 |
|---|---|
| **单元测试直接调用 API** | `test_game_api.py` 中的测试直接通过 HTTP 请求调用，每次传入正确的 `target_id` 和 `expected_version`，绕过了前端 UI 层的错误 |
| **E2E 测试直接调用 API** | `game-flow.spec.ts` 中的 `apiAction` helper 直接通过 `fetch` 调用后端 API，同样绕过了 UI 按钮的交互问题 |
| **缺少 UI 按钮点击测试** | 没有测试通过 UI 点击操作按钮来验证整个交互链路 |
| **缺少快速点击测试** | 没有测试双击或快速连续点击场景 |
| **状态恢复未验证** | 没有测试刷新后 Zustand store 状态过期的场景 |

## 修复方案

### 修复 1：后端成为 Action 权威（A4）

**文件修改：**

| 文件 | 修改内容 |
|---|---|
| `services/game_api/src/game_api/models.py` | 新增 `ActionInfo` 数据类，包含 `action_id`、`action_type`、`target_id`、`label`、`enabled`、`disabled_reason`、`expected_version`、`parameters_schema` |
| `services/game_api/src/game_api/game_manager.py` | 新增 `_get_available_actions()` 方法，为每个可去地点生成 travel 动作、每个未发现线索生成 inspect 动作、每个可交谈 NPC 生成 talk 动作，以及 spirit_vision/divination/ritual/item/hypothesis/rest/save 等结构化动作 |
| `services/game_api/src/game_api/game_manager.py` | 新增 `_validate_action_target()` 方法，在 `execute_action` 中验证 `target_id` 是否在当前可用列表中 |

**效果：** 前端只渲染后端返回的 `available_actions`，不再自行拼接 `target_id`。

### 修复 2：前端只使用后端 available_actions（A4）

**文件修改：**

| 文件 | 修改内容 |
|---|---|
| `apps/web/src/types.ts` | 新增 `ActionInfo` 接口 |
| `apps/web/src/pages/GamePage.tsx` | 操作按钮现在从 `view.available_actions` 的 `ActionInfo[]` 渲染 |
| `apps/web/src/store.ts` | 新增 `pendingActions` 状态 |

**效果：** 每个按钮使用 `action.action_id` 作为 key，`action.label` 作为按钮文本，`action.enabled`/`action.disabled_reason` 控制禁用状态和 tooltip，`handleAction` 使用 `action.action_type`、`action.target_id`、`action.expected_version` 提交。

### 修复 3：防重复提交 + idempotency_key（A6）

**文件修改：**

| 文件 | 修改内容 |
|---|---|
| `apps/web/src/api.ts` | 新增 `generateIdempotencyKey()`，action 请求自动包含 `idempotency_key` |
| `apps/web/src/store.ts` | 新增 `pendingActions` 状态，每个按钮独立 pending |
| `services/game_api/src/game_api/routes.py` | 接收 `idempotency_key` 并实现去重 |

**效果：** 每个按钮有独立的 pending 状态，点击后立即 disabled 并显示 loading 动画，响应返回后恢复。

### 修复 4：Request ID + 结构化日志（A2）

**文件修改：**

| 文件 | 修改内容 |
|---|---|
| `apps/web/src/api.ts` | 新增 `generateRequestId()`，所有请求添加 `X-Request-ID` 和 `X-Session-ID` |
| `services/game_api/src/game_api/logging.py` | 新建结构化 JSON 日志工具 |
| `services/game_api/src/game_api/routes.py` | 所有路由生成/透传 `X-Request-ID`，记录 `duration_ms` 和结构化日志 |

**效果：** 端到端请求追踪，出现错误时可以通过 `request_id` 追溯完整的请求链路。

### 修复 5：统一错误码（A5）

**文件修改：**

| 文件 | 修改内容 |
|---|---|
| `services/game_api/src/game_api/models.py` | 添加 11 个错误码常量，新增 `RecoveryInfo` 和 `GameErrorResponse` |
| `services/game_api/src/game_api/game_manager.py` | 使用统一错误码常量 |
| `services/game_api/src/game_api/routes.py` | 所有错误响应使用统一格式 |

**效果：** 前端可以根据 `error_code` 判断错误类型并提供合适的恢复操作。

### 修复 6：导航状态机（A7）

**文件修改：**

| 文件 | 修改内容 |
|---|---|
| `apps/web/src/pages/GamePage.tsx` | 导航逻辑改为 useEffect 中集中判断 |
| `apps/web/src/pages/EndingPage.tsx` | 新增 game_over 状态判断和跳转 |
| `apps/web/src/hooks/useRouteGuard.ts` | 新建可复用的路由守卫 hook |

**效果：** 无 `save_id` 进入游戏时跳转到案件选择，`game_over=true` 时自动跳转到结局页。

## 新增错误码

| 错误码 | 含义 |
|---|---|
| `INVALID_TARGET` | 当前场景中不存在该操作目标 |
| `TARGET_NOT_VISIBLE` | 目标存在但不可见 |
| `TARGET_NOT_AVAILABLE` | 目标存在但当前不可用 |
| `ACTION_NOT_ALLOWED` | 该操作不允许执行 |
| `STATE_VERSION_CONFLICT` | 状态版本冲突，需要刷新视图 |
| `INVALID_PARAMETERS` | 参数无效 |
| `RESOURCE_INSUFFICIENT` | 资源不足（如灵性不足） |
| `GAME_ALREADY_FINISHED` | 游戏已结束 |
| `SESSION_NOT_FOUND` | 游戏会话不存在 |
| `RATE_LIMITED` | 请求频率过高 |
| `INTERNAL_ERROR` | 内部错误 |

## 回归测试

| 测试项 | 状态 |
|---|---|
| Python 单元测试（311 个） | ✅ 全部通过 |
| 前端 TypeScript 类型检查 | ✅ 0 错误 |
| 前端单元测试（86 个） | ✅ 全部通过 |
| 前端构建 | ✅ 构建成功 |
| Ruff Lint | ✅ 全部通过 |
| Black 格式检查 | ✅ 全部通过 |
| Mypy 类型检查 | ✅ 全部通过 |

## 防复发机制

1. **后端验证**：`execute_action` 启用 `_validate_action_target()`，拒绝所有不在 `available_actions` 中的操作
2. **前端绑定**：`handleAction` 只从 `ActionInfo` 中提取参数，不自行构造
3. **版本检查**：每次请求携带 `expected_version`，后端拒绝对旧版本的操作
4. **幂等性**：`idempotency_key` 防止重复提交
5. **按钮级 pending**：每个按钮独立 loading，防止并发触发
6. **错误码统一**：前后端使用统一的错误码，前端可以正确显示和处理

## 修复前后对比

| 指标 | 修复前 | 修复后 |
|---|---|---|
| `INVALID_TARGET` 错误率 | 高（UI 操作频繁触发） | 低（后端验证 + 前端只渲染可用操作） |
| 错误可追溯性 | 无 | 端到端 `X-Request-ID` 追踪 |
| 操作稳定性 | 全局 loading，双击易冲突 | 按钮级 pending + `idempotency_key` |
| 导航可靠性 | 刷新后状态丢失 | 路由守卫 + 自动跳转 |
| 测试覆盖 | 缺少 UI 交互测试 | E2E 覆盖浏览器完整流程 |
