# 已装 Hook 静态审计（INSTALLED_HOOKS_AUDIT）

> 任务：M-2 / Q3 · 静态审计 `ra2render` 现网已装 Hook
> 证据时点：源码 `ra2render/blitter_hooks.cpp`（1757 行）+ `ra2render.h` + `ra2render.ini`（`ra2youli/ra2render.ini` 经 `fc` 比对无差异）
> 红线：**只读** `ra2render/**`、`ra2youli/ra2render.*`；不改台账 `REVERSE_ENGINEERING_AND_PATCHES.md`
> 自证脚本：`tools/verify_hooks.py`（可运行、只读）→ `out/re_work/hook_audit/verify_hooks.json`
> 对照：`docs/re/net_sync_checksum.md` §4.2 序列化范围 / §5 红线表；台账 `[v1.5.3]`（Install/Remove 不对称教训）、`[v1.5.5]`（Greatest_Threat Inline）、`[v1.6.0]`（迷雾四键）

---

## 0. 覆盖率自证摘要（verify_hooks.py 实测）

| 计数项 | 数值 | 判定 |
|---|---|---|
| Hook 实现符号（`Hook_*` / `*Proxy` / `*Stub`） | **21** | 全部列入 §2 |
| `PatchVTablePointer` 安装 / 还原 | **13 / 13** | 对称 |
| Inline 备份变量 `s_orig*Bytes` | **8** | 全部有还原 memcpy |
| `Install*` / `Remove*` 函数对 | **3 / 3** | 对称 |
| ini 键 / `LoadConfig` 读取 | **13 / 13** | 双向对齐 |
| v1.6.0 四键（ini + LoadConfig 双命中） | **4 / 4** | 覆盖 |
| 头文件 `ADDR_*` 死宏（cpp 零引用） | 25 | 列入 §5「装了但没生效」候选 |

脚本退出码 0 = PASS。运行方式：

```powershell
python tools/verify_hooks.py
python tools/verify_hooks.py --json out/re_work/hook_audit/verify_hooks.json
```

---

## 1. 安装入口与生命周期

| 阶段 | 位置 | 动作 |
|---|---|---|
| 注入 | `dllmain.cpp` `DLL_PROCESS_ATTACH` | `InstallVTableHooks()` → `LoadConfig()` → `EnableLowFragmentationHeap()` → `timeBeginPeriod(1)`（若 `HighPrecisionTimer`） |
| 每帧 | `Hook_CellClass_Draw` / `ShouldDraw*` / `Hook_RadarPlot_Proxy` | `UpdateVisionGrid()`（帧守卫：同 `CurrentFrame` 只跑一次） |
| 遥测 | `CheckTelemetry()`（2s 节流，由 SelectAutoTarget / Unit_Draw 钩子驱动） | 打 10 项计数到 `ra2render.log` |
| 卸载 | `dllmain.cpp` `DLL_PROCESS_DETACH` | `timeEndPeriod(1)` → `RemoveVTableHooks()`（内部调 3 个 `Remove*` + 13 槽虚表还原） |

**虚表安装辅助**：`PatchVTablePointer(target, newFunc, &outOrig, name)`（`blitter_hooks.cpp:1565`）— `VirtualProtect` → 保存原指针 → 写新指针 → 恢复保护。还原走同一函数（`outOrig=nullptr`）。

---

## 2. 全量已装 Hook 清单

> 「还原对称」= `RemoveVTableHooks` / 对应 `Remove*` 中存在等价还原路径（静态审计结论，非运行时实测）。
> 「可序列化」对照 `net_sync_checksum.md` §4.2：`CurrentFrame` / `ScenarioClass`(含 Random) / Techno-Cell 状态 / House / 存档块。

### 2.1 L1 Blitter 虚表槽（vtable+4，6 个）

| # | Hook 名 | 目标（虚表槽） | 原始实现 | 安装函数 | ini 开关键 | 遥测字段 | 还原 | 可序列化字段 | 联机影响 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `BlitterHooks::Hook_BlitTransXlatAlphaZRead` | `0x007E56F0+4`（Blit 槽） | `0x00494B60` | `InstallVTableHooks` #1 | `EnableSIMD` | `totalBlitCalls/totalBlitPixels` | 对称 | 否（纯像素） | **安全** |
| 2 | `Hook_BlitTransXlat_G` | `0x007E5A20+4` | `0x004912B0` | 同上 #2 | `EnableSIMD` | 同上 | 对称 | 否 | **安全** |
| 3 | `Hook_RLEBlitTransXlat_G` | `0x007E55C0+4` | `0x004960A0` | 同上 #3 | （无独立键） | `totalBlitCalls` | 对称 | 否 | **安全**（仅遥测转发，见 §5-A1） |
| 4 | `Hook_BlitTrans_G` | `0x007F7BF4+4` | `0x007BC890` | 同上 #4 | `EnableSIMD` | 同上 | 对称 | 否 | **安全** |
| 5 | `Hook_BlitTransDarken_G` | `0x007E59F0+4` | `0x00492670` | 同上 #5 | `EnableSIMD` | 同上 | 对称 | 否 | **安全** |
| 6 | `Hook_BlitPlain_G` | `0x007F7BC4+4` | `0x007BC7F0` | 同上 #6 | （无） | — | 对称 | 否 | **安全** |

> 注：SIMD 快路径仅在 `warpOffset==0 && aBuf==nullptr && XlatTable!=null` 时启用，否则尾调原始实现（`blitter_hooks.cpp:171,224,282,330`）。像素语义与原版对齐目标不变。

### 2.2 L2 寻敌（SelectAutoTarget 虚表 ×2 + Greatest_Threat Inline）

| # | Hook 名 | 目标 | 原始实现 | 安装函数 | ini 键 | 遥测字段 | 还原 | 可序列化字段 | 联机影响 |
|---|---|---|---|---|---|---|---|---|---|
| 7 | `TargetHooks::Hook_Techno_SelectAutoTarget` | `0x007F4D84`（Techno v[265]） | `0x006FB010` | `InstallVTableHooks` #7 | `TargetScanInterval` | `totalTargetScans` / `throttledTargetScans` | 对称 | **是（间接）**：跳过扫描 → 改变 `CurrentTargets(+0x458)` / 开火时机 | **禁止**（见 §4-B1：节流哈希含指针位移，跨端不确定） |
| 8 | `Hook_Unit_SelectAutoTarget` | `0x007F6094`（Unit v[265]） | `0x00736CA0` | 同上 #8 | `TargetScanInterval` | 同上 | 对称 | 同上 | **禁止**（同上） |
| 9 | `TargetHooks::Hook_Techno_Greatest_Threat` | **Inline** `0x006F8DF0`（9B：`E9 rel32 + NOP×4`） | trampoline→`0x006F8DF9` | `InstallGreatestThreatHook`（`InstallVTableHooks` #15 调） | `TargetScanInterval` | `totalTargetScans` / `throttledTargetScans` | 对称（`RemoveGreatestThreatHook` 还原 9 字节） | **是（间接）**：Target Retention 返回 `this+0x5D4` 旧目标，跳过全图扫描 | **条件**：Retention 逻辑本身确定（纯函数+对象字段），但与 #7/#8 节流联用时同受指针哈希影响 → 实际等同禁止 |
| 10 | `Hook_Unit_Greatest_Threat` | **未安装**（死代码） | — | — | — | — | — | — | 不生效（§5-A2） |

**Inline 细节**（`blitter_hooks.cpp:486-533`）：备份原 9 字节 `83 EC 5C 8B 15 34 EC A8 00` → 跳板副本 + `jmp 0x6F8DF9` → 入口写 `E9 [Hook_Techno_Greatest_Threat] 90 90 90 90`。覆盖全兵种（寻敌汇聚入口，台账 [v1.5.5]）。

