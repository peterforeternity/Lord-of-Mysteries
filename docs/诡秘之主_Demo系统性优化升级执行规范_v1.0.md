# 《诡秘之主》Demo 系统性优化升级执行规范 v1.0

## 一、统一命名

项目对外名称统一改为：

**诡秘之主**

英文内部代号可保留为 `Lord of Mysteries`。为避免破坏依赖，不重命名现有 Python 包、目录和数据库表。

必须同步修改：

- 浏览器 `<title>`；
- 首页主标题、Logo、导航栏；
- 新手教程、规则页、加载页；
- 存档页、结局页、错误页；
- README、部署文档和 PR 描述；
- PWA manifest、SEO/Open Graph metadata（如存在）；
- 监控项目名、日志 application_name；
- 前端测试断言与快照；
- `/v1/health` 中的服务显示名称。

公开商业发布前，需单独确认名称、角色、世界观和素材授权。本轮只处理技术升级。

---

## 二、升级目标

将现有浏览器 Demo 升级为：

1. 交互稳定、错误可追踪；
2. 新用户 3 分钟内理解基础规则；
3. 剧情目标清晰、推进可视化；
4. 核心流程具有完整自动化测试；
5. 完成真实用户体验测试方案；
6. 可部署到固定公网生产环境；
7. 具备安全防护、监控、备份与回滚能力。

项目目录：

```text
/Users/peterchen/Documents/trae_projects/诡秘之主
```

开发分支：

```text
feat/demo-optimization-v1
```

本轮禁止：

- 继续 UE5 开发；
- 增加第二个案件；
- 接入真实付费 AI；
- 增加账号、商城、多人或支付；
- 使用 Cloudflare Quick Tunnel 作为正式生产环境；
- 伪造用户测试、渗透测试、性能或可用性数据。

---

## 三、技术指标定义

### 1. 交互正确率

“100% 正确响应”仅指规范定义的交互在规定浏览器、视口和测试数据下全部通过。

覆盖：

- 单击、双击、快速连续点击；
- 键盘、触控、滑动；
- 拖拽（如推理板使用）；
- 浏览器前进/后退；
- 刷新、保存、恢复；
- 慢速网络、API 超时、业务错误。

### 2. 延迟

UI 操作到按钮出现 pressed/loading/disabled：

```text
p95 ≤ 100ms
p99 ≤ 150ms
```

生产 API：

```text
GET /v1/health：p95 ≤ 200ms
GET /v1/game/{save_id}/view：p95 ≤ 300ms
POST /v1/game/{save_id}/action：p95 ≤ 500ms
p99 ≤ 1000ms
```

页面：

```text
首次可操作时间 ≤ 3 秒
路由切换主要内容显示 ≤ 500ms
前端未捕获错误率 < 0.1%
```

### 3. 可用性

99.9% 可用性必须由真实线上监控验证。开发完成时只能声明：

```text
已具备 99.9% SLO 所需架构、监控、告警、备份和回滚能力；
实际可用性需累计至少 30 天线上数据验证。
```

---

# Phase A：错误修复与交互稳定性

## A1. 建立基线

创建：

```text
docs/optimization/baseline-report.md
```

包含：

- 当前 Commit SHA；
- 页面、路由、Game API 清单；
- 数据库与部署方式；
- 当前测试数量；
- 当前性能数据；
- 当前错误处理；
- `invalid target` 复现步骤；
- Console、Network、后端日志；
- Playwright trace 或截图。

## A2. 请求关联 ID

所有请求增加：

```text
X-Request-ID
X-Session-ID
```

要求：

- 前端生成或复用 Request ID；
- 后端原样返回；
- EventLog、应用日志和错误报告使用相同 ID；
- 不记录 Token、Cookie 和敏感输入。

## A3. invalid target 根因检查

不得通过隐藏提示修复。必须检查：

1. 前端当前 View 中目标是否仍可用；
2. `target_id` 是否与后端 ID 完全一致；
3. 是否把显示文字当成 ID；
4. 是否传入 undefined、null 或空字符串；
5. 刷新后 Zustand 状态是否过期；
6. `state_version` 是否落后；
7. 连续点击是否发送重复请求；
8. Action 完成后旧按钮是否仍可点击；
9. 地点切换时旧组件是否继续发请求；
10. 读档后旧目标是否残留；
11. 不同 Action 是否使用不同命名规范；
12. E2E 是否调用当前 UI 不可见目标；
13. 内容文件是否有重复 ID；
14. 目标“可见性”和“可执行性”是否由不同逻辑判断；
15. API 代理是否改写请求体。

## A4. 后端成为 Action 权威

Game View 返回：

