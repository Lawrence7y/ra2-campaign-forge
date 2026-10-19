# Hook 门控覆盖缺口表（HOOK_GATE_GAP_TABLE）

> 任务：**M-7** · 派工 v11 · 2026-09-26
> 交付目标：一张可直接给 **ZCode** 执行的 gap 表——逐 Hook 覆盖「ini 键 / 默认值 / 是否门控 / MP 判定 / 建议+优先级」
> 强制覆盖：**21 个安装路径** + **v1.6.0 四键**（`EnableBuildingFog` / `EnableBulletFog` / `FadeFogTransition` / `EnableMinimapFog`）+ **L2 三处 `>>4`** + **L4 `0x006D3D99`**
> 写作用域：本文件 + `out/re_work/hook_gate_gap/**`；**只读** `ra2render/**`、`ra2youli/ra2render.*`；不改台账 `REVERSE_ENGINEERING_AND_PATCHES.md`
>
> 证据源（只读快照）：
> | 源 | 版本/规模 |
> |---|---|
> | `ra2render/blitter_hooks.cpp` | ~~**1788 行**（2026-09-26 18:42:48，82,259 B）~~ **【原记】** 派生快照已失效 ⇒ 见 §10.4（E4）：本任务实测现快照 **2346 行 / 117,930 B**（2026-09-27 15:21:17） |
> | `ra2render/ra2render.h` | 266 行（18:26） |
> | `ra2render/ra2render.ini` | 53 行；与 `ra2youli/ra2render.ini` `Compare-Object` **无差异** |
> | `ra2render/dllmain.cpp` | 52 行（安装/卸载生命周期） |
>
> 对照文档：`docs/re/MP_SAFETY_REVIEW.md`（判定图例与 MP 列）、`docs/re/INSTALLED_HOOKS_AUDIT.md`（21 符号清单）、`docs/re/mp_autodowngrade_spec.md`（联机旁路白名单 W1–W6）
>
> 判定图例（**沿用 MP_SAFETY_REVIEW**）：
> - **SAFE** = 纯表现层，不进同步契约，联机锁步下可共存
> - **RISK** = 可能影响同步，需条件验证（全端同构建/同 ini/确定性键/对拍）
> - **VIOLATION** = 现网实现下必导致或高概率 desync
>
> 默认值口径（两列并列，防混淆）：
> - **API 默认** = `GetPrivateProfileIntA/StringA` 第 4 参（键缺失时的回落值），给源码行号
> - **ini 现值** = `ra2render.ini` 实际写入值（部署态），给 ini 行号
> - 两者不一致即缺口（见 §5）
>
> **★ 快照与锚点声明（FOG-ERRATA · 2026-09-27 · 见 §10 / E4）**
> 本表 §0–§9 成文于 `blitter_hooks.cpp` **1788 行**快照；该快照**已失效**：正文中**全部 `:行号` 引用**（含 §9.4 行号对照表）自本版起**不得再作为验收依据**。
> 引用与验收口径改为 **VA / RVA 锚点**：引擎侧用 `gamemd.exe` 的 **VA**（如 B1 `0x0047F40F`、B2 `0x0047F4AE`、L4 `0x006D3D99`），产物件用 **RVA**（如 B1 关闸出口 `RVA 0x21B1`）；行号仅作溯源提示。
> 现快照实测：`blitter_hooks.cpp` **2346 行 / 117,930 B**（2026-09-27 15:21:17，SHA-256 `AC07312974516B01C5B12AEA3F5E624543841DCA3C7DE3C515246C684B66C718`）。

---

## 0. 与旧审计的时点差异（必须先读）

本表以 **18:42 构建**为准。`INSTALLED_HOOKS_AUDIT.md`（1757 行快照）与 `MP_SAFETY_REVIEW.md`（17:18 构建）之后源码已变，下列差异直接影响判定：

| 变化 | 旧文档口径 | 当前源码 | 对缺口表的影响 |
|---|---|---|---|
| **L2 节流键** | 三处 `unitHash = (uintptr_t)pThis >> 4`（指针哈希） | `ThrottleKey()`（`:167-184`）默认 **position 坐标哈希**；指针 `>>4` 仅 `TargetScanKey=pointer` 分支（`:168-169`） | #7/#8/#9 在默认键下从 **VIOLATION → RISK**（待对拍）；pointer 分支仍是 **VIOLATION** |
| **雷达挂钩** | 调用点 `0x006574C3` 等长替换 | **路线 A**：`Plot_Cell` 内部 `0x00655D38` 9 字节补丁 + 跳板（`:1466-1516`） | #20 目标地址改写；`0x6574C3` 仅剩宏 `ADDR_RADAR_PLOT_CALLSITE`（死宏） |
| **`EnableMinimapFog` 默认** | ini / API 均为 1 | API 默认仍 **1**（`:103`）；**ini 现值 = 0**（`ra2render.ini:44`，缺陷1 保守默认） | **API/ini 不一致缺口**（G-01） |　**【F-11 正文级订正 · Lead · 2026-09-27】** 改前证据已过期：`ra2render.ini:45` 现值实为 `EnableMinimapFog=1`（双副本一致，Lead 实测）；缺口应重述为「**键缺失即静默全开**」（API 默认 1），裁定见 `[v1.5.23]`/`[v1.5.37]`（API 默认改 0）。
| **`TargetScanKey`** | 不存在 | 新增（`:90-92`，默认 `"position"`） | 缺陷2 修复键；需联机旁路/文档化 |
| **S2/S3 执行条件** | 旧雷达代理无条件调 `UpdateVisionGrid` → 全键关仍写 | 当前 `UpdateVisionGrid` 调用点仅 4 处绘制路径（`:882/:954/:1003/:1039`），均在 fog 键门控之后；**雷达代理不再调用** | 「全 fog 键=0 时 S2/S3 不执行」成立；但**仍无独立键**可单关状态写 |

---

## 1. 主缺口表 · 21 个安装路径 + S1–S4

> 列定义：① Hook 名 / 目标地址或虚表槽 ② ini 键名（无则「无门控」）+ 默认值（API/ini，行号） ③ 当前是否受门控（源码行号） ④ MP 判定 ⑤ 建议 + 优先级
> 「安装」= `InstallVTableHooks` / `Install*Hook` 中真实写入补丁；「未装」= 符号存在但无安装点。

### 1.1 L1 Blitter 虚表（6）

| # | ① Hook / 目标 | ② ini 键 + 默认值 | ③ 是否门控 | ④ MP | ⑤ 建议 + 优先级 |
|---|---|---|---|---|---|
| 1 | `Hook_BlitTransXlatAlphaZRead`<br>`0x007E56F0+4`（原 `0x494B60`） | `EnableSIMD`<br>API=1 `:65`；ini=1 `:3` | **是**：`g_enableSIMD` 只控 SIMD 快路径（`:210`）；Hook 本体始终安装并累加遥测 | **SAFE** | 保持。可选：`EnableSIMD=0` 时改尾调原版（现为标量等价路径，语义一致）。**P2** |
| 2 | `Hook_BlitTransXlat_G`<br>`0x007E5A20+4`（原 `0x4912B0`） | 同上（共用 `EnableSIMD`） | **是**：`:256` | **SAFE** | 同上。**P2** |
| 3 | `Hook_RLEBlitTransXlat_G`<br>`0x007E55C0+4`（原 `0x4960A0`） | **无门控**（无独立键；不读 `EnableSIMD`） | **否**：`:288-298` 仅遥测 + 尾调原版（审计 A1 空转） | **SAFE**（不生效） | 补功能或 ini 旁路不装（`EnableRLEBlit=0` 时不写虚表）。**P2** |
| 4 | `Hook_BlitTrans_G`<br>`0x007F7BF4+4`（原 `0x7BC890`） | `EnableSIMD` API=1 `:65`；ini=1 `:3` | **是**：`:314` | **SAFE** | 保持。**P2** |
| 5 | `Hook_BlitTransDarken_G`<br>`0x007E59F0+4`（原 `0x492670`） | 同上 | **是**：`:362` | **SAFE** | 保持。**P2** |
| 6 | `Hook_BlitPlain_G`<br>`0x007F7BC4+4`（原 `0x7BC7F0`） | **无门控** | **否**：`:398-413` 自写 `memcpy` 快路径，无键 | **SAFE** | 可接受；如需回滚基线洁净可补 `EnableBlitPlainFast`。**P2** |

> 注：#1/#2/#4/#5 的 SIMD 只是向量快路径开关，关掉后标量路径仍走 Hook 自身（像素语义对齐）；**不是**「卸载补丁」。安装点 `:1623/:1629/:1635/:1641/:1647/:1653`。

### 1.2 L2 寻敌（4，其中 #10 未装）

