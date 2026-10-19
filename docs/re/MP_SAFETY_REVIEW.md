# 联机锁步安全复核（MP_SAFETY_REVIEW）

> 任务：**M-4** · 派工 v8 · 2026-09-26
> 基准红线：`docs/re/net_sync_checksum.md` **§5（地址级红线表）** 与 **§10（可安全优化 vs 联机红线结论表）**
> 复核对象：现网已装 **21 个 Hook 实现符号** + **4 项非 Hook 状态改写（S1–S4）**，含 v1.6.0 四键与 L2 三处 `unitHash = (uintptr_t)pThis >> 4`
> 证据源（只读）：`ra2render/blitter_hooks.cpp`（1757 行，17:18:42 构建）、`ra2render/ra2render.ini`、`docs/re/INSTALLED_HOOKS_AUDIT.md`、`REVERSE_ENGINEERING_AND_PATCHES.md` `[v1.6.0]` / `[v1.6.0-缺陷2]`
> 写作用域：本文件 + `out/re_work/mp_safety/**`；**不改** `ra2render/**`、台账、`gamemd.exe`
> 判定图例：
> - **SAFE** = 纯表现层，不进同步契约，联机锁步下可共存
> - **RISK** = 可能影响同步，需条件验证（全端同构建/同 ini/确定性键等）
> - **VIOLATION** = 确定违规（现网实现下必导致或高概率导致 desync）

---

## 0. 结论摘要

| 判定 | 条目 |
|---|---|
| **VIOLATION（3）** | #7 `Hook_Techno_SelectAutoTarget`、#8 `Hook_Unit_SelectAutoTarget`、#9 `Hook_Techno_Greatest_Threat`（含 Target Retention 联用）——三处共享 `unitHash = (uintptr_t)pThis >> 4` 节流键（`blitter_hooks.cpp:404/425/463`），指针哈希无跨端一致性契约 |
| **RISK（4）** | S1 `PatchSpySatBuildingTypes`（TYPE 补丁无还原）、S2 `ScenarioClass` 标志写、S3 `House+0x577A` 写、#9 在改确定性键后的语义偏离（缓存目标短路） |
| **SAFE（其余 17 + S4）** | Blit×6、Draw 剔除×5、Cell/混色×3、L4 全量刷、雷达×2——纯像素/重绘范围 |

**一句话**：现网构建在 `TargetScanInterval>1`（默认 8）下 **不可联机**；置 `TargetScanInterval=1` 可立即解除唯一硬违规。SpySat/Scenario/House 三处状态改写属「全端同 DLL+同 ini 才成立」的条件面，与原版客户端混联必分叉。

---

## 1. 红线基准（摘自 net_sync §5 / §10，判定时逐条对照）

| 基准 | 节号 | 与本次复核的耦合点 |
|---|---|---|
| **寻敌枚举序敏感**（`>` 择优、同分保留先到者） | §5.1「寻敌」、§10 #10 | Greatest_Threat 三路枚举 `0x6F8DF0`；任何返回值替代都等价于改选择结果 |
| **跳过/节流判定必须是 `CurrentFrame` 纯函数且全员一致** | §6.2、§10 #11 | SelectAutoTarget / Greatest_Threat 节流；禁止指针哈希、墙钟、线程调度 |
| **迷雾显示可动，迷雾判定禁动** | §5.3、§10 #3 | Draw 剔除只拦 `Draw` 虚函数；不碰 `IsShrouded 0x487950` / `IsCellShrouded 0x5865E0` / `RevealArea*` |
| **Blit / dirty-rect / 音频 = 安全** | §5.3、§10 #1–2 | Blit 族、L4 全量刷、雷达像素 |
| **可序列化状态**（`ScenarioClass` / `House` / Techno-Cell） | §4.2 | S2/S3 每帧写；Target `+0x5D4` 为 Techno 状态 |
| **RNG 流 / 命令序 / 帧 CRC = 禁止** | §5.1、§10 #14–16、#18 | 本批 Hook **无一触碰** RNG `0x65C780/0x65C7E0`、命令队列 `0x8B4204`、`Compute_Frame_CRC 0x64DAB0` |
| **TYPE/规则数据影响超武状态机** | M-3 收口：`IsCharged/Granted` 进 `v[13]` | S1 改 `SuperWeaponTypeClass+0xB0/+0xF8` → CD/半径 → 充能帧不同 → Checksum 归因分叉 |

---

## 2. 逐条复核（必覆盖 8 类 + 全量 21 Hook / S1–S4）

> 每条格式：**Hook 名 / 目标地址或虚表槽 / 是否写可序列化状态 / 是否改 RNG 或枚举序 / 判定 / 依据 / 建议**

### 2.1 `>>4` 节流（L2 · 三处，VIOLATION 核心）

| 字段 | 内容 |
|---|---|
| **Hook 名** | `TargetHooks::Hook_Techno_SelectAutoTarget` |
| **目标地址/槽** | `TechnoClass` v[265] = `0x007F4D84` → 原 `0x006FB010` |
| **写可序列化状态** | **间接**：跳过扫描 → 改变 `CurrentTargets(+0x458)` / 开火时机 → 位置/血量进帧 CRC |
| **改 RNG/枚举序** | 不直接改 RNG；**改寻敌调用时序** = 等价于改「谁在本帧被考虑」 |
| **判定** | **VIOLATION**（`TargetScanInterval>1` 时） |
| **依据** | `blitter_hooks.cpp:404` `uint32_t unitHash = (uintptr_t)pThis >> 4`；`:407` `((unitHash + currentFrame) % interval) != 0` 则 `return`。net_sync **§6.2**（跳过判定必须 `CurrentFrame` 纯函数）；**§10 #11**（不许只在部分端提前跑）；`[v1.6.0-缺陷2]` |
| **建议** | ① **联机即时门控**：`TargetScanInterval=1`（源码 `:406` 有 `g_targetScanInterval > 1` 短路，置 1 即全量原版扫描，零补丁）；② **根治**：节流键改为确定性量——推荐 `CurrentFrame % interval == 0`（全员同帧放行）或 `(objectId + CurrentFrame) % interval`（objectId 须为同步契约内字段，**禁止**指针）；③ 保留 ini 键与遥测，附「同种子同命令序下 `(this, ret, frame)` 序列一致」对拍验证 |

| 字段 | 内容 |
|---|---|
| **Hook 名** | `TargetHooks::Hook_Unit_SelectAutoTarget` |
| **目标地址/槽** | `UnitClass` v[265] = `0x007F6094` → 原 `0x00736CA0` |
| **写可序列化状态** | 同上（间接） |
| **改 RNG/枚举序** | 同上 |
| **判定** | **VIOLATION** |
| **依据** | `blitter_hooks.cpp:425` 同一 `unitHash = (uintptr_t)pThis >> 4`；`:428` 同一取模节流。net_sync §6.2 / §10 #11 |
| **建议** | 同上（两槽共用 `TargetScanInterval`，一键 `=1` 同时解除） |

| 字段 | 内容 |
|---|---|
| **Hook 名** | `TargetHooks::Hook_Techno_Greatest_Threat`（Inline + Target Retention） |
| **目标地址/槽** | **Inline** `0x006F8DF0`（9B：`E9 rel32 + NOP×4`，覆盖全兵种汇聚入口，台账 [v1.5.5]） |
| **写可序列化状态** | 本身**只读** `this+0x5D4` / `pTarget+0x6C` / `pTarget+0x81`；返回值改变后续 AI 开火/移动 → 间接写位置 |
| **改 RNG/枚举序** | 不改 RNG；**返回缓存目标 = 跳过三路枚举**，相对原版是「结果替代」（见 §3.2 专论） |
| **判定** | **VIOLATION**（`TargetScanInterval>1` 时，与 #7/#8 同源） |
| **依据** | `blitter_hooks.cpp:463` 第三处 `unitHash = (uintptr_t)pThis >> 4`；`:466-468` 节流帧 `return pTarget` 短路。net_sync §5.1「寻敌枚举序敏感」、§6.2、§10 #10–11；`[v1.6.0-缺陷2]` |
| **建议** | ① `TargetScanInterval=1` 可完全禁用短路路径（`:465` 同样要求 `interval > 1`）；② 若保留节流：键改 `CurrentFrame` 纯函数；③ Target Retention 语义（返回旧目标而非重扫）须在修复后单独做「同种子目标选择序列」回放对拍，确认全端逐帧一致 |

