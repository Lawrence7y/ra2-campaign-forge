# 触发器系统全表（Event / Action）—— 派发表逐项解算
> 目标二进制：`ra2youli\gamemd.exe`（ImageBase `0x400000`，无 `.reloc`；文件偏移 = VA − 0x400000；`.bss` 无文件数据）
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 证据级别：`[实证]` = VA + 文件偏移 + 原始字节（可用 `tools/audit_bytes.py out/re_work/triggers/claims.txt` 复算）；`[推演]` = 由相邻证据推断；`[待实测]` = 需运行验证
> 关联文档（只读引用）：`net_sync_checksum.md` §9（NetworkEvent 填充序）、§2（RNG）、§3（Checksum）、§5（红线表）；`superweapon_re.md`（超武授予路径）；`house_team_ai_update.md`（TeamClass 脚本表）

---

## 0. 结论速览

### 0.1 三张派发表（互不相同，勿混）

| 表 | 所有者 / 入口 | 跳转表 VA | 表项数 | 索引语义 | 索引上界指令（实证） |
|---|---|---|---|---|---|
| **A. 触发器动作表（Action）** | `TActionClass::Execute 0x6DD8B0` | `0x6DFDEC` | **145** | `ActionKind − 1`，`ActionKind ∈ 1..0x91` | `0x6DD8DB: 81 FA 90 00 00 00`（`cmp edx,0x90`）→ `0x6DD8E7: FF 24 95 EC FD 6D 00` |
| **B. 触发器事件表（Event）** | `TEventClass::HasOccured 0x71E940` | `0x71F218`（12 项）+ 字节选择表 `0x71F248`（49 B） | **12 个目标 / 49 个 kind 槽** | `EventKind − 0x0D`，`EventKind ∈ 0x0D..0x3D` | `0x71E950: 8D 41 F3 83 F8 30`（`lea eax,[ecx-0xD]; cmp eax,0x30`）→ `0x71E964: FF 24 95 18 F2 71 00` |
| **C. 队伍脚本动作表（Team Script）** | `TeamClass::AI 0x6E9050` | `0x6E9F74` | **65** | `脚本动作号 0..0x40`（**不是** TriggerAction） | `0x6E944B: 83 F8 40`（`cmp eax,0x40`）→ `0x6E945B: FF 24 85 74 9F 6E 00` |

**表长自证（口径）**：A 表长度由「5 字节 `cmp edx,0x90` 上界（0x90+1=145 项）+ `jmp [edx*4+0x6DFDEC]` 基址」唯一确定；C 表同理由 `cmp eax,0x40`（65 项）+ `jmp [eax*4+0x6E9F74]` 确定。B 表是**两级**结构：字节选择表 49 项（`EventKind 0x0D..0x3D`）映射到 12 个目标 dword。

### 0.2 五条硬结论

1. **Action 表是 145 项、以 `ActionKind−1` 索引的紧凑跳表** —— 与 YRpp `enum class TriggerAction`（`None=0x00 … JumpCameraHome=0x91`）**逐项对齐**（0x00 无表项，走 `ja` 默认路径 `0x6DFDDD`）。[实证]
2. **Action 表里存在 4 个「声明了但空实现」的动作**：`AllowWin(0x0F)`→`0x6DFDDD`（仅 epilogue）、`ChangeZoomLevel(0x27)`/`ActivateFirestorm(0x5C)`/`DeactivateFirestorm(0x5D)`→`0x6DFDDB`（`B0 01` = `mov al,1` 后直接返回）。前者是 TS 遗留、后两者是 TS 专属 Firestorm 功能在本作未实现。[实证]
3. **Event 表由 4 层派发串成**：1 级 12 个「全局/自身」事件（`0x71F218`）；2 级 2 目标门（`0x71F27C` + 选择表 `0x71F284`，区分「对象身份判定」与「扁平比较链 `0x71ECAF`」）；3 级 14 目标（`0x71F2C0` + 选择表 `0x71F2F8`，按**房级计数/最近建造类型**判定）；4 级 10 目标（`0x71F328` + 选择表 `0x71F350`，按 `HouseClass` 电力/击杀计数判定）。[实证]
4. **接线（唯一调用方）**：`TriggerClass::RegisterEvent 0x7264C0` → `TEventClass::HasOccured 0x71E940`（`0x726540: E8 FB 83 FF FF`）；`TriggerClass::FireActions 0x7265C0` → `TActionClass::Execute 0x6DD8B0`（`0x726605: E8 A6 72 FB FF`）；`TriggerTypeClass::GetFlags 0x7271E0` → 事件 `0x71F680` + 动作 `0x6E3EE0` 按位或。[实证]
5. **`Action 49 / Success`（派单给定锚点）不属于本表**：`0x006E9CE8 = C6 86 84 00 00 00 01` 位于 `TeamClass::AI 0x6E9050` 的**队伍脚本动作表 C**（`0x6E9F74[49] = 0x6E9CE1`，同体另有 `C6 86 80 00 00 00 01` 写 `[esi+0x80]`），与 `TActionClass`（表 A）无关 —— 详见 §8 勘误。[实证]

### 0.3 联机判定速览（详见 §9）

- 表 A 145 项中：**改逻辑状态 `L` 97 项、改地图/地形 `M` 11 项、纯表现 `P` 31 项、财金+逻辑 `$+L` 2 项、空实现 `-` 4 项**（口径见 §9；总数 145 = 表 A 表项数）。
- **纯表现 31 项**（音频/镜头/闪示/UI 局部）不进同步契约，是本项目可独立优化的候选面；其余 114 项（含空实现 4 项）**改语义即多端分叉**。
- 表 B 全部为**只读判定**（不写对局状态），但其中 `SelectedByPlayer(0x21)`、`EnemyInSpotlight(0x23)`、`PickupCrate*(0x31/0x32)`、`DiscoveredByPlayer(0x04)` 依赖**本机交互/可见性**，是 desync 的高危输入面。

﻿---

## 1. 系统结构与运行管线（地址级 [实证]）

### 1.1 类与实例链

```
TriggerTypeClass  ──(每张地图触发器类型)──> 事件链表 [type+0xAC] / 动作链表 [type+0xB0]
      │
      ├─ TriggerTypeClass::GetFlags 0x7271E0 ─> TEventClass::GetFlags 0x71F680
      │                                          TActionClass::GetFlags 0x6E3EE0  （按位或，递归父类）
      │
   TriggerClass（实例：附着于对象/房）
      ├─ RegisterEvent 0x7264C0 ─> TEventClass::HasOccured 0x71E940
      │                            + GetStateA 0x71F950 / GetStateB 0x71F9C0（重复触发语义）
      └─ FireActions   0x7265C0 ─> 遍历动作链，逐个 TActionClass::Execute 0x6DD8B0
                                    （返回值 1 表示"至少一个动作成功"，0x72660E: mov bl,1）
```

- `FireActions` 动作遍历：`esi = [TriggerType+0xB0]` → `call 0x6DD8B0`（`0x726605`）→ `esi = [esi+0x28]`（`NextAction`，`0x726610`）。[实证]
- `RegisterEvent` 事件遍历：`edi = [TriggerType+0xAC]` → `call 0x71E940`（`0x726540`）→ `esi=[esi+0x28]`。两层链表节点偏移均为 `+0x28`。[实证]
- 前置门控：`TriggerClass+0x44`（已过期）与 `TriggerClass+0x30`（已禁用）任一为真则整条跳过（`0x7264C4`/`0x7264CF`、`0x7265C3`/`0x7265CA`）。[实证]

> **【勘误 DA2-T1 · 2026-09-27】`TriggerClass` 实例门控字段名错位（原文保留，见下对照；本节编号自成一系，与 §8.2/§8.3 的 E-1/E-2 无关）**
> 
> - **原表述**：`TriggerClass+0x44`（**已过期**）与 `TriggerClass+0x30`（**已禁用**）**任一为真则整条跳过**（`0x7264C4`/`0x7264CF`、`0x7265C3`/`0x7265CA`）。
> - **更正表述**：`TriggerClass+0x44` = **`Enabled`**（门控要求 **≠0**：为真才放行）；`TriggerClass+0x30` = **`Destroyed`**（门控要求 **==0**：为真即整条跳过）。原文两处错：① 两个字段名均错位（`+0x44` 不是「已过期」、`+0x30` 不是「已禁用」）；② 「任一为真则跳过」对 `+0x44` **方向写反**（真才是放行条件）。
> - **依据（VA + 原始字节，机器可复算 `out/re_work/da2/claims.txt` 28 条全 OK）**：
>   - `0x007264C4 = 8A 46 44 84 C0 0F 84`（`mov al,[esi+0x44]; test al,al; je 0x7265b4`）⇒ **`+0x44`==0 直接跳过**；`0x007264CF = 8A 46 30 84 C0 0F 85`（`mov al,[esi+0x30]; test al,al; jne 0x7265b4`）⇒ **`+0x30`!=0 跳过**。`FireActions 0x7265C0` 同构：`0x007265C3 = 8A 47 44 84 C0`（`je 0x726620`）/ `0x007265CA = 8A 47 30 84 C0`（`jne 0x726620`）。
>   - 构造函数 `0x725FA0`：`0x00725FB8 = 88 5E 30`（`mov [esi+0x30],bl`，`bl=0`）与 `0x00725FCA = C6 46 44 01`（`mov byte [esi+0x44],1`）⇒ **`+0x30` 初值 0 / `+0x44` 初值 1**。
>   - 语义定名：`Destroy 0x726720` 首句 `0x00726723 = C6 46 30 01`（置 `Destroyed=1`）；`Enable 0x7268F0 = C6 41 44 01`+`jmp 0x726400`(`ResetTimers`)、`Disable 0x726900 = C6 41 44 00`。
>   - 只读交叉源：`YRpp/TriggerClass.h:122` `bool Destroyed; // ActionClass::DestroyTrigger called on`、`:126` `bool Enabled;`，其字段序 `Type(+0x24) / NextTrigger(+0x28) / House(+0x2C) / Destroyed(+0x30) / Timer(+0x34) / OccuredEvents(+0x40) / Enabled(+0x44)` 与上述字节逐字吻合。
> - **错位根因（供 Lead 参考）**：§1.2 表把 **`TActionClass+0x44 = Waypoint`**（动作参数字段）与 **`TriggerClass+0x44`**（实例门控）当成同一物，实例门控因此被套上了动作字段的语义。
> - **影响面**：仅 §1.1 本行；§2/§3 派发表与 §9 联机判定口径**不受影响**。

﻿### 1.2 实例字段布局（由指令反推，两表类同构）

`TActionClass` / `TEventClass` 均继承 `AbstractClass`，字段偏移由指令实证：

| 偏移 | TActionClass | TEventClass | 关键实证指令 |
|---|---|---|---|
| `+0x24` | `ArrayIndex` | `indexInArray` | **`0x6E4650: 8B 41 24 C3`**（`GetArrayIndex` = `mov eax,[ecx+0x24]; ret`）[实证] |
| `+0x28` | `NextAction` | `NextEvent` | `0x726610: mov esi,[esi+0x28]`（链表遍历） |
| `+0x2C` | `ActionKind` | `EventKind` | `0x6DD8D7: mov edx,[esi+0x2c]`；`0x71E94D: mov ecx,[ebp+0x2c]` |
| `+0x30` | `TeamType*` | `TeamType*`（AITeamType） | CreateTeam/Reinforcement 取队伍 |
| `+0x34` | `Bounds`（`RectangleStruct`，动作 40 用） | `arg`（事件参数） | `0x71EB53: mov edx,[ebp+0x34]`（GlobalSet 参数） |
| `+0x44` | `Waypoint` | — | `0x6DD91D` 起（IonCannonStrike 取路径点） |
| `+0x48` | `Value2` | — | `0x6DD33D: mov eax,[esi+0x48]`（`mode=0x2E` 存档分支） |
| `+0x4C` | `TagType*` | — | `0x6DD3DE: mov edx,[esi+0x4c]`；DestroyTag 读同址 |
| `+0x50` | `TriggerType*` | — | `0x6DD3BE: mov edx,[esi+0x50]`；DestroyTrigger/ForceTrigger 读同址 |
| `+0x54` | `TechnoID[0x19]`（字符串） | — | `0x6DD330: lea ebp,[esi+0x54]`（存档按名字保存） |
| `+0x6D` | `Text[0x20]`（字符串） | — | `0x6DD406: lea ebp,[esi+0x6d]`（`mode=0x27` 分支） |
| `+0x90` | `Value`（多用整型） | — | `0x6DD310: mov ecx,[esi+0x90]`；超武编号见 `superweapon_re.md` |
| `+0x38` | — | `TechnoName[0x1C]` | `0x71EA47: lea edx,[ebp+0x38]`（TechTypeExists 比对对象类型名） |
| `+0x54` | — | `House*` | [推演]（`HasOccured` 经 `call 0x502D30` 由 `arg` 反查房指针） |

> **总长自证 [实证]**：`TActionClass::Size 0x6E4630 = B8 94 00 00 00 C3`（`mov eax,0x94; ret`）→ 实例大小 **0x94**，与"`Value` 之后即结束"的字段算术**完全吻合**（`0x90+4=0x94`）。
>
> 布局自检 [实证]：`0x24`(index) `+4`(next) `+4`(kind) `+4`(team) `+0x10`(bounds) `+4`(wp) `+4`(v2) `+4`(tag) `+4`(trigtype)
> `+0x19`(TechnoID → 0x6D) `+0x20`(Text → 0x8D) `+3`(align，YRpp `align_8D[3]`) = `Value@0x90` —— 算术与三条独立指令读写完全吻合。

### 1.3 与网络事件（`net_sync_checksum.md` §9）的真实关系 [实证]

- 触发器侧代码（`0x6DD000–0x6E5000`、`0x71E000–0x727000`）**没有任何一处调用** `FillEvent_*`（`0x4C6650/0x4C66C0/0x4C6720/0x4C6780/0x4C6800/0x4C6970/0x4C6AE0/0x4C6B60`）。全部调用点落在 UI/生产/脚本路径（`0x4AB9CC`、`0x6AA600`、`0x4F10E0` 等），见 `out/re_work/triggers/xrefs.txt`。
- 结论：**触发器 Event/Action 是本地求值的判定链，不产生 NetworkEvent 命令**；§9 的 `Kind` 是 `NetworkEvent::Kind`，与本表 `TriggerEvent` **仅数值重叠、语义无关**（详见 §8.2）。

﻿---

## 2. Action 表（`TActionClass::Execute 0x6DD8B0`，跳表 `0x6DFDEC`，**145 项**）

> 布局旁证：`0x6DFDE1 = 81 C4 40 02 00 00`（`add esp,0x240`）、`0x6DFDE7 = C2 10 00`（`ret 0x10`）、`0x6DFDEA = 8B FF`（hotpatch 填充），跳表紧随其时 —— 是 MSVC 同 TU 大 switch 的标准布局。

派发指令原文（[实证]，`claims.txt` 第 2–3 条）：

```
006DD8D7  8B 56 2C              mov edx, dword ptr [esi + 0x2c]      ; edx = this->ActionKind
006DD8DA  4A                    dec edx                               ; 表以 ActionKind-1 索引
006DD8DB  81 FA 90 00 00 00     cmp edx, 0x90                         ; 上界 0x90 -> 145 项
006DD8E1  0F 87 F6 24 00 00     ja  0x6DFDDD                          ; 越界默认路径
006DD8E7  FF 24 95 EC FD 6D 00  jmp dword ptr [edx*4 + 0x6DFDEC]       ; 跳表基址 0x6DFDEC
```