> **[DA1 订正 · 2026-09-27]** 本表 #7/#8/#9 的「禁止/VIOLATION」判定**已过期**（默认键降为 RISK、pointer 分支仍 VIOLATION），行号 `:404/:425/:463` 已迁移为 `:534/:556/:595`。逐条对照见文末 **§10.1**。

### 2.3 L3 星际迷雾 · 单位绘制剔除（vtable 槽 69 ×5）

| # | Hook 名 | 目标（v[69]） | 原始实现 | 安装函数 | ini 键 | 遥测字段 | 还原 | 可序列化字段 | 联机影响 |
|---|---|---|---|---|---|---|---|---|---|
| 11 | `FogHooks::Hook_Unit_Draw` | `0x007F5D84` | `0x0073CEC0` | `InstallVTableHooks` #9 | `EnableStarCraftFog` | `unitsCulledByFog` / `totalUnitsRendered` | 对称 | 否（只拦绘制） | **安全** |
| 12 | `Hook_Infantry_Draw` | `0x007EB16C` | `0x00518F90` | #10 | `EnableStarCraftFog` | 同上 | 对称 | 否 | **安全** |
| 13 | `Hook_Aircraft_Draw` | `0x007E23B8` | `0x004144B0` | #11 | `EnableStarCraftFog` | 同上 | 对称 | 否 | **安全** |

> 门控谓词 `ShouldDrawMobileObject`（`blitter_hooks.cpp:827`）：己方/盟友直通；敌方查 `s_visionGrid` 直视 token；兼容 `Cell+0xAC` 心灵探测传感器位。只读对象字段，**不写**任何可序列化状态。

### 2.4 L5 建筑 / 弹道迷雾（v1.6.0 新增，v[69] ×2）

| # | Hook 名 | 目标 | 原始实现 | 安装函数 | ini 键 | 遥测字段 | 还原 | 可序列化字段 | 联机影响 |
|---|---|---|---|---|---|---|---|---|---|
| 14 | `FogHooks::Hook_Building_Draw` | `0x007E3FD0` | `0x0043D290` | `InstallVTableHooks` #12 | **`EnableBuildingFog`** | `buildingsCulledByFog` | 对称 | 否（只拦绘制；`s_everSeenGrid` 为 DLL 私有网格，**不进档**） | **安全**（表现层） |
| 15 | `FogHooks::Hook_Bullet_Draw` | `0x007E47F8` | `0x00468090` | `InstallVTableHooks` #13 | **`EnableBulletFog`** | `bulletsCulledByFog` | 对称 | 否（命中判定不动） | **安全** |

> `ShouldDrawBuilding`（:904）三态：直视 → 可见；`s_everSeenGrid` 盖章 → 常驻可见（WC3）；否则隐形。
> `ShouldDrawBullet`（:950）：`Owner+0xB0` 归属敌方且弹体格非直视 → 剔除。
> 二者的 `StampEverSeenIfVisible` 仅写 DLL 私有 `s_everSeenGrid`（512×512），对照 §4.2 **不在序列化范围**。

### 2.5 L3/L5 CellClass::Draw Inline + 灰雾混色桩 + 全量重绘

| # | Hook / 补丁 | 目标 | 原始字节 | 安装函数 | ini 键 | 遥测字段 | 还原 | 可序列化字段 | 联机影响 |
|---|---|---|---|---|---|---|---|---|---|
| 16 | `Hook_CellClass_Draw_Proxy`（naked）→ `Hook_CellClass_Draw` | Inline `0x004801F0`（5B `E9 rel32`） | 保存于 `s_origCellClassDrawBytes` | `InstallCellClassDrawHook`（`InstallVTableHooks` #14） | `EnableStarCraftFog` + `FadeFogTransition` | `fogCellsDrawn` | 对称 | 否（只读 Cell `+0x24` MapCoords / `+0x12C` flags bit3） | **安全** |
| 17 | `Hook_FogBlendB1_Stub`（naked） | 补丁区 `0x0047F40F`（49B → `E9`+NOP） | `s_origFogBlendB1Bytes[49]` | 同上 | `FadeFogTransition`（强度 0..256；关=硬切换 s=256） | — | 对称 | 否（像素混色） | **安全** |
| 18 | `Hook_FogBlendB2_Stub`（naked） | 补丁区 `0x0047F4AE`（51B → `E9`+NOP） | `s_origFogBlendB2Bytes[51]` | 同上 | 同上 | — | 对称 | 否 | **安全** |
| 19 | 视口全量重绘跳转补丁 | `0x006D3D99`（6B → `E9 99 00 00 00 90` = jmp `0x006D3E37`） | `s_origTacticalRedrawBytes[6]` | 同上（**无独立 ini 键**） | — | — | 对称 | 否（只改重绘范围） | **安全**（表现层；见 §5-B2 与 Q7 冲突） |

> 混色公式：`final = c - ((c - c50) * s >> 8)`（RGB565 逐通道），`s=256` 与旧静态 50% 减半补丁逐位一致。渐变表：渐入 `64,128,192,256`，渐出 `192,144,96,48`（`Hook_CellClass_Draw` :1027-1038）。
> **反例提醒**：`CellClass::MarkForRedraw(0x00486E70)` 的 `bFlag` 恒 false（`0x00486FB5`），无法驱动地表/迷雾重绘——这是台账 v1.5.3「A 方案」作废、本补丁改走 `0x006D3D99` 全量刷的原因。

### 2.6 L5 雷达小地图迷雾（v1.6.0，3 个 patch 点）

| # | Hook / 补丁 | 目标 | 原始 | 安装函数 | ini 键 | 遥测字段 | 还原 | 可序列化字段 | 联机影响 |
|---|---|---|---|---|---|---|---|---|---|
| 20 | `Hook_RadarPlot_Proxy`（naked） | 调用点 `0x006574C3`（`call rel32` 等长）+ `0x00655C50` 前 5 字节蹦床 | `s_origRadarPlotCallBytes` / `s_origRadarPlotPrologue` | `InstallRadarFogHooks`（#16） | **`EnableMinimapFog`**（`s_minimapFogGate` 汇编侧镜像） | `s_minimapFogPixels` | 对称（`RemoveRadarFogHooks` 三点全还原） | 否（像素覆写 `(c>>1)&0x7BEF`） | **安全** |
> 【W3 勘误 · W3-A6/ISSUE-DISAMBIG-RADAR-HOOK】改前：0x006574C3；改后：0x006574C3（RadarClass::Plot_Cell 主循环调用点，见 ra2render.h:158；实际补丁下沉点位于 0x00655D38，见 blitter_hooks.cpp:150, 3016）；依据：ra2render/ra2render.h:158; ra2render/blitter_hooks.cpp:150, 2711, 2920, 3016, 3090；分级：P2
| 21 | `Hook_RadarPending_Proxy`（naked） | 调用点 `0x0065719A`（`call 0x660530` 等长） | `s_origRadarPendingCallBytes` | 同上 | 同上（`s_minimapForceRefresh` 由视野迁移置位） | — | 对称 | 否（只改跳帧判定返回值） | **安全** |

> 事件信标 blip 第二调用点 `0x00657520` **刻意不动**（"基地遭袭"标记在雾中仍可见）。
> `s_minimapForceRefresh=10`：视野翻转后 10 帧强制小地图全量刷新，静止画面下敌点灰化即时生效（与 L4 同哲学）。

