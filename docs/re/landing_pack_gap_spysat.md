# M-10 落地包：裂缝保护 NOP×3 + SpySat 门控 + G-07 Remove 还原

> **任务**：M-10 · 派工 v14 · 2026-09-26
> **交付**：本文件（`docs/re/landing_pack_gap_spysat.md`）+ 取证 `out/re_work/landing_gap/**`
> **执行方**：ZCode（照表落地 + 真机验证，不做静态推理）
> **写作用域**：本文件 + `out/re_work/landing_gap/**`；**只读** `ra2render/**`、台账 `REVERSE_ENGINEERING_AND_PATCHES.md`
> **目标二进制**：`gamemd.exe`（尤里的复仇 1.001），ImageBase `0x00400000`，`.text` raw offset = RVA
>
> **证据图例**
> - **[实证]** = 已对 `ra2youli/gamemd.exe` 做字节级核验（脚本 `out/re_work/landing_gap/verify_m10_bytes.py`，输出 `verify_m10_bytes_out.txt`），或源码/反汇编已有明确引用
> - **[待实测]** = 规格闭合，但真机行为/回滚尚未跑通，ZCode 验收时必须补证
>
> **基础文档（只读）**
> | 文档 | 用途 |
> |---|---|
> | `docs/re/superweapon_re.md` §5.2/§5.3/§6 | 三写点字节、SpySat 关键字节、联机裁决 |
> | `docs/re/gap_generator_spysat_deep_dive.md` §3.3/§4.3 | 清零根因、6B NOP 方案、CellClass 布局 |
> | `docs/re/visibility_gap_spysat.md` §2.4/§3.3/§5 | Gap×SpySat 反制、S1 引擎侧对应、Hook 红线 |
> | `docs/re/INSTALLED_HOOKS_AUDIT.md` G-07/A8 | S1 无 Remove 还原缺口 |
> | `docs/re/hook_gate_gap_table.md` §1.6 S1 / §5 G-07 | S1 门控面、G-07 验收判据 |
> | `docs/re/net_sync_checksum.md` §4.2 / §5 | 同步契约（序列化范围 / 红线表） |
>
> **Lead 已复核字节**（本包不再改字节，只做落地规格化）：
> 1. `0x568273 = 89 99 34 01 00 00`；`0x577EC5 = 89 B8 34 01 00 00`；`0x577B60 = 89 98 34 01 00 00`（语义：清 `CellClass+0x134 GapsCoveringThisCell`）
> 2. `0x508F88 = 80 B8 A5 16 00 00 00 74 65`（`cmp byte [eax+0x16A5], 0 / je`，`Type+0x16A5` = `SpySat`）
> 3. G-07：S1 TYPE 补丁 Remove 还原（存原 `BuildingType+0x16A5/+0x16F0` 与 `SuperWeaponType+0xB0/+0xF8`，在 `RemoveVTableHooks` 还原）

---

## 0. 三项总览

| 项 | 名称 | 补丁形态 | 地址 | 开关键 | 默认 | 同步契约 |
|---|---|---|---|---|---|---|
| **P-1** | 裂缝保护 NOP×3 | 3 × 6B 等长 NOP | `0x568273` / `0x577EC5` / `0x577B60` | `[FogOfWar] EnableGapProtection` | **1** | **条件**（Cell 进档；须全端同补丁） |
| **P-2** | SpySat 门控 | 2B 等长 `je→jmp` | `0x508F8F`（窗口 `0x508F88` 共 9B） | `[FogOfWar] EnableSpySatGate` | **1** | **条件**（阻止 RevealArea3 写 Cell/House；须全端同 DLL） |
| **P-3** | G-07 S1 TYPE Remove 还原 | 数据备份 + 卸载还原（无 .text 补丁） | TYPE 字段 4 处（见 §3） | 随 `[FogOfWar] EnableSpySatRadarSweep` | **1**（既有键） | **不进**（TYPE 不进档；但 S1 写出的行为仍是「条件」） |

> **与 S1 的关系**（避免 ZCode 重复/打架）：
> - **P-2（代码门）** 只做「阻止 `UpdateSpySat` 走 `RevealArea3` 全图开」——**不改 TYPE**。
> - **S1（`PatchSpySatBuildingTypes`）** 做完整「间谍卫星 → 人族雷达」改造：关 `Type+0x16A5` + 绑 `+0x16F0` + 改 `SW+0xB0/+0xF8`。
> - 两者 **可并存**：双开时效果一致（都不全图开），P-2 冗余但无害；只开 P-2 可拿到「干净回滚、不动 TYPE」的最小面；只开 S1 则必须依赖 **P-3 的还原** 才能进程内回滚。
> - **互斥提醒**（`superweapon_re.md` §5.4）：裂缝保护选 **NOP 路线** 后，**禁止** 再从 SuperClass 侧写 `Cell+0x134`（不要叠「Super 覆写」方案）。