| # | ① Hook / 目标 | ② ini 键 + 默认值 | ③ 是否门控 | ④ MP | ⑤ 建议 + 优先级 |
|---|---|---|---|---|---|
| 7 | `Hook_Techno_SelectAutoTarget`<br>Techno v[265] `0x007F4D84`（原 `0x6FB010`） | `TargetScanInterval` API=8 钳 1..64 `:61-63`；ini=8 `:8`<br>`TargetScanKey` API=`"position"` `:91-92`；ini=`position` `:52` | **是**（双键）：<br>节流门 `g_targetScanInterval>1` `:438-439`<br>键型 `ThrottleKey` `:436` | **RISK**（默认 position 键，interval>1）<br>**VIOLATION**（`TargetScanKey=pointer`） | ① 联机旁路：强制 `interval=1` 或 `TargetScanKey=position` + 对拍（`mp_autodowngrade` W1）② 禁止联机用 pointer 键（日志红字）③ 保留键+遥测。**P0** |
| 8 | `Hook_Unit_SelectAutoTarget`<br>Unit v[265] `0x007F6094`（原 `0x736CA0`） | 同 #7（共用两键） | **是**：`:457-460` | **RISK** / **VIOLATION**（pointer） | 同 #7（一键同解）。**P0** |
| 9 | `Hook_Techno_Greatest_Threat`<br>**Inline** `0x006F8DF0`（9B `E9 rel32 + NOP×4`） | 同 #7（共用）<br>Target Retention 无独立键 | **部分**：短路受 `interval>1` `:497-498` + 节流帧 `return pTarget` `:500`；**Retention 逻辑本身无键**（`interval=1` 时仍可能…见下） | **RISK**（默认键；返回值替代需对拍）<br>**VIOLATION**（pointer）<br>Retention 单独看 = **RISK** | ① `interval=1` 禁短路 ② 补 `MpThreatRetention=0`/`EnableThreatRetention` 独立键（W2）③ 修键后「同种子目标序列」对拍 ④ `IsBadReadPtr` 移出控制流（`:487/:489`）。**P0**（联机）/**P1**（键） |
| 10 | `Hook_Unit_Greatest_Threat`<br>**未安装**（`:514-516` 仅转发 #9） | 无门控 | **否**（死代码；`ADDR_VTABLE_ENTRY_UNIT_GREATEST_THREAT` 死宏） | **SAFE（不生效）** | 删除或标 deprecated；**勿**按虚表补装（会与 inline 双挂钩）。**P2** |

> **L2 三处 `>>4` 专项**（任务强制覆盖）见 §3。
> 安装点：#7 `:1659`、#8 `:1665`、#9 `InstallGreatestThreatHook :518`（由 `:1703` 调用）。

### 1.3 L3/L5 Draw 剔除（5）

| # | ① Hook / 目标 | ② ini 键 + 默认值 | ③ 是否门控 | ④ MP | ⑤ 建议 + 优先级 |
|---|---|---|---|---|---|
| 11 | `Hook_Unit_Draw`<br>Unit v[69] `0x007F5D84`（原 `0x73CEC0`） | `EnableStarCraftFog`<br>API=1 `:77-78`；ini=1 `:26` | **是**：`g_enableStarCraftFog && !ShouldDrawMobileObject` `:1536` | **SAFE** | 保持（纯表现，允许各端 ini 不同）。**P2** |
| 12 | `Hook_Infantry_Draw`<br>Infantry v[69] `0x007EB16C`（原 `0x518F90`） | 同上 | **是**：`:1548` | **SAFE** | 保持。**P2** |
| 13 | `Hook_Aircraft_Draw`<br>Aircraft v[69] `0x007E23B8`（原 `0x4144B0`） | 同上 | **是**：`:1560` | **SAFE** | 保持。**P2** |
| 14 | `Hook_Building_Draw`<br>Building v[69] `0x007E3FD0`（原 `0x43D290`） | **`EnableBuildingFog`**（v1.6.0）<br>API=1 `:94-95`；ini=1 `:37` | **是**：`g_enableBuildingFog && !ShouldDrawBuilding` `:1572`<br>everSeen 盖章另受同键 `:807` | **SAFE** | 保持。everSeen 不进档（A10）属体验遗留。**P2** |
| 15 | `Hook_Bullet_Draw`<br>Bullet v[69] `0x007E47F8`（原 `0x468090`） | **`EnableBulletFog`**（v1.6.0）<br>API=1 `:97-98`；ini=1 `:39` | **是**：`g_enableBulletFog && !ShouldDrawBullet` `:1583` | **SAFE** | 保持。**P2** |

> 谓词只读对象字段 + DLL 私有网格（`s_visionGrid`/`s_everSeenGrid`），不写引擎状态。
> 安装点 `:1671/:1677/:1683/:1689/:1695`。

### 1.4 L3/L5 CellClass::Draw + 灰雾桩 + L4（4 个补丁点）

| # | ① Hook / 目标 | ② ini 键 + 默认值 | ③ 是否门控 | ④ MP | ⑤ 建议 + 优先级 |
|---|---|---|---|---|---|
| 16 | `Hook_CellClass_Draw`(+`_Proxy`)<br>Inline `0x004801F0`（5B `E9 rel32`） | `EnableStarCraftFog` API=1 `:77`；ini=1 `:26`<br>（`FadeFogTransition` 只控强度，见 #17） | **是**（追加灰雾层）：`if (!g_enableStarCraftFog) return` `:1033`<br>**否**（原版调用）：`:1029-1031` 恒执行 | **SAFE** | 保持。**P2** |
| 17 | `Hook_FogBlendB1_Stub`<br>`0x0047F40F`（49B → `E9`+NOP） | `FadeFogTransition` API=1 `:100-101`；ini=1 `:41`<br>**安装侧无键** | **软门控**：强度 `:1059`（关= s 恒 256 硬切换）<br>**安装无条件**：`:1282-1298` | **SAFE** | 补独立键或随总闸装卸（A6/A7）：建议 `[FogOfWar] EnableFogBlendStubs=1`，~~或 `FadeFogTransition=0` 时不写补丁字节~~ **【原记】**。**P1** <br>**【E1/E2 勘误 · 见 §10.1/§10.2】** ~~原版语义 = 引擎原生 50% 减法~~**【原记】实为 FOG.SHP alpha 插值混色**（`lea ecx,[ecx+edx-0x7f]`）；关闸实施方式改为**运行期门控**（判据 = 关闸三计数恒 0 + 关闸出口反汇编证据）|
| 18 | `Hook_FogBlendB2_Stub`<br>`0x0047F4AE`（51B） | 同 #17 | 同 #17（`:1288-1304`） | **SAFE** | 同 #17。**P1** <br>**【E1/E2 勘误 · 见 §10.1/§10.2】** 同 #17（B2 原版 51B 与 B1 同族 alpha 插值混色）|
| 19 | **L4 视口全量重绘**<br>`0x006D3D99`（6B：`jge`→`E9 99 00 00 00 90` = `jmp 0x006D3E37`） | **无门控** | **否**：`:1307-1313` 无条件打补丁；`EnableStarCraftFog=0` 仍生效 | **SAFE**（dirty-rect 域） | 补 `[Render] L4DirtyMode=force-full\|off`（对齐 Q7/L4 折中）或随 `EnableStarCraftFog` 总闸装卸。**P1** |
> 【W3 勘误 · W3-A6/ISSUE-SECTION-L4DIRTYMODE】改前：[Render] L4DirtyMode；改后：[FogOfWar] L4DirtyMode=force-full；依据：ra2render/blitter_hooks.cpp:757; ra2render/ra2render.ini:251；分级：P0

> 详见 §4 L4 专项。安装/还原：`InstallCellClassDrawHook :1252-1318` / `RemoveCellClassDrawHook :1320-1349`（三点字节备份齐全）。

### 1.5 L5 雷达小地图（2，路线 A）