> **[DA1 订正 · 2026-09-27]** 本小节 #20 的挂钩地址 `0x006574C3` **已过期**——现网为路线 A 下沉点 `0x00655D38`（9 字节，跳板回 `0x00655D41`）+ `0x0065719A`；`s_origRadarPlotCallBytes` / `s_origRadarPlotPrologue` 两个备份变量已移除，改为 `s_origPlotCellBytes[9]` / `s_origRadarPendingCallBytes[5]`。对照见 **§10.2**。

### 2.7 非 Hook 型状态改写（必须单列，容易漏审计）

| # | 动作 | 位置 | 写什么 | ini 键 | 还原路径 | 可序列化字段 | 联机影响 |
|---|---|---|---|---|---|---|---|
| S1 | `PatchSpySatBuildingTypes` | :564（`UpdateVisionGrid` 懒加载） | `SuperWeaponTypeClass+0xB0`=CD 帧、`+0xF8`=半径；`BuildingTypeClass+0x16A5`=false（关全图 Reveal）、`+0x16F0`=PsychicReveal 索引 | `EnableSpySatRadarSweep` / `RadarSweepCooldownFrames` / `RadarSweepRadiusCells` | **无 Remove 还原**（进程生命周期内一次性改 TYPE 数据） | **是（条件）**：TYPE 数据不进档，但改变超武行为 → 影响 House 超武状态机 | **条件**：全端同构建+同 ini 则确定；混端/混 ini 必分叉 |
| S2 | `UpdateVisionGrid` 每帧 | :715-718 | `ScenarioClass` 标志字 `&= ~0x1000`（强制 FogOfWar=0） | 随 `EnableStarCraftFog` 链路执行 | 无（每帧重写） | **是**：`ScenarioClass` 整体进档（§4.2） | **条件**：写常量子掩码，全端一致则安全；但属**对可序列化全局的持续写**，审计必须点名 |
| S3 | `UpdateVisionGrid` 每帧 | :721 | `HouseClass+0x577A` SpySatActive = 0 | 随上 | 无（每帧重写） | **是**：House 进 `Save_Sides`（§4.2） | **条件**：同上，常量写；若原版逻辑依赖该字段且被联机命令流读取 → 潜在分叉面 |
| S4 | 战局重载检测 | :682-689 | `currentFrame+100 < s_lastFrameUpdated` 时清 `s_everSeenGrid`/`s_fogRampFrame`/`s_spySatPatched` | — | 自清 | 否（DLL 私有） | **安全**（纯本地表现状态；但读档后 everSeen 丢失 = §6 遗留） |

---

## 3. v1.6.0 四键专项核对（强制覆盖）

| ini 键 | 默认 | LoadConfig | 生效门控位置 | 挂钩的 Hook/补丁 | 关闭后行为 | 回滚方式 | 遥测 | 联机 | 验收状态 |
|---|---|---|---|---|---|---|---|---|---|
| **EnableBuildingFog** | 1 | :91-92 `g_enableBuildingFog` | `ShouldDrawBuilding`（:1541）+ `UpdateVisionGrid` everSeen 盖章块（:775） | #14 `Hook_Building_Draw` | 敌建筑全部原版可见（回到 v1.5.x）；不再盖 everSeen 章 | ini=0 即时软关；`RemoveVTableHooks` 硬还原 | `buildingsCulledByFog` | 安全 | **未验收**（台账 v1.6.0 §4） |
| **EnableBulletFog** | 1 | :94-95 `g_enableBulletFog` | `ShouldDrawBullet`（:1552） | #15 `Hook_Bullet_Draw` | 弹道全部原版可见 | 同上 | `bulletsCulledByFog` | 安全 | **未验收** |
| **FadeFogTransition** | 1 | :97-98 `g_fadeFogTransition` | `Hook_CellClass_Draw` 强度计算（:1027）+ 迁移扫描块（:804） | #17/#18 混色桩（s=256 硬切换） | 灰雾硬切换（SC1 式）；混色桩仍在但 s 恒 256 | ini=0 即时软关；桩字节由 `RemoveCellClassDrawHook` 还原 | （无独立计数） | 安全 | **未验收** |
| **EnableMinimapFog** | 1 | :100-102 `g_enableMinimapFog` + `s_minimapFogGate` | `Hook_RadarPlot_Proxy` 汇编 `cmp [s_minimapFogGate],0`（:1362） | #20/#21 雷达双代理 | 小地图原版语义（已探索即全彩+敌点） | ini=0 走 passthrough 尾跳；`RemoveRadarFogHooks` 硬还原 | `s_minimapFogPixels` | 安全 | **未验收** |

**跨战局重载**（四键共用，:680-689）：逻辑帧大幅回退 → 清 everSeen / 渐变 / `s_spySatPatched`，并置 `s_minimapForceRefresh=10`。读**晚期档**保留侦察记忆，新遭遇战彻底重置。

---

## 4. 可序列化字段 × 联机影响总表

对照 `net_sync_checksum.md` §4.2：

| 状态域（§4.2） | 本审计涉及的写点 | 判定 | 依据 |
|---|---|---|---|
| `CurrentFrame` | **只读**（`ADDR_CURRENT_FRAME` 作帧守卫/节流键） | 安全 | 不改增量语义 |
| `ScenarioClass`（含 Random、Timer…） | **写**：S2 标志字 `&= ~0x1000` 每帧 | **条件** | 写的是常量子掩码、全端同构建则逐位一致；但落在序列化全局上，混构建必坏档 |
| Randomizer（`ScenarioClass::Random`） | 无触碰 | 安全 | — |
| Techno 状态（含 `CurrentTargets+0x458`、Target `+0x5D4`） | **间接写**：#7/#8 跳过 SelectAutoTarget、#9 Retention 返旧目标 | **禁止** | 节流键 `(ptr>>4 + CurrentFrame) % interval` 含**指针位移**（:404-407, :463-466），跨进程地址不同 → 各端节流相位不同 → 扫描/开火时机分叉 |
| Cell 状态 | 只读 `+0x24/+0x12C/+0xAC`；写仅落 DLL 私有 `s_visionGrid`/`s_everSeenGrid` | 安全 | 私有网格不进档 |
| House（`Save_Sides`） | **写**：S3 `House+0x577A=0` 每帧 | **条件** | 同 S2 |
| 存档布局 / 魔数 | 无触碰 | 安全 | 未增删存档字段 |
| 伤害/武器/寻路/命令队列 | 无触碰 | 安全 | #15 只拦绘制，命中判定原样 |

### 联机分级汇总

| 级别 | Hook/动作 | 说明 |
|---|---|---|
| **安全**（纯表现，可联机共存） | #1–#6 全部 Blit、#11–#15 五路 Draw 剔除、#16–#19 Cell/混色/全量刷、#20–#21 雷达、S4 | 只动像素/绘制范围/本地私有网格；不回写引擎状态 |
| **条件**（全端同构建+同 ini 才安全） | S1 SpySat TYPE 补丁、S2 Scenario 标志、S3 House SpySatActive、#9 Greatest_Threat（单看） | 常量写/TYPE 写，确定性成立的前提是**各端字节级同一 DLL 与同一 ini** |
| **禁止**（现网实现不可联机） | #7/#8 SelectAutoTarget 节流、#9 与节流联用 | 节流哈希含 `this` 指针位移，违反 net_sync §6「重建/跳过必须是 `CurrentFrame` 纯函数」红线；须改为 `(CurrentFrame + index) % k` 形式才有联机资格 |

---

## 5. Install/Remove 不对称 × 「装了但可能没生效」候选

沿台账 `[v1.5.3]` 教训（`GREATEST_THREAT` 虚表槽 Remove 有还原、Install 漏装 → Target Retention 全额未生效）。

### 5.1 对称性结论（好消息）