---

## 1. P-1 裂缝保护：三处 6 字节 NOP

### 1.1 语义与根因（为什么必须打）

原版三处把 `CellClass+0x134`（`GapsCoveringThisCell`，敌方裂缝引用计数）**暴力清零**：

| VA | 指令 | 所在函数 | 后果 |
|---|---|---|---|
| `0x00568273` | `mov [ecx+0x134], ebx`（`ebx=0`） | `MapClass::RevealArea2` 循环内（PsychicReveal 局部开图） | 扫描区裂缝计数归零 |
| `0x00577EC5` | `mov [eax+0x134], edi`（`edi=0`） | `MapClass::RevealArea3`（SpySat 全图开） | 全图裂缝计数归零 |
| `0x00577B60` | `mov [eax+0x134], ebx`（`ebx=0`） | `MapClass::Reshroud`（SpySat 离线重遮） | 全图裂缝计数归零 |

计数归零后：裂缝建筑自身 `GeneratingGap==true` **不会** 再调 `CreateGap`；`CellClass::ReshroudCell`（`0x487690`）把 `ShroudCounter` 截断为 `GapsCoveringThisCell`，导致该格 **永远无法重新变黑**——裂缝被「物理阉割」。详见 `gap_generator_spysat_deep_dive.md` §3.3。

**修复**：6 字节整指令 NOP，**只删清零副作用**，保留 `RevealArea2/3/Reshroud` 的其余写（`CopyFlags`、`ShroudCounter` 等）不动。

### 1.2 字节级规格

| 项 | gap1 | gap2 | gap3 |
|---|---|---|---|
| **VA** | `0x00568273` | `0x00577EC5` | `0x00577B60` |
| **文件偏移**（VA−`0x400000`） | `0x168273` | `0x177EC5` | `0x177B60` |
| **原字节** | `89 99 34 01 00 00` | `89 B8 34 01 00 00` | `89 98 34 01 00 00` |
| **原指令** | `mov [ecx+0x134], ebx` | `mov [eax+0x134], edi` | `mov [eax+0x134], ebx` |
| **新字节** | `90 90 90 90 90 90` | `90 90 90 90 90 90` | `90 90 90 90 90 90` |
| **新指令** | NOP ×6 | NOP ×6 | NOP ×6 |
| **核验** | **[实证]** | **[实证]** | **[实证]** |

> 等长 6B，**不改控制流**、不引入 trampoline、不碰 `.detour` 节（遵守 M-8 同款节约束）。

### 1.3 开关键 / 默认值 / 安装形态

| 字段 | 值 |
|---|---|
| **ini 键** | `[FogOfWar] EnableGapProtection` |
| **API 默认** | `1`（`GetPrivateProfileIntA("FogOfWar", "EnableGapProtection", 1, ...)`） |
| **ini 现值（建议写入）** | `1` |
| **开关形态** | **安装门控**（Install Gate）：`=0` 时 **完全不写补丁字节**，零残留（推荐，对齐 telemetry 规格「安装门控」定义） |
| **备选形态** | 运行时短路不可用——NOP 本身无 Hook 体，**不能** 做 runtime short-circuit；只能安装门控 |
| **安装函数** | `InstallGapProtectionPatches()`（新增） |
| **卸载函数** | `RemoveGapProtectionPatches()`（新增） |
| **挂接点** | `InstallVTableHooks()` 尾部调 Install；`RemoveVTableHooks()` 调 Remove（与 13 虚表还原同级） |
| **字节备份** | `static uint8_t s_origGapProtectBytes[3][6]` + `static bool s_gapProtectInstalled` |
| **遥测** | 建议 `gapProtectionPatchesInstalled`（0..3，装了几处）；安装/卸载各打一条 LogMessage |

### 1.4 回滚

| 层级 | 操作 | 效果 |
|---|---|---|
| **软关** | `EnableGapProtection=0` + **重启游戏** | 新进程不写补丁，回到原版（会重新出现裂缝失效 bug） |
| **硬卸（进程内）** | `RemoveGapProtectionPatches()`（`DLL_PROCESS_DETACH` 自动） | memcpy 还原 `s_origGapProtectBytes[3][6]` → 三处 `mov` 复活 |
| **彻底** | 移除/改名 `ra2render.dll` | gamemd.exe 从未写盘（红线保持） |

**回滚判据**：出现「开图后裂缝区域仍显示遮挡/逻辑异常」且怀疑 NOP 影响 → `EnableGapProtection=0` 复测；仍异常则整体 DLL 回退。

### 1.5 验收方法