| 字段 | 内容 |
|---|---|
| **Hook 名** | `Hook_Unit_Greatest_Threat` |
| **目标地址/槽** | **未安装**（死代码，`:482` 仅转发给 Techno 版） |
| **写可序列化状态** | — |
| **改 RNG/枚举序** | — |
| **判定** | **SAFE（不生效）** |
| **依据** | `INSTALLED_HOOKS_AUDIT.md` §5-A2：无任何 `PatchVTablePointer` 安装点 |
| **建议** | 清理死符号；勿再按虚表槽补装（会与 inline 双挂钩） |

---

### 2.2 Greatest_Threat 目标保持：只读是否安全？缓存返回是否改枚举序？（必覆盖）

#### 2.2.1 只读字段（`blitter_hooks.cpp:455-459`）

| 读取 | 偏移 | 性质 | 是否安全 |
|---|---|---|---|
| `*(void**)(pThis + 0x5D4)` | Techno **Target** 指针 | 技术对象状态；进存档/Checksum（§4.2 Techno 域） | **只读安全**——不写回、不改值 |
| `*(int*)(pTarget + 0x6C)` | **Health** | 同上，帧 CRC / v[13] 均覆盖血量 | **只读安全** |
| `*(uint8_t*)(pTarget + 0x81)` | **InLimbo** | 对象生命周期标志 | **只读安全** |

**结论 1**：三处读取均为**纯读**可序列化状态，不改 RNG、不写对象、不改枚举容器 → 读取本身 **SAFE**。  
附加风险备注：前置 `IsBadReadPtr(pTarget, 0x84)` 在「对象已释放但指针未清」的极端情况下可能跨端判定不一致（一端可读、一端不可读）→ 若发生会分叉；属低概率边界，修复时建议改为「Target 非空且 `InLimbo==0 && Health>0` 的字段级判断」，去掉 `IsBadReadPtr` 参与控制流。

#### 2.2.2 返回缓存目标是否改枚举序？

| 问题 | 答案 |
|---|---|
| 是否改变三路枚举（桶 `0x887888` → 螺旋 Cell → 数组）的**弹出序**？ | **不直接改**——短路时**根本不进入枚举** |
| 是否改变 Greatest_Threat 的**返回值**（相对原版）？ | **是**。原版对当前全图候选做 `>` 严格大于择优；Retention 返回「上帧旧目标」，即使已出现更高威胁也不切换 |
| 等价效果 | 相当于**用缓存结果替代重算结果**——比「改枚举序」更强的偏离：原序下 `A` 应胜出，Retention 返回 `B` |
| 联机锁步影响 | 若**全端同帧、同条件**短路，各端都返回同一缓存目标（该指针值来自同步的 Techno 状态）→ 命令/开火一致，**锁步可维持**；若短路相位不一致（现网 `>>4` 即此）→ 一端切换目标、一端粘滞 → desync |
| 对照红线 | net_sync **§10 #10** 允许的「预过滤短接」要求「短接前后返回值相同」——Retention **不满足**该条；应归入 **§10 #11** 节流语义管理（跳过判定必须 `CurrentFrame` 纯函数） |

**结论 2**：返回缓存目标**不改枚举序，但改返回值**（结果替代）。在「确定性键 + 全端同构建」前提下可条件成立（**RISK**）；与现网 `>>4` 联用即 **VIOLATION**。

| 字段 | 内容（汇总条目） |
|---|---|
| **Hook 名** | `Hook_Techno_Greatest_Threat` · Target Retention 短路分支 |
| **目标地址/槽** | Inline `0x006F8DF0` |
| **写可序列化状态** | 否（短路本身只读）；返回值影响后续 AI 间接状态 |
| **改 RNG/枚举序** | 不改 RNG；**改返回值（非枚举序）** |
| **判定** | **RISK**（去指针键后）/ **VIOLATION**（现网） |
| **依据** | net_sync §10 #10–11、§5.1 寻敌；`blitter_hooks.cpp:451-479` |
| **建议** | `TargetScanInterval=1`（禁用短路）或键改 `CurrentFrame` 纯函数后，做目标选择序列回放对拍；`IsBadReadPtr` 移出控制流 |

---

### 2.3 各类 Draw 剔除（槽 69 · Unit / Infantry / Aircraft / Building / Bullet，必覆盖）

| 字段 | #11 `Hook_Unit_Draw` | #12 `Hook_Infantry_Draw` | #13 `Hook_Aircraft_Draw` |
|---|---|---|---|
| **目标地址/槽** | `0x007F5D84`（Unit v[69]）→ 原 `0x0073CEC0` | `0x007EB16C` → 原 `0x00518F90` | `0x007E23B8` → 原 `0x004144B0` |
| **写可序列化状态** | **否**——只拦 `Draw`；谓词 `ShouldDrawMobileObject` 只读 `Owner+0x21C` / `+0x9C/+0xA0` / `Cell+0xAC` | 同左 | 同左 |
| **改 RNG/枚举序** | **否** | 否 | 否 |
| **判定** | **SAFE** | **SAFE** | **SAFE** |
| **依据** | net_sync §10 #3「迷雾/黑幕显示=条件安全，只动绘制」；不触碰 `IsShrouded/IsCellShrouded/RevealArea*`；`s_visionGrid` 为 DLL 私有，不进档 | 同 | 同 |
| **建议** | 可联机共存；纯表现层甚至允许各端 ini 不同。保持不写逻辑状态 |

| 字段 | #14 `Hook_Building_Draw`（v1.6.0） | #15 `Hook_Bullet_Draw`（v1.6.0） |
|---|---|---|
| **目标地址/槽** | `0x007E3FD0` → 原 `0x0043D290` | `0x007E47F8` → 原 `0x00468090` |
| **写可序列化状态** | **否**；`s_everSeenGrid`（512×512）为 DLL 私有，对照 §4.2 **不进档** | **否**；命中判定不动（`Owner+0xB0` 只读） |
| **改 RNG/枚举序** | 否 | 否 |
| **判定** | **SAFE** | **SAFE** |
| **依据** | net_sync §10 #3；`INSTALLED_HOOKS_AUDIT.md` §2.4 | 同 |
| **建议** | 可联机；注意 everSeen 不进档（读档后侦察记忆丢失 = 体验问题，非 desync）。真机未验收（台账闸门） |

---

### 2.4 L4 `0x006D3D99` 全量刷（必覆盖）

| 字段 | 内容 |
|---|---|
| **Hook 名** | 视口全量重绘跳转补丁（无独立 Hook 符号，随 `InstallCellClassDrawHook` 安装） |
| **目标地址/槽** | `0x006D3D99`（原 6B `0F 8D 98 00 00 00` = `jge 0x006D3E37`）→ `E9 99 00 00 00 90`（`jmp 0x006D3E37`） |
| **写可序列化状态** | **否**——只改重绘范围（dirty-rect 域） |
| **改 RNG/枚举序** | **否** |
| **判定** | **SAFE** |
| **依据** | net_sync §10 #2「dirty-rect/重绘范围 = 安全」；`cell+0x5C` 只读 `CurrentFrame`。性能影响，无同步契约触碰 |
| **建议** | 联机可用。但**无独立 ini 键**（审计 A6）——`EnableStarCraftFog=0` 时该补丁仍生效，污染「关迷雾」基线；建议补 `[Render] L4DirtyMode=force-full\|off`（与 Q7/L4 折中对齐），或随总闸装卸。不改同步语义 |
> 【W3 勘误 · W3-A6/ISSUE-SECTION-L4DIRTYMODE】改前：[Render] L4DirtyMode；改后：[FogOfWar] L4DirtyMode=force-full；依据：ra2render/blitter_hooks.cpp:757; ra2render/ra2render.ini:251；分级：P0

---