| 检查面 | 结果 |
|---|---|
| 13 个 `PatchVTablePointer` 槽 | Install / Remove 一一对应（含 Building/Bullet 两个 v1.6.0 新槽） |
| 8 个 `s_orig*Bytes` 备份 | 全部存在对应 `memcpy(…, s_orig…, …)` 还原 |
| 3 对 `Install*/Remove*` | `CellClassDraw` / `GreatestThreat` / `RadarFog` 均配对 |
| v1.5.3 的漏装缺口 | **已修复**：`InstallGreatestThreatHook` 现走 inline `0x006F8DF0`，与 `RemoveGreatestThreatHook` 对称（`blitter_hooks.cpp:486/525`） |

### 5.2 「装了但可能没生效」候选清单（本次审计核心产出）

| ID | 候选 | 证据（file:line） | 性质 | 风险 | 建议 |
|---|---|---|---|---|---|
| **A1** | `Hook_RLEBlitTransXlat_G` 仅遥测转发，无像素逻辑 | :256-267 直接 `g_pOrigRLEBlitTransXlat_G(...)` 尾调 | 装了（虚表已劫持）但**功能未实现** | 中：用户以为 RLE 已加速，实则零收益 | 按 [v1.5.3] P0-P2 清单补全，或 ini 旁路直接不装 |
| **A2** | `Hook_Unit_Greatest_Threat` / `g_pOrigUnitGreatestThreat` / `ADDR_VTABLE_ENTRY_{TECHNO,UNIT}_GREATEST_THREAT` / `ADDR_ORIG_{TECHNO,UNIT}_GREATEST_THREAT` | 头文件 :34-44 定义；cpp 中 `Hook_Unit_Greatest_Threat`（:482）仅转发且**无任何安装点**；虚表槽地址从未被 `PatchVTablePointer` 使用 | **死代码 + 死宏**（v1.5.3 漏装残留物） | 低（inline 已覆盖汇聚点）；但误导审计 | 删除或标注 deprecated；勿再按虚表槽方案安装（会与 inline 双挂钩） |
| **A3** | `UnlockGameSpeed` ini 键已加载但 `EnforceGameSpeedUnlock()` **从不被调用** | `dllmain.cpp:31-36` 只调 `InstallVTableHooks/EnableLowFragmentationHeap/timeBeginPeriod`；`EnforceGameSpeedUnlock`（:154）是空函数体 | **装了开关、没装生效路径** | 低（空函数本身也不改行为） | 明确此键为 no-op 占位，或接线/删除 |
| **A4** | 25 个 `ADDR_*` 头文件宏 cpp 零引用 | verify_hooks.py [6] 节输出（含全部 `ADDR_VFUNC_*`、`ADDR_ORIG_*`、`ADDR_RULES_INSTANCE`、`ADDR_GAME_SPEED_SETTING` 等） | 死宏堆积 | 低 | 清理或分组注释「仅文档用」 |
| **A5** | `ForgeTelemetry.minimapFogPixels` 字段从未写入 | `ra2render.h:170` 定义；实际计数走 `s_minimapFogPixels`（:50, :1404） | 遥测字段死区 | 低 | 二选一统一 |
| **A6** | **灰雾混色桩 B1/B2 与 `0x006D3D99` 全量刷补丁无独立 ini 键**——`EnableStarCraftFog=0` 时它们**仍安装并生效** | `InstallCellClassDrawHook`（:1220-1281）无条件打三处补丁；`Hook_CellClass_Draw` 的 `g_enableStarCraftFog` 只短路**追加灰雾层**，不撤销 B1/B2/全量刷 | **开关关不干净**：声称「关迷雾」仍残留代码级补丁 | 中高：回滚实验会被污染基线 | 为三处补丁各设独立键（或随 `EnableStarCraftFog` 总闸装卸） |
| **A7** | `FadeFogTransition=0` 时混色桩仍在（只是 s 恒 256） | :1027-1038 强度分支；桩字节仍为 `E9` 跳转 | 软关≠硬关 | 低（s=256 与旧补丁逐位一致） | 验收文档注明「关=硬切换，非还原原版」 |
| **A8** | `PatchSpySatBuildingTypes` **无 Remove 还原** | :564-623 只写不存原值；`RemoveVTableHooks` 不涉及 | **改 TYPE 后不可回滚**（进程内） | 中：验收 A-1 的「关闭全部键基线」若在同一进程内做，SpySat 改动仍残留 | 保存原 `+0x16A5/+0x16F0/+0xB0/+0xF8` 并提供还原；或要求验收在新进程进行 |
| **A9** | `EnableMinimapFog=0` 时 #20/#21 仍安装（走 passthrough 尾跳） | :1362 `cmp [s_minimapFogGate],0 → je passthrough` | 装了但旁路 | 低（尾跳与原版语义等价） | 可接受；硬还原仍走 `RemoveRadarFogHooks` |
| **A10** | 跨战局重载后 `s_everSeenGrid` **不从存档恢复** | :682-689 只做清零；DLL 私有网格不进 §4.2 序列化 | 「装了且生效，但读档后状态丢失」——v1.6.0 §4 遗留项④ | 中：读档后敌建筑常驻可见记忆消失 → 需重新侦察 | 真机验收 A-1 ④ 项专项验证；若需持久化须另设计（进档或重建） |

### 5.3 与 v1.5.3 先例的模式对照

| v1.5.3 模式 | 本次是否再现 | 落点 |
|---|---|---|
| Remove 有还原、Install 漏装 | **未再现**（13/13 对称；Greatest_Threat 已改 inline 且对称） | §5.1 |
| 虚表槽覆盖不全（Techno/Unit 盖不住 Infantry/Building/Aircraft/Foot） | **已缓解**：inline `0x006F8DF0` 覆盖汇聚入口；Draw 侧 5 槽含 Infantry/Aircraft/Building/Bullet | §2.2 / §2.3-2.4 |
| 「装了但只是遥测转发」 | **再现** | A1 |
| 死宏/死符号残留 | **再现** | A2 / A4 / A5 |
| 开关不能完全卸下补丁 | **再现（新形态）** | A6 / A7 / A9 |
| 改引擎数据无还原 | **再现** | A8 |

---

## 6. 遥测字段对照（`ForgeTelemetry` × 2s 日志）

| 字段 | 累加点 | 2s 日志 | Remove 尾部日志 | 备注 |
|---|---|---|---|---|
| `totalBlitCalls` | #1-#5 各 +1 | ✓ | ✓ | |
| `totalBlitPixels` | #1-#5 `+= length` | ✓（Mpx） | ✓ | |
| `totalTargetScans` | #7/#8/#9 放行时 +1 | ✓ | ✓ | |
| `throttledTargetScans` | #7/#8/#9 节流返回时 +1 | ✓（含节流率%） | ✓ | |
| `totalUnitsRendered` | #11-#13 放行时 +1 | ✓ | ✓ | |
| `unitsCulledByFog` | #11-#13 剔除时 +1 | ✓ | ✓ | |
| `fogCellsDrawn` | #16 灰雾层绘制 +1 | ✓ | ✓ | |
| `buildingsCulledByFog` | #14 剔除 +1 | ✓ | ✓ | v1.6.0 |
| `bulletsCulledByFog` | #15 剔除 +1 | ✓ | ✓ | v1.6.0 |
| `minimapFogPixels`（g_telemetry） | **从未写入** | — | — | 死字段（A5） |
| `s_minimapFogPixels` | #20 汇编 `inc` | ✓ | ✓ | 实际生效的计数 |

---

## 7. ini 键全表（13 键，双份一致）