| # | 判据 | 证据形态 | 状态 |
|---|---|---|---|
| A1.1 | 安装前读三处各 6B == 原字节 | 脚本 dump | **[实证]**（`verify_m10_bytes.py`） |
| A1.2 | `EnableGapProtection=1` 启动后读三处各 6B == `90×6` | 脚本/调试器 dump | **[待实测]** |
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0
| A1.3 | `EnableGapProtection=0`（或卸载后）三处恢复原字节 | 同上 | **[待实测]** |
| A1.4 | 行为：裂缝产生器覆盖区释放 PsychicReveal / SpySat 开图后，扫描退去该格 **恢复黑雾**（`GapsCoveringThisCell` 未被清零） | 真机对局 + 日志/截图 | **[待实测]** |
| A1.5 | 不崩溃：窗口内 `except.txt` 无新增（EVIDENCE_STANDARD v3 一票否决） | 验收包 | **[待实测]** |

### 1.6 是否进同步契约（对照 `net_sync_checksum.md`）

| 问题 | 答案 |
|---|---|
| **直接进帧 CRC `0x64DAB0`？** | **否**。NOP 只阻止写 `Cell+0x134`，不新增 RNG/CRC 消费 |
| **进 CalculateChecksum / 存档？** | **间接是**：`Map/Cell`（含 shroud 数据）在 §4.2 序列化范围内；`GapsCoveringThisCell` 是 Cell 字段，其演化被本补丁改变 |
| **判定** | **条件安全**（`superweapon_re.md` §6.4 同判）：**必须全端字节级同一 DLL**。混端（一端 NOP、一端原版）→ 裂缝可见性分叉 → 寻敌/AI 分叉 → desync |
| **红线对照** | 不碰 `IsShrouded` / `RevealArea*` 的**其余**语义、不碰 CreateGap/DestroyGap、不碰 RNG/命令队列。只删一处已确认的 bug 写点 → 不触碰 net_sync §5.1「禁改」域本体 |
| **联机策略** | 联机/混联：全端同构建 + 同 `EnableGapProtection`；建议联机固定 =1 并纳入构建指纹 |

---

## 2. P-2 SpySat 门控（`0x508F88` 代码级）

### 2.1 语义

`HouseClass::UpdateSpySat`（`0x508F60`）遍历建筑时的核心门：

```
0x00508F88  80 B8 A5 16 00 00 00    cmp byte ptr [eax+0x16A5], 0   ; Type->SpySat
0x00508F8F  74 65                   je  0x00508FF6                 ; 非 SpySat → 跳过
```

后续：SpySat 建筑在线且有电 → `call RevealArea3(0x577D90)` 全图开 + `House+0x577A SpySatActive=1`。`RevealArea3` 会清全图 `GapsCovering` 并置 `CopyFlags|=0x18`——这正是原版裂缝失效的第二根因（第一根因是 PsychicReveal/RevealArea2）。

**门控目标**：在代码层 **强制跳过** SpySat 激活分支（不全图开），且 **可开关、可还原、不动 TYPE**。

### 2.2 字节级规格

| 项 | 值 |
|---|---|
| **核验窗口** | `0x00508F88` 共 **9 字节**（cmp 7B + jcc 2B） |
| **原字节（9B）** | `80 B8 A5 16 00 00 00 74 65` **[实证]** |
| **补丁点** | `0x00508F8F`（jcc 首字节） |
| **原字节（2B）** | `74 65`（`je +0x65` → `0x00508FF6`）**[实证]** |
| **新字节（2B）** | `EB 65`（`jmp +0x65` → **同一落点** `0x00508FF6`） |
| **效果** | 无条件走「非 SpySat」分支：**永不** 调 `RevealArea3`，**永不** 置 `SpySatActive=1` |
| **为何用 `EB` 不用 NOP** | 落点相同、等长、零副作用；`cmp` 保留无害（仅置 flags，后续无条件跳转不吃 flags） |
| **备选（不推荐）** | 把 9B 全改成 `80 B8 A5 16 00 00 00 EB 65` —— 与 2B 方案逐位等价，只是备份面更大 |

> `je` 目标验算：`0x508F8F + 2 + 0x65 = 0x508FF6` **[实证]**（与 `gap_generator_spysat_deep_dive.md` §3.4 的 `je 0x508ff6` 一致）。

### 2.3 开关键 / 默认值 / 安装形态

| 字段 | 值 |
|---|---|
| **ini 键** | `[FogOfWar] EnableSpySatGate` |
| **API 默认** | `1` |
| **ini 现值（建议写入）** | `1` |
| **开关形态** | **安装门控**：`=0` 时完全不写补丁字节 |
| **安装函数** | `InstallSpySatGatePatch()`（新增） |
| **卸载函数** | `RemoveSpySatGatePatch()`（新增） |
| **挂接点** | `InstallVTableHooks()` / `RemoveVTableHooks()`（与 P-1 同级） |
| **字节备份** | `static uint8_t s_origSpySatGateBytes[2]` + `static bool s_spySatGateInstalled` |
| **遥测** | 建议 `spysatGatePatchesInstalled`（0/1）；安装/卸载 LogMessage |