```json
{
  "available_actions": [
    {
      "action_id": "action_abc123",
      "action_type": "inspect",
      "target_id": "clue_burn_pattern",
      "label": "调查地面灼痕",
      "enabled": true,
      "disabled_reason": null,
      "expected_version": 23,
      "parameters_schema": {}
    }
  ]
}
```

前端规则：

- 只渲染 `available_actions`；
- 不自行拼接 `target_id`；
- 不使用显示文字作为 ID；
- 提交服务端提供的 `action_type`、`target_id`、`expected_version`；
- 成功后用响应中的完整 View 替换旧 View。

## A5. 统一错误码

至少实现：

```text
INVALID_TARGET
TARGET_NOT_VISIBLE
TARGET_NOT_AVAILABLE
ACTION_NOT_ALLOWED
STATE_VERSION_CONFLICT
INVALID_PARAMETERS
RESOURCE_INSUFFICIENT
GAME_ALREADY_FINISHED
SESSION_NOT_FOUND
RATE_LIMITED
INTERNAL_ERROR
```

错误响应示例：

```json
{
  "success": false,
  "error_code": "INVALID_TARGET",
  "message": "当前场景中不存在该操作目标。",
  "request_id": "req_xxx",
  "recoverable": true,
  "recovery": {
    "refresh_view": true,
    "latest_state_version": 24
  }
}
```

## A6. 防重复提交

所有交互按钮：

- 请求开始立即 pending；
- pending 期间禁止重复触发；
- GET 可使用 AbortController 取消过期请求；
- 页面卸载后不得更新组件；
- POST Action 禁止自动盲重试；
- 增加 `idempotency_key`；
- 同一 key 返回相同结果。

## A7. 导航状态机

统一为：

```text
START
CASE_SELECT
PLAYING
DEDUCTION
RITUAL
SAVE_LOAD
ENDING
ERROR_RECOVERY
```

规则：

- 路由守卫依据服务端 View；
- 只有 `view.game_over=true` 可进入 Ending；
- 无 `save_id` 进入 Game 时返回案件选择；
- Ending 刷新后通过 `save_id` 获取最新 View；
- 浏览器后退不得丢失服务端状态；
- 禁止在 React render 阶段执行 navigate；
- 所有跳转写入 InteractionLog。

## A8. 交互性能埋点

记录：

```text
interaction_start
visual_feedback_shown
request_sent
response_received
view_committed
navigation_completed
```

计算：

- input_to_feedback_ms；
- request_duration_ms；
- response_to_render_ms；
- total_interaction_ms；
- success、error_code；
- route、action_type、target_id；
- state_version。

## A9. 根因报告

创建：

```text
docs/optimization/invalid-target-rca.md
```

包含：

- 现象与复现；
- 根因；
- 为什么旧测试未发现；
- 修复方案和代码位置；
- 回归测试；
- 防复发机制；
- 修复前后错误率与延迟。

---

# Phase B：三级引导与玩法可视化

## B1. 引导架构

新增配置化结构：

```text
TutorialDefinition
TutorialStep
TutorialProgress
TutorialTrigger
TutorialOverlay
TutorialManager
```

禁止把引导逻辑散落在页面组件中。

## B2. 新手引导

首次进入案件触发，3 分钟内完成：

1. 认识当前地点；
2. 调查第一个目标；
3. 获得第一条线索；
4. 理解灵性、污染、稳定度；
5. 前往第二地点；
6. 打开推理板；
7. 理解线索如何支持或反驳假设；
8. 学会保存。

支持：

- 跳过、暂停、上一步；
- 重新播放；
- 永久关闭；
- 设置页重置。

## B3. 功能引导

首次解锁时触发：

- 灵视；
- 占卜；
- 仪式；
- 异常物品；
- 推理提交；
- 存档读取。

每项不超过 3 步。

## B4. 场景引导

特殊节点触发：

- 高污染；
- 灵性不足；
- 仪式材料不足；
- NPC 即将离开；
- 出现矛盾证据；
- 结局提交前确认；
- 失败后恢复路线。

## B5. 视觉提示

实现：

- 聚光高亮；
- 半透明遮罩；
- 动态箭头；
- 呼吸高亮；
- 锚定提示框；
- 步骤进度；
- Esc 关闭；
- 移动端安全区避让；
- `prefers-reduced-motion`；
- 屏幕阅读器文本。

禁止高频闪烁、无法关闭或只依赖颜色表达。

## B6. 游戏规则页

新增：

```text
/rules
```

页面标题：

```text
《诡秘之主》玩法规则
```

覆盖：

- 调查、线索、NPC 陈述；
- 灵视、占卜、仪式；
- 推理板、污染、存档、结局。