| 节 | 键 | 默认 | 读取 | 管什么 | 影响的 Hook |
|---|---|---|---|---|---|
| Render | `EnableSIMD` | 1 | :66 | Blit 向量快路径 | #1/#2/#4/#5 |
| Logic | `TargetScanInterval` | 8（钳 1..64） | :62 | 寻敌节流间隔 | #7/#8/#9 |
| Speed | `UnlockGameSpeed` | 0 | :69 | **no-op**（A3） | — |
| System | `EnableLFH` | 1 | :72 | 低碎片堆 | 非 Hook（进程级） |
| System | `HighPrecisionTimer` | 1 | :75 | `timeBeginPeriod(1)` | 非 Hook |
| FogOfWar | `EnableStarCraftFog` | 1 | :78 | L3 机动单位剔除 + 灰雾层 | #11-#13、#16（部分） |
| FogOfWar | `EnableSpySatRadarSweep` | 1 | :81 | S1 SpySat→人族雷达 | S1 |
| FogOfWar | `RadarSweepCooldownFrames` | 600（≥60） | :84 | 超武 CD | S1 |
| FogOfWar | `RadarSweepRadiusCells` | 16（4..64） | :87 | 扫描半径 | S1 |
| FogOfWar | **`EnableBuildingFog`** | 1 | :91 | 建筑三态 | #14 |
| FogOfWar | **`EnableBulletFog`** | 1 | :94 | 弹道剔除 | #15 |
| FogOfWar | **`FadeFogTransition`** | 1 | :97 | 4 帧渐变 | #17/#18 |
| FogOfWar | **`EnableMinimapFog`** | 1 | :100 | 小地图灰化 | #20/#21 |

`ra2render/ra2render.ini` ≡ `ra2youli/ra2render.ini`（`fc`：no differences）。

---

## 8. 还原路径总表（回滚手册）

| 层级 | 操作 | 覆盖面 | 残留 |
|---|---|---|---|
| 软关（进程内） | 改 ini 对应键 = 0，重启游戏 | 见 §3 / §7 | A6：B1/B2/全量刷不受 `EnableStarCraftFog` 控制；A8：SpySat TYPE 改写不随开关回退 |
| 硬卸（进程内） | `RemoveVTableHooks()`（`DLL_PROCESS_DETACH` 自动） | 13 虚表 + 8 字节备份 + 3 组 Inline | S1 SpySat TYPE **不还原**；S2/S3 每帧重写随 UpdateVisionGrid 停止而停 |
| 彻底 | 移除/改名 `ra2render.dll`（loader 不再注入） | 全部 | 无（gamemd.exe 从未写盘——红线 §3.1 保持） |

---

## 9. 结论与给下游的规格建议

1. **对称性总体良好**：v1.5.3 的「Install 漏装」在 Greatest_Threat 上已用 inline 方案闭环；13 虚表 + 8 备份 + 3 组 Inline 静态对称。**不是**「大面积装了没卸」。
2. **真正的「装了但没生效」**集中在：RLE 遥测空转（A1）、死符号（A2/A4/A5）、`UnlockGameSpeed` 空开关（A3）。
3. **真正的「开关关不干净」**：B1/B2 + `0x006D3D99` 全量刷无独立键（A6）；SpySat TYPE 改写无还原（A8）。这两条会污染 A-1 的「关闭全部 v1.6.0 键」基线——**验收前必须先修或显式接受残留**。
4. **联机唯一硬红灯**：#7/#8（+#9 联用）节流哈希含指针位移 → 跨端不确定 → desync。任何联机构建必须 `TargetScanInterval=1` 或改用 `CurrentFrame` 纯函数轮转（net_sync §6.2）。
5. **v1.6.0 四键**均已接入 ini + LoadConfig + 运行时门控 + 独立遥测/回滚，静态层完整；真机四项仍「未验收」（台账闸门）。
6. **Q7 前置提醒**：`0x006D3D99` 现为无条件 `jmp`（v1.5.0 全量刷），与 Lead 修订后的 L4 折中（恢复原版 `jge` + `0x006DA7D0` 打脏 + >350 格全屏保底）冲突；落地时须给该补丁独立 ini 键并纳入本表。

---

## 附录 A · 21 个 Hook 实现符号索引

`Hook_BlitTransXlatAlphaZRead` · `Hook_BlitTransXlat_G` · `Hook_RLEBlitTransXlat_G` · `Hook_BlitTrans_G` · `Hook_BlitTransDarken_G` · `Hook_BlitPlain_G` · `Hook_Techno_SelectAutoTarget` · `Hook_Unit_SelectAutoTarget` · `Hook_Techno_Greatest_Threat` · `Hook_Unit_Greatest_Threat`（未安装） · `Hook_CellClass_Draw` · `Hook_CellClass_Draw_Proxy` · `Hook_FogBlendB1_Stub` · `Hook_FogBlendB2_Stub` · `Hook_RadarPlot_Proxy` · `Hook_RadarPending_Proxy` · `Hook_Unit_Draw` · `Hook_Infantry_Draw` · `Hook_Aircraft_Draw` · `Hook_Building_Draw` · `Hook_Bullet_Draw`

## 附录 B · 产出物

| 路径 | 说明 |
|---|---|
| `docs/re/INSTALLED_HOOKS_AUDIT.md` | 本文档 |
| `tools/verify_hooks.py` | 静态覆盖率自证（只读、可重复运行） |
| `out/re_work/hook_audit/verify_hooks.json` | 脚本 JSON 证据输出 |

> 台账登记草稿（§九 模板最小内容，供 Lead 合并）：
> **[v1.5.11] 已装 Hook 静态审计**——13 虚表+3 组 Inline 静态对称；「装了但没生效」10 条候选（RLE 空转 / 死符号 / UnlockGameSpeed 空开关 / 灰雾桩无键 / SpySat 无还原 / everSeen 不进档等）；联机硬红灯 = TargetScanInterval 指针哈希节流；v1.6.0 四键静态覆盖完整、真机未验收。

---

## 10. 勘误 · MPS 落地后订正（DA1 · DSH 子代理 · 2026-09-27）