> 【W3 勘误 · FREEZE_CANDIDATE §7 C11 / Lead DC-06】[W3-Lead临时裁决] 改前：API 默认 1 / ini 现值（建议写入）1；改后：默认值订正为 0（安全侧，键缺失即原版）；MP 语义保持总表强一致（不加 forced-off-mp）；依据：Lead 临时裁决 DC-06；分级：[推演]

### 2.4 与 S1 / P-3 的组合矩阵

| EnableSpySatGate (P-2) | EnableSpySatRadarSweep (S1) | 行为 | TYPE 是否被改 | 进程内可回滚 |
|---|---|---|---|---|
| 1 | 1 | 不全图开；且 SpySat 建筑被改造成 PsychicReveal 雷达 | 是（需 P-3） | P-2 可；TYPE 靠 P-3 |
| **1** | **0** | **不全图开；TYPE 原样** | **否** | **是（干净）** |
| 0 | 1 | 不全图开（靠 TYPE+0x16A5=false）；改造雷达 | 是（需 P-3） | 靠 P-3 |
| 0 | 0 | **原版 SpySat 全图开**（裂缝失效风险，除非 P-1 已打） | 否 | — |

**推荐默认组合**：P-1=1 + P-2=1 + S1=1（完整「星际雷达」体验）；若要最小侵入/最干净回滚：P-1=1 + P-2=1 + S1=0。

### 2.5 回滚

| 层级 | 操作 | 效果 |
|---|---|---|
| **软关** | `EnableSpySatGate=0` + 重启游戏 | 不写 `EB`，原版 `je` 恢复 |
| **硬卸（进程内）** | `RemoveSpySatGatePatch()` | memcpy 还原 `74 65` |
| **彻底** | 移除 DLL | — |

**回滚判据**：SpySat 建筑上线后 **仍不** 全图开（预期：门控生效）；若业务需要原版全图开 → 关键 =0 并确认 TYPE 未被 S1 改写（或已 P-3 还原）。

### 2.6 验收方法

| # | 判据 | 证据形态 | 状态 |
|---|---|---|---|
| A2.1 | 安装前 `0x508F88..8F90` == `80 B8 A5 16 00 00 00 74 65` | 脚本 dump | **[实证]** |
| A2.2 | 门控开：`0x508F8F..8F90` == `EB 65` | 进程内读内存 | **[待实测]** |
| A2.3 | 门控关/卸载：恢复 `74 65` | 同上 | **[待实测]** |
| A2.4 | 行为：建造 SpySat 建筑并供电 → **不** 触发 `RevealArea3` 全图开（小地图不整图亮）；`House+0x577A` 不置 1 | 真机 + 日志 | **[待实测]** |
| A2.5 | 不崩溃（EVIDENCE_STANDARD v3） | 验收包 | **[待实测]** |

### 2.7 是否进同步契约（对照 net_sync）

| 问题 | 答案 |
|---|---|
| **直接进帧 CRC？** | **否**。补丁本身不写任何状态，只改一处分支 |
| **进 CalculateChecksum / 存档？** | **间接是**：阻止 `RevealArea3` 对全图 `Cell+0x12C/+0x130/+0x134` 的写入（Cell 进档）；同时阻止 `House+0x577A SpySatActive=1`（House 进 `Save_Sides`） |
| **判定** | **条件安全**：全端同 DLL 才确定。混端（一端门控、一端原版）→ 一端全图亮一端不亮 → 可见性/寻敌分叉 |
| **红线对照** | 不改 `UpdateSpySat` 其余逻辑、不改 `RevealArea3/Reshroud` 本体、不碰 RNG。只是「少走一个分支」 |
| **联机策略** | 与 P-1 相同：全端同构建 + 同 ini；建议联机固定 =1 并纳入构建指纹 |

---

## 3. P-3 G-07：S1 TYPE 补丁的 Remove 还原

### 3.1 缺口回顾

`PatchSpySatBuildingTypes`（`blitter_hooks.cpp:596-655`）在 `EnableSpySatRadarSweep=1` 时 **只写不存**：

| 写点 | 目标 | 写入值 | 现状 |
|---|---|---|---|
| `:614` | `SuperWeaponTypeClass+0xB0`（`RechargeTime`） | `g_radarSweepCooldownFrames`（默认 600） | **无备份** |
| `:617` | `SuperWeaponTypeClass+0xF8`（`Range`） | `(float)g_radarSweepRadiusCells`（默认 16.0） | **无备份** |
| `:638` | `BuildingTypeClass+0x16A5`（`SpySat`） | `false` | **无备份** |
| `:644` | `BuildingTypeClass+0x16F0`（超武绑定槽） | `psychicRevealIndex`（仅当原值 `-1`） | **无备份** |