### 2.5 雷达绘制代理 / MinimapFog（必覆盖）

| 字段 | #20 `Hook_RadarPlot_Proxy` | #21 `Hook_RadarPending_Proxy` |
|---|---|---|
| **目标地址/槽** | 调用点 `0x006574C3`（`call rel32` 等长替换）+ `0x00655C50` 前 5B 蹦床 | 调用点 `0x0065719A`（`call 0x00660530` 等长） |
> 【W3 勘误 · W3-A6/ISSUE-DISAMBIG-RADAR-HOOK】改前：0x006574C3；改后：0x006574C3（RadarClass::Plot_Cell 主循环调用点，见 ra2render.h:158；实际补丁下沉点位于 0x00655D38，见 blitter_hooks.cpp:150, 3016）；依据：ra2render/ra2render.h:158; ra2render/blitter_hooks.cpp:150, 2711, 2920, 3016, 3090；分级：P2
| **写可序列化状态** | **否**——像素覆写 `(c>>1)&0x7BEF`（**属雷达减暗体等价式，非 E1 目标**；见文末 §10.1【原记·反证】），走 `Set_Pixel [vt+0x24]` | **否**——只改「跳帧」判定返回值（`al`） |
| **改 RNG/枚举序** | 否 | 否 |
| **判定** | **SAFE**（同步维度） | **SAFE**（同步维度） |
| **依据** | net_sync §10 #7「雷达小点=安全」、#8「纯 FX 绘制=条件安全」；不写雷达单例逻辑字段 | 同；`s_minimapForceRefresh` 为 DLL 私有 |
| **建议** | 联机可用。⚠️ **稳定性独立问题**：`[v1.6.0-缺陷1]` 崩溃 EIP `0x5450202F`、栈回 `006574C8`，本路径为头号嫌疑（`Ecx=0x1A0` 疑似标量被当指针，`:1372` `test byte [ecx+0x12C], 8`）——联机前应默认 `EnableMinimapFog=0` 并补空指针守卫。此缺陷是**崩溃/稳定性**，不是 desync；但联机掉线同样致命 |

---

### 2.6 SpySat TYPE 补丁 / UpdateVisionGrid 写 Scenario / House（必覆盖）

| 字段 | **S1** `PatchSpySatBuildingTypes` |
|---|---|
| **目标地址/槽** | 懒加载于 `UpdateVisionGrid`（`:564-623`）；写 `SuperWeaponTypeClass+0xB0`（CD）、`+0xF8`（半径）、`BuildingTypeClass+0x16A5`（关全图 Reveal）、`+0x16F0`（PsychicReveal 索引） |
| **写可序列化状态** | **是（TYPE/规则数据）**——不直接进每帧 CRC，但改变超武充能/发射行为 → `SuperClass.IsCharged/Granted` 进 `v[13]`（M-3 实证） |
| **改 RNG/枚举序** | 不改 RNG；改超武状态机时序（充能帧不同） |
| **判定** | **RISK** |
| **依据** | net_sync §5.1「生产/建造」邻域 + M-3：`IsCharged/Granted/OneTime` 进 Checksum；TYPE 行为不一致 = 全端分叉。`[v1.6.0]` SpySat 重构语义 |
| **建议** | ① **联机最小集：`EnableSpySatRadarSweep=0`**（`:565` 直接 return，不打补丁）；② 若坚持启用：必须**全端同 DLL + 同 ini**（含 `RadarSweepCooldownFrames/RadiusCells`）；③ 补 Remove 还原（审计 A8：现无回滚）；④ 与原版客户端混联 = 确定 desync |

| 字段 | **S2** `UpdateVisionGrid` 写 `ScenarioClass` 标志 |
|---|---|
| **目标地址/槽** | `:715-718` `*(uint32_t*)scenarioBase &= ~0x1000u`（每逻辑帧） |
| **写可序列化状态** | **是**——`ScenarioClass` 整体进档（net_sync §4.2） |
| **改 RNG/枚举序** | 否；写常量子掩码 |
| **判定** | **RISK** |
| **依据** | net_sync §4.2 序列化范围；写的是恒定 0 位清除。若原版该位本就恒 0 → 实际无状态变化（近 SAFE）；若任何路径会置 1 → 改变可序列化全局。注释自证：「绝不可置 1，否则 Draw_Shroud / CellClass::Draw 全图变黑」 |
| **建议** | 全端同构建则逐位一致；混构建必坏。理想做法：仅当检测到该位非 0 时写入并打遥测，确认原版是否永不置位。无独立 ini（随 `UpdateVisionGrid` 执行） |

| 字段 | **S3** `UpdateVisionGrid` 写 `House+0x577A` SpySatActive |
|---|---|
| **目标地址/槽** | `:721` `*(uint8_t*)(pPlayer + 0x577A) = 0`（每逻辑帧） |
| **写可序列化状态** | **是**——`House` 进 `Save_Sides`（§4.2） |
| **改 RNG/枚举序** | 否；但**改 GapGenerator / SpySat 交互语义**（解除裂缝锁死） |
| **判定** | **RISK** |
| **依据** | net_sync §4.2 House 域；字段被原版 SpySat 逻辑读写。强制清零使「SpySat 永久揭示」失效、裂缝产生器恢复效力 = 玩法语义变更 |
| **建议** | ① 全端同 DLL 则各端都写 0 → 锁步可维持；② 混联（对方原版有 SpySat）= 分叉；③ **注意**：即使 `EnableSpySatRadarSweep=0`（S1 关闭），S3 **仍会执行**（无独立开关，且 `Hook_RadarPlot_Proxy:1347` 无条件调 `UpdateVisionGrid`）——联机最小集若要求零残留，需代码级把 S2/S3 挂到 SpySat 开关下（规格交 ZCode） |

| 字段 | **S4** 战局重载检测清私有网格 |
|---|---|
| **目标地址/槽** | `:682-689` 清 `s_everSeenGrid` / `s_fogRampFrame` / `s_spySatPatched` |
| **写可序列化状态** | **否**（DLL 私有） |
| **改 RNG/枚举序** | 否 |
| **判定** | **SAFE** |
| **依据** | §4.2 不进档清单；纯本地表现状态 |
| **建议** | 无同步风险。everSeen 不进档是体验遗留（审计 A10） |

---

### 2.7 Blit 家族 Hook（必覆盖，6 个）

| 字段 | #1 `Hook_BlitTransXlatAlphaZRead` | #2 `Hook_BlitTransXlat_G` | #3 `Hook_RLEBlitTransXlat_G` |
|---|---|---|---|
| **目标地址/槽** | `0x007E56F0+4` → 原 `0x00494B60` | `0x007E5A20+4` → 原 `0x004912B0` | `0x007E55C0+4` → 原 `0x004960A0` |
| **写可序列化状态** | 否（纯像素） | 否 | 否 |
| **改 RNG/枚举序** | 否 | 否 | 否 |
| **判定** | **SAFE** | **SAFE** | **SAFE**（仅遥测转发，见 A1） |
| **依据** | net_sync §10 #1「Blit/RLE/NonRLE = 安全」；不进 `0x64DAB0` 对象扫描，不在 CalculateChecksum 类目 | 同 | 同 |
| **建议** | 联机可用；SIMD 快路径仅在 `warpOffset==0 && aBuf==nullptr && XlatTable!=null` 启用，否则尾调原版——像素语义对齐即可 |

| 字段 | #4 `Hook_BlitTrans_G` | #5 `Hook_BlitTransDarken_G` | #6 `Hook_BlitPlain_G` |
|---|---|---|---|
| **目标地址/槽** | `0x007F7BF4+4` → 原 `0x007BC890` | `0x007E59F0+4` → 原 `0x00492670` | `0x007F7BC4+4` → 原 `0x007BC7F0` |
| **写可序列化状态** | 否 | 否 | 否 |
| **改 RNG/枚举序** | 否 | 否 | 否 |
| **判定** | **SAFE** | **SAFE** | **SAFE** |
| **依据** | §10 #1 | 同 | 同 |
| **建议** | 同上 |

---

### 2.8 B1 / B2 灰雾混色桩 + CellClass::Draw（必覆盖）