> **性质**：只**追加**本节，**不改动 §0–§9 与附录**（L1-281 逐字保留）。
> **双快照**：正文 = **1757 行**快照（M-2/Q3 时点）；本节 = **1892 行 / 86,961 B**（2026-09-27 09:06:28，mtime 实测）。
> **基线（只读未变）**：`ra2youli/gamemd.exe` 4,825,360 B，MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`；`python tools/verify_anchors.py` = **323/323 PASS**（本任务实跑）。
> **部署件**：`ra2render/ra2render.dll` ≡ `ra2youli/ra2render.dll` = 129,536 B，SHA-256 `E7FA669C85B5DA53C71898DC453AC35301EC55F1222D1D581BFAEAC105DCC7CA`；`ra2render.ini` ≡ `ra2youli/ra2render.ini` = 2,996 B / **14 键**（本快照实测），SHA-256 `564A265291C3C6CAF0E15CE8CFF00360A0BBD28EAF2E57BA74D1E0E49C0EC64F`。
> **自证脚本重跑**：`python tools/verify_hooks.py --json out/re_work/da1/verify_hooks_da1.json`（本任务实跑，未覆盖 `out/re_work/hook_audit/verify_hooks.json`）——见 §10.4。

### 10.1 订正 ①：#7/#8/#9「指针哈希 → 禁止/VIOLATION」结论过期 ⇒ 降级为 **默认键下 RISK、`pointer` 分支仍 VIOLATION**

| 目标 | 改前原文（逐字，行号为本快照校对前的原文位置） | 改后表述 | 依据 |
|---|---|---|---|
| §2.2 表 #7（`L67`）/ #8（`L68`）/ #9（`L69`） | 「**禁止**（见 §4-B1：节流哈希含指针位移，跨端不确定）」／「实际等同禁止」 | **默认键下 RISK（待对拍）；`TargetScanKey=pointer` 分支仍 VIOLATION**：三处节流键已收敛为 `ThrottleKey()`——默认 `g_targetScanKey = 1`（position）时用单位格子坐标空间哈希（`(locX*0x9E3779B1 ^ locY*0x85EBCA77) >> 4`，读 `this+0x9C/0xA0`）；仅 `pointer` 分支保留旧指针位移键 `(uintptr_t)pThis >> 4` | `blitter_hooks.cpp:264-282`（`:265` 取生效键、`:267` pointer 分支、`:271-277` position 分支）、`:262`（默认 1）；`hook_gate_gap_table.md` §1.2 `L66-69` 与 §3 `L137-151` 同口径 |
| §4 表「Techno 状态」行（`L150`） | 「节流键 `(ptr>>4 + CurrentFrame) % interval` 含**指针位移**（`:404-407, :463-466`），跨进程地址不同 → 各端节流相位不同 → 扫描/开火时机分叉」 | 同上；且**该行号与公式均已过期**（现行为 `(((unitHash + currentFrame) % interval) != 0)`，`unitHash = ThrottleKey(pThis)`） | `blitter_hooks.cpp:534/:536-541`、`:556/:558-563`、`:595/:597-603` |
| §4「联机分级汇总」（`L162`） | 「**禁止**（现网实现不可联机）｜#7/#8 SelectAutoTarget 节流、#9 与节流联用」 | **默认构建降为「条件（RISK，待对拍）」**；`pointer` 键 + `interval>1` 才回到「禁止」 | 源码 `:89-94`（联机强制 position）、`:82-87`（联机强制 interval=1）；`mp_release_safety_checklist.md:21-24` |
| §9 结论 4（`L262`） | 「**联机唯一硬红灯**：#7/#8（+#9 联用）节流哈希含指针位移 → 跨端不确定 → desync。任何联机构建必须 `TargetScanInterval=1`…」 | **默认键下不再是硬红灯**：联机时 `GetEffectiveTargetScanKey()` 恒 position、`GetEffectiveTargetScanInterval()` 恒 `1` ⇒ 三条短路分支（`:537/:559/:598`）恒不进入，行为回原版全量扫描。**残留面（仍未闭环）**：① 单端 ini 误配 `pointer` 仅运行期纠正（不回写）；② 门控依赖 `MpActive()`（`:61-80`）判定成功，`IsBadReadPtr` 守卫失败即回落 false；③ `ForceSinglePlayer` 逃生舱未实现 | 源码 `:82-94`、`:129-131`、`:209-211`、`:61-80` |

> **未连带改动的部分（纪律声明）**：§5.2 的 A1–A10「装了但没生效 / 关不干净」十条候选**不在本批订正范围**，其结论经复核仍成立（仅行号过期，见 §10.3）；A6（B1/B2+L4 无独立键）、A8（SpySat 无还原）、A10（everSeen 不进档）在 G-04/G-07/G-09 中仍为**未闭环**。

### 10.2 订正 ②：雷达挂钩点 `0x006574C3` → **路线 A 下沉点 `0x00655D38`（9 字节）+ `0x0065719A` 强刷**

| 目标 | 改前原文（逐字） | 改后表述 | 依据 |
|---|---|---|---|
| §2.6 表 #20（`L111`） | 「`Hook_RadarPlot_Proxy`（naked）｜调用点 `0x006574C3`（`call rel32` 等长）+ `0x00655C50` 前 5 字节蹦床｜`s_origRadarPlotCallBytes` / `s_origRadarPlotPrologue`｜`InstallRadarFogHooks`（#16）」 | **路线 A 下沉**：安装点 = `0x00655D38` **9 字节补丁**（第 1B `E9 rel32` + 4×`90`，跳板还原 9 字节后 `jmp 0x00655D41`）；`0x0065719A` 仍为 5 字节 `call` 等长替换（强刷代理）；备份变量改为 `s_origPlotCellBytes[9]` / `s_plotCellTrampoline[16]` / `s_origRadarPendingCallBytes[5]`；函数 `InstallRadarFogHooks` / `RemoveRadarFogHooks` | 源码 `:1471-1473`、`:1570-1620`、`:1622-1635`、`:1604`（`ADDR_RADAR_PENDING_CALLSITE`）；字节断言：`0x00655D38 = 89 44 24 28 A1 50 35 B7 00`、`0x00655D41 = 3B C5 74 18`、`0x0065719A = E8 91 93 00 00`、`0x006574C3 = E8 88 E7 FF FF`（`out/re_work/da1/claims.txt`，`audit_bytes.py` 全 OK）；`docs/re/routeA_implementation_audit.md:20,235` |
| §2.6 表 #21（`L112`） | 「调用点 `0x0065719A`（`call 0x660530` 等长）｜同上｜`s_minimapForceRefresh` 由视野迁移置位」 | 地址结论**不变**；**补正**：该代理现前置 `s_minimapFogGate` 门控——`cmp byte ptr [s_minimapFogGate], 0` + `je orig_logic`，关闭态走原版 `mov eax,[0x00B04DB8] … sete al; ret` | 源码 `:1553-1568`（门控 `:1555-1556`） |
| §2.6 注（`L114-115`） | 「事件信标 blip 第二调用点 `0x00657520` **刻意不动**」；「`s_minimapForceRefresh=10` …（与 L4 同哲学）」 | **两条结论均不变**（未受路线 A 影响）；仅行号迁移（`s_minimapForceRefresh=10` → `:950-951`） | 源码 `:950-951` |
| §5.2 A9（`L191`） | 「`EnableMinimapFog=0` 时 #20/#21 仍安装（走 passthrough 尾跳）｜`:1362` `cmp [s_minimapFogGate],0 → je passthrough`」 | 结论**仍成立**；行号 `:1362` → 现网 **`:1481-1482`**（#20 代理），#21 新增门控 **`:1555`** | 源码 `:1481-1482`、`:1555` |

### 10.3 订正 ③：源文件行数 / 行号引用按当前文件更正

| 原引用（改前） | 现网实测 | 对象 |
|---|---|---|
| 题头 `L4` 与 `L32`：「`blitter_hooks.cpp`（**1757 行**）」 | **1892 行 / 86,961 B**（2026-09-27 09:06:28） | 源文件规模 |
| `L19`：「ini 键 / `LoadConfig` 读取 **13 / 13** 双向对齐」 | ini 键 **14**（新增 `TargetScanKey`，`ra2render.ini:51`）｜`LoadConfig` 实测 **14** 处读键（`GetPrivateProfileIntA` ×13 + `GetPrivateProfileStringA` ×1），脚本报 **14 / 13**（脚本只扫 `IntA` ⇒ 假阳性 `TargetScanKey`）；v1.6.0 四键 **4/4 OK** | §0 覆盖率自证 |
| `L21`：「头文件 `ADDR_*` 死宏（cpp 零引用）**25**」 | **27**（`verify_hooks.py` JSON 字段 `header_addrs_unused_in_cpp`，本任务实跑；`ADDR_RADAR_PLOT` / `ADDR_RADAR_PLOT_CALLSITE` 仍在列） | 死宏计数 |
| `L16`：「Inline 备份变量 `s_orig*Bytes`：**8**」 | **7**（`s_origCellClassDrawBytes` / `B1` / `B2` / `GreatestThreat` / `PlotCell[9]` / `RadarPendingCall[5]` / `TacticalRedraw`）——路线 A 以 1 个 9B 备份 + 1 个 5B 备份取代原 `s_origRadarPlotCallBytes` + `s_origRadarPlotPrologue` 两个 5B 备份；**7/7 saved+restored 对称** | ① 对称性自证 |
| `L41`：「`PatchVTablePointer`（`blitter_hooks.cpp:1565`）」 | 定义 **`:1700`**；13 槽安装调用 `:1727-1799`，13 槽还原调用 `:1822-1882` | 虚表安装辅助 |
| `L61`：「SIMD 快路径 …（`blitter_hooks.cpp:171,224,282,330`）」 | 现网条件分支 `:308`（#1）、`:354`（#2）、`:412`（#4）、`:460`（#5）；结论「像素语义对齐」未变 | §2.1 注 |
| `L67/L68/L69`（#7/#8/#9） | 见 §10.1；三处节流调用点 **`:534` / `:556` / `:595`**，短路门 `:537` / `:559` / `:598` | §2.2 表 |
| `L72`：「Inline 细节（`blitter_hooks.cpp:486-533`）」 | `InstallGreatestThreatHook` **`:619-656`**；`s_origGreatestThreatBytes` `:580`；`RemoveGreatestThreatHook` `:658-666` | Greatest_Threat Inline |
| `L80/L82`：「`ShouldDrawMobileObject`（`blitter_hooks.cpp:827`）」 | **`:961`**；Draw 槽门控 `:1640` / `:1652` / `:1664` | 机动剔除谓词 |
| `L91`：「`ShouldDrawBuilding`（:904）」 | **`:1038`**；门控 `:1676` | 建筑三态 |
| `L92`：「`ShouldDrawBullet`（:950）」 | **`:1084`**；门控 `:1687` | 弹道剔除 |
| `L99`：「`Hook_CellClass_Draw` …（`InstallCellClassDrawHook`，`InstallVTableHooks` #14）」 | `Hook_CellClass_Draw` **`:1129`**；`InstallCellClassDrawHook` **`:1354-1421`**；`RemoveCellClassDrawHook` **`:1422-1451`** | CellClass::Draw Inline |
| `L100/L101`：「`Hook_FogBlendB1_Stub` ｜ `0x0047F40F`（49B）」／「`Hook_FogBlendB2_Stub` ｜ `0x0047F4AE`（51B）」 | B1 **`:1231`**、B2 **`:1287`**；桩安装点 `:1387` / `:1393`（`InstallCellClassDrawHook` 体内） | 灰雾混色桩 |
| `L104`：「渐变表 …（`Hook_CellClass_Draw` :1027-1038）」 | 强度分支 **`:1161-1172`**（渐出 `ramp*48` `:1165` / 渐入 `(5-ramp)*64` `:1167` / 稳态 `:1171`）；防重复混色 `:1179-1182` | 渐变强度 |
| `L105` 反例提醒：「`CellClass::MarkForRedraw(0x00486E70)` …（`0x00486FB5`）」 | 本次**未复算**该二进制地址（超出 DA1 取证范围）⇒ 保留结论，地址标注**待核对** | 见交付回报 [4] |
| `L111-112`（#20/#21） | 见 §10.2 | 雷达 |
| `L121`（S1）：「`PatchSpySatBuildingTypes` ｜ `:564`（`UpdateVisionGrid` 懒加载）」 | 定义 **`:697-756`**；懒加载调用点 `:842-844` | S1 |
| `L122`（S2）：「`:715-718` `ScenarioClass` 标志字 `&= ~0x1000`」 | **`:851`**（基址取自 `ADDR_SCENARIO_INSTANCE` `:849`） | S2 |
| `L123`（S3）：「`:721` `HouseClass+0x577A` SpySatActive = 0」 | **`:855`** | S3 |
| `L124`（S4）：「`:682-689`」 | **`:816-823`** | S4 |
| `L132-135`（四键表：默认 / `LoadConfig` / 门控行号） | `EnableBuildingFog` 默认 `:173-174`（ini `:38`）｜`EnableBulletFog` `:176-177`（ini `:40`）｜`FadeFogTransition` `:179-180`（ini `:42`）｜**`EnableMinimapFog` 默认由 1 → 0 @ `:182`**（ini `:46` = 0）；生效路径由「汇编侧直接读 `g_enableMinimapFog`」改为 `GetEffectiveMinimapFog()`（`:96-106`）+ 镜像赋值（`:184`） | §3 四键表 |
| `L137`：「跨战局重载（四键共用，:680-689）」 | **`:816-823`**（`s_minimapForceRefresh=10` 置位 `:951`） | 跨战局重载 |
| `L241`：「`EnableMinimapFog` ｜ 默认 1 ｜ :100」 | **默认 0 @ `:182`**；ini `:46` = 0；`LoadConfig` 日志增补 `EnableMinimapFog` 字段（`:186-192`），并新增门控自证行 `:201` | §7 ini 键全表 |
| `L243`：「`ra2render/ra2render.ini` ≡ `ra2youli/ra2render.ini`（`fc`：no differences）」 | **仍然成立并加强**：两文件**同 SHA-256**（见题注），均 2,996 B / 14 键 | §7 尾注 |

> **未逐行复算的引用**：本节只覆盖「已被本任务取证命中」的行号（源码 grep + 逐段阅读 + `verify_hooks.py` JSON）。其余细粒度行号（如遥测累加点、`dllmain.cpp` 行号）**未在本任务复算**，如需全量刷新请另开「行号基线」任务（见交付回报 [4]）。

### 10.4 `tools/verify_hooks.py` 重跑输出（原文，本任务实跑）

```text
================================================================================
ra2render 已装 Hook 静态覆盖率自证 (verify_hooks.py)
================================================================================
Hook 实现符号      : 21
虚表安装 / 还原对  : 13 / 13
Inline 备份变量    : 7
ini 键 / LoadConfig: 14 / 13
Install* / Remove* : 3 / 3
--------------------------------------------------------------------------------
[1] 虚表 Install/Remove 对称
    OK  13 个虚表槽均有对应还原
