# Unreal 数据导入状态

> 更新日期：2026-07-22
> 本文件记录 Python 案件数据向 Unreal Engine 导入的实际完成状态。
> 不得假定未验证的步骤已经完成。

---

## 状态说明

```
JSON 转换脚本   ──(已验证)──→  Unreal JSON     ──(未验证)──→  DataTable/     ──(未完成)──→  .uasset
                                 反序列化                          PrimaryDataAsset

Editor Utility
(未完成)
```

---

## 各步骤详细状态

### 1. JSON 转换脚本 — 已验证 ✅

**文件**: `unreal/GreyFog/Scripts/import_case_data.py`

- 已将 Python 领域模型 (investigation_core) 的 JSON 输出映射为 UE JSON 格式
- 映射内容包括：facts、clues、hypotheses、npcs、endings、dialogueLines
- 枚举值映射表（Python snake_case → UE PascalCase）已建立
- 核心秘密事实验证（core_secret 至少 2 个来源）已实现
- 支持 `--dry-run` 验证模式
- 可通过 `uv run` 在无 UE 环境下执行

#### 示例用法
```bash
uv run python unreal/GreyFog/Scripts/import_case_data.py \  
    --case-dir content/cases/case_clockmaker_01 \  
    --dry-run
```

### 2. Unreal JSON 反序列化 — 未验证 ❌

- `CaseGraphSubsystem::ImportCaseFromJson()` 接收 JSON 字符串  
- 当前仅提取 `case_id` 和 `title` 字段  
- FFG_CaseData 的完整反序列化尚未实现  
- 未编写自动化测试验证反序列化正确性

#### 已知问题
```text
REQUIRES_UE_COMPILE: 需要 UE5.8 运行 import 测试用例来验证完整 JSON 反序列化路径。
```

### 3. DataTable / PrimaryDataAsset 创建 — 未完成 ❌

- 未创建 UDataTable 定义  
- 未创建 UPrimaryDataAsset 派生类  
- 当前使用纯 USTRUCT（FFG_FactData 等）在 C++ 中直接持有数据  
- 游戏启动时通过子系统 API 手动注入数据

### 4. .uasset 导入 — 未完成 ❌

- **`unreal/GreyFog/Content/` 目录不存在**
- 无 `.uasset` 文件
- 导入脚本的 `--output` 目标路径不可写入（需先创建 Content 目录）

### 5. Editor Utility — 未完成 ❌

- 未创建任何 Editor Utility Widget 或 Blueprint
- 数据导入当前仅通过命令行脚本和 C++ API 进行
- 未来可用于批量导入的蓝图编辑器工具尚未设计

---

## 数据流总结

```
content/cases/case_clockmaker_01/
├── case.json              ──→ 案件元数据
├── facts.secret.json      ──→ 事实列表
├── claims.json            ──→ NPC 陈述
├── clues.json             ──→ 线索列表
├── hypotheses.json        ──→ 假说列表
├── npcs.json              ──→ NPC 定义
├── items.json             ──→ 灵异物品
├── rituals.json           ──→ 仪式定义
└── playthroughs/          ──→ 自动化测试用例（Python 端）

  │
  ▼
import_case_data.py (已验证)
  │
  ▼
UE JSON 格式 (已验证)
  │
  ▼
CaseGraphSubsystem::ImportCaseFromJson() (未验证)
  │
  ▼
FFG_CaseData USTRUCT 内存对象 (部分实现)
  │
  ▼
DataTable / PrimaryDataAsset (未完成)
  │
  ▼
.uasset 导入 (未完成)
```

---

## 关键阻塞项

1. 需要 UE5.8 Editor 创建 `Content/` 目录和 `.uasset`
2. `ImportCaseFromJson()` 需要完成完整字段反序列化
3. 需要定义 DataTable 行结构体（RowStruct）
4. Editor Utility 需要蓝图编辑器环境