`RemoveVTableHooks` **不涉及** 这些 TYPE 字段（`INSTALLED_HOOKS_AUDIT.md` A8 / `hook_gate_gap_table.md` G-07）。后果：进程内改 TYPE 后不可回滚，验收 A-1 的「关闭全部键基线」会被残留污染。

### 3.2 还原规格（给 ZCode 的代码级要求）

**原则**：只存「第一次写之前的原值」；重复打补丁（跨战局重载 `s_spySatPatched` 复位后 `:740-741` 会再进）**不得覆盖备份**；还原用首次备份。

#### 3.2.1 备份结构（建议）

```cpp
// —— G-07: S1 TYPE patch backup (process-lifetime) ——
struct SpySwBackup {
    void* pSW;              // SuperWeaponTypeClass*
    int   origRechargeTime; // +0xB0
    float origRange;        // +0xF8
    bool  saved;
};
struct SpyBldBackup {
    void* pBld;             // BuildingTypeClass*
    bool  origSpySat;       // +0x16A5
    int   origSWIndex;      // +0x16F0
    bool  saved;
};
static SpySwBackup            s_spySwBackup   = {};           // 至多 1 个 PsychicReveal SW
static SpyBldBackup           s_spyBldBackups[64] = {};       // SpySat 建筑类型（通常 1 个）
static int                    s_spyBldBackupCount = 0;
static bool                   s_spyTypeBackupsTaken = false;
```

#### 3.2.2 保存时机（插进 `PatchSpySatBuildingTypes`）

| 位置 | 动作 |
|---|---|
| SW 循环命中 `PsychicReveal` 后、**写 `+0xB0/+0xF8` 之前** | `if (!s_spySwBackup.saved) { s_spySwBackup.pSW=pSW; s_spySwBackup.origRechargeTime=*(int*)(pSW+0xB0); s_spySwBackup.origRange=*(float*)(pSW+0xF8); s_spySwBackup.saved=true; }` |
| 建筑循环 `hasSpySat==true` 后、**写 `+0x16A5/+0x16F0` 之前** | `if (s_spyBldBackupCount < 64) { 记录 pBld / 原 +0x16A5 / 原 +0x16F0; s_spyBldBackupCount++; }`（若该 `pBld` 已在备份表中则跳过） |
| 函数末尾 `s_spySatPatched = true` 时 | `s_spyTypeBackupsTaken = true`（可选，作守卫） |

> **注意**：`+0x16F0` 只在原值 `-1` 时才写 `:643-644`；备份仍应记录原值（可能是 `-1` 或其它索引），还原时 **无条件** 写回原值。

#### 3.2.3 还原时机（`RemoveVTableHooks` 尾部，13 槽虚表还原之后）

新增 `RestoreSpySatBuildingTypes()`：

```
if (s_spySwBackup.saved):
    *(int*)(pSW+0xB0)  = origRechargeTime
    *(float*)(pSW+0xF8)= origRange
    s_spySwBackup.saved = false
for each s_spyBldBackups[i] (i < s_spyBldBackupCount):
    *(bool*)(pBld+0x16A5) = origSpySat
    *(int*)(pBld+0x16F0)  = origSWIndex
s_spyBldBackupCount = 0
s_spyTypeBackupsTaken = false
s_spySatPatched = false
LogMessage("[ra2render-fog] G-07 SpySat TYPE restored")
```

`RemoveVTableHooks()` 调用顺序建议：`RemoveGapProtectionPatches()` → `RemoveSpySatGatePatch()` → 既有 3×Remove* → 13 槽虚表还原 → **`RestoreSpySatBuildingTypes()`**。

#### 3.2.4 字段值域（还原正确性自检）

| 字段 | 类型 | 原版典型值 | S1 写入后 | 还原目标 |
|---|---|---|---|---|
| `BuildingType+0x16A5` | `bool` | `true`（SpySat 建筑） | `false` | **`true`** |
| `BuildingType+0x16F0` | `int` | `-1`（无绑定） | `psychicRevealIndex`（≥0） | **`-1`** |
| `SuperWeaponType+0xB0` | `int`（帧） | `0x1194` = **4500**（ctor 实证） | `600`（默认键） | **4500**（或 ini 覆盖前的原值） |
| `SuperWeaponType+0xF8` | `float` | **`0.0`**（ctor 实证） | `16.0`（默认键） | **`0.0`**（或原值） |

> `+0xB0` 原值不一定是 4500：rulesmd.ini 可覆盖。**必须以写前实读为准**，上表典型值仅作自检参考。

### 3.3 开关键 / 默认值

