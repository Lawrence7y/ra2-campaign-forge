# MP 门控残余深潜（R-MP-GATE）

> **文档标识**：`docs/re/mp_gate_residual_deep_dive.md` · 任务 **R-MP-GATE**（全静态，不启动游戏）
> **目标二进制**：`ra2youli/gamemd.exe` YR 1.001 · MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` · ImageBase `0x400000` · `file_off = VA − 0x400000`
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **写作用域**：本文件 + `out/re_work/re_sprint/R_mp_gate/**`。**未改** `ra2render/**`、`gamemd.exe`、`ra2youli/**`、`tools/**`、台账、看板、ATLAS、`out/reverse/**`。
> **证据源（只读）**：`ra2render/blitter_hooks.cpp`（3505 行工作树快照）、`ra2render/ra2render.ini`、`docs/re/mp_autodowngrade_spec.md`（M-6）、`docs/re/mp_release_safety_checklist.md`（G-01…G-10 / R-01…R-04）、`docs/re/MP_SAFETY_REVIEW.md`（M-4）、`docs/re/hook_gate_gap_table.md`、`docs/re/mp_landing_consistency.md`、`docs/re/re_sprint_S16_report.md`（NetworkManager 定谳）、`docs/re/sav_gap_cell_abi_deep_dive.md`、`docs/re/landing_pack_gap_p21.md`、`docs/re/landing_pack_particle.md`、`docs/re/vxl_cache_shadow_landing.md`、`docs/re/audio_throttle_landing.md`、`docs/re/gap_protection_install_spec.md`
> **取证脚本**：`out/re_work/re_sprint/R_mp_gate/scan_sessionflags.py`、`scan_source_gates.py`（输出 `sessionflags_xrefs.*`、`source_gate_census.txt`、`claims.txt`）
> **证据三档**：**[实证]** 本任务对 `gamemd.exe` 字节/源码复算；**[前证]** 既有深潜已实证、本轮抽查一致；**[待实测]** 需真机混联/双端对拍。
> **既定政策（红线）**：**禁止提议任何新握手字段**。可落地动作仅限「**启动日志打印 + 强制降级（旁路/强制值/不装）**」。

---

## 0. 结论摘要

| 维度 | 结论 |
|---|---|
| **Gate1（R-01/R-02/R-03）** | **代码层已闭环** [实证]：`EnableMinimapFog` 默认 0 + 联机强制 0；`TargetScanKey` 联机强制 position；`TargetScanInterval` 联机强制 1。 |
| **Gate2（G-03/G-06）** | **仍未闭环** [实证]：`EnableThreatRetention` / `MpStateWrites` 全库 0 命中；S2/S3 每帧写无旁路。 |
| **M-6 W1–W6** | W1/W2 经 interval=1 **间接生效**；W3（SpySat TYPE）**未旁路**；W4/W5（Scenario/House 写）**未旁路**；W6 载体保留。 |
| **SessionFlags** | `0xA8D5F8 = NetworkManager(0xA8D58C)+0x6C`，bit0=SP / bit1=NetworkActive / bit2=Attract [前证 S16 + 本轮 52 处 xref 复算一致]。 |
| **混端 DESYNC** | **gap（Cell+0x134）= 致命**；**S2/S3/SpySat TYPE = 致命/高**；particle/vxl/audio 新卡 = **表现层 SAFE**（无 DESYNC，有观感分叉）。 |
| **握手字段** | **不新增**（政策既定）。以「启动日志打印 + 联机强制降级」替代；混端禁令走文档红线。 |
| **发布判定** | **GATE-MP 仍 NO-GO**：Gate2 未闭环 + Gate3（混联 ≥5000 帧零 OOS）未执行 [待实测]。 |

**一句话**：P0 三项已落地且有日志自证，但 W3/W4/W5 状态写与 TYPE 补丁仍无 `MpActive()` 旁路——混端（对方原版）在第一次 `RevealArea2` / SpySat 触发后必分叉；在补齐旁路前，联机侧必须整局不加载 `ra2render.dll`，或全员同构建同开关。

---

## 1. G-01…G-10 / M-6 现状 vs 规格缺口清点

### 1.1 总表（现网源码 3505 行快照 · 2026-09-30 复核）

| 编号 | 规格要求（Lead 终局） | 现网状态 | 判定 | 缺口 / 残余动作 |
|---|---|---|---|---|
| **G-01** | `EnableMinimapFog` API 默认 0；联机强制 0（R-01，P0） | `GetIniIntEx(..., 0, ...)` `:577`；静态 `g_enableMinimapFog=false`；`GetEffectiveMinimapFog()` `:245` 联机 `eff=false`；ini `:117 EnableMinimapFog=0` | **✅ 闭环** [实证] | 剩真机验收（缺陷1 三局）[待实测] |
| **G-02** | 联机强制 `position` 键，禁 pointer（R-02，P0） | `GetEffectiveTargetScanKey()` `:227` 联机 `return 1`；红字告警 `:323-325`/`:776` | **✅ 闭环** [实证] | 无 |
| **G-03** | `[Logic] EnableThreatRetention`（单机 1 / 联机强制 0） | **0 命中**；Retention 短路仍绑 `interval>1` | **❌ 未闭环** | 经 G-08 interval=1 **间接禁短路**（`return pTarget` 不可达）；独立键仍缺，单机无法单关对拍 |
| **G-04** | B1/B2 + L4 接 `EnableStarCraftFog` 总闸；关闸还原/门控 | `L4DirtyMode` 字面 **10** 命中（源码）+ ini 2；E2 勘误：部署 DLL 内桩已带运行期 `je` 总闸 | **◐ 运行期门控已落** [前证 E2] | 「关闸三计数恒 0」= [待实测]；`EnableFogBlendStubs` 独立键仍无 |
| **G-05** | `Hook_RadarPending_Proxy` 前置 `s_minimapFogGate`（R-04，P2） | 源码已接 `cmp [s_minimapFogGate],0; je orig_logic`（DA1 §6.2 / hook_gate §9.2） | **✅ 源码已实现** [前证] | 不在 Lead 三项清单，待裁决入册 |
| **G-06** | `[Multiplayer] MpStateWrites=0`；联机旁路 S2/S3 | **0 命中**；`:1550` `&= ~0x1000u`、`:1554` `+0x577A=0` **每帧无条件写** | **❌ 未闭环（P1 最高残余）** | 见 §2.3 可落地点 L-3 |
| **G-07** | S1 TYPE 4 字段备份 + `RemoveVTableHooks` 还原 | `RestoreSpySat` **0 命中**；`PatchSpySatBuildingTypes` `:1392-1451` 只写不备份 | **❌ 未闭环** | 回滚能力缺失；且无 MpActive 旁路 |
| **G-08** | 联机无条件 `TargetScanInterval=1`（R-03，P0） | `GetEffectiveTargetScanInterval()` `:220` 联机 `return 1`；三处调用点 `:1231/:1253/:1292` | **✅ 闭环** [实证] | 剩遥测「节流率 0.0%」真机 [待实测] |
| **G-09** | everSeen 不进档（体验遗留，P2） | `s_everSeenGrid` DLL 私有 `static uint8_t[512*512]`，不入 `.SAV`/CRC | **✅ 维持现状** [前证] | 文档声明即可，不阻断 |
| **G-10** | 死符号/死宏/空开关清理（卫生，P2） | `Hook_Unit_Greatest_Threat` / `ADDR_RADAR_PLOT_CALLSITE` / `EnforceGameSpeedUnlock` 仍在 | **❌ 未清理** | SAFE，不阻断 |

### 1.2 M-6 降级白名单 W1–W6 对照

| # | M-6 要求 | 现网 | 判定 |
|---|---|---|---|
| **W1** | 联机旁路 `>>4` 节流，强制 interval=1 + position 键 | `GetEffectiveTargetScanInterval/Key` 已做 | **✅**（=G-02+G-08） |
| **W2** | 禁 Threat Retention 短路 | interval=1 时短路分支不可达；无独立键 | **◐ 间接生效** |
| **W3** | 联机跳过 S1 SpySat TYPE 补丁 | `PatchSpySatBuildingTypes` **无** `MpActive()` 门 | **❌** |
| **W4** | 联机跳过 S2 Scenario 标志写 | `:1550` 无门 | **❌** |
| **W5** | 联机跳过 S3 House+0x577A 写 | `:1554` 无门 | **❌** |
| **W6** | UpdateVisionGrid 调用保留、状态写旁路 | 调用保留 ✓；状态写旁路 ✗ | **◐** |

### 1.3 规格外缺口（本任务新登记）

| ID | 缺口 | 证据 | 风险 |
|---|---|---|---|
| **X-1** | `MpActive()` 异常路径 `return false`（`:213-215`），**与 M-6 §3.2「检测失败→保守按联机」相反** | [实证] 源码 | 读失败时可能误判单机 → 保留 VIOLATION 项 |
| **X-2** | `MpAutoDowngrade` / `ForceSinglePlayer` 总闸/逃生舱键 **未实现**（0 命中） | [实证] | 无一键回滚、无单机强制覆盖 |
| **X-3** | `MpThrottleForceInterval` / `MpBypass*` 细粒度键未实现 | [实证] | 调试粒度不足（非阻断） |
| **X-4** | 辅助确认 `0xA8B238 ∈{1..4}` **已作废**（勘误 v1.8.3：GameMode 枚举，不能分菜单/局内） | [前证] | 现网 `MpActive()` 已不依赖它 ✓ |
| **X-5** | Gap 保护 `InstallGapProtectionPatch` 只在**安装期**判 MpActive（`:3214`）；若先装后进联机则字节仍在 | [实证]+[推演] | 运行中升联机不会拆补丁（M-6 防抖语义缺失） |

---

## 2. MpActive / SessionFlags 门控点全表

### 2.1 SessionFlags 位域（已定谳 · S16 + 本轮 52 xref 复算）

| 字段 | 值 |
|---|---|
| **宿主** | `NetworkManager` 单例基址 `0x00A8D58C`，字段 `SessionFlags` 偏移 `+0x6C` |
| **地址** | `0x00A8D5F8`（BSS dword，按 byte 位域用） |
| **bit0 = 0x01** | SinglePlayer 标志；写点 `0x52E963` 清（`and al,0xFE`）；读 `test …,1` ×3 [实证] |
| **bit1 = 0x02** | **NetworkActive（联机会话/锁步）**；置位 `0x52DD00`（`or edi,2` → `ConnectSession`）；清 `0x52DC34/0x52DD23/0x48CF87`（`and al,0xFD`）；读 `test …,2` ×**20** [实证] |
| **bit2 = 0x04** | Attract/Demo（`-ATTRACT`）；置位 `0x52F9EB`（`or al,4`）；读 `test …,4` ×1 + `test …,bl(bl=4)` ×2 [实证] |
| **组合** | `test …,0x03`（bit0\|bit1）×1 @ GameRunner；`test …,bl` 用于 bit2 复测 [实证] |
| **全文规模** | imm32 `F8 D5 A8 00` = **52** 处（`sessionflags_xrefs.txt`）[实证] |
| **写点全集** | `mov [0xA8D5F8], eax` ×5：`0x48CF9A / 0x52DC3B / 0x52DD2A / 0x52E96A / 0x52F9F2` [实证] |
| **门控读法** | **只读 bit1**（`& 0x02`）= 引擎自身锁步开关；bit0/bit2 不参与联机判定 |

### 2.2 现网 `MpActive()` 判定链（`blitter_hooks.cpp:198-217`）

```
主判: *(uint8_t*)0x00A8D5F8 & 0x02 != 0          → true（联机）
辅判: *(int32_t*)0x00AA0444 == 2                  → true（DirectPlay 模态）
异常: __except → return false                     → ★与 M-6 保守默认相反（X-1）
否则: false
```

> 口径：现网为「**OR 命中即联机**」，不是 M-6 的「四选二计分」。功能上更保守（任一命中即降级），但异常路径漏了「失败→按联机」。

### 2.3 门控点全表（VA / 条件 / 现行为）

| # | 门控点 | 引擎/源码位置 | 条件 | 现行为（联机 MpActive=true） | 档 |
|---|---|---|---|---|---|
| G1 | NetFrameSync 锁步入口 | 引擎 `0x00647260` `test al,2` → `je 0x6474C7` | bit1=0 | 引擎自早退（单机不跑收包/CRC/命令） | [实证] |
| G2 | MainLogicFrame 联机分支 | 引擎 `0x0055D463` / `0x0055D878` | bit1 | 走联机路径 | [实证] |
| G3 | GameRunner 联机分支 | 引擎 `0x0048CE0D` / `0x0048CF0E` | bit1 / bit0\|1 | 走联机/会话路径 | [实证] |
| G4 | NetworkEvent::Execute | 引擎 `0x004C7929` / `0x004C80F6` | bit1 | 事件按联机语义执行 | [实证] |
| G5 | GameMainLoop 联机分支 | 引擎 `0x0052DB33` | bit1 | 联机分支 | [实证] |
| G6 | DirectPlay 收包忙等门 | 引擎 `0x0053E86C` `cmp [0xAA0444],2` | ==2 | 进忙等环 `0x53E8B3` | [实证] |
| **P1** | `GetEffectiveTargetScanInterval` | 源码 `:219-224` | `MpActive()` | **强制 return 1**（禁节流） | [实证] |
| **P2** | `GetEffectiveTargetScanKey` | 源码 `:226-231` | `MpActive()` | **强制 return 1**（position） | [实证] |
| **P3** | `GetEffectiveMinimapFog` | 源码 `:243-253` | `MpActive()` | **强制 false**；镜像 `s_minimapFogGate=0` | [实证] |
| **P4** | `CheckMpGateTransition` | 源码 `:300-327` | 边沿检测 | 打「门控状态迁移」日志 + 红字 pointer 警告 | [实证] |
| **P5** | `LoadConfig` 启动门控行 | 源码 `:761-792` | `MpActive()` | 打「门控: MpActive=… 配置→生效」+ `[ra2render-mpgate]` 生效值行 | [实证] |
| **P6** | `InstallGapProtectionPatch` | 源码 `:3214-3215` | `MpActive()` | **强制不装**，打 `GapProtection=forced-off-mp` | [实证] |
| **P7** | `UpdateVisionGrid` → S2 | 源码 `:1548-1551` | （无门） | **每帧** `ScenarioClass.flags &= ~0x1000` | [实证] **缺口** |
| **P8** | `UpdateVisionGrid` → S3 | 源码 `:1554` | （无门） | **每帧** `House+0x577A = 0` | [实证] **缺口** |
| **P9** | `PatchSpySatBuildingTypes` (S1) | 源码 `:1392-1451` | 仅 `g_enableSpySatRadarSweep` | 写 TYPE `+0xB0/+0xF8/+0x16A5/+0x16F0`，无备份无旁路 | [实证] **缺口** |
| **P10** | 三处 L2 节流调用 | 源码 `:1231/:1253/:1292` | `GetEffectiveTargetScanInterval()` | 联机 interval=1 ⇒ 短路分支不可达 | [实证] |
| **P11** | RadarPending 代理 | 汇编镜像 `s_minimapFogGate` | gate=0 | 走 orig_logic（原版 call） | [前证] |

### 2.4 SessionFlags 引擎读点速查（摘自 `sessionflags_xrefs.txt`，全 52 表见该文件）

| VA | op | 语义 |
|---|---|---|
| `0x00647260` | `mov al,[0xA8D5F8]` + `test al,2` | NetFrameSync 主判 |
| `0x0064729F/0x006472B6` | `test [0xA8D5F8], bl`（bl=4） | bit2 复测 |
| `0x0052DB33` | `test …,2` | GameMainLoop |
| `0x0048CE0D` | `test …,2` | GameRunner |
| `0x0048CF0E` | `test …,3` | GameRunner bit0\|1 |
| `0x0055D463` | `test …,2` | MainLogicFrame |
| `0x004C7929` | `test …,2` | NetworkEvent::Execute |
| `0x0052DD00` | `or edi,2` + 写回 | **置 bit1**（连会话） |
| `0x0052DC34` | `and al,0xFD` + 写回 | **清 bit1**（拆会话） |
| `0x0052F9EB` | `or al,4` + 写回 | **置 bit2**（-ATTRACT） |
| `0x0052E963` | `and al,0xFE` + 写回 | **清 bit0** |

---

## 3. 可落地点（禁握手字段 · 仅「启动日志打印 + 强制降级」）

> 政策：不新增任何网络协议/握手字段。混端一致性靠「本端强制降级到原版逻辑面 + 文档禁令」。

| ID | 动作类型 | 落点 | 具体做法 | 闭环 | 风险面 |
|---|---|---|---|---|---|
| **L-1** | 强制降级 | `GetEffectiveTargetScanInterval/Key/MinimapFog` | 已实现（联机 1 / position / false） | G-01/02/08 | L2 节流、指针键、小地图 |
| **L-2** | 强制降级 | `InstallGapProtectionPatch:3214` | 已实现（联机不装 + `forced-off-mp` 日志） | Gap R-1 | Cell+0x134 |
| **L-3** | 强制降级 | `UpdateVisionGrid:1548-1554` | **待补**：`if (!MpActive()) { …S2…; …S3…; }`（或 `MpStateWrites` 键语义由 MpActive 承担） | G-06 / W4+W5 | Scenario / House 序列化 |
| **L-4** | 强制降级 | `PatchSpySatBuildingTypes:1392` | **待补**：入口 `if (MpActive()) return;`（W3）；单机路径补 4 字段备份 + Remove 还原（G-07） | W3 / G-07 | TYPE → SW 充能帧 → v[13] |
| **L-5** | 强制降级 | L2 Retention 短路 | 已由 interval=1 间接禁用；可选补 `EnableThreatRetention` 单机调试键（**联机恒 0**） | G-03 | 寻敌返回值 |
| **L-6** | 启动日志 | `LoadConfig:766-792` | 已有「配置→生效」对照 + `[ra2render-mpgate]` 行；**建议补** W3/W4/W5/L2-Retention 生效位到同一条，形成一张表 | 观测 | — |
| **L-7** | 启动日志 | Gap/Particle/VXL/Audio 安装点 | 每项打 `feature=on\|off\|forced-off-mp` 一行（Gap 已有；particle/vxl/audio 落地时照抄） | 观测 | — |
| **L-8** | 强制降级 | particle / vxl / audio 新卡 | 见 §4：particle/vxl/audio 为纯表现层，**联机可不降级**；若要求观感一致，照 VXL G0.5「L-VXL-2 联机不装」模式 | 观感 | 无 DESYNC |
| **L-9** | 回滚键 | `[Logic] MpAutoDowngrade` / `ForceSinglePlayer` | **待补**（X-2）：总闸与单机强制覆盖；默认 `MpAutoDowngrade=1` | 运维 | 误判回滚 |
| **L-10** | 保守默认 | `MpActive()` `:213-215` | **待补**（X-1）：`__except` 改 `return true`（或返回 AMBIGUOUS 且视同联机） | 检测失败安全 | 误判方向 |

> **明确不做**：不加 `EnableGapProtection`/`EnableSpySatGate` 入握手校验字段（`gap_protection_install_spec.md` §「不采纳」已裁）；不改 `Compute_Frame_CRC 0x64DAB0`；不写 `0xA8D5F8` / 事件环 / RNG。

---

## 4. 混端 DESYNC 风险表（gap / particle / vxl / audio 新卡交叉）

> 「混端」= 本端加载 `ra2render.dll`，对端原版 `gamemd.exe`（无 DLL）。  
> 判定沿用 M-4：SAFE / RISK / VIOLATION。

| 卡 | 补丁/特性 | 触碰面 | 进 `.SAV`/CRC？ | 混端后果 | 判定 | 现网门控 | 可落地点 |
|---|---|---|---|---|---|---|---|
| **gap P-2.1** | `0x568273` 6B NOP（不写 `Cell+0x134`） | `GapsCoveringThisCell` 引用计数 | **进 `.SAV`**；间接主导索敌/可见性谓词 | 第一次 `RevealArea2/3/Reshroud` 后 `+0x134` 分叉 → 索敌/可见性 → 坐标 → **帧 CRC 间接 DESYNC** | **VIOLATION** | `InstallGapProtectionPatch` 联机强制不装 ✓ | L-2（已落） |
| **gap P-2.2/2.3** | `0x577EC5` / `0x577B60` 同上 | 同上 | 同上 | 同上 | **VIOLATION** | 同上（当前实现为整包不装） | L-2 |
| **gap SpySat 门 P-2** | `0x508F8F` je→jmp | 阻 `RevealArea3` 全图开 | 间接（House/Cell 可见性演进） | 一端门一端原版 ⇒ 开图语义分叉 | **VIOLATION** | `EnableSpySatGate` **0 命中**（未落地） | L-4 邻域 |
| **S1 SpySat TYPE** | 写 `SW+0xB0/+0xF8`、`Bld+0x16A5/+0x16F0` | TYPE 规则数据 | TYPE **不进 `.SAV`**，但改充能帧 → `IsCharged/Granted` 进 `v[13]` | 超武发射帧不同 → Checksum 分叉 | **VIOLATION**（混端）/ RISK（全端同 DLL） | **无 MpActive 门** ✗ | L-4 |
| **S2 Scenario 标志** | `ScenarioClass.flags &= ~0x1000` | 可序列化全局 | **进档**（`ScenarioClass`） | 若对端该位演进不同 → 存档/CRC 面分叉 | **RISK→VIOLATION**（混端） | **无门** ✗ | L-3 |
| **S3 House+0x577A** | `SpySatActive=0` | House 字段 | **进档**（`Save_Sides`） | 解除裂缝锁死 = 玩法语义变更；混端分叉 | **RISK→VIOLATION**（混端） | **无门** ✗ | L-3 |
| **L2 节流** | `>>4` 指针键 + interval=8 | 寻敌调用时序 | 间接（目标选择→开火→坐标） | 相位不一致必 desync | **VIOLATION**（interval>1） | 联机强制 interval=1 + position ✓ | L-1 |
| **Threat Retention** | 节流帧 `return pTarget` | 寻敌返回值 | 间接 | 短路相位不一致 → 一端切换一端粘滞 | **RISK**（修键后）/ VIOLATION（指针键） | 绑 interval，联机不可达 ✓ | L-5 |
| **particle M-9** | Particle/PSys 槽 69 Draw 剔除 | 纯绘制虚表 | **否**（不进档/不进 CRC） | **无 DESYNC**；仅烟雾/尾迹可见性观感分叉 | **SAFE** | `EnableParticleFog` **0 命中**（未落地） | L-8（可不降级） |
| **vxl L-VXL-1/3** | 缓存预热 / VXL 影缓存 | 绘制缓存 | **否** | 无 DESYNC | **SAFE** | 未落地 | L-8 |
| **vxl L-VXL-2** | SHP 影强制跳过 | 绘制 | **否** | 无 DESYNC，但脚下影观感分叉 | **SAFE**（观感） | 规格 G0.5：MpActive 时强制不装 | L-8 |
| **audio 限频** | `PlayGlobal@0x750920` / `PlayAt@0x7509E0` 入口丢弃 | 声道池调度 | **否**；Play* 内 **0 次同步 RNG** | **无 DESYNC**；本地少放音 | **SAFE** | `EnableAudioThrottling` **0 命中**（未落地） | L-8（可不降级） |
| **CRT 池 L2** | 高频小对象池化 | 堆布局 | 否（但指针序敏感） | 若引入指针哈希/枚举序 → 分叉；L1 纯复用 SAFE | **RISK**（L2）/ SAFE（L1） | 未落地；规格：联机仅 L1 | L-8 |
| **L4 全量刷 / B1B2 桩** | dirty-rect / 像素混色 | 像素 | 否 | 无 DESYNC | **SAFE** | E2：运行期总闸 | — |
| **雷达×2** | Plot/Pending 像素 | 像素 | 否 | 无 DESYNC；缺陷1 崩溃另论 | **SAFE** | MinimapFog 联机强制 0 ✓ | L-1 |

### 4.1 风险排序（混端视角）

1. **P0 致命**：gap 三处 NOP（`Cell+0x134`）——已被 L-2 联机不装门挡住（安装期）。
2. **P0 致命**：S1 TYPE + S2/S3 状态写——**当前无门，是发布前最大残余**（L-3/L-4）。
3. **P1**：L2 节流/Retention——已被 L-1 强制 interval=1 + position 挡住。
4. **P2 观感**：particle / vxl 影 / audio——纯表现层，无 DESYNC；混端可共存，观感可不一致。
5. **P2 卫生**：G-10 死代码、G-09 everSeen。

### 4.2 「新卡」交叉结论

| 新卡 | 与 MP 门控的关系 | 落地建议 |
|---|---|---|
| **gap_inst**（P-21 安装门禁） | 已对齐 `MpActive` 强制不装模板 | 保持；补运行中升联机不拆/告警（X-5） |
| **part_fog**（粒子迷雾剔除） | 纯 Draw，不进同步契约 | **可联机保留**；无需强制降级 |
| **vxl_cache** | L-VXL-1/3 SAFE；L-VXL-2 观感 | 观感一致要求时 MpActive 不装 L-VXL-2 |
| **audio_limit** | 入口丢弃对 lockstep 安全（0 同步 RNG） | **可联机保留**；默认关更稳 |

---

## 5. 发布门禁读法（不变）

| Gate | 内容 | 状态 |
|---|---|---|
| **Gate1** | R-01 / R-02 / R-03 | **代码层已落地** [实证] |
| **Gate2** | G-03 Retention 键 + G-06 MpStateWrites（S2/S3 旁路）+ W3 SpySat 旁路 | **未闭环** |
| **Gate3** | 真机混联 ≥10 min / ≥5000 帧零 OOS | **未执行** [待实测] |

⇒ **不得宣判「MP 可发布」**。当前唯一安全混端姿势：**本端整局不加载 `ra2render.dll`**，或全员同构建 + 同 `EnableGapProtection`/`EnableSpySatRadarSweep` 开关（且仍需 Gate3）。

---

## 6. 残余动作清单（按优先级）

| 优先级 | 动作 | 对应 |
|---|---|---|
| **P0** | `UpdateVisionGrid` S2/S3 挂 `if (!MpActive())` | L-3 / G-06 / W4+W5 |
| **P0** | `PatchSpySatBuildingTypes` 入口 `if (MpActive()) return` | L-4 / W3 |
| **P1** | S1 TYPE 四字段备份 + Remove 还原 | L-4 / G-07 |
| **P1** | `MpActive()` 异常返回改保守 true | L-10 / X-1 |
| **P1** | 启动日志补 W3/W4/W5/Retention 生效位（一张表） | L-6 |
| **P2** | `MpAutoDowngrade` / `ForceSinglePlayer` 键 | L-9 / X-2 |
| **P2** | `EnableThreatRetention` 单机调试键 | L-5 / G-03 |
| **P2** | particle/vxl/audio 落地时照抄 `forced-off-mp` 日志模板 | L-7/L-8 |
| **P2** | G-10 死代码清理 | 卫生 |

---

## 7. 附录：复算命令

```powershell
python out/re_work/re_sprint/R_mp_gate/scan_sessionflags.py
python out/re_work/re_sprint/R_mp_gate/scan_source_gates.py
```

产物：`sessionflags_xrefs.txt`（52 xref 全表）、`source_gate_census.txt`（源码门控/残键）、`claims.txt`（三档断言）、`EVIDENCE_INDEX.md`。

---

> **台账 §九 草稿**（供 Lead 合并，本任务禁改台账）：
> ```
> ### [R-MP-GATE] - MP 门控残余清点与混端 DESYNC 风险表（全静态）
> #### 1. 现象与需求
> - 联机侧闸门锁闭；需清点 G-01…G-10/M-6 现状 vs 缺口、SessionFlags 门控全表、
>   仅日志+强制降级可落地点、混端 DESYNC 风险（gap/particle/vxl/audio 新卡交叉）。
> #### 2. 逆向调研
> - 0xA8D5F8=NetworkManager+0x6C SessionFlags：bit0=SP/bit1=Net/bit2=ATTRACT；52 xref 复算。
> - 源码 MpActive 门 6 处已落（interval/key/minimap/gap/log）；S2/S3/S1 无旁路。
> - G-01/02/08 闭环；G-03/06/07/10 未闭环；G-04 运行期门控；G-05 源码已接。
> #### 3. 修改
> - 无代码补丁。产出 docs/re/mp_gate_residual_deep_dive.md + R_mp_gate 取证包。
> #### 4. 验证
> - [静态核验] scan_sessionflags 52/52；scan_source_gates 残键 0 命中复核。
> - 混联杀手用例 [待实测]。
> ```