**列说明**
- `# / HEX`：动作号（YRpp `enum class TriggerAction`，`0x00=None` 无表项）。
- `派发入口`：跳表目标（**内联实现体**）VA 与**文件偏移**（= VA − 0x400000）。
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
- `slave`：YRpp `ACTION_FUNC` 同名独立函数地址；`[M+N]`=调用集匹配+同名双证据（64 项）、`[N]`=仅同名对应（推演）、`[M]`=仅调用集匹配。**注意**：`Execute()` 的主体是内联副本，hook slave 不必然生效（YRpp 头原话）。
- `mode`：`TActionClass::GetMode 0x6E3B60` 返回值 = 参数序列化类别（决定存档/INI 里该参数写成"名字"还是"数字"）。
- `flags`：`TActionClass::GetFlags 0x6E3EE0` 位域；实测仅两值（`0` 与 `2`）。`2` 的 7 个动作见 §6.2。
- `参数布局`：实读字段（`Value(0x90)`=`+0x90` 等，字段名见 §1.2）。
- **`参数布局`列的口径**：由块内 `[esi/edi/ebp+disp]` 访存归纳，**寄存器在块内可能被复用为其他指针**（例：`SetObjectTechLevel 0x6DF5D1` 的 `ebp` 是对象指针，故其 `[ebp+0x24]` 不是 `ArrayIndex`）→ 该列整体为 [推演]，但附录 C 的 26 个代表项已逐条人工复核；`mode`/`flags` 两列不受影响（来自独立小表）。
- `副作用`：`P` 纯表现｜`L` 改逻辑状态｜`M` 改地图/地形｜`$` 改财金（组合记为 `$+L`）｜`-` 空实现。
- `联机`：红=改语义即多端分叉（红线，见 `net_sync_checksum.md` §5.1）｜黄=本机 UI/表现但需保证各端调用次数与 RNG 消耗一致｜绿=纯本机表现，可独立优化。

### 2.1 Action 表全文（145/145）

| # | HEX | 名称（YRpp TriggerAction） | 派发入口 VA(文件偏移) | slave 函数 | mode | flags | 参数布局 | 副作用 | 联机风险 |
|---|---|---|---|---|---|---|---|---|---|