| 字段 | 值 |
|---|---|
| **ini 键** | **无新增键**（跟随既有 `EnableSpySatRadarSweep`） |
| **相关键** | `[FogOfWar] EnableSpySatRadarSweep` API=1；`RadarSweepCooldownFrames` API=600≥60；`RadarSweepRadiusCells` API=16 钳 4..64 |
| **说明** | G-07 是 **还原能力**，不是行为开关。S1 仍由 `EnableSpySatRadarSweep` 门控；`=0` 时本就不写 TYPE，也无需还原 |
| **安装形态** | 数据备份随 `PatchSpySatBuildingTypes` 首次执行；还原随 `RemoveVTableHooks` |
| **遥测** | 建议 `spySatTypeRestored`（0/1 或还原字段计数）；还原时 LogMessage |

### 3.4 回滚

| 层级 | 操作 | 效果 |
|---|---|---|
| **软关** | `EnableSpySatRadarSweep=0` + **重启游戏**（新进程 TYPE 由 rules 重新解析，天然干净） | 注意：**同进程** 改 ini 不会自动还原已写的 TYPE——这正是 G-07 要补的 |
| **硬卸（进程内）** | `RemoveVTableHooks()` → `RestoreSpySatBuildingTypes()` | 四字段写回首次备份 |
| **彻底** | 移除 DLL / 重启 | — |

**回滚判据**：同进程开→关（或 DLL 卸载）后，SpySat 建筑恢复全图开行为、PsychicReveal CD/半径回 rules 值 → G-07 生效；若仍残留改造效果 → 备份/还原未接线，按 A3.x 复测。

### 3.5 验收方法

| # | 判据 | 证据形态 | 状态 |
|---|---|---|---|
| A3.1 | 首次 `PatchSpySatBuildingTypes` 前，日志打印四字段原值 | `ra2render.log` | **[待实测]** |
| A3.2 | 打补丁后：`+0x16A5==false`、`+0x16F0==index`、`+0xB0==600`、`+0xF8==16.0`（默认键下） | 调试器/日志 | **[待实测]** |
| A3.3 | `RemoveVTableHooks` 后（或同进程模拟卸载）：四字段 == A3.1 记录的原值 | 同上 | **[待实测]** |
| A3.4 | 跨战局重载再打补丁：备份仍是 **首次** 原值（不被 600/16.0 污染） | 两次日志对比 | **[待实测]** |
| A3.5 | 行为回滚：还原后 SpySat 建筑重新触发全图开（若 P-2 关）或至少 TYPE 语义回原版 | 真机 | **[待实测]** |
| A3.6 | 不崩溃（EVIDENCE_STANDARD v3） | 验收包 | **[待实测]** |

### 3.6 是否进同步契约（对照 net_sync）

| 问题 | 答案 |
|---|---|
| **TYPE 数据进档？** | **否**。`BuildingTypeClass` / `SuperWeaponTypeClass` 是 rules 解析出的类型单例，不进 §4.2 序列化范围 |
| **但 S1 的行为后果？** | **是（条件）**：改 `+0xB0` CD = 改充能完成帧 → 改 Launch 发生帧；改 `+0x16A5/+0x16F0` = 改超武授予/全图开语义 → 间接进 House 超武状态机与 Cell 可见性 |
| **G-07 还原本体判定** | **不进同步契约**（还原只在 `RemoveVTableHooks`/进程退出时发生，不参与对局内状态演化）。它是 **工程回滚能力**，不改变 S1 的「条件」判定 |
| **联机策略** | 与既有 S1 一致：全端同 DLL + 同 ini；联机建议 `EnableSpySatRadarSweep=0` 或全端强制同值（`mp_autodowngrade` W3 旁路仍待落地，不在本包范围） |

---

## 4. 同步契约对照总表（net_sync）

> 对照 `net_sync_checksum.md` §4.2（序列化范围）/ §5（红线表）。图例：**安全** = 不进同步契约；**条件** = 全端同构建+同 ini 才确定；**禁止** = 必分叉。

| 项 | 写什么 | 帧 CRC `0x64DAB0` | CalculateChecksum / 存档 | RNG | 判定 | 依据 |
|---|---|---|---|---|---|---|
| **P-1** NOP×3 | **阻止** 写 `Cell+0x134` | 否 | Cell（Map/Cell 块）演化被改 | 否 | **条件** | superweapon_re §6.4；net_sync §4.2 Map/Cell |
| **P-2** SpySat 门 | **阻止** `RevealArea3` 写全图 Cell + `House+0x577A` | 否 | Cell + House（`Save_Sides`）演化被改 | 否 | **条件** | visibility_gap_spysat §3.3；net_sync §4.2 |
| **P-3** G-07 还原 | 进程退出时回写 TYPE 4 字段 | 否 | TYPE **不进档** | 否 | **安全**（还原本体）；S1 写出仍 **条件** | INSTALLED_HOOKS S1；net_sync §4.2（TYPE 不在列） |