| 字段 | #17 `Hook_FogBlendB1_Stub` | #18 `Hook_FogBlendB2_Stub` |
|---|---|---|
| **目标地址/槽** | 补丁区 `0x0047F40F`（49B → `E9`+NOP，动态强度） | 补丁区 `0x0047F4AE`（51B → `E9`+NOP） |
| **写可序列化状态** | **否**（像素混色 `final = c - ((c-c50)*s>>8)`） | 同 |
| **改 RNG/枚举序** | 否 | 否 |
| **判定** | **SAFE** | **SAFE** |
| **依据** | net_sync §10 #1/#3 像素层；`s_fogBlendStrength` 为 DLL 全局，单线程渲染 |
| **建议** | 联机可用。**无独立 ini**（审计 A6）：`EnableStarCraftFog=0` / `FadeFogTransition=0` 时桩字节仍安装（后者仅 s 恒 256）——建议补独立键或随总闸装卸；不影响同步 |

> **【E1 勘误 · FOG-ERRATA · DSH 子代理 · 2026-09-27】** 本节的 **SAFE 判定维持不变**，但需就地标注一处**原版语义**口径：~~混色桩 B1/B2「替代引擎原生 **50% 减法**」~~ **【原记】** ⇒ 正确表述为「替代引擎原版 **FOG.SHP 逐像素 alpha 插值混色**」（独立反汇编证据见文末 **§10.1**）。
> **【原记·反证】** 本文现行快照 grep `50% 减法` / `50% 半化` / `减法` / `原生` 均 **0 命中**（`0x7BEF` 仅 §2.5 `L167`，属雷达像素覆写，**正确、不在本条范围**）。

| 字段 | #16 `Hook_CellClass_Draw`（+ `_Proxy`） |
|---|---|
| **目标地址/槽** | Inline `0x004801F0`（5B `E9 rel32`） |
| **写可序列化状态** | 否（只读 Cell `+0x24` MapCoords / `+0x12C` bit3） |
| **改 RNG/枚举序** | 否 |
| **判定** | **SAFE** |
| **依据** | §10 #3 显示层；灰雾追加绘制不改 Cell 状态 |
| **建议** | 联机可用 |

---

### 2.9 条目总表（21 Hook + S1–S4 一览）

| # | Hook / 动作 | 目标 | 写可序列化 | 改 RNG/枚举序 | 判定 | 建议（修复字节或 ini） |
|---|---|---|---|---|---|---|
| 1 | `Hook_BlitTransXlatAlphaZRead` | `0x7E56F0+4` | 否 | 否 | **SAFE** | 保持 |
| 2 | `Hook_BlitTransXlat_G` | `0x7E5A20+4` | 否 | 否 | **SAFE** | 保持 |
| 3 | `Hook_RLEBlitTransXlat_G` | `0x7E55C0+4` | 否 | 否 | **SAFE** | 保持（A1 空转待补） |
| 4 | `Hook_BlitTrans_G` | `0x7F7BF4+4` | 否 | 否 | **SAFE** | 保持 |
| 5 | `Hook_BlitTransDarken_G` | `0x7E59F0+4` | 否 | 否 | **SAFE** | 保持 |
| 6 | `Hook_BlitPlain_G` | `0x7F7BC4+4` | 否 | 否 | **SAFE** | 保持 |
| 7 | `Hook_Techno_SelectAutoTarget` | v[265] `0x7F4D84` | 间接 | 调用时序 | **VIOLATION** | `TargetScanInterval=1`；或键改 `CurrentFrame` 纯函数 |
| 8 | `Hook_Unit_SelectAutoTarget` | v[265] `0x7F6094` | 间接 | 调用时序 | **VIOLATION** | 同上 |
| 9 | `Hook_Techno_Greatest_Threat` | Inline `0x6F8DF0` | 间接 | 返回值替代 | **VIOLATION**（现网）/ **RISK**（修键后） | `TargetScanInterval=1` 禁短路；修键后对拍目标序列 |
| 10 | `Hook_Unit_Greatest_Threat` | 未安装 | — | — | SAFE（不生效） | 删死符号 |
| 11 | `Hook_Unit_Draw` | v[69] `0x7F5D84` | 否 | 否 | **SAFE** | 保持 |
| 12 | `Hook_Infantry_Draw` | v[69] `0x7EB16C` | 否 | 否 | **SAFE** | 保持 |
| 13 | `Hook_Aircraft_Draw` | v[69] `0x7E23B8` | 否 | 否 | **SAFE** | 保持 |
| 14 | `Hook_Building_Draw` | v[69] `0x7E3FD0` | 否（everSeen 私有） | 否 | **SAFE** | 保持（`EnableBuildingFog`） |
| 15 | `Hook_Bullet_Draw` | v[69] `0x7E47F8` | 否 | 否 | **SAFE** | 保持（`EnableBulletFog`） |
| 16 | `Hook_CellClass_Draw` | Inline `0x4801F0` | 否 | 否 | **SAFE** | 保持 |
| 17 | `Hook_FogBlendB1_Stub` | `0x47F40F` 49B | 否 | 否 | **SAFE** | 补独立 ini（A6） |
| 18 | `Hook_FogBlendB2_Stub` | `0x47F4AE` 51B | 否 | 否 | **SAFE** | 同上 |
| 19 | L4 全量刷补丁 | `0x6D3D99` 6B | 否 | 否 | **SAFE** | 补 `L4DirtyMode` 键（A6） |
| 20 | `Hook_RadarPlot_Proxy` | 调用点 `0x6574C3` | 否 | 否 | **SAFE**（同步） | 保持；联机默认关 `EnableMinimapFog`（缺陷1 崩溃） |
| 21 | `Hook_RadarPending_Proxy` | 调用点 `0x65719A` | 否 | 否 | **SAFE** | 同上 |
| S1 | `PatchSpySatBuildingTypes` | TYPE `+0xB0/+0xF8/+0x16A5/+0x16F0` | **是**（TYPE） | 超武时序 | **RISK** | `EnableSpySatRadarSweep=0`；或全端同 ini；补还原 |
| S2 | Scenario 标志 `&= ~0x1000` | `ScenarioClass+0` | **是** | 否 | **RISK** | 全端同构建；验证原版是否恒 0 |
| S3 | `House+0x577A=0` | House 域 | **是** | 否 | **RISK** | 全端同构建；挂到 SpySat 开关下 |
| S4 | 战局重载清网格 | DLL 私有 | 否 | 否 | **SAFE** | 保持 |

---

## 3. 判定推导说明（关键争议点）

### 3.1 为何 `>>4` 是 VIOLATION 而非 RISK

1. 联机为**确定性锁步**（net_sync §0.1/§1.1）：各端同一逻辑帧必须做同一决策。
2. 节流键 `unitHash = (uintptr_t)pThis >> 4` 来自**堆指针**。指针值取决于分配顺序、ASLR、加载路径——**没有任何同步契约**保证跨端一致（§6.2 明文禁止「指针哈希」）。
3. 节流相位不同 → 端 A 本帧扫描并开火、端 B 本帧跳过 → 伤害/移动时序分叉 → 位置进 `0x64DAB0` 帧 CRC → desync（静默、难复现）。
4. 该缺陷已被 Lead 独立复核源码并登记 `[v1.6.0-缺陷2]`；本复核维持 **VIOLATION** 判定。
5. **`TargetScanInterval=1` 是零补丁止血**：`:406/:427/:465` 均有 `if (g_targetScanInterval > 1 && …)`，置 1 后三处短路分支永不进入，行为回到原版全量扫描。

### 3.2 Greatest_Threat Retention：读安全，返值需条件

- **读** `+0x5D4/+0x6C/+0x81`：纯读同步契约内状态，SAFE。
- **返回缓存目标**：跳过三路枚举，用旧目标替代「当前最大威胁」——**不改弹出序（未枚举），但改返回值**。全端同帧同结果时锁步可维持；相位不一致即 desync。
- 与 §10 #10「短接前后返回值相同」的允许形态不符 → 不能按「空间哈希优化」豁免，按 §10 #11 节流管理。