| 1 | `0x01` | **Win** | `006DEA37` (0x2DEA37) | PlayerWin 0x6E0440 [N] | 13 | — | 房号；读 Value(0x90) | `L` | 红｜场景胜负判定；调 HouseClass::Win |
| 2 | `0x02` | **Lose** | `006DEA67` (0x2DEA67) | PlayerLose 0x6E0460 [N] | 13 | — | 房号；读 Value(0x90) | `L` | 红｜场景胜负判定；调 HouseClass::Lose |
| 3 | `0x03` | **ProductionBegins** | `006DEA97` (0x2DEA97) | EnableProductionForHouse 0x6E1E40 [N] | 13 | — | 房号；读 Value(0x90) | `L` | 红｜房生产开关 |
| 4 | `0x04` | **CreateTeam** | `006DEB57` (0x2DEB57) | CreateTeam 0x6E1F60 [M+N] | 12 | — | TeamType*；读 TeamType*(0x30) | `L` | 红｜创建 TeamClass 实例（进对象表/可能吃 RNG） |
| 5 | `0x05` | **DestroyTeam** | `006DEB8D` (0x2DEB8D) | DestroyAllInstancesOfTeam 0x6E1F90 [M+N] | 12 | — | TeamType*；读 TeamType*(0x30) | `L` | 红｜销毁该队全部实例 |
| 6 | `0x06` | **AllToHunt** | `006DEBF9` (0x2DEBF9) | — | 13 | — | 房号；读 Value(0x90) | `L` | 红｜该房全单位转 Hunt 任务 |
| 7 | `0x07` | **Reinforcement** | `006DEBAE` (0x2DEBAE) | SpawnTeamAtWP 0x6E1FD0 [M+N] | 12 | — | TeamType*；读 TeamType*(0x30) | `L` | 红｜路径点增援（生成队伍） |
| 8 | `0x08` | **DropZoneFlare** | `006DEA0A` (0x2DEA0A) | DiplayDropFlare 0x6E1CC0 [N] | 9 | — | 路径点 | `L` | 红｜生成投放区信号弹动画对象 |
| 9 | `0x09` | **FireSale** | `006DEAD6` (0x2DEAD6) | FireSale 0x6E1EA0 [N] | 13 | — | 房号；读 Value(0x90) | `$+L` | 红｜拆卖该房建筑（改财金+对象态） |
| 10 | `0x0A` | **PlayMovie** | `006DE72F` (0x2DE72F) | PlayMovie 0x6E16D0 [M+N] | 2 | — | 影片id；读 Value(0x90) | `P` | 黄｜播放影片（会局部接管界面/暂停） |
| 11 | `0x0B` | **TextTrigger** | `006DE0A8` (0x2DE0A8) | PrintMessage 0x6E0D60 [N] | 39 | — | 文本缓冲；读 Text(0x6D) | `P` | 黄｜显示文本（本机消息层） |
| 12 | `0x0C` | **DestroyTrigger** | `006DF051` (0x2DF051) | DeleteTrigger 0x6E2A10 [M+N] | 11 | — | TriggerType*；读 TriggerType*(0x50) | `L` | 红｜删除触发器实例 |
| 13 | `0x0D` | **AutocreateBegins** | `006DEB18` (0x2DEB18) | EnableAutocreateForHouse 0x6E1F00 [N] | 13 | — | 房号；读 Value(0x90) | `L` | 红｜房自动建造开关 |
| 14 | `0x0E` | **ChangeHouse** | `006DE04E` (0x2DE04E) | SwitchAttachedObjectsToHouse 0x6E0AA0 [N] | 13 | 2 | 房号 | `L` | 红｜附着建筑换属主 |
| 15 | `0x0F` | **AllowWin** | `006DFDDD` (0x2DFDDD) | — | 0 | 0 | 无参 | `-` | 红｜**空实现**（仅 epilogue，实测无动作） |
| 16 | `0x10` | **RevealAllMap** | `006DE3A8` (0x2DE3A8) | — | 0 | 0 | 无参 | `M` | 红｜全图去雾（改可见性/遮罩状态） |
| 17 | `0x11` | **RevealAroundWaypoint** | `006DE34E` (0x2DE34E) | RevealAroundWaypoint 0x6E0FE0 [N] | 9 | 0 | 路径点 | `M` | 红｜路径点周围去雾 |
| 18 | `0x12` | **RevealWaypointZone** | `006DE37B` (0x2DE37B) | RevealZoneOfWaypoint 0x6E11C0 [N] | 9 | 0 | 路径点 | `M` | 红｜路径点区域去雾 |
| 19 | `0x13` | **PlaySoundEffect** | `006DE780` (0x2DE780) | PlayAudio 0x6E1760 [M+N] | 3 | 0 | 音效(Voc)id；读 Value(0x90) | `P` | 绿｜VocClass::PlayGlobal（本机音频） |
| 20 | `0x14` | **PlayMusicTheme** | `006DE8E4` (0x2DE8E4) | PlayTheme 0x6E1B90 [M+N] | 1 | 0 | 主题id；读 Value(0x90) | `P` | 绿｜切换主题音乐（本机音频） |
| 21 | `0x15` | **PlaySpeech** | `006DE904` (0x2DE904) | PlayEVA 0x6E1BB0 [M+N] | 4 | 0 | 语音(Vox)id；读 Value(0x90) | `P` | 绿｜VoxClass::PlayIndex（本机语音） |
| 22 | `0x16` | **ForceTrigger** | `006DF0E7` (0x2DF0E7) | ForceTrigger 0x6E2AA0 [M+N] | 11 | 0 | TriggerType*；读 TriggerType*(0x50) | `L` | 红｜强制触发另一触发器（递归 FireActions） |
| 23 | `0x17` | **TimerStart** | `006DE418` (0x2DE418) | MissionTimerStart 0x6E13A0 [M+N] | 0 | 0 | 无参 | `L` | 红｜场景计时器启动 |
| 24 | `0x18` | **TimerStop** | `006DE457` (0x2DE457) | MissionTimerStop 0x6E13E0 [N] | 0 | 0 | 无参 | `L` | 红｜场景计时器停止 |
| 25 | `0x19` | **TimerExtend** | `006DE4A0` (0x2DE4A0) | MissionTimerExtend 0x6E1440 [N] | 10 | 0 | 整数；读 Value(0x90) | `L` | 红｜场景计时器延长 |
| 26 | `0x1A` | **TimerShorten** | `006DE501` (0x2DE501) | MissionTimerShorten 0x6E14A0 [N] | 10 | 0 | 整数；读 Value(0x90) | `L` | 红｜场景计时器缩短 |
| 27 | `0x1B` | **TimerSet** | `006DE5C9` (0x2DE5C9) | MissionTimerStartWithText 0x6E1530 [N] | 10 | 0 | 整数；读 Value(0x90) | `L` | 红｜场景计时器设定+文本 |
| 28 | `0x1C` | **GlobalSet** | `006DE2CE` (0x2DE2CE) | GlobalSet 0x6E0FA0 [M+N] | 22 | 0 | —；读 Value(0x90) | `L` | 红｜全局变量置位（存档/同步状态） |
| 29 | `0x1D` | **GlobalClear** | `006DE2F1` (0x2DE2F1) | GlobalClear 0x6E0FC0 [N] | 22 | 0 | —；读 Value(0x90) | `L` | 红｜全局变量清零 |
| 30 | `0x1E` | **AutoBaseBuilding** | `006DE206` (0x2DE206) | — | 16 | 0 | 房号+TechnoID；读 Value(0x90)/TechnoID+0xC(0x60)/TechnoID(0x54) | `L` | 红｜AI 自动建基地开关 |
| 31 | `0x1F` | **GrowShroud** | `006DE2B5` (0x2DE2B5) | GrowShroud 0x6E0F90 [M+N] | 0 | 0 | 无参 | `M` | 红｜去掉路径点周围黑幕 |
| 32 | `0x20` | **DestroyAttachedObject** | `006DEC3B` (0x2DEC3B) | DestroyAttached 0x6E2050 [N] | 0 | 2 | 无参 | `L` | 红｜销毁附着对象 |
| 33 | `0x21` | **AddOneTimeSuperWeapon** | `006DE925` (0x2DE925) | Grant1ShotSW 0x6E1BD0 [N] | 17 | 0 | 超武编号；读 Value(0x90) | `L` | 红｜授予一次性超武（SuperClass::Grant + 侧边栏） |
| 34 | `0x22` | **AddRepeatingSuperWeapon** | `006DE98E` (0x2DE98E) | GrantPermanentSW 0x6E1C40 [M+N] | 17 | 0 | 超武编号；读 Value(0x90) | `L` | 红｜授予可重复超武 |
| 35 | `0x23` | **PreferredTarget** | `006DE1DC` (0x2DE1DC) | SetTargetCell 0x6E0ED0 [N] | 15 | 0 | 目标格(待实测)；读 Value(0x90) | `L` | 红｜房 AI 首选目标格 |
| 36 | `0x24` | **AllChangeHouse** | `006DE07B` (0x2DE07B) | SwitchAllObjectsToHouse 0x6E0B60 [N] | 13 | 0 | 房号 | `L` | 红｜该房全部对象换属主 |
| 37 | `0x25` | **MakeAlly** | `006DE136` (0x2DE136) | MakeTwoHousesAlly 0x6E0DF0 [N] | 13 | 0 | 房号；读 Value(0x90) | `L` | 红｜结盟（外交状态） |
| 38 | `0x26` | **MakeEnemy** | `006DE189` (0x2DE189) | MakeTwoHousesEnemy 0x6E0E60 [N] | 13 | 0 | 房号；读 Value(0x90) | `L` | 红｜宣战（外交状态） |
| 39 | `0x27` | **ChangeZoomLevel** | `006DFDDB` (0x2DFDDB) | — | 10 | 0 | 整数 | `-` | 红｜**空实现**（`mov al,1;ret`，与 Firestorm 同体；本作未实现缩放档位） |
| 40 | `0x28` | **ResizePlayerView** | `006DEC68` (0x2DEC68) | ResizePlayerView 0x6E21E0 [N] | 21 | 0 | 视图参数 | `P` | 绿｜本地视图尺寸 |
| 41 | `0x29` | **PlayAnimAt** | `006DEC95` (0x2DEC95) | PlayAnimAtWP 0x6E2290 [N] | 23 | 0 | 动画类型id | `L` | 红｜按路径点播动画（新增 AnimClass 对象） |
| 42 | `0x2A` | **DoExplosionAt** | `006DECC2` (0x2DECC2) | FireWeaponAtWP 0x6E2390 [N] | 24 | 0 | 武器/爆点参数 | `L` | 红｜按路径点开火（伤判+对象态） |
| 43 | `0x2B` | **CreateVoxelAnim** | `006DECEF` (0x2DECEF) | PlayVoxelAnimAtWP 0x6E2520 [N] | 27 | 0 | 体素动画类型id | `L` | 红｜按路径点生成体素动画对象 |
| 44 | `0x2C` | **IonStormStart** | `006DED1C` (0x2DED1C) | LightningStormStart 0x6E2600 [N] | 10 | 0 | 整数 | `L` | 红｜离子风暴启动（全局环境状态） |
| 45 | `0x2D` | **IonStormStop** | `006DED61` (0x2DED61) | LightningStormStop 0x6E2640 [N] | 0 | 0 | 无参 | `L` | 红｜离子风暴停止 |
| 46 | `0x2E` | **LockInput** | `006DED8B` (0x2DED8B) | — | 0 | 0 | 无参 | `P` | 黄｜锁输入（本机 UI 状态；Display/Mouse 本地标志） |
| 47 | `0x2F` | **UnlockInput** | `006DEDEB` (0x2DEDEB) | — | 0 | 0 | 无参 | `P` | 黄｜解锁输入 |
| 48 | `0x30` | **MoveCameraToWaypoint** | `006DEDFF` (0x2DEDFF) | PlayVoxelAnimAtWP 0x006E2520 [M] | 30 | 0 | 坐标/路径点；读 Waypoint(0x44)/Value(0x90) | `P` | 绿｜镜头移到路径点 |
| 49 | `0x31` | **ZoomIn** | `006DEEB8` (0x2DEEB8) | ZoomIn 0x6E2860 [M+N] | 0 | 0 | 无参 | `P` | 绿｜放大 |
| 50 | `0x32` | **ZoomOut** | `006DEF35` (0x2DEF35) | ZoomOut 0x6E28DC [M+N] | 0 | 0 | 无参 | `P` | 绿｜缩小 |
| 51 | `0x33` | **ReshroudMap** | `006DEF9B` (0x2DEF9B) | — | 0 | 0 | 无参 | `M` | 红｜整图重新遮罩 |
| 52 | `0x34` | **ChangeLightBehavior** | `006DEFBC` (0x2DEFBC) | SetAttachedSpotlightBehaviour 0x6E2970 [M+N] | 25 | 0 | 灯光参数；读 TechnoID+0x18(0x6C)/Value(0x90)/Text+7(0x74)/Text+0x14(0x81)/Bounds.XY(0x34) | `P` | 黄｜改附着点探照灯行为（表现为主，改 BuildingLight 状态） |
| 53 | `0x35` | **EnableTrigger** | `006DF137` (0x2DF137) | EnableTrigger 0x6E2AF0 [N] | 11 | 0 | TriggerType* | `L` | 红｜启用触发器 |
| 54 | `0x36` | **DisableTrigger** | `006DF164` (0x2DF164) | — | 11 | 0 | TriggerType*；读 TriggerType*(0x50) | `L` | 红｜禁用触发器 |
| 55 | `0x37` | **CreateRadarEvent** | `006DF1AD` (0x2DF1AD) | RadarEventAdd 0x6E2BB0 [M+N] | 28 | 0 | 雷达事件参数；读 Waypoint(0x44)/Value(0x90) | `P` | 绿｜加雷达事件提示（本机雷达） |
| 56 | `0x38` | **LocalSet** | `006DF1DE` (0x2DF1DE) | LocalSet 0x6E2BE0 [M+N] | 29 | 0 | 局部变量；读 Value(0x90) | `L` | 红｜局部变量置位 |
| 57 | `0x39` | **LocalClear** | `006DF201` (0x2DF201) | LocalClear 0x6E2C00 [N] | 29 | 0 | 局部变量；读 Value(0x90) | `L` | 红｜局部变量清零 |
| 58 | `0x3A` | **MeteorShower** | `006DF223` (0x2DF223) | StartMeteorShower 0x6E2C40 [N] | 31 | 0 | 流星雨参数 | `L` | 红｜流星雨（生成伤害对象）〔**DA2 补注 · RNG×4**：`StartMeteorShower 0x6E2C40` 函数体内 `call 0x65C780`（`Randomizer::Random`）**恰 4 处** —— `0x6E2CEB = E8 90 9A F7 FF` / `0x6E2D4E = E8 2D 9A F7 FF` / `0x6E2D5A = E8 21 9A F7 FF` / `0x6E2DB0 = E8 CB 99 F7 FF`，全函数无其它 RNG 触点；派发块 `0x6DF23E = E8 FD 39 00 00`（`call 0x6E2C40`）⇒ 联机各端该动作的 **RNG 消耗次数=4** 必须一致〕 |
| 59 | `0x3B` | **ReduceTiberium** | `006DE313` (0x2DE313) | ReduceTiberiumAt 0x6E1180 [M+N] | 9 | 0 | 路径点；读 Value(0x90) | `M` | 红｜减少路径点泰伯伦（改 overlay） |
| 60 | `0x3C` | **SellBuilding** | `006DDEF5` (0x2DDEF5) | SellAttachedBuildings 0x6E08B0 [M+N] | 0 | 2 | 无参；读 Value(0x90)/Text+7(0x74)/Text+0x14(0x81)/Bounds.XY(0x34) | `$+L` | 红｜建筑出售（改财金+对象态） |
| 61 | `0x3D` | **TurnOffBuilding** | `006DDF65` (0x2DDF65) | SendAttachedBuildingsOffline 0x6E09A0 [M+N] | 0 | 2 | 无参；读 Value(0x90)/Text+7(0x74)/Text+0x14(0x81)/Bounds.XY(0x34) | `L` | 红｜建筑离线（断电式关闭） |
| 62 | `0x3E` | **TurnOnBuilding** | `006DDFD9` (0x2DDFD9) | SendAttachedBuildingsOnline 0x6E0A20 [M+N] | 0 | 2 | 无参；读 Value(0x90)/Text+7(0x74)/Text+0x14(0x81)/Bounds.XY(0x34) | `L` | 红｜建筑在线 |
| 63 | `0x3F` | **Apply100Damage** | `006DDDC9` (0x2DDDC9) | Apply100DamageAt 0x6E0490 [N] | 9 | 0 | 路径点 | `L` | 红｜路径点 100 伤（对象态） |
| 64 | `0x40` | **SmallLightFlash** | `006DDDF6` (0x2DDDF6) | SmallLightFlashAt 0x6E0790 [M+N] | 9 | 0 | 路径点；读 Value(0x90) | `L` | 红｜小闪光（生成光照/伤害动画对象） |
| 65 | `0x41` | **MediumLightFlash** | `006DDE4B` (0x2DDE4B) | MediumLightFlashAt 0x6E07F0 [N] | 9 | 0 | 路径点；读 Value(0x90) | `L` | 红｜中闪光 |
| 66 | `0x42` | **LargeLightFlash** | `006DDEA0` (0x2DDEA0) | LargeLightFlashAt 0x6E0850 [N] | 9 | 0 | 路径点；读 Value(0x90) | `L` | 红｜大闪光 |
| 67 | `0x43` | **AnnounceWin** | `006DDD77` (0x2DDD77) | PlayerWin 0x6E0440 [N] | 0 | 0 | 无参 | `L` | 红｜宣告胜利（HouseClass::Win） |
| 68 | `0x44` | **AnnounceLose** | `006DDD93` (0x2DDD93) | PlayerLose 0x6E0460 [M+N] | 0 | 0 | 无参 | `L` | 红｜宣告失败（HouseClass::Lose） |
| 69 | `0x45` | **ForceEnd** | `006DDDAF` (0x2DDDAF) | EndScenario 0x6E0480 [M+N] | 0 | 0 | 无参 | `L` | 红｜强制结束场景 |
| 70 | `0x46` | **DestroyTag** | `006DF094` (0x2DF094) | DeleteTag 0x6E2A50 [M+N] | 26 | 0 | —；读 TagType*(0x4C) | `L` | 红｜删除标签（TagClass） |
| 71 | `0x47` | **SetAmbientStep** | `006DF250` (0x2DF250) | SetAmbientChangeStep 0x6E2E20 [N] | 33 | 0 | 环境参数 | `L` | 黄｜环境光变化步长（全局环境状态，偏表现） |
| 72 | `0x48` | **SetAmbientRate** | `006DF271` (0x2DF271) | SetAmbientChangeRate 0x6E2E40 [N] | 33 | 0 | 环境参数 | `L` | 黄｜环境光变化速率 |
| 73 | `0x49` | **SetAmbientLight** | `006DF292` (0x2DF292) | SetAmbientLevel 0x6E2F4F [M+N] | 10 | 0 | 整数；读 Value(0x90) | `L` | 黄｜环境光等级 |
| 74 | `0x4A` | **AITriggersBegin** | `006DF2D1` (0x2DF2D1) | EnableAITriggers 0x6E2FA0 [N] | 13 | 0 | 房号；读 Value(0x90) | `L` | 红｜AI 触发器启用 |
| 75 | `0x4B` | **AITriggersStop** | `006DF310` (0x2DF310) | DisableAITriggers 0x6E3000 [N] | 13 | 0 | 房号；读 Value(0x90) | `L` | 红｜AI 触发器停用 |
| 76 | `0x4C` | **RatioOfAITriggerTeams** | `006DF34F` (0x2DF34F) | SetRatioAITeam 0x6E3300 [N] | 10 | 0 | 整数；读 Value(0x90) | `L` | 红｜AI 触发部队比例 |
| 77 | `0x4D` | **RatioOfTeamAircraft** | `006DF379` (0x2DF379) | SetRatioAITeamAircraft 0x6E3320 [N] | 10 | 0 | 整数；读 Value(0x90) | `L` | 红｜队伍飞机比例 |
| 78 | `0x4E` | **RatioOfTeamInfantry** | `006DF3A3` (0x2DF3A3) | SetRatioAITeamInfantry 0x6E3340 [N] | 10 | 0 | 整数；读 Value(0x90) | `L` | 红｜队伍步兵比例 |
| 79 | `0x4F` | **RatioOfTeamUnits** | `006DF3CD` (0x2DF3CD) | SetRatioAITeamUnits 0x6E3360 [N] | 10 | 0 | 整数；读 Value(0x90) | `L` | 红｜队伍车辆比例 |
| 80 | `0x50` | **ReinforcementAt** | `006DEBD0` (0x2DEBD0) | SpawnTeamAtWP 0x6E1FD0 [M+N] | 34 | 0 | 队伍id+路径点；读 TeamType*(0x30)/Waypoint(0x44) | `L` | 红｜队伍在路径点增援 |
| 81 | `0x51` | **WakeupSelf** | `006DDB67` (0x2DDB67) | WakeupAttachedObjects 0x6E01C0 [N] | 0 | 0 | 无参 | `L` | 红｜唤醒附着对象 |
| 82 | `0x52` | **WakeupAllSleepers** | `006DDBF6` (0x2DDBF6) | WakeupAllIdle 0x6E02B0 [N] | 0 | 0 | 无参；读 Value(0x90)/Text+7(0x74)/Text+0x14(0x81) | `L` | 红｜唤醒全部休眠单位 |
| 83 | `0x53` | **WakeupAllHarmless** | `006DDC71` (0x2DDC71) | WakeupAllHarmless 0x6E0330 [N] | 0 | 0 | 无参；读 Value(0x90)/Text+7(0x74)/Text+0x14(0x81) | `L` | 红｜唤醒全部无害单位 |
| 84 | `0x54` | **WakeupGroup** | `006DDCEC` (0x2DDCEC) | WakeupGroup 0x6E03B0 [M+N] | 10 | 0 | 整数；读 Value(0x90)/Text+7(0x74)/Text+0x14(0x81) | `L` | 红｜唤醒指定组 |
| 85 | `0x55` | **VeinGrowth** | `006DDB94` (0x2DDB94) | SetVeinGrowth 0x6E0250 [N] | 16 | 0 | 房号+TechnoID；读 Value(0x90) | `M` | 红｜矿脉生长速率（改地形） |
| 86 | `0x56` | **TiberiumGrowth** | `006DDBB4` (0x2DDBB4) | SetTiberiumGrowth 0x6E0270 [N] | 16 | 0 | 房号+TechnoID；读 Value(0x90) | `M` | 红｜泰伯伦生长速率 |
| 87 | `0x57` | **IceGrowth** | `006DDBD5` (0x2DDBD5) | SetIceGrowth 0x6E0290 [N] | 16 | 0 | 房号+TechnoID；读 Value(0x90) | `M` | 红｜冰面生长速率 |
| 88 | `0x58` | **ParticleAnim** | `006DF3F7` (0x2DF3F7) | IonBlastAtWP 0x006E3380 [M] | 35 | 0 | 粒子系统类型；读 Waypoint(0x44)/Value(0x90) | `L` | 红｜生成粒子系统对象 |
| 89 | `0x59` | **RemoveParticleAnim** | `006DF49E` (0x2DF49E) | RemoveParticleSystemsAt 0x6E0080 [M+N] | 9 | 0 | 路径点；读 Waypoint(0x44)/Value(0x90) | `L` | 红｜移除粒子系统 |
| 90 | `0x5A` | **LightningStrike** | `006DF51B` (0x2DF51B) | LightningStrikeAt 0x6E0050 [M+N] | 9 | 0 | 路径点；读 Waypoint(0x44) | `L` | 红｜路径点雷击（伤害） |
| 91 | `0x5B` | **GoBerzerk** | `006DDAF9` (0x2DDAF9) | BerserkAttachedInfantry 0x6E0930 [M+N] | 0 | 2 | 无参；读 Value(0x90)/Text+7(0x74)/Text+0x14(0x81)/Bounds.XY(0x34) | `L` | 红｜单位暴走 |
| 92 | `0x5C` | **ActivateFirestorm** | `006DFDDB` (0x2DFDDB) | — | 0 | 0 | 无参 | `-` | 红｜**空实现**（仅 mov al,1;ret，TS 遗留） |
| 93 | `0x5D` | **DeactivateFirestorm** | `006DFDDB` (0x2DFDDB) | — | 0 | 0 | 无参 | `-` | 红｜**空实现**（仅 mov al,1;ret，TS 遗留） |
| 94 | `0x5E` | **IonCannonStrike** | `006DD913` (0x2DD913) | IonBlastAtWP 0x6E3380 [M+N] | 9 | 0 | 路径点；读 Waypoint(0x44) | `L` | 红｜离子炮打击（生成 IonBlastClass+伤害） |
| 95 | `0x5F` | **NukeStrike** | `006DD9BF` (0x2DD9BF) | NukeAtWP 0x6E3410 [N] | 9 | 0 | 路径点 | `L` | 红｜核弹打击 |
| 96 | `0x60` | **ChemMissileStrike** | `006DDACC` (0x2DDACC) | ChemLauncherAtWP 0x6E38F0 [N] | 9 | 0 | 路径点 | `L` | 红｜化学导弹打击 |
| 97 | `0x61` | **ToggleTrainCargo** | `006DD8EE` (0x2DD8EE) | ToggleTrainCrate 0x6E3B20 [N] | 0 | 0 | 无参 | `L` | 红｜训练用木箱开关 |
| 98 | `0x62` | **PlaySoundEffectRandom** | `006DE7A5` (0x2DE7A5) | PlayAudioAtRandomWP 0x6E1780 [M+N] | 3 | 0 | 音效(Voc)id；读 Value(0x90) | `P` | 黄｜随机音效（**消耗同步 RNG**） |
| 99 | `0x63` | **PlaySoundEffectAtWaypoint** | `006DE845` (0x2DE845) | PlayAudioAtSpecificWP 0x6E18B0 [N] | 38 | 0 | 音效id+路径点；读 Waypoint(0x44)/Value(0x90) | `P` | 绿｜在路径点播音效 |
| 100 | `0x64` | **PlayIngameMovie** | `006DF546` (0x2DF546) | PlayMovieInSidebar 0x6E1720 [N] | 2 | 0 | 影片id；读 Value(0x90) | `P` | 黄｜内嵌影片 |
| 101 | `0x65` | **ReshroudMapAtWaypoint** | `006DE8B7` (0x2DE8B7) | ReshroudMapAroundWaypoint 0x6E1A70 [N] | 9 | 0 | 路径点 | `M` | 红｜路径点周围重新遮罩 |
| 102 | `0x66` | **LightningStormStrike** | `006DD9EC` (0x2DD9EC) | LightningStormAtWP 0x6E35F0 [M+N] | 9 | 0 | 路径点；读 Waypoint(0x44) | `L` | 红｜雷暴打击 |
| 103 | `0x67` | **TimerText** | `006DE66A` (0x2DE66A) | MissionTimerSetText 0x6E15F0 [N] | 39 | 0 | 文本缓冲；读 Text(0x6D) | `P` | 黄｜计时器文本 |
| 104 | `0x68` | **FlashTeam** | `006DF562` (0x2DF562) | FlashTeamFor 0x6E4020 [M+N] | 40 | 0 | 队伍id+时长；读 TeamType*(0x30)/Value(0x90) | `P` | 绿｜队伍闪烁 |
| 105 | `0x69` | **TalkBubble** | `006DF588` (0x2DF588) | TalkBubble 0x6E4040 [M+N] | 12 | 0 | TeamType*；读 TeamType*(0x30)/Value(0x90) | `P` | 绿｜气泡对话（队伍首个实例） |
| 106 | `0x6A` | **SetObjectTechLevel** | `006DF5D1` (0x2DF5D1) | SetTechLevelOfTechnoType 0x6E37F0 [N] | 43 | 0 | TechnoID+值；读 TechnoID(0x54)/ArrayIndex(0x24) | `L` | 红｜设置科技等级（规则状态） |
| 107 | `0x6B` | **ReinforcementByChrono** | `006DF672` (0x2DF672) | ChronoInTeam 0x6E3890 [M+N] | 34 | 0 | 队伍id+路径点；读 TeamType*(0x30)/Waypoint(0x44) | `L` | 红｜超时空增援 |
| 108 | `0x6C` | **CreateCrate** | `006DF69B` (0x2DF69B) | CrateAtWP 0x6E38B0 [M+N] | 44 | 0 | 箱子参数+路径点；读 Waypoint(0x44)/Value(0x90) | `L` | 红｜路径点生成木箱（新增对象） |
| 109 | `0x6D` | **IronCurtain** | `006DF6D0` (0x2DF6D0) | IronCurtainAtWP 0x6E36E0 [N] | 9 | 0 | 路径点 | `L` | 红｜路径点铁幕（无敌状态） |
| 110 | `0x6E` | **PauseGame** | `006DF6FD` (0x2DF6FD) | PauseScenarioFor 0x6E4080 [M+N] | 10 | 0 | 整数；读 Value(0x90) | `L` | 红｜暂停对局（联机敏感） |
| 111 | `0x6F` | **EvictOccupiers** | `006DF717` (0x2DF717) | EjectOccupantsOfFirstAttachedBuilding 0x6E4090 [M+N] | 0 | 2 | 无参；读 Value(0x90)/Text+7(0x74)/Text+0x14(0x81)/Bounds.XY(0x34) | `L` | 红｜驱离占用者 |
| 112 | `0x70` | **CenterCameraAtWaypoint** | `006DF795` (0x2DF795) | PlayVoxelAnimAtWP 0x006E2520 [M] | 9 | — | 路径点；读 Waypoint(0x44) | `P` | 绿｜镜头居中到路径点 |
| 113 | `0x71` | **MakeHouseCheer** | `006DF848` (0x2DF848) | Cheer 0x6E3060 [N] | 13 | — | 房号；读 Value(0x90) | `P` | 绿｜房欢呼 |
| 114 | `0x72` | **SetTabTo** | `006DF887` (0x2DF887) | SwitchToTab 0x6E4100 [N] | 10 | — | 整数 | `P` | 绿｜切换侧边栏页签 |
| 115 | `0x73` | **FlashCameo** | `006DF8B4` (0x2DF8B4) | FlashCameo 0x6E4150 [N] | 43 | — | TechnoID+值 | `P` | 绿｜闪烁图标(cameo) |
| 116 | `0x74` | **StopSounds** | `006DF8E1` (0x2DF8E1) | StopAudioAtSpecificWP 0x6E1980 [N] | 9 | — | 路径点 | `P` | 绿｜停止路径点音效 |
| 117 | `0x75` | **PlayIngameMovieAndPause** | `006DF90E` (0x2DF90E) | PlayMovieInSidebarPauseGame 0x6E1740 [M+N] | 2 | — | 影片id；读 Value(0x90) | `P` | 黄｜内嵌影片并暂停 |
| 118 | `0x76` | **ClearAllSmudges** | `006DF92A` (0x2DF92A) | ClearSmudges 0x6E2C20 [N] | 0 | — | 无参 | `M` | 红｜清除全部污渍（改地图 smudge，进档/进校验） |
| 119 | `0x77` | **DestroyAll** | `006DF957` (0x2DF957) | DestroyAllObjectsOf 0x6E3180 [N] | 13 | — | 房号 | `L` | 红｜销毁该房全部对象 |
| 120 | `0x78` | **DestroyAllBuildings** | `006DF984` (0x2DF984) | DestroyAllBuildingsOf 0x6E31E0 [N] | 13 | — | 房号 | `L` | 红｜销毁该房全部建筑 |
| 121 | `0x79` | **DestroyAllLandUnits** | `006DF9B1` (0x2DF9B1) | DestroyAllNonNavalUnitsOf 0x6E3240 [N] | 13 | — | 房号 | `L` | 红｜销毁该房全部陆上单位 |
| 122 | `0x7A` | **DestroyAllNavalUnits** | `006DF9DE` (0x2DF9DE) | DestroyAllNavalUnitsOf 0x6E32A0 [N] | 13 | — | 房号 | `L` | 红｜销毁该房全部海军单位 |
| 123 | `0x7B` | **MindControlBase** | `006DFA0B` (0x2DFA0B) | MindControlBuildingsOfHouse 0x6E0CA0 [N] | 13 | — | 房号 | `L` | 红｜精神控制该房基地 |
| 124 | `0x7C` | **RestoreMindControlledBase** | `006DFA38` (0x2DFA38) | RelinquishMindControlOfBuildingsOfHouse 0x6E0D00 [N] | 13 | — | 房号 | `L` | 红｜解除精神控制 |
| 125 | `0x7D` | **CreateBuilding** | `006DFA65` (0x2DFA65) | SpawnBuilding 0x6E4200 [N] | 45 | — | 建筑类型+路径点 | `L` | 红｜生成建筑 |
| 126 | `0x7E` | **RestoreStartingUnits** | `006DFA92` (0x2DFA92) | RestoreStartingUnitsOf 0x6E30C0 [N] | 13 | — | 房号 | `L` | 红｜恢复初始单位 |
| 127 | `0x7F` | **StartChronoScreenEffect** | `006DFABF` (0x2DFABF) | SetChronoScreenEffectState 0x6E2F90 [M+N] | 10 | — | 整数；读 Value(0x90) | `P` | 绿｜超时空屏幕特效 |
| 128 | `0x80` | **TeleportAll** | `006DFAD9` (0x2DFAD9) | TeleportAllHouseObjectTo 0x6E1A40 [N] | 9 | — | 路径点 | `L` | 红｜全房对象传送到路径点 |
| 129 | `0x81` | **SetSuperWeaponCharge** | `006DFB06` (0x2DFB06) | SetSWChargeLevel 0x6E42D0 [N] | 46 | — | 超武编号+值 | `L` | 红｜设置超武充能等级 |
| 130 | `0x82` | **RestoreStartingBuildings** | `006DFB33` (0x2DFB33) | RestoreStartingBuildingsOf 0x6E3120 [N] | 13 | — | 房号 | `L` | 红｜恢复初始建筑 |
| 131 | `0x83` | **FlashBuildingsOfType** | `006DFB60` (0x2DFB60) | FlashBuildingsOfType 0x6E4560 [N] | 47 | — | 建筑类型 | `P` | 绿｜按类型闪烁建筑 |
| 132 | `0x84` | **SuperWeaponSetRechargeTime** | `006DFB8D` (0x2DFB8D) | SetSWRechargeTime 0x6E4320 [N] | 46 | — | 超武编号+值 | `L` | 红｜超武重充时间设定 |
| 133 | `0x85` | **SuperWeaponResetRechargeTime** | `006DFBBA` (0x2DFBBA) | ResetSWRechargeTime 0x6E4360 [N] | 46 | — | 超武编号+值 | `L` | 红｜超武重充时间复位 |
| 134 | `0x86` | **SuperWeaponReset** | `006DFBE7` (0x2DFBE7) | ResetSW 0x6E43A0 [N] | 17 | — | 超武编号 | `L` | 红｜超武复位 |
| 135 | `0x87` | **SetPreferredTargetCell** | `006DFC14` (0x2DFC14) | SetPreferredTargetCell 0x6E43E0 [N] | 9 | — | 路径点 | `L` | 红｜设置首选目标格 |
| 136 | `0x88` | **ClearPreferredTargetCell** | `006DFC41` (0x2DFC41) | ResetTargetCell 0x6E4440 [N] | 0 | — | 无参 | `L` | 红｜清除首选目标格 |
| 137 | `0x89` | **SetBaseCenterCell** | `006DFC6E` (0x2DFC6E) | SetBaseCenter 0x6E44E0 [N] | 9 | — | 路径点 | `L` | 红｜设置基地中心格 |
| 138 | `0x8A` | **ClearBaseCenterCell** | `006DFC9B` (0x2DFC9B) | ResetBaseCenter 0x6E4540 [N] | 0 | — | 无参 | `L` | 红｜清除基地中心格 |
| 139 | `0x8B` | **BlackoutRadar** | `006DFCC8` (0x2DFCC8) | RadarBlackout 0x6E3B40 [N] | 10 | — | 整数 | `L` | 红｜雷达黑屏（玩家侧状态） |
| 140 | `0x8C` | **SetDefensiveTargetCell** | `006DFCF5` (0x2DFCF5) | SetDefenseCell 0x6E4460 [N] | 9 | — | 路径点 | `L` | 红｜设置防御目标格 |
| 141 | `0x8D` | **ClearDefensiveTargetCell** | `006DFD22` (0x2DFD22) | ResetDefenseCell 0x6E44C0 [N] | 0 | — | 无参 | `L` | 红｜清除防御目标格 |
| 142 | `0x8E` | **RetintRed** | `006DFD4F` (0x2DFD4F) | SetTintRed 0x6E2E60 [N] | 10 | — | 整数 | `P` | 绿｜色调 R（本机渲染） |
| 143 | `0x8F` | **RetintGreen** | `006DFD7C` (0x2DFD7C) | SetTintGreen 0x6E2EB0 [N] | 10 | — | 整数 | `P` | 绿｜色调 G |
| 144 | `0x90` | **RetintBlue** | `006DFDA9` (0x2DFDA9) | SetTintBlue 0x6E2F00 [N] | 10 | — | 整数 | `P` | 绿｜色调 B |
| 145 | `0x91` | **JumpCameraHome** | `006DFDD6` (0x2DFDD6) | JumpCameraHome 0x6E2850 [M+N] | 0 | — | 无参 | `P` | 绿｜镜头回主基地 |

