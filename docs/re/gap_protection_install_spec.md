# ZCode 安装规格 · EnableGapProtection 门控 + P-2.1 六字节写入

> **规格号**：`R-GAP-INST` · **上游落地卡**：`docs/re/landing_pack_gap_p21.md`（`ZC-GAP-P21`）  
> **上游深潜**：`docs/re/gap_psychic_reveal_deep_dive.md`（R-GAP-PSY）· 复算 `out/re_work/re_sprint/R_gap_psy/`  
> **本规格范围**：P-2.1 **安装路径**（A/B 并列论证 + 首选裁决）。**不改** `ra2render/**` / `gamemd.exe` / `tools/**` / 台账。  
> **执行方**：ZCode（真机写者）· **起草**：MiMo（R-GAP-INST 全静态）  
> **证据基线**：`ra2bench/gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · ImageBase `0x00400000` · `file_off = VA − 0x00400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **本规格独立复核（2026-09-29 静态）**：`0x568271..0x56827B` = `3B C3 | 89 99 34 01 00 00 | 7C 14 | 3D` **MATCH**（`out/re_work/re_sprint/R_gap_inst/claims.txt`）

---

## 0. 一句话

**首选 A（ra2render 加载期补丁）**：在 `InstallVTableHooks` 既有生命周期内，按 `EnableGapProtection` + `MpActive` 门控对 `VA 0x00568273` 做 6B 等长 `90×6` 写入，`RemoveVTableHooks`/进程卸载时 `memcpy` 还原；**B（外部补丁器）** 仅作离线回退/无 DLL 场景，必须同一套 G0/Q1 门禁与还原契约。二者**禁止同时生效**。

---

## 1. 写入点（字节级，与落地卡 §1 严格一致）

| 项 | 值 |
|---|---|
| **步骤 ID** | `P-2.1` |
| **VA** | `0x00568273` |
| **文件偏移** | `0x00168273` |
| **节** | `.text`（禁动 `.detour`） |
| **函数** | `MapClass::RevealArea2` @ `0x005678E0` |
| **原 6B** | `89 99 34 01 00 00` = `mov [ecx+0x134], ebx`（`ebx=0`） |
| **新 6B** | `90 90 90 90 90 90` |
| **约束** | **必须 6==6**；只许 `90`；禁 trampoline / 禁 `89→8B` / 禁 `add/or/and/xor/cmp` 类 1B 翻法（flags 邻接 + ebx 零常量） |

**上下文窗（21B 自检）**：

> 【勘误 2026-09-30 · R-E02 · errata_sync】原文「21B 自检」→ 订正为：指令对齐合计 **17B**（2+6+2+7）。若按首末 VA 跨度计则 45B，两种口径不可混用。权威：RESULT_GAP_P21.md §5 E-2 / p223_readiness_check.md:106。原文保留不删字。

| 相对 VA | 原字节 | 角色 |
|---|---|---|
| `0x568271` | `3B C3` | `cmp eax, ebx` —— 产生后续 `jl` 所需 flags |
| `0x568273` | `89 99 34 01 00 00` | **★ 替换点** |
| `0x568279` | `7C 14` | `jl …` —— 消费上一条 `cmp` 的 flags（`mov`/`nop` 均不改 flags） |

**语义边界**：只删 `GapsCoveringThisCell←0`；`0x56824A ShroudCounter←0` 与 `0x568297 CopyFlags\|=0x10` **原样保留**。

【勘误 2026-09-30 · R-E01 · errata_sync】原文 VA「0x568297」错误。该指令实际在 VA 0x0056829A（83 89 2C 01 00 00 10 = or dword [ecx+0x12C], 0x10）；0x568297 处字节为 50 DC AB 00，属上一条 mov ecx,0xABDC50 的立即数尾巴。权威：RESULT_GAP_P21.md §5 E-1。原文保留不删字。

---

## 2. 路径 A · ra2render.dll 加载期补丁（**首选**）

### 2.1 调用时机（对照现有生命周期，零新线程）

