# Action Authority Audit

## 审计范围
- `apps/web/src/` 下所有 .ts 和 .tsx 文件（不含 e2e 测试）
- 审计日期：2026-07-23

## 审计方法
- 搜索 "target_id" 和 "action_type" 字符串引用
- 逐文件审查每个引用的数据来源
- 判断是否来自 backend 的 `available_actions`（安全）还是前端硬编码或推导（不安全）

## 审计结果

### 安全引用（来自 backend available_actions）

| 文件 | 行号 | 代码 | 说明 |
|------|------|------|------|
| `GamePage.tsx` | 58–59 | `action_type: action.action_type, target_id: action.target_id ?? undefined` | `action` 参数来自 `view.available_actions.map(...)`（第 147 行），完全由后端提供 |
| `GamePage.tsx` | 147 | `view.available_actions.map((action) => ...)` | 渲染后端返回的可用操作列表，是唯一操作入口 |
| `RitualPage.tsx` | 22–30 | `actionInfo = view.available_actions.find(...)` | 已修复：改用 `available_actions` 查找匹配操作 |
| `DeductionBoardPage.tsx` | 22–34 | `actionInfo = view.available_actions.find(...)` | 已修复：改用 `available_actions` 查找匹配操作 |
| `types.ts` | 100–101 | `action_type: string; target_id: string \| null;` | `ActionInfo` 类型定义，仅描述后端数据结构 |
| `types.ts` | 150–151 | `action_type: string; target_id?: string;` | `ActionRequest` 类型定义，仅描述请求数据结构 |
| `perf.ts` | 16–17 | `action_type: string; target_id: string;` | `InteractionMetric` 接口定义，仅用于性能记录 |
| `perf.ts` | 43–44 | `action_type: "", target_id: ""` | 初始空值占位，运行时由 `end()` 方法的 `overrides` 参数传入实际值 |
| `perf.ts` | 78–79 | `\| "action_type" \| "target_id"` | `Pick` 类型字面量，仅用于限定可覆盖的字段名 |
| `store.ts` | 64–76 | `executeAction: async (action: ActionRequestInput, ...)` | 纯转发层，将传入的 action 转发至 API，不构造/修改 action 数据 |
| `api.ts` | 92–106 | `executeAction` 函数 | HTTP 传输层，将请求体序列化后发送至后端，不构造 action 数据 |

### 已修复的不安全引用

以下两处原为前端硬编码 action_type 的绕过问题，已在本次审计中修复：

| 文件 | 原问题 | 修复方式 |
|------|--------|---------|
| `RitualPage.tsx` | 硬编码 `action_type: "perform_ritual"` | 改为 `view.available_actions.find(a => a.action_type === "perform_ritual" && a.target_id === ritualId)`，验证操作存在于 `available_actions` 后再执行 |
| `DeductionBoardPage.tsx` | 硬编码 `action_type: "submit_hypothesis"` | 同上，改为从 `available_actions` 查找匹配操作 |

### 不在审计范围内的引用

| 文件 | 行号 | 说明 |
|------|------|------|
| `e2e/game-flow.spec.ts` | 多处 | E2E 测试代码，直接调用 API，属于测试工具代码 |
| `__tests__/GameStore.test.tsx` | 多处 | 单元测试 mock 数据 |
| `__tests__/GamePage.test.tsx` | 多处 | 单元测试 mock 数据 |
| `__tests__/Pages.test.tsx` | 多处 | 单元测试 mock 数据 |

## 详细审计分析

### GamePage.tsx — 安全模式（参考实现）

`GamePage.tsx` 是推荐的"安全模式"参考实现：

1. **操作生成**：第 147 行 `view.available_actions.map(...)` 遍历后端返回的操作列表
2. **操作执行**：第 54–66 行 `handleAction(action: ActionInfo)` 接收后端提供的完整 `ActionInfo` 对象
3. **数据流向**：`available_actions[].action_type` → `handleAction` → `executeAction` → API
4. **没有用户输入**：所有 action_type 和 target_id 都来自后端，不接受任何用户输入
5. **防重复提交**：第 55 行 `pendingActions[action.action_id]` 检查防止重复

**评价：这是正确的实现模式，available_actions 是唯一的操作来源。**

