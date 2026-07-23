# UE 工程文件清单

> 生成时间：2026-07-22
> 基于磁盘实际文件的审计结果，而非之前 AI 会话中的假定。

---

## 一、工程结构文件

| 路径 | 大小 | 空文件 | 职责 | 已验证 |
|---|---|---|---|---|
| `GreyFog.uproject` | 675B | 否 | UE 工程定义文件，声明模块与插件 | 是 |
| `Source/GreyFog.Target.cs` | 357B | 否 | Game 目标构建配置 | 是 |
| `Source/GreyFogEditor.Target.cs` | 409B | 否 | Editor 目标构建配置 | 是 |
| `Source/GreyFog/GreyFog.Build.cs` | 673B | 否 | GreyFog Runtime 模块构建定义 | 是 |
| `Source/GreyFog/GreyFog.h` | 233B | 否 | 模块头，声明日志类别 | 是 |
| `Source/GreyFog/GreyFog.cpp` | 223B | 否 | 模块实现，IMPLEMENT_PRIMARY_GAME_MODULE | 是 |

---

## 二、模块头文件 (.h)

| 路径 | 大小 | 空 | 职责 | 对应 .cpp | 验证 |
|---|---|---|---|---|---|
| `API/ApiSubsystem.h` | 4.2K | 否 | AI Gateway HTTP 通信子系统 | 存在 (12K) | 是 |
| `AbilitySystem/DivinationAbility.h` | 2.0K | 否 | 占卜 Ability | 存在 (3.3K) | 是 |
| `AbilitySystem/GreyFogAttributeSet.h` | 2.6K | 否 | GAS 属性集（灵性/腐化/稳定） | 存在 (2.5K) | 是 |
| `AbilitySystem/InvestigationGameplayAbility.h` | 2.1K | 否 | Ability 基类 | 存在 (1.3K) | 是 |
| `AbilitySystem/RitualInteractionAbility.h` | 1.6K | 否 | 仪式交互 Ability | 存在 (2.9K) | 是 |
| `AbilitySystem/SpiritVisionAbility.h` | 1.7K | 否 | 灵视 Ability | 存在 (2.9K) | 是 |
| `DataStructures/CaseData.h` | 2.3K | 否 | 案件数据 USTRUCT | N/A（纯头文件） | 是 |
| `DataStructures/ClueData.h` | 2.9K | 否 | 线索数据 USTRUCT | N/A | 是 |
| `DataStructures/DialogueData.h` | 3.4K | 否 | 对话数据 USTRUCT/UENUM | N/A | 是 |
| `DataStructures/EndingData.h` | 2.4K | 否 | 结局数据 USTRUCT | N/A | 是 |
| `DataStructures/FactData.h` | 1.3K | 否 | 事实数据 USTRUCT/UENUM | N/A | 是 |
| `DataStructures/HypothesisData.h` | 2.7K | 否 | 假说数据 USTRUCT | N/A | 是 |
| `DataStructures/NpcData.h` | 2.0K | 否 | NPC 数据 USTRUCT/UENUM | N/A | 是 |
| `GreyFogGameModeBase.h` | 941B | 否 | Game Mode 基类 | 存在 (755B) | 是 |
| `Investigation/EndingManager.h` | 2.6K | 否 | 结局管理器 | 存在 (2.6K) | 是 |
| `Investigation/InteractiveClueActor.h` | 3.1K | 否 | 可交互线索 Actor | 存在 (3.6K) | 是 |
| `Investigation/InvestigationBoardWidget.h` | 2.7K | 否 | 调查面板 Widget | 存在 (3.6K) | 是 |
| `Investigation/InvestigationComponent.h` | 3.2K | 否 | 调查状态组件 | 存在 (3.5K) | 是 |
| `NPC/GreyFogNpcCharacter.h` | 3.3K | 否 | NPC 角色类 | 存在 (1.7K) | 是 |
| `NPC/GreyFogNpcStateTree.h` | 4.1K | 否 | 确定性 NPC 状态机 | 存在 (5.4K) | 是 |
| `Subsystems/CaseGraphSubsystem.h` | 3.5K | 否 | 案件数据查询子系统 | 存在 (4.5K) | 是 |
| `Subsystems/DialogueSubsystem.h` | 2.9K | 否 | 对话管理子系统 | 存在 (2.7K) | 是 |
| `Subsystems/EventLogSubsystem.h` | 4.5K | 否 | 事件日志子系统 | 存在 (4.5K) | 是 |
| `Subsystems/GreyFogSaveSubsystem.h` | 5.5K | 否 | 存档子系统 | 存在 (5.7K) | 是 |
| `Subsystems/HypothesisSubsystem.h` | 3.4K | 否 | 假说评估子系统 | 存在 (4.2K) | 是 |
| `World/GreyFogGameState.h` | 3.1K | 否 | GameState | 存在 (1.3K) | 是 |
| `World/GreyFogPlayerController.h` | 1.6K | 否 | PlayerController | 存在 (897B) | 是 |
| `World/LocationActor.h` | 2.4K | 否 | 地点 Actor | 存在 (814B) | 是 |