每项包含示意图、50 字以内说明、操作示例、键鼠和触控说明。

---

# Phase C：剧情推进机制

## C1. 剧情节点模型

```json
{
  "node_id": "story_node_03",
  "chapter_id": "chapter_01",
  "title": "停摆的钟",
  "status": "locked",
  "triggers": {
    "all": [],
    "any": [],
    "none": []
  },
  "objectives": [],
  "unlock_actions": [],
  "completion_actions": [],
  "next_nodes": []
}
```

## C2. 触发条件

支持：

- elapsed_turns；
- completed_actions；
- discovered_clues；
- revealed_facts；
- inventory_items；
- NPC state；
- hypothesis status；
- player attributes；
- visited locations；
- ritual result；
- specific choice；
- event count；
- previous node completed。

关键剧情不得依赖 AI 或真实时间作为唯一条件。

## C3. 确定性

- 剧情触发在后端执行；
- AI 不得触发剧情节点；
- 同一 Seed 和 EventLog 重放一致；
- 节点只完成一次；
- 重复请求不得重复奖励；
- 节点解锁、开始、完成写入 EventLog。

## C4. 剧情 UI

实现：

- 顶部主线进度条；
- 当前章节和当前节点；
- 下一目标；
- 章节地图；
- 剧情节点指示器；
- 当前主目标；
- 1—3 个子目标；
- 推荐行动与风险提示；
- 章节标题卡和过渡动画。

隐藏节点不得泄露真相，只显示“未知节点”。

---

# Phase D：测试与质量保障

## D1. 四类测试

- 功能测试；
- 兼容性测试；
- 性能测试；
- 用户体验测试。

浏览器：

- Chrome、Safari、Firefox、Edge 最新版；
- iPhone Safari、Android Chrome；
- 390×844、412×915、平板视口。

## D2. 至少 30 个核心交互测试

至少覆盖：

1. 新游戏；
2. 案件加载；
3. 地点移动；
4. 普通线索；
5. 隐藏线索；
6. NPC 对话；
7. 灵视；
8. 占卜；
9. 仪式成功；
10. 仪式失败；
11. 使用物品；
12. 休息；
13. 推理板；
14. 正确假设；
15. 错误假设；
16. 快速双击；
17. state_version 冲突；
18. 保存；
19. 刷新；
20. 读取；
21. 浏览器后退；
22. 网络断开；
23. API 超时；
24. 手机导航；
25. 新手引导跳过；
26. 功能引导；
27. 场景引导；
28. Ending 刷新；
29. 高污染警告；
30. invalid target 自动恢复。

验收：

```text
自动化通过率 100%
人工核心流程通过率 ≥ 95%
```

## D3. 10 人真实用户测试

创建：

```text
docs/ux/user-test-plan.md
docs/ux/user-test-results.csv
docs/ux/user-test-report.md
```

每位测试者记录：

- 是否首次接触；
- 3 分钟内是否理解规则；
- 是否知道下一步；
- 首次完成调查时间；
- 首次打开推理板时间；
- 卡住位置；
- 错误次数；
- 上手难度 1—5；
- 剧情自然度 1—5；
- 建议。

目标：

```text
样本数 ≥ 10
上手难度平均 < 3/5
规则理解题正确率 ≥ 80%
剧情自然度平均 ≥ 4/5
```

没有真实测试者时标记：

```text
PENDING_REAL_USER_STUDY
```

## D4. 剧情连贯性

覆盖所有主线节点、替代路线、NPC 移除、失败恢复、保存读取和三类结局。

自动检查：

- 不可达节点；
- 死循环；
- 无下一步节点；
- 唯一线索软锁；
- 冲突触发器；
- 重复奖励；
- 提前泄露 Ending。

---

# Phase E：公网部署与安全

## E1. 生产架构

Quick Tunnel 仅用于临时演示。

推荐：

```text
Cloudflare DNS/CDN/WAF
        ↓
静态前端托管
        ↓
Game API
        ↓
PostgreSQL
```

可选：

- Cloudflare Pages + Render/Railway/Fly.io；
- Vercel + Render/Railway；
- VPS + Caddy + Docker Compose。

生产环境不使用 SQLite 多实例写入。

## E2. 环境

至少：

```text
development
staging
production
```

配置通过环境变量，禁止提交 Secret、Token、数据库密码和 `.env`。

## E3. 安全措施

必须实现：

- HTTPS、HSTS；
- CSP；
- X-Content-Type-Options；
- Referrer-Policy；
- Permissions-Policy；
- 限制 CORS；
- 参数化 SQL；
- XSS 防护；
- CSRF 防护或明确威胁模型；
- 不可预测 save_id；
- 请求体大小限制；
- Action 限流；
- 管理接口保护；
- 不返回内部堆栈；
- dependency audit；
- secret scan；
- CodeQL/SAST；
- OWASP ZAP staging scan。