### 3.3 纯表现层为何允许各端 ini 不同

Draw 剔除 / Blit / 灰雾 / 小地图灰化只改**像素与重绘范围**，不进 `0x64DAB0` 帧 CRC、不进 `v[13]` Checksum、不进存档（§4.2 不进档清单）。锁步只要求**逻辑状态**一致；两端「一端看得见、一端看不见」不产生 desync（观感差异，不同步分叉）。  
例外：**不要**把「显示剔除」误接到 `IsShrouded/IsCellShrouded/RevealArea*` 判定上——那是 §10 #3 的红线。

### 3.4 S2/S3 的「常量写」为何仍标 RISK

写入值本身是常量（`0`），全端同构建时逐位一致；但它们落在**可序列化全局**（Scenario / House）上：
- 与原版客户端混联时，原版可能在某些帧持有非 0 值（SpySatActive）→ 状态分叉；
- 存档兼容性：本 DLL 写出的 House 状态与原版语义不同（裂缝/SpySat 交互）。
故不能标 SAFE，需「全端同 DLL+同 ini」条件验证。

---

## 4. 联机构建推荐 ini · 最小安全集

### 4.1 绝对最小（解除全部 VIOLATION，1 行）

```ini
[Logic]
TargetScanInterval=1
```

> 原理：三处节流短路均要求 `interval > 1`；置 1 后 SelectAutoTarget / Greatest_Threat 全量走原版，`>>4` 键不再参与任何控制流。  
> **仅此一行即可解除唯一硬违规。** SpySat/Scenario/House 的 RISK 面仍在（见 4.2）。

### 4.2 推荐联机配置（最小安全集 · 建议默认）

```ini
; ===== 联机锁步安全配置（MP_SAFETY_REVIEW 推荐） =====
[Render]
EnableSIMD=1              ; SAFE 纯像素，可保留

[Logic]
TargetScanInterval=1      ; ★必改★ 禁用指针哈希节流（VIOLATION 止血）

[Speed]
UnlockGameSpeed=0         ; no-op，无同步影响

[System]
EnableLFH=1               ; 进程级，SAFE
HighPrecisionTimer=1      ; 显示定时，SAFE（不进 CurrentFrame）

[FogOfWar]
; —— 同步契约面（RISK）：关闭以消除 TYPE/全局写 ——
EnableSpySatRadarSweep=0  ; ★必改★ 禁用 S1 TYPE 补丁（无还原、改超武状态机）
; RadarSweep* 仅在 SpySat=1 时生效，联机保持默认即可
RadarSweepCooldownFrames=600
RadarSweepRadiusCells=16

; —— 纯表现面（SAFE）：联机可开可关，不影响锁步 ——
; 若追求与原版观感一致或担心缺陷1崩溃，可全部置 0
EnableStarCraftFog=1      ; Draw 剔除，SAFE
EnableBuildingFog=1       ; SAFE
EnableBulletFog=1         ; SAFE
FadeFogTransition=1       ; SAFE
EnableMinimapFog=0        ; SAFE（同步维度），但缺陷1 崩溃路径未修 → 建议默认 0
```

### 4.3 最保守（与原版客户端混联 / 疑难排障用）

```ini
[Logic]
TargetScanInterval=1

[FogOfWar]
EnableStarCraftFog=0
EnableSpySatRadarSweep=0
EnableBuildingFog=0
EnableBulletFog=0
FadeFogTransition=0
EnableMinimapFog=0
```

> ⚠️ **注意**：即便全部 fog 键置 0，以下补丁**仍安装且生效**（审计 A6 / 本复核实证）：
> - L4 `0x006D3D99` 全量刷（无键）
> - B1/B2 混色桩（无键）
> - **S2 Scenario 标志写、S3 House+0x577A 写**（`Hook_RadarPlot_Proxy:1347` 无条件调 `UpdateVisionGrid`）
> 
> 与**原版 gamemd（无 DLL）**混联仍不安全。**混联场景只能整局不加载 `ra2render.dll`。**

### 4.4 全端一致前提（若要保留 SpySat 重构等玩法）

- 所有客户端：同一 `ra2render.dll` 构建 + 同一 `ra2render.ini`（含 `TargetScanInterval=1` 与 SpySat 三键）。
- 验收探针：net_sync §11 H-D5 逐帧 CRC 镜像 + H-D6 命令流镜像双端对拍，零差异方可放行。

---

## 5. 修复优先级（供 ZCode / 落地轨道）

| 优先级 | 项 | 动作 | 回滚 |
|---|---|---|---|
| **P0** | `>>4` 节流 VIOLATION | ini `TargetScanInterval=1`（即时）；源码键改 `(CurrentFrame) % N` 或对象逻辑 ID | ini 恢复；源码开关 `MPTargetThrottle=0/1` |
| **P0** | 缺陷1 雷达崩溃 | `EnableMinimapFog` 默认 0；`Hook_RadarPlot_Proxy` 补 `pCell`/`s_radarThis` 空指针与 `+0x12C` 范围守卫 | `RemoveRadarFogHooks` 已对称 |
| **P1** | S1 TYPE 无还原 | 保存原 `+0xB0/+0xF8/+0x16A5/+0x16F0` 并提供 Remove | 进程内还原 |
| **P1** | S2/S3 无门控 | 挂到 `EnableSpySatRadarSweep`（或新键 `MPStateWrites=0`） | ini |
| **P2** | A6 三补丁无独立键 | `L4DirtyMode` / 混色桩独立键 | ini |
| **P2** | Retention 修键后对拍 | 同种子目标序列日志 vs 原版 | 对拍不过则禁短路 |

---

## 6. 遗留与边界

1. **`IsBadReadPtr` 参与控制流**（`:455/:457`）：极端悬垂指针时跨端可能判定不一致；建议移出控制流（§2.2.1）。
2. **everSeen 不进档**（A10）：非 desync，读档后需重新侦察；若要持久化须另设计（进档 = 进同步契约，需 bump 存档魔数，§5.1）。
3. **L4 折中（Q7）**：`0x006D3D99` 现为无条件 `jmp`；折中方案（恢复 `jge` + `0x006DA7D0` 打脏）落地时须给独立键——同步维度两种实现均 SAFE。
4. **Particle/ParticleSystem Draw** 未安装（Owner 偏移实证后）：未来挂载须扩展槽 69 既有 `FogHooks`，只动绘制层（§10 #8）。
5. **本复核为静态审计**（`[静态核验]`）：未跑真机双端对拍；联机放行前建议用 H-D5/H-D6 镜像做 ≥3 局双端逐帧 CRC 一致性实测。

---

## 7. 产出物

| 路径 | 说明 |
|---|---|
| `docs/re/MP_SAFETY_REVIEW.md` | 本文档 |
| `out/re_work/mp_safety/` | 本任务工作目录（预留探针输出） |

> **台账 §九 草稿**（供 Lead 合并）：
> ```
> ### [v1.5.x] - 联机锁步 MP 安全复核（纯审计，无补丁）
> #### 1. 现象与需求描述
> - 以 net_sync §5/§10 红线逐条对照现网 21 Hook + S1–S4，判定联机锁步安全性。
> #### 2. 逆向调研与根因剖析
> - VIOLATION×3：L2 节流 unitHash=(uintptr_t)pThis>>4（:404/:425/:463）跨端不确定；
> - RISK×4：SpySat TYPE、Scenario 标志、House+0x577A、Threat Retention 返回值替代；
> - SAFE：Blit×6、Draw 剔除×5、Cell/混色/L4/雷达（纯表现）。
> #### 3. 具体修改与补丁实现
> - 无代码补丁。产出 MP_SAFETY_REVIEW.md。
> #### 4. 实测验证效果
> - [静态核验]；止血 = TargetScanInterval=1；双端 CRC 对拍待实测。
> ```

---

## 8. 附录 · 勘误标记（收尾-C / task-13，2026-09-26）