---

## 三、测试模块文件

| 路径 | 大小 | 空 | 职责 | 对应 .h | 验证 |
|---|---|---|---|---|---|
| `GreyFog.Tests/GreyFogTests.h` | 301B | 否 | 测试模块头（GF_TEST_LOG 宏） | 自身 | 是 |
| `GreyFog.Tests/GreyFogTests.cpp` | 315B | 否 | 测试模块入口 | 存在 | 是 |
| `GreyFog.Tests/GreyFog.Tests.Build.cs` | 692B | 否 | 测试模块构建定义 | N/A | 是 |
| `GreyFog.Tests/AIConnectionFallbackTest.cpp` | 2.0K | 否 | AI 断线回退测试 | 无独立 .h | 是 |
| `GreyFog.Tests/AIDisabledCompletionTest.cpp` | 4.8K | 否 | AI 禁用完成测试 | 无独立 .h | 是 |
| `GreyFog.Tests/AIWritesNoDirectStateTest.cpp` | 3.6K | 否 | AI 不直接写状态测试 | 无独立 .h | 是 |
| `GreyFog.Tests/CaseDataImportTest.cpp` | 6.4K | 否 | 案件数据导入测试 | 无独立 .h | 是 |
| `GreyFog.Tests/DeterministicSeedTest.cpp` | 2.6K | 否 | 确定性种子测试 | 无独立 .h | 是 |
| `GreyFog.Tests/EndingReachabilityTest.cpp` | 6.3K | 否 | 结局可达性测试 | 无独立 .h | 是 |
| `GreyFog.Tests/FactMultiSourceTest.cpp` | 3.0K | 否 | 多源事实验证测试 | 无独立 .h | 是 |
| `GreyFog.Tests/NpcRemovalTest.cpp` | 6.7K | 否 | NPC 移除测试 | 无独立 .h | 是 |
| `GreyFog.Tests/SaveLoadConsistencyTest.cpp` | 5.5K | 否 | 存档一致性测试 | 无独立 .h | 是 |

---

## 四、配置文件

| 路径 | 大小 | 空 | 职责 |
|---|---|---|---|
| `Config/DefaultEngine.ini` | 935B | 否 | 引擎默认配置 |
| `Config/DefaultGame.ini` | 696B | 否 | 游戏默认配置 |
| `Config/DefaultInput.ini` | 917B | 否 | 输入默认配置 |

---

## 五、脚本文件

| 路径 | 大小 | 空 | 职责 | 已验证 |
|---|---|---|---|---|
| `Scripts/import_case_data.py` | 12K | 否 | Python → UE JSON 格式转换 | 是（dry-run 可用） |
| `Scripts/audit_cpp_structure.py` | 12K | 否 | C++ 结构静态审计 | 是 |

---

## 六、资产文件

| 类型 | 是否存在 | 说明 |
|---|---|---|
| `.umap` 地图文件 | 无 | 五个灰盒地图均未创建 |
| `.uasset` 资产文件 | 无 | 无 UE 编辑器生成的资产 |
| `Content/Data/*.json` | 无 | JSON 导入数据尚未写入 |

---

## 七、文件统计

| 指标 | 数值 |
|---|---|
| 总文件数 | 63 |
| 空文件数 | 0 |
| `.h` 头文件 | 30 |
| `.cpp` 源文件 | 32 |
| 配置 .ini 文件 | 3 |
| Python 脚本 | 2 |
| 地图/资产 | 0 |

---

## 八、模块 API 宏审计

- `GREYFOG_API` 使用次数：21（所有 UCLASS 类正确标注）
- `GFLOG_API` 残留：**0**
- 结论：宏修复已完成，无残留。

---

## 九、头文件-实现对应关系

- 28 个头文件，28 个对应的 .cpp 文件
- 测试文件无独立 .h（10 个 .cpp 共享 1 个 .h）
- 数据结构的 7 个头文件为纯 USTRUCT/UENUM 定义，无需 .cpp

---

## 十、依赖警告

| 文件 | 依赖 | 状态 |
|---|---|---|
| `InvestigationBoardWidget.cpp` | 调用 `GetAllHypotheses()` / `GetAllClues()` | **编译错误** — `CaseGraphSubsystem.h` 未声明这些方法 |
| `DialogueSubsystem.cpp` | 使用 `FFG_DialogueResponse` 字段 | **编译错误** — 字段名与 `DialogueData.h` 定义不匹配 |
| 所有 .h 文件 | UE 标准头文件 (`CoreMinimal.h` 等) | 无 UE5.8 SDK，无法编译验证 |

---

*注：本清单基于磁盘实际文件内容，未引用之前的 AI 会话假定。标有"编译错误"的问题需要在 UE5.8 环境中确认和修复。*