```
DllMain PROCESS_ATTACH                 dllmain.cpp:27
  └─ InstallVTableHooks()              dllmain.cpp:31 → blitter_hooks.cpp:3177
       ├─ LoadConfig()                 blitter_hooks.cpp:3178 → :496   ★只在此读 ini 一次
       ├─ PatchVTablePointer ×13       :3181..:3257（既有风格）
       ├─ InstallCellClassDrawHook()   :3260
       ├─ InstallGreatestThreatHook()  :3263
       ├─ InstallRadarFogHooks()       :3266
       └─ ★ InstallGapProtectionP21()  【本规格新增挂点，建议紧随 :3266 之后、最终 Log 之前】
            └─ 门控 → 读窗 → 备份 → VirtualProtect → memcpy 90×6 → 还原保护 → 遥测

DllMain PROCESS_DETACH                 dllmain.cpp:39
  └─ RemoveVTableHooks()               dllmain.cpp:44 → blitter_hooks.cpp:3272
       ├─ RemoveCellClassDrawHook / RemoveGreatestThreatHook / RemoveRadarFogHooks  :3273-3275
       ├─ ★ RemoveGapProtectionP21()   【本规格新增：若已装则 memcpy s_origP21[6] 还原】
       └─ 虚表还原 + 遥测收口           :3277..:3351
```

**为什么挂在这里（而非热路径）**：

1. 与 `LoadConfig` **仅 init 读**的现状一致（`blitter_hooks.cpp:445` 注释已点名「本键只在 LoadConfig 读一次」的教训；`FogStrengthPct` 是后来才加 `SyncFogStrengthMirror` 热重载例外，**本键不做例外**）。
2. 与 `InstallCellClassDrawHook` / `InstallRadarFogHooks` 的「备份原字节 → `VirtualProtect` → 写 → 卸载还原」风格完全同构（`:2508-2535` / `:2580-2613` / `:2940-3034`）。
3. 写入点是 **`.text` 指令字节**，不是虚表指针；必须 init 一次写完，禁止每帧/每格判断（避免 flags 邻接被二次改写、也避免热路径膨胀）。
4. `RevealArea2` 有 **22 个 E8 调用者**（R-GAP-PSY §4）；写一次全局生效，无需 per-call hook。

### 2.2 伪代码契约（ZCode 落地时可直接照抄骨架）