**共同前提（三项共享）**：
1. **全端字节级同一 DLL**（构建指纹/哈希一致）；
2. **全端同一 ini**（尤其 `EnableGapProtection` / `EnableSpySatGate` / `EnableSpySatRadarSweep`）；
3. 不得叠加「SuperClass 覆写 `Cell+0x134`」方案（与 P-1 互斥，`superweapon_re` §5.4）；
4. 不改 `IsShrouded` / `CreateGap` / `DestroyGap` / Launch 跳表 / RNG 消费序（net_sync §5.1 红线）。

---

## 5. 建议 ini 增量（供 ZCode 合并进 `ra2render.ini`，两份同步）

```ini
[FogOfWar]
; ---- M-10 gap / spysat landing ----
; P-1: 3x6B NOP 保护 GapsCoveringThisCell（裂缝不再被扫图清零）
EnableGapProtection=1
; P-2: 0x508F8F je->jmp，SpySat 不再全图开（不动 TYPE）
EnableSpySatGate=1
; 既有 S1（改 TYPE 为 PsychicReveal 雷达；G-07 提供 Remove 还原）
EnableSpySatRadarSweep=1
RadarSweepCooldownFrames=600
RadarSweepRadiusCells=16

; v1.6.0 雷达小地图灰化（G-01 / R-01，P0）——★ **必须显式置 0**：API 默认 1、ini 现值 1，
; **键被删/安装包漏配即静默全开**（小地图状态机单端异步风险）
EnableMinimapFog=0
```

> **【F-11 订正（落地侧）· 2026-09-26 · task-14】** 改前：§5 建议 ini **只列 M-10 三键**（`EnableGapProtection` / `EnableSpySatGate` / `EnableSpySatRadarSweep` + 两个 Radar 参数），`EnableMinimapFog` **0 命中**；改后：补入 **`EnableMinimapFog=0`** 与 G-01 口径注。依据：**证据更新** —— `ra2youli/ra2render.ini` 与 `ra2render/ra2render.ini` 现值均已是 `EnableMinimapFog=1`（`:45`，`:44` 为注释，两份字节一致）`[实证]`，而源码 API 默认仍为 `1`（`blitter_hooks.cpp:103`）`[实证]` → 缺口应重述为「**键缺失即静默全开**」而非「API 与 ini 不一致」；终局裁定 = API 默认强制 `0`（`mp_release_safety_checklist.md:21` R-01 / `ARCHITECTURE_ATLAS.md:1536` G-01）。**权威正文勘误落点**为 `hook_gate_gap_table.md` §8 附录 E-1（`L263,276-277`，task-13 已登）；本行仅作为**执行链落地**（执行总表 §3.1 已同步补键，见 `pending_execution_master_table.md` §3.1）。

> 若走「最小侵入」组合：`EnableSpySatRadarSweep=0`，只留 `EnableGapProtection=1` + `EnableSpySatGate=1`。

---

## 6. 给 ZCode 的执行表

> **用法**：按步骤顺序执行；每步完成后勾「验收」。标注 **[实证]** = 本包已字节核验，直接照抄；**[待实测]** = 落地后必须真机取证。  
> 「地址」为 VA（ImageBase `0x400000`）。写内存一律 `VirtualProtect` → 备份 → 写 → 恢复保护。