﻿> **表长自证（布局级）**：`0x6DFDE1 = 81 C4 40 02 00 00`（`add esp,0x240`）、`0x6DFDE7 = C2 10 00`（`ret 0x10`）、`0x6DFDEA = 8B FF`（hotpatch 填充）⇒ 跳表 `0x6DFDEC` 紧接 `Execute` 函数体之后；`0x6E0030 = B0 01 C2 10`（`mov al,1; ret 0x10` + `CC` 填充）⇒ 表止于 `0x6E002F`（`0x6DFDEC + 145×4`）；`0x6E004F/0x6E0050` 起即 `ACTION_FUNC` 从属函数块（`LightningStrikeAt`）。**跳表恰好夹在 `Execute` 体与从属函数块之间**，与"145 项"互证。[实证]

计数自证：表项 145 = 唯一目标 143 + 重复 2（`0x6DFDDB` 被 `0x27/0x5C/0x5D` 共用，多计 2）。

﻿---

## 3. Event 表（`TEventClass::HasOccured 0x71E940`）

派发结构原文（[实证]，`claims.txt` 第 33–37 条）：

```
0071E94D  8B 4D 2C                mov ecx, dword ptr [ebp + 0x2c]   ; EventKind
0071E950  8D 41 F3                lea eax, [ecx - 0xD]              ; 1 级：kind-0x0D
0071E953  83 F8 30                cmp eax, 0x30                     ; 覆盖 0x0D..0x3D（49 槽）
0071E956  0F 87 07 03 00 00       ja  0x71EC63                     ; 其余 kind 走对象/辅助链
0071E95C  33 D2                   xor edx, edx
0071E95E  8A 90 48 F2 71 00       mov dl, byte ptr [eax + 0x71F248]  ; 49 字节选择表
0071E964  FF 24 95 18 F2 71 00    jmp dword ptr [edx*4 + 0x71F218]   ; 12 项跳表
```

四级派发链（全部为 [实证]，选择表/跳表原始字节见 `out/re_work/triggers/event_*.txt`）：

| 层 | 触发条件 | 跳表 | 选择表 | 目标数 | 语义 |
|---|---|---|---|---|---|
| **1 级** | `EventKind ∈ 0x0D..0x3D` | `0x71F218` | `0x71F248`（49 B） | 12 | 全局/自身事件（时间、全局/局部变量、环境光、科技存在性、任务计时器） |
| **1 级默认** | 其余 kind（`0x00..0x0C`、`0x0F..0x12`…） | — | — | — | 落 `0x71EC63`，再进 2 级门 |
| **2 级** | `EventKind ∈ 1..0x3B` | `0x71F27C` | `0x71F284`（59 B） | 2 | 分流 `0x71EC9A`（**对象身份判定**：`cmp esi,ecx` + 全局抑制位 `[0xA8ED6B]`）↔ `0x71ECAF`（**扁平比较链**，含 `Build*Type`、`AITrigger`、`TeamLeavesMap` 等 26 个 kind） |
| **3 级** | 经 `[ebp+0x34]` 反查房（`call 0x502D30`）后，`kind-0x0C ∈ 0..0x2D` | `0x71F2C0` | `0x71F2F8`（46 B） | 14 | **房级状态**：资金、被毁计数、最近建造类型 id、工厂数、容器计数 |
| **4 级** | 同上，`kind-3 ∈ 0..0x37` | `0x71F328` | `0x71F350`（56 B） | 10 | **房级电量/击杀**：电力、海军/陆上被毁计数；默认 `0x71F1B1` → 返回真 |

**列说明**：`主判入口`=1 级跳表目标（`sel`=选择表槽位）；`辅助入口`=2/3/4 级目标；`A/B/F`=`GetStateA(0x71F950:A)` / `GetStateB(0x71F9C0:B)` / `GetFlags(0x71F680:F)` 返回（`1`=真支、`0`=假支、`calc`=继续计算）——三项均为 2 目标小表（`0x71F970`/`0x71F9E0`/`0x71F6F8`，选择表 `0x71F978`/`0x71F9E8`/`0x71F700`）[实证]。

### 3.1 Event 表全文（62/62，`0x00..0x3D`）

| # | HEX | 名称（YRpp TriggerEvent） | 主判入口 | 辅助入口（2/3/4 级） | A/B/F | 判定依据（实证字段/调用） | 联机风险 |
|---|---|---|---|---|---|---|---|