```cpp
// ---- 常量（与落地卡 §1 一致，禁止漂移）----
static const uintptr_t ADDR_P21          = 0x00568273;
static const uint8_t   kP21Orig[6]       = {0x89,0x99,0x34,0x01,0x00,0x00};
static const uint8_t   kP21New[6]        = {0x90,0x90,0x90,0x90,0x90,0x90};
static const uint8_t   kP21WinPre[2]     = {0x3B,0xC3};          // 0x568271
static const uint8_t   kP21WinPost[2]    = {0x7C,0x14};          // 0x568279
static uint8_t s_origP21[6] = {0};
static bool    s_gapP21Installed = false;

// ---- LoadConfig() 内新增（init-only，风格对齐 GetIniIntEx 既有调用）----
// int gapVal = GetIniIntEx("FogOfWar", "EnableGapProtection", 0, iniPath, &h_gap);
// g_enableGapProtection = (gapVal != 0);   // ★ API 默认 0 = 不装（零行为变化）
// 日志尾追：EnableGapProtection=%d(%s)  —— 只追加字段，不改既有行顺序

static bool InstallGapProtectionP21() {
    // G0.6 + MP 门（对齐 GetEffectiveMinimapFog :235 的「MpActive 强制关」）
    if (!g_enableGapProtection) { Log("GapProtection=off"); return false; }
    if (MpActive())             { Log("GapProtection=forced-off-mp"); return false; }

    // G0.5 PE/基址（可选但推荐）：ImageBase==0x400000 && 目标落在 .text
    // G0.3/G0.4 上下文窗
    if (memcmp((void*)(ADDR_P21-2), kP21WinPre, 2)  != 0) { Log("G0.3 FAIL"); return false; }
    if (memcmp((void*)(ADDR_P21+6), kP21WinPost, 2) != 0) { Log("G0.4 FAIL"); return false; }

    // G0.2 / Q1 首字节门禁
    uint8_t first6[6];
    memcpy(first6, (void*)ADDR_P21, 6);
    if (memcmp(first6, kP21New, 6) == 0) {
        // 已是 90×6：区分「我方已装」vs「外部安装者」
        if (s_gapP21Installed) { Log("GapProtection=already"); return true; }
        Log("[警告/红字] GapProtection=external-installer-detected (Q1) —— 停手，禁止覆盖");
        return false;
    }
    if (memcmp(first6, kP21Orig, 6) != 0) {
        Log("[警告/红字] GapProtection=byte-mismatch —— 拒绝安装");
        return false;
    }

    // 备份 + 写入（对齐 InstallCellClassDrawHook 风格）
    memcpy(s_origP21, (void*)ADDR_P21, 6);
    DWORD oldProt;
    if (!VirtualProtect((void*)ADDR_P21, 6, PAGE_EXECUTE_READWRITE, &oldProt)) {
        Log("GapProtection=virtualprotect-fail"); return false;
    }
    memcpy((void*)ADDR_P21, kP21New, 6);
    VirtualProtect((void*)ADDR_P21, 6, oldProt, &oldProt);
    s_gapP21Installed = true;
    g_telemetry.gapProtectInstalled = 1;
    Log("GapProtection=on");
    return true;
}

static void RemoveGapProtectionP21() {
    if (!s_gapP21Installed) return;
    DWORD oldProt;
    if (VirtualProtect((void*)ADDR_P21, 6, PAGE_EXECUTE_READWRITE, &oldProt)) {
        memcpy((void*)ADDR_P21, s_origP21, 6);
        VirtualProtect((void*)ADDR_P21, 6, oldProt, &oldProt);
    }
    s_gapP21Installed = false;
    g_telemetry.gapProtectInstalled = 0;
    Log("GapProtection=restored");
}
```

### 2.3 开关语义（ini）

| 键 | 节 | API 默认 | ini 建议出厂 | 语义 |
|---|---|---|---|---|
| `EnableGapProtection` | `[FogOfWar]` | **`0`** | `0` | `1` 才安装 P-2.1；`0`/缺失 = 不碰 `.text` |
| （预留）`EnableGapProtectP22` / `P23` | — | — | — | **本规格不实现**；键名勿占用 |

- **联机**：`MpActive()==true` ⇒ **强制不安装**（与 `EnableMinimapFog` 同级门控，`GetEffectiveMinimapFog:235-245` 模式）。
- **启动日志必打**：`GapProtection=on|off|forced-off-mp|already|external-installer-detected`。
- **遥测**：`gapProtectInstalled`（0/1）；可选 `gapProtectSkipClearCount`（软计数，默认省略）。

---

## 3. 路径 B · 外部补丁器（离线回退）

适用：无 `ra2render.dll` 的最小包、安装前预打、或 A 暂不可用时。**文件级**改 `gamemd.exe`。

### 3.1 命令面（最小）

| 命令 | 行为 |
|---|---|
| `gap21 --install [--exe <path>]` | G0 门禁 → 写 6B → 写 sidecar |
| `gap21 --uninstall-p21` | 按 sidecar/原 6B 还原该 6B |
| `gap21 --status` | 打印哈希、6B 状态、sidecar |

### 3.2 安装前门禁（与 A 同序，全 PASS 才写）

| # | 检查 | 期望 | 失败则 |
|---|---|---|---|
| G0.1 | 文件 SHA-256 | `73201CC0…F67476` | **拒绝** |
| G0.2 | `file_off 0x168273` 首 6B | `89 99 34 01 00 00` | `90×6`→「已打」跳过；其它→**拒绝** |
| G0.3 | `0x168271` | `3B C3` | 拒绝 |
| G0.4 | `0x168279` | `7C 14` | 拒绝 |
| G0.5 | PE32 / ImageBase `0x400000` / 目标在 `.text` | MATCH | 拒绝 |
| G0.6 | 操作者显式确认 / 配置 `EnableGapProtection=1` | 显式才写 | 默认不写 |
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0