自动扫描不等于第三方渗透测试。未进行第三方测试时不得声称“全面渗透测试完成”。

## E4. 监控告警

前端：

- JavaScript exception；
- unhandled promise；
- route、release SHA、request_id；
- source map；
- 敏感数据脱敏。

后端 JSON 日志字段：

```text
timestamp
level
service
environment
request_id
session_id
route
method
status_code
duration_ms
action_type
target_id
state_version
error_code
release_sha
```

指标：

- 请求量、p50/p95/p99；
- 4xx、5xx；
- INVALID_TARGET；
- STATE_VERSION_CONFLICT；
- Action 成功率；
- JS 错误；
- 保存失败率；
- Ending 完成率；
- 数据库错误；
- CPU、内存、磁盘。

告警：

- 5xx > 2% 持续 5 分钟；
- p95 > 500ms 持续 10 分钟；
- 健康检查连续失败；
- INVALID_TARGET 突增；
- 数据库不可用；
- JS 错误突增；
- 磁盘 > 80%；
- 备份失败。

---

# CI/CD 要求

Python：

```bash
uv sync --frozen
uv run ruff check .
uv run black --check .
uv run mypy .
uv run pytest --cov --cov-report=term-missing --cov-fail-under=90
uv run python tools/run_playthrough.py --all
```

Frontend：

```bash
cd apps/web
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
```

E2E：

```bash
npm run test:e2e
```

安全：

- dependency audit；
- secret scan；
- CodeQL/SAST；
- OWASP ZAP staging scan。

发布流程：

```text
PR → CI → staging → smoke test → security check → manual approval → production
```

必须支持回滚。

---

# 必须提交的报告

```text
docs/optimization/optimization-report.md
docs/optimization/invalid-target-rca.md
docs/optimization/interaction-performance-report.md
docs/optimization/tutorial-implementation.md
docs/optimization/story-system.md
docs/testing/test-plan.md
docs/testing/test-results.md
docs/ux/user-test-plan.md
docs/ux/user-test-report.md
docs/deployment/production-deployment.md
docs/deployment/rollback.md
docs/security/threat-model.md
docs/security/security-assessment.md
docs/operations/monitoring-alerting.md
```

报告必须区分：

- 已实现；
- 已自动验证；
- 已人工验证；
- 已线上验证；
- 等待真实用户测试；
- 等待第三方安全测试。

---

# 可直接交给 Agent 的执行指令

```text
现在对《诡秘之主》浏览器 Demo 执行系统性优化升级。

项目目录：
/Users/peterchen/Documents/trae_projects/诡秘之主

第一要求：
将产品对外名称统一修改为“诡秘之主”。

必须修改：
- 浏览器 title
- 首页标题
- 导航栏
- 教程
- 游戏规则页
- 存档页
- 结局页
- 错误页
- README
- 部署文档
- 监控项目名
- 测试断言
- metadata
- /v1/health 服务显示名称

不要重命名现有 Python 包、目录和数据库表。

创建分支：

git checkout main
git pull --ff-only origin main
git checkout -b feat/demo-optimization-v1

完整阅读并执行：

docs/诡秘之主_Demo系统性优化升级执行规范_v1.0.md

按阶段执行，不能一次性同时做完五个阶段。

第一轮只执行 Phase A：

1. 建立 baseline-report
2. 稳定复现 invalid target
3. 输出 invalid-target-rca
4. 后端实现 available_actions
5. 前端只能使用后端返回的 action_type 和 target_id
6. 实现 idempotency_key 和防重复提交
7. 建立统一导航状态机
8. 增加 Request ID、结构化日志和错误监控
9. 增加交互性能埋点
10. 完成 invalid target、重复点击、刷新、后退和读档回归测试
11. 运行所有 Python、Frontend 和 E2E 门禁
12. 创建独立 Commit 并推送分支

禁止：
- 增加第二个案件
- 接入真实 AI
- 继续 UE5
- 正式生产部署
- 伪造性能、用户测试和安全测试结果

Phase A 完成后报告：

1. 产品名修改清单
2. invalid target 复现步骤
3. 根因
4. 为什么旧测试未发现
5. 修复方案
6. 修改文件
7. 新增错误码
8. Request ID 和日志字段
9. 防重复提交实现
10. 导航异常修复
11. 新增测试数量和结果
12. UI 反馈延迟 p50/p95/p99
13. API 延迟 p50/p95/p99
14. Commit SHA
15. PR 地址
16. 未完成事项

当前只执行 Phase A。完成并验收后再进入 Phase B。
```