| 0 | `0x00` | **None** | `flat(0x71ECAF chain)` | — | `A= B= F=1` | 无事件占位 | 绿 |
| 1 | `0x01` | **EnteredBy** | `flat(0x71ECAF chain)` | 0071EC9A | `A= B= F=1` | 对象身份比对 cmp esi,ecx + 全局抑制位 [0xA8ED6B] | 红 |
| 2 | `0x02` | **SpiedBy** | `flat(0x71ECAF chain)` | 0071EC9A | `A= B= F=calc` | 同上（被间谍侵入） | 红 |
| 3 | `0x03` | **ThievedBy** | `flat(0x71ECAF chain)` | 0071EC9A / 0071F0E1 | `A= B= F=calc` | House[esi+0x244] 标志位 | 红 |
| 4 | `0x04` | **DiscoveredByPlayer** | `flat(0x71ECAF chain)` | 0071EC9A / 0071F1B1 | `A= B= F=1` | 对象身份比对（被发现） | 红·UI依赖 |
| 5 | `0x05` | **HouseDiscovered** | `flat(0x71ECAF chain)` | 0071ECAF / 0071F0FB | `A= B= F=calc` | House[esi+0x1F4] 标志位 | 红 |
| 6 | `0x06` | **AttackedByAnybody** | `flat(0x71ECAF chain)` | 0071EC9A / 0071F1B1 | `A= B= F=calc` | 对象身份比对（被攻击，攻方登记） | 红 |
| 7 | `0x07` | **DestroyedByAnybody** | `flat(0x71ECAF chain)` | 0071EC9A / 0071F1B1 | `A= B= F=calc` | 对象身份比对（被摧毁） | 红 |
| 8 | `0x08` | **AnyEvent** | `flat(0x71ECAF chain)` | 0071ECAF / 0071F1B1 | `A= B= F=1` | 4 级默认目标：直接返回真（恒真） | 红 |
| 9 | `0x09` | **DestroyedUnitsAll** | `flat(0x71ECAF chain)` | 0071ECAF / 0071F12F | `A= B= F=calc` | House+0x5564/+0x5578 容器计数（call 0x49FB60） | 红 |
| 10 | `0x0A` | **DestroyedBuildingsAll** | `flat(0x71ECAF chain)` | 0071ECAF / 0071F115 | `A= B= F=calc` | House+0x2F0 计数 > 0 | 红 |
| 11 | `0x0B` | **DestroyedAll** | `flat(0x71ECAF chain)` | 0071ECAF / 0071F189 | `A= B= F=calc` | House+0x2F0 ≤ 0 且两容器计数 ≤ 0 | 红 |
| 12 | `0x0C` | **CreditsExceed** | `flat(0x71ECAF chain)` | 0071ECAF / 0071EF01 / 0071F1B1 | `A= B= F=calc` | House vfunc+0x18（取资金）与 arg(+0x34) 比较 | 红 |
| 13 | `0x0D` | **ElapsedTime** | `0071EC33` sel=0 | 0071ECAF / 0071F069 / 0071F1B1 | `A=1 B=0 F=calc` | Timer{start@+0,dur@+8} 与 CurrentFrame@0xA8ED84 比较 | 红 |
| 14 | `0x0E` | **MissionTimerExpired** | `0071EBE9` sel=1 | 0071ECAF / 0071F069 / 0071F1B1 | `A=1 B=1 F=calc` | Scenario[0xA8B230]+0x11E8/+0x11F0 任务计时器为 -1 检查 | 红 |
| 15 | `0x0F` | **DestroyedBuildingsNum** | `0071EC63` sel=11 | 0071ECAF / 0071F03F / 0071F1B1 | `A=1 B=1 F=calc` | House+0x5488 被毁建筑计数 ≥ arg | 红 |
| 16 | `0x10` | **DestroyedUnitsNum** | `0071EC63` sel=11 | 0071ECAF / 0071F058 / 0071F1B1 | `A=1 B=1 F=calc` | House+0x5434 被毁单位计数 < arg | 红 |
| 17 | `0x11` | **NoFactoriesLeft** | `0071EC63` sel=11 | 0071ECAF / 0071EF3F / 0071F1B1 | `A=0 B=1 F=calc` | House+0x2F0 工厂数 ≤ 0 且 +0x78 列表空 | 红 |
| 18 | `0x12` | **CiviliansEvacuated** | `0071EC63` sel=11 | 0071EC9A / 0071EF8E / 0071F1B1 | `A=1 B=0 F=calc` | House+0x1F9 平民撤离标志 | 红 |
| 19 | `0x13` | **BuildBuildingType** | `0071EC63` sel=11 | 0071EC9A / 0071EFEB / 0071F1B1 | `A=1 B=1 F=calc` | House+0x26C 最近建造建筑类型 id == arg | 红 |
| 20 | `0x14` | **BuildUnitType** | `0071EC63` sel=11 | 0071EC9A / 0071F003 / 0071F1B1 | `A=0 B=1 F=calc` | House+0x274 最近建造载具类型 id == arg | 红 |
| 21 | `0x15` | **BuildInfantryType** | `0071EC63` sel=11 | 0071EC9A / 0071F01D / 0071F1B1 | `A=0 B=1 F=calc` | House+0x270 最近建造步兵类型 id == arg | 红 |
| 22 | `0x16` | **BuildAircraftType** | `0071EC63` sel=11 | 0071EC9A / 0071F037 / 0071F1B1 | `A=0 B=1 F=calc` | House+0x278 最近建造飞机类型 id == arg | 红 |
| 23 | `0x17` | **TeamLeavesMap** | `0071EC63` sel=11 | 0071EC9A / 0071EEA9 / 0071F1B1 | `A=0 B=1 F=calc` | 全局队伍表 [0x8B40EC]/[0x8B40F8] + TeamType(+0x30) 比对 | 红 |
| 24 | `0x18` | **ZoneEntryBy** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=0 B=1 F=1` | 对象进入区域（身份比对） | 红 |
| 25 | `0x19` | **CrossesHorizontalLine** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=0 B=1 F=1` | 跨水平线（对象坐标 vs arg） | 红 |
| 26 | `0x1A` | **CrossesVerticalLine** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=0 B=1 F=1` | 跨垂直线 | 红 |
| 27 | `0x1B` | **GlobalSet** | `0071EB53` sel=2 | 0071ECAF / 0071F069 / 0071F1B1 | `A=0 B=1 F=calc` | arg → call 0x689760（全局变量查询） | 红 |
| 28 | `0x1C` | **GlobalCleared** | `0071EB75` sel=3 | 0071ECAF / 0071F069 / 0071F1B1 | `A=0 B=1 F=calc` | 同上取反 | 红 |
| 29 | `0x1D` | **DestroyedFakesAll** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=0 B=1 F=calc` | 假建筑被毁（身份比对） | 红 |
| 30 | `0x1E` | **LowPower** | `0071EC63` sel=11 | 0071ECAF / 0071F069 / 0071F099 | `A=1 B=1 F=calc` | call 0x4FCE30（房电力）vs 常量 [0x7E1718] | 红 |
| 31 | `0x1F` | **AllBridgesDestroyed** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=1 B=1 F=1` | 全桥被毁（地图状态） | 红 |
| 32 | `0x20` | **BuildingExists** | `0071EC63` sel=11 | 0071ECAF / 0071EFA8 / 0071F1B1 | `A=1 B=1 F=calc` | House+0x5550 容器 + call 0x49FAE0 命中 | 红 |
| 33 | `0x21` | **SelectedByPlayer** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=1 B=1 F=calc` | 被玩家选中（**依赖本机交互/UI**） | **最高危** |
| 34 | `0x22` | **ComesNearWaypoint** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=1 B=1 F=calc` | 靠近路径点（对象坐标 + Waypoint） | 红 |
| 35 | `0x23` | **EnemyInSpotlight** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=1 B=1 F=calc` | 敌人进入探照灯（**依赖本机探照灯**） | **最高危** |
| 36 | `0x24` | **LocalSet** | `0071EB9E` sel=4 | 0071ECAF / 0071F069 / 0071F1B1 | `A=1 B=1 F=calc` | arg → call 0x689A00（局部变量查询） | 红 |
| 37 | `0x25` | **LocalCleared** | `0071EBC0` sel=5 | 0071ECAF / 0071F069 / 0071F1B1 | `A=1 B=1 F=calc` | 同上取反 | 红 |
| 38 | `0x26` | **FirstDamaged_combatonly** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=1 B=1 F=calc` | 首次受伤（战斗来源，攻击方登记） | 红 |
| 39 | `0x27` | **HalfHealth_combatonly** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=0 B=1 F=calc` | 半血（战斗来源） | 红 |
| 40 | `0x28` | **QuarterHealth_combatonly** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=0 B=1 F=calc` | 四分之一血（战斗来源） | 红 |
| 41 | `0x29` | **FirstDamaged_anysource** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=1 B=1 F=calc` | 首次受伤（任何来源） | 红 |
| 42 | `0x2A` | **HalfHealth_anysource** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=0 B=1 F=calc` | 半血（任何来源） | 红 |
| 43 | `0x2B` | **QuarterHealth_anysource** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=1 B=0 F=calc` | 四分之一血（任何来源） | 红 |
| 44 | `0x2C` | **AttackedByHouse** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=0 B=1 F=calc` | 被指定房攻击（攻方房号） | 红 |
| 45 | `0x2D` | **AmbientLightBelow** | `0071EAE7` sel=6 | 0071ECAF / 0071F069 / 0071F1B1 | `A=1 B=1 F=calc` | Scenario+0x352C（环境光）< arg | 黄 |
| 46 | `0x2E` | **AmbientLightAbove** | `0071EB06` sel=7 | 0071ECAF / 0071F069 / 0071F1B1 | `A=1 B=1 F=calc` | Scenario+0x352C > arg | 黄 |
| 47 | `0x2F` | **ElapsedScenarioTime** | `0071EB28` sel=8 | 0071ECAF / 0071F069 / 0071F1B1 | `A=1 B=1 F=calc` | CurrentFrame@0xA8ED84 × 魔数 0x88888889（帧→秒）≥ arg | 红 |
| 48 | `0x30` | **DestroyedByAnything** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=0 B=1 F=calc` | 被任何事物摧毁 | 红 |
| 49 | `0x31` | **PickupCrate** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=0 B=1 F=calc` | 拾取木箱（指定对象） | 红·UI依赖 |
| 50 | `0x32` | **PickupCrate_any** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=1 B=1 F=calc` | 拾取木箱（不限对象） | 红·UI依赖 |
| 51 | `0x33` | **RandomDelay** | `0071EC33` sel=0 | 0071ECAF / 0071F069 / 0071F1B1 | `A=1 B=1 F=calc` | **与 ElapsedTime 同体**：Timer vs CurrentFrame（名 Random 但**不吃 RNG**） | 红 |
| 52 | `0x34` | **CreditsBelow** | `0071EC63` sel=11 | 0071ECAF / 0071EF20 / 0071F1B1 | `A=1 B=1 F=calc` | House vfunc+0x18（资金）≤ arg | 红 |
| 53 | `0x35` | **SpyAsHouse** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=1 B=1 F=1` | 间谍伪装成某房 | 红 |
| 54 | `0x36` | **SpyAsInfantry** | `0071EC63` sel=11 | 0071EC9A / 0071F069 / 0071F1B1 | `A=1 B=1 F=1` | 间谍伪装成某步兵（TechnoName） | 红 |
| 55 | `0x37` | **DestroyedUnitsNaval** | `0071EC63` sel=11 | 0071ECAF / 0071F069 / 0071F159 | `A=1 B=1 F=calc` | House+0x2EC 被毁海军计数 > 0 | 红 |
| 56 | `0x38` | **DestroyedUnitsLand** | `0071EC63` sel=11 | 0071ECAF / 0071F069 / 0071F16F | `A=1 B=0 F=calc` | House+0x2E8/+0x2EC/+0x2F4 陆上单位计数 | 红 |
| 57 | `0x39` | **BuildingDoesNotExist** | `0071EC63` sel=11 | 0071ECAF / 0071EFCB / 0071F1B1 | `A=0 B=1 F=calc` | House+0x5550 容器 + call 0x49FAE0 未命中 | 红 |
| 58 | `0x3A` | **PowerFull** | `0071EC63` sel=11 | 0071ECAF / 0071F0BD | `A=0 B=1 F=calc` | call 0x4FCE30（房电力）反向比较 | 红 |
| 59 | `0x3B` | **EnteredOrOverflownBy** | `0071EC63` sel=11 | 0071EC9A | `A=0 B=1 F=1` | 被进入或被飞越（对象类型比对） | 红 |
| 60 | `0x3C` | **TechTypeExists** | `0071E96B` sel=9 | — | `A=1 B=1 F=` | 遍历 [0xA8EAEC]/[0xA8EB10]，比对 ob->TypeName(+0x24) 与 TechnoName(+0x38) | 红 |
| 61 | `0x3D` | **TechTypeDoesntExist** | `0071EA30` sel=10 | — | `A=1 B=1 F=` | 同上取反 | 红 |

﻿> **表长自证（布局级）**：`0x71F218 + 12×4 = 0x71F248` —— 12 项目标表与 49 字节选择表在文件中**紧邻连续**；选择表末尾 `0x71F248 + 0x31 = 0x71F279` 处为 `8D 49 00`（`lea ecx,[ecx]` 对齐填充，[实证]），紧随 `0x71F27C` 即 2 级跳表（`9A EC 71 00 | AF EC 71 00`）。三级/四级/GetState/GetFlags 各表同构（目标表 + 紧邻选择表，见 `event_aux_tables.txt`）。

﻿---

## 4. 附录 A：队伍脚本动作表（`TeamClass::AI 0x6E9050`，跳表 `0x6E9F74`，**65 项**）

派发原文 [实证]：

```
006E944B  83 F8 40                    cmp eax, 0x40              ; 65 项（0..0x40）
006E9451  89 4C 24 24                 mov dword ptr [esp + 0x24], ecx
006E9455  0F 87 50 01 00 00           ja  0x6E95AB              ; 越界默认
006E945B  FF 24 85 74 9F 6E 00        jmp dword ptr [eax*4 + 0x6E9F74]
```

- 索引值来自 `call 0x691500`（`ScriptClass::GetCurrentAction`，YRpp `ScriptClass.h:32`）返回结构的首 dword（`ScriptClass+0x2C` 类字段）→ 即**队伍脚本的动作号**，与 `TriggerAction` 无关。
- 与触发器系统的关系：**仅通过触发器动作 4（CreateTeam）/ 7 / 80 / 107 间接触发**（建队后队伍执行自己的脚本）。二者编号空间不同、所有者不同（`TeamClass` vs `TActionClass`）。
- 该表就是派单锚点 `0x006E9CE8`（Action 49 = Success → 写 `[esi+0x84] = 1`）的所属表，交叉引用 `house_team_ai_update.md`（其结论与本表一致）。

| 动作号 | 派发入口 VA | 文件偏移 | this 读写 | 关键调用 |
|---|---|---|---|---|

| 00 | `006E9783` | `002E9783` | - | sub_006ED090 |
| 01 | `006E9605` | `002E9605` | - | sub_006EC9A0 |
| 02 | `006E95AB` | `002E95AB` | - | - |
| 03 | `006E95EC` | `002E95EC` | - | sub_006EC7D0 |
| 04 | `006E95B3` | `002E95B3` | - | sub_005657A0 |
| 05 | `006E97CE` | `002E97CE` | this+0x58 | sub_006EB870;sub_00426630 |
| 06 | `006E98AE` | `002E98AE` | this+0x28 | sub_006915A0 |
| 07 | `006E98C9` | `002E98C9` | - | HouseClass::Win |
| 08 | `006E9CC8` | `002E9CC8` | - | sub_006EF110 |
| 09 | `006E97B5` | `002E97B5` | - | sub_006ED4D0 |
| 0A | `006E9832` | `002E9832` | - | sub_006EDB50 |
| 0B | `006E9812` | `002E9812` | - | sub_006ED7E0 |
| 0C | `006E982B` | `002E982B` | - | - |
| 0D | `006E9879` | `002E9879` | this+0x54 | - |
| 0E | `006E979C` | `002E979C` | - | sub_006ED200 |
| 0F | `006E9637` | `002E9637` | - | sub_006ECE60 |
| 10 | `006E961E` | `002E961E` | - | sub_006ECCE0 |
| 11 | `006E972C` | `002E972C` | this+0x28 | CRT::_new;ScriptClass::noinit_t;sub_00691590 |
| 12 | `006E96BD` | `002E96BD` | this+0x2C | CRT::_new;TeamClass::noinit_t |
| 13 | `006E984B` | `002E984B` | this+0x54 | - |
| 14 | `006E9683` | `002E9683` | this+0x54 | - |
| 15 | `006E9650` | `002E9650` | this+0x54 | - |
| 16 | `006E9583` | `002E9583` | this+0x34 this+0x54 | sub_00580BC0;sub_006E9050;sub_006EBAD0 |
| 17 | `006E98E5` | `002E98E5` | - | HouseClass::Lose |
| 18 | `006E94BA` | `002E94BA` | - | - |
| 19 | `006E9901` | `002E9901` | - | VocClass::PlayGlobal |
| 1A | `006E9921` | `002E9921` | - | sub_005BF260 |
| 1B | `006E993E` | `002E993E` | - | sub_00720B20 |
| 1C | `006E9958` | `002E9958` | this+0x54 | sub_0057B790 |
| 1D | `006E99C8` | `002E99C8` | this+0x2C | - |
| 1E | `006E99E1` | `002E99E1` | this+0x2C | - |
| 1F | `006E99FD` | `002E99FD` | this+0x54 this+0x6C this+0x90 this+0x74 this+0x81 | - |
| 20 | `006E9A74` | `002E9A74` | - | sub_0053A100;sub_00539EB0 |
| 21 | `006E9AAE` | `002E9AAE` | - | sub_0053A100;sub_0053A090 |
| 22 | `006E9ACF` | `002E9ACF` | this+0x34 | MapClass::GetCellFloorHeight/MapClass::sub_578080;sub_00565730;TacticalClass::FocusOn |
| 23 | `006E9B6B` | `002E9B6B` | - | sub_00577BB0 |
| 24 | `006E9B86` | `002E9B86` | - | sub_00577F30 |
| 25 | `006E954D` | `002E954D` | this+0x54 | - |
| 26 | `006E9530` | `002E9530` | - | sub_00689670 |
| 27 | `006E9BA1` | `002E9BA1` | - | sub_00689910 |
| 28 | `006E9BBE` | `002E9BBE` | - | sub_00689910 |
| 29 | `006E9BDB` | `002E9BDB` | this+0x54 | - |
| 2A | `006E9C09` | `002E9C09` | - | sub_006EDCA0 |
| 2B | `006E9C22` | `002E9C22` | this+0x54 | - |
| 2C | `006E9462` | `002E9462` | this+0x54 | CRT::strcmpi;sub_00747370 |
| 2D | `006E94C9` | `002E94C9` | this+0x54 | CRT::strcmpi;sub_00747370 |
| 2E | `006E9C64` | `002E9C64` | - | sub_006EE310 |
| 2F | `006E9C7D` | `002E9C7D` | - | sub_006EE3F0 |
| 30 | `006E9CAF` | `002E9CAF` | - | sub_006EE800 |
| 31 | `006E9CE1` | `002E9CE1` | - | - |
| 32 | `006E9CF7` | `002E9CF7` | this+0x54 | - |
| 33 | `006E9D29` | `002E9D29` | - | sub_006EF610 |
| 34 | `006E9D42` | `002E9D42` | this+0x54 | sub_0070F120 |
| 35 | `006E9D63` | `002E9D63` | - | sub_006EF700 |
| 36 | `006E9D7C` | `002E9D7C` | - | sub_006EFA10 |
| 37 | `006E9D95` | `002E9D95` | - | sub_006EFC70 |
| 38 | `006E9DAE` | `002E9DAE` | - | sub_006EFE60 |
| 39 | `006E9DC7` | `002E9DC7` | - | sub_006F0130 |
| 3A | `006E9C96` | `002E9C96` | - | sub_006EE5C0 |
| 3B | `006E9DE0` | `002E9DE0` | - | sub_006ECA70 |
| 3C | `006E9DF9` | `002E9DF9` | this+0x54 | TeamClass::LiberateMember |
| 3D | `006E9E3E` | `002E9E3E` | this+0x54 | TeamClass::LiberateMember |
| 3E | `006E9E83` | `002E9E83` | this+0x54 | TeamClass::LiberateMember |
| 3F | `006E9EC8` | `002E9EC8` | this+0x54 | TeamClass::LiberateMember |
| 40 | `006E9F0D` | `002E9F0D` | this+0x54 | TeamClass::LiberateMember |

﻿---

## 5. 附录 B：参数序列化类别（`GetMode 0x6E3B60`）与位域（`GetFlags 0x6E3EE0`）

### 5.1 GetMode（144 项，kinds 1..0x90）

```
006E3B60  8D 41 FF              lea eax, [ecx - 1]
006E3B63  3D 8F 00 00 00        cmp eax, 0x8F        ; 覆盖 ActionKind 1..0x90（144）
006E3B68  0F 87 DB 00 00 00     ja  0x6E3C49         ; 0x91(JumpCameraHome)=无参
006E3B70  8A 88 D8 3C 6E 00     mov cl, byte ptr [eax + 0x6E3CD8]   ; 选择表 144 B
006E3B76  FF 24 8D 4C 3C 6E 00  jmp dword ptr [ecx*4 + 0x6E3C4C]    ; 跳表（每目标 = mov eax,imm; ret）
```

每个目标体仅 `B8 imm32 C3`（`mov eax,imm; ret`），故 mode 值可直接逐项读出（`out/re_work/triggers/getmode_table.txt`）。**语义由消费方实证**：唯一调用方 `TActionClass::PrepareSaveToINI 0x6DD300`（`0x6DD30B: E8 50 68 00 00`）按 mode 决定把哪个字段写成**名字**还是**数字**：

| mode | 消费分支（[实证]） | 被取字段 | 语义 |
|---|---|---|---|
| `0x2F`/`0x2B` | `0x6DD31A: cmp eax,0x2F` / `0x6DD352: cmp eax,0x2B` | `lea ebp,[esi+0x54]` | **TechnoID 字符串**（存档类型码 9） |
| `0x2E` | `0x6DD338: cmp eax,0x2E` | `[esi+0x48]`+`[esi+0x90]` | 双整数（Value2+Value，存档类型码 0xb） |
| `0x2D` | `0x6DD364: cmp eax,0x2D` | `[esi+0x54]` | TechnoID（存档类型码 0xa） |
| `0x28` | `0x6DD37D: cmp eax,0x28` | `TeamType*[0x30]` → 名 `+0x24`，并另存 `+0x98` | **队伍名**（类型码 5） |
| `0x0C`/`0x22` | `0x6DD39D`/`0x6DD3A2` | `TeamType*[0x30]` | 队伍名（类型码 1） |
| `0x0B` | `0x6DD3C5: cmp eax,0x0B` | `TriggerType*[0x50]` → 名 `+0x24`，另存 `+0x98` | **触发器名**（类型码 2） |
| `0x1A` | `0x6DD3E5: cmp eax,0x1A` | `TagType*[0x4C]` | **标签名**（类型码 3） |
| `0x27` | `0x6DD3FE: cmp eax,0x27` | `lea ebp,[esi+0x6D]`（空则写 `"-1"`） | **文本缓冲**（类型码 4） |
| `4` | `0x6DD41D: cmp eax,4` | `call 0x752460` | **Vox（语音）名**查找：`[0xB1D4A4]` 数组 + `[0xB1D4B0]` 计数，越界回退 `0x817694`（类型码 6）[实证+推演] |
| `3`/`0x26` | `0x6DD42E`/`0x6DD433` | `call 0x751590` | **Voc（音效）名**查找：`[0xB1D37C]` 数组 + `[0xB1D388]` 计数，越界回退 `0x817474`/`0x846574`（类型码 7）[实证+推演] |
| `1` | `0x6DD438: cmp eax,1` | `[0xA83D10]` + `call 0x721270` | **主题名**查找：`ecx+0x18` 数组 + `ecx+0x24` 计数（类型码 8）[实证+推演] |
| 其余（9/10/11/12/13/16/…） | 落到 `0x6DD45B` 默认 | `[esi+0x90]` 原样 | **纯数字**（类型码 0） |

> 校验：`mode=11` 的 4 个动作（DestroyTrigger/ForceTrigger/EnableTrigger/DisableTrigger）实测读 `[this+0x50]`=TriggerType*；`mode=13` 的 21 个动作全部经 `TActionClass::FindHouseByIndex 0x6E45E0` 取房号 → 与上表一致。[实证+推演]

### 5.2 GetFlags（98 项，kinds 0x0E..0x6F）

```
006E3EE5  83 F9 61              cmp ecx, 0x61       ; ecx = ActionKind - 0x0E → 98 项
006E3EEC  8A 91 08 3F 6E 00     mov dl, byte ptr [ecx + 0x6E3F08]
006E3EF2  FF 24 95 00 3F 6E 00  jmp dword ptr [edx*4 + 0x6E3F00]
006E3EF9  B8 02 00 00 00        mov eax, 2          ; flags = 2
006E3EFE  C3                    ret                 ; flags = 0（默认）
```

实测 `flags = 2` 的动作仅 **7** 个：`0x0E ChangeHouse`、`0x20 DestroyAttachedObject`、`0x3C SellBuilding`、`0x3D TurnOffBuilding`、`0x3E TurnOnBuilding`、`0x5B GoBerzerk`、`0x6F EvictOccupiers`。[实证]
共同特征：这 7 项的实现体都读 `[this+0x34]`（`Bounds`）+ `[this+0x81]`，且全部调用 `TagClass::ContainsTrigger` —— 即**需要"源对象"上下文**才可执行（[推演]，与 `FireActions` 传入的 `pObject`/`location` 参数一致）。

﻿---

## 6. 名称来源与证据级别（重要口径）

1. **本体无枚举名字表**：对 `ElapsedTime`/`GlobalSet`/`AnnounceWin` 等名字做全文件搜索，命中处均为调试日志文本（如 `0x83D8F3` 一带是 `Scenario.CPP` 的 `ElapsedTimer = %ld` 字符串），**不是** kind↔name 映射表；`TActionClass::LoadFromINI 0x6DD5B0` 解析的是**数字**（`call 0x7C9BFD`/`0x7C9CC2` = `atoi` 系）而非名字。见 `out/re_work/triggers/name_tables.txt`、`find_names.py`。
2. 因此本表"名称"列取自 `YRpp/GeneralDefinitions.h` 的 `enum class TriggerAction` / `TriggerEvent`（[推演/命名]，非本体字节证据）。**编号列、派发入口列、参数列、副作用列均为 [实证]**。
3. **编号对齐已被独立验证**（不依赖枚举名）：用「内联体调用集 vs YRpp `ACTION_FUNC` 函数调用集」做匹配，64 个动作获得 ≥0.66 的双证据命中（`[M+N]`），例如 `0x04 CreateTeam`↔`0x6E1F60`、`0x0A PlayMovie`↔`0x6E16D0`（6/6 调用全同）、`0x31 ZoomIn`↔`0x6E2860`（6/6）、`0x37 CreateRadarEvent`↔`0x6E2BB0`、`0x3B ReduceTiberium`↔`0x6E1180`、`0x0C DestroyTrigger`↔`0x6E2A10`、`0x22 AddRepeatingSW`↔`0x6E1C40`。见 `out/re_work/triggers/action_slave_match.txt`、`slave_final.tsv`。
4. 派单给定的 `superweapon_re.md` 锚点 `0x6DE93F` 落在本表 `0x21 AddOneTimeSuperWeapon`（派发入口 `0x6DE925`）体内 —— 与超武文档一致。[实证]

---

## 7. 字节断言复算（`python tools/audit_bytes.py out/re_work/triggers/claims.txt`）

`claims.txt` 共 **77** 条，全部 `OK`（`MISMATCH/NOREAD = 0`），JSON：`out/re_work/triggers/audit.json`。

```
合计 77 条：OK=77  MISMATCH/NOREAD=0
```

代表性断言（原文摘录，VA = 字节，`#` 后为标签）：