**Q1 外部安装者**：若首字节已 `90` 且 sidecar 不是我方 `gap21` 写的 ⇒ **停手上报**，禁止覆盖未知安装者（落地卡 §2 Q1）。

### 3.3 Sidecar（B 独有，A 不需要）

安装成功后写 `gamemd.exe.gap21.json`（与 exe 同目录）：

```json
{
  "step": "P-2.1",
  "va": "0x00568273",
  "file_off": "0x168273",
  "orig_sha256": "73201CC0…F67476",
  "orig_6b": "89 99 34 01 00 00",
  "new_6b":  "90 90 90 90 90 90",
  "installed_at": "ISO-8601",
  "tool": "gap21/1.0"
}
```

**为何必须 sidecar**：B 是文件级补丁，**G0.1 的整文件 SHA-256 在安装后必然改变**；后续 `--uninstall` / 二次 `--install` 不得再拿「原版哈希」当唯一门禁，改为：

1. 有 sidecar ⇒ 校验 `orig_6b` + 当前 6B ∈ {orig, new}，哈希仅作参考；
2. 无 sidecar 且 6B=原版 ⇒ 走完整 G0.1；
3. 无 sidecar 且 6B=`90×6` ⇒ **Q1 外部安装者，停手**。

### 3.4 B 的固有局限（写进安装说明，避免误用）

| 局限 | 后果 | 缓解 |
|---|---|---|
| 无法运行时 `MpActive` 强制关 | 联机局仍可能带着补丁 ⇒ 混端 DESYNC | 安装器启动时要求 `EnableGapProtection=1` 且文档强制「联机全员同构建同开关」；或联机前 `--uninstall-p21` |
| 整文件哈希变更 | 与依赖原版哈希的校验器/其它工具互斥 | sidecar + 状态报告；与 A **二选一** |
| 开关不能热切换 | 改 ini 无效，必须重跑补丁器 | 见 §5 |
| 可能与其它外部补丁器互撞 | 覆盖未知写者 | G0.2/Q1 停手策略 |

---

## 4. 与既有 Hook 门控矩阵兼容（只读 `ra2render/**` + `HOOK_POINT_MATRIX.md`）

### 4.1 门控矩阵对照（本键 = 独立逻辑态补丁，不进绘制谓词链）

| 既有键 | 作用域 | 与 `EnableGapProtection` 关系 | 裁决 |
|---|---|---|---|
| `EnableStarCraftFog` | 已探索非直视档压暗（总闸） | **无关**。P-2.1 改的是 `Cell+0x134` 逻辑计数，不改绘制强度 | 解耦；总闸=0 时 P-2.1 仍可装 |
| `EnableBuildingFog` / `EnableBulletFog` / `EnableUnitFog` | 玩法可见性三剔除 | **无关**。三键走 `Hook_*_Draw` 谓词，不写 `.text` | 解耦 |
| `VisibilityMode` | 覆盖三剔除子键 | **无关** | 解耦 |
| `FadeFogTransition` | 灰雾渐变强度（运行期镜像可热更） | **无关**；且 **禁止**给 `EnableGapProtection` 做 `SyncFogStrengthMirror` 式热重载 | 解耦 + 不热更 |
| `EnableMinimapFog` | 小地图减暗；`MpActive` 强制 0 | **同级 MP 门控模板**：`GetEffectiveMinimapFog:235` 的「联机强制关」照抄 | 对齐 |
| `EnableSpySatRadarSweep` / S1 TYPE 补丁 | 写 TYPE 内存，W3 联机旁路 | **相关但不重叠**：S1 封 SpySat 路线，P-2.1 封 RevealArea2 路线；两者互补 | 允许并存；联机侧两者都应关 |
| `TargetScanInterval` / `TargetScanKey` | L2 节流 | 无关 | — |
| L4 `0x006D3D99` / B1/B2 桩 | 脏矩形/混色 | 无关；P-2.1 **不**占 `.detour`、不做 trampoline | — |
| `EnableSIMD` / `EnableLFH` / `HighPrecisionTimer` / `UnlockGameSpeed` | 渲染/系统 | 无关 | — |