| 步骤 | 动作 | 地址 | 原字节 / 原值 | 新字节 / 新值 | 开关 | 回滚 | 验收 | 标注 |
|---|---|---|---|---|---|---|---|---|
| **1** | P-1 备份+NOP gap1 | `0x00568273` | `89 99 34 01 00 00` | `90 90 90 90 90 90` | `EnableGapProtection=1` 时才写；`=0` 跳过本步 | `RemoveGapProtectionPatches` 写回 `89 99 34 01 00 00` | 装后 dump == `90×6`；卸后 == 原字节 | 字节 **[实证]** / 装卸 **[待实测]** |
| **2** | P-1 备份+NOP gap2 | `0x00577EC5` | `89 B8 34 01 00 00` | `90 90 90 90 90 90` | 同上 | 写回 `89 B8 34 01 00 00` | 同上 | 字节 **[实证]** / 装卸 **[待实测]** |
| **3** | P-1 备份+NOP gap3 | `0x00577B60` | `89 98 34 01 00 00` | `90 90 90 90 90 90` | 同上 | 写回 `89 98 34 01 00 00` | 同上 | 字节 **[实证]** / 装卸 **[待实测]** |
| **4** | P-2 备份+门控 SpySat jcc | `0x00508F8F`（上下文 `0x00508F88` 起 9B：`80 B8 A5 16 00 00 00 74 65`） | `74 65` | `EB 65` | `EnableSpySatGate=1` 时才写；`=0` 跳过 | `RemoveSpySatGatePatch` 写回 `74 65` | 装后 `0x508F8F==EB`；SpySat 不再全图开；卸后 `==74` | 字节 **[实证]** / 装卸 **[待实测]** |
| **5** | P-3 备份 TYPE（SW） | `SuperWeaponTypeClass+0xB0` / `+0xF8` | 实读原值（典型 `0x1194` / `0.0`） | S1 写入：`600` / `16.0`（受 `RadarSweep*` 键） | 随 `EnableSpySatRadarSweep=1` | `RestoreSpySatBuildingTypes` 写回实读原值 | 日志含写前原值；还原后字段==原值 | 规格 **[实证]** / 行为 **[待实测]** |
| **6** | P-3 备份 TYPE（Bld） | `BuildingTypeClass+0x16A5` / `+0x16F0` | 实读原值（典型 `true` / `-1`） | S1 写入：`false` / `psychicRevealIndex` | 同上 | 同上，写回实读原值 | 同上 | 规格 **[实证]** / 行为 **[待实测]** |
| **7** | 挂接 Install | `InstallVTableHooks()` 尾部 | — | 调 `InstallGapProtectionPatches()` + `InstallSpySatGatePatch()`（先于/并列既有 S1 懒加载） | 各自 ini 键 | — | 启动日志出现安装条目 | **[待实测]** |
| **8** | 挂接 Remove | `RemoveVTableHooks()` | — | 调 `RemoveGapProtectionPatches()` + `RemoveSpySatGatePatch()` + **`RestoreSpySatBuildingTypes()`** | — | — | 卸载日志出现还原条目；四字段回原值 | **[待实测]** |
| **9** | 行为验收 P-1 | 对局：裂缝覆盖区放 PsychicReveal / 开 SpySat | — | 扫描退去后裂缝黑雾恢复 | `EnableGapProtection=1` | 关键 =0 后 bug 复现（作为反证） | A1.4 真机截图/日志 | **[待实测]** |
| **10** | 行为验收 P-2 | 对局：建造 SpySat 并供电 | — | 不触发全图开；`SpySatActive` 不置 1 | `EnableSpySatGate=1` | 关键 =0 且 S1=0 时全图开复现 | A2.4 真机截图/日志 | **[待实测]** |
| **11** | 行为验收 P-3 | 同进程开→关 S1（或卸载 DLL） | TYPE 已被改 | TYPE 四字段回原值 | `EnableSpySatRadarSweep` | 不还原则记缺陷 | A3.3/A3.5 | **[待实测]** |
| **12** | 崩溃闸门 | 验收窗口 `ra2youli/except.txt` | — | **零新增** | — | — | EVIDENCE_STANDARD v3 一票否决 | **[待实测]** |

**实施约束（ZCode 必须遵守）**
1. **禁止** 改 `ra2render/**` 之外的引擎盘上文件；gamemd.exe **只在内存** 打补丁，绝不写盘。
2. **禁止** 禁写 `.detour` 节；全部等长替换（6B/2B），无 trampoline（本包三项均不需要）。
3. **禁止** 与「SuperClass 覆写 `Cell+0x134`」方案叠加。
4. 备份数组必须在 **首次写入前** 填好；还原用首次值（G-07 跨重载不污染）。
5. ini 键写入 **两份** `ra2render.ini`（`ra2render/` 与 `ra2youli/`）保持一致（现有约定）。
6. 遥测/日志按 `telemetry_and_switches_spec.md` 四要素：开关 / 计数 / 卸载还原 / 回滚判据。

---

## 7. 证据索引

| 产物 | 路径 |
|---|---|
| 字节核验脚本 | `out/re_work/landing_gap/verify_m10_bytes.py` |
| 字节核验输出 | `out/re_work/landing_gap/verify_m10_bytes_out.txt`（RESULT: PASS） |
| 本落地包 | `docs/re/landing_pack_gap_spysat.md` |
| 反汇编/根因 | `docs/re/gap_generator_spysat_deep_dive.md` §3.3/§4.3 |
| SpySat 关键字节 | `docs/re/superweapon_re.md` §5.3 |
| G-07 缺口原文 | `docs/re/INSTALLED_HOOKS_AUDIT.md` A8；`docs/re/hook_gate_gap_table.md` §5 G-07 |
| 同步契约 | `docs/re/net_sync_checksum.md` §4.2/§5 |

**核验摘要（2026-09-26，`ra2youli/gamemd.exe` 4,825,360 B）**

```
gap1 0x00568273 : 89 99 34 01 00 00          MATCH
gap2 0x00577EC5 : 89 B8 34 01 00 00          MATCH
gap3 0x00577B60 : 89 98 34 01 00 00          MATCH
spysat 0x00508F88 : 80 B8 A5 16 00 00 00 74 65  MATCH
je target : 0x00508FF6                        MATCH
```