> **性质**：本文成文于 Lead 终局裁定之前（全文不含 `G-01…G-10` 编号）。本附录仅登记「本文判断 → 终局裁决」的收敛关系，**不改动正文**（§0–§7 与台账草稿逐字保持原样）。
> **维持不变的结论**：§0 判定（VIOLATION×3 = #7/#8/#9；RISK×4 = S1/S2/S3/#9 语义；SAFE = 其余 17 + S4）、§3.1 的 `>>4` 指针哈希推导、§4.1「`TargetScanInterval=1` 即解除唯一硬违规」**全部维持**（收尾复核见 `docs/re/mp_landing_consistency.md` §2）。

> **[DA1 勘误 · 2026-09-27]** 上述「全部维持」**不再成立**：G-01 / G-02 / G-08 **三项已收口**（MPS 落地），#7/#8/#9 默认键降为 RISK，`>>4` 推导仅对 `pointer` 分支成立。逐条对照见文末 **§9.1 / §9.2**。
> **权威落点**：`docs/re/mp_release_safety_checklist.md` §一 L19-24（R-01…R-04）+ §三 L60-71；`docs/re/ARCHITECTURE_ATLAS.md` §9.4 L1530-1544。

| 本文条目（行号） | 本文口径 | 终局裁决（勘误后） |
|---|---|---|
| §4.2 `L363` `EnableMinimapFog=0`（建议默认关） | 建议（缺陷1 崩溃路径未修） | **采纳并升级**：`EnableMinimapFog` **API 默认强制 0**（G-01 / R-01，P0），防键缺失静默全开 |
| §5 `L399` P0「ini `TargetScanInterval=1`（即时止血）」 | ini 级止血 | 升级为**联机无条件强制 `g_targetScanInterval = 1`**（G-08 / R-03，P0）；ini 兼容保留 |
| §5 `L399` P0「源码键改 `CurrentFrame % N` 或对象逻辑 ID」 | 待定根治方案 | 维持为**根治方向**；联机侧不再等待（强制 interval=1 先行，G-02 强制 `position` 键） |
| §5 `L400` P0「`EnableMinimapFog` 默认 0」（理由：缺陷1 崩溃） | 建议 | 与 R-01 同向，理由升格为「防键缺失静默全开」（G-01） |
| §5 `L401` P1「S1 TYPE 无还原 → 保存原 `+0xB0/+0xF8/+0x16A5/+0x16F0` 并提供 Remove」 | 建议 | **采纳为 G-07**（MP-G07，P1）：备份 + `RemoveVTableHooks` 尾部还原；还原本体**不进同步契约**（TYPE 不入 `.SAV`），S1 写出仍为「全端同 DLL + 同 ini」条件面 |
| §5 `L402` P1「S2/S3 无门控 → 挂到 `EnableSpySatRadarSweep`（**或**新键 `MPStateWrites=0`）」 | 二选一未定 | **定为 `[Multiplayer] MpStateWrites=0`**（G-06，P1）；`MpActive()` 旁路为实现手段，不再以 `EnableSpySatRadarSweep` 为载体 |
| §5 `L403` P2「A6 三补丁无独立键 → `L4DirtyMode` / 混色桩独立键」 | 独立键 | **定为接入 `EnableStarCraftFog` 总闸**（G-04，P1）：总闸=0 时不写 `0x47F40F` / `0x47F4AE` / `0x6D3D99` 并逐字节还原；独立键（`L4DirtyMode` 等）作补充 |
| §5 `L404` P2「Retention 修键后对拍，不过则禁短路」 | 无独立键，仅靠对拍 | **增设 `[Logic] EnableThreatRetention=1`**（单机默认 1、联机强制 0）（G-03 / MP-G03，P1） |
| §2.5 `L162-174`（雷达代理 / MinimapFog，仅判 SAFE，未提 #21 门控） | 未覆盖 | 补 **G-05 / R-04**（P2）：`Hook_RadarPending_Proxy`（`0x0065719A` 入口）前置 `cmp byte ptr [s_minimapFogGate], 0; je orig_logic`，`EnableMinimapFog=0` 时与 `call 0x00660530` 逐帧等价 |
| §6.2 `L411`「everSeen 不进档（A10）：非 desync，读档需重新侦察」 | 已知体验限制 | **采纳为 G-09**（MP-G09，P2）：维持本文判断；`s_everSeenGrid` 为 DLL 私有网格、不入 `.SAV`、不进帧 CRC，不阻断发布 |
| §4.4 `L390`「所有客户端：同一 DLL + 同一 ini」 | 全端一致前提 | 维持；补充：G-01/G-05/G-08 属**单端即可违规**项，故必须在代码层强制（不能只靠 ini 纪律） |

**附注（两条）**

1. **证据勘误（G-01）**：本文 §4.2/§4.3 的 ini 建议（`EnableMinimapFog=0`）现行工作树**未落地**——`ra2render/ra2render.ini` 第 45 行为 `EnableMinimapFog=1`（两份 ini 副本字节一致），源码 `blitter_hooks.cpp:103` 默认参数仍为 `1` [实证]。G-01 缺口的准确表述是「**键缺失/漏配即静默全开**」。
2. **未决措辞归零**：本文 §5/§6 中所有「或 / 二选一」形态（`L402` 等）自本附录起以 checklist §一/§三 与 atlas §9.4 的单一裁决为准；正文保留原文仅为审计痕迹。G-07/G-09 的专项结论与依据见 `docs/re/mp_landing_consistency.md` §2.3。

---

## 9. 勘误 · MPS 落地后的状态同步（DA1 · DSH 子代理 · 2026-09-27）

> **性质**：只**追加**本节，**不改动 §0–§8 与台账草稿**（L1-465 逐字保留）。
> **双快照**：正文 = 17:18 构建（全文不含 G-01…G-10 编号，见 §8 声明）；本节 = **`blitter_hooks.cpp` 1892 行 / 86,961 B**（2026-09-27 09:06:28）。
> **基线（只读未变）**：`ra2youli/gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`；`python tools/verify_anchors.py` = **323/323 PASS**（本任务实跑）。
> **部署件**：`ra2render/ra2render.dll` ≡ `ra2youli/ra2render.dll` = 129,536 B，SHA-256 `E7FA669C85B5DA53C71898DC453AC35301EC55F1222D1D581BFAEAC105DCC7CA`；`ra2render.ini` ≡ `ra2youli/ra2render.ini` = 2,996 B / 14 键，SHA-256 `564A265291C3C6CAF0E15CE8CFF00360A0BBD28EAF2E57BA74D1E0E49C0EC64F`。

### 9.1 §8「全部维持」⇒ **改为「三项已收口（G-01/G-02/G-08）」**

| §8 原表述（行号） | 更正表述 | 依据 |
|---|---|---|
| §8 导语 `L445`：「**维持不变的结论**：§0 判定（VIOLATION×3 = #7/#8/#9；RISK×4 = S1/S2/S3/#9 语义；SAFE = 其余 17 + S4）、§3.1 的 `>>4` 指针哈希推导、§4.1「`TargetScanInterval=1` 即解除唯一硬违规」**全部维持**」 | **订正为**：① **G-01 / G-02 / G-08 三项已收口**（2026-09-27 MPS 落地，代码层闭环）；② `>>4` 指针哈希推导**仅对 `TargetScanKey=pointer` 分支仍成立**（默认键已改 position 空间哈希）；③ §4.1 结论**仍成立且更强**（默认键下三处短路已由联机强制 `interval=1` 关闭，`interval=1` 从「必须手工配置」升为「联机自动强制」）；④ SpySat/Scenario/House（S1/S2/S3）**仍为未闭环** | 源码 `:82-94`、`:264-282`、`:182`；`mp_release_safety_checklist.md` §一 R-01/R-02/R-03 + 文末 §六；`hook_gate_gap_table.md` §9 |
| §8 表首行 `L450`：「§4.2 `L363` `EnableMinimapFog=0`（建议默认关）｜建议（缺陷1 崩溃路径未修）」 | **升格**：§4.2 的建议**已落地为 API 默认 0 + ini 0 + 联机强制 0**；理由由「缺陷1 崩溃」升格为「防键缺失静默全开」（G-01/R-01）；**用户决策（2026-09-27）**：保持默认关 | 源码 `:16` / `:182` / `:96-106`；ini `:46`；门控日志 `:201` |
| §8 表 `L451`：「§5 `L399` P0「ini `TargetScanInterval=1`（即时止血）」｜ini 级止血」 | **升级为已落地**：联机（`MpActive()`）**无条件**强制 `g_targetScanInterval = 1`（`GetEffectiveTargetScanInterval()` `:82-87`），ini 兼容保留 | 源码 `:82-87`、三处调用点 `:536` / `:558` / `:597` |
| §8 表 `L452`：「§5 `L399` P0「源码键改 `CurrentFrame % N` 或对象逻辑 ID」｜维持为**根治方向**」 | **维持等待**：现网采用「默认空间哈希 + 联机强制 position/interval=1」的**缓解式**收口；`CurrentFrame` 纯函数轮转仍为根治方向（未落地） | `hook_gate_gap_table.md` §3 建议②仍未实现 |
| §8 附注 1（`L464`）：「证据勘误（G-01）… `ra2render/ra2render.ini` 第 45 行为 `EnableMinimapFog=1`（两份 ini 副本字节一致），源码 `blitter_hooks.cpp:103` 默认参数仍为 `1` [实证]」 | **该附注本身已成为过期陈述**：本快照 `ra2render.ini:46 = EnableMinimapFog=0`（两份副本**同 SHA-256**），API 默认参数**已改为 0** @ `:182`。⇒ G-01 缺口收敛为「**API 默认 0 + ini 0；仅显式 `=1` 才开启**」，R-01 **已落地**（由 P0 缺口转「待真机验收」） | 本任务实测：ini `:46`；源码 `:16` / `:182`；ini 双副本 SHA-256 同值 |