### 4.2 与 Hook 点冲突

| 项 | 结论 |
|---|---|
| `HOOK_POINT_MATRIX.md` §2.6 行 `0x00568273` | 状态由「未装 (P5)」→ 本规格落地后「已装」；**是全表唯一 6B NOP 写点** |
| 与 CellClass::Draw `0x4801F0` / Draw_Fog B1/B2 / L4 / 雷达路线 A | **地址不相交**；无虚表槽争用 |
| 与 Greatest_Threat `0x6F8DF0` 9B trampoline | 不相交 |
| 与 P-2.2 `0x577EC5` / P-2.3 `0x577B60` | 同族写点，**本规格只装 P-2.1**；P-2.2/2.3 留后续卡（落地卡 §7）。若未来并装，回滚顺序 **P-2.3 → P-2.2 → P-2.1** |
| `.detour` 节 | **禁止写入**（落地卡 G0.5 约束延伸） |

### 4.3 MP 策略（**不新增握手字段**）

沿用 `RE_COORDINATION.md` 已裁决「**不采纳**把 `EnableGapProtection`/`EnableSpySatGate` 纳入联机握手校验字段」：

1. **无**新协议字段、无握手键、无版本交换；
2. 策略 = **全员强制同值 + 禁混端**（`landing_pack_gap_p21.md` R-1；`mp_autodowngrade_spec.md` 红线）；
3. 运行期 `MpActive` 只做**本端旁路**（A 路径强制不装 / 已装则…见 §5.3），日志留痕，**不改任何网络消息**；
4. 混端（一端 NOP、一端原版）因 `+0x134` 进 `.SAV` 必 DESYNC —— 文档级禁止，不靠握手拦截。

---

## 5. 失败路径 · 回滚 · 「开关重启才生效」

### 5.1 失败路径一览

| 场景 | 判定 | 动作 | 日志/上报 |
|---|---|---|---|
| **哈希不符**（G0.1） | SHA-256 ≠ `73201CC0…` | **拒绝安装**，不写任何字节 | `GapProtection=hash-mismatch` |
| **字节窗不符**（G0.3/G0.4） | 前 `3B C3` / 后 `7C 14` 任一失配 | **拒绝** | `GapProtection=context-mismatch` |
| **6B 既非原版也非 90×6** | G0.2 失败 | **拒绝**（禁止猜测补丁） | `GapProtection=byte-mismatch` |
| **已打 = 我方**（A 重入 / B 二次 install） | 6B=`90×6` 且 `s_gapP21Installed`/sidecar 匹配 | **跳过**，幂等成功 | `GapProtection=already` |
| **已打 = 未知外部安装者（Q1）** | 6B=`90×6` 且无我方标记 | **停手 + 上报**，禁止覆盖 | `GapProtection=external-installer-detected`（红字） |
| **MP**（`MpActive`） | 会话标志 `0xA8D5F8 bit1` 或 DP==2 | **强制不安装**；若 A 已装则不在运行中拆除（见 §5.3） | `GapProtection=forced-off-mp` |
| **开关=0 / 键缺失** | API 默认 0 | 不碰 `.text` | `GapProtection=off` |
| **`VirtualProtect` 失败** | Win32 失败 | 中止；**不得半写** | `GapProtection=virtualprotect-fail` |
| **PE/基址不符**（G0.5） | 非 PE32 或 base≠`0x400000` | 拒绝 | `GapProtection=pe-mismatch` |

### 5.2 回滚