```
0x6DD8DB = 81 FA 90 00 00 00   # dec edx / cmp edx,0x90 -> 145-entry bound
0x6DD8E7 = FF 24 95 EC FD 6D 00 # jmp dword ptr [edx*4 + 0x6DFDEC]
0x6DFDEC = 37 EA 6D 00 67 EA 6D 00 # table[0]=0x6DEA37(Win) table[1]=0x6DEA67(Lose)
0x6E002C = D6 FD 6D 00         # table[144]=0x6DFDD6 (kind 0x91 JumpCameraHome)
0x6DFDE1 = 81 C4 40 02 00 00   # Execute 尾声 add esp,0x240（表紧接其后）
0x6DFDE7 = C2 10 00            # ret 0x10 ; 0x6DFDEA: 8B FF(hotpatch pad) -> 0x6DFDEC 表头
0x6E0030 = B0 01 C2 10         # 表尾后为 mov al,1; ret 0x10 + CC 填充，证明表止于 0x6E002F
0x71F279 = 8D 49 00            # 49 槽选择表结束处为对齐填充，紧随 0x71F27C 二级跳表
0x71E950 = 8D 41 F3 83 F8 30 0F 87 # lea eax,[ecx-0xD]; cmp eax,0x30
0x71E964 = FF 24 95 18 F2 71 00 # jmp dword ptr [edx*4 + 0x71F218]
0x71F248 = 00 01 0B 0B 0B 0B 0B 0B # 49 字节选择表头
0x6E944B = 83 F8 40            # TeamClass::AI: cmp eax,0x40 (65)
0x6E945B = FF 24 85 74 9F 6E 00 # jmp dword ptr [eax*4 + 0x6E9F74]
0x6EA038 = E1 9C 6E 00         # team-script table[49] = 0x6E9CE1
0x6E9CE1 = C6 86 80 00 00 00 01 C6 86 84 00 00 # [esi+0x80]=1 ; [esi+0x84]=1（锚点 0x6E9CE8）
0x726605 = E8 A6 72 FB FF     # FireActions: call 0x6DD8B0
0x726540 = E8 FB 83 FF FF     # RegisterEvent: call 0x71E940
0x7271F4 = E8 87 84 FF FF     # TriggerTypeClass::GetFlags: call 0x71F680
0x72720F = E8 CC CC FB FF     # TriggerTypeClass::GetFlags: call 0x6E3EE0
0x6DD30B = E8 50 68 00 00     # PrepareSaveToINI: call 0x6E3B60 (GetMode)
```

> 逐条明细（含 capstone 反汇编上下文）见 `out/re_work/triggers/audit.json`。**注**：`claims.txt` 中 4 条"上界/表尾"类断言（`0x6DD8DB`、`0x6E0030`、`0x71E950`、`0x6E944B`）是**表长自证**的核心：上界立即数与表尾越界字节共同确定表项数，无解释余地。

﻿---

## 8. 与 `net_sync_checksum.md` §9 的交叉引用（含勘误）

### 8.1 一致项（无矛盾）

| # | §9 的说法 | 本次复核（地址级） | 判定 |
|---|---|---|---|
| C1 | §9 记录 8 个 `FillEvent_*` 填充体及其 Kind→handler 对照 | 全 8 个填充体的调用点扫描结果与 §9 的"调用方=UI/生产/侧边栏"一致（`0x4AB9CC`、`0x6AA600`、`0x4F10E0`、`0x731840` 等），**无一在触发器代码区** | ✅ 一致 |
| C2 | §9.0 的"填充序"7 条规律（HouseIndex→Kind→载荷→Timestamp 末写） | 与触发器无关（不同系统）；触发器侧对应物是 `HasOccured` 的 4 级判定序（本文 §3）与 `FireActions` 的链表顺序 | ✅ 不冲突（不同系统） |
| C3 | §5.1 红线"必须 bit 级一致（禁改语义/顺序/次数）" | 本表 114 个非纯表现动作全部落在红线面；31 个纯表现动作落在 §5.3"可动"面 | ✅ 一致 |

### 8.2 勘误 E-1：`Action 49 / Success` 归属（**新旧对照**）

| 项 | 旧（派单锚点表述） | 新（本次实证） |
|---|---|---|
| 字节 | `0x006E9CE8 = C6 86 84 00 00 00 01` | **确认相同**（`mov byte [esi+0x84],1`） |
| 所属表 | 隐含为 `TActionClass` 动作表 | **`TeamClass::AI 0x6E9050` 的队伍脚本动作表 `0x6E9F74`**（`cmp eax,0x40` → 65 项；`table[49]=0x6E9CE1`） |
| 触发器动作 49 | — | `TActionClass` 动作 `49=0x31 = ZoomIn`，派发入口 `0x6DEEB8`（与 `0x6E9CE8` 无关） |
| 依据 | — | `0x6E944B: 83 F8 40`；`0x6E945B: FF 24 85 74 9F 6E 00`；`0x6EA038: E1 9C 6E 00`；且 `house_team_ai_update.md:368-369`、`re_sprint_S6_report.md:87-92` 亦记录同一结论 |

### 8.3 勘误 E-2：数值空间冲突（**交叉引用时必须区分**）

`NetworkEvent::Kind`（§9）与 `TriggerEvent`（本文表 B）**共用 `0x00..0x3D` 数值区间但语义无关**，且二者在同一进程内并存，极易误引：

| 数值 | §9 `NetworkEvent::Kind`（网络命令） | 本文 `TriggerEvent`（地图触发器事件） |
|---|---|---|
| `0x03` | Ally（结盟命令） | `ThievedBy` |
| `0x0B` | Place（放置命令，handler `0x4C70E1`） | `DestroyedAll` |
| `0x0C` | Options（玩家选项） | `CreditsExceed` |
| `0x0D` | GameSpeed | `ElapsedTime`（主判入口 `0x71EC33`） |
| `0x0E/0x0F/0x10` | Produce/Suspend/Abandon | `MissionTimerExpired`/`DestroyedBuildingsNum`/`DestroyedUnitsNum` |
| `0x12` | SpecialPlace（超武落点，handler `0x4C78D6`） | `CiviliansEvacuated` |
| `0x14` | Animation（**硬编码 Kind 0x14**，handler `0x4C6FDE`） | `BuildUnitType` |
| `0x17` | SellCell | `TeamLeavesMap` |

> **结论**：`net_sync_checksum.md` §9 中的 "Kind" 一律指 `NetworkEvent::Kind`；本文 "HEX/编号" 一律指 `TriggerEvent`/`TriggerAction`。两者**唯一共同点**是都用了小整数枚举，无任何实现层耦合（§1.3 已实证无调用关系）。

### 8.4 勘误 E-3：两个"名字会骗人"的项

| 项 | 直觉假设 | 实证 |
|---|---|---|
| `TriggerEvent 0x33 RandomDelay` | 用随机数延时（会消耗 RNG） | 与 `ElapsedTime` **同体**（`0x71EC33`）：Timer 结构（`{start@+0, dur@+8}`）与 `CurrentFrame@0xA8ED84` 比较，**不消耗 RNG** [实证] |
| `TriggerAction 0x62 PlaySoundEffectRandom` | 纯表现、无同步影响 | 体内调用 `Randomizer::RandomRanged` + `ScenarioClass::IsDefinedWaypoint`（`0x6DE7A5` 起）→ **消耗局内 RNG**，属 §2 RNG 契约面：各端调用次数必须一致，否则分叉 [实证] |

（`PlaySoundEffectRandom` 因此在本表标"黄"而非"绿"：它是 31 个纯表现动作里**唯一**属于 RNG 契约面的项。）