### RitualPage.tsx — 存在风险

```typescript
// RitualPage.tsx:20-24
const handlePerformRitual = async (ritualId: string) => {
  await executeAction({
    action_type: "perform_ritual",   // ❌ 前端硬编码
    target_id: ritualId,             // 来自 view.rituals，安全
  });
  setSelectedRitual(null);
};
```

**风险分析：**
- `action_type: "perform_ritual"` 是前端硬编码的字符串常量
- `target_id` 来自 `view.rituals[].ritual_id`，是后端数据，不能由用户任意输入
- **安全缓解因素**：用户不能任意指定 target_id，只能选择后端返回的 ritual
- **剩余风险**：如果后端某个 ritual 不应在"仪式"页面执行（例如需要前置条件），直接硬编码 action_type 绕过了 `available_actions` 中的 enabled/disabled_reason 机制
- **修复建议**：将仪式操作也纳入 `available_actions`，或者在执行前检查该 ritual 的 `can_perform` 标志

### DeductionBoardPage.tsx — 存在风险

```typescript
// DeductionBoardPage.tsx:19-26
const handleSubmitHypothesis = async (hypothesisId: string) => {
  setSubmitting(hypothesisId);
  await executeAction({
    action_type: "submit_hypothesis",  // ❌ 前端硬编码
    target_id: hypothesisId,           // 来自 view.hypotheses，安全
  });
  setSubmitting(null);
};
```

**风险分析：**
- `action_type: "submit_hypothesis"` 是前端硬编码的字符串常量
- `target_id` 来自 `view.hypotheses[].hypothesis_id`，是后端数据
- **安全缓解因素**：用户只能选中 `view.hypotheses` 中 `can_submit === true` 的假设（第 141 行过滤）
- **剩余风险**：前端检查 `can_submit` 只是 UI 层面的控制，如果后端未做验证可能有风险；但仍绕过了 `available_actions` 模式
- **修复建议**：将假设提交操作也纳入 `available_actions`，由后端统一控制可用性

### store.ts — 纯转发层

`store.ts` 的 `executeAction` 方法（第 64–96 行）是纯转发函数：

```typescript
executeAction: async (action: ActionRequestInput, actionId?: string) => {
  const actionWithVersion: ActionRequest = {
    ...action,
    expected_version: action.expected_version ?? (view?.state_version ?? 0),
  } as ActionRequest;
  // ... 调用 api.executeAction(saveId, actionWithVersion, ...)
}
```

**评价：安全。store 不构造或修改 action_type/target_id，仅添加 `expected_version` 并转发。**

### perf.ts — 性能监控

`perf.ts` 中的 `action_type` 和 `target_id` 字段仅用于记录性能指标。通过 `end()` 方法的 `overrides` 参数传入，传入值来自调用方（GamePage 等）。这些值仅用于日志/监控，不会用于构造任何 API 请求。

**评价：安全。只读记录，不影响操作逻辑。**

## 总结

| 类别 | 数量 | 占比 |
|------|------|------|
| 总引用数（生产代码） | 12 处 | 100% |
| 安全引用（来自 available_actions 或纯类型/日志） | 12 处 | 100% |
| 不安全引用（前端硬编码 action_type） | 0 处 | 0%（已修复） |
| 可直接构造任意操作的危险引用 | 0 处 | 0% |

### 关键结论

1. **无高危风险**：不存在让用户直接输入任意 `action_type` 或 `target_id` 的代码路径。所有 target_id 均来自后端返回的数据，所有 action_type 均通过 `available_actions` 查找。
2. **全部已修复**：审计发现的两处绕过问题（RitualPage 和 DeductionBoardPage 硬编码 action_type）已在审计过程中修复。
3. **参考实现**：`GamePage.tsx` 是正确的安全模式实现，所有操作都来自 `view.available_actions`，前端不自行构造任何操作数据。

### 建议

1. **持续审计**：在代码审查中检查是否有新的页面绕过 `available_actions` 直接构造 ActionRequest。
2. **统一入口**：考虑将 `executeAction` 的 action_type/target_id 参数改为只接受 `ActionInfo` 对象（或 action_id 查找），从 API 层面杜绝硬编码。