| 层 | 操作 | 时机 |
|---|---|---|
| **软** | `EnableGapProtection=0` + **重启游戏/重载 DLL** | 下次 init 不装；A 的 DETACH 会还原本次会话写入 |
| **硬（A）** | `RemoveGapProtectionP21()`：`memcpy` `s_origP21[6]` | `DLL_PROCESS_DETACH` / `RemoveVTableHooks` 末尾 |
| **硬（B）** | `gap21 --uninstall-p21`：按 sidecar/`kP21Orig` 写回文件 6B | 安装前/任意时刻（游戏未运行时） |
| **灾难** | 重装/校验 `gamemd.exe` 原版哈希 | sidecar 丢失且字节窗被未知方改写 |

**回滚验收**：还原后 `0x568273` 必须逐字节 `89 99 34 01 00 00`，且 `0x568271/0x568279` 仍未改动。

### 5.3 「开关重启才生效」坑（**必须写进 ini 注释与安装说明**）

| 事实 | 依据 | 用户可见后果 |
|---|---|---|
| `LoadConfig()` **仅** `InstallVTableHooks` init 调用一次 | `blitter_hooks.cpp:3178` → `:496`；`:445` 注释 | 游戏运行中改 `EnableGapProtection` **无效** |
| 安装态是 `.text` 写入，不是每帧谓词 | 本规格 §2.1 | 不存在「≤1 帧生效」；也**不要**做成热切换 |
| `FogStrengthPct` 有热重载是**例外**（`SyncFogStrengthMirror`） | `:455-494` | 不得类推到本键 |
| A 卸载即还原 | `RemoveVTableHooks` | 重启后 `=0` ⇒ 行为回到原版；**无需**手动还原 |
| B 改的是磁盘文件 | §3 | `=0` **不会**自动还原；必须 `--uninstall-p21` 或重装原版 exe |

**ini 注释模板（给 ZCode 抄）**：

```ini
; EnableGapProtection: P-2.1 裂缝保护（RevealArea2 不再清 GapsCoveringThisCell）
; 【安装态】仅在游戏/DLL 启动时决定 —— 改本键后必须重启才生效（非热重载）。
; 【默认 0】= 不安装（零行为变化，.text 不被触碰）。
; 【联机】MpActive 强制不安装（与 EnableMinimapFog 同级）；全员必须同构建同本键，严禁混端。
; 【回滚】置 0 后重启即可（加载期补丁会自动还原）；外部补丁器安装的需 --uninstall-p21。
EnableGapProtection=0
```

### 5.4 运行中遇到 MP 的 A 路径细则

- **init 时已是 MP**：不装（`forced-off-mp`）。
- **init 单机已装、中途进入 MP**：**不在热路径拆除**（拆写本身有 flags/线程风险，且两端本应同构建）。正确策略是文档级「全员同开关」+ 启动日志审计；若产品要求更狠，留后续卡做「MP 边沿还原」（需与 `mp_autodowngrade` W 系列一并设计，**本规格不做**）。
- **禁止**为了 MP 在 `RevealArea2` 里加运行期分支 —— 那会引入非 `90` 指令，违反 R-4/R-5。

---

## 6. A / B 并列论证与裁决

| 维度 | **A 加载期补丁** | **B 外部补丁器** |
|---|---|---|
| 与现有架构 | 同构（`Install*Hook` / `Remove*Hook` / `s_orig*`） | 旁路工具，生命周期外 |
| `EnableGapProtection` 门控 | 原生 `GetIniIntEx`，与其它键同风格 | 只能在安装时读 ini/参数 |
| **MP 强制关** | **可**（`MpActive`） | **不可**（静态文件） |
| Q1 外部安装者 | init 读 6B 可检 | 安装前可检 |
| 回滚 | 卸载自动还原 + 软开关 | 需 `--uninstall` |
| 开关体验 | 重启即生效/还原 | 重启不够，还要跑工具 |
| 整文件哈希 | **不变**（只改内存） | **必变**（需 sidecar） |
| 无 DLL 最小包 | 不适用 | 适用 |
| 混端风险控制 | 强（本端可强制关） | 弱（靠纪律） |
| 实现面 | ra2render 一处挂点 | 独立 exe + 文档 |

### 裁决（推荐）

**首选 A，并列保留 B 为离线回退。**