### 8.5 勘误 E-4：4 个"空实现"动作

`AllowWin(0x0F)`、`ChangeZoomLevel(0x27)`、`ActivateFirestorm(0x5C)`、`DeactivateFirestorm(0x5D)` 的派发目标只含 `mov al,1` + 函数尾声（`0x6DFDDB`/`0x6DFDDD`）[实证]。若其他文档/工具把它们当作生效动作（例如"AllowWin 开启胜利通道"），应改标为**本作未实现**。

﻿---

## 9. 联机风险判定规则与清单

### 9.1 规则（与 `net_sync_checksum.md` §5 红线表口径对齐）

| 标记 | 判据 | 依据 |
|---|---|---|
| **红** | 该动作会写对局逻辑状态（对象增删/属主/任务/胜负/变量/计时器/超武/外交/财金/地图遮罩与 overlay）→ 多端若语义或调用次数不同即分叉 | §5.1 "必须 bit 级一致（禁改语义/顺序/次数）" |
| **黄** | 只影响**本机**玩家侧视图/UI（输入锁、贴图、镜头、影片、文本），或**消耗同步 RNG**（`0x62`）→ 不进帧 CRC 对象扫描，但 RNG 消耗次数必须一致 | §5.3 + §2.2 |
| **绿** | 纯本机表现（音频/镜头/闪示/闪字/tab），不进同步契约，可独立优化 | §5.3 "可动（纯表现，不进同步契约）" |

> **注意**：触发器在**每端独立求值**（事件判定读的是本端状态），所以"红/黄/绿"是**动作副作用**的风险面；真正的分叉第一源是**事件判定输入**（表 B 的 UI 相关项，§9.3）。

### 9.2 纯表现 31 项（可优化候选面，"绿/黄"）

`0x0A PlayMovie`、`0x0B TextTrigger`、`0x13 PlaySoundEffect`、`0x14 PlayMusicTheme`、`0x15 PlaySpeech`、`0x28 ResizePlayerView`、`0x2E LockInput`、`0x2F UnlockInput`、`0x30 MoveCameraToWaypoint`、`0x31 ZoomIn`、`0x32 ZoomOut`、`0x34 ChangeLightBehavior`、`0x37 CreateRadarEvent`、`0x62 PlaySoundEffectRandom`（**黄**）、`0x63 PlaySoundEffectAtWaypoint`、`0x64 PlayIngameMovie`（黄）、`0x67 TimerText`（黄）、`0x68 FlashTeam`、`0x69 TalkBubble`、`0x70 CenterCameraAtWaypoint`、`0x71 MakeHouseCheer`、`0x72 SetTabTo`、`0x73 FlashCameo`、`0x74 StopSounds`、`0x75 PlayIngameMovieAndPause`（黄）、`0x7F StartChronoScreenEffect`、`0x83 FlashBuildingsOfType`、`0x8E/0x8F/0x90 Retint*`、`0x91 JumpCameraHome`
> **【DA2 复核 · 2026-09-27｜结论：本节「0x62 唯一 RNG 契约项」「0x63 无 RNG」两条均成立，无需订正】**
> 复核方法（可复跑 `out/re_work/da2/scan_rng3.py`）：对 §9.2 列出的 **31 项**逐一取其 `TActionClass` 跳表派发块（`0x6DFDEC`，块边界取 `out/re_work/triggers/action_dispatch_table.tsv`），统计**两层** RNG 触点 —— ①本块直接 `call`；②本块一级被调函数体（以 `ret` + 填充为边界）内的直接 `call`；RNG 判定集 = `0x65C780 Randomizer::Random` / `0x65C7E0 Randomizer::RandomRanged`。
> - **命中恰 1 项**：`0x62 PlaySoundEffectRandom`（块入口 `0x6DE7A5`，`0x006DE80F = E8 CC DF F7 FF` → `call 0x65C7E0`）⇒ 「31 个纯表现动作里**唯一**属于 RNG 契约面的项」**成立**。
> - **其余 30 项两层均无 RNG 触点**，其中 `0x63 PlaySoundEffectAtWaypoint`（块入口 `0x6DE845`，块内 `call 0x68BD00`/`0x6E1830`/`0x5F6CB0`）⇒ 「`0x63` 无 RNG」的**绿**判定**成立**。
> - 注：本节「唯一」的口径**限于这 31 项**；全表中另有 `0x3A MeteorShower` 消耗 RNG×4（该动作本表标**红**，见 §2.1 表中 `#` 列 = 58 的 `0x3A` 行 DA2 补注），两者不冲突。

### 9.3 高危事件输入（表 B，"红"中最危险的一类）

`0x04 DiscoveredByPlayer`、`0x21 SelectedByPlayer`、`0x23 EnemyInSpotlight`、`0x31/0x32 PickupCrate*`、`0x2F ElapsedScenarioTime`（帧→秒，依赖 `CurrentFrame`）、`0x33 RandomDelay`（Timer 语义）。
前 4 项依赖**本机交互/可见性**（选择、探照灯、拾取），在联机中不同玩家的求值时刻天然不同 → 若其触发链上有"红"动作，就会分叉。**这是触发器系统在 MP 场景的首要 review 面**。

### 9.4 改地图 11 项（"M"）

`0x10 RevealAllMap`、`0x11 RevealAroundWaypoint`、`0x12 RevealWaypointZone`、`0x1F GrowShroud`、`0x33 ReshroudMap`、`0x3B ReduceTiberium`、`0x55 VeinGrowth`、`0x56 TiberiumGrowth`、`0x57 IceGrowth`、`0x65 ReshroudMapAtWaypoint`、`0x76 ClearAllSmudges`
→ 其中 `ReduceTiberium`/`VeinGrowth`/`TiberiumGrowth`/`IceGrowth` **改 overlay/地形**，最可能进 `Checksummer`（`net_sync_checksum.md` §3.1）；遮罩类（Reveal*/Reshroud*）改的是 per-house 可见性状态 → [待实测] 是否进帧 CRC（§3.2）。

### 9.5 静态观察：无 MP 门控

全表未见按 `SessionClass`（`0xA8B238`）或 GameMode 分支的"联机禁用某动作"代码：145 个动作在 SP/MP 下走同一张表 [推演，证据=0x6DD8B0 函数体内无 0xA8B238 引用]。因此 MP 安全性完全取决于**地图作者**是否在 MP 图上使用"红"动作 + 事件判定是否确定。

---

## 10. 未闭环与下一步取法

| # | 未闭环项 | 状态 | 下一步取法 |
|---|---|---|---|
| U1 | 事件"发起方"映射：哪些代码以哪个 `EventKind` 调 `TriggerClass::RegisterEvent 0x7264C0` | 未闭环 | 扫描 `call 0x7264C0` 全部调用点，回溯其 `push` 常量/寄存器，按 kind 归类；预期落在 `ObjectClass::ReceiveDamage`、`BuildingClass::Sell`、拾取木箱等 |
| U2 | 2 级门 `0x71EC9A` 中的全局抑制位 `[0xA8ED6B]`（写入方/语义） | 部分闭环 | 扫 `mov byte [0xA8ED6B]` 的写入点（`out/re_work/triggers/xrefs.py` 已有扫描器可复用） |
| U3 | 3/4 级表的"中继"语义：`0x71F069`（进 4 级）与 `0x71F1B1`（默认返回真）的完备性 | 部分闭环 | 逐 kind 走通全部 62 条路径，标注"发起方判定"型 kind 集合 |
| U4 | mode `15/16/21/23/24/25/27/28/29/30/31/33/34/35/38/40/43/44/45/46/47` 的**精确**参数类型名 | [推演] | 每个 mode 抽一个代表动作，跟到实际使用点（如 `mode=43` 的 `SetObjectTechLevel` 读 `TechnoID+Value`）复核；`GetMode 0x6E3B60` 只被 `PrepareSaveToINI` 调用，语义只能由消费点定 |
| U5 | 11 个 "M" 动作是否进 `Checksummer` / 帧 CRC | [待实测] | 交叉 `net_sync_checksum.md` §3.1/§3.2 的扫描类目；需运行时比对 `SYNC*.TXT` |
| U6 | 145 项中的重复目标 | 已闭环 | `145 项 → 143 个不同目标`：唯一重复是 `0x6DFDDB` 被 `0x27 ChangeZoomLevel`/`0x5C ActivateFirestorm`/`0x5D DeactivateFirestorm` 共用（空实现体）；`0x0F AllowWin` 指向其相邻的 `0x6DFDDD`。团队脚本表 C 为 `65 项 → 65 个不同目标`（无共用）。对账数据：`out/re_work/triggers/action_dispatch_table.tsv`、`dups.py` 输出 |

> 说明：`distinct` 由 `out/re_work/triggers/dups.py` 直接对跳表 145 个 dword 去重得到（143），非估算。


---

## 附录 C：代表动作的指令级入口证据（26 项，字节级）

> 全 145 项的完整反汇编见 `out/re_work/triggers/action_blocks_full.txt`（含每项 VA + 原始字节 + 反汇编）。

### `0x21 AddOneTimeSuperWeapon` → 入口 `0x006DE925`（文件偏移 `0x2DE925`）

```
006DE925  8b bc 24 54 02 00 00 mov edi, dword ptr [esp + 0x254]
006DE92C  8b 86 90 00 00 00    mov eax, dword ptr [esi + 0x90]
006DE932  55                   push ebp
006DE933  55                   push ebp
006DE934  8b 8f 58 02 00 00    mov ecx, dword ptr [edi + 0x258]
006DE93A  6a 01                push 1
006DE93C  8b 0c 81             mov ecx, dword ptr [ecx + eax*4]
006DE93F  e8 1c cc fe ff       call 0x6cb560
006DE944  39 3d 4c 3d a8 00    cmp dword ptr [0xa83d4c], edi
```
调用：`SuperClass::Grant`, `SidebarClass::AddCameo`, `SidebarClass::GetObjectTabIdx`, `SidebarClass::RepaintSidebar`

### `0x22 AddRepeatingSuperWeapon` → 入口 `0x006DE98E`（文件偏移 `0x2DE98E`）

```
006DE98E  8b bc 24 54 02 00 00 mov edi, dword ptr [esp + 0x254]
006DE995  8b 86 90 00 00 00    mov eax, dword ptr [esi + 0x90]
006DE99B  55                   push ebp
006DE99C  55                   push ebp
006DE99D  8b 8f 58 02 00 00    mov ecx, dword ptr [edi + 0x258]
006DE9A3  55                   push ebp
006DE9A4  8b 0c 81             mov ecx, dword ptr [ecx + eax*4]
006DE9A7  e8 b4 cb fe ff       call 0x6cb560
006DE9AC  8b 96 90 00 00 00    mov edx, dword ptr [esi + 0x90]
```
调用：`SuperClass::Grant`, `SidebarClass::AddCameo`, `SidebarClass::GetObjectTabIdx`, `SidebarClass::RepaintSidebar`

### `0x04 CreateTeam` → 入口 `0x006DEB57`（文件偏移 `0x2DEB57`）

```
006DEB57  8b 0d ac e7 a8 00    mov ecx, dword ptr [0xa8e7ac]
006DEB5D  41                   inc ecx
006DEB5E  89 0d ac e7 a8 00    mov dword ptr [0xa8e7ac], ecx
006DEB64  8b 76 30             mov esi, dword ptr [esi + 0x30]
006DEB67  3b f5                cmp esi, ebp
006DEB69  74 08                je 0x6deb73
006DEB6B  55                   push ebp
006DEB6C  8b ce                mov ecx, esi
006DEB6E  e8 4d 1e 01 00       call 0x6f09c0
```
调用：`TeamTypeClass.CreateTeam`

### `0x05 DestroyTeam` → 入口 `0x006DEB8D`（文件偏移 `0x2DEB8D`）

```
006DEB8D  8b 76 30             mov esi, dword ptr [esi + 0x30]
006DEB90  3b f5                cmp esi, ebp
006DEB92  0f 84 43 12 00 00    je 0x6dfddb
006DEB98  8b ce                mov ecx, esi
006DEB9A  e8 d1 1e 01 00       call 0x6f0a70
006DEB9F  b0 01                mov al, 1
006DEBA1  5f                   pop edi
006DEBA2  5e                   pop esi
006DEBA3  5d                   pop ebp
```
调用：`TeamTypeClass.DestroyAllInstances`

### `0x07 Reinforcement` → 入口 `0x006DEBAE`（文件偏移 `0x2DEBAE`）

```
006DEBAE  8b 76 30             mov esi, dword ptr [esi + 0x30]
006DEBB1  3b f5                cmp esi, ebp
006DEBB3  0f 84 a9 0c 00 00    je 0x6df862
006DEBB9  83 ca ff             or edx, 0xffffffff
006DEBBC  8b ce                mov ecx, esi
006DEBBE  e8 1d ed f7 ff       call 0x65d8e0
006DEBC3  5f                   pop edi
006DEBC4  5e                   pop esi
006DEBC5  5d                   pop ebp
```
调用：`sub_0065D8E0`

### `0x0A PlayMovie` → 入口 `0x006DE72F`（文件偏移 `0x2DE72F`）

```
006DE72F  e8 7c f6 04 00       call 0x72ddb0
006DE734  8b 0d 40 76 88 00    mov ecx, dword ptr [0x887640]
006DE73A  8b 01                mov eax, dword ptr [ecx]
006DE73C  ff 50 14             call dword ptr [eax + 0x14]
006DE73F  32 c9                xor cl, cl
006DE741  e8 aa 5b fa ff       call 0x6842f0
006DE746  8b 8e 90 00 00 00    mov ecx, dword ptr [esi + 0x90]
006DE74C  6a 01                push 1
006DE74E  6a 01                push 1
```
调用：`sub_0072DDB0`, `VT+0x14`, `sub_006842F0`, `sub_005BF260`, `VT+0x18`, `sub_0072DEF0`

### `0x0C DestroyTrigger` → 入口 `0x006DF051`（文件偏移 `0x2DF051`）

```
006DF051  39 6e 50             cmp dword ptr [esi + 0x50], ebp
006DF054  0f 84 81 0d 00 00    je 0x6dfddb
006DF05A  8b 15 f8 ea a8 00    mov edx, dword ptr [0xa8eaf8]
006DF060  8d 7a ff             lea edi, [edx - 1]
006DF063  3b fd                cmp edi, ebp
006DF065  0f 8c 70 0d 00 00    jl 0x6dfddb
006DF06B  a1 ec ea a8 00       mov eax, dword ptr [0xa8eaec]
006DF070  8b 0c b8             mov ecx, dword ptr [eax + edi*4]
006DF073  8b 46 50             mov eax, dword ptr [esi + 0x50]
```
调用：`TriggerClass.Destroy`

### `0x10 RevealAllMap` → 入口 `0x006DE3A8`（文件偏移 `0x2DE3A8`）

```
006DE3A8  a1 4c 3d a8 00       mov eax, dword ptr [0xa83d4c]
006DE3AD  8a 88 40 02 00 00    mov cl, byte ptr [eax + 0x240]
006DE3B3  84 c9                test cl, cl
006DE3B5  0f 85 20 1a 00 00    jne 0x6dfddb
006DE3BB  b9 e8 f7 87 00       mov ecx, 0x87f7e8
006DE3C0  c6 80 40 02 00 00 01 mov byte ptr [eax + 0x240], 1
006DE3C7  e8 84 9f e9 ff       call 0x578350
006DE3CC  b9 e8 f7 87 00       mov ecx, 0x87f7e8
006DE3D1  e8 ba 9e e9 ff       call 0x578290
```
调用：`MapClass.CellIteratorReset`, `MapClass.CellIteratorNext`, `sub_00653810`, `MapClass.RedrawSidebar`

### `0x13 PlaySoundEffect` → 入口 `0x006DE780`（文件偏移 `0x2DE780`）