| # | ① Hook / 目标 | ② ini 键 + 默认值 | ③ 是否门控 | ④ MP | ⑤ 建议 + 优先级 |
|---|---|---|---|---|---|
| 20 | `Hook_RadarPlot_Cell_Proxy`（naked）<br>**路线 A** `0x00655D38`（9B：`E9 rel32 + NOP×4`）<br>跳板还原后 `jmp 0x00655D41` | **`EnableMinimapFog`**（v1.6.0）<br>API=**1** `:103-104`；ini=**0** `:44`<br>汇编镜像 `s_minimapFogGate` `:49,:105` | **是**（汇编门）：`cmp [s_minimapFogGate],0 → je passthrough` `:1379-1380`<br>另有游戏状态门 `:1382-1385`、pCell 护栏 `:1387-1391` | **SAFE**（同步维度）<br>⚠️ 稳定性：缺陷1 路径已加护栏，仍建议联机默认关 | ① **改 API 默认为 0**（与 ini 对齐，防键被删后静默开启）② 联机默认 `EnableMinimapFog=0` 直至 3 局无 except ③ 保持 passthrough 旁路（A9 可接受）。**P0**（默认值）/**P1**（联机策略） |
| 21 | `Hook_RadarPending_Proxy`（naked）<br>调用点 `0x0065719A`（`call 0x660530` 等长） | 同 #20（共用 `EnableMinimapFog` / `s_minimapFogGate`）<br>实际强驱 `s_minimapForceRefresh`（`:849-851`，无键） | **部分**：`:1453` 只看 `s_minimapForceRefresh`；**不看** `s_minimapFogGate` | **SAFE**（只改跳帧返回值 `al`） | ① 补 `s_minimapFogGate==0` 时直接走 `orig_logic`（与 #20 一致）② 或接受（强驱仅视野迁移 10 帧）。**P2** |

> 安装点 `InstallRadarFogHooks :1466-1516` / 还原 `RemoveRadarFogHooks :1518-1531`（两点对称）。
> 事件信标第二调用点 **刻意不动**（基地遭袭标记雾中仍可见）。
> 注：旧 `ADDR_RADAR_PLOT_CALLSITE 0x006574C3`（`ra2render.h:73`）已非安装点，仅为文档宏。

### 1.6 非 Hook 状态改写（S1–S4，门控审计必单列）

| # | ① 动作 / 目标 | ② ini 键 + 默认值 | ③ 是否门控 | ④ MP | ⑤ 建议 + 优先级 |
|---|---|---|---|---|---|
| S1 | `PatchSpySatBuildingTypes`<br>写 `SWType+0xB0`（CD）/`+0xF8`（半径）/`BldType+0x16A5`（关全图 Reveal）/`+0x16F0`（PsychicReveal 索引） | `EnableSpySatRadarSweep` API=1 `:80-81`；ini=1 `:28`<br>`RadarSweepCooldownFrames` API=600≥60 `:83-84`；ini=600 `:30`<br>`RadarSweepRadiusCells` API=16 钳 4..64 `:86-88`；ini=16 `:32` | **是**：入口 `if (!g_enableSpySatRadarSweep) return` `:597`；懒加载 `:740-742` | **RISK**（TYPE 写改超武状态机；混端必分叉） | ① 联机 `EnableSpySatRadarSweep=0` ② 补 Remove 还原（A8）③ 自动降级旁路（W3）。**P1** |
| S2 | `UpdateVisionGrid` 写 `ScenarioClass` 标志 `&= ~0x1000` ~~（每逻辑帧）~~ **【原记】** → **条件写**（仅在该函数被调用时写）：见 §10.3 / E3 | **无独立键**<br>（随 `UpdateVisionGrid` 执行） | **间接门控**：仅当 #11/#12/#13（`EnableStarCraftFog`）或 #14（`EnableBuildingFog`）或 #15（`EnableBulletFog`）任一开启并触达谓词时调用（`:882/:954/:1003/:1039`）；**全 fog 键=0 时不执行**<br>本体写点 `:747-750` | **RISK**（写可序列化全局；常量写，全端同 DLL 才一致） | ① 补 `MpStateWrites=0` 或挂 `EnableSpySatRadarSweep`（W4）② 自动降级 `MpActive()` 旁路 ③ 可选：仅当位非 0 时写 + 遥测。**P1** |
| S3 | `UpdateVisionGrid` 写 `House+0x577A SpySatActive=0` | **无独立键** | 同 S2（载体相同）；写点 `:753` | **RISK**（House 进 `Save_Sides`；改 GapGenerator/SpySat 语义） | 同 S2（W5）。**P1** |
| S4 | 战局重载清 `s_everSeenGrid`/`s_fogRampFrame`/`s_spySatPatched` | 无（自清） | 帧回退检测 `:714-721` | **SAFE**（DLL 私有） | 保持。everSeen 不进档（A10）→ 体验遗留。**P2** |

> **重要修正**（相对 `MP_SAFETY_REVIEW` §2.6 / §4.3）：旧口径称「`Hook_RadarPlot_Proxy:1347` 无条件调 `UpdateVisionGrid` → 全键关仍写 S2/S3」。**路线 A 落地后该调用点已消失**；当前 `UpdateVisionGrid` 仅由 4 处绘制谓词调用且均在 fog 键之后。混联最小集仍须显式关 fog 键 + 落地 W4/W5 旁路，但「只关键、不改码」的残留面比旧审计**更小**。

---

## 2. v1.6.0 四键专项核对（强制覆盖）

| ini 键 | API 默认（行号） | ini 现值（行号） | 生效门控位置 | 挂钩 Hook/补丁 | 关闭后行为 | 回滚 | 遥测 | MP | 验收 | 缺口与建议 |
|---|---|---|---|---|---|---|---|---|---|---|
| **EnableBuildingFog** | 1 `:94-95` | 1 `:37` | `ShouldDrawBuilding` `:1572`；everSeen 盖章 `:807` | #14 | 敌建筑回原版可见；不盖 everSeen | ini=0 软关；`RemoveVTableHooks` 硬还原 | `buildingsCulledByFog` | **SAFE** | 未验收（台账闸门） | 无键缺口。**P2** 保持 |
| **EnableBulletFog** | 1 `:97-98` | 1 `:39` | `ShouldDrawBullet` `:1583` | #15 | 弹道回原版可见 | 同上 | `bulletsCulledByFog` | **SAFE** | 未验收 | 无。**P2** |
| **FadeFogTransition** | 1 `:100-101` | 1 `:41` | 强度 `:1059`；迁移扫描 `:836` | #17/#18（软） | 灰雾硬切换（s=256）；**桩字节仍在** | 软关≠硬关（A7） | 无独立计数 | **SAFE** | 未验收 | **缺口 G-04**：~~关时不还原桩。建议 `FadeFogTransition=0` 时不写 B1/B2 或补 `EnableFogBlendStubs`。~~ **【原记】** ⇒ **改为运行期门控**（本版已落地）：补丁字节照常安装，桩内 `cmp [总闸]/je` 决定是否混色；判据见 §10.2。**P1** |
| **EnableMinimapFog** | **1** `:103-104` | **0** `:44` | `s_minimapFogGate` 汇编 `:1379`（#20）<br>**#21 不看此键** `:1453` | #20/#21 | 小地图原版语义；#20 passthrough | ini=0 软旁路；`RemoveRadarFogHooks` 硬还原 | `s_minimapFogPixels` | **SAFE** | 未验收；缺陷1 需 `=1` 三局证据 | **缺口 G-01（P0）**：API 默认 1 ≠ ini 0，键被删即静默全开。<br>**缺口 G-05（P2）**：#21 未接 gate。建议 API 默认改 0；#21 接 `s_minimapFogGate` |

**跨战局重载**（四键共用）：`:714-721` 帧号大幅回退 → 清 everSeen/渐变/`s_spySatPatched`，`s_minimapForceRefresh=10`。

---

## 3. L2 三处 `>>4` 专项（强制覆盖）

历史缺陷 `[v1.6.0-缺陷2]`：节流键 `unitHash = (uintptr_t)pThis >> 4` 含指针位移 → 跨端不确定 → desync。
当前实现经 `ThrottleKey()` 收敛为**双模键**，三处调用点不变：

| 调用点 | 行号 | 计算 | `TargetScanKey=position`（默认） | `TargetScanKey=pointer` |
|---|---|---|---|---|
| `Hook_Techno_SelectAutoTarget` | `:436` `:438-439` | `(unitHash + CurrentFrame) % interval` | `unitHash = (locX*0x9E3779B1 ^ locY*0x85EBCA77) >> 4`（`:175-179`）；locX/Y=`this+0x9C/0xA0`，**同步契约内** → 跳过判定是 `CurrentFrame` 纯函数 → **RISK**（待对拍） | `unitHash = (uint32_t)(uintptr_t)pThis >> 4`（`:169`）→ **VIOLATION** |
| `Hook_Unit_SelectAutoTarget` | `:457` `:459-460` | 同上 | 同上 | 同上 |
| `Hook_Techno_Greatest_Threat` | `:495` `:497-500` | 同上；节流帧 `return pTarget`（Retention） | 跳过相位一致时各端同返缓存目标（`this+0x5D4` 同步字段）→ 锁步可维持；**返回值替代语义仍需对拍** → **RISK** | **VIOLATION** |

| 项 | 内容 |
|---|---|
| **短路总门** | 三处均为 `if (g_targetScanInterval > 1 && currentFrame > 0)`（`:438/:459/:497`）——`interval=1` 时零补丁全禁 |
| **ini** | `TargetScanInterval` API=8 钳 1..64 `:61-63`；ini=8 `:8`<br>`TargetScanKey` API=`"position"` `:91-92`；ini=`position` `:52` |
| **MP 判定（汇总）** | 默认键 + interval>1：**RISK**；pointer 键：**VIOLATION**；interval=1：**SAFE**（回到原版全量扫描） |
| **建议** | ① **P0 联机旁路**：`MpAutoDowngrade` 落地后强制 `interval=1`（W1）；或维持 position 键 + 双端 `(this,ret,frame)` 对拍<br>② **P0 红线**：联机/混联禁止 `TargetScanKey=pointer`（LoadConfig 检测到 MP 时强制 position 或 interval=1，并红字日志）<br>③ **P1**：Retention 补独立键 `EnableThreatRetention`（W2），便于对拍失败时单关<br>④ **P2**：`IsBadReadPtr` 移出控制流（`:171/:487/:489`） |

---

## 4. L4 `0x006D3D99` 专项（强制覆盖）

| 字段 | 内容 |
|---|---|
| **Hook/补丁名** | 视口全量重绘跳转补丁（无独立 Hook 符号，随 `InstallCellClassDrawHook` 安装） |
| **目标** | `0x006D3D99`：原 6B `0F 8D 98 00 00 00`（`jge 0x006D3E37`）→ `E9 99 00 00 00 90`（`jmp 0x006D3E37`） |
| **源码** | 定义 `:1245-1250`；安装 `:1307-1313`；还原 `:1343-1348`（`s_origTacticalRedrawBytes[6]`） |
| **ini 键** | **无门控** |
| **是否门控** | **否**——无条件打补丁；`EnableStarCraftFog=0` / 全 fog 键=0 仍生效（审计 A6） |
| **MP 判定** | **SAFE**（只改 dirty-rect 重绘范围；不进帧 CRC / 存档 / RNG） |
| **与 Q7 冲突** | 无条件 `jmp` 与 Lead 修订的 L4 折中（恢复 `jge` + `0x006DA7D0` 打脏 + >350 格全屏保底）互斥；落地折中时必须带键 |
| **建议** | 补 **`[Render] L4DirtyMode=force-full\|off\|vision-dirty`**（默认 `force-full` = 现网行为）：<br>· `force-full`：现行 `jmp`<br>· `off`：不写补丁（原版 `jge`）<br>· `vision-dirty`：预留 Q7 折中<br>或最小改法：`EnableStarCraftFog=0` 时不安装本补丁。**优先级 P1** |

---

## 5. 执行缺口表（给 ZCode，四列）

> 排序按优先级。每条可独立开 PR；验收方法只写可勾选判据。

| 缺口 | 建议改动 | 影响面 | 验收方法 |
|---|---|---|---|
| **G-01** `EnableMinimapFog` API 默认 1 ≠ ini 现值 0（键缺失即静默全开，缺陷1 风险） | `GetPrivateProfileIntA(..., 0, ...)`（`:103`）；或 LoadConfig 后 `if (ini 无键) 强制 0`；注释与 `ra2render.h:187` 同步 | 仅默认值；显式 `=1` 不受影响 | 删掉 ini 该键 → 遥测/行为与 `EnableMinimapFog=0` 一致；`LoadConfig` 日志显示 `false` |　**【F-11 正文级订正 · Lead · 2026-09-27】** 改前证据已过期：`ra2render.ini:45` 现值实为 `EnableMinimapFog=1`（双副本一致，Lead 实测）；缺口应重述为「**键缺失即静默全开**」（API 默认 1），裁定见 `[v1.5.23]`/`[v1.5.37]`（API 默认改 0）。
| **G-02** 联机可用 `TargetScanKey=pointer` 回到指针哈希（VIOLATION） | LoadConfig / 每帧门控：检测联机（W1）时强制 `g_targetScanKey=1` 或 `g_targetScanInterval=1`；日志红字 | L2 全路径；混联安全 | 联机会话中改 ini 为 pointer 仍走 position/interval=1；双端 CRC 对拍零差异 |
| **G-03** L2 Retention 无独立键，对拍失败无法单关 | 补 `[Logic] EnableThreatRetention=0/1`（默认 1）；`MpDisableThreatRetention`（W2）接线 | #9 返回值语义 | `EnableThreatRetention=0` 时 #9 恒走原版全图扫描（`totalTargetScans` 增、无 `return pTarget` 短路） |
| **G-04** B1/B2 混色桩 + L4 补丁无独立键，「关迷雾」关不干净（A6/A7） | 补 `[FogOfWar] EnableFogBlendStubs` + `[Render] L4DirtyMode`；~~或 `EnableStarCraftFog=0`/`FadeFogTransition=0` 时不写对应补丁字节~~ **【原记】** ⇒ **改为运行期门控**（见 §10.2 / E2；判据 = 关闸三计数恒 0 + 关闸出口反汇编证据）| 回滚基线洁净；Q7 折中预留 | 全键=0 启动后读 `0x47F40F/0x47F4AE/0x6D3D99` 原字节恢复；`Remove*` 后与无 DLL 基线一致 |
| **G-05** #21 `Hook_RadarPending_Proxy` 不看 `s_minimapFogGate` | `:1453` 前加 `cmp [s_minimapFogGate],0; je orig_logic` | 仅跳帧强驱 10 帧 | `EnableMinimapFog=0` 时 #21 行为与原版 `call 0x660530` 逐帧一致 |
| **G-06** S2/S3 状态写无独立键（混联残留面） | 挂 `MpActive()` 旁路（W4/W5）或新键 `MpStateWrites`；可选挂在 `EnableSpySatRadarSweep` 下 | 同步契约面（Scenario/House） | 联机遥测 `mpDowngraded` 含 W4/W5 位；混联 ≥2 局无 desync |
| **G-07** S1 TYPE 补丁无 Remove 还原（A8） | 存原 `+0xB0/+0xF8/+0x16A5/+0x16F0` 并在 `RemoveVTableHooks` 还原 | 进程内回滚；验收基线 | 同进程内开→关 `EnableSpySatRadarSweep` 后 TYPE 字段恢复 |
| **G-08** `TargetScanInterval` 默认 8 在联机仍开节流（即使 position 键亦为 RISK） | 联机强制 1（W1 `MpThrottleForceInterval`）；或文档+启动日志提示 | L2 性能 vs 安全权衡 | 联机遥测 `g_targetScanInterval==1`；`throttledTargetScans` 不增 |
| **G-09** `EnableMinimapFog=1` 时 everSeen 不进档（A10） | 文档声明；或读档后按 `Scenario` 重建（复杂，P2） | 体验（读档丢侦察记忆） | 读档后敌建筑常驻可见记忆清零（已知行为，不作为 desync） |
| **G-10** `UnlockGameSpeed` 空开关（A3）；RLE 空转（A1）；死符号 #10/死宏（A2/A4/A5） | 清理或标注 deprecated；`ForgeTelemetry.minimapFogPixels` 与 `s_minimapFogPixels` 二选一 | 低（误导审计） | `verify_hooks.py` 死宏计数下降；日志不再出现空开关 |

---

## 6. ini 键全表（当前 14 键，双份一致）

| 节 | 键 | API 默认（源码行） | ini 现值（ini 行） | 管什么 | 影响 |
|---|---|---|---|---|---|
| Render | `EnableSIMD` | 1 `:65` | 1 `:3` | Blit 向量快路径 | #1/#2/#4/#5 |
| Logic | `TargetScanInterval` | 8 钳 1..64 `:61-63` | 8 `:8` | 寻敌节流间隔 | #7/#8/#9 |
| Logic | `TargetScanKey` | `"position"` `:91-92` | `position` `:52` | 节流分片键型 | #7/#8/#9 |
| Speed | `UnlockGameSpeed` | 0 `:68-69` | 0 `:14` | **no-op**（A3） | — |
| System | `EnableLFH` | 1 `:71-72` | 1 `:18` | 低碎片堆 | 进程级 |
| System | `HighPrecisionTimer` | 1 `:74-75` | 1 `:20` | `timeBeginPeriod(1)` | 进程级 |
| FogOfWar | `EnableStarCraftFog` | 1 `:77-78` | 1 `:26` | 机动剔除 + 灰雾层 | #11-#13、#16、S2/S3 载体 |
| FogOfWar | `EnableSpySatRadarSweep` | 1 `:80-81` | 1 `:28` | S1 TYPE 补丁 | S1 |
| FogOfWar | `RadarSweepCooldownFrames` | 600≥60 `:83-84` | 600 `:30` | 超武 CD | S1 |
| FogOfWar | `RadarSweepRadiusCells` | 16 钳 4..64 `:86-88` | 16 `:32` | 扫描半径 | S1 |
| FogOfWar | `EnableBuildingFog` | 1 `:94-95` | 1 `:37` | 建筑三态 | #14 |
| FogOfWar | `EnableBulletFog` | 1 `:97-98` | 1 `:39` | 弹道剔除 | #15 |
| FogOfWar | `FadeFogTransition` | 1 `:100-101` | 1 `:41` | 4 帧渐变 | #17/#18（软） |
| FogOfWar | `EnableMinimapFog` | **1** `:103-104` | **0** `:44` | 小地图灰化 | #20（#21 未接） |

**建议新增键**（落地 G-01…G-06）：`EnableThreatRetention`、`EnableFogBlendStubs`、`L4DirtyMode`、`MpAutoDowngrade`/`ForceSinglePlayer`/`MpStateWrites`（见 `mp_autodowngrade_spec.md` §4.2）。

---

## 7. 台账 §九 草稿（供 Lead 合并）

```
### [v1.5.x] - Hook 门控覆盖缺口表（M-7，纯审计，无补丁）
#### 1. 现象与需求描述
- 逐 Hook 盘点 ini 门控覆盖：21 安装路径 + v1.6.0 四键 + L2 三处节流 + L4 0x6D3D99，
  输出可执行 gap 表供 ZCode 补键/改默认/加联机旁路。
#### 2. 逆向调研与根因剖析
- 证据时点：blitter_hooks.cpp 1788 行（18:42 路线 A 构建）；ini 双份一致。
- 时点差异：TargetScanKey=position 默认（缺陷2 修复）→ L2 默认 RISK、pointer 仍 VIOLATION；
  雷达改 0x00655D38 9B 路线 A；EnableMinimapFog API 默认 1 ≠ ini 0；
  UpdateVisionGrid 不再由雷达路径调用 → 全 fog 键=0 时 S2/S3 不执行。
- 主缺口：G-01 默认值不一致（P0）；G-02 联机可回退 pointer 键（P0）；
  G-03 Retention 无键；G-04 B1/B2+L4 无键；G-05 #21 未接 gate；
  G-06 S2/S3 无独立键；G-07 S1 无还原；G-08 interval 默认 8。
#### 3. 具体修改与补丁实现
- 无代码补丁。产出 docs/re/hook_gate_gap_table.md + out/re_work/hook_gate_gap/**。
#### 4. 实测验证效果
- [静态核验] 行号/ini/安装点逐条对源；联机对拍与真机四键验收仍待 ZCode 证据包。
```

---

## 附录 A · 覆盖率自检

| 强制覆盖项 | 条目 | 落表位置 |
|---|---|---|
| 21 个安装路径 | #1–#21（含 #10 未装） | §1.1–§1.5 |
| v1.6.0 四键 | EnableBuildingFog / EnableBulletFog / FadeFogTransition / EnableMinimapFog | §2（并入 §1.3–§1.5） |
| L2 三处 `>>4` | `:436` / `:457` / `:495`（`ThrottleKey` `:167-184`） | §3 |
| L4 `0x006D3D99` | 6B `jge`→`jmp`，无键 | §4、#19 |
| S1–S4 状态改写 | SpySat TYPE / Scenario / House / 重载清网格 | §1.6 |
| 执行缺口表 | G-01…G-10 四列 | §5 |

## 附录 B · 产出物

| 路径 | 说明 |
|---|---|
| `docs/re/hook_gate_gap_table.md` | 本文档 |
| `out/re_work/hook_gate_gap/evidence_index.md` | 行号/地址/ini 证据索引（自证） |

---

## 8. 附录 · 勘误标记（收尾-C / task-13，2026-09-26）

> **性质**：本附录仅**登记**「正文现状 vs Lead 终局裁决」的差异，**不改动正文**（§1–§7 逐字保持原样，四列缺口表 L174-185 不重写）。
> **权威落点**：`docs/re/mp_release_safety_checklist.md` §一 L19-24（R-01…R-04）+ §三 L60-71（MP-G01…MP-G10）；`docs/re/ARCHITECTURE_ATLAS.md` §9.4 L1530-1544（G-01…G-09 联机安全门控矩阵）；字节级依据 `docs/re/net_sync_checksum.md` §13.3 L844-909。
> **收尾审计全文**：`docs/re/mp_landing_consistency.md`（§2 裁决收敛、§2.3 G-07/G-09 专项结论）。

| 缺口 | 正文现状（行号） | 终局裁决（勘误后口径） | 权威落点 |
|---|---|---|---|
| **G-01** | §2 表 `L38`、§1.4 表 `L129`：把「API 默认仍 **1**、ini 现值 **0**」列为未决缺口 | `EnableMinimapFog` **API 默认强制 0**（P0）；缺口重述为「INI 键被删/安装包漏配时静默全开」，非「API 与 ini 不一致」 | checklist `L21`(R-01)；atlas `L1536` |
| **G-02** | §5 `L177`：「建议…强制 position 或 interval=1」 | **联机强制 `position` 键**（`MpActive()` 为真时禁止回落 `pointer`，日志红字）P0 | checklist `L22`(R-02)；atlas `L1537` |
| **G-03** | §5 `L178`：「补 `[Logic] EnableThreatRetention=0/1`（默认 1）」为**建议** | **采纳**：`[Logic] EnableThreatRetention=1`（单机默认 1、**联机强制 0**），`MpDisableThreatRetention`（W2）接线 P1 | checklist `L64`(MP-G03)；atlas `L1538`；net_sync `L857` |
| **G-04** | §1.4 `L128`、§5 `L179`：建议独立键（`EnableFogBlendStubs` / `L4DirtyMode`）或随总闸 | **定为「接入 `EnableStarCraftFog` 总闸」**：总闸=0 时**不写** `0x47F40F`/`0x47F4AE`/`0x6D3D99` 并逐字节还原原版（B1 49B / B2 51B 原字节见 net_sync `L861-862`，已复核 [实证]）；独立键作补充 P1 <br>**【E2 勘误 · 见 §10.2】** ~~总闸=0 时「不写字节并逐字节还原」为验收判据~~ **【原记】** ⇒ 实施改为**运行期门控**，判据改为「关闸**三计数恒 0** + 关闸出口反汇编证据」| atlas `L1539`；net_sync `L866-868`；checklist `L65` |
| **G-05** | §1.5 表 `L103`、§5 `L180`：缺口「#21 不看 `s_minimapFogGate`」 | **采纳**：`Hook_RadarPending_Proxy` 前置 `cmp byte ptr [s_minimapFogGate], 0; je orig_logic`（`0x0065719A` 入口）P2 | checklist `L24`(R-04)；atlas `L1540` |
| **G-06** | S2 行 `L114`、§5 `L181`：「挂 `MpActive()` 旁路**或**新键 `MpStateWrites`」 | **定为 `[Multiplayer] MpStateWrites=0`**（联机强制阻断 `ScenarioClass` / `House+0x577A` 状态写；`MpActive()` 旁路即其实现）P1 | atlas `L1541`；net_sync `L883`；checklist `L67` |
| **G-07** | §5 `L182`：缺口行 | **采纳**：备份 `SW+0xB0/+0xF8`、`Bld+0x16A5/+0x16F0` 首次写前原值，`RemoveVTableHooks` 尾部 `RestoreSpySatBuildingTypes()` 还原（规格见 `landing_pack_gap_spysat.md` §3）。还原本体**不进同步契约**，S1 写出仍为「全端同 DLL+同 ini」条件面 P1 | checklist `L68`(MP-G07)；atlas `L1542`；net_sync `L885-893`；\docs/re/mp_landing_consistency.md\ §2.3 |
| **G-08** | §3 `L151`、§5 `L183`：「联机强制 1（W1 `MpThrottleForceInterval`）」 | **采纳**：联机环境**无条件**强制 `g_targetScanInterval = 1`（即使 `position` 键亦强制，回归原版逐帧全量扫描）P0 | checklist `L23`(R-03)/`L69`(MP-G08)；atlas `L1543` |
| **G-09** | §5 `L184`：缺口行 | **采纳（维持现状）**：`s_everSeenGrid` 为 DLL 私有 `static uint8_t[512*512]`，不入 `.SAV`、不进 `0x64DAB0` 帧 CRC → 判**体验遗留（读档丢侦察记忆）**，不阻断发布 P2 | checklist `L70`(MP-G09)；atlas `L1544`；net_sync `L895-909`；\docs/re/mp_landing_consistency.md\ §2.3 |
| **G-10** | §5 `L185`：缺口行（`UnlockGameSpeed` 空开关 / RLE 空转 / 死符号 #10 / 死宏） | **采纳**：判 SAFE（卫生项，P2），清理死符号与死宏，遥测字段与汇编镜像二选一；不阻断发布 | checklist `L71`(MP-G10) |

**附注（三条）**

1. **证据勘误（G-01 两方证据已陈旧）**：正文 `L38`/`L129` 记「ini 现值 0（`ra2render.ini:44`）」。工作树实测 `ra2render/ra2render.ini` **第 45 行** `EnableMinimapFog=1`（第 44 行为注释），`ra2youli/ra2render.ini` 字节相同；源码 `blitter_hooks.cpp:103` 默认参数仍为 `1` [实证]。→ G-01 缺口收敛为「**API 默认 1 + 键缺失/漏配即静默全开**」，R-01（默认改 0）**仍必需且优先级不变**。
2. **§6「ini 键全表（当前 14 键）」需补键**：正文 `L208` 已列「建议新增键」，终局键名与默认值以 `ARCHITECTURE_ATLAS.md` §9.4 为唯一口径：`EnableMinimapFog=0`(API 默认)、`TargetScanKey=position`(MP 强制)、`EnableThreatRetention=1`(MP 强制 0)、`EnableStarCraftFog=1`(总闸)、`MpStateWrites=0`、`MpThrottleForceInterval=1`、`RestoreTypeOffsets`(G-07)、`MinimapEverSeenNotice`(G-09)。
3. **未决措辞归零**：正文中所有「建议 / 或 / 二选一」形态（`L129`、`L177-181`、`L208`）自本附录起一律以 checklist §一/§三 与 atlas §9.4 的**单一裁决**为准；正文保留原文仅为审计痕迹，**不再作为落地依据**。

---

## 9. 勘误 · MPS 落地后的状态同步（DA1 · DSH 子代理 · 2026-09-27）

> **性质**：仅**登记**「正文（§0–§8 = M-7 快照）→ MPS 落地快照」的差异，**不改动正文任何一行**（L1-277 逐字保留）。
> **双快照口径**：正文 = `ra2render/blitter_hooks.cpp` **1788 行**（2026-09-26 18:42:48，82,259 B）；本附录 = **1892 行 / 86,961 B**（2026-09-27 09:06:28，mtime 实测）。
> **基线（只读未变）**：`ra2youli/gamemd.exe` 4,825,360 B，MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`；本任务实跑 `python tools/verify_anchors.py` = **断言总数 323 条 / PASS 323 (100.00%) / FAIL 0 / NOREAD 0**。
> **部署件（本附录依据）**：`ra2render/ra2render.dll` ≡ `ra2youli/ra2render.dll` = 129,536 B，SHA-256 `E7FA669C85B5DA53C71898DC453AC35301EC55F1222D1D581BFAEAC105DCC7CA`（MD5 `4A8BE46D3D761DEB607EBF1680B1B0E5`）；`ra2render/ra2render.ini` ≡ `ra2youli/ra2render.ini` = 2,996 B / 53 行，SHA-256 `564A265291C3C6CAF0E15CE8CFF00360A0BBD28EAF2E57BA74D1E0E49C0EC64F`（MD5 `0B239E604546CBEF77F70DB31E86C048`）。
> **DLL 同代实证**：部署 DLL 内 UTF-8 明文含门控日志格式串「门控: MpActive=%s, TargetScanKey=配置(」（file_off `0x16184`）与「(Plot_Cell 0x00655D38 9 」（file_off `0x16812`）⇒ 部署件即 MPS + 路线 A 同代构建；同时 grep 该 DLL **不含** `EnableThreatRetention` / `MpStateWrites` / `L4DirtyMode` 字面（G-03/G-04/G-06 未落地之旁证）。探针脚本 `out/re_work/da1/probe_dll_strings2.py`。

### 9.1 G-01 / G-02 / G-08：**已落地（MPS，2026-09-27）**（正文缺口口径作废）

| 缺口 | 正文原表述（行号） | 更正表述（现网事实） | 实现位置（源码行） | 验证方式（可复算） |
|---|---|---|---|---|
| **G-01** | §2 表 `L129`「**缺口 G-01（P0）**：API 默认 1 ≠ ini 0，键被删即静默全开」；§5 `L176`「`EnableMinimapFog` API 默认 1 ≠ ini 现值 0…」；§1.4/#20 `L102`「API=**1** `:103-104`」；§6 `L206`；§7 `L222`；附录 `L263` | **已落地**：API 默认值 `1 → 0`（`GetPrivateProfileIntA("FogOfWar", "EnableMinimapFog", 0, iniPath)`）；静态初值 `g_enableMinimapFog = false`；两份 ini 显式 `EnableMinimapFog=0`（键位由旧口径 `:44`/`:45` 移至 **:46**）。**用户决策（2026-09-27）**：保持默认关 ⇒ 统一口径为「**默认关闭，需显式 `=1` 才启用**」；且**联机（MpActive）下保守强制关闭**（联机分支恒 `eff = false`） | `blitter_hooks.cpp:182`（ini 默认值）、`:16`（静态初值）、`:96-106`（`GetEffectiveMinimapFog()`，`:100` 联机强制 false）、`:49`/`:104`（汇编侧镜像 `s_minimapFogGate`）；ini `ra2render/ra2render.ini:46` ≡ `ra2youli/ra2render.ini:46` | ① 源码行；② 门控日志自证行 `:201`（含 `EnableMinimapFog=配置(%d)->生效(%d)`）；③ DLL SHA-256 见上；④ `verify_anchors.py` 323/323 |
| **G-02** | §5 `L177`「**建议**① 联机旁路：强制 `interval=1` 或 `TargetScanKey=position`（`mp_autodowngrade` W1）」；§3 `L151` 建议①/②；附录 `L264` | **已落地**：`GetEffectiveTargetScanKey()` 在 `MpActive()` 为真时无条件返回 `1`（position）；单机回落 ini 配置。红字告警两处：状态迁移期与启动期 | `blitter_hooks.cpp:89-94`（`:91` 联机 `return 1`；`:93` 单机回落）；告警 `:129-131`（`CheckMpGateTransition`）/ `:209-211`（`LoadConfig`）；调用点 `:265`（`ThrottleKey`）；ini `:51` `TargetScanKey=position` | ① 源码行；② 门控日志 `:201` 的 `TargetScanKey=配置(%s)->生效(%s)` 对照段；③ 红字告警原文含「强制覆盖 TargetScanKey: 配置(pointer) -> 生效(position)」 |
| **G-08** | §3 `L151`「① **P0 联机旁路**：…强制 `interval=1`（W1）」为**建议**；§5 `L183` 缺口行；§7 `L226` | **已落地**：`GetEffectiveTargetScanInterval()` 联机返回 `1`（禁用节流，回原版逐帧全量扫描），单机回落 `g_targetScanInterval`；三处节流调用点已全部改用该函数 | `blitter_hooks.cpp:82-87`（`:84` 联机 `return 1`）；调用点 `:536`（Techno SelectAutoTarget）/ `:558`（Unit SelectAutoTarget）/ `:597`（Greatest_Threat）；短路条件 `interval > 1 && currentFrame > 0` @ `:537` / `:559` / `:598` | 联机时 `interval == 1` ⇒ 三条短路分支恒不进入 ⇒ `throttledTargetScans` 不增（2s 遥测日志 `:241` 的「节流率」恒 0.0%） |

> **附录 附注 1（正文 `L276`）的二次订正**：附注 1 记「工作树实测 `ra2render/ra2render.ini` **第 45 行** `EnableMinimapFog=1`…源码 `blitter_hooks.cpp:103` 默认参数仍为 `1` [实证]」——该证据**已于 2026-09-27 09:06 快照失效**：ini 现为 `:46 = 0`（双副本**同 SHA-256**），源码默认参数已改为 0 @ `:182`。⇒ 本 §9.1 的 G-01 行**取代**附录 附注 1；R-01 的状态由「**仍必需且优先级不变（P0 缺口）**」更正为「**已落地（API 默认 + 双份 ini 均为 0）/ 待真机验收**」。

> **残留面（三项共有，不因落地而消失）**：① ini 文件本身**不回写**——显式 `pointer` 只被运行期强制纠正并告警（`:129-131`/`:209-211`），落盘值仍为 `pointer`；② 门控依赖 `MpActive()`（`:61-80`，主判定 `*(uint8_t*)0x00A8D5F8 & 0x02`，辅判 `*(int32_t*)0x00AA0444 == 2`）——`IsBadReadPtr` 守卫失败即回落 `false`（安全但等于放行单机语义），且 `ForceSinglePlayer` 逃生舱**未实现**（grep 0 命中）；③ `CheckMpGateTransition()`（`:108-133`）为**惰性求值**（状态迁移时才重算并打日志），非每帧重算。

### 9.2 G-05：源码实证**已接门控**（额外发现，**不在 Lead 本批三项清单内**，待裁决）

| 缺口 | 正文原表述（行号） | 源码实证（本次复核） | 判定 |
|---|---|---|---|
| **G-05** #21 未接 `s_minimapFogGate` | §1.5 `L103`「**#21 不看此键** `:1453`」；§5 `L180` 缺口行；§2 表 `L129`「缺口 G-05（P2）」；附录 `L267`（终局裁决 R-04 采纳） | `Hook_RadarPending_Proxy`（`:1553-1568`）首两条指令即 `cmp byte ptr [s_minimapFogGate], 0` + `je orig_logic`；关闭态走原版 `mov eax, 0x00B04DB8 / mov eax,[eax] / test eax,eax / sete al / ret` | **R-04 已在源码实现**。但 Lead 任务卡 DA1 只点名 G-01/G-02/G-08，**本表不擅自把 G-05 记为「已落地」**，仅登记事实并交 Lead 裁决（见交付回报 [9] 待裁决项） |

### 9.3 G-03 / G-04 / G-06 / G-07 / G-10：**维持未落地**（逐项现状核对）

| 缺口 | 正文行号 | 现网现状（1892 行快照，全源码 + DLL 字面 grep 复核） | 判定 |
|---|---|---|---|
| **G-03** `EnableThreatRetention` | §5 `L178`；附录 `L265`（终局裁决「采纳，P1」） | 全库 grep `ThreatRetention` = **0 命中**（源码与 ini 均无）；Retention 短路仍绑 `interval`（`:598-603`，节流帧 `return pTarget`） | **未落地** |
| **G-04** `EnableFogBlendStubs` / `L4DirtyMode` | §1.4 `L128`、`L179`；§4 `L163`；附录 `L266`（定为接入 `EnableStarCraftFog` 总闸） | grep `EnableFogBlendStubs` / `L4DirtyMode` = **0 命中**（源码 + DLL + ini）；B1/B2 混色桩与 L4 补丁仍在 `InstallCellClassDrawHook`（`:1354-1421`）内**无条件安装**；`g_enableStarCraftFog` 仅短路灰雾层追加（`:1135`），不撤销桩字节 | ~~**未落地**~~ **【原记】** ⇒ **本行口径已被 §10.2（E2）取代**：现网部署 DLL（135,680 B / MD5 `491C25F9DE72E6A5EB3484E4CF154DA3`）B1/B2/L4 桩内**均已带总闸运行期门控**（关闸 `je` 目标 RVA `0x21B1`/`0x2251`/`0x22D2`，关闸出口无反汇编可见的像素写；计数 `inc` 位于 `je` 之后）；本行「未落地」对应 129,536 B 旧 DLL 快照。**真机「三计数恒 0」仍为 `[待实测]`** |
| **G-06** `[Multiplayer] MpStateWrites=0` | S2 行 `L114`；S3 行 `L115`；§5 `L181`；附录 `L268` | grep `MpStateWrites` = **0 命中**；`UpdateVisionGrid()` 仍每帧写 `ScenarioClass` 标志（`:851` `&= ~0x1000u`，基址宏 `ADDR_SCENARIO_INSTANCE` `:849`）与 `House+0x577A`（`:855`），**无 `MpActive()` 旁路** | **未落地** |
| **G-07** `RestoreTypeOffsets` | §5 `L182`；§1.6 S1 行 `L113`；附录 `L269` | grep `RestoreSpySat` = **0 命中**；`PatchSpySatBuildingTypes`（`:697-756`，懒加载调用 `:842-844`）只写不备份原值；`RemoveVTableHooks`（`:1816-1891`）无 TYPE 还原调用 | **未落地** |
| **G-10** 死代码/死宏/空开关卫生 | §5 `L185`；附录 `L272` | 未清理：死符号 `Hook_Unit_Greatest_Threat`（`:615-617`）+ 头声明（`ra2render.h:250`）；`EnforceGameSpeedUnlock` 空函数（`:284-287`）且 `dllmain.cpp:31-36` 不调用；死宏 `ADDR_RADAR_PLOT_CALLSITE`（`ra2render.h:77`） | **未落地**（SAFE 卫生项，P2） |

### 9.4 行号对照（正文自述行号 → 当前快照实测行号）

> 旧行号取自正文自述；新行号为本快照**实测**。中间插行（MPS 门控三函数 `:61-133` 等）导致整体下移，故一并给出对象名以便交叉核对。

| 对象 | 正文自述行号 | 当前快照行号 |
|---|---|---|
| G-01 ini 默认值（`GetPrivateProfileIntA`） | `:103` | **`:182`** |
| G-01 汇编侧镜像 `s_minimapFogGate` | `:49,:105` | `:49` / `:104` |
| `ThrottleKey()` 定义 | `:167-184` | **`:264-282`** |
| 三处节流 `ThrottleKey()` 调用 | `:436` / `:457` / `:495` | **`:534` / `:556` / `:595`** |
| 三处短路总门 `interval > 1 && currentFrame > 0` | `:438` / `:459` / `:497` | **`:537` / `:559` / `:598`** |
| `UpdateVisionGrid` 四调用点（全 fog 键门控之后） | `:882` / `:954` / `:1003` / `:1039` | **`:984` / `:1056` / `:1105` / `:1141`** |
| `PatchSpySatBuildingTypes` | `:564-623` | **`:697-756`** |
| S2 `ScenarioClass` 写点 / S3 `House+0x577A` 写点 | `:747-750` / `:753` | **`:851` / `:855`** |
| 战局重载清网格（S4） | `:682-689` / `:714-721` | **`:816-823`** |
| `s_minimapForceRefresh=10` | `:849-851` | **`:950-951`** |
| #20 汇编门 `cmp [s_minimapFogGate],0` | `:1379-1380` | **`:1481-1482`** |
| #21 门控 | `:1453`（未接门） | **`:1555-1556`（已接门）** |
| `InstallRadarFogHooks` / `RemoveRadarFogHooks` | `:1466-1516` / `:1518-1531` | **`:1570-1620` / `:1622-1635`** |
| 源文件规模（题头 `L11`） | 1788 行 / 82,259 B | **1892 行 / 86,961 B** |
| 安装点清单（`:1623/:1629/…/:1703`、`:1659/:1665`、`:1671/:1677/…`） | 见 §1.1/§1.2/§1.3 注 | 现网：Blit 六槽 `:1727-1757`；节流两槽 `:1763/:1769`；Draw 五槽 `:1775-1799`；`InstallCellClassDrawHook` `:1804`、`InstallGreatestThreatHook` `:1807`、`InstallRadarFogHooks` `:1810` |

> **本节结论**：G-01/G-02/G-08 的三条**P0 缺口在代码层已闭合**（默认值 + 联机强制 + 日志自证齐备），其唯一剩余动作是**真机联机验收**（≥3 局双端帧 CRC 对拍，`[待实测]`）；G-03/~~G-04~~/G-06/G-07/G-10 **维持未落地**（**【E2 勘误 · 见 §10.2】** ~~G-04 未落地~~**【原记】**现网已改为**运行期门控**且见诸 135,680 B 部署 DLL；判据随之更新）；G-05 源码侧已实现但**未经 Lead 裁入清单**。用户决策「`EnableMinimapFog` 保持默认关」已在 `:16`/`:182`/ini `:46` 三处一致落地。

---

## 10. 勘误 · FOG-ERRATA 就地订正（E1–E4 · DSH 子代理 · 2026-09-27）

> **标注约定（F4 自查口径）**：本节整体即**勘误块**；节内凡出现被推翻措辞者，必带 **【原记】**（引文）或 **【原记·反证】**（证据/计数）标注，**不存在无标注的独立残留**。
> **性质**：本节对 §0–§9 的 **4 类误述**做最小就地订正。正文（§0–§9）**逐字保留**：被推翻的措辞已在原页就地加 ~~删除线~~ 与 **【原记】** 前缀，订正口径集中在本节。
> **依据**：FOG-SWITCH 定谳 + **本任务独立反汇编复核**（capstone 5.0.7；脚本/产物见 `out/re_work/fog_errata/**`）。凡本任务复算与该清单不一致者，以本任务独立结果为准 —— 本批**无**不一致项。
> **快照（E4 强制声明）**：正文 = `blitter_hooks.cpp` **1788 行** / 82,259 B（2026-09-26 18:42:48）；本节实测 = **2346 行 / 117,930 B**（2026-09-27 15:21:17，SHA-256 `AC07312974516B01C5B12AEA3F5E624543841DCA3C7DE3C515246C684B66C718`）。**正文 `:行号` 全部失效**，改以 VA/RVA 锚点引用（§10.4）。
> **基线（只读未变）**：`ra2youli/gamemd.exe` 4,825,360 B / MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`；`python tools/verify_anchors.py` = **323/323 PASS**；`python tools/audit_bytes.py out/re_work/fog_errata/claims.txt` = **7/7 OK**。
> **产物件（本节独立实测，只读）**：`ra2render/ra2render.dll` ≡ `ra2youli/ra2render.dll` = 135,680 B / MD5 `491C25F9DE72E6A5EB3484E4CF154DA3`（2026-09-27 15:21:25）；`ra2render/ra2render.ini` ≡ `ra2youli/ra2render.ini` = 7,001 B / SHA-256 `0DAD9A41B2032EB7E61910C5E7DE4234F72BD646313CFB96A0C4130307E4A8C0`。

### 10.1 E1（产品决策级）· B1/B2 原版语义 = FOG.SHP alpha 插值混色（~~「引擎原生 50% 减法」~~ **【原记】不成立**）

| 项 | 内容 |
|---|---|
| **涉及位置** | §1.4 #17/#18（`0x0047F40F` / `0x0047F4AE`）、§2 表 `FadeFogTransition` 行、G-04；即本表任何 ~~「B1/B2 替代引擎原生 50% 减法」~~ **【原记】** 形态表述 |
| ~~改前口径~~ **【原记】** | ~~混色桩 B1/B2「替代引擎原生 **50% 减法**」~~（历史措辞；【原记】引文出自 FOG-SWITCH 勘误清单 E1 与旧源码注释。**本文现行快照已不含该串**，见下「全篇排查」） |
| **订正口径【原记·反证】** | 两桩替代的是引擎原版 **FOG.SHP 逐像素 alpha 插值混色**：`mov cx,[eax]`（读目标像素）→ `cmp cx,0x7f` → `and ecx,0xFFFF` / `and edx,0xFF`（取 alpha 字节）→ **`lea ecx,[ecx+edx-0x7f]`**（以 `0x7f` 为中性点的插值）→ `test/setle/dec/and` 负值钳零 → `mov [eax],cx`。**不含任何固定 50% 半化算子**。 |
| **独立证据【原记·反证】（本任务自跑，未采信他方）** | ① **B1** 49B @ VA `0x0047F40F`（FileOffset `0x07F40F`）、**B2** 51B @ VA `0x0047F4AE`（`0x07F4AE`）逐条反汇编如上形态（B2 仅 `dst==0x7f` 分支写法不同）。<br>② **全 exe `and reg,0x7BEF` = 0 处**：`.text` 全段（4,063,232 B / 覆盖 100.00%）稳健 resync 线性反汇编 **1,394,120** 条指令，其中 `and reg32,imm32` 形态 6,411 条（证明扫描确实覆盖该族），而 **imm == `0x7BEF` 的指令 0 条**；全文件原始字节 `EF 7B` 仅 2 处命中，均在 `.data`（`0x82FC1A` / `0x8748AD`），**非指令流**。<br>③ 反证：**我方桩内确有** 50% 等价算子（`and ecx,0x7bef` @ 产物 RVA `0x2145` / `0x21E5`）⇒「50%」是**我方桩** `s=256` 时的等效观感。 |
| **理由【原记·反证】** | 引擎不存在「~~原生 50% 减法~~**【原记】**」这一算子；该说法把我方桩的**等效观感**误挂到引擎原版行为上。 |
| **影响面【原记·反证】（产品决策）** | 「关闸不得落回 ~~引擎原生 50%~~ **【原记】**」被**更强满足**：关闸出口既不经过原版 alpha 插值混色、也不经过任何 50% 掩码 ⇒ 目标更强成立；**判定结论不变**，验收判据按 §10.2 更新。 |
| **本文全篇排查【原记·反证】** | 本文现行快照 grep：`50% 减法` = **0**、`50% 半化` = **0**、`减法` = **0**、`原生` = **0**、`0x7BEF` = **0** 命中 ⇒ 本文**已无独立残留**（逐行输出见 `out/re_work/fog_errata/f4_grep_selfcheck.txt`）。 |

> **附带独立复算【原记·反证】（与 `docs/RE_COORDINATION.md:1490` 交叉一致）**：全 exe FOG.SHP 压降**落像素点仅 3 处** = `0x47F43D`（B1）、`0x47F4BB` 与 `0x47F4DE`（B2），与本任务反汇编逐条吻合（`66 89 08` / `66 89 10`）⇒ **短路两桩即「彻底无压暗」**。
>
> **E1 域外残留【原记·反证】（不在本任务写作用域，交 Lead 处置）**：同一 ~~「引擎原生 50% 减半」~~**【原记】**口径仍存活于
> ① 【原记】（勘误前曾存在于源码注释）`ra2render/blitter_hooks.cpp`：~~`:50`「灰雾混色强度：256=原生 50% 减半」、`:1302`「256 = 原生 50% 减半（稳态）」、`:1331`（同句式）~~ —— **【FOG-COMMENT 已订正 · 2026-09-27】**：该 6 行（`50/1302/1331/1368/1371/1592`）已改为「256 = **我方** 50% 等效观感（引擎原版为 FOG.SHP alpha 插值混色，非固定半化）」；改后源码 `50% 减半`/`原生 50%`/`减半` 三词**均 0 命中**，且**未重编译**（两 DLL MD5 仍 `491C25F9…`）。注 `:1368`/`:1371`/`:1592` 原有括注「语义另论」已被本次**统一口径覆盖**（LD 附录 R3）。
> ② `docs/RE_COORDINATION.md:1467` 的「③ 混色桩不介入且不落回 ~~引擎原生 50%~~**【原记】**」为**改前口径** —— **Lead 已于同文件 `:1489` 落「★更正（产品决策级）」**（结论与本节 E1 一致：原版 = FOG.SHP alpha 插值混色；全 exe `and reg,0x7BEF` 0 次）⇒ **该文档侧已无待处理项**。
> ⇒ **E1 域外残留（源码注释）已由 `FOG-COMMENT` 订正归零** 〔2026-09-27〕；**剩余项仅** `ra2youli/ra2render.ini:37` 与 `ra2render/ra2render.ini:37` 的注释「不是恢复引擎原生 50%」（**推迟至 ZC-4 会话结束后**再改，以免污染其在跑的真机 A/B 与结尾哈希还原校验）。

### 10.2 E2 · G-04 实施方式：安装期条件化 → **运行期门控**（判据随之更新）

| 项 | 内容 |
|---|---|
| **涉及位置** | §1.4 #17 ⑤、§2 表 `FadeFogTransition` 行、§5 G-04 行、§9.3 G-04 行（四处已就地标注） |
| ~~改前口径~~ **【原记】** | ~~「`EnableStarCraftFog=0`/`FadeFogTransition=0` 时**不写**对应补丁字节」（安装期条件化）；验收 = 「全键=0 启动后读 `0x47F40F/0x47F4AE/0x6D3D99` 原字节恢复」~~ |
| **订正口径** | 改为**运行期门控**（FOG-SWITCH 本版已落地）：补丁字节**照常安装**，桩内 `cmp [总闸] / je` 决定是否混色 / 是否驱动；**关闸出口不经过任何写像素或写状态指令**。 |
| **判据更新（本任务强制）** | 由「关闸后原字节恢复」改为：**① 关闸时「三计数恒 0」**（半透明层绘制次数 / 混色桩介入次数 / 小地图减暗驱动次数；连续两行遥测均为 0）**+ ② 关闸出口反汇编证据**。注：**字节恢复判据不再适用** —— 补丁字节在开/关闸两种状态下都常驻，属设计如此。 |
| **独立证据（本任务自跑，DLL 只读）** | DLL MD5 `491C25F9DE72E6A5EB3484E4CF154DA3`：<br>· **B1 桩** @ RVA `0x2120`：`80 3D 23 10 02 10 00` = `cmp byte ptr [0x10021023],0`（总闸镜像）；`0F 84 84 00 00 00` = `je 0x100021B1`；**关闸出口 RVA `0x21B1` = `B9 40 F4 47 00 FF E1`（`mov ecx,0x47F440; jmp ecx`）** —— 出口前无像素写，且计数 `inc dword ptr [0x102E1A3C]` 位于 `je` **之后**（关闸不增）。<br>· **B2 桩** @ RVA `0x21C0` 同构：`je 0x10002251`，出口 RVA `0x2251` = `B9 E1 F4 47 00 FF E1`（`mov ecx,0x47F4E1; jmp ecx`）。<br>· **L4 桩** @ RVA `0x22C1`：`cmp` / `je 0x100022D2` → 关闸侧 `popfd; jge 0x100022DC; mov ecx,0x6D3D9F; jmp ecx`（回原版 `jge` 后继）。<br>原文见 `out/re_work/fog_errata/f3c_dll_gate_exit_disasm.txt`；源码侧三计数符号 `s_fogLayerDraws / s_fogBlendStubHits / s_radarDarkenDriven` 与遥测行 `[ra2render-fogswitch] 总闸三计数` 存在。 |
| **影响面** | 实施方式与**验收判据**变更；关闸语义（产品决策）不变。§9.3 该行「未落地」对应 `129,536 B` 旧 DLL 快照，现网运行期门控为独立复核所见事实；**真机三计数恒 0 未跑**（本任务禁跑游戏）⇒ `[待实测]`。 |

### 10.3 E3 · S2「每逻辑帧写」→ **条件写**

| 项 | 内容 |
|---|---|
| **涉及位置** | §1.6 S2 行（已就地标注）；S3 行同源（载体相同） |
| ~~改前口径~~ **【原记】** | ~~S2「`UpdateVisionGrid` **每逻辑帧**写 `ScenarioClass &= ~0x1000`」~~ |
| **订正口径** | **条件写**：仅在该函数**被调用**时才写。调用者 = `Hook_CellClass_Draw`（受**总闸**门控）+ `ShouldDrawMobileObject` / `ShouldDrawBuilding` / `ShouldDrawBullet`（受**各自子键**门控）。⇒ **总闸=0 时**：只要 `EnableBuildingFog` 或 `EnableBulletFog` 任一为 1（默认值），该写**仍执行**；**三者全 0 时**我方不再写该位。 |
| **证据锚点** | 现快照 `blitter_hooks.cpp`（2346 行）：函数定义 `:945`；调用点 `:1123` / `:1195` / `:1244` / `:1287`（4 处，均在对应 fog 键门控之后）；写点 `:990`（`scenarioBase &= ~0x1000u`）。行号仅作溯源（见 §10.4），权威锚点为上述**函数名 + VA/RVA**。 |
| **影响面** | 只影响「关总闸是否零干预」的**表述**；产品决策不变（像素级判据由 B1/B2 + L4 短路保证，见 §10.2）。 |

### 10.4 E4 · 行号引用失效 → **VA/RVA 锚点**

| 项 | 内容 |
|---|---|
| **涉及位置** | 本文全篇 `:行号`（§0 表、§1.x、§3、§7、§9.4 对照表） |
| ~~改前口径~~ **【原记】** | ~~以「`blitter_hooks.cpp` **1788 行** / 82,259 B」为快照，正文以 `:行号` 作引用与验收依据~~ |
| **订正口径** | 本任务实测现快照 **2346 行 / 117,930 B**（2026-09-27 15:21:17）⇒ 正文全部 `:行号` **失效**（任务卡「2280+ 行」口径方向一致）；引用与验收一律改用 **VA（引擎侧）/ RVA（产物件）** 锚点，行号仅作溯源提示。 |

| 对象 | VA / RVA 锚点（权威） | 正文旧行号（仅溯源） |
|---|---|---|
| B1 混色桩原版区 | VA `0x0047F40F`（49B，FileOffset `0x07F40F`） | #17 `0x0047F40F` |
| B2 混色桩原版区 | VA `0x0047F4AE`（51B，FileOffset `0x07F4AE`） | #18 `0x0047F4AE` |
| B1/B2 关闸出口（产物件） | RVA `0x21B1` / `0x2251` | `:1379-1380` 式行号 |
| L4 全量重绘补丁点 | VA `0x006D3D99`（6B `jge`→`jmp`）；桩 RVA `0x22C1` | §4、#19 |
| CellClass::Draw 挂钩点 | VA `0x004801F0`（5B `E9 rel32`）；引擎 FogOfWar 位门 VA `0x00480251` | #16 |
| 雷达挂钩点（路线 A） | VA `0x00655D38`（9B）；VA `0x0065719A`（5B `call`） | #20 / #21 |
| 总闸镜像 / 混色强度（产物件） | RVA `0x21023`（byte 总闸镜像）/ `0x21020`（word 强度） | §2 表 |
| S2 / S3 状态写点 | 符号 `UpdateVisionGrid`（定义 `:945`、调用 `:1123/:1195/:1244/:1287`、写点 `:990`） | S2 / S3 行 |

> **附注（两条）**
> 1. **§0–§9 未被改写**：本次订正只在原页加 ~~删除线~~ + **【原记】** + 指路标，并把口径集中到本节；§8/§9 既有登记原样保留（其内部被本版取代的措辞已就地标注）。
> 2. **快照行数测量口径提醒（实测坑）**：对同一文件，PowerShell `(Get-Content f).Count` = **2166**、`Get-Content f | Measure-Object -Line` = **1890**，而 `[IO.File]::ReadAllLines(f).Length` = **2346**、`cmd find /c /v ""` = **2346**、python `LF` 计数 = **2346**（三法一致）。⇒ 后续快照声明一律用 **LF 计数 + SHA-256**，禁用 PowerShell `.Count`。