1. **A 对齐门控矩阵**：`EnableMinimapFog` 的 MP 强制关、`LoadConfig` 的 init-only、`blitter_hooks` 的备份-写-还原，全部现成可抄；B 无法满足落地卡 §3.1 的 `MpActive` 强制不安装。
2. **A 不改磁盘哈希**，不与其它校验器、不与「禁改游戏」的运维面冲突。
3. **B 仍有价值**：预装、无 DLL 裸 exe、故障恢复；但必须 sidecar + Q1 停手，且**与 A 互斥**（同一时刻只允许一种写者）。
4. **禁止 A+B 同时生效**：A 的 Q1 会把 B 的产物识别为「外部安装者」而停手 —— 这是**特性不是缺陷**，强制单一写者。

---

## 7. 真机验收（承接落地卡 A1–A5，补安装路径专条）

| ID | 步骤 | 期望 |
|---|---|---|
| A1 | 默认配置启动 | `0x568273` 仍为原版 6B；日志 `GapProtection=off` |
| A2 | `EnableGapProtection=1` 启动 | `0x568273=90×6`；`0x568271/0x568279` 未变；`GapProtection=on` |
| A3 | 敌方 Gap 覆盖 + PsychicReveal/任一 RevealArea2 开图 | **裂缝遮挡仍在**（禁止只看「没崩」） |
| A4 | A3 后存 `.SAV` → 读档 | 缝态保持；`except.txt` 空 |
| A5 | 摧毁缝建筑 / DestroyGap | 计数能回 0，无残留永久缝 |
| **I1** | 启动前先由外部工具写 `90×6`，再 `EnableGapProtection=1` 启动（A） | 日志 `external-installer-detected`，**不覆盖** |
| **I2** | `EnableGapProtection=1` → 游戏中改 `=0` | **不**立即还原；重启后 `off` 且字节为原版 |
| **I3** | B：`--install` 后 `--status` → `--uninstall-p21` → 再 `--status` | 6B 往返为原版；sidecar 一致 |
| **I4** | B 安装后二次 `--install` | `already` 幂等，不重复写 |
| **I5** | 联机/MpActive 下 A 启动 | `forced-off-mp`，字节保持原版 |

---

## 8. 禁止项（执行方红线）

1. **禁止**新增 MP 握手字段 / 协议键 / 版本交换（维持既有策略）。
2. **禁止**改 `ra2render/**` 以外的游戏源；ZCode 可写实现，但**规格面**不得把 P-2.2/P-2.3 偷偷带上。
3. **禁止** trampoline / 改 flags / 改 `ebx` / 非 `90` 替换。
4. **禁止**把 `EnableGapProtection` 做成热重载。
5. **禁止** A+B 双写者；禁止覆盖 Q1 未知安装者。
6. **禁止**在热路径（`RevealArea2` 每格）加运行期开关分支。
7. **禁止**占用 `EnableGapProtectP22/P23` 键名。

---

## 9. 交付回执（ZCode 填写）

```
R-GAP-INST / ZC-GAP-P21 RESULT
- install path: A ra2render | B external | (rejected)
- build/md5(gamemd):
- EnableGapProtection (ini/API):
- G0.1–G0.6:
- Q1 first byte before:
- bytes after @0x568273:
- MpActive at install:
- GapProtection log line:
- A1..A5 / I1..I5:
- rollback tested:
- sidecar (B only):
- except.txt:
```

---

*依据：`landing_pack_gap_p21.md` §1–§5；`gap_psychic_reveal_deep_dive.md`；`HOOK_POINT_MATRIX.md` §2.6/§3.6；`hook_gate_gap_table.md` §1–§2；`mp_autodowngrade_spec.md` W3/红线；`ra2render/dllmain.cpp:25-51`；`ra2render/blitter_hooks.cpp` `LoadConfig:496` / `MpActive:190` / `GetEffectiveMinimapFog:235` / `InstallVTableHooks:3177` / `InstallCellClassDrawHook:2508` / `RemoveVTableHooks:3272`。字节窗本规格独立复核 MATCH。*