```
006DE780  8b 8e 90 00 00 00    mov ecx, dword ptr [esi + 0x90]
006DE786  55                   push ebp
006DE787  ba 00 20 00 00       mov edx, 0x2000
006DE78C  68 00 00 80 3f       push 0x3f800000
006DE791  e8 8a 21 07 00       call 0x750920
006DE796  b0 01                mov al, 1
006DE798  5f                   pop edi
006DE799  5e                   pop esi
006DE79A  5d                   pop ebp
```
调用：`VocClass.PlayGlobal`

### `0x14 PlayMusicTheme` → 入口 `0x006DE8E4`（文件偏移 `0x2DE8E4`）

```
006DE8E4  8b 96 90 00 00 00    mov edx, dword ptr [esi + 0x90]
006DE8EA  b9 10 3d a8 00       mov ecx, 0xa83d10
006DE8EF  52                   push edx
006DE8F0  e8 2b 22 04 00       call 0x720b20
006DE8F5  b0 01                mov al, 1
006DE8F7  5f                   pop edi
006DE8F8  5e                   pop esi
006DE8F9  5d                   pop ebp
006DE8FA  5b                   pop ebx
```
调用：`sub_00720B20`

### `0x15 PlaySpeech` → 入口 `0x006DE904`（文件偏移 `0x2DE904`）

```
006DE904  8b 8e 90 00 00 00    mov ecx, dword ptr [esi + 0x90]
006DE90A  6a ff                push -1
006DE90C  ba 02 00 00 00       mov edx, 2
006DE911  e8 6a 3b 07 00       call 0x752480
006DE916  b0 01                mov al, 1
006DE918  5f                   pop edi
006DE919  5e                   pop esi
006DE91A  5d                   pop ebp
006DE91B  5b                   pop ebx
```
调用：`VoxClass.PlayIndex`

### `0x16 ForceTrigger` → 入口 `0x006DF0E7`（文件偏移 `0x2DF0E7`）

```
006DF0E7  39 6e 50             cmp dword ptr [esi + 0x50], ebp
006DF0EA  0f 84 eb 0c 00 00    je 0x6dfddb
006DF0F0  a1 f8 ea a8 00       mov eax, dword ptr [0xa8eaf8]
006DF0F5  33 ff                xor edi, edi
006DF0F7  3b c5                cmp eax, ebp
006DF0F9  0f 8e dc 0c 00 00    jle 0x6dfddb
006DF0FF  8b 0d ec ea a8 00    mov ecx, dword ptr [0xa8eaec]
006DF105  8b 46 50             mov eax, dword ptr [esi + 0x50]
006DF108  8b 0c b9             mov ecx, dword ptr [ecx + edi*4]
```
调用：`TriggerClass.FireActions`

### `0x17 TimerStart` → 入口 `0x006DE418`（文件偏移 `0x2DE418`）

```
006DE418  a1 30 b2 a8 00       mov eax, dword ptr [0xa8b230]
006DE41D  83 c9 ff             or ecx, 0xffffffff
006DE420  8b 90 e8 11 00 00    mov edx, dword ptr [eax + 0x11e8]
006DE426  3b d1                cmp edx, ecx
006DE428  0f 85 ad 19 00 00    jne 0x6dfddb
006DE42E  3b d1                cmp edx, ecx
006DE430  75 0c                jne 0x6de43e
006DE432  8b 0d 84 ed a8 00    mov ecx, dword ptr [0xa8ed84]
006DE438  89 88 e8 11 00 00    mov dword ptr [eax + 0x11e8], ecx
```
调用：`sub_006D0F00`

### `0x1C GlobalSet` → 入口 `0x006DE2CE`（文件偏移 `0x2DE2CE`）

```
006DE2CE  8b 8e 90 00 00 00    mov ecx, dword ptr [esi + 0x90]
006DE2D4  6a 01                push 1
006DE2D6  51                   push ecx
006DE2D7  8b 0d 30 b2 a8 00    mov ecx, dword ptr [0xa8b230]
006DE2DD  e8 8e b3 fa ff       call 0x689670
006DE2E2  b0 01                mov al, 1
006DE2E4  5f                   pop edi
006DE2E5  5e                   pop esi
006DE2E6  5d                   pop ebp
```
调用：`sub_00689670`

### `0x1F GrowShroud` → 入口 `0x006DE2B5`（文件偏移 `0x2DE2B5`）

```
006DE2B5  b9 e8 f7 87 00       mov ecx, 0x87f7e8
006DE2BA  e8 01 e8 dc ff       call 0x4acac0
006DE2BF  b0 01                mov al, 1
006DE2C1  5f                   pop edi
006DE2C2  5e                   pop esi
006DE2C3  5d                   pop ebp
006DE2C4  5b                   pop ebx
006DE2C5  81 c4 40 02 00 00    add esp, 0x240
006DE2CB  c2 10 00             ret 0x10
```
调用：`sub_004ACAC0`

### `0x31 ZoomIn` → 入口 `0x006DEEB8`（文件偏移 `0x2DEEB8`）

```
006DEEB8  a1 e0 71 88 00       mov eax, dword ptr [0x8871e0]
006DEEBD  8b 15 24 73 88 00    mov edx, dword ptr [0x887324]
006DEEC3  05 50 05 00 00       add eax, 0x550
006DEEC8  8b 08                mov ecx, dword ptr [eax]
006DEECA  89 8a c0 00 00 00    mov dword ptr [edx + 0xc0], ecx
006DEED0  8b 0d 24 73 88 00    mov ecx, dword ptr [0x887324]
006DEED6  8b 40 04             mov eax, dword ptr [eax + 4]
006DEED9  89 81 c4 00 00 00    mov dword ptr [ecx + 0xc4], eax
006DEEDF  8b 0d 70 f7 87 00    mov ecx, dword ptr [0x87f770]
```
调用：`InputManagerClass::DoSomething`, `VT+0xC`, `sub_006938C0`, `MapClass.RedrawSidebar`, `sub_004F4480`, `VT+0x7E11F0`

### `0x37 CreateRadarEvent` → 入口 `0x006DF1AD`（文件偏移 `0x2DF1AD`）

```
006DF1AD  8b 4e 44             mov ecx, dword ptr [esi + 0x44]
006DF1B0  8d 54 24 20          lea edx, [esp + 0x20]
006DF1B4  51                   push ecx
006DF1B5  8b 0d 30 b2 a8 00    mov ecx, dword ptr [0xa8b230]
006DF1BB  52                   push edx
006DF1BC  e8 ff ca fa ff       call 0x68bcc0
006DF1C1  8b 00                mov eax, dword ptr [eax]
006DF1C3  8b 8e 90 00 00 00    mov ecx, dword ptr [esi + 0x90]
006DF1C9  50                   push eax
```
调用：`ScenarioClass.GetWaypointCoords`, `sub_0065FA70`

### `0x3B ReduceTiberium` → 入口 `0x006DE313`（文件偏移 `0x2DE313`）

```
006DE313  8b 86 90 00 00 00    mov eax, dword ptr [esi + 0x90]
006DE319  8d 4c 24 20          lea ecx, [esp + 0x20]
006DE31D  50                   push eax
006DE31E  51                   push ecx
006DE31F  8b 0d 30 b2 a8 00    mov ecx, dword ptr [0xa8b230]
006DE325  e8 96 d9 fa ff       call 0x68bcc0
006DE32A  8b 10                mov edx, dword ptr [eax]
006DE32C  8d 44 24 10          lea eax, [esp + 0x10]
006DE330  50                   push eax
```
调用：`ScenarioClass.GetWaypointCoords`, `sub_0057B790`

### `0x3C SellBuilding` → 入口 `0x006DDEF5`（文件偏移 `0x2DDEF5`）

```
006DDEF5  a1 50 eb a8 00       mov eax, dword ptr [0xa8eb50]
006DDEFA  32 db                xor bl, bl
006DDEFC  33 ff                xor edi, edi
006DDEFE  3b c5                cmp eax, ebp
006DDF00  7e 54                jle 0x6ddf56
006DDF02  8b ac 24 5c 02 00 00 mov ebp, dword ptr [esp + 0x25c]
006DDF09  8b 0d 44 eb a8 00    mov ecx, dword ptr [0xa8eb44]
006DDF0F  8b 34 b9             mov esi, dword ptr [ecx + edi*4]
006DDF12  8a 86 90 00 00 00    mov al, byte ptr [esi + 0x90]
```
调用：`TagClass::ContainsTrigger`, `VT+0x1A0`

### `0x5E IonCannonStrike` → 入口 `0x006DD913`（文件偏移 `0x2DD913`）

```
006DD913  8b 56 44             mov edx, dword ptr [esi + 0x44]
006DD916  8b 0d 30 b2 a8 00    mov ecx, dword ptr [0xa8b230]
006DD91C  8d 44 24 20          lea eax, [esp + 0x20]
006DD920  52                   push edx
006DD921  50                   push eax
006DD922  e8 99 e3 fa ff       call 0x68bcc0
006DD927  8b 00                mov eax, dword ptr [eax]
006DD929  55                   push ebp
006DD92A  89 44 24 14          mov dword ptr [esp + 0x14], eax
```
调用：`ScenarioClass.GetWaypointCoords`, `sub_0041C230`, `MapClass.GetCellFloorHeight`, `CRT::_new`, `IonBlastClass::IonBlastClass`

### `0x62 PlaySoundEffectRandom` → 入口 `0x006DE7A5`（文件偏移 `0x2DE7A5`）

```
006DE7A5  68 80 5d 46 00       push 0x465d80
006DE7AA  6a 64                push 0x64
006DE7AC  8d 84 24 c8 00 00 00 lea eax, [esp + 0xc8]
006DE7B3  6a 04                push 4
006DE7B5  50                   push eax
006DE7B6  e8 35 81 d2 ff       call 0x4068f0
006DE7BB  33 ff                xor edi, edi
006DE7BD  33 ed                xor ebp, ebp
006DE7BF  8d 9c 24 c0 00 00 00 lea ebx, [esp + 0xc0]
```
调用：`sub_004068F0`, `ScenarioClass.IsDefinedWaypoint`, `ScenarioClass.GetWaypointCoords`, `Randomizer::RandomRanged`, `sub_00642740`, `VocClass.PlayIndexAtPos`

### `0x0F AllowWin(空实现)` → 入口 `0x006DFDDD`（文件偏移 `0x2DFDDD`）

```
006DFDDD  5f                   pop edi
006DFDDE  5e                   pop esi
006DFDDF  5d                   pop ebp
006DFDE0  5b                   pop ebx
006DFDE1  81 c4 40 02 00 00    add esp, 0x240
006DFDE7  c2 10 00             ret 0x10
```

### `0x5C ActivateFirestorm(空实现)` → 入口 `0x006DFDDB`（文件偏移 `0x2DFDDB`）

```
006DFDDB  b0 01                mov al, 1
006DFDDD  5f                   pop edi
006DFDDE  5e                   pop esi
006DFDDF  5d                   pop ebp
006DFDE0  5b                   pop ebx
006DFDE1  81 c4 40 02 00 00    add esp, 0x240
006DFDE7  c2 10 00             ret 0x10
```

### `0x91 JumpCameraHome` → 入口 `0x006DFDD6`（文件偏移 `0x2DFDD6`）

```
006DFDD6  e8 c5 17 05 00       call 0x7315a0
006DFDDB  b0 01                mov al, 1
006DFDDD  5f                   pop edi
006DFDDE  5e                   pop esi
006DFDDF  5d                   pop ebp
006DFDE0  5b                   pop ebx
006DFDE1  81 c4 40 02 00 00    add esp, 0x240
006DFDE7  c2 10 00             ret 0x10
```
调用：`sub_007315A0`

﻿---

## 11. 产物索引（`out/re_work/triggers/**`）

### 11.1 派发表 dump（逐项解算）

| 文件 | 内容 |
|---|---|
| `action_dispatch_table.tsv` | **Action 表 145 项**：kind / 目标 VA / 文件偏移 / 区间 / 指令数 / 调用 / this 读写 / 出口 jmp |
| `action_blocks_full.txt` | 145 项内联体**全文反汇编**（VA + 原始字节 + 助记符） |
| `action_blocks_summary.txt` | 同上的压缩摘要（逐项 3 行） |
| `event_dispatch_jumptable.txt` | 1 级 12 项目标体反汇编 + 选择表 |
| `event_selector_table.txt` | kind(0x0D..0x3D) → 选择槽 → 目标 VA 对照 |
| `event_table.tsv` | **Event 表 62 项**：四级入口 + GetStateA/B/GetFlags 解析结果 |
| `event_aux_tables.txt` | 2/3/4 级选择表逐 kind 展开 + 每个目标体前 7 条指令 |
| `event_hasoccured_full.txt` | `HasOccured`（0x71E940..0x71F163）全文反汇编 |
| `team_script_dispatch_table.tsv` | **队伍脚本表 65 项**（`TeamClass::AI`，含锚点 49） |
| `team_script_blocks_full.txt` | 65 项全文反汇编 |
| `all_jump_tables.json` | 全 `.text` 387 张 `jmp [reg*4+disp]` 跳表清单（VA/表址/上界），用于确认"位处触发器区的表只有这 3 张" |

### 11.2 语义/参数解算

| 文件 | 内容 |
|---|---|
| `action_rows.txt` / `action_rows.json` | 145 项的 mode/flags/读字段/调用（供二次加工） |
| `getmode_table.txt` | `GetMode` 144 项 → mode 值 |
| `getflags_table.txt` | `GetFlags` 98 项 → flags 值 |
| `mode_flags.json` | 上述两表的机器可读形式 |
| `prepare_save_action.txt` | `TActionClass::PrepareSaveToINI 0x6DD300` 全文（mode 消费点证据） |
| `name_tables.txt` | `TEventClass::PrepareSaveToINI` / `TActionClass::LoadFromINI` 全文（证明本体无名字表） |
| `action_slave_match.txt` / `slave_final.tsv` / `slave_map.json` | 内联体 ↔ `ACTION_FUNC` 从属函数调用集匹配（64 项双证据） |
| `xrefs.txt` | `Execute`/`HasOccured`/`FireActions`/`RegisterEvent`/`FillEvent_*` 的调用点归属 |
| `yrpp_syms.json` | 由 `YRpp/*.h` 解析出的 1078 条 地址→符号 映射 |

### 11.3 断言与脚本

| 文件 | 内容 |
|---|---|
| `claims.txt` | **77 条**字节断言（可直接 `python tools/audit_bytes.py out/re_work/triggers/claims.txt` 复算） |
| `audit.json` | 审计明细（含 capstone 上下文） |
| `pe.py` | 本次使用的 PE/反汇编最小工具（VA↔文件偏移、section 表） |
| `dump_triggers.py` / `gen_event_table.py` / `mk_action_md2.py` / `assemble.py` | 复现脚本（一键重生成全部 dump 与本文表格） |
| `dups.py` / `lists.py` | 表长/重复目标对账、副作用分类清单 |

---

## 12. 验收自证

| 验收项 | 结果 |
|---|---|
| 两张表条目数 = 派发跳表实际条目数 | Action **145/145**（`cmp edx,0x90` + 145 dword + 表尾 `mov al,1;ret 0x10` 三重自证）；Event **62/62**（`0x00..0x3D` 全覆盖；其中 12 kind 挂 1 级表、其余走 2/3/4 级与扁平链，逐 kind 已在 `event_table.tsv` 落位）；附：队伍脚本表 **65/65** |
| ≥10 个动作有指令级入口证据 | **145/145** 有派发入口 VA+文件偏移（`action_dispatch_table.tsv`），**26** 个在附录 C 给出字节级反汇编，**64** 个有内联体↔从属函数双证据 |
| 与 `net_sync_checksum.md` §9 交叉引用一致 | 一致（§8.1 C1–C3）；`NetworkEvent::Kind` 与 `TriggerEvent` 的数值空间冲突单列勘误 E-2；锚点归属单列勘误 E-1 |
| 字节断言复算 | `claims.txt` **77 条全部 OK**（§7）；其中含 2 条布局类断言（`Size()=0x94`、`GetArrayIndex=[ecx+0x24]`） |