### 9.2 #7/#8/#9 判定口径更正（与 `INSTALLED_HOOKS_AUDIT.md §10.1` 同口径）

| 位置（行号） | 原口径 | 更正口径 | 依据 |
|---|---|---|---|
| §0 摘要 `L19`、§2.1 `L53` / `L63` / `L73`、§2.9 表 `L269-271` | 「**VIOLATION（3）**：#7/#8/#9 —— 三处共享 `unitHash = (uintptr_t)pThis >> 4`（`blitter_hooks.cpp:404/425/463`），指针哈希无跨端一致性契约」 | **默认键（`TargetScanKey=position`）下 = RISK（待对拍）；`TargetScanKey=pointer` 分支 = VIOLATION**。三处键已收敛为 `ThrottleKey()`（默认 position 坐标空间哈希；仅 pointer 分支保留 `>>4`） | 源码 `:264-282`（`:267` pointer / `:271-277` position）；`hook_gate_gap_table.md` §1.2 / §3 |
| §2.1 `L54` / `L64` / `L74` | 「`blitter_hooks.cpp:404`…`:407` `((unitHash + currentFrame) % interval) != 0` 则 `return`」等三条 | 现网行号 **`:534-541` / `:556-563` / `:595-603`**；公式不变；`interval` 改由 `GetEffectiveTargetScanInterval()` 取得（联机恒 1 ⇒ 短路恒不触发） | 源码逐行 |
| §2.2.1 `L91` 表：「只读字段（`blitter_hooks.cpp:455-459`）」 | 现网 **`:586-592`**（`+0x5D4` Target / `+0x6C` Health / `+0x81` InLimbo 三处只读，结论「纯读安全」不变） | 源码逐行 |
| §2.2.2 `L112`：「与现网 `>>4` 联用即 **VIOLATION**」 | **订正**：与**默认 position 键**联用时降为 **RISK**（返回缓存目标 = 结果替代，仍需对拍）；与 `pointer` 键联用才为 VIOLATION | 同上 |
| §3.1 `L296`：「节流键 `unitHash = (uintptr_t)pThis >> 4` 来自**堆指针**」 | **仅对 `TargetScanKey=pointer` 分支成立**；默认分支的键为同步契约内的格子坐标（`this+0x9C/0xA0`），全端同帧同坐标 ⇒ 相位逐帧一致 | 源码 `:271-277` |

### 9.3 雷达挂钩点更正（`0x006574C3` → 路线 A `0x00655D38`）