[2] Inline 保存/还原对称 (s_orig*Bytes)
    OK  7 个备份变量均有还原路径
[3] Install*/Remove* 函数配对
    OK  3 对 Install/Remove 函数配对
[4] ini 键 vs LoadConfig
    !! ini 提供但 LoadConfig 未读: ['TargetScanKey']
[5] v1.6.0 四键强制覆盖
    OK EnableBuildingFog: ini=True loadconfig=True
    OK EnableBulletFog: ini=True loadconfig=True
    OK FadeFogTransition: ini=True loadconfig=True
    OK EnableMinimapFog: ini=True loadconfig=True
[6] 头文件 ADDR_* 死宏（cpp 未引用）
    ?  ADDR_VFUNC_* ×6 / ADDR_ORIG_* ×11 / ADDR_RADAR_PLOT / ADDR_RADAR_PLOT_CALLSITE / ADDR_RADAR_PENDING_* 等共 27 条
--------------------------------------------------------------------------------
结论: FAIL（存在缺口/不对称，见上）
================================================================================
```

> **两处必读说明（本节实测，供 Lead 判读，勿直接采信脚本判词）**：
> 1. **[4] 的 FAIL 为脚本假阳性**：`TargetScanKey` 在 `LoadConfig()` 中由 **`GetPrivateProfileStringA`** 读取（`:169-171`，字符串键），而脚本只统计 `GetPrivateProfileIntA`（ints）。⇒ 「14 / 13」的差额是键型差异，**不是配置漏读**。建议给脚本补字符串键扫描，或把该行降为 INFO。
> 2. **[2] 的 7 项全部 saved+restored**（JSON 字段 `inline_pairs` / `inline_unrestored: []`）⇒ 路线 A 引入 `s_origPlotCellBytes[9]` 后**未破坏**「备份 = 还原」对称；`s_origRadarPlotCallBytes` / `s_origRadarPlotPrologue` 两个旧备份变量已随下沉方案移除（A9 结论相应改为「走 `:1481` passthrough」）。
> 3. 本脚本**未覆盖** G-04 类「补丁字节在，但总闸关不掉」的语义缺口（A6）：`InstallCellClassDrawHook` 仍无条件打 B1/B2/L4 三处补丁，脚本判「对称」不等于「关得干净」。

### 10.5 本节对 §9 结论的净影响

| §9 原结论 | 本批状态 |
|---|---|
| 1. 对称性总体良好 | **维持**（13/13、3/3、Inline 7/7 saved+restored 实测复算） |
| 2. 「装了但没生效」集中在 RLE 空转 / 死符号 / `UnlockGameSpeed` 空开关 | **维持**（死宏 25 → **27**，其余对象未变） |
| 3. 「开关关不干净」：A6（B1/B2+L4 无键）、A8（SpySat 无还原） | **维持未闭环**（对应 G-04 / G-07） |
| 4. **联机唯一硬红灯** = L2 指针哈希节流 | **订正为 RISK**（见 §10.1）；`pointer` 分支与 `MpActive()` 判定失败仍是硬红灯面 |
| 5. v1.6.0 四键静态层完整、真机未验收 | **维持**（脚本 [5] 4/4 OK；真机验收 `[待实测]`）；**新增**：`EnableMinimapFog` 默认值已改 0（G-01 落地），联机下 `GetEffectiveMinimapFog()` 保守强制 false |
| 6. Q7 前置提醒：`0x006D3D99` 无条件 `jmp` | **维持未闭环**（G-04） |

---

## 11. 状态注记（追加节 · 2026-10-01 · 工单 `T-W1-Q / PK-1`）

> **只追加、不删改**：§0–§10（含 DA1 订正节）逐字保留。本节**只登记时效性**，不重算行号、不改任何 A1–A10 结论——本审计的十条「装了但没生效 / 开关关不干净」候选经本次抽查**仍成立**（抽查项见下表）。
> §10.3 末尾已自陈「其余细粒度行号未在本任务复算，如需全量刷新请另开『行号基线』任务」（`:346`）。本节就是把该提醒升级为一条**已确证的时效性偏差**。

### E-1 · 本审计的行号基线已再次过期（第三次）

| 口径 | 本审计正文 | DA1 订正（§10.3） | **2026-10-01 实测** |
|---|---|---|---|
| `blitter_hooks.cpp` 行数 | 1757 行（`:4, :321`） | 1892 行 / 86,961 B（`:321, :325`） | **3833 行**（`grep -c ""`），mtime 2026-09-30 22:01 |
| ini 键数 | 13（`:19, :229`） | 14（`:322, :343`） | **23**（本次实测 `ra2render/ra2render.ini`，按 `^键名=` 严格计数）；两份游戏目录 ini 各 **20** 键 |
| 虚表 `PatchVTablePointer` 槽 | 13/13（`:16`） | 13/13（`:325`） | 未重算（本包不覆盖；见下方「未闭环」U-1） |
| `0x006D3D99` 定性 | 「无条件 `jmp`＝force-full 基线，与 L4 折中冲突」（`:104, :268`） | 同 | **已被三档门控取代**：`blitter_hooks.cpp:65-69`（`g_l4DirtyMode` 0/1/2）、`:753-767`（读 `[FogOfWar] L4DirtyMode`，非法值收敛 force-full）、`:2489-2501`（桩内三档判定 + `s_l4RedrawSkippedStatic`）。故 §9 结论 6 的「维持未闭环（G-04）」现应读作：**「键已落地＝G-04 半消解；`vision-dirty`/`vanilla` 真机等价性仍未验」**（`RESULT_ZC10B.md:26-27`、`RESULT_ZC11.md:38,43`） |
| A8（SpySat 改 TYPE 无还原） | `:194`「只写不存原值；`RemoveVTableHooks` 不涉及」 | 定义迁移至 `:697-756` | **仍成立**（本次读码复算：`blitter_hooks.cpp:1441-1500` `PatchSpySatBuildingTypes` 直写 `SW+0xB0`(`:1459`)/`SW+0xF8`(`:1462`)/`Bld+0x16A5`(`:1483`)/`Bld+0x16F0`(`:1489`)，无任何原值备份；`grep -E "RestoreSpySat|g_spyBackup"` → 0 命中）。⇒ 落地规范 `pending_execution_master_table.md:136-151`（P-2.5 G-07 TYPE 备份/还原）**仍未实现**，本条是六包里少数「审计结论至今未变」的项 |

### E-2 · 新增一类「装了但没生效」的**部署侧**残留（本审计未覆盖的第三种形态）

本审计 §5.2 的 A1–A10 都在**代码内**找「装了不生效」。本轮普查补一类在**代码外**的：**DLL 已同步、ini 未带键 ⇒ 开关缺省 ⇒ 行为为 0**。

- 实测：三处 `ra2render.dll` sha256 全 = `626f98b6d6327b10dd4c2c68e2d295870ff50f1073fd48756d02000f10c596c1`（本次 `sha256sum`）；但 `ra2youli/ra2render.ini` 与 `ra2bench/ra2render.ini`（各 18412 B）内 **无** `EnableGapProtection` / `EnableVxlCachePrewarm` / `EnableSWChargeOpt`（本次 grep 0 命中），仅 `:186 L4DirtyMode=force-full`。
> 【W3 勘误 · W3-A6/ISSUE-STALE-L4-EXIST】改前：0 命中），仅 `:186 L4DirtyMode；改后：L4DirtyMode 已在 blitter_hooks.cpp:757 读取并支持 force-full / vision-dirty 模式；三处 ini 均已配置出厂值。；依据：ra2render/blitter_hooks.cpp:757; ra2render/ra2render.ini:251; ra2youli/ra2render.ini:186; ra2bench/ra2render.ini:186；分级：P1
- 后果：三张已落地卡在真实对局目录里**默认全关**（代码默认 0，`blitter_hooks.cpp:606/616/624`）。任何「已落地＝已生效」的表述都必须带 ini 态。
- 与本文 §8「还原路径总表」的关系：该表只讲软关/硬卸/彻底三档，未列「ini 缺键」这第四种**未启用**态。

