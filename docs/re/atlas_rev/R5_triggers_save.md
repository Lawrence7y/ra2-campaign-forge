# R5 交付 · atlas 新章锚定补丁块（§14 触发器脚本运行时 / §15 存档块与序列化全景）

> **执行方**：DSH 子代理（Agent Teams 成员 atlas-r5-triggers）｜**共享任务**：task-7
> **写作用域（声明）**：docs/re/atlas_rev/R5_triggers_save.md、out/re_work/atlas_rev/R5/**
> **基线二进制（只读）**：ra2youli/gamemd.exe（MD5 4f37486e5b0dbe2ae5f45aeee0f98367，4,825,360 B），ImageBase 0x400000，FileOffset = VA − 0x400000
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **atlas 快照**：docs/re/ARCHITECTURE_ATLAS.md = 2002 行（本批未改一个字节；行号口径以该快照为准）
> **机器可复算断言**：out/re_work/atlas_rev/R5/claims_R5.txt（**696 条**，tools/audit_bytes.py 全 OK）
> **纪律**：本文件**只产出补丁块**；ARCHITECTURE_ATLAS.md 由 Lead 唯一写入。未真机运行的验证一律 [待实测]；静态复算一律 [实证]（VA+FileOffset+原始字节+反汇编可复算）。
> **证据等级**：[实证] = VA + 原始字节 + 反汇编（可 audit_bytes 复算）｜[推演] = 由相邻实证按 x86/MSVC6 惯例推导｜[待实测] = 需真机运行。

---

## 一、锚定补丁块（共 3 块）

| 补丁 | 动作 | 目标锚点（实跑 grep 命中行号，唯一） | 内容 |
|---|---|---|---|
| PATCH-R5-01 | APPEND_SECTION | **L1981**（唯一，见下） | 新章 §14 触发器脚本运行时 |
| PATCH-R5-02 | APPEND_SECTION | **L1981**（唯一，同锚点） | 新章 §15 存档块与序列化全景 |
| PATCH-R5-03 | ERRATUM | **L1926**（唯一，见下） | §12.2 红线框「每帧恰消费 2 次」加限定语（RNG 消费面） |

**锚点实跑 grep（原文）**

```text
> python out\re_work\atlas_rev\R5\scratch\anchors.py
PATTERN '## 附录 DA1' -> lines [1981] (count=1)
   L1981  first40='## 附录 DA1 · 勘误登记（雷达挂钩地址与 G-10 覆盖，2026-09'  full='## 附录 DA1 · 勘误登记（雷达挂钩地址与 G-10 覆盖，2026-09-27）'
PATTERN '每帧恰消费 2 次' -> lines [1926] (count=1)
   L1926  first40=' │   - 局内唯一随机数 (ScenarioClass::Random 0x'  full=' │   - 局内唯一随机数 (ScenarioClass::Random 0x00A8B230+0x218 每帧恰消费 2 次) │'
```
> 说明：两张新章**同一锚点**（L1981）是任务卡指定口径（Lead 按流号顺序插入，插入后行号漂移由 Lead 处理）。
> 本文件**不含**任何修改「## 目录」的补丁块（TOC 由 Lead 统一重建）。

---

### PATCH-R5-01 新章 §14 触发器脚本运行时（类/虚表拓扑 + 每帧节拍 + 派发表三联 + PRNG 契约 + 生命周期）

- **目标锚点**: **L1981**｜该行前 40 字符原文：`## 附录 DA1 · 勘误登记（雷达挂钩地址与 G-1`（实跑 grep 唯一命中 L1981）
- **动作**: APPEND_SECTION
- **现状问题**: atlas §0–§12 覆盖渲染/迷雾/机动/索敌/AI/音频/超武/时钟/联机/内存十大子系统，**但没有触发器（Trigger/Tag）系统专章**。触发器是「地图作者可见语义」与「联机分叉第一源」的交汇点：它的每帧遍历位置、求值顺序、随机数消费面、动作副作用风险面在 atlas 中完全缺失（§0 拓扑图无对应节点，§9 只在 Team 节点里出现一个 AITrigger 名字）。缺章导致 atlas 无法回答三个产品级问题：①改触发器动作会不会分叉；②触发器在每逻辑帧的哪个位置被求值；③触发器与存档/CRC 的契约边界在哪。
- **替换文本**:

````markdown
## 14. §14 触发器脚本运行时 (Trigger Script Runtime)

> **章性质**：架构级专章（类/虚表拓扑 + 关键 VA + 跨子系统契约 + 未闭环项），不是源报告搬运。
> **来源（只读引用）**：`docs/re/trigger_system_manifest.md`（事件/动作全表）、`docs/re/trigger_runtime_deep_dive.md`（运行时语义与确定性）；字节断言库 `out/re_work/triggers/claims.txt`（77 条）、`out/re_work/triggers_deep/claims.txt`（174 条）、`out/re_work/da2/claims.txt`（28 条）——三库全部条目已由 R5 独立复算（0 mismatch），并入 `out/re_work/atlas_rev/R5/claims_R5.txt`。
> **本章新增实证（R5 独立复算，非搬运）**：6 个触发器类虚表 + 1 个容器虚表由 **MSVC6 RTTI 链（vtable−4 → CompleteObjectLocator+0xC → TypeDescriptor+8）直接解出装饰类名**；`0x8B40C8` 每帧向量的容器类型解出为 `.?AV?$DynamicVectorClass@PAVTagClass@@@@`；延迟析构队列的 grow 路径指令与源报告注解**不一致**（见本节末「R5 勘误登记」E-R5-2）。

### 14.1 结论速览

| # | 结论 | 等级 |
|---|---|---|
| **C1** | 每逻辑帧**唯一**遍历触发器系统的位置是 `LogicClass` 轮询器 `0x55AFB0`（`MainLogicFrame 0x55D360` 内 `0x55DC9E`，全镜像唯一调用点，位于 `0x55DBCD` 条件块汇合点之后 ⇒ 无条件），它遍历的是**每帧 Tag 名单向量 `0x8B40C8`**（容器经 RTTI 定名为 `DynamicVectorClass<TagClass*>`），**不遍历触发器对象**。 | [实证] |
| **C2** | 触发器对象本身**不在任何每帧循环里**：条件求值唯一入口 `TriggerClass::RegisterEvent 0x7264C0` 全镜像只有 1 个调用点（`0x6E5414`，在 `TagClass::RaiseEvent` 内）；触发器是纯事件驱动。 | [实证] |
| **C3** | 求值顺序三层全为**插入序**：每帧名单 = `TagTypeClass::Array` 下标升序（任务初始化 `0x684E2F` 尾接建立）；Tag→Trigger 为**头插**（LIFO）；Trigger→Event/Action 为 INI 链序。全链路**无任何按指针值/地址排序的指令**（负证）。 | [实证] |
| **C4** | 局内 PRNG 实例 = `ScenarioClass::Random`（`[0xA8B230]+0x218`）。触发器子系统对它的消费点**恰好 4 个函数 / 9 条指令**，事件判定链 `0x71E940–0x71F700` **零消费**；另有帧 CRC `0x64DAB0` 每次消费 1 次（`0x64DE3F`）。 | [实证] |
| **C5** | 条件侧 PRNG **不是「每次判定抽一次」**，而是「计时器装填瞬间抽一次」：`RandomDelay(0x33)` 装填 = `RandomRanged(0,arg)`，时长 `15*((arg>>1)+rand)` 逻辑帧。 | [实证] |
| **C6** | 三张派发表互不相同：Action **145** 项（`TActionClass::Execute 0x6DD8B0`，跳表 `0x6DFDEC`）、Event **49 槽 / 12 目标**（`TEventClass::HasOccured 0x71E940`，`0x71F218` + 选择表 `0x71F248`）、队伍脚本动作 **65** 项（`TeamClass::AI 0x6E9050`，跳表 `0x6E9F74`）。 | [实证] |
| **C7** | `Destroyed` 只是标记位；真正释放走**帧尾统一抽干**的延迟析构队列 `0xB0F698`（`0x725C70`，`MainLogicFrame` 尾部 `0x55DE9F`）——这是多端销毁时机一致性的保证点。 | [实证] |
| **C8** | `AITrigger 0x6F0AB0` 与 Tag/Trigger 体系**零交叉**（无共同数组/链表/事件号），但它**共享同一条局内 RNG 流**：门控计时器 `TeamDelayTimer` 若多端不一致 ⇒ 抽数次数不同 ⇒ 立即分叉。 | [实证]（门控周期 [推演]） |
| **C9** | 145 个动作在 SP/MP 走**同一张表、无 MP 门控**（函数体内无 `[0xA8B238]` 引用）；真正的分叉第一源是**事件判定输入**（依赖本机交互的 kind）与**动作副作用**。 | [实证] + [推演] |
| **C10** | 触发器的存档契约与 §15 强耦合：每帧 Tag 向量整体进档（4 B/项）并在载入时**按原序重建**；`CurrentFrame` 同批进档；`TriggerClass` 事件位图 `OccuredEvents@+0x40` 的**位序 = 事件链位次**，因此 `TriggerClass` 的 Save/Load 必须严格保持链序。 | [实证] |

### 14.2 类与虚表拓扑（RTTI 定名，[实证]）

RTTI 复算方法：`COL = [vtable−4]`；`TypeDescriptor = [COL+0xC]`；装饰类名 = `ASCIIZ at TD+8`。下表「类」列**由该链直接解出**（不是 YRpp 名称对齐推断），可用 `out/re_work/atlas_rev/R5/claims_R5.txt` 复算。

| 类 | 主虚表 VA | vtable−4 = COL | TypeDescriptor 名 | 实例尺寸 | 全局容器（数组） | 关键证据 |
|---|---|---|---|---|---|---|
| `TagClass` | `0x7F44E0` | `0x80BBA0` | `.?AVTagClass`` | `0x38` | `TagClass::Array 0xB0E720` | ctor 写 vtable `0x6E4F69 = C7 07 E0 44 7F 00`；`operator new(0x38)` = `0x6E52C5 = 6A 38` |
| `TagTypeClass` | `0x7F45C4` | `0x80BCF0` | `.?AVTagTypeClass`` | — | `TagTypeClass::Array 0xB0E780` | vtable 槽位 RTTI 链 |
| `TriggerClass` | `0x7F5858` | `0x80C968` | `.?AVTriggerClass`` | `0x48` | `TriggerClass::Array 0xA8EAE8`（另有 `0xB0F670 / 0xB0F708` 两个同型向量） | `Size()` = `0x726930 = B8 48 00 00 00 C3` |
| `TriggerTypeClass` | `0x7F5904` | `0x80CA20` | `.?AVTriggerTypeClass`` | — | `TriggerTypeClass::Array 0x8B4178` | vtable 槽位 RTTI 链 |
| `TEventClass` | `0x7F5578` | `0x80C5E0` | `.?AVTEventClass`` | `0x94`（同族 `TActionClass::Size`） | 挂在 `TriggerTypeClass+0xAC` 链表 | `0x6E4630 = B8 94 00 00 00 C3` |
| `TActionClass` | `0x7F443C` | `0x80BAF0` | `.?AVTActionClass`` | `0x94` | 挂在 `TriggerTypeClass+0xB0` 链表 | RTTI 链 + `0x6E4630` |
| `DynamicVectorClass<TagClass*>` | `0x7EA5A4` | `0x8024B0` | `.?AV?$DynamicVectorClass@PAVTagClass@@@@` | 容器 | **每帧轮询名单 `0x8B40C8`** | 容器类型由该 RTTI 直接定名 |

> **三个「每帧上下文」向量**：`0x8B40C8`（自求值/计时器名单，元素 `TagClass*`）、`0x8B41A8`（`AnyEvent(0x08)/ZoneEntryBy(0x18)` 专用名单）、`0xB0E720`（全部 Tag 实例，仅创建/销毁用）。注册判据是 `TagTypeClass::GetFlags()` 的位：bit2 → `0x8B41A8`，**bit4（0x10）→ `0x8B40C8`**（`0x684D66` / `0x684DCF`）。
> **游戏契约 [推演]**：`GetFlags()` 未置 bit4 的 Tag，在任务初始化时**连 `TagClass` 实例都不会被创建**（`GetInstance` 仅在对应位命中时调用）⇒ 这类 Tag 永远不进每帧名单；若它同时声明了 `RandomDelay/ElapsedTime`，该事件在运行时**不会按帧求值**。建议列入地图制作告警清单。

### 14.3 每逻辑帧节拍（[实证]）

```text
MainLogicFrame 0x55D360    (每逻辑帧；CurrentFrame++ 唯一在 0x55DE73)
  ...
  0x55DC99  mov ecx,0x87F778          ; this = LogicClass::Logics（YRpp MapClass.h）
  0x55DC9E  call 0x55AFB0             ; ★ 全镜像唯一调用点（在 0x55DBCD 条件块汇合点之后 ⇒ 无条件）
  ...
  0x55DE9F  call 0x725C70             ; 帧尾：延迟析构队列抽干
```
轮询器主体：`0x55AFDB` 归零迭代游标 `[0xA83CDC]` → `0x55AFE6 = 8B 0D CC 40 8B 00`（`Items = [0x8B40CC]`）→ `0x55AFEC = 8B 34 81`（`esi = Items[i]`，**下标升序**）→ `0x55B169 = 8B 0D D8 40 8B 00`（读 `Count`）→ 每 Tag 依序抛 **10 个自求值事件**。

| 序 | EventKind | 名称 | 前置锁存位（读 `ScenarioClass*`） | 调用点 VA |
|---|---|---|---|---|
| 1 | `0x32` | PickupCrate_any | `[+0x34BE] != 0` | `0x55B00A` |
| 2 | `0x1B` | GlobalSet | `[+0x34AA] != 0` | `0x55B037` |
| 3 | `0x1C` | GlobalCleared | 同上 | `0x55B055` |
| 4 | `0x24` | LocalSet | 同上 | `0x55B073` |
| 5 | `0x25` | LocalCleared | 同上 | `0x55B090` |
| 6 | `0x2D` | AmbientLightBelow | `[+0x34AB] != 0` | `0x55B0BE` |
| 7 | `0x2E` | AmbientLightAbove | 同上 | `0x55B0DC` |
| 8 | `0x0D` | ElapsedTime | 无条件 | `0x55B0F5` |
| 9 | `0x33` | RandomDelay | 无条件 | `0x55B10F` |
| 10 | `0x0E` | MissionTimerExpired | 任务计时器 `[Scenario+0x11E8]` 到期 | `0x55B159` |

- **两个「每帧边界」语义**：轮询器**早于** `CurrentFrame++`（`0x55DE73`），故抛事件时 `CurrentFrame` 仍是本帧前的值；而 `ResetTimers` 读 `[0xA8ED84]` —— 二者共同决定计时器相位。 [实证]
- **每 Tag 的短路语义**：任一事件在该 Tag 上「至少执行了一个动作」即跳到下一 Tag（`0x55B011 = 0F 85 47 01 00 00`），**不是**中止整帧遍历 ⇒ 同一帧多 Tag 各自触发是允许且必然按向量序发生。 [实证]
- **第二个每帧入口**：`TeamClass::AI` 内 `0x6E92F3` / `0x6EA4B1` 两处遍历**同一** `0x8B40C8` 向量并抛 `0x17 TeamLeavesMap`（`0x6E9304` / `0x6EA4C0`）。 [实证]
- **10 个 kind 与 `TEventClass::GetFlags` bit `0x10`（`0x71F6F1 = 83 CE 10`）逐项一致**（差集 `0x08/0x2F/0x3C/0x3D` 的抛出点未闭环，见 14.11 U-5）。 [实证]

### 14.4 事件驱动漏斗与「唯一入口」表（[实证]）

| 函数 | 直呼调用点数 | 唯一/主要调用点 | 架构含义 |
|---|---|---|---|
| `TagClass::RaiseEvent 0x6E53A0` | **73**（聚簇：轮询器 10、步兵 9、载具 5、飞行器 15、建筑 1、队伍 2、世界/杂项 41） | 多个 | **全系统把「世界上发生了什么」送进触发器系统的唯一闸门** |
| `TriggerClass::RegisterEvent 0x7264C0` | **1** | `0x6E5414` | 条件求值唯一入口（唯一挂钩点） |
| `TEventClass::HasOccured 0x71E940` | **1** | `0x726540` | 62 条件分支唯一入口 |
| `TriggerClass::FireActions 0x7265C0` | **5** | `0x6E5439 / 0x6E5450 / 0x6E546D` + 动作 `0x16 ForceTrigger` 体内 + 辅助簇 | 动作执行入口极少 |
| `TActionClass::Execute 0x6DD8B0` | **1** | `0x726605` | 145 项动作唯一入口 |
| `TriggerClass::ResetTimers 0x726400` | **5** | ctor `0x7260E7` / `0x7263BB` / `0x7263EB` / `0x7265A4` / `0x7268F4` | **PRNG 消费点集合**（见 14.7） |
| `TriggerClass::Destroy 0x726720` | **4** | `0x6DF07D`（动作 `0x0C`）/ `0x6E2A3A` / `0x6E5457` / `0x6E5474` | 销毁入口 |

`RaiseEvent` 前置门（逐条字节）：`0x6E53A0 = 51 A0 6B ED A8 00`（`ArmageddonMode` 置位即整条返回 false）、`0x6E53BC`（`IsExecuting@+0x35` 重入保护）、`0x6E53C7`（`Destroyed@+0x34`）、`0x6E53D2 = 8B 45 24`（`Type==0`）；随后按 `TagTypeClass+0x9C`（Persistence）分派：`0x6E5408 = 83 FA 02 0F 94 C2` ⇒ `persistent := (Persistence==2)`（0 = FireActions+Destroy；1 = 视 `InstanceCount`；2 = 仅 FireActions、永不销毁）。

`RegisterEvent` 内部关键字节：`0x7264C4 = 8A 46 44 84 C0`（**`Enabled@+0x44` 必须非 0 才继续**）、`0x7264CF = 8A 46 30 84 C0`（**`Destroyed@+0x30` 必须为 0**）、`0x726501 = 8B 46 40`（`OccuredEvents` 位图）、`0x72650B = D3 E5`（`1<<eventIndex`，位序 = 事件在链表中的位次）、`0x726540 = E8 FB 83 FF FF`（`HasOccured`）、`0x726582 = 09 6E 40`（置位）、`0x7265A4 = E8 57 FE FF FF`（`ResetTimers`）。

> **勘误（相对 docs/re/trigger_system_manifest.md §1.1 旧表述，源文档已原地勘误）**：原写「`TriggerClass+0x44`（已过期）与 `+0x30`（已禁用）任一为真则跳过」——**字段名与方向均错位**；`+0x44 = Enabled`（要求非 0）、`+0x30 = Destroyed`（要求为 0）。atlas 引用时应采信本节口径（源侧依据：`docs/re/trigger_system_manifest.md:57-67` DA2-T1 块；`out/re_work/da2/claims.txt` 28 条，R5 复算 0 mismatch）。

### 14.5 三张派发表（互不相同，勿混）（[实证]）

| 表 | 所有者 / 入口 | 跳转表 VA | 表项数 | 索引语义 | 表长自证字节 |
|---|---|---|---|---|---|
| **A. 触发器动作** | `TActionClass::Execute 0x6DD8B0` | `0x6DFDEC` | **145** | `ActionKind−1`，`1..0x91` | `0x6DD8DB = 81 FA 90 00 00 00`；表尾 `0x6E0030 = B0 01 C2 10` ⇒ 表止于 `0x6E002F` |
| **B. 触发器事件** | `TEventClass::HasOccured 0x71E940` | `0x71F218`（12 目标）+ 选择表 `0x71F248`（49 B） | **49 槽 / 12 目标** | `EventKind−0x0D`，`0x0D..0x3D` | `0x71E950 = 8D 41 F3 83 F8 30 0F 87`；`0x71E964 = FF 24 95 18 F2 71 00` |
| **C. 队伍脚本动作** | `TeamClass::AI 0x6E9050` | `0x6E9F74` | **65** | 脚本动作号 `0..0x40`（**不是** TriggerAction） | `0x6E944B = 83 F8 40`；`0x6E945B = FF 24 85 74 9F 6E 00` |

- **4 个「声明了但空实现」的动作**：`AllowWin(0x0F)` → `0x6DFDDD`（仅尾声）；`ChangeZoomLevel(0x27) / ActivateFirestorm(0x5C) / DeactivateFirestorm(0x5D)` → `0x6DFDDB = B0 01`（`mov al,1` 后返回）。其他文档/工具若把它们当生效动作（如「AllowWin 开启胜利通道」）应改标**本作未实现**。 [实证]
- **145 项 → 143 个不同目标**（唯一重复 = 上述空实现体 `0x6DFDDB` 被 3 项共用）；**动作主体是内联副本，hook YRpp slave 不一定生效**（同逻辑常有两份死副本，如动作 `0x62` 的 slave `0x6E1780` 全镜像 0 个直呼点）。 [实证]
- **名称来源口径**：本体**无枚举名字表**（`TActionClass::LoadFromINI 0x6DD5B0` 解析的是数字）；「名称」列取自 YRpp 枚举（[推演/命名]），编号/派发入口/参数列才是 [实证]。

### 14.6 求值顺序与锁步确定性（[实证]）

| 层 | 数据结构 | 插入操作 | 求值序 |
|---|---|---|---|
| 每帧 Tag 名单 | `DynamicVectorClass<TagClass*> 0x8B40C8` | 尾接 `0x684E2F = 89 3C 81`（`Items[Count]=tag`；`0x684E23` 写回 `Count@0x8B40D8`） | **下标升序 = TagType 注册序** |
| Tag → Trigger | 单链表 `TagClass+0x28` | **头插** `0x6E55C0 = 8B 44 24 04 8B 51 28 89 50 28` | **创建序逆序（LIFO）** |
| Trigger → Event/Action | 单链表 `TriggerClass+0x28` 节点 | 尾接（INI 序） | **INI 声明序** |
| 每帧事件种类 | 硬编码指令序列 | 固定 10 步 | **固定序 `0x32→…→0x0E`** |

- **无地址依赖（负证）**：`RaiseEvent / RegisterEvent / FireActions` + 轮询器四段代码的全部遍历都是「向量下标 +1」或「链表 `[x+0x28]` 前进」，**无任何比较两个条目地址大小决定次序**的指令。 [实证]
- **迭代期安全变更**：摘除时按需回退游标 `[0xA83CDC]`（`0x6E4FD0 = 8B 0D DC 3C A8 00 3B C8 7C 14 8B C1 48 A3`），保证不漏求值。 [实证]
- **存档还原**：`0x67FB8A = 8B 15 CC 40 8B 00` → `0x67FB93`（`Count++`）→ `0x67FB9D = 89 0C 82`（尾接）⇒ **按存档原序重建，不按 TagType 重排**。 [实证]
- **加载序未闭环**：`TagTypeClass::Array` 的加载顺序是否严格等于 INI 文本序，静态不可判定 ⇒ [待实测]（见 14.11 U-1）。

### 14.7 PRNG 消费面（联机红线）（[实证]）

实例：**局内** `ScenarioClass::Random` = `[0xA8B230]+0x218`（触发器子系统**不用** `Randomizer::Global 0x886B88`）。

| # | 函数 / 体内联 | 消费指令 VA | 语义 | 次/调用 |
|---|---|---|---|---|
| T1 | `TriggerClass::ResetTimers 0x726400` | `0x726464 = 8D 88 18 02 00 00` / `0x72646A = E8 71 63 F3 FF` | `RandomRanged(0,arg)` 装填 `RandomDelay` | 1 / 每个 RandomDelay 事件 |
| T2 | 动作 `0x3A MeteorShower`（块 `0x6DF223` → 辅助 `0x6E2C40`） | `0x6E2CEB` / `0x6E2D4E` / `0x6E2D5A` / `0x6E2DB0` | 流星落点/数量 | **4** |
| T3 | 动作 `0x62 PlaySoundEffectRandom`（块 `0x6DE7A5`） | `0x6DE809` / `0x6DE80F = E8 CC DF F7 FF` | `RandomRanged(0,Value−1)` | 1 |
| T3′ | YRpp slave `0x6E1780`（**同体死副本，0 直呼点**） | `0x6E17D8` / `0x6E17DE` | 同上；**hook slave 不会生效** | 1 |
| T4 | `AITrigger 0x6F0AB0` | `0x6F0AFB` / `0x6F0B01 = E8 DA BC F6 FF` | `RandomRanged(1,100)` 概率门（`0x6F0B06` 与 `[edi+0x565C]` 比较） | 1 |
| T5 | `AITrigger` 姊妹 `0x6F0C9C` | `0x6F0CE8` / `0x6F0CEE` | 加权挑选 | 1 |
| T6 | 帧 CRC `0x64DAB0` | `0x64DE39` / `0x64DE3F = E8 3C E9 00 00` | 取 1 随机数折进 `CurrentFrameCRC` | 1 / 每次 CRC |

- **条件侧 = 「装填瞬间抽一次」**：`RandomDelay(0x33)` 时长 = `15*((arg>>1)+RandomRanged(0,arg))` 逻辑帧（`0x72648B` / `0x726491` 的 `*3 *5` = 每秒 15 逻辑帧；`ElapsedTime(0x0D)` 同处共享该乘法序列 ⇒ `Timer.Duration` 单位 = 逻辑帧）。重新装填（**再次消费**）的条件是「该 Trigger 的全部事件已发生 且 `persistent==1`」（`RegisterEvent` 尾 `0x726591` / `0x7265A4`）；其余 4 个 `ResetTimers` 调用点 = 构造 / Enable / `NotifyGlobalChanged` / `NotifyLocalChanged`。 [实证]
- **「每帧几次」的准确表述**：atlas §12.2〔ASM-FIX2-1〕确认**帧 CRC 路径**每逻辑帧 2 次消费；本节进一步给出触发器侧为**额外且条件性**的消费（T1–T6 全部依附于具体事件/动作/门控）⇒ 全帧总消费量**不是恒定 2**，而是 `2 + Σ(触发器侧条件消费)`（代码面 [实证]；运行期是否命中 [待实测]，见 U-9）。
- **对 docs/re/trigger_system_manifest.md §9 的补强**：动作 `0x62` 由「绿」升「黄」成立（消耗同步 RNG）；`0x63 PlaySoundEffectAtWaypoint` 内联体与 `0x6E1830` 路径**不消费 RNG**（「绿」成立）；**建议为动作 `0x3A` 补注「RNG×4」**——联机改图若削减流星雨次数会立即改变 RNG 序列。 [实证]
- **CRC 与 RNG 的准确表述**：CRC **消费**一次 RNG 输出并折进累加器（`0x64DE44 = 8B 15 FC 51 AC 00`、`0x64DE4F = 8D 0C 51`），**不读取** RNG 内部状态（`Table/Next1/Next2` 无访存）⇒「RNG 状态分叉」会经下一次 CRC 立即显形（[推演]）。 [实证] + [推演]

### 14.8 生命周期、Destroyed 与延迟析构队列（[实证]）

| 阶段 | 入口 | 字节锚点 |
|---|---|---|
| Tag 加载/实例化 | `TagClass::GetInstance 0x6E52A0` | 线性扫 `TagClass::Array` 比较 `[tag+0x24]==pType`；未命中 `operator new(0x38)`（`0x6E52C5 = 6A 38`）→ ctor `0x6E4DE0` |
| Trigger 构造 | `TriggerClass::ctor 0x725FA0` | `0x725FB8`（`Destroyed@+0x30=0`）、`0x725FBB`（`Timer.Start=CurrentFrame`）、`0x725FCA = C6 46 44 01`（`Enabled=1`）、`0x7260DD`（尾接 `TriggerClass::Array`）、`0x7260E7`（★ **构造即可能消费 PRNG**：含 RandomDelay 则调 `ResetTimers`） |
| 触发后置位/销毁 | `TagClass::Destroy 0x6E5230` | `0x6E5233 = C6 46 34 01`（`Destroyed@+0x34=1`）→ 尾接进延迟队列（`0x6E5272` 读 `Count@0xB0F6A8`、`0x6E527B` 写回自增） |
| 队列增长路径 | `TagClass::Destroy` 内 | `0x6E5266 = B9 98 F6 B0 00`（`ecx = 0xB0F698` = 队列实例基址）、`0x6E526B = FF 50 08`（虚调用 `[eax+8]`，`eax = [0xB0F698]` = **队列 vtable 指针**）——注意 `0x6E525E = A1 98 F6 B0 00` 取的是 **vtable**，不是 Count（见 [3] 勘误 E-R5-2） |
| 帧尾统一抽干 | `0x725C70` | `MainLogicFrame` 尾部 `0x55DE9F = E8 CC 7D 1C 00`；遍历 → `0x725C8F = FF 52 44`（`IsDead()`）→ `0x725CAA = FF 52 10`（`RemoveItem`）→ 释放 |
| Trigger 控制面 | `0x7268F0`（Enable）/ `0x726900`（Disable）/ `0x7263A0` / `0x7263D0` | `+0x44` 直写 + 变量变更推送侧（`GlobalSet/GlobalCleared/LocalSet/LocalCleared` 的推送方） |
| 持久化 | `TriggerClass` IPersistStream `0x726860` / `0x7268D0`；`TagClass` `0x6E5730` / `0x6E57A0` | 读回后重置 4 个 vtable 指针 |

> **架构要点**：销毁**不是就地 `delete`**，而是「标记 + 排队 + 帧尾抽干」。这是多端销毁时机一致性的结构保证，也是任何「在触发器回调里立即释放对象」的改动会破坏的契约（⇒ 联机风险）。

### 14.9 AITrigger 与普通触发器（[实证]）

| 维度 | 普通触发器（Tag/Trigger） | AITrigger（`0x6F0AB0`） |
|---|---|---|
| 宿主 | `TagClass→TriggerClass→TEventClass/TActionClass` 链 | `AITriggerTypeClass::Array 0xA8B200` |
| 直呼点 | `RaiseEvent` 73 点 | **仅 2 点**：`0x4F8A6A`、`0x4FA220`（均在 `HouseClass` AI 簇 `0x4F8440`） |
| 节拍 | 每逻辑帧（10 自求值事件）+ 对象事件冒泡 | `TeamDelayTimer` 门控、**非每帧**（[推演]，依据门控点与直呼点相邻） |
| 随机 | 仅 `RandomDelay`（**装填时** 1 次） | **每次评估 1 次** `RandomRanged(1,100)`（+姊妹 1 次） |
| 判据 | 62 种 EventKind 逐 kind 编译进 4 层跳表 | 房级 Team 计数 / 上限比较 + 概率门 |
| 进每帧 Tag 名单 | 是（若含 bit`0x10` 事件） | **否**（零交叉：无共同数组/链表/事件号） |
| 联机含义 | 判定输入面（本机交互类 kind）为首要风险 | **门控计时器多端必须一致**，否则 RNG 抽数次数不同 ⇒ 立即分叉 |

### 14.10 与其它子系统的契约（点名）

| 对端 | 契约 | 证据等级 |
|---|---|---|
| **§8 帧时钟循环** | 轮询器早于 `CurrentFrame++`；延迟队列在 `MainLogicFrame` 尾部抽干 ⇒ 触发器求值与「帧递增/收尸」有固定相位 | [实证] |
| **§6 音频引擎与 EVA** | 动作 `0x15 PlaySpeech` 是「触发器 → EVA」**唯一**动作路径（`0x6DE90C = BA 02 00 00 00` `mode=2` → `0x6DE911` `call 0x752480`，EVA 专属流）；全局性 EVA（任务计时器到期）在轮询器尾部，表现侧与动作侧分离 | [实证]（`0x752480` 身份引用 §6） |
| **§9 联机确定性与帧校验** | 触发器**不产生 `NetworkEvent`**（触发器代码区 0 处 `FillEvent_*` 调用，负证）⇒ 判定链是**本地求值**；风险面 = 事件输入 + 动作副作用 + RNG 消费 | [实证] |
| **§5 战术 AI 与小队调度** | AITrigger 由 `HouseClass` AI 簇调用，与 Team 计数/上限比较耦合（见 14.9） | [实证] + [推演] |
| **§15 存档块与序列化** | 每帧名单向量整体进档 / 原序还原；`CurrentFrame` 同批进档；`OccuredEvents` 位图依赖链序；RNG 状态（`Scenario+0x218`）属**禁改**面 | [实证] |
| **§11 速查表** | 本类族 6 个虚表 + `DynamicVectorClass<TagClass*>` 容器虚表 + 两处 `Size()` 应并入 §11（见 14.12） | [实证] |

### 14.11 未闭环项

| # | 未闭环项 | 为什么静态闭不了 | 下一步取证 | 级别 |
|---|---|---|---|---|
| U-1 | `TagTypeClass::Array` 加载序是否逐字等于 INI 文本序 | 未反汇编解析器的键枚举循环 | 反汇编 `0x6E5ED0` 全函数；真机双端 dump 前 N 项比对 | P1 |
| U-2 | 每帧 `location` 全局 `0xABCCD8` 的有效写入方 | 间接写点未穷尽 | 取址型指令扫描（`8D 0D/8D 15/B8` 形态）+ 硬件写断 | P2 |
| U-3 | `0x722xxx` 簇 5 处 RNG 消费点（`0x7224AE / 0x722AF0 / 0x722F6A / 0x722FF2 / 0x7235A0`）的上游归属 | 其所在函数未被本次回溯。**R5 新增负证**：`Load_Core` 的 4 个家族外读取器（`0x722240 / 0x722D00 / 0x72AD20 / 0x72DEF0`）函数体**RNG 零命中** ⇒ 这 5 点**不在**读档直呼链上 | 对这 5 点的函数起点做 `who`，回溯首个属于已知表的调用者 | P1 |
| U-4 | 延迟析构队列 `0xB0F698` 与游标 `0xA83CDC` 是否进存档 | 未枚举完 `0x67F7E0–0x67F9C0` 全部 Write 实参 | 枚举区间内所有 `call [vtable+0x10]` 实参，与 §15 的 S-1 序列做差集 | P2 |
| U-5 | `EventKind 0x08 / 0x2F / 0x3C / 0x3D` 的抛出点 | 只钉住轮询器 10 kind + `0x17` 两点 | 以「bit`0x10` 集合 ∖ 已闭环集合」为差集，机械筛 73 个 `call 0x6E53A0` 点的前置 `push imm` | P2 |
| U-6 | `RaiseEvent` 尾部宿主字段 `[edi+0x34]` 与 `call 0x5F5B50` 语义 | 每帧路径 `pTagOwner` 恒为 NULL | 反汇编 `0x5F5B50` + `ObjectClass/TechnoClass` 布局核对 | P2 |
| U-7 | 锁存位 `[Scenario+0x34AA / 0x34AB / 0x34BE]` 置位来源与 MP 确定性 | 本批只证「轮询器读它们」 | 扫全镜像写点（含经 `ecx=[0xA8B230]` 的间接寻址），判定是否含本机输入路径 | **P0（联机风险面）** |
| U-8 | AITrigger 门控 `TeamDelayTimer` 精确周期与多端一致性 | 未反汇编门控比较 | 与 `house_team_ai_update.md` 交叉 + 反汇编 `0x4F8A00` 附近比较 | P1 |
| U-9 | 触发器「每帧总 RNG 消费量」的真机分布 | 需运行期计数 | 真机 hook `0x65C780 / 0x65C7E0` 计数 + 与 CRC 帧号对拍 | **P0（联机对拍门禁）** |

### 14.12 关键 VA 速查表（供 Lead 并入 §11）

| VA | 名称 / 职责 | 证据等级 | 来源 |
|---|---|---|---|
| `0x7F44E0` | `TagClass` 主虚表（RTTI `.?AVTagClass``） | [实证] | claims_R5 `0x7F44E0` |
| `0x7F45C4` | `TagTypeClass` 主虚表 | [实证] | claims_R5 `0x7F45C4` |
| `0x7F5858` | `TriggerClass` 主虚表（Size `0x48`） | [实证] | claims_R5 `0x7F5858` / `0x726930` |
| `0x7F5904` | `TriggerTypeClass` 主虚表 | [实证] | claims_R5 `0x7F5904` |
| `0x7F5578` | `TEventClass` 主虚表 | [实证] | claims_R5 `0x7F5578` |
| `0x7F443C` | `TActionClass` 主虚表（Size `0x94`） | [实证] | claims_R5 `0x7F443C` / `0x6E4630` |
| `0x7EA5A4` | `DynamicVectorClass<TagClass*>` 虚表（每帧名单 `0x8B40C8` 的容器类型） | [实证] | claims_R5 `0x7EA5A4`（RTTI 链） |
| `0x8B40C8` | **每帧 Tag 名单**（Items `0x8B40CC` / Count `0x8B40D8`） | [实证]（.bss 无文件字节，仅指令级可断言） | claims_R5 `0x55AFE6` / `0x55B169` |
| `0x55AFB0` | 每逻辑帧唯一轮询器（10 个自求值事件） | [实证] | claims_R5 `0x55DC9E` / `0x55AFB0` |
| `0x6E53A0` | `TagClass::RaiseEvent`（世界事件唯一闸门，73 调用点） | [实证] | claims_R5 `0x6E53A0` / `0x6E5414` |
| `0x7264C0` | `TriggerClass::RegisterEvent`（条件求值唯一入口） | [实证] | claims_R5 `0x7264C0` / `0x7264C4` |
| `0x71E940` | `TEventClass::HasOccured`（62 条件唯一入口） | [实证] | claims_R5 `0x71E940` / `0x726540` |
| `0x6DD8B0` | `TActionClass::Execute`（145 项唯一入口） | [实证] | claims_R5 `0x6DD8B0` / `0x726605` |
| `0x6DFDEC` | Action 跳表（145 项） | [实证] | claims_R5 `0x6DD8DB` / `0x6E0030` |
| `0x71F218` | Event 一级跳表（12 目标）+ 选择表 `0x71F248` | [实证] | claims_R5 `0x71E950` / `0x71F248` |
| `0x6E9F74` | 队伍脚本动作跳表（65 项） | [实证] | claims_R5 `0x6E944B` / `0x6EA038` |
| `0x726400` | `TriggerClass::ResetTimers`（PRNG 消费点集合） | [实证] | claims_R5 `0x72646A` |
| `0x7265C0` | `TriggerClass::FireActions`（动作执行入口） | [实证] | claims_R5 `0x726605` |
| `0x725C70` | 帧尾延迟析构队列抽干（由 `0x55DE9F` 调用） | [实证] | claims_R5 `0x55DE9F` / `0x725C70` |
| `0x6F0AB0` | `AITrigger` 评估（`0x4F8A6A` / `0x4FA220` 两直呼点） | [实证] | claims_R5 `0x6F0AB0` / `0x6F0B01` |
| `0x752480` | EVA 专属播放入口（动作 `0x15 PlaySpeech` 唯一路径） | [实证] | claims_R5 `0x6DE911` |
| `0x65C780` / `0x65C7E0` | `Randomizer::Random` / `RandomRanged`（局内实例 `Scenario+0x218`） | [实证] | claims_R5 `0x65C780` / `0x72646A` |

### 14.13 R5 勘误登记（本章范围内，源文档侧）

| # | 目标（源文档:行） | 改前原文 | 改后文本 | 理由 / 证据 |
|---|---|---|---|---|
| E-R5-2 | `docs/re/trigger_runtime_deep_dive.md:531`（§7(4) 代码块） | `006E525E  A1 A8 F6 B0 00  mov eax,[0xB0F6A8]  ; 延迟析构向量 Count` | `006E525E  A1 98 F6 B0 00  mov eax,[0xB0F698]  ; 队列实例基址（= vtable 指针，供 grow 路径 call [eax+8]）` | 实读字节 `0x6E525E = A1 98 F6 B0 00`；Count 的读/写真锚点为 `0x6E5272 = 8B 0D A8 F6 B0 00` 与 `0x6E527B = 89 0D A8 F6 B0 00`。原文两处错（字节 + 语义）；§4.4 的布局表述正确，不受影响 |
| E-R5-3 | `docs/re/trigger_runtime_deep_dive.md:500` 附近（§7(2) 代码块） | `00726509  D3 E5  shl ebp,cl` | `00726509  8B CB  mov ecx,ebx` ／ `0072650B  D3 E5  shl ebp,cl` | 实读：`0x726509 = 8B CB`、`0x72650B = D3 E5`；该文档自带断言库 `out/re_work/triggers_deep/claims.txt` 已记 `0x726509 = 8B CB`（正文与断言库口径不一致，正文需补 2 字节偏移） |
| E-R5-4 | `docs/re/trigger_runtime_deep_dive.md:533`（§7(4) 代码块末行） | `0055DE9F  E8 CC 7D 02 00  call 0x725C70` | `0055DE9F  E8 CC 7D 1C 00  call 0x725C70` | 实读 `E8 CC 7D 1C 00`（rel32 末字节 `1C`）；同文档 §6 的 Q4-4 行已按〔勘误 ASM-FIX-4〕订正，**§7 代码块未同步** ⇒ 建议就地同步 |

````
- **证据**: 等级 [实证]｜来源 `docs/re/trigger_runtime_deep_dive.md:16-21`（C1–C6）、`:31-39`（类表）、`:75-94`（每帧 10 kind 表）、`:96-141`（RaiseEvent / 唯一入口）、`:143-164`（RegisterEvent 内部顺序与门控）、`:176-224`（顺序与确定性）、`:246-260`（PRNG 清单）、`:264-291`（RandomDelay 公式与 CRC）、`:301-380`（生命周期/存档关联）、`:384-421`（AITrigger）、`:552-565`（未闭环 U-1..U-8）；`docs/re/trigger_system_manifest.md:14-16`（三表）、`:22-26`（硬结论）、`:36-98`（结构/接线/负证）、`:514-519`（名称口径）、`:611-644`（联机判定与无 MP 门控）；**R5 独立复算新增（见 claims_R5.txt）**：6 个类虚表 + 容器虚表的 RTTI 链（`0x7F44E0` / `0x7F45C4` / `0x7F5858` / `0x7F5904` / `0x7F5578` / `0x7F443C` / `0x7EA5A4` 及各自 `vtable−4` 的 COL 与 TD 名）、`0x6E5266` / `0x6E526B` / `0x6E5272` / `0x6E527B`（队列 append/grow）、`0x72650B`、`0x55B011`、`0x6E4FD0`。
- **影响面**: **影响 §11 速查表**（新增 6 类虚表 + 容器虚表 + 2 个 `Size()` + 一组关键函数 VA，见 14.12）；**影响 §12 契约**（14.10 点名 §8/§6/§9/§5/§15 五条；14.7「每帧总消费量非恒定 2」是对 §12.2 红线框 RNG 条目的限定，配套 PATCH-R5-03）；**不影响 §0 准则**（只新增/细化，不改方法论）；不触碰 §1–§4 / §7 / §10。

### PATCH-R5-02 新章 §15 存档块与序列化全景（容器 / 写侧三类序列化单元 / 读侧不对称 / 兼容性红线）

- **目标锚点**: **L1981**｜该行前 40 字符原文：`## 附录 DA1 · 勘误登记（雷达挂钩地址与 G-1`（实跑 grep 唯一命中 L1981）
- **动作**: APPEND_SECTION
- **现状问题**: atlas §7 讲超武持久化、§10 讲内存与对象生命周期，但**没有存档/读档序列化专章**。后果：①「哪些结构落盘、以什么次序落盘」在 atlas 中无法回答；②§9 讲帧 CRC 却没有任何一节把它与「存档兼容性红线」对接；③「引擎用 OLE 复合文档而非自研指针 swizzle」这一**架构级事实**（决定了所有对象寻址方式）在 atlas 中完全缺席。本章补齐容器格式、写/读驱动链、序列化原语与兼容性红线。
- **替换文本**:

````markdown
## 15. §15 存档块与序列化全景 (Savegame Blocks & Serialization)

> **章性质**：架构级专章（容器 / 驱动链 / 序列化原语 / 引用面拓扑 / 兼容性红线 + 未闭环项）。
> **来源（只读引用）**：`docs/re/savegame_block_manifest.md`（82 KB，含 §12 定谳）；字节断言库 `out/re_work/save_blocks/claims.txt`（82 条）、`out/re_work/savegame/claims.txt`（143 条）、`out/re_work/da4/claims.txt`（12 条）——三库全部条目已由 R5 独立复算（0 mismatch）。
> **本章新增实证（R5 独立复算）**：①读侧助手调用点**18 处 / 16 个不同目标**（源文档口径 A 记 17，漏 1，见 E-R5-1）；②读侧 **8 段完全同形的通用 OLE 对象读循环**（`push 0x7F7C90` + `call edi`），与写侧 35 个命名模板块**不对称**；③`OleSaveToStream / OleLoadFromStream` 的**全镜像引用面**分类（46 / 12 处，含 4 类"子系统本地序列化器"）；④家族外序列化器 `0x721010`（主题管理器）与 4 个读侧家族外块读取器。

### 15.1 结论速览

| # | 结论 | 等级 |
|---|---|---|
| **C1** | 存档**容器 = OLE2 复合文档（CFB）**，不是扁平流：写侧 `ole32!StgCreateDocfile`（`0x67CF42 = FF 15 C8 15 7E 00`，全镜像唯一非 thunk 引用）、读侧 `ole32!StgOpenStorage`（`0x67E489`）；真机档签名 `D0 CF 11 E0 A1 B1 1A E1`，每档 **15 个流**（`CONTENTS` 为游戏状态）。 | [实证] |
| **C2** | **对象寻址 = OLE CLSID + 存储路径**，不是自研指针 swizzle：`ole32!OleSaveToStream`（IAT `0x7E15F4`）/ `ole32!OleLoadFromStream`（IAT `0x7E15F8`），镜像内无裸地址落盘。 | [实证] |
| **C3** | 写侧驱动链 `Game::Save 0x67D0C0` → `Game::Save_Core 0x67D300`，由**三类序列化单元**构成：**S-1 标量块**（`0x67F7E0`，含 `CurrentFrame`）、**28 个内联向量块**、**35 个模板块函数**（`0x67FDF0..0x680EF0`，步长 `0x80`）。 | [实证] |
| **C4** | 35 个模板块函数**逐字节相同**（127 B 纯代码 / 128 B 含 1 字节 `90` 对齐填充，两种口径各自 35/35 唯一）；无任何直接/间接调用者，仅被 `Save_Core` 顺序直接 `call` 35 次；「对应哪个子系统」由 `call` 前的 `mov edx,<对象 VA>` 给出。 | [实证] |
| **C5** | 读侧与写侧**不对称**：`Game::Load 0x67CEF0` → `Game::Load_Core 0x67E440` 采用 **8 段同形的通用 OLE 对象读循环**（`push 0x7F7C90` riid + `call edi`，`edi = [0x7E15F8]`）+ **18 处助手调用点（16 个不同目标）** + **4 个家族外块读取器**（`0x722240 / 0x722D00 / 0x72AD20 / 0x72DEF0`），**没有** 35 个镜像块函数。 | [实证] |
| **C6** | 序列化原语的引用面：`OleSaveToStream` **46 处**（其中 **35 处 = 模板副本各 1**，11 处非模板）、`OleLoadFromStream` **12 处**；非模板点落在 6 类对象/子系统（各对象类自己的 `IPersistStream::Save/Load`、触发器区 `0x719D29/0x719DE7`、音频区 `0x75C6ED/0x75C7A7`、CRT 区 `0x7C88DA/0x7C88E0`）。 | [实证] |
| **C7** | `0x71xxx` 的 OLE 对**不是**触发器系统：RTTI 链把 `{0x7F50CC, 0x7F5000, 0x7F4FDC}` 解为 `.?AVTeleportLocomotionClass``（其次级扇区 `0x7EADF4` = `.?AVLocomotionClass``），且该对象把 `CurrentFrame` 存在 `+0x3C`。 | [实证] |
| **C8** | 存档兼容性红线（与 §9 帧 CRC 输入集对照）：**禁改** = 流名/顺序（`Internal Version` / `CONTENTS`）、35 块调用顺序 + 每块前导 Count、`CurrentFrame`、RNG 状态、量化坐标/朝向字节；其中 **RNG 与位置/朝向三元组同时是帧 CRC 输入** ⇒ 改存档兼容性几乎必然改联机确定性。 | [实证] + [推演] |

### 15.2 容器与文件格式（[实证]）

```text
ALL01UMD.sav  1,220,002 B   头 8 字节 D0 CF 11 E0 A1 B1 1A E1   (OLE2 / CFB)
ECH01.sav       825,470 B   头 8 字节 D0 CF 11 E0 A1 B1 1A E1
CONTENTS 流   1,205,666 B   游戏状态（35 块 + 28 向量 + S-1 标量）
```
| 流 | 大小 | 含义 |
|---|---|---|
| `\x05SummaryInformation` | 356–380 | OLE 属性集 |
| `Scenario Description / Player House` | 可变 | UTF-16 场景描述 / 玩家国家 |
| `Version` | 4 | 容器格式版本（`01 00 00 00`） |
| **`Internal Version`** | **4** | **引擎内部版本 = Savegame_Magic**（`98 B8 02 00` = `0x0002B898`，真机档文件偏移 `0x0C40`） |
| `Start Time / Last Save Time / Play Time` | 8×3 | FILETIME |
| `Executable Name` | 16 | UTF-16 |
| `CONTENTS` | 814 206–1 256 190 | **游戏状态** |

- **魔数的读侧语义（易误读）**：`Game::Load` 在 `0x67CF70 = A1 60 D5 83 00` 读全局 `[0x83D560]` 后交给 `0x681080`——而 `0x681080 = 8B 44 24 04 89 01 C2 04 00`（`mov eax,[esp+4]; mov [ecx],eax; ret 4`）是**描述符字段 setter，不是比较指令**；真正的落盘/读回在 OLE 层。反证：`SOV01T.sav` 同址 = `CC 88 02 00`（≠ 魔数）⇒ 该流确是**版本闸**。 [实证]
- `CONTENTS` 首 4 字节 = `0x00003278`（≠ 魔数）；`0x2B898` 在 `CONTENTS` 全流各编码（LE/BE/16 位/XOR/NOT/±1/ASCII）**0 次出现** ⇒ 魔数**不在** `CONTENTS` 内。 [实证]
- `0x83D5A8 = 43 00 4F 00 4E 00 54 00 45 00 4E 00 54 00 53 00 00 00` = `CONTENTS` 的 UTF-16LE 常量。 [实证]

### 15.3 写侧驱动链与三类序列化单元（[实证]）

```text
Game::Save 0x67D0C0        (__thiscall，1 个栈参 = 文件名)
  0x67D0C6  call 0x67FDE0            ; 构造本地流包装
  0x67D0DD  call [0x7E15FC]          ; ole32!CoCreateInstance（造流包装 COM 对象）
  0x67D131  call [edx+0xC]           ; IStream::Write(CONTENTS 载荷)
  0x67D1AF  call 0x67D300            ; → Save_Core（唯一调用者）
Game::Save_Core 0x67D300
  0x67D308  mov ecx,[0xA8B230]        ; ScenarioClass::Instance
  0x67D31B  call 0x4C6340             ; 原始 0x44 字节写入器（全局对象 0x8A38E0）
  0x67D327  call 0x674730             ; Rules 块
  0x67D32C..0x67E1B5                  ; 28 个内联 DynamicVectorClass<T*> 循环
  0x67D421  call 0x67F7E0             ; ★ S-1 标量块（写 CurrentFrame 等）
  0x67DF0F..0x67E3AA                  ; 35 个模板块函数 call（#1..#35）
  0x67E3BD  cmp [0xA8B238],5          ; GameMode==5(Skirmish) 分支
  0x67E429  call 0x721010             ; 收尾：主题管理器 0xA83D10 的 2 个 dword
```
| 单元 | 地址 | 规模 | 口径 |
|---|---|---|---|
| **S-1 标量块** | 写 `0x67F7E0` / 读 `0x67F9C0` | 一次写入的全局序列：`0xA8ED78` → `0xA83D4C`（`HouseClass::Player`）→ **`0xA8ED84`（CurrentFrame）** → `0xA8ECC8`(Count) + `0xA8ECBC[i]` → `0x89EA40`（`0x1B0` 字节）→ … | `0x67F819 = 68 84 ED A8 00` + `call [vtable+0x10]`；读侧 `0x67FA19` + `call [vtable+0xC]` |
| **28 个内联向量块** | `0x67D32C` … | 每块：`Count@[global]` → `IStream::Write(4,&count)` → 逐元素 `虚表[0]` → `OleSaveToStream` → `虚表[2]` | 布局校验 `Count == Items+0xC`：**28/28 通过** |
| **35 个模板块函数** | `0x67FDF0 + 0x80*i` | 每个 127 B 纯代码，签名 `HRESULT Serialize(LPSTREAM ecx, DynamicVectorClass<T*>* edx)` | 见表 15.4 |

> **写侧调用者关系**：`Game::Save 0x67D0C0` **本镜像内无任何 `E8/E9` 直接调用者、也无 imm32 引用**（0 refs）⇒ 只能经函数指针/虚表调用，**未闭环**（见 15.10 U-3）。

### 15.4 35 个模板块：字节同一性与「谁是谁」（[实证]）

```text
0x0067FDF0 = 83 EC 08 53 56 57 8B FA 8B D9   ; sub esp,8; push ebx,esi,edi; mov edi,edx; mov ebx,ecx
0x0067FE0D = FF 51 10                        ; call [ecx+0x10]  IStream::Write(4,&count)
0x0067FE45 = FF 15 F4 15 7E 00               ; call [0x7E15F4]  ole32!OleSaveToStream
0x0067FE56 = FF 51 08                        ; call [ecx+8]     元素释放
0x0067FE6E = C3                              ; 127 B 纯代码末字节 = ret
0x0067FE6F = 90                              ; 128 B 口径的 1 字节对齐填充
0x0067FDF0 / 0x0067FE70 / 0x00680EF0         ; #1 / #2 / #35 序言逐字节相同
```
| 口径 | 区间 | 末字节 | MD5 | 唯一性 |
|---|---|---|---|---|
| **127 B（纯代码，推荐）** | `0x67FDF0..0x67FE6E` | `C3` = ret | `9f6770a9cd27b9fa49558adf28c92f10` | 35/35 同值 |
| 128 B（含 1 B pad） | `0x67FDF0..0x67FE6F` | `90` = nop | `cb13908da7ed66fb2a7545323b865a3d` | 35/35 同值 |

- **为什么有两种长度口径**：步长 `0x80 = 128`，MSVC6 按 16 B 对齐填充，**函数体实际 127 B**，尾补 1 B `90` 凑满 128。两种口径**各自在 35 条内全等，不构成矛盾**；引用时必须写明字节数（本项目 `docs/re/cross_doc_consistency_audit.md §2.6` 用 128 B 口径）。
- **块 ↔ 子系统映射口径**：真正的「哪个子系统」= `call` 前一条 `mov edx,<对象 VA>` 的实参对象（35 组，例：#1 `0x67DF0F` ← `mov edx,0xA83E30`；#17 `0x67E0AF` ← `mov edx,0x8B4120` 即 `Save_Sides`；#35 `0x67E3AA` ← `mov edx,0xB04BD0`）。**34/35 的类名静态无法定名**（`.bss` 对象 + RTTI 描述符在文件内无引用）⇒ 仅 #17 `Save_Sides` 已由 YRpp 符号定名。 [实证]
- **两个"家族的边界"事实**：`0x680EF0 + 0x80 = 0x680F70` —— 读侧助手族**紧接**写侧模板族之后开始（两族地址相邻但**不再是**等长同体家族，读侧助手的序言逐条不同）。 [实证]

### 15.5 读侧驱动链：结构性不对称（[实证]）

```text
Game::Load 0x67CEF0
  0x67CF42  call [0x7E15C8]           ; ole32!StgCreateDocfile（hint=253，IAT index 0）
  0x67CF70  mov eax,[0x83D560]        ; Savegame_Magic
  0x67CF7D  call 0x681080             ; 描述符 setter（不是比较）
  0x67CF6B/0x67CF8A/0x67CF98/...      ; 12 处描述符助手调用点（见下）
Game::Load_Core 0x67E440
  0x67E489  mov ebx,[0x7E15E4]        ; ole32!StgOpenStorage
  0x67E4A2  call ebx                  ; 打开 .SAV 容器
  0x67E4E8  mov [0xA8B238],eax        ; SessionClass::Instance ← 读回的 GameMode
  0x67E572  call [ecx+0x10]           ; IStorage::OpenStream("CONTENTS")
  0x67E5D0  call [0x7E1600]           ; ole32!OleRun
  0x67E840  mov edi,[0x7E15F8]        ; ★ 缓存 OleLoadFromStream，供 8 段读循环共用
  0x67E857/0x67E8A0/0x67E8FF/0x67E93A/0x67E978/0x67E9B6/0x67E9F4/0x67EA32   ; 8 段同形读循环
  0x67E6AE → 0x722D00 ; 0x67E6B3 → 0x722240 ; 0x67E6D5 → 0x72DEF0 ; 0x67E776 → 0x72AD20
  0x67E8B5  call 0x67F9C0             ; S-1 标量块（读 CurrentFrame 等）
```
**8 段同形读循环的字节指纹（每段 5 条指令完全同形）**：

```text
lea  ecx,[esp+0x14] / push ecx ; push 0x7F7C90(riid) ; push esi ; call edi
→ OleLoadFromStream(stream=esi, riid=0x7F7C90, ppv=&slot)     [8/8 段一致]
```
| 读侧结构 | 数量 | 证据 |
|---|---|---|
| 通用 OLE 对象读循环 | **8**（`0x67E857 / 0x67E8A0 / 0x67E8FF / 0x67E93A / 0x67E978 / 0x67E9B6 / 0x67E9F4 / 0x67EA32`，各自前置 `push 0x7F7C90`） | `0x67E840 = 8B 3D F8 15 7E 00`；`0x67E9B6 = FF D7` |
| 描述符助手调用点 | **18 处 / 16 个不同目标**（`0x680F70` 被调 2 次；窗口 `0x680F70..0x681840`） | 完整 18 点清单见 R5 交付文件 [2] 节；其中 `0x67E62B → 0x680F70` 为源文档口径 A **漏记**的第 18 点（E-R5-1） |
| 家族外块读取器 | **4**（`0x722D00` / `0x722240` / `0x72DEF0` / `0x72AD20`） | 4 函数体全量反汇编（109 / 109 / 44 / 32 条指令）**RNG 零命中**（对 §14 U-3 的负证） |
| 写侧镜像块函数 | **0** | 读侧不存在 35 个镜像模板块函数 |

> **架构解读 [推演]**：写侧把 35 个子系统向量「手工打磨成等长 127 B 模板」并用**命名调用**顺序发射（便于断点/对拍定位）；读侧改为**通用循环**（先读 Count，再逐个 `OleLoadFromStream` 重建对象），因此读侧无法用"35 个断点"定位——这是排障时最容易踩的不对称。两族**序列化口径完全相同**（写 4 B Count + 每元素虚表[0]/[2] 夹 `OleSave/OleLoad`）。

### 15.6 序列化原语引用面（[实证]）

| IAT 槽 | 导入函数 | 镜像内 dword 引用数 | 分布 |
|---|---|---|---|
| `0x7E15C8` | `ole32!StgCreateDocfile` | 1（非 thunk） | `0x67CF42` |
| `0x7E15E4` | `ole32!StgOpenStorage` | 2 | `0x67E489`（Load）、`0x67FD6F` |
| `0x7E15F4` | **`ole32!OleSaveToStream`** | **46** | **35 = 模板副本各 1**（`0x67FE47` 型）+ `0x67D353` + `0x4AF8A7 / 0x4B6366 / 0x4DB7C0 / 0x5046CB / 0x54B88D / 0x5BE851 / 0x69EFB7 / **0x719DE7** / **0x75C7A7** / 0x7C88E0` |
| `0x7E15F8` | **`ole32!OleLoadFromStream`** | **12** | `0x67C6B7 / 0x67E842` + `0x4AF7ED / 0x4B62AD / 0x4DB56A / 0x504065 / 0x54B7C6 / 0x5BE4DE / 0x69EEFD / **0x719D29** / **0x75C6ED** / 0x7C88DA` |
| `0x7E1600` | `ole32!OleRun` | 2+ | `0x67D0EE`（Save）、`0x67E5D0`（Load） |
| `0x7E15FC` | `CoCreateInstance`（存档流包装） | 1 | `0x67D0DD` |

> 计数方法：`.text` 区间（`0x401000–0x7E038D`）内该 4 字节小端值的全部出现点（与仓库内 `tools/xref_abs.py` 同口径）。**注意**：35 个模板副本各自含 1 处，故"46"内含 35 个同体副本 —— 源文档 `docs/re/savegame_block_manifest.md §2.5` 只列了 8 个代表点（含"35 个块函数内"1 行），本表给的是**全量分类**（新增可见 `0x69EFB7 / 0x719DE7 / 0x75C7A7 / 0x7C88E0` 等 4 处）。

### 15.7 子系统本地序列化器（R5 新增发现）（[实证]）

`Save_Core / Load_Core` 并不是"自己写所有字节"：它们把若干子系统状态**转交该子系统自己的序列化函数**——这些函数住在子系统代码区，因此**不在** 35 模板 / 28 向量 / S-1 之内。

| 位置 | 形态 | 语义 | 证据 |
|---|---|---|---|
| `0x721010` | 写侧：`IStream::Write(4,&this[+4])` → `IStream::Write(4,&this[+8])`，`ret 4` | **主题/音乐管理器** `0xA83D10` 的 2 个 dword（唯一直呼点 = `Save_Core` 尾部 `0x67E429`，`mov ecx,0xA83D10`） | `0x721010`（`0x721023` / `0x721035` 两次 `call [reg+0x10]`、`0x72103A = C2 04 00`）；该区 `0x7209D0` 的主题检查函数被 `0x406F70`（音频帧更新）调用 |
| `0x722D00 / 0x722240 / 0x72DEF0 / 0x72AD20` | 读侧：家族外块读取器（`__thiscall`/栈参混用） | 由 `Load_Core` 在 `0x67E6AE / 0x67E6B3 / 0x67E6D5 / 0x67E776` 直呼；**函数体 RNG 零命中** | 4 函数全量反汇编 |
| `0x719D29 / 0x719DE7` | 对象 `IPersistStream` 对（读 `OleLoadFromStream` / 写 `OleSaveToStream`；读侧 `push 0x7ED358` CLSID、`ret 8`） | **`TeleportLocomotionClass`**（RTTI 解出 `{0x7F50CC, 0x7F5000, 0x7F4FDC}`；次扇区 `0x7EADF4` = `LocomotionClass`），ctor 把 `CurrentFrame` 存 `+0x3C` | RTTI 链 + `0x719CC2 / 0x719CDF / 0x719CD5 / 0x719D20 / 0x719D27 / 0x719DE7` |
| `0x75C6ED / 0x75C7A7` | 音频区 `IPersistStream` 对 | 音频子系统自序列化对象（未定名） | 引用面分类（15.6） |
| `0x69EEFD / 0x69EFB7`、`0x7C88DA / 0x7C88E0` | 另两组 `IPersistStream` 对 | 未定名（`0x7C8xxx` = CRT/内存区） | 引用面分类（15.6） |
| `0x751620 / 0x7533B0` | `Save_Core` 尾部的另外两个 finalizer（音频区） | 收尾动作，参数 = 流对象 | `0x67E3FB / 0x67E410` |

> **架构结论**：**存档 = 「核心驱动（顺序/计数/容器）+ 子系统本地序列化器（各自对象图）」** 的两层结构。任何"新增子系统状态"必须同时决定它落进哪一层——这决定了存档兼容性红线的适用范围。

### 15.8 存档兼容性红线（与 §9 帧 CRC 输入集对照）（[实证] + [推演]）

| 级别 | .SAV 结构 | 同时进帧 CRC？ | 破坏后果 |
|---|---|---|---|
| **禁改** | OLE 流名/顺序（尤其 `Internal Version`、`CONTENTS`） | 否 | 读档打不开 |
| **禁改** | 35 块调用顺序 + 每块前导 Count | 部分（向量块） | 流错位 / 读档崩溃 |
| **禁改** | `CurrentFrame`（S-1 标量块） | 否（不直接进 CRC） | 全部 Timer / 触发器相位错乱 |
| **禁改** | RNG 状态（`ScenarioClass::Random`） | **是** | 联机 desync |
| **禁改** | 对象量化坐标（÷10）/ 朝向字节 | **是** | 联机 desync |
| **慎改** | 量化除数、`0x4C93D0` 离散化 | **是** | 假 desync / 漏报 |
| **可动** | dirty-rect、迷雾显示、音频、FPS | 否 | 无 |

> **一句话**：`.SAV` 的「顺序 + Count + `Internal Version` + RNG + `CurrentFrame`」是兼容性红线；其中**位置/朝向/RNG 三元组同时是帧 CRC 输入** ⇒ 改存档兼容性几乎必然改联机确定性（与 §9 红线表口径一致）。

### 15.9 与其它子系统的契约（点名）

| 对端 | 契约 | 证据等级 |
|---|---|---|
| **§14 触发器脚本运行时** | 每帧 Tag 名单向量由 S-1 标量块写入（`0x67F8C5`）与按原序重建（`0x67FB8A`）；`CurrentFrame` 同批进档；`TriggerClass` 位图依赖链序 | [实证] |
| **§9 联机确定性与帧校验** | 对局内读档是**同步命令**（`Game::Load` 调用者含 `NetworkEvent` 处理器簇 `0x4C7AC0 / 0x4C7B3D`）；RNG/坐标同属 CRC 输入 | [实证] + [推演] |
| **§8 帧时钟循环** | `CurrentFrame` 的序列化在 Save_Core 内、位于第 1 个内联向量块之后（`0x67D421`），**不在** 35 块序列内；游戏循环调用者 `0x55DC92` | [实证] |
| **§10 内存与对象生命周期** | 对象释放走 OLE `CoCreateInstance` 语义（读档即"重新构造对象"），与 SBH/池化分配器交互面未闭环 | [实证] + 未闭环 |
| **§6 音频引擎** | 主题管理器（`0xA83D10`）与音频 finalizer 属音频子系统，但由存档驱动链调用（15.7） | [实证] |
| **§11 速查表** | 见 15.11（新增 Save/Load 驱动链 + OLE IAT 槽 + 模板块族） | [实证] |

### 15.10 未闭环项

| # | 未闭环项 | 为什么静态闭不了 | 下一步取证 | 级别 |
|---|---|---|---|---|
| U-1 | 35 个块实参对象的**类名 / RTTI 解析** | `.bss` 对象无文件内 RTTI 描述符引用（962 类型名 vs 43 描述符指针，无一命中） | 真机断 `0x67FDF0`（或 35 个 `call` 点）读 `EDX`→`[EDX]`→`COL+0xC`→`TD+8`，回填类名 | P1 |
| U-2 | 写侧 35 块 / 读侧 8 通用循环的**映射关系** | 读侧无命名块、无镜像函数，数量不对称 | 以"读循环前读到的 Count 全局"与写侧 35 个实参对象做地址级配对；真机对拍 `CONTENTS` 逐段长度 | P1 |
| U-3 | `Game::Save 0x67D0C0` 的调用者 | 镜像内 0 个 `E8/E9`/imm32 引用 ⇒ 只能经函数指针/虚表 | 扫虚表槽位与运行期断点回溯 | P2 |
| U-4 | 家族外序列化器的**类名**（`0x75C6ED/0x75C7A7`、`0x69EEFD/0x69EFB7`、`0x7C88DA/0x7C88E0`） | 同上（对象在 `.bss`，但**本批已对 `0x719D29/0x719DE7` 用 RTTI 定名成功**，说明可行） | 对每对地址回溯其 `IPersistStream` 宿主对象的 vtable → RTTI 链 | P2 |
| U-5 | `0x67E62B → 0x680F70` 的助手语义（第 18 个调用点） | 助手族未逐个定名 | 反汇编 `0x680F70` 全函数 + 其调用上下文 | P2 |
| U-6 | `0x67F7E0` 一次写入的全局序列**完整清单** | 未枚举全部 Write 实参（与 §14 U-4 同域） | 枚举 `0x67F7E0–0x67F9C0` 区间所有 `call [vtable+0x10]` 的实参 | P1 |
| U-7 | 跨版本存档兼容矩阵（1.001 vs 其它版本） | 只有真机档样本（`SOV01T.sav` `Internal Version` 不同） | 收集多版本 `.SAV` 做 `Internal Version` / 流布局差分 | P2 |

### 15.11 关键 VA 速查表（供 Lead 并入 §11）

| VA | 名称 / 职责 | 证据等级 | 来源 |
|---|---|---|---|
| `0x67D0C0` | `Game::Save`（外层：建档/开流） | [实证] | claims_R5 `0x67D0C0` |
| `0x67D300` | `Game::Save_Core`（核心序列化驱动） | [实证] | claims_R5 `0x67D300` / `0x67D1AF` |
| `0x67CEF0` | `Game::Load`（外层：校验魔数/开 CONTENTS 流） | [实证] | claims_R5 `0x67CEF0` / `0x67CF42` |
| `0x67E440` | `Game::Load_Core`（核心读档驱动） | [实证] | claims_R5 `0x67E440` / `0x67E840` |
| `0x67FDF0` | 35 模板块族首地址（步长 `0x80`，127 B/块；`0x680EF0` 为 #35） | [实证] | claims_R5 `0x67FDF0` / `0x67FE6E` / `0x680EF0` |
| `0x6805F0` | `Save_Sides`（模板实例，实参 `0x8B4120`） | [实证] | claims_R5 `0x6805F0` / `0x67E0A8` |
| `0x67F7E0` / `0x67F9C0` | **S-1 标量块**（写 / 读；含 `CurrentFrame`） | [实证] | claims_R5 `0x67F819` / `0x67FA19` |
| `0x721010` | 主题管理器 2-dword 写侧序列化器（`Save_Core` 尾部调用） | [实证] | claims_R5 `0x721010` / `0x67E429` |
| `0x7E15F4` / `0x7E15F8` | IAT：`ole32!OleSaveToStream` / `OleLoadFromStream` | [实证] | claims_R5 `0x7E15F4` / `0x7E15F8` |
| `0x7E15C8` / `0x7E15E4` | IAT：`ole32!StgCreateDocfile` / `StgOpenStorage` | [实证] | claims_R5 `0x67CF42` / `0x67E489` |
| `0x83D560` | `Game::Savegame_Magic` = `0x0002B898`（魔数常量） | [实证] | claims_R5 `0x83D560` |
| `0x83D5A8` | `CONTENTS` 流名（UTF-16LE 常量） | [实证] | claims_R5 `0x83D5A8` |
| `0x681080` | 版本描述符 setter（**不是**比较指令） | [实证] | claims_R5 `0x681080` |
| `0x4C6340` | 原始 0x44 字节写入器 | [实证] | claims_R5 `0x4C6340` |

### 15.12 R5 勘误登记（本章范围内，源文档侧）

| # | 目标（源文档:行） | 改前原文 | 改后文本 | 理由 / 证据 |
|---|---|---|---|---|
| E-R5-1 | `docs/re/savegame_block_manifest.md:859-862`（§12.2 口径 A 清单） | 「口径A 额外 2 处（边界外，构成 16 个不同目标）: #16 0x0067D193 → 0x00680F70 ; #17 0x0067E4CA → 0x00681840」（全表合计 17 点） | 「口径 A 的**调用点**共 **18** 处（不同目标仍为 **16**）：新增第 18 点 `0x0067E62B = E8 40 29 00 00 → 0x680F70`（`0x67E622 = 8D 44 24 14` / `0x67E62A = 50` 之后）」 | 实跑 `0x67CE00–0x67EA40` 区间 `call` 目标 ∈ `[0x680F70,0x681840]` 的全部调用点：**18 点 / 16 目标**（目标集合与源文档口径 A 一致，仅漏记 1 个调用点）。口径 B（窄窗 15 点）**不受影响** — 因 `0x680F70 < 0x680FF0` |
| E-R5-5 | `docs/re/savegame_block_manifest.md:261-262`（§2.5 IAT 表） | 「`0x007E15F4` … 非 thunk 引用点：`0x0067D353`、`0x0067FE47`（35 个块函数内）、`0x004AF8A7 / 0x004B6366 / 0x004DB7C0 / 0x005046CB / 0x0054B88D / 0x005BE851`」 | 同列补全为**全量 11 个非模板点**：原 8 项之外补 `0x0069EFB7`、`0x00719DE7`、`0x0075C7A7`、`0x007C88E0`；`0x7E15F8` 同列补 `0x0069EEFD`、`0x00719D29`、`0x0075C6ED`、`0x007C88DA` | 全 `.text` 区间 dword 引用扫描：`0x7E15F4` 共 **46** 处（35 处 = 模板副本各 1 + 11 处非模板）、`0x7E15F8` 共 **12** 处 ⇒ 源表列的是"代表点"，非全量；补全后与 15.7 的"子系统本地序列化器"拓扑自洽 |

````
- **证据**: 等级 [实证]｜来源 `docs/re/savegame_block_manifest.md:14-28`（结论速览）、`:41-141`（模板族指纹 / 逐字节同一）、`:146-250`（Save/Load 外层与容器 / OLE 原语 / xref）、`:291-341`（35 块 → 实参对象）、`:345-416`（28 内联向量块）、`:420-465`（真机档格式 / CONTENTS 头）、`:469-477`（CurrentFrame 与联机）、`:796-1055`（§12 定谳：MD5 双口径 / 读档计数 / 逐块证据表 / U-2·U-3·U-9 闭环 / 兼容性红线）；**R5 独立复算新增（见 claims_R5.txt）**：`0x67E62B`（第 18 调用点）、8 段 OLE 读循环指纹（`0x67E840` + `0x67E851/0x67E89A/0x67E8F9/0x67E934/0x67E972/0x67E9B0/0x67E9EE/0x67E9A2+…` 的 `push 0x7F7C90` 与 `call edi`）、`OleSave/OleLoad` 全量引用面（46 / 12）、家族外序列化器 `0x721010` 全函数与唯一调用者、4 个读侧家族外块读取器（RNG 零命中）、`0x719D29/0x719DE7` 的 RTTI 定名（`TeleportLocomotionClass`）。
- **影响面**: **影响 §11 速查表**（新增 Save/Load 四函数 + 模板族 + OLE IAT 槽 + S-1 标量块 + 主题序列化器，见 15.11）；**影响 §9 契约表**（15.8 兼容性红线与帧 CRC 输入集对照；15.9 点名校验「对局内读档 = 同步命令」）；**影响 §10**（对象重建经 OLE `CoCreateInstance` 语义，与分配器交互面列入未闭环）；**不影响 §0 准则**；不触碰 §1–§7（§7 超武持久化与本节为互补关系，S-1/模块块的落盘点未与 §7 逐字段对齐 ⇒ 列为 U-6）。

### PATCH-R5-03 ERRATUM：§12.2 红线框「每帧恰消费 2 次」加限定语（RNG 消费面）

- **目标锚点**: **L1926**｜该行前 40 字符原文：` │   - 局内唯一随机数 (ScenarioClass::Random 0x`（实跑 grep：`'每帧恰消费 2 次' -> lines [1926] (count=1)`，唯一命中）
- **动作**: ERRATUM（就地订正 + 保留原文对照；**不改 §12.2 的结论强度**）
- **现状问题**: 红线框把局内 RNG 写成「**每帧恰消费 2 次**」。该数字的成立范围是**帧 CRC 路径**（§12.2 的〔勘误 ASM-FIX2-1〕已经把原文的"仅 1 次"改成 2 次），但**没有限定语**：§14.7 实证触发器子系统另有 4 个函数 / 9 条指令对该实例消费（`RandomDelay` 装填、动作 `0x3A` ×4、动作 `0x62` ×1、`AITrigger` ×2），全部为**条件性**消费。读到「每帧恰 2 次」的读者会得出"触发器动作不烧随机数"或"RNG 消费量恒定"的错误结论，进而误判联机对拍口径与 hook 风险面。
- **替换文本**（按顺序两处：① 就地改 L1926 那一行的行内文本；② 在该行之后插入 1 行注记）:

````markdown
① L1926 行改为（行首的框线符与缩进保持原样）：
 │   - 局内唯一随机数 (ScenarioClass::Random 0x00A8B230+0x218 **帧 CRC 路径**每逻辑帧 2 次；**另有条件消费**：触发器子系统 4 函数/9 指令，见 §14.7) │

② 紧随其后的新增注记行：

> **〔限定语 · R5 §14.7 · 2026-09-29〕** 上框「每逻辑帧 2 次」是**帧 CRC 路径的下界**，不是全帧总量：帧 CRC `0x64DAB0` 在 `0x64DE39/0x64DE3F` 消费 1 次（另帧尾 `0x64DE70 → 0x650A90` 1 次，见〔勘误 ASM-FIX2-1〕）；**触发器/动作侧另有条件消费** `RandomRanged/Random` 共 9 条指令 —— `ResetTimers 0x72646A`（RandomDelay 装填）、动作 `0x3A` 4 次（`0x6E2CEB/0x6E2D4E/0x6E2D5A/0x6E2DB0`）、动作 `0x62` 1 次（`0x6DE80F`）、`AITrigger` 2 次（`0x6F0B01/0x6F0CEE`）。⇒ 全帧总量 = `2 + Σ(触发器侧条件消费)`，**不是恒定量**；RNG 消费次数因此是联机对拍必须逐帧观测的量（§14.11 U-9，[待实测]）。字节断言：`out/re_work/atlas_rev/R5/claims_R5.txt`。
````
- **证据**: 等级 [实证]（代码面）+ [待实测]（运行期分布）｜`0x72646A = E8 71 63 F3 FF`、`0x6DE80F = E8 CC DF F7 FF`、`0x6E2CEB = E8 90 9A F7 FF`、`0x6F0B01 = E8 DA BC F6 FF`、`0x64DE3F = E8 3C E9 00 00`（均在 claims_R5.txt，audit_bytes 全 OK）；来源 `docs/re/trigger_runtime_deep_dive.md:246-260`（PRNG 逐条清单）、`:264-291`（RandomDelay 公式与 CRC 折入）、`docs/re/trigger_system_manifest.md:626-631`（DA2 复核：31 项纯表现动作中唯一 RNG 契约项 = `0x62`）。
- **影响面**: **影响 §12.2 红线框读法**（RNG 条目加限定语，结论强度不变）；与 L1946 的〔勘误 ASM-FIX2-1〕注记**互补不冲突**（后者已要求"建议补注另帧尾再消费 1 次"，本补丁补的是**触发器侧条件消费面**）；**影响 §9 红线表口径**（"必须 bit 级一致"的范围需覆盖条件消费）；**不影响 §0 准则、不影响 §14/§15 新章**（新章 14.7 与本补丁同源）。

---

## 二、十节回执（AGENT_DELIVERY_FORMAT.md 骨架）

```text
[META]
task=task-7 (R5 补写 atlas 新章 §14 / §15)   executor=atlas-r5-triggers (DSH 子代理, Agent Teams 成员)
elapsed=约 3.0 h（含独立复算/门禁/写作；单会话连续执行，未跨会话）
mode=read-only（基线二进制与全部既有文档）+ write（仅 docs/re/atlas_rev/R5_triggers_save.md、out/re_work/atlas_rev/R5/**）
scope_declared=docs/re/atlas_rev/R5_triggers_save.md、out/re_work/atlas_rev/R5/**（含 claims_R5.txt）
```
### [0] 结论摘要

1. 产出 **3 个锚定补丁块**：PATCH-R5-01（新章 §14 触发器脚本运行时，APPEND_SECTION@L1981）、PATCH-R5-02（新章 §15 存档块与序列化全景，APPEND_SECTION@L1981）、PATCH-R5-03（§12.2 红线框 RNG 条目 ERRATUM@L1926）；**未提交任何 TOC 补丁**。
2. 新章的架构级核心结论：触发器是**事件驱动**（每逻辑帧唯一轮询器 `0x55AFB0` 只遍历"每帧 Tag 名单 `0x8B40C8`"，触发器对象本身不被每帧遍历）；其 PRNG 消费是**条件性**的 4 函数/9 指令；存档则是**两层结构**（核心驱动 + 子系统本地序列化器），容器为 **OLE2 复合文档**、对象寻址靠 **OLE CLSID** 而非自研 swizzle。
3. **7 项源文档侧勘误**（E-R5-1 读侧调用点数 17→18；E-R5-2/E-R5-3/E-R5-4 源章节字节/语义错位；E-R5-5 OLE 引用面补全 8→11 / 12）+ **1 项 atlas 侧补丁**（PATCH-R5-03）——全部附字节级依据。
4. **门禁全绿**：`python tools\verify_anchors.py` = **323/323 PASS**；`python tools\audit_bytes.py out\re_work\atlas_rev\R5\claims_R5.txt` = **696 条 OK=696 / MISMATCH·NOREAD=0**（其中 516 条由 6 个源断言库**独立复算 0 mismatch**，128 条为 R5 新增实证）。
5. **最大风险**：§14.7 的"全帧 RNG 总量非恒定 2"与 §12.2 现有红线框口径存在读法冲突（已用 PATCH-R5-03 限定，**须 Lead 裁决是否采纳**）；另 §14 U-7（轮询器锁存位是否含本机输入路径）**直接决定触发器在 MP 下的分叉面**，列为 P0。

### [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| 1 | 新章编号是否按卡指定 | 是：§14 / §15，均 `## 14. §14 … / ## 15. §15 …` 格式，未自选编号 | [实证] | 本文件 PATCH-R5-01/02 替换文本首行 |
| 2 | 新章是否用 APPEND_SECTION + 指定锚点 | 是：两章均 APPEND_SECTION，锚点 = atlas L1981 `## 附录 DA1 …`（实跑 grep 唯一） | [实证] | 本文件「锚点实跑 grep（原文）」块 |
| 3 | 是否提交 TOC 补丁 | **否**（TOC 由 Lead 统一重建）；也未改 §11（改为在章末给速查表供 Lead 并入） | [实证] | 本文件 §一 说明 + 14.12 / 15.11 |
| 4 | 触发器每帧在哪遍历 | 唯一位置 `LogicClass` 轮询器 `0x55AFB0`（`0x55DC9E` 唯一调用点，无条件）；遍历 `0x8B40C8`（`DynamicVectorClass<TagClass*>`，RTTI 定名） | [实证] | claims_R5 `0x55DC9E / 0x55DC9F?→` `0x55DC9E` / `0x55AFB0` / `0x7EA5A4` |
| 5 | 条件求值/动作执行入口数 | `RegisterEvent` 1 点、`HasOccured` 1 点、`Execute` 1 点（全镜像） | [实证] | `0x6E5414` / `0x726540` / `0x726605` |
| 6 | 三张派发表规模 | Action 145 / Event 49 槽·12 目标 / 队伍脚本 65 | [实证] | `0x6DD8DB` / `0x71E950` / `0x6E944B` + 表尾 `0x6E0030` |
| 7 | 触发器是否烧随机数（次数/位置） | 是：4 函数 9 指令（条件性）+ CRC 1 次；条件判定链 0 次 | [实证] | `0x72646A / 0x6E2CEB·4 / 0x6DE80F / 0x6F0B01 / 0x6F0CEE / 0x64DE3F` |
| 8 | 存档容器与对象寻址 | OLE2 复合文档（15 流）+ OLE CLSID 寻址（`StgCreateDocfile/StgOpenStorage/OleSaveToStream/OleLoadFromStream`） | [实证] | `0x67CF42 / 0x67E489 / 0x67FE45 / 0x67E840` |
| 9 | 35 块的真实性质 | 35 个**逐字节相同**的 127 B 模板函数，仅 `Save_Core` 顺序 call；实参对象 = 调用前 `mov edx` | [实证] | `0x67FDF0` / `0x67FE6E = C3` / `0x67DF0F` |
| 10 | 读侧是否对称 | **不对称**：8 段同形 OLE 读循环 + 18 调用点/16 目标助手 + 4 家族外读取器；无镜像块函数 | [实证] | `0x67E840 / 0x67E851…0x67EA32 / 0x67E62B` |
| 11 | 是否越界写入 | 否（详见 [5]） | [实证] | 本文件 [5] 节 |
| 12 | 未真机项是否标 [待实测] | 是：全部运行期/真机项均标 [待实测]（14.11 U-1/U-7/U-8/U-9、15.10 U-1/U-2/U-7、PATCH-R5-03 运行期分布） | [实证] | 本文件 14.11 / 15.10 |

### [2] 关键证据块（VA / FileOffset / 原始字节 / 反汇编 / xref；机器可读断言见 claims_R5.txt）

**(1) 触发器：每帧节拍与唯一入口**

```text
0x55DC9E = E8 0D D3 FF FF        MainLogicFrame: call 0x55AFB0（唯一调用点；FileOffset 0x15DC9E）
0x55DBCD = 39 3D 38 B2 A8 00     cmp [0xA8B238],edi（该条件块在 0x55DC99 汇合 ⇒ 轮询器无条件）
0x55AFE6 = 8B 0D CC 40 8B 00     ecx = [0x8B40CC]（每帧 Tag 名单 Items）
0x55AFEC = 8B 34 81              esi = Items[i]（下标升序）
0x684E2F = 89 3C 81              Items[Count] = tag（尾接；Count 在 0x8B40D8）
0x6E5414 = E8 A7 10 04 00        RaiseEvent → call 0x7264C0（RegisterEvent 唯一调用点）
0x726540 = E8 FB 83 FF FF        RegisterEvent → call 0x71E940（HasOccured 唯一调用点）
0x726605 = E8 A6 72 FB FF        FireActions → call 0x6DD8B0（Execute 唯一调用点）
0x6E55C0 = 8B 44 24 04 8B 51 28 89 50 28   TagClass::AddTrigger 头插（LIFO）
0x55DE9F = E8 CC 7D 1C 00        MainLogicFrame 尾部 → call 0x725C70（延迟析构抽干）
```
**(2) 触发器：RTTI 定名（R5 新增）**

```text
vtable 0x7F44E0 → [0x7F44DC] = 0x0080BBA0(COL) → [COL+0xC] → TD+8 = ".?AVTagClass`"
vtable 0x7F45C4 → … ".?AVTagTypeClass`" ; 0x7F5858 → ".?AVTriggerClass`"
vtable 0x7F5904 → … ".?AVTriggerTypeClass`" ; 0x7F5578 → ".?AVTEventClass`"
vtable 0x7F443C → … ".?AVTActionClass`"
vtable 0x7EA5A4 → [0x7EA5A0] = 0x008024B0(COL) → TD+8 = ".?AV?$DynamicVectorClass@PAVTagClass@@@@"
```
**(3) 触发器：PRNG 9 条消费指令 + CRC**

```text
0x726464 = 8D 88 18 02 00 00     lea ecx,[eax+0x218]   (ResetTimers: &ScenarioClass::Random)
0x72646A = E8 71 63 F3 FF        call 0x65C7E0  RandomRanged(0,arg)   [RandomDelay 装填]
0x6E2CEB = E8 90 9A F7 FF        call 0x65C780  Random()  #1  [Action 0x3A MeteorShower]
0x6E2D4E / 0x6E2D5A / 0x6E2DB0   Random() #2 #3 #4             [Action 0x3A]
0x6DE80F = E8 CC DF F7 FF        call 0x65C7E0  RandomRanged    [Action 0x62 PlaySoundEffectRandom]
0x6E17DE = E8 FD AF F7 FF        slave 0x6E1780 同体死副本（0 直呼点 ⇒ hook 不生效）
0x6F0B01 = E8 DA BC F6 FF        call 0x65C7E0  RandomRanged(1,100) [AITrigger 概率门]
0x6F0CEE =                        call 0x65C7E0  RandomRanged    [AITrigger 加权挑选]
0x64DE3F = E8 3C E9 00 00        call 0x65C780  Random()        [帧 CRC 0x64DAB0]
```
**(4) 存档：容器 / 模板族 / 驱动链**

```text
0x67CF42 = FF 15 C8 15 7E 00     Game::Load: call [0x7E15C8] StgCreateDocfile（全镜像唯一非 thunk 引用）
0x67E489 = 8B 1D E4 15 7E 00     Load_Core: ebx = [0x7E15E4] StgOpenStorage
0x67E840 = 8B 3D F8 15 7E 00     Load_Core: edi = [0x7E15F8] OleLoadFromStream（8 段读循环共用）
0x67E9B0 = 68 90 7C 7F 00 / 0x67E9B6 = FF D7    读循环指纹（push riid + call edi）
0x67FE45 = FF 15 F4 15 7E 00    模板块体内: call [0x7E15F4] OleSaveToStream
0x67FE6E = C3 / 0x67FE6F = 90   127 B 纯代码末字节(r et) / 128 B 口径的 1 B 填充
0x67D421 = E8 BA 23 00 00        Save_Core → call 0x67F7E0（S-1 标量块）
0x67F819 = 68 84 ED A8 00        S-1: push 0xA8ED84 (CurrentFrame)
0x67E429 = E8 E2 2B 0A 00        Save_Core 尾部 → call 0x721010（主题管理器，唯一调用者）
0x721010 = 56 8B 74 24 08 57 8B F9   写 [this+4] 与 [this+8] 两个 dword；0x72103A = C2 04 00
```
**(5) 读侧 18 个助手调用点（口径 A；★ = 源文档漏记的第 18 点）**

```text
0x67CF6B→0x680FF0  0x67CF7D→0x681080  0x67CF8A→0x6810A0  0x67CF98→0x681060
0x67CFB1→0x6810D0  0x67CFCA→0x681110  0x67CFE2→0x681130  0x67CFF3→0x6811C0
0x67D006→0x6812C0  0x67D022→0x681280  0x67D033→0x681200  0x67D044→0x681240
0x67D055→0x6812E0  0x67D193→0x680F70  0x67E461→0x680FF0  0x67E4CA→0x681840
0x67E4E3→0x6812D0  ★0x67E62B→0x680F70（E8 40 29 00 00；不同目标仍为 16）
```
**(6) OLE 序列化原语引用面（全量分类，R5 复算）**

```text
[0x7E15F4] OleSaveToStream：46 处 = 35（模板副本各 1）+ 0x67D353 + 0x4AF8A7 + 0x4B6366
   + 0x4DB7C0 + 0x5046CB + 0x54B88D + 0x5BE851 + 0x69EFB7 + 0x719DE7 + 0x75C7A7 + 0x7C88E0
[0x7E15F8] OleLoadFromStream：12 处 = 0x67C6B7 + 0x67E842 + 0x4AF7ED + 0x4B62AD + 0x4DB56A
   + 0x504065 + 0x54B7C6 + 0x5BE4DE + 0x69EEFD + 0x719D29 + 0x75C6ED + 0x7C88DA
```
> 全部 696 条断言的逐条明细（含 Capstone 反汇编回显）见 `out/re_work/atlas_rev/R5/gate_audit_bytes_full.txt`；断言生成脚本 `out/re_work/atlas_rev/R5/mkclaims.py`（可重跑）。

### [3] 勘误（逐条：目标文件:行号 ｜ 改前原文 ｜ 改后文本 ｜ 理由 ｜ 影响面）

> 纪律：**本节列出的 7 条勘误都在"我的写作用域之外"**（既有 docs/re/*.md），因此**只登记不改**，交 Lead 处理；atlas 自身的勘误已由 PATCH-R5-03 承载。

| # | 目标文件:行号 | 改前原文 | 改后文本 | 理由（字节依据） | 影响面 |
|---|---|---|---|---|---|
| E-R5-1 | `docs/re/savegame_block_manifest.md:859-862` | 口径 A 清单共 **17** 个调用点（§12.2） | 口径 A 调用点共 **18** 处（不同目标仍 16）：补 `0x0067E62B = E8 40 29 00 00 → 0x680F70` | 实跑 `0x67CE00–0x67EA40` 全区间 call 目标 ∈ [0x680F70,0x681840]：18 点 / 16 目标（claims_R5 `0x67E62B`） | 口径 B（15）不受影响；读档助手清单需 +1 |
| E-R5-2 | `docs/re/trigger_runtime_deep_dive.md:531` | `006E525E  A1 A8 F6 B0 00  mov eax,[0xB0F6A8] ; 延迟析构向量 Count` | `006E525E  A1 98 F6 B0 00  mov eax,[0xB0F698] ; 队列实例基址（= vtable，供 grow 路径 call [eax+8]）` | 实读 `0x6E525E = A1 98 F6 B0 00`；Count 的读/写真锚点 = `0x6E5272 = 8B 0D A8 F6 B0 00` / `0x6E527B = 89 0D A8 F6 B0 00` | 仅该行；§4.4 布局表述正确不受影响 |
| E-R5-3 | `docs/re/trigger_runtime_deep_dive.md:500` 附近（§7(2)） | `00726509  D3 E5  shl ebp,cl` | `00726509  8B CB  mov ecx,ebx` ／ `0072650B  D3 E5  shl ebp,cl` | 实读 `0x726509 = 8B CB`、`0x72650B = D3 E5`；同文档自带断言库 `out/re_work/triggers_deep/claims.txt` 已记 `0x726509 = 8B CB` | 正文与断言库口径需统一 |
| E-R5-4 | `docs/re/trigger_runtime_deep_dive.md:533`（§7(4) 末行） | `0055DE9F  E8 CC 7D 02 00  call 0x725C70` | `0055DE9F  E8 CC 7D 1C 00  call 0x725C70` | 实读 `E8 CC 7D 1C 00`（rel32 末字节 `1C`）；该文档 §6 Q4-4 行已按〔ASM-FIX-4〕订正但 §7 代码块未同步 | 文档一致性（同一文件内两处口径不一致） |
| E-R5-5 | `docs/re/savegame_block_manifest.md:261-262`（§2.5 IAT 表） | `OleSaveToStream` 非 thunk 引用列 8 项（含"35 个块函数内"1 行）；`OleLoadFromStream` 列 8 项 | 全量：`0x7E15F4` = 46 处（35 模板副本 + 11 非模板，补 `0x69EFB7 / 0x719DE7 / 0x75C7A7 / 0x7C88E0`）；`0x7E15F8` = 12 处（补 `0x69EEFD / 0x719D29 / 0x75C6ED / 0x7C88DA`） | 全 `.text` dword 引用扫描（claims_R5 逐点） | 影响"序列化原语引用面"完整性；补全后与 §15.7 子系统本地序列化器拓扑自洽 |
| E-R5-6 | `docs/re/trigger_system_manifest.md:55`（§1.1 门控行） | `TriggerClass+0x44（已过期）与 +0x30（已禁用）任一为真则整条跳过` | `+0x44 = Enabled（要求非 0）、+0x30 = Destroyed（要求为 0）` | `0x7264C4 = 8A 46 44 84 C0` / `0x7264CF = 8A 46 30 84 C0`；**该文档 §1.1 已在原地勘误（DA2-T1），此行属"旧行未同步"** | 仅引用一致性；atlas 引用须采 14.4 口径 |
| E-R5-7 | `docs/re/trigger_system_manifest.md:600`（§8.4 E-3 表） | `TriggerEvent 0x33 RandomDelay … 不消耗 RNG` | 该表述**在事件判定侧成立**，但须补限定："装填计时器时消耗 1 次 `RandomRanged`（`0x72646A`）" | `0x726464/0x72646A` + 时长公式 `0x72648B/0x726491` | 影响 RNG 契约面读法（与 §14.7 / PATCH-R5-03 同源） |

> **atlas 侧**：唯一需改的是 §12.2 红线框一行 ⇒ 已作为 **PATCH-R5-03** 提交（含原文对照），不在本节重复。

### [4] 未闭环清单（汇总 16 项；本节给阻断级别最高的 8 项，全表见 14.11 / 15.10）

| 缺口 | 为何无法静态闭环 | 下一步取证（可直接执行） | 级别 |
|---|---|---|---|
| 轮询器锁存位 `[Scenario+0x34AA/0x34AB/0x34BE]` 置位来源 | 只证"轮询器读它们"，写点未穷尽 | 扫全镜像这三处的写指令（含 `ecx=[0xA8B230]` 间接寻址），判定是否含本机输入（拾取木箱等）路径 | **P0** |
| 触发器"每帧总 RNG 消费量"分布 | 需运行期计数 | 真机 hook `0x65C780 / 0x65C7E0` 计数 + 与 CRC 帧号对拍（联机双端） | **P0** |
| `TagTypeClass::Array` 加载序 = INI 文本序？ | 未反汇编解析器键枚举循环 | 反汇编 `0x6E5ED0` 全函数；真机双端 dump 前 N 项比对 | P1 |
| 35 块实参对象类名 | `.bss` 对象无文件内 RTTI 引用（962 名 vs 43 描述符指针，无一命中） | 真机断 `0x67FDF0` / 35 个 call 点，读 `EDX→[EDX]→COL+0xC→TD+8` | P1 |
| 写侧 35 块 ↔ 读侧 8 读循环的映射 | 读侧无命名块/无镜像函数 | 以读循环前置 `Count` 全局与写侧 35 实参做地址级配对；真机对拍 `CONTENTS` 分段长度 | P1 |
| `0x722xxx` 簇 5 处 RNG 点上游归属 | 所在函数未回溯（**R5 已证不在读档直呼链上**） | 对 5 点函数起点做 `who`，回溯首个已知表调用者 | P1 |
| `0x67F7E0`（S-1）一次写入的全局完整清单 | 未枚举全部 Write 实参 | 枚举 `0x67F7E0–0x67F9E0` 内所有 `call [vtable+0x10]` 实参，与 §14 U-4 做差集 | P1 |
| AITrigger 门控 `TeamDelayTimer` 精确周期 | 未反汇编门控比较 | 反汇编 `0x4F8A00` 附近 `TimerStruct` 比较 + 与 house_team_ai_update.md 交叉 | P1 |

> 其余 P2 项（`0xABCCD8` 写入方、`EventKind 0x08/0x2F/0x3C/0x3D` 抛出点、延迟队列/游标是否进档、家族外序列化器类名、`Game::Save` 调用者、跨版本存档矩阵）。

### [5] 写作用域合规声明

**改动文件清单（全部在授权作用域内；本会话仅新建，无就地改写既有文件）**

| 路径 | 类型 | 字节数 | 行数 |
|---|---|---|---|
| `docs/re/atlas_rev/R5_triggers_save.md` | 新建（本文件） | 94,139 | 821 |
| `out/re_work/atlas_rev/R5/claims_R5.txt` | 新建（696 条断言） | 74,012 | 700 |
| `out/re_work/atlas_rev/R5/mkclaims.py` | 新建（断言生成/复算脚本） | 35,223 | 531 |
| `out/re_work/atlas_rev/R5/harvest_report.txt` | 新建（6 库复算报告，0 mismatch） | 336 | — |
| `out/re_work/atlas_rev/R5/gate_verify_anchors.txt` / `gate_audit_bytes_full.txt` / `gate_audit_head.txt` / `gate_audit_tail.txt` | 新建（门禁原文） | — | — |
| `out/re_work/atlas_rev/R5/scratch/{r5re.py,probe*.py,anchors.py,verify_claims.py}` | 新建（一次性取证脚本） | — | — |

**未触碰（只读）清单**：`docs/re/ARCHITECTURE_ATLAS.md`（**Lead 唯一写者**，本会话 0 次写入）、其它 R# 流文件、`ra2render/**`、`ra2youli/**`（基线二进制只读）、`REVERSE_ENGINEERING_AND_PATCHES.md`、任何既有 `docs/re/*.md`（只读：trigger_system_manifest.md / trigger_runtime_deep_dive.md / savegame_block_manifest.md / EVIDENCE_STANDARD.md / AGENT_DELIVERY_FORMAT.md）、`tools/**`（只调用，未修改）。

> **快照声明（并发环境）**：本批执行期间工作区由 Agent Teams 多流并发写入（`out/re_work/atlas_rev/{R1..R4,R6..R8,lead}/**` 在同一 2 小时窗口内有 mtime 变动，见 `out/re_work/atlas_rev/R5/scratch/scopecheck.py` 输出）。**这些写入均不属本流**；本流写入全部落在 `docs/re/atlas_rev/R5_triggers_save.md` 与 `out/re_work/atlas_rev/R5/**` 之内。
> **被审计目标的快照**：`docs/re/ARCHITECTURE_ATLAS.md` = 140,159 B / MD5 `6e790b55b2709ff5c41ad3f73f7e49e4` / mtime `2026-09-27T22:22:08`（**本流 0 次写入**，行号口径 = 该快照的 2002 行）；`ra2youli/gamemd.exe` = MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`（只读未变）。

**基线只读自证**：`ra2youli/gamemd.exe` = 4,825,360 B，MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`（由 `verify_anchors.py` 的 `.text` 段哈希 `c0368a179f6e...` 与 `.detour` 原生签名双重印证；两次门禁运行（开工/收尾）均 PASS 同值）。

### [6] 门禁实跑输出（原文粘贴）

**① `python tools\verify_anchors.py` → 323/323 PASS（收尾实跑）**

```text
===================================================================================================================
  RA2/YR 二进制决定性锚点自动化回归测试套件 (verify_anchors.py)
===================================================================================================================
目标文件 : D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe (大小: 4,825,360 字节, ImageBase: 0x400000)
断言文件 : D:\Project\ra2-campaign-forge\docs\re\anchor_claims.txt
反汇编器 : Capstone x86-32 引擎已就绪
-------------------------------------------------------------------------------------------------------------------
[基线完整性审计]
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
-------------------------------------------------------------------------------------------------------------------
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
===================================================================================================================
```
**② `python tools\audit_bytes.py out\re_work\atlas_rev\R5\claims_R5.txt` → 696 条全 OK（首 10 行 + 汇总行原文）**

```text
VA         期望字节                       实际字节                   判定     标签/上下文
--------------------------------------------------------------------------------------------------------------
0x4926c0   52 8b 54 24 20             52 8b 54 24 20         OK     [da4] push edx; mov edx,[esp+0x20]（N-2 订正；原记 66 8B 01） | push edx
0x4af7ed   f8 15 7e 00 5f 5e          f8 15 7e 00 5f 5e      OK     OleLoadFromStream ref (0x4AF7ED) | clc
0x4af8a7   f4 15 7e 00 8b f0          f4 15 7e 00 8b f0      OK     OleSaveToStream ref (0x4AF8A7) | hlt
0x4c6340   8b 44 24 04 6a 00 6a 44 51 8b 10 50 ff 52 10 c2 04 00   OK     [save_blocks] raw "write 0x44 bytes" helper | mov eax, [esp + 4]
0x4f8a6a   e8 41 80 1f 00             e8 41 80 1f 00         OK     [triggers_deep] AITrigger caller #1 (HouseClass AI cluster) | call 0x6f0ab0
0x4fa220   e8 8b 68 1f 00             e8 8b 68 1f 00         OK     [triggers_deep] AITrigger caller #2 (HouseClass AI cluster) | call 0x6f0ab0
0x559f3a   8b 0d 60 d5 83 00          8b 0d 60 d5 83 00      OK     [save_blocks] other reader of the magic global (LoadOptionsClass path) | mov ecx, [0x83d560]
0x55afb0   83 ec 28 8b 15 40 cd ab 00 89 4c 24    OK     per-frame poller prologue | sub esp, 0x28
0x55afd3   89 15 40 cd ab 00          89 15 40 cd ab 00      OK     [triggers_deep] poller: store global counter 0xABCD40 | mov dword ptr [0xabcd40], edx
0x55afdb   a3 dc 3c a8 00 0f          a3 dc 3c a8 00 0f      OK     poller: reset iteration cursor [0xA83CDC] | mov dword ptr [0xa83cdc], eax
--------------------------------------------------------------------------------------------------------------
合计 696 条：OK=696  MISMATCH/NOREAD=0
```
**③ 独立复算（第三方口径，非 audit_bytes）：6 个源断言库逐条重读 → 0 mismatch**

```text
out/re_work/triggers_deep/claims.txt | parsed=174 mismatch=0
out/re_work/save_blocks/claims.txt | parsed=82 mismatch=0
out/re_work/triggers/claims.txt | parsed=77 mismatch=0
out/re_work/savegame/claims.txt | parsed=143 mismatch=0
out/re_work/da2/claims.txt | parsed=28 mismatch=0
out/re_work/da4/claims.txt | parsed=12 mismatch=0
（复算脚本：out/re_work/atlas_rev/R5/mkclaims.py；另 out/re_work/atlas_rev/R5/scratch/verify_claims.py 对 claims_R5.txt 逐行独立重读 → 无 BAD 行）
```
> **VA 覆盖度自证（R5 自跑 `out/re_work/atlas_rev/R5/selfcheck.py`）**：补丁块文本内 < `0xA00000` 的地址型 VA 共 **673** 个；其中 **651 个有字节断言支撑**（`claims_R5.txt` / `out/re_work/asm_scan/claims.txt` / `docs/re/anchor_claims.txt` 任一命中）。余下 **22 处（10 个唯一 VA）**为**数据段全局**（`0x87F778` / `0x886B88` / `0x89EA40` / `0x8A38E0` / `0x8B40C8` / `0x8B40CC` / `0x8B40D8` / `0x8B4120` / `0x8B4178` / `0x8B41A8`），位于 `.data` 的零填充尾区（`rawptr+SizeOfRawData` 之后，**无文件字节**）⇒ **静态不可断言**；本文件对每个此类全局都给出了**引用它的指令级断言**作为等价支撑（例：`0x8B40C8` ↔ `0x55AFE6 = 8B 0D CC 40 8B 00` / `0x55B169 = 8B 0D D8 40 8B 00`；`0x8B4120` ↔ `0x67E0A8 = BA 20 41 8B 00`；`0x89EA40` ↔ `0x67F7E0` 序列）。**这是数据段全局的固有边界，不是遗漏**；Lead 的 `tools/atlas_va_crosscheck.py` 若把这类 VA 计入"证据悬空"，建议按本注记口径豁免。

### [7] 风险与红线提示

| # | 是否触及 | 说明 |
|---|---|---|
| ① 同步语义 / 命令序 | **触及（文档层）** | §14.7 给出"触发器 PRNG 消费为条件性、全帧总量非恒定 2"⇒ 任何以"消费量恒定"为前提的改动/对拍口径都会误判。**需要 MP 门控矩阵 + 真机双端逐帧对拍验收**，禁止宣称"零风险/零 Desync"。 |
| ② 随机数消费序 | **触及（文档层）** | 触发器侧 9 条消费指令的**顺序**已逐条钉住（T1–T6 表）；顺序本身未被改动，但"次数依赖世界状态"这一事实必须在任何 hook 设计中显式处理。 |
| ③ 存档结构 | **触及（文档层）** | §15 全部结论均为**静态只读**；本章**不提出任何存档格式改动**。若后续要动 S-1/模板族/流布局，必须按 §15.8 红线表评估（其中 RNG/坐标同属 CRC 输入）。 |
| ④ 渲染像素等价性 | **不触及** | 本章不含渲染路径结论。 |
| ⑤ 基线二进制 | **不触及** | 全程只读；未启动游戏、未注入、未改任何字节（[5] 的 MD5/段哈希自证）。 |

> **须显式声明的边界**：本批所有"运行期行为"结论均为 [待实测]；本文件**不宣称**任何性能/生效性收益，也不宣称对原版行为做过真机验证。

### [8] 交付物清单

| 类型 | 路径 | 规模 |
|---|---|---|
| 新文档 | `docs/re/atlas_rev/R5_triggers_save.md` | 820 行（含 3 个锚定补丁块 + 十节回执 + 覆盖度自证表） |
| 断言 | `out/re_work/atlas_rev/R5/claims_R5.txt` | **696 条**（harvest 516 + R5 新增 180；VA 去重后 696 个断言点） |
| 脚本 | `out/re_work/atlas_rev/R5/mkclaims.py` + `out/re_work/atlas_rev/R5/scratch/`（r5re.py、probe2-13.py、anchors.py、verify_claims.py、t*.py） | 16 个（可重跑复现全部字节断言与锚点 grep） |
| dump/报告 | `out/re_work/atlas_rev/R5/` 下 harvest_report.txt、gate_verify_anchors.txt、gate_audit_bytes_full.txt、gate_audit_head.txt、gate_audit_tail.txt | 5 个（门禁原文 + 6 库复算报告） |
| 补丁块 | 3 个：PATCH-R5-01（§14 新章）、PATCH-R5-02（§15 新章）、PATCH-R5-03（§12.2 ERRATUM） | 全部含「行号 + 该行前 40 字符 + 可直接粘贴 markdown」 |

### [9] 待裁决项（需要 Lead / 人决定的分叉）

| # | 分叉 | 选项 | 建议与理由 |
|---|---|---|---|
| 1 | **§11 速查表由谁合并** | (a) Lead 合并（本文件 14.12 / 15.11 已给表）｜(b) 我另提交 §11 INSERT 补丁 | **建议 (a)**：任务卡明确「Lead 会并入 §11」，且 §11.1/§11.2 有既定三表版式；由 Lead 统一插入可避免重复行与版式冲突。若需我做，可在 1 轮内按 §11.2 现有列结构产出 INSERT 补丁。 |
| 2 | **PATCH-R5-03 是否采纳** | (a) 采纳（红线框加限定语）｜(b) 不采纳，仅靠 §14.7 说明 | **建议 (a)**：§12.2 是产品级红线框，读者极易把「恰 2 次」当恒定量；限定语不改结论强度，且与既有〔ASM-FIX2-1〕注记同向。 |
| 3 | **E-R5-1..E-R5-7 由谁执行** | (a) Lead 批处理（跨文件最小订正清单）｜(b) 指派 R5 追加一轮 | **建议 (a)**：7 条全部落在我的禁写区（既有 docs/re/*.md）。其中 E-R5-1/E-R5-5 属清单补全，E-R5-2/E-R5-3/E-R5-4 属字节/偏移错位，均为低风险就地勘误。 |
| 4 | **新章插入方向与 TOC** | Lead 按流号顺序插入 R1–R8 新章 | 本流只负责 §14/§15 文本；插入点在 DA1 之前或之后、以及 TOC 行由 Lead 统一裁决 —— 本文件不含 TOC 补丁，也不假设插入方向。 |
| 5 | **§14.7「RNG 总量」表述粒度** | (a) 保留 `2 + Σ(条件消费)` 表述｜(b) 追加真机计数表 | **建议 (a) 先落地**；(b) 需真机（U-9），建议作为独立验收任务派发（联机双端逐帧对拍）。 |

---

## 三、覆盖度自证表（来源文档 §小节 → 命中的 PATCH-R5-NN / 或不入 atlas 的理由）

### 3.1 docs/re/trigger_runtime_deep_dive.md（631 行）

| 源小节 | 行范围 | 命中 | 说明 |
|---|---|---|---|
| §0 结论速览 C1–C6 | 12-21 | PATCH-R5-01 §14.1（C1–C10） | 6 条全吸收 + 补 4 条（C7 延迟队列 / C8 AITrigger RNG / C9 无 MP 门控 / C10 存档耦合） |
| §1.1 类与实例链（vtable/数组表） | 27-39 | §14.2 | 表全量吸收 + **R5 新增 RTTI 定名列** |
| §1.2 每帧轮询器 + 10 kind 表 | 41-94 | §14.3 | 表与调用点字节全量；补 `0x55B011` 短路字节与两处每帧边界语义 |
| §1.3 RaiseEvent 漏斗（73 调用点聚簇） | 96-130 | §14.4 | 聚簇表 + 前置门字节全量 |
| §1.4 求值/执行唯一性 | 132-164 | §14.4 + §14.5 | 唯一入口表；门控命名勘误口径（关联 E-R5-6） |
| §1.5 第二每帧入口 TeamLeavesMap | 166-170 | §14.3 | 吸收（`0x6E92F3 / 0x6EA4B1` + `0x6E9304 / 0x6EA4C0`） |
| §2 求值顺序与锁步确定性 | 174-224 | §14.6 | 三层插入序表 + 无地址比较负证 + 游标回退 + 存档原序 |
| §3.1 两个 Randomizer + GetFlags 位语义 | 229-244 | §14.7 + §14.2 | bit `0x10` = 每帧准入，以「注册判据」形式吸收 |
| §3.2 PRNG 消费逐条清单 | 246-260 | §14.7（T1–T6） | 9 条指令 + 死副本 T3′；补「9 条指令」计数口径 |
| §3.3 条件侧消费与时长公式 | 262-282 | §14.7 | 公式 + 装填条件 + 5 个 ResetTimers 调用点 |
| §3.4 帧 CRC 与 RNG | 284-291 | §14.7 + PATCH-R5-03 | 吸收并升级为 §12.2 限定语 |
| §3.5 对 manifest §9 的补强 | 293-297 | §14.7 | 0x62 黄 / 0x63 绿 / 0x3A RNG×4 三条全吸收 |
| §4.1–4.2 Tag/Trigger 生命周期 | 303-334 | §14.8 | 全量；补队列 append/grow 正确字节（E-R5-2） |
| §4.3 触发后置位三分支 | 336-346 | §14.4 + §14.8 | Persistence 三分支 + 位图位序 = 链序 |
| §4.4 Destroyed 与延迟析构队列 | 348-353 | §14.8 | 吸收 + 修正 §7 代码块（E-R5-2） |
| §4.5 EVA 播报链路 | 355-367 | §14.10（§6 契约行） | 动作 0x15 → 0x752480 唯一路径 |
| §4.6 与存档的关联点 | 369-380 | §14.10 + §15.9 | 每帧向量 / CurrentFrame / 位图 / IPersistStream v[5]·v[6] / RNG 禁改 |
| §5 AITrigger 与普通触发器 | 384-421 | §14.9 | 差异表全量 + 「共享同一 RNG 流」风险 |
| §6 逐条结论表 Q1–Q6 | 425-468 | 全章锚点 | 逐条回填 §14.1–§14.9（不逐条复制，避免搬运） |
| §7 关键证据（原始机器码） | 472-548 | §14 各节 + [2] 节 | 4 处代码块逐条复算：2 处与实读不符（E-R5-2 / E-R5-3 / E-R5-4） |
| §8 未闭环 U-1..U-8 | 552-565 | §14.11 | 全量吸收 + **R5 新增 U-9** |
| §9 改动清单 + 门禁输出 | 569-613 | — | **不入 atlas**：过程性交付记录，非架构结论；其门禁值由本文件 [6] 节独立重跑取代 |
| 附 claims 主题分布 | 617-631 | [8] 节统计 | 174 条已独立复算并并入 claims_R5.txt |

### 3.2 docs/re/trigger_system_manifest.md（1076 行）

| 源小节 | 行范围 | 命中 | 说明 |
|---|---|---|---|
| §0 结论速览（三表 + 五硬结论 + 联机速览） | 8-33 | §14.5 + §14.1 C6/C9 | 三表规模与索引语义；4 空实现动作；无 MP 门控 |
| §1.1 类与实例链 + 门控 | 36-67 | §14.4 | 接线（唯一调用方）吸收；门控行按 DA2-T1 口径订正（E-R5-6） |
| §1.2 实例字段布局（+0x24..+0x90） | 69-93 | §14.4 + §14.2 注 | 只吸收与架构契约相关的 3 项（位序 / Size 自证 / Revent 门控）；逐字段表留源文档 |
| §1.3 与 NetworkEvent 的真实关系 | 95-98 | §14.10（§9 契约行） | 「触发器不产生 NetworkEvent」负证 |
| §2 Action 表全文（145 项） | 102-283 | §14.5（规模/边界/代表项） | **按纪律不搬运 145 行大表**；atlas 给规模 + 自证字节 + 3 个代表项口径 |
| §3 Event 表（49 槽 / 62 kind） | 284-381 | §14.5 | 两级/四级派发结构 + 表长自证字节 |
| §4 附录 A 队伍脚本动作表（65 项） | 382-467 | §14.5（表 C） | 规模 + 跳表字节 + table[49] 归属（Action 49 谜题） |
| §5 GetMode / GetFlags 类别与位域 | 468-513 | §14.5（flags 列）+ §14.7 | flags 实测只有 {0,2}（7 项）；GetMode 属参数序列化类别 ⇒ 与 §15 的 S-1 相关（15.10 U-6） |
| §6 名称来源与证据级别 | 514-519 | §14.5 | 口径条：本体无名字表 ⇒ 名称列 [推演/命名] |
| §7 字节断言复算 | 523-556 | [6] 节 | 77 条已独立复算 0 mismatch |
| §8 交叉引用与勘误 E-1..E-4 | 560-607 | §14.5 + E-R5-7 | E-1（Action 49 归属）/ E-2（数值空间）/ E-4（空实现）吸收；E-3 补限定 |
| §9 联机风险判定规则与清单 | 611-644 | §14.1 C9 + §14.7 | 红/黄/绿口径 + 纯表现 31 项 + 高危事件输入 + 改地图 11 项 |
| §10 未闭环与下一步 | 648-659 | §14.11（U-5 口径） | 与深潜专章 U 项合并去重 |
| 附录 C 26 项入口证据 | 664-1021 | — | **不入 atlas**：逐项指令级证据属源文档粒度；架构结论（内联体为主 / hook slave 不必然生效）已在 §14.5 |
| §11–§12 产物索引 / 验收自证 | 1022-1076 | — | **不入 atlas**：过程性记录 |

### 3.3 docs/re/savegame_block_manifest.md（1055 行）

| 源小节 | 行范围 | 命中 | 说明 |
|---|---|---|---|
| §0 结论速览 | 14-37 | §15.1（C1–C8） | 全量吸收；魔数行采 U-2 定谳口径 |
| §1.1–1.2 模板族指纹与语义 | 41-128 | §15.4 | 127/128 B 双口径 + 指令级语义 |
| §1.3 调用者取证 | 130-141 | §15.4 | 「0 处 E8/E9 + 35 处直呼」 |
| §2.1–2.3 Save/Load 外层与容器 | 146-241 | §15.2 / §15.3 / §15.5 | 三层驱动链字节全量 |
| §2.4 xref | 242-250 | §15.3 注 + §15.10 U-3 | `Game::Save` 0 引用（未闭环） |
| §2.5 序列化原语 = OLE | 252-286 | §15.6 + E-R5-5 | 补全引用面 46 / 12 |
| §3 逐块清单（35 → 实参对象） | 291-341 | §15.4 | 映射口径（`mov edx` 实参）+ 类名未闭环 |
| §4 内联向量块 28 个 + COUNT/ITEMS 表 | 345-416 | §15.3 + §15.1 C3 | 28/28 布局校验；28 个 COUNT 全局表属「逐表命名」粒度 ⇒ atlas 只给结构与校验结论 |
| §5 存档文件格式（真机档） | 420-465 | §15.2 | CFB 目录项 + `CONTENTS` 头 |
| §6 CurrentFrame 与联机一致性 | 469-477 | §15.8 + §15.9 | 帧阈值块与 CRC 阈值同段（[推演]） |
| §7 字节断言审计 | 481-520 | [6] 节 | 82 条已独立复算 0 mismatch |
| §8 交叉引用与勘误 1–5 | 571-692 | §15.8 | 结构性表述订正与净清单已吸收进兼容性红线 |
| §9 未闭环 + 9-bis 定谳 | 693-752 | §15.10 | U 项合并去重 |
| §10 证据产物索引 / §11 一句话给下游 | 753-795 | — | **不入 atlas**：过程性记录 |
| §12 专项核对定谳（MD5 口径 / 读档计数 / U 项 / 兼容性红线 / 逐块证据表） | 796-1055 | §15.4 + §15.5 + §15.8 + E-R5-1 + E-R5-5 | 逐块静态证据表 35 行并入 §15.4 结构结论；口径 A 调用点数订正 |
| §12.4.1–12.4.3（U-2 / U-3 / U-9 闭环细节） | 939-1003 | §15.2 + §15.3 | 魔数流级、CurrentFrame 归属 S-1、IAT 定名 |

> **口径声明**：本表「命中」= 该源小节至少有一条结论进入补丁块。「不入 atlas」两类理由：①**粒度**（源文档逐项大表 / 逐条指令证据，atlas 只保留架构级结论与代表锚点，避免把 atlas 变成搬运合集）；②**性质**（过程性交付记录、门禁输出、产物索引，不属架构知识）。

---

*R5 交付完成 · 2026-09-29 · atlas 新章 §14/§15 锚定补丁块（3 块）+ 696 条可复算字节断言 + 7 项源文档勘误登记*