| 位置（行号） | 原表述 | 更正表述 | 依据 |
|---|---|---|---|
| §2.5 `L166`：「调用点 `0x006574C3`（`call rel32` 等长替换）+ `0x00655C50` 前 5B 蹦床」 | **路线 A 下沉**：`0x00655D38` 9 字节补丁（`E9 rel32` + 4×`90`）+ 跳板（还原 9 字节后 `jmp 0x00655D41`）；`0x0065719A` 仍为 5 字节 `call` 等长替换 | 源码 `:1471-1473`、`:1570-1620`；字节 `0x00655D38 = 89 44 24 28 A1 50 35 B7 00`（`out/re_work/da1/claims.txt`） |
| §2.5 `L171`：「本路径为头号嫌疑（`Ecx=0x1A0` 疑似标量被当指针，`:1372` `test byte [ecx+0x12C], 8`）」 | **结论不撤回**，但行号订正：现网 `test byte ptr [eax + 0x12C], 8` @ **`:1496`**，且上游新增两道护栏（`cmp eax, 0x10000 / jbe` @ `:1490-1491`；`cmp eax, 0x00ABDC50 / je` @ `:1492-1493`）；`Hook_RadarPending_Proxy` 亦增 `s_minimapFogGate` 前置（`:`1555-1556`） | 源码 `:1476-1549` |
| §2.9 表 #20（`L282`）：「`0x6574C3`」 | 改为 `0x00655D38`（9B）+ `0x0065719A`；两处旧宏 `ADDR_RADAR_PLOT` / `ADDR_RADAR_PLOT_CALLSITE` 为 cpp 零引用死宏（`ra2render.h:76-77`） | `tools/verify_hooks.py` 死宏清单（27 条含此二宏） |

### 9.4 S2/S3「无条件被雷达路径调用」更正

| 位置（行号） | 原表述 | 更正表述 | 依据 |
|---|---|---|---|
| §2.6 S3 `L202`：「**注意**：即使 `EnableSpySatRadarSweep=0`（S1 关闭），S3 **仍会执行**（无独立开关，且 `Hook_RadarPlot_Proxy:1347` 无条件调 `UpdateVisionGrid`）」 | **前半成立、后半作废**：路线 A 落地后**雷达代理不再调用 `UpdateVisionGrid`**；当前仅 4 处绘制谓词调用（`:984` / `:1056` / `:1105` / `:1141`），且均在对应 fog 键门控之后 ⇒ 全 fog 键=0 时 S2/S3 **不执行**。S3「无独立开关」结论仍成立 | 源码 `:961-1141`（`ShouldDrawMobileObject` / `ShouldDrawBuilding` / `ShouldDrawBullet` / `Hook_CellClass_Draw` 四处）；`hook_gate_gap_table.md` §1.6「重要修正」 |
| §4.3 `L384` 注：「**S2 Scenario 标志写、S3 House+0x577A 写**（`Hook_RadarPlot_Proxy:1347` 无条件调 `UpdateVisionGrid`）」 | 同上传订：调用来源改为 4 处绘制路径（均受 fog 键门控）；**「混联仍不安全、整局不加载 DLL」的结论不变** | 同上 |
| §2.6 S1 `L179`：「懒加载于 `UpdateVisionGrid`（`:564-623`）…（`:565` 直接 return，不打补丁）」 | 行号订正：`PatchSpySatBuildingTypes` **`:697-756`**（入口 `if (!g_enableSpySatRadarSweep) return;` @ **`:698`**）；懒加载调用点 `:842-844` | 源码逐行 |
| §2.6 S4 `L206`：「`:682-689` 清 3 个私有网格」 | **`:816-823`**（清 `s_everSeenGrid` / `s_prevVisionGrid` / `s_fogRampFrame` / `s_spySatPatched`，置 `s_minimapForceRefresh=10` @ `:951`） | 源码 `:816-823` |

### 9.5 其余维持不动（避免过度订正）

| 项 | 状态 |
|---|---|
| Blit×6 = SAFE（§2.7 / §2.9 #1-#6） | **维持**（纯像素，不进帧 CRC / 存档） |
| Draw 槽 69 剔除×5 = SAFE（§2.3 / §2.9 #11-#15） | **维持** |
| CellClass::Draw / B1 / B2 / L4 = SAFE（§2.8 / §2.9 #16-#19） | **维持**（同步维度 SAFE）；A6「无独立键、关不干净」仍为未闭环（G-04） |
| S1/S2/S3 = RISK（§2.6） | **维持未闭环**（G-06/G-07 未落地） |
| S4 = SAFE（DLL 私有） | **维持** |
| §4.1「`TargetScanInterval=1` 解除唯一硬违规」 | **维持并加强**（现由联机自动强制，且默认键已非硬违规） |
| §6 遗留 1「`IsBadReadPtr` 参与控制流（`:455/:457`）」 | **维持**：现网参与控制流处为 `:533` / `:555` / `:594`（+ 各谓词内 `__try` 体系），结论「建议移出控制流」不变 |

> **本节不宣称「零风险 / 无 Desync」**：G-01/G-02/G-08 的收口为**代码层静态结论**，真机 ≥3 局双端逐帧 CRC 对拍（§4.4 验收探针）**未执行**，仍记 `[待实测]`；G-03/G-04/G-06/G-07 未落地，`FeatureSinglePlayer` 逃生舱不存在（grep 0 命中）。

---

## 10. 勘误 · FOG-ERRATA E1（B1/B2 原版语义）就地订正（DSH 子代理 · 2026-09-27）

> **标注约定（F4 自查口径）**：本节整体即**勘误块**；节内凡出现被推翻措辞者，必带 **【原记】**（引文）或 **【原记·反证】**（证据/计数）标注。
> **性质**：本节**追加**（§0–§9 逐字保留）+ 在 §2.8 就地加指路标。**不改动本文任何原有判定**。
> **依据**：FOG-SWITCH 定谳 + **本任务独立反汇编复核**（capstone 5.0.7；脚本/产物见 `out/re_work/fog_errata/**`）；凡本任务复算与清单不一致者以本任务独立结果为准 —— 本批**无**不一致项。
> **快照**：本节实测 `blitter_hooks.cpp` **2346 行 / 117,930 B**（2026-09-27 15:21:17，SHA-256 `AC07312974516B01C5B12AEA3F5E624543841DCA3C7DE3C515246C684B66C718`）；本文正文 = 17:18 构建（1757 行）⇒ 正文 `:行号` 仅作溯源（本文 §9.3/§9.4 已作过同类行号订正）。
> **基线（只读未变）**：`ra2youli/gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`；`python tools/verify_anchors.py` = **323/323 PASS**；`python tools/audit_bytes.py out/re_work/fog_errata/claims.txt` = **7/7 OK**。

### 10.1 E1（产品决策级）· B1/B2 替代的是「FOG.SHP alpha 插值混色」（~~「引擎原生 50% 减法」~~ **【原记】不成立**）

| 项 | 内容 |
|---|---|
| **涉及位置** | §2.8（B1/B2 灰雾混色桩，`L237-246`）、§2.9 表 `#17/#18`（`L279-280`）、§4.3 注（`L381-386`） |
| ~~改前口径~~ **【原记】** | ~~混色桩 B1/B2「替代引擎原生 **50% 减法**」~~（历史措辞；【原记】引文出自 FOG-SWITCH 勘误清单 E1。**本文现行快照 grep 0 命中**，见下「全篇排查」） |
| **订正口径【原记·反证】** | 两桩替代的是引擎原版 **FOG.SHP 逐像素 alpha 插值混色**：`mov cx,[eax]`（读目标像素）→ `cmp cx,0x7f` → `and ecx,0xFFFF` / `and edx,0xFF`（取 alpha 字节）→ **`lea ecx,[ecx+edx-0x7f]`**（以 `0x7f` 为中性点的插值）→ 负值钳零 → `mov [eax],cx`。**不含固定 50% 半化算子**。 |
| **独立证据【原记·反证】（本任务自跑，未采信他方）** | ① **B1** 49B @ VA `0x0047F40F`（FileOffset `0x07F40F`）、**B2** 51B @ VA `0x0047F4AE`（`0x07F4AE`）逐条反汇编均为上列形态。<br>② **全 exe `and reg,0x7BEF` = 0 处 / 含 imm`0x7BEF` 的指令 = 0 条**：`.text` 全段（4,063,232 B，覆盖 100.00%）稳健 resync 线性反汇编 **1,394,120** 条指令，其中 `and reg32,imm32` 形态 6,411 条（覆盖性自证）。<br>③ 反证：**我方**桩内确有 50% 等价算子（`and ecx,0x7bef` @ 产物 RVA `0x2145` / `0x21E5`）⇒「50%」是我方桩 `s=256` 的等效观感。<br>原文见 `out/re_work/fog_errata/disasm_b1b2_plus_7bef_scan.txt`、`f3b_fullscan_and7bef.txt`。 |
| **理由【原记·反证】** | 引擎不存在「~~原生 50% 减法~~**【原记】**」这一算子；该说法把我方桩的**等效观感**误挂到引擎原版行为上。 |
| **影响面【原记·反证】（对本文）** | ① **§2.8 / §2.9 的 SAFE 判定不受影响**——该判定着眼「是否写可序列化状态」，与「50% 还是 alpha 插值」之争无关；本条只订正**原版语义描述**。<br>② 但**产品决策级结论**受影响：「关闸不得落回 ~~引擎原生 50%~~ **【原记】**」被**更强满足**（关闸出口既不经过原版 alpha 插值混色、也不经过任何 50% 掩码）⇒ 关闸目标更强成立，验收判据改按「关闸三计数恒 0 + 关闸出口反汇编证据」（该项属 `hook_gate_gap_table.md` §10.2 / G-04）。 |
| **本文全篇排查【原记·反证】** | grep：`50% 减法` = **0**、`50% 半化` = **0**、`减法` = **0**、`原生` = **0**、`7BEF` = **1**（仅 `L167`）。<br>⇒ `L167` 的 `(c>>1)&0x7BEF` 属 **§2.5 雷达像素覆写**（引擎减暗体的等价式，另一处机制），**正确、不在 E1 范围内**。本文**已无 E1 独立残留**（逐行输出见 `out/re_work/fog_errata/f4_grep_selfcheck.txt`）。 |

> **E1 域外残留【原记·反证】（不在本任务写作用域，交 Lead 处置）**：同一 ~~「引擎原生 50% 减半」~~**【原记】**口径仍存活于
> ① 【原记】（勘误前曾存在于源码注释）`ra2render/blitter_hooks.cpp`：~~`:50`「灰雾混色强度：256=原生 50% 减半」、`:1302`「256 = 原生 50% 减半（稳态）」、`:1331`（同句式）~~ —— **【FOG-COMMENT 已订正 · 2026-09-27】** 该 6 行已改为「256 = **我方** 50% 等效观感（引擎原版为 FOG.SHP alpha 插值混色，非固定半化）」，改后源码旧措辞 0 命中、**未重编译**（DLL MD5 仍 `491C25F9…`）；
> ② `docs/RE_COORDINATION.md:1467` 的「③ 混色桩不介入且不落回 ~~引擎原生 50%~~**【原记】**」为**改前口径** —— **Lead 已于同文件 `:1489` 落「★更正（产品决策级）」**（结论与本节 E1 一致：原版 = FOG.SHP alpha 插值混色；全 exe `and reg,0x7BEF` 0 次）⇒ **该文档侧已无待处理项**。
> ⇒ **E1 域外残留（源码注释）已由 `FOG-COMMENT` 订正归零** 〔2026-09-27〕；**剩余项仅** `ra2youli/ra2render.ini:37` 与 `ra2render/ra2render.ini:37` 的注释「不是恢复引擎原生 50%」（**推迟至 ZC-4 会话结束后**再改，以免污染其在跑的真机 A/B 与结尾哈希还原校验）。

> **附注**：本任务禁跑游戏/禁注入，E1 结论为**纯静态反汇编 + 字节计数**证据；关闸侧的真机「三计数恒 0」仍 `[待实测]`。