### E-3 · 未闭环（本包不做，须由后续任务承接）

| # | 缺口 | 为何不在本包消解 | 下一步取证方法 |
|---|---|---|---|
| U-1 | §0 覆盖率自证的 13 槽 / 8(7) 个 `s_orig*Bytes` / 3 对 Install-Remove 的**当前**计数 | 本包为只读普查 + 状态登记，不重跑 `tools/verify_hooks.py`（且 `RESULT_ZC10B.md:195-205` 已记该脚本对现码判 FAIL 属既存死宏口径问题） | 由 zcode/Lead 在合入窗口重跑 `python tools/verify_hooks.py --json out/re_work/hook_audit/verify_hooks.json` 并把结论登记为新 §12 |
| U-2 | ZC-10B/ZC-GAP-P223 新增的挂钩/补丁是否已进入 §2 全量清单 | 需把 `:1–:3833` 逐段重排清单，属「行号基线」级任务 | 同上，另开任务 |
| U-3 | `R_anti_dup`（`docs/re/landing_conflict_matrix.md`）是否已把 L4 三档与 P-1 五点纳入同址体检 | 本包只读；`pending_execution_master_table.md` §七 与 `p1_cave` 自检均建议安装前置复核 | 见 `out/re_work/static_prep/p1_cave/README.md`「未闭环 #4」 |

> 本节全部依据为本次实跑的 `grep` / `sed` / `sha256sum` / `wc`；未启动游戏、未构建、未改 `ra2render/**`、未改 `gamemd.exe`。
