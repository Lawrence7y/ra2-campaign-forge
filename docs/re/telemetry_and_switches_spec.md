# 遥测与独立开关规格（Telemetry & Switches Spec）

> **文档属性**：任务 Z-3 产出（只读分析，基于 ra2render 现网代码与台账 [v1.5.5]/[v1.6.0]）
> **对象模块**：`ra2render.dll`（Hook 载体）+ `gamemd.exe` 1.001（被 Hook 目标）
> **分析基线**：`ra2render/blitter_hooks.cpp`（1757 行）、`ra2render/ra2render.h`、`ra2render/dllmain.cpp`、`ra2render/ra2render.ini` 与 `ra2youli/ra2render.ini`、`REVERSE_ENGINEERING_AND_PATCHES.md` §七/[v1.5.5]/[v1.6.0]、`docs/re/dirty_rect_deep_dive.md`
> **闸门依据**：`docs/RE_COORDINATION.md`——每个 Hook 必须有「ini 开关 / 遥测计数器 / 卸载还原路径 / 回滚判据」四要素，缺失项必须标出；联机影响按台账 [v1.5.10] §5 三级分类（**可动** = 纯表现 / **慎改** = 保持确定性契约 / **红线** = 禁改）。

---

## 〇、口径约定（读表前必读）

1. **生效层级**：
   - **进程级**：键值在 `DllMain(DLL_PROCESS_ATTACH) → InstallVTableHooks() → LoadConfig()`（blitter_hooks.cpp L1587；dllmain.cpp L31）一次性读入，运行期**不热重载**；
   - **帧级**：全局变量的**判定**在每次 Hook 调用时读取（每帧/每对象），因此改 ini 需重启进程才能生效，但判定本身是帧级粒度。
2. **「开关」两种形态（本规格严格区分）**：
   - **安装门控**（Install Gate）：ini 键决定补丁字节是否写入；关闭时零开销、零残留；
   - **运行时短路**（Runtime Short-Circuit）：补丁无条件安装，Hook 体开头判 ini 键后提前返回。
   现网 **所有 FogOfWar 键均为运行时短路**（补丁字节恒写入，仅绘制路径判键短路），见缺失项 M-G1。
3. **遥测汇总口径**：`CheckTelemetry()`（L128-152）为 **2 秒窗口打印 + 累计计数**——`GetTickCount` 差 ≥2000ms 时打印一次并重置窗口起点，但**计数器从不清零**，故日志中的"节流率"是**自注入以来的累计值**而非窗口瞬时值（见缺失项 M-10）。
4. **联机确定性分类**（引用 `docs/re/net_sync_checksum.md` §5）：
   - **可动** = §5.3 纯表现（Blit/RLE/dirty-rect/迷雾**显示**/雷达点/FPS/时钟）；
   - **慎改** = §5.2（保持确定性契约，如时间片分片规则、逻辑字段强写）；
   - **红线** = §5.1（RNG、帧 CRC、命令序、枚举序等，本项目现网补丁均未触碰，但 L2 指针哈希见 M-5）。

---

## 一、Hook 总表（已安装 23 项 + 计划 1 项）

> 行号证据均指 `ra2render/blitter_hooks.cpp`（下称 BHK.cpp），另注明者除外。「装/卸」= Install/Remove 代码行号。

### 1.1 L1 渲染 Blit 族（6 枚，虚表劫持）

| # | Hook（原始入口） | 目标地址（虚表槽 +4） | 安装方式 | ini 键（默认/层级） | 遥测计数器（口径） | 卸载还原 | 回滚判据 | 联机 |
|---|---|---|---|---|---|---|---|---|
| 1 | `Hook_BlitTransXlatAlphaZRead`（0x00494B60） | 0x007E56F4（=0x007E56F0+4，ra2render.h L12） | 虚表劫持 `PatchVTablePointer`（装 BHK.cpp L1591-1594 / 卸 L1686-1690） | `EnableSIMD=1`（[Render]，进程级装载/帧级判定，L66-67）；**无 per-hook 开关** | `totalBlitCalls`/`totalBlitPixels` 各 Hook 入口自增（L168-169）；SIMD 快路径/标量尾巴/fallback **无分路计数** | 回写原指针，对称；自处理条件 `warpOffset==0 && aBuf==nullptr && XlatTable`（L171），否则转原版（L205-207） | 调色板错色/爆炸高光异常 → `EnableSIMD=0` 复测；仍异常需整体 DLL 回退（缺单独键，M-1） | 可动（§5.3） |
| 2 | `Hook_BlitTransXlat_G`（0x004912B0） | 0x007E5A24（ra2render.h L18） | 同上（装 L1597-1600 / 卸 L1691-1695） | 同上（共用 `EnableSIMD`） | 同上（L215-216） | 对称；fallback 条件 `pThis->XlatTable` 不满足（L218/251-253） | 单位/建筑阵营色错 → `EnableSIMD=0` | 可动 |
| 3 | `Hook_RLEBlitTransXlat_G`（0x004960A0） | 0x007E55C4（ra2render.h L15） | 同上（装 L1602-1606 / 卸 L1696-1700） | `EnableSIMD` 对本 Hook **无效**（无自处理路径） | 同上（L261-262）；但 `pixels += Length` 中 Length 为 **uint8_t 截断值**（ra2render.h L127 签名缺陷，见 C-3），口径失真 | 对称；**纯遥测转发**（L264-266），无任何加速——台账 v1.5.3 已定性"仅为遥测转发"（"装了但没生效"项） | 不适用（无行为变更）；像素统计异常 → 见 M-3 | 可动 |
| 4 | `Hook_BlitTrans_G`（0x007BC890） | 0x007F7BF8（ra2render.h L21） | 同上（装 L1609-1612 / 卸 L1701-1705） | 同上 | 同上（L274-275） | 对称；fallback 条件 `dst&&src&&length>0`（L277/311-313） | 半透明叠层花屏 → `EnableSIMD=0` | 可动 |
| 5 | `Hook_BlitTransDarken_G`（0x00492670） | 0x007E59F4（ra2render.h L24） | 同上（装 L1615-1618 / 卸 L1706-1710） | 同上 | 同上（L321-322） | 对称；fallback L361-363 | 步兵/载具阴影消失或全黑 → `EnableSIMD=0` | 可动 |
| 6 | `Hook_BlitPlain_G`（0x007BC7F0） | 0x007F7BC8（ra2render.h L27） | 同上（装 L1621-1624 / 卸 L1711-1715） | **不受任何键控制**（memcpy 直通 L374-377，无 SIMD 分支） | 同上（L371-372） | 对称；fallback L379-381 | 地表/纯拷贝层撕裂 → 整体 DLL 回退（缺键，M-1） | 可动 |

### 1.2 L2 寻敌节流（3 枚生效 + 1 枚死代码）

| # | Hook（原始入口） | 目标地址 | 安装方式 | ini 键（默认/层级） | 遥测计数器（口径） | 卸载还原 | 回滚判据 | 联机 |
|---|---|---|---|---|---|---|---|---|
| 7 | `Hook_Techno_SelectAutoTarget`（0x006FB010） | 虚表项 0x007F4D84（ra2render.h L37） | 虚表劫持（装 L1627-1630 / 卸 L1716-1720） | `TargetScanInterval=8`（[Logic]，L62-64，clamp 1..64，ini 注释未记载 clamp） | `throttledTargetScans++`（节流帧，L408）；`totalTargetScans++`（放行执行，L413）。**与 #8/#9 共用计数器，口径混合（M-4）** | 对称 | 单位发呆/不主动还击 → `TargetScanInterval=1`；仍异常 → 需卸载补丁（无独立键，M-4） | 慎改（§5.2 时间片；**分片用指针哈希违反 §6.2，见 M-5**） |
| 8 | `Hook_Unit_SelectAutoTarget`（0x00736CA0） | 虚表项 0x007F6094（ra2render.h L46） | 同上（装 L1633-1636 / 卸 L1721-1725） | 同上 | 同上（L429/434） | 对称 | 同上 | 慎改（同上） |
| 9 | `Hook_Techno_Greatest_Threat`（Inline Hook） | **0x006F8DF0** 函数本体 | 9 字节内联补丁 `E9 rel32 + 90×4`（装 L486-523，跳板 16B=原 9 字节+jmp 0x006F8DF9，L495-501 / 卸 L525-533 还原 9 字节） | 无独立键；间接受 `TargetScanInterval` 控制（interval=1 时 retention 永不命中，Hook 退化为纯转发） | retention 命中计入 `throttledTargetScans`（L467，语义=返回旧目标）；全扫描计入 `totalTargetScans`（L475）。**与 #7/#8 混计且"节流"语义不同（M-4）** | 对称（备份 `s_origGreatestThreatBytes[9]` L448）；半途失败状态不上报（C-7） | 单位丢失锁定/攻击发呆（retention 返回过期目标）→ `TargetScanInterval=1`；联机对局 → **禁用（M-5）** | 慎改→**联机风险**（指针哈希分片，M-5） |
| — | `Hook_Unit_Greatest_Threat`（死代码） | —（ra2render.h L43-44 宏、L198 extern 均未被安装路径引用） | **从未安装**（BHK.cpp L482-484 仅转发定义，v1.5.5 改 inline 后遗留） | — | — | — | — | — |

### 1.3 L3 星际三态迷雾（6 枚 + 数据补丁）

| # | Hook（原始入口） | 目标地址 | 安装方式 | ini 键（默认/层级） | 遥测计数器（口径） | 卸载还原 | 回滚判据 | 联机 |
|---|---|---|---|---|---|---|---|---|
| 10 | `Hook_Unit_Draw`（0x0073CEC0） | 虚表槽 69：0x007F5D84 | 虚表劫持（装 L1639-1642 / 卸 L1726-1730） | `EnableStarCraftFog=1`（[FogOfWar]，运行时短路 L1505） | `unitsCulledByFog`（L1506）/`totalUnitsRendered`（L1509）；`CheckTelemetry` 心跳在 L1504 | 对称 | 雾中敌坦克可见（漏剔）或己方单位隐形（误剔）→ 键置 0 回原版 | 可动（只拦绘制） |
| 11 | `Hook_Infantry_Draw`（0x00518F90） | 0x007EB16C | 同上（装 L1645-1648 / 卸 L1731-1735） | 同上（L1517） | 同上（L1518/1521）；**无 CheckTelemetry 心跳（M-10）** | 对称 | 同上 | 可动 |
| 12 | `Hook_Aircraft_Draw`（0x004144B0） | 0x007E23B8 | 同上（装 L1651-1654 / 卸 L1736-1740） | 同上（L1529） | 同上（L1530/1532）；无心跳 | 对称 | 同上 | 可动 |
| 13 | `Hook_CellClass_Draw`（0x004801F0 原版 Draw_Shroud_And_Fog） | 函数本体 0x004801F0 | 5 字节内联 `E9` → 裸汇编代理（L1068-1084）+ 10 字节跳板（装 L1220-1247 / 卸 L1288-1295） | `EnableStarCraftFog=1`（短路判定在 L1001，**先调原版再判键**）；`FadeFogTransition=1`（渐变强度分支 L1027） | `fogCellsDrawn++` 仅在实际绘制灰雾时（L1062）；关断/全亮路径无计数 | 对称 | 黑雾区黄白高亮/全图变黑（v1.3.0 症状）→ 键置 0；**注意 ScenarioFlags 强写仍在**（M-8） | 可动（§5.3 迷雾显示） |
| 14 | `Hook_FogBlendB1_Stub`（动态强度混色桩） | **0x0047F40F**（49 字节区段，续接 0x0047F440） | `E9 + 44×NOP` 等长补丁（装 L1250-1266 / 卸 L1297-1302，还原 `s_origFogBlendB1Bytes[49]`） | **无任何 ini 键**（无条件安装）；强度由 `s_fogBlendStrength` 运行时驱动（L1052/1061） | **无计数器**（每次灰雾像素混色量不可观测，M-6） | 对称，但守卫 `s_origFogBlendB1Bytes[0]!=0`（L1297）以首字节判定，脆弱（C-13） | 灰雾噪斑/通道溢出（v1.4.0 症状）→ **无键可回滚**，只能整体 DLL 回退（M-6） | 可动 |
| 15 | `Hook_FogBlendB2_Stub` | **0x0047F4AE**（51 字节，续接 0x0047F4E1） | `E9 + 46×NOP`（装 L1256-1272 / 卸 L1304-1309） | 同上（无键） | 同上（无计数） | 对称（同 C-13 守卫） | 同上 | 可动 |
| 16 | 视口全量刷新补丁（v1.5.0 L4，无 Hook 函数） | **0x006D3D99**（原 `jge` → `jmp 0x006D3E37`） | 6 字节等长替换 `E9 99 00 00 00 90`（装 L1276-1281 / 卸 L1311-1316，备份 L1214-1218） | **无 ini 键**（无条件安装；每帧强制全视口重绘） | **无计数器**（全量刷开销不可观测，M-7） | 对称 | 静止视角迷雾退回失效 → 键不存在，只能整体回退；计划由 P-1 规格行接管 | 可动（§5.3 dirty-rect） |
| 17 | 间谍卫星数据补丁 `PatchSpySatBuildingTypes`（非代码 Hook） | BuildingTypeClass+0x16A5（SpySat）、+0x16F0（超武绑定）；SuperWeaponTypeClass+0xB0（CD）、+0xF8（半径）；HouseClass+0x577A；ScenarioFlags&0x1000 | 内存数据写（L564-623；每帧强写 ScenarioFlags L715-718 与 SpySatActive L720-721 由 `UpdateVisionGrid` 承担） | `EnableSpySatRadarSweep=1`（L81-82，门控 L565）；`RadarSweepCooldownFrames=600`（L84-85，clamp ≥60）；`RadarSweepRadiusCells=16`（L87-89，clamp 4..64） | **无运行时计数器**（patchedCount 仅一次性日志 L616-617；扫描施放次数/覆盖格数无统计，M-9） | **无还原路径**（类型数据修改后不恢复；仅跨战局重载时重置 `s_spySatPatched` 重新打补丁，L687） | 裂缝产生器永久失效复发（v1.5.9-C 根因）/超武 CD 不生效 → 键置 0 **并重开局**（懒加载在帧守卫内，已改数据不回滚） | 慎改（玩法语义改动；联机需**全端一致注入** DLL，否则类型数据分叉） |

### 1.4 L5 迷雾正确性补全（v1.6.0 四项）

| # | Hook（原始入口） | 目标地址 | 安装方式 | ini 键（默认/层级） | 遥测计数器（口径） | 卸载还原 | 回滚判据 | 联机 |
|---|---|---|---|---|---|---|---|---|
| 18 | `Hook_Building_Draw`（0x0043D290） | 虚表槽 69：0x007E3FD0 | 虚表劫持（装 L1657-1660 / 卸 L1741-1745） | `EnableBuildingFog=1`（[FogOfWar]，短路 L1541） | `buildingsCulledByFog`（L1542，"从未侦察被剔除"数）；**缺 everSeen 常驻可见命中数（M-11）** | 对称 | 雾中新建敌建筑直接全彩（漏剔）或己方/已侦察建筑隐形（误剔）→ 键置 0 | 可动（只拦绘制） |
| 19 | `Hook_Bullet_Draw`（0x00468090） | 0x007E47F8 | 同上（装 L1663-1666 / 卸 L1746-1750） | `EnableBulletFog=1`（短路 L1552） | `bulletsCulledByFog`（L1553） | 对称 | 直视圈内敌方炮弹消失/闪烁（误剔）→ 键置 0 | 可动（只拦绘制，命中判定不动） |
| 20 | `Hook_RadarPlot_Proxy`（Plot_Cell 0x00655C50 代理） | 调用点 **0x006574C3**（call rel32 等长替换 L1448-1461）+ Plot_Cell 前 5 字节跳板（L1434-1446） | 调用点等长替换 `E8 rel32`（装 L1433-1480 / 卸 L1482-1500：先还原两个调用点再还原 Plot_Cell 序言） | `EnableMinimapFog=1`（汇编侧镜像 `s_minimapFogGate`，L102，代理内判定 L1362-1363）；另有菜单守卫 `[0x00A8B238]==0` 直通（L1359-1361） | `s_minimapFogPixels++`（asm L1404，灰化像素累计；独立 uint32 全局，非 ForgeTelemetry 字段，C-8） | 对称（三份备份 L1335-1337） | 小地图全灰/事件信标（基地遭袭 blip）被灰化 → 键置 0 | 可动（绘制层） |
> 【W3 勘误 · W3-A6/ISSUE-DISAMBIG-RADAR-HOOK】改前：0x006574C3；改后：0x006574C3（RadarClass::Plot_Cell 主循环调用点，见 ra2render.h:158；实际补丁下沉点位于 0x00655D38，见 blitter_hooks.cpp:150, 3016）；依据：ra2render/ra2render.h:158; ra2render/blitter_hooks.cpp:150, 2711, 2920, 3016, 3090；分级：P2
| 21 | `Hook_RadarPending_Proxy`（跳帧判定 0x00660530 代理） | 调用点 **0x0065719A**（call rel32 等长替换 L1463-1476） | 调用点等长替换（装同上 / 卸 L1489-1493） | **无直接键**——行为门为 `s_minimapForceRefresh`（L1421-1424），而该变量由 `FadeFogTransition || EnableMinimapFog` 驱动（L804）→ 与 EnableMinimapFog 语义不完全对齐（M-12） | **无计数器**（强制刷新帧数不可观测，M-12） | 对称 | 视野变化后小地图刷新异常卡顿 → 依赖 M-12 规格补键 | 可动（绘制层） |

> **【勘误 DA4-2 · 2026-09-27】（原文保留，未删字：上表 #20 行照旧）**
> - **分类**：本条属「**误当现网安装点**」——已过期的 v1.6.0 调用点口径。
> - **改前原文（上表 #20 行「目标地址」与「安装方式」列）**：「调用点 **0x006574C3**（call rel32 等长替换 L1448-1461）+ Plot_Cell 前 5 字节跳板（L1434-1446）」／「调用点等长替换 `E8 rel32`（装 L1433-1480 / 卸 L1482-1500：先还原两个调用点再还原 Plot_Cell 序言）」。
> - **订正后（现网路线 A 口径）**：**目标地址 = `0x00655D38`（9 字节：`E9 rel32` + 4×`90`）**——偷取 9 字节（原指令 `89 44 24 28` 4B + `A1 50 35 B7 00` 5B），跳板还原 9 字节后 `jmp 0x00655D41`；**「Plot_Cell 前 5 字节序言跳板」已整体取消**。`0x0065719A`（5 字节 `call` 等长替换）地址结论**不变**。备份变量同步变更为 `s_origPlotCellBytes[9]` / `s_plotCellTrampoline[16]` / `s_origRadarPendingCallBytes[5]`。
> - **同源影响**：本行其余四要素——ini 键 `EnableMinimapFog`（默认 1，与 ini 默认 0 不一致见 `hook_gate_gap_table.md` #20）、计数器 `s_minimapFogPixels`、对称卸载、回滚判据——**结论全部不变**；「安装方式/卸」列内的 **L14xx 行号属 1,757 行构建快照**，路线 A 落地后已漂移，**以符号搜定位为准**（`InstallRadarFogHooks` / `RemoveRadarFogHooks`）。
> - **真机证据**：`ra2youli/ra2render.log:1099`（同文共 15 处）——「成功挂载路线 A 下沉挂钩 (Plot_Cell 0x00655D38 9 字节补丁 + 强制刷新 0x0065719A)」。
> - **字节依据**（`out/re_work/da4/claims.txt`，`audit_bytes.py` 12/12 全 OK）：`0x00655D38 = 89 44 24 28 A1 50 35 B7 00`、`0x00655D41 = 3B C5 74 18`、`0x0065719A = E8 91 93 00 00`、`0x006574C3 = E8 88 E7 FF FF`（原版调用点原文，已非安装点）。

### 1.5 系统环境（DllMain 级）

| # | 项 | 目标 | 安装方式 | ini 键（默认/层级） | 遥测计数器 | 卸载还原 | 回滚判据 | 联机 |
|---|---|---|---|---|---|---|---|---|
| 22 | `EnableLowFragmentationHeap` | 进程全部堆（`GetProcessHeaps` + `HeapSetInformation`，L113-126；dllmain.cpp L32） | API 调用 | `EnableLFH=1`（[System]，L72-73） | **无计数器**（仅一次性日志"激活 N/M 个堆" L125，M-13） | **无还原路径**——Windows 语义 LFH 开启后不可按堆关闭；规格必须标注「不可还原，回滚=置 0 后重启进程」（M-13） | 分配器相关崩溃/与第三方工具堆检测冲突 → `EnableLFH=0` 重启 | 可动（§5.3 系统层） |
| 23 | `timeBeginPeriod(1)` | 系统时钟中断周期 | API 调用（dllmain.cpp L33-36 装载 / **L41-43 `timeEndPeriod(1)` 对称还原**） | `HighPrecisionTimer=1`（L75-76） | **无计数器**（仅一次性日志 L35） | 对称，但 detach 门控读运行期 `g_highPrecisionTimer` 当前值——若未来支持热重载将 Begin/End 不对称（M-14：建议 attach 快照 `s_timerAcquired`） | 帧节拍异常/与 cnc-ddraw 等外部组件时钟冲突 → 键置 0 重启 | 可动（§5.3，与 CurrentFrame 解耦） |

### 1.6 计划项预留（P-1：L4 折中，dirty_rect_deep_dive.md §5 已给实现稿）

| # | Hook / 补丁 | 目标地址 | 安装方式 | ini 键（建议） | 遥测计数器（建议） | 卸载还原 | 回滚判据 | 联机 |
|---|---|---|---|---|---|---|---|---|
| P-1 | `SetTacticalRedrawMode(bool)` 动态补丁 + `RegisterCellAsVisible`（0x006DA7D0）局部打脏 | **0x006D3D99**（复用现有 6 字节补丁点：vanilla=`0F 8D 98 00 00 00` / force=`E9 99 00 00 00 90`，备份已存在 L1214-1218）；打脏调用 `TacticalClass::Instance(0x00887324)`→0x006DA7D0 | 同一 6 字节补丁点**动态切换**（dirty_rect_deep_dive.md §5.1 实现稿），替代现行 #16 的无条件 jmp；`UpdateVisionGrid` 内双向收集翻转格并 **3×3 外扩**调 0x006DA7D0（仅已探索格，`CellFlags&0x08`） | **`L4DirtyMode=auto`**（[FogOfWar]；`auto`=局部打脏 / `force-full`=现 v1.5.0 行为 / `vanilla`=原版 jge，供排查）；**`L4LocalFlipThreshold=350`**（单帧翻转格超阈值退化全屏，保护 VisibleCells[800]） | **`l4FlippedCells`**（每帧视野翻转格数，埋点 UpdateVisionGrid 翻转收集处，即现 L804-821 prevVisionGrid 比对扩展）；**`l4LocalDirtyCalls`**（0x006DA7D0 成功登记数）；**`l4FullscreenFallbackFrames`**（>350 退化全屏的帧数，阈值告警口径：占比 >5% 需调阈值）；建议并入 ForgeTelemetry（uint64） | 复用现有 `s_origTacticalRedrawBytes[6]`（L1214）与 `RemoveCellClassDrawHook` 内还原（L1311-1316），**无需新增卸载路径**；切换函数本身须 VirtualProtect 恢复原保护属性（参照 L1277-1279 模式） | ① 静止视角迷雾退回 >1 逻辑帧（对拍 v1.5.0 基线，dirty_rect_deep_dive.md §6.2 测试 1）→ `auto`→`force-full`；② VisibleCells 越界/崩溃或 `l4FullscreenFallbackFrames` 占比 >5% → 调 `L4LocalFlipThreshold` 或 `force-full`；③ 残影像素残留（Pass1 未覆盖旧单位投影）→ `vanilla` | 可动（§5.3：只影响重绘范围；`cell+0x5C` 去重仅**只读** CurrentFrame） |

> 附注（非本规格核心，仅登记指针）：`ParticleClass::Draw 0x007EFA68` / `ParticleSystemClass::Draw 0x007EFCB0` 槽 69 迷雾剔除为 v1.6.0 §4 遗留待办（Owner 偏移未实证故未安装）；RLE P0 补全、路径缓存 0x004D3E4B、音频限流 0x750920/0x7509E0、CRT 池化等计划项落地时，须各自补齐本规格同款四要素行。

---

## 二、ForgeTelemetry 字段与日志格式核对

### 2.1 计数器清单（结构 L160-171 + 汇编侧独立变量）

| 计数器 | 类型 | 自增位置（行号） | 口径说明 |
|---|---|---|---|
| `totalBlitCalls` | uint64 | L168/215/261/274/321/371（六枚 Blit Hook 入口，混计） | 不分 Hook、不分路径（M-2） |
| `totalBlitPixels` | uint64 | 同上（`+= length`/`+= Length`） | #3 处 Length 为 uint8_t 截断值（C-3）；打印时 ÷(1024×1024) 标注 "Mpx"（实为 MiB-px，C-8） |
| `totalTargetScans` | uint64 | L413/434（两个 SelectAutoTarget 放行）、L475（GT 全扫描） | 三路径混计（M-4） |
| `throttledTargetScans` | uint64 | L408/429（SAT 节流跳过）、L467（GT retention 返回旧目标） | 混计且语义不同：一个"什么都不做"，一个"返回旧目标"（M-4） |
| `unitsCulledByFog` | uint64 | L1506/1518/1530（Unit/Infantry/Aircraft 剔除） | g_enableStarCraftFog 关断时为 0（口径正确） |
| `totalUnitsRendered` | uint64 | L1509/1521/1533 | 仅机动单位三枚 Draw；建筑/弹道无对应"渲染数"（不对称但可接受） |
| `fogCellsDrawn` | uint64 | L1062（Hook_CellClass_Draw 实际绘制灰雾时） | 开关关断/直视全亮/单帧防重 Token 命中路径均不计（L1040-1048） |
| `buildingsCulledByFog` | uint64 | L1542 | — |
| `bulletsCulledByFog` | uint64 | L1553 | — |
| `minimapFogPixels` | —（结构外） | asm L1404 → `s_minimapFogPixels`（uint32，L50） | **不在 ForgeTelemetry 结构内**；uint32 长局理论回绕（C-8） |

### 2.2 日志格式串核对结论

- **2 秒遥测**（L139-150）：11 个格式符 vs 11 个实参（`%llu`×9 + `%.1f`×1 + `%u`×1），逐参数类型核对**匹配**；`s_minimapFogPixels`（uint32）用 `%u` 正确。
- **卸载总结**（L1752-1756）：10 格式符 vs 10 实参**匹配**；但 `totalBlitPixels` 在此处打印**原始字节数**（不 ÷1MB），与 2 秒遥测的 "Mpx" 口径不一致（C-8）。
- `RemoveVTableHooks` 逐项还原日志（L1687-1749 共 13 条 `PatchVTablePointer` 日志）无格式问题。
- `LoadConfig` 回显日志（L104-110）12 项与实参**匹配**。
- **心跳挂点**：`CheckTelemetry` 仅在 3 处被调用——L400（Techno SelectAutoTarget）、L421（Unit SelectAutoTarget）、L1504（Unit Draw）；Infantry/Aircraft/Building/Bullet/CellClass/GT Hook **均不调用** → 若三个心跳路径不活跃（如菜单内、纯建筑对局），遥测完全静默（M-10）。

---

## 三、缺失项清单（18 条，逐条给补齐规格）

> 编号规则：M-x；「规格」= 建议的键名 / 计数器名 / 埋点位置 / 回滚判据。优先级：P0 = 落地 L4 折中或联机前必须；P1 = 下一轮补丁随行；P2 = 择机。

**M-1（P1）L1 六枚 Blit Hook 无独立开关**
- 缺：除 `EnableSIMD`（控制 SIMD 向量化路径，L178/224/282/330）外，无法单独禁用某一枚 Blit Hook，也无整体关闭 Blit Hook 的总闸（#6 甚至完全不受键控）。
- 规格：`[Render] EnableBlitHooks=1`（总闸，**安装门控**——置 0 时 `InstallVTableHooks` 跳过 #1-#6 安装，埋点 L1590-1624 六处调用前）；排查期可选 `EnableBlitHook_<Name>=1`（AlphaZRead/Xlat/RLE/Trans/Darken/Plain）。
- 计数器：`blitFallbackCalls`（各 Hook 走原版 fallback 分支的次数，埋点 L205/251/264/311/361/379）——该值持续偏高说明自处理条件失配。
- 回滚判据：任一类精灵渲染异常且 `EnableSIMD=0` 不能消除 → 关 `EnableBlitHooks` 验证归因。

**M-2（P1）L1 无分路径遥测**
- 缺：`totalBlitCalls/totalBlitPixels` 六路混计；SIMD 快路径、标量尾巴、原版 fallback 三条路径不可区分；"16px 全透明块跳过"收益（台账 §2.3 的 300% 结论）无现网数据支撑。
- 规格：`blitCallsByHook[6]`、`blitSimdFastPathBlocks`（mask==0xFFFF continue 处，L184/230/288/338）、`blitScalarTailPixels`、`blitFallbackCalls`；2 秒日志按 Hook 拆行或加 CSV 行（遥测文件分离见 M-16）。

**M-3（P0）RLE Hook 纯转发 + 像素口径失真**
- 缺：`Hook_RLEBlitTransXlat_G`（L256-267）无任何加速逻辑（台账 v1.5.3 定性"仅为遥测转发"），属「装了但没生效」；且 `totalBlitPixels += Length` 的 Length 受 ra2render.h L127/L150 `uint8_t` 签名截断（v1.5.3/v1.5.7 勘误"补全前必改"至今未改，C-3）。
- 规格：修复签名（`uint8_t Length` → `int Length`，`EncodedLen` → `skipLeft`）前，该 Hook 的像素增量**不得计入**主口径（单列 `rleForwardCalls`）；补全向量化实现时按台账 v1.5.7 §2-A 规格落 P0 两枚（0x007E55A4/0x007E55C4）并各自给四要素行。
- 回滚判据：步兵阴影/本体渲染异常 → 新 Hook 键置 0（安装门控）。

**M-4（P0）L2 节流率口径混合三路径且语义不同**
- 缺：`totalTargetScans/throttledTargetScans` 同时被 #7（L408/413）、#8（L429/434）、#9（L467/475）自增。Greatest_Threat 的"节流"= **retention 返回旧目标**（输出有值），SelectAutoTarget 的"节流"= **直接跳过**（无输出）——混计后 2 秒日志的"节流率 %.1f%%"（L138）无法回答"Greatest_Threat 路径占比多少"这一关键问题（台账 v1.5.3 的现网审计缺口）。
- 规格：拆分 `satThrottled`/`satExecuted`（L408/413、L429/434）与 `gtRetentionHits`/`gtFullScans`（L467/475）；节流率分列打印；`TargetScanInterval` 对 #9 增加**独立键** `GreatestThreatThrottle=1`（置 0 时 GT Hook 强制走 `totalTargetScans` 直通路径，埋点 L465 判定前）。
- 回滚判据：单位发呆/丢失锁定（retention 返回过期目标）→ `GreatestThreatThrottle=0`；联机对局 → 一律 0（见 M-5）。

**M-5（P0）L2 节流分片使用指针哈希——联机确定性风险**
- 缺：分片判据 `unitHash = (uintptr_t)pThis >> 4`（L404/425/463）+ `(unitHash + currentFrame) % Interval`。台账 [v1.5.10] §6.2 明文「重建时机必须是 CurrentFrame 的纯函数……禁止指针哈希参与」；联机各端堆地址不一致 → 同一单位在不同端于不同帧被扫描 → 目标选择分叉 → OOS 风险。单机无碍。
- 规格：分片键改为对象**逻辑序号**（如 `HouseClass`/`TechnoClass` ArrayIndex +0x30，或 `ID` AbstractClass 基类字段）+ CurrentFrame，保证各端一致；过渡期提供 `[Logic] OnlineSafeMode=0`（置 1 时 interval 强制 1，即关闭节流）并在联机检测（`0x00A8D5F8` 会话位，net_sync §7-10）下告警日志。
- 回滚判据：联机 desync（SYNC*.TXT 生成）且堆栈指向 GT/SelectAutoTarget → `OnlineSafeMode=1` 或 `TargetScanInterval=1`。

**M-6（P1）灰雾混色桩 B1/B2 无开关、无遥测、回滚路径缺失**
- 缺：#14/#15 无条件安装（L1250-1272），无任何 ini 键；灰雾像素混色次数/强度分布无计数；一旦桩有 bug（v1.4.0 噪斑类症状复发），无键可回滚，只能整体 DLL 回退。
- 规格：`[FogOfWar] EnableFogBlendStubs=1`（安装门控，置 0 时不装 B1/B2 且**必须**同时恢复 v1.4.0 的 0-JMP 静态 50% 减半补丁或原版字节——规格上二选一并写死：建议回**原版字节**，让 L3 完全依赖 #13 关断）；计数器 `fogBlendPixels`（B1/B2 桩内 `mov [eax],cx` 前自增或由 #13 统计）。
- 回滚判据：灰雾区噪斑/偏色 → `EnableFogBlendStubs=0`；渐变闪烁 → `FadeFogTransition=0`（注意：该键只关渐变强度，**不卸载桩**，见 C-12）。

**M-7（P0，随 P-1 落地自动解决）现行 L4 补丁（#16）无开关、无遥测**
- 缺：0x006D3D99 强制全量刷无条件安装（L1276-1281），每帧全视口重绘的开销与收益均不可观测。
- 规格：由 P-1 规格行的 `L4DirtyMode` + `l4FlippedCells/l4LocalDirtyCalls/l4FullscreenFallbackFrames` 接管；P-1 落地前，临时补一个 2 秒口径观测即可（`l4ForcedRedrawFrames` 在帧级无法埋点——0x6D3D99 是纯字节补丁，故 P-1 前该项**接受不可观测**并在台账标注）。

**M-8（P1）UpdateVisionGrid 每帧强写逻辑字段——无开关、无遥测、无还原**
- 缺：`ScenarioFlags &= ~0x1000`（L715-718）与 `HouseClass+0x577A = 0`（L720-721）每逻辑帧强写，属**写逻辑状态**（区别于纯表现剔除），是 `EnableStarCraftFog` 的隐式副作用但未在规格中单列；`s_visionToken` 回绕清零（L694-701）与跨战局重载重置（L682-689）均无遥测。
- 规格：文档化为 EnableStarCraftFog 的从属行为（本规格 §1.3 #17 已列）；计数器 `visionTokenWrapCount`（L694）、`scenarioReloads`（L682，同时记录重置项掩码）。
- 回滚判据：读档后侦察记忆丢失/开局黑雾异常 → 检查 L682 阈值（currentFrame+100）与重置项。

**M-9（P1）间谍卫星/雷达扫描无运行时遥测、数据补丁无还原**
- 缺：#17 修改类型数据（SpySat/CD/半径/超武绑定）后无还原路径；扫描超武施放次数、覆盖格数、与裂缝产生器（Gap）交互无任何计数；clamp 下限（CD≥60、半径 4..64）未写入 ini 注释。
- 规格：计数器 `spySatPatchedTypes`（L615 patchedCount 存量）、`radarSweepCasts`（埋点需新 Hook PsychicReveal 施放路径 0x6CD70C——P2）；ini 注释补 clamp；还原路径=打补丁前备份 `0x16A5/0x16F0/0xB0/0xF8` 原值数组，`Remove` 阶段恢复（当前 DLL 卸载即进程退出，风险可控但四要素缺一）。
- 回滚判据：裂缝产生器永久失效复发 → `EnableSpySatRadarSweep=0` + 重开局。

**M-10（P1）遥测心跳挂点不均 + 累计口径未标注**
- 缺：`CheckTelemetry` 仅 3 处调用（L400/L421/L1504），Infantry/Aircraft/Building/Bullet/CellClass/GT 均无；心跳路径不活跃时遥测静默；计数器累计不清零，"节流率"是累计值（易误读为窗口值）。
- 规格：心跳移至 `UpdateVisionGrid()`（每逻辑帧必经，L673 入口处）或独立 2s 线程；2 秒日志增加**窗口增量**列（`lastTotal - prevTotal`）与累计列并存。
- 回滚判据：遥测本身异常刷屏/性能损耗 → `[System] TelemetryEnabled=0`（新键，见 M-16）。

**M-11（P2）EnableBuildingFog 缺 everSeen 命中计数**
- 缺：`buildingsCulledByFog` 只统计"从未侦察被剔除"；"直视可见"与"everSeen 常驻可见"不可区分——WC3 式常驻（L936-938）的现网命中率无数据，验收 [v1.6.1] 时无法量化。
- 规格：`buildingsEverSeenShown`（埋点 `ShouldDrawBuilding` L936 命中分支）；2 秒日志追加。
- 回滚判据：已侦察建筑在侦察方视野外被误隐 → 键置 0。

**M-12（P1）EnableMinimapFog 与 Hook_RadarPending_Proxy 的开关耦合失配**
- 缺：#21 无直接键判定，行为门 `s_minimapForceRefresh` 由 `(g_fadeFogTransition || g_enableMinimapFog)` 驱动（L804）——`EnableMinimapFog=0` 且 `FadeFogTransition=1` 时强制刷新仍生效（无害但语义失配）；强制刷新帧数无计数。
- 规格：代理入口补 `cmp byte ptr [s_minimapFogGate],0 / je orig_logic`（asm L1420 前插）；计数器 `minimapForceRefreshFrames`（asm 置 al=0 分支自增）。
- 回滚判据：小地图刷新风暴（CPU 尖峰）→ `FadeFogTransition=0` 且 `EnableMinimapFog=0`。

**M-13（P1）LFH 无还原路径、无遥测（规格化「不可还原」）**
- 缺：#22 LFH 开启后 Windows 不允许按堆关闭 → 卸载还原路径**不可能存在**，但规格未标注；激活数仅一次性日志。
- 规格：文档标注「还原=N/A（OS 语义），回滚=EnableLFH=0 + 重启进程」；静态字段 `lfhHeapsEnabled/lfhHeapsTotal`（L119-124 存量，注入后写入遥测首行）。
- 回滚判据：堆分配相关崩溃且 `EnableLFH=0` 后消失 → 保持 0。

**M-14（P2）HighPrecisionTimer 还原的快照化**
- 缺：detach 时 `if (g_highPrecisionTimer) timeEndPeriod(1)`（dllmain.cpp L41-43）读的是**当前**全局值——现网 LoadConfig 只跑一次故安全，但若未来加热重载即产生 Begin/End 不对称。
- 规格：attach 成功 `timeBeginPeriod` 后置静态 `s_timerAcquired=true`，detach 按快照还原；计数器 N/A（一次性行为）。
- 回滚判据：与外部工具（如 cnc-ddraw 垂直同步策略、录制软件）时钟冲突 → 键置 0 重启。

**M-15（P2）ra2render.log 无开关/级别控制（日志本身是热路径开销）**
- 缺：`LogMessage` 每条 `fopen`-懒初始化 + `fprintf + fflush`（dllmain.cpp L6-23）；`ShouldDrawMobileObject` 前 10 条剔除日志（L883-888）在 Draw 热路径写文件；无级别过滤、无文件轮转。
- 规格：`[System] LogToFile=1`、`LogLevel=info`（error/warn/info/verbose）；剔除类日志降为 verbose；遥测迁独立文件 `ra2render_telemetry.log`（CSV 行，供 Z-1 harness 消费）。
- 回滚判据：N/A（开发设施）。

**M-16（P1）遥测结构化收口（供 Q1 harness）**
- 缺：`s_minimapFogPixels` 游离于 `ForgeTelemetry` 之外（L50）；无 CSV/结构化导出接口（Z-1 基准 harness 需要机器可读格式）；计数器为 uint64 但日志文案口径（Mpx/字节）两套（C-8）。
- 规格：`s_minimapFogPixels` 升 uint64 并入 `ForgeTelemetry`（追加字段属**追加**，不破坏现有日志）；新增 `TelemetryExportTelemetry()` 每窗口打印单行 CSV：`tick,blitCalls,blitPixels,satThrottled,satExecuted,gtRetention,gtFull,culledUnits,fogCells,renderedUnits,culledBld,culledBullet,minimapPx`。

**M-17（P2）EnableStarCraftFog 关断时 #13 的残开销不可观测**
- 缺：`EnableStarCraftFog=0` 时 Hook_CellClass_Draw 仍先调原版再判键（L997-1003），每格一次调用开销与关断事实无数据。
- 规格：`fogGateSkippedCells`（埋点 L1001 短路分支）；验收口径：关断后 fogGateSkippedCells>0 且 fogCellsDrawn==0。

**M-18（P1）「装了但没生效」自证机制缺失**
- 缺：`InstallVTableHooks` 忽略三个子安装函数的 bool 返回值（L1669/1672/1675）且恒 `return true`（L1678）、无条件打"全部挂载成功"（L1677）——无法从日志区分 13 枚虚表 + 4 处补丁哪些实际生效（Q3 审计的硬需求）。
- 规格：安装结果位图 `g_hookInstallMask`（uint32，每 Hook 一 bit，PatchVTablePointer/三个子 Install 成功置位）；结尾日志打印掩码十六进制；`InstallVTableHooks` 返回 `(mask & EXPECTED_MASK) == EXPECTED_MASK`；DllMain 对 false 打 ERROR 级日志（不阻断加载——部分 Hook 失败仍可运行）。
- 回滚判据：掩码缺位对应功能回滚到键置 0 状态。

---

## 四、不一致点清单（13 条，逐条给证据）

| # | 不一致点 | 证据 | 影响 | 建议 |
|---|---|---|---|---|
| C-1 | **双份 ini 内容一致但行尾不一致**：`ra2render/ra2render.ini` 为 LF，`ra2youli/ra2render.ini` 为 CRLF；去 CR 后 diff 为空 | `diff` 逐行报差异（1,43c1,43），`tr -d '\r'` 后完全一致；`od -c` 首行 `[Render]\n` vs `[Render]\r\n` | 低（Windows API 解析两者均可）；但跨工具 diff/合并会全文件冲突 | 统一为 CRLF；v1.6.0 所称"双份同步"建议改为脚本化拷贝 〔**DA2 勘误 · 2026-09-27：本条已被事实推翻**（两副本 MD5 全同），详见本节表后勘误块 **X-1**〕 |
| C-2 | **台账 §2.2/§七 与代码的 L1 虚表地址整组不符**：台账 §2.2（L56-61）与 §七（L211-216）记 0x007F1BE4/0x007F10C4/0x007F1D04/0x007F1044/0x007F1504/0x007F0FC4；代码实际安装 0x007E56F4/0x007E5A24/0x007E55C4/0x007F7BF8/0x007E59F4/0x007F7BC8 | ra2render.h L12-28；BHK.cpp L1592/1598/1604/1610/1616/1622；**台账内部也自相矛盾**——v1.5.7 行（L540-544）的 0x007E55C4 等与 ra2render.h 一致 | 文档失真：按台账地址审计会全部"找不到补丁" | 以 ra2render.h 为准修订台账 §2.2/§七 L1 六行（原始入口 0x00494B60 等两者一致，仅虚表槽址错） |
| C-3 | **RLE 签名勘误未回改代码**：台账 v1.5.3（L371-372）/v1.5.7（L547）明言 `uint8_t Length` 错误（汇编全程 32 位 int）、"补全前必改"；ra2render.h L127（`RLEBlitterCore::Blit`）与 L150（`FnRLEBlitTransXlat`）仍为 `uint8_t Length` | 两处头文件行号；BHK.cpp L257 同签名 | 潜在截断（现网步兵帧宽 ≤255 未爆）；遥测像素口径失真（M-3） | 随 RLE P0 补同一并修 |
| C-4 | **死配置/死代码成簇**（v1.5.5 改 inline 后遗留）：`ADDR_VTABLE_ENTRY_TECHNO_GREATEST_THREAT`（ra2render.h L34）、`ADDR_VTABLE_ENTRY_UNIT_GREATEST_THREAT`/`ADDR_ORIG_UNIT_GREATEST_THREAT`（L43-44）、`ADDR_RADAR_PENDING_ORIG`（L75）、`ADDR_ORIG_TECHNO_AUTO_TARGET`/`ADDR_ORIG_UNIT_AUTO_TARGET`（L38/47）宏未使用；`extern g_pOrigUnitGreatestThreat`（L198）在 BHK.cpp L28 有定义但从未读写；`Hook_Unit_Greatest_Threat`（BHK.cpp L482-484）定义从未安装 | grep 全文件仅上述定义处命中 | 审计干扰：Q3 脚本会误判"存在 Unit GT Hook" | 删除或标注 `// legacy, superseded by inline hook v1.5.5` |
| C-5 | **UnlockGameSpeed 死键**：ini 注释仍长篇描述其"保护作用"（ini L11-14），代码读取（BHK.cpp L69-70）后唯一消费者 `EnforceGameSpeedUnlock()` 是**空函数**（L154-157） | 两处行号 | 用户/测试误以为该键有行为 | 键标注 deprecated 保留兼容，或删除键并更新注释 |
| C-6 | **安装失败被吞 + 恒成功日志**：`InstallCellClassDrawHook`/`InstallGreatestThreatHook`/`InstallRadarFogHooks` 的 bool 返回值被忽略（L1669/1672/1675）；`InstallVTableHooks` 恒 `return true`（L1678）且无条件打"全部核心虚表……挂载成功"（L1677）；同样 `PatchVTablePointer` 失败仅打日志不中止（L1566-1574） | 行号如列 | 部分失败时日志与事实矛盾；Q1/Q3 审计盲区（对应 M-18） | 落地 M-18 安装位图 |
| C-7 | **Greatest_Threat 安装半途失败的状态不一致**：L501 先赋 `g_pOrigTechnoGreatestThreat = trampoline`，L503-506 `VirtualProtect(0x6F8DF0)` 失败才 return false——此时全局指针非空但入口未补丁（hook 未生效）；`RemoveGreatestThreatHook` 守卫（L526）会"还原"相同字节（无害但语义混乱） | L495-523/L525-533 | 低（失败即无 hook）；属 C-6 的具体案例 | 赋值移到补丁写入成功之后 |
| C-8 | **同字段双口径**：`totalBlitPixels` 在 2 秒遥测 ÷(1024×1024) 后标注 "Mpx"（L139-141，1024² 是 MiB-px 而非 10⁶ 的 Mpx）；卸载日志打原始字节（L1752-1753）；`s_minimapFogPixels` 为结构外 uint32（L50，理论回绕） | 行号如列 | 跨文档/跨 harness 数据对不上 | 统一"原始像素数"为唯一口径，显示层再换算；升 uint64 入结构（M-16） |
| C-9 | **遥测为累计口径但文案似窗口口径**：`CheckTelemetry` 只重置 `s_lastTelemetryTick`（L136），不清零计数器；"节流率 %.1f%%"（L138-139）是自注入起累计值 | L128-151 | 长局中窗口突变（如突然大量交火）被累计值稀释，回滚判据失真 | 增加 Δ 窗口列（M-10） |
| C-10 | **ForgeTelemetry 与日志格式串：核对通过（正面结论）**：2 秒遥测 11 对、卸载日志 10 对、配置回显 12 对，格式符个数/顺序/宽度均匹配（逐参数核对 L139-150、L1752-1756、L104-110） | 行号如列 | 无 | 保持"新增计数器必须同步两处日志"的纪律 |
| C-11 | **Hook_RadarPending_Proxy 无直接开关**：与 `EnableMinimapFog` 的对应关系经由 `s_minimapForceRefresh ← (fade||minimap)`（L804）间接成立；`EnableMinimapFog=0` 且 `FadeFogTransition=1` 时该 Hook 仍会强制小地图刷新 | L804/L1419-1431 | 低（多余刷新）；语义审计会判"开关不完整" | M-12 补 asm 门 |
| C-12 | **「安装门控」与「运行时短路」混用未声明**：全部 FogOfWar 键（StarCraftFog/SpySat/BuildingFog/BulletFog/FadeFogTransition/MinimapFog）均为运行时短路——`EnableStarCraftFog=0` 时 0x004801F0/0x0047F40F/0x0047F4AE/0x006D3D99 四处补丁**仍全部在场**（L1001 短路仅覆盖灰雾绘制层）；`FadeFogTransition=0` 不卸载混色桩，s=256 稳态与 v1.4.0 静态补丁逐位等价（设计如此，台账 [v1.6.0] L774 称"卸载仍还原原始字节"指的是 DLL 卸载而非键关断） | L1249-1281（无条件安装）/L1001、L1027（键短路）/L1061（s 复位 256） | 回滚语义与直觉不符："关开关"≠"还原补丁"，残留补丁在异常时仍是怀疑对象 | ini 注释与台账补一句「FogOfWar 键均为绘制层短路，字节级回滚需 DLL 回退」 |
| C-13 | **卸载守卫以"首字节非零"代替显式标志**：`s_origFogBlendB1Bytes[0]!=0`（L1297）/`s_origFogBlendB2Bytes[0]!=0`（L1304）/`s_origRadarPlotCallBytes[0]!=0`（L1484）/`s_origRadarPendingCallBytes[0]!=0`（L1489）/`s_origRadarPlotPrologue[0]!=0`（L1494）/`s_origTacticalRedrawBytes[0]!=0`（L1311）——若原版首字节恰为 0x00 则跳过还原（现网六处原版首字节均非零：B1/B2 为 lea/mov 族、call 为 0xE8、prologue 为 0xA1、jge 为 0x0F，实际风险低） | 行号如列 | 低；但属隐性不对称模式 | 改为独立 `bool s_xxxInstalled` 标志（顺手在落 P-1 时统一） |
> **【勘误 X-1 · DA2 · 2026-09-27】C-1「双份 ini 内容一致但行尾不一致」不成立（原文保留，见上表 C-1 行原地加注）**
> - **原表述（C-1）**：`ra2render/ra2render.ini` 为 **LF**、`ra2youli/ra2render.ini` 为 **CRLF**；去 CR 后 diff 为空 ⇒ 「跨工具 diff/合并会全文件冲突」。
> - **更正表述 / 现状实测**：两份 ini **完全相同** —— `D:\Project\ra2-campaign-forge` 路径下实测（`Get-FileHash -Algorithm MD5`）：`ra2render\ra2render.ini` = `ra2youli\ra2render.ini` = **`0B239E604546CBEF77F70DB31E86C048`**，两者均 **2,996 B / 51 行**，mtime `2026-09-27 09:06:39` 与 `09:06:44`。⇒ **行尾差异不存在**，「全文件冲突」风险随之为零。（历史快照口径：09-26 旧副本为 2,747 B / 49 行 / MD5 `190709D025C133757142062F996E0ED6`；两副本当时亦为**同 MD5**，与 C-1 的行尾差异描述不符。）
> - **影响面**：§四 C-1 一行；本条「影响=低」故无产品决策影响，但会把后续审计引向**不存在的差异**。另：C-1 的副产物表述「v1.6.0 所称『双份同步』建议改为脚本化拷贝」仍然成立且更必要（现状依赖人工/构建脚本各拷贝一次）。

**卸载还原对称性逐对核对总表**（Install ↔ Remove）：

| 补丁点 | Install | Remove | 对称性 |
|---|---|---|---|
| 6 枚 L1 虚表 | L1591-1624 | L1686-1715（回写原指针） | ✅ 对称 |
| 2 枚 SelectAutoTarget 虚表 | L1627-1636 | L1716-1725 | ✅ 对称 |
| 5 枚 Draw 虚表（Unit/Infantry/Aircraft/Building/Bullet） | L1639-1666 | L1726-1750 | ✅ 对称 |
| Greatest_Threat 9 字节 inline | L486-523 | L525-533 | ✅ 对称（半途失败状态见 C-7） |
| CellClass::Draw 5 字节 inline + 跳板 | L1220-1247 | L1288-1295 | ✅ 对称 |
| 混色桩 B1/B2（49/51 字节） | L1250-1272 | L1297-1309 | ✅ 对称（守卫模式见 C-13） |
| L4 0x006D3D99 6 字节 | L1276-1281 | L1311-1316 | ✅ 对称 |
| 雷达调用点 ×2 + Plot_Cell 序言 | L1433-1480 | L1482-1500 | ✅ 对称 |
| **SpySat/超武/ScenarioFlags/House+0x577A 数据写** | L564-623、L715-721 | **无** | ❌ 不对称（M-9/M-8） |
| **LFH** | L113-126（dllmain L32） | **无（不可还原）** | ❌ 规格化（M-13） |
| **timeBeginPeriod** | dllmain L33-36 | dllmain L41-43 | ✅ 对称（快照化建议 M-14） |

---

## 五、建议的 ini 全量模板

> 【现网】= 双份 ini 已有键（值与注释与现网一致，仅补 clamp/语义注记）；【建议】= 本规格 M-x 提出的新键，落地前**不生效**；【计划】= P-1 落地时新增。生效层级除注明外均为「进程级装载 + 帧级判定」。

```ini
[Render]
; 【现网】启用 SSE2 向量化软件 Blit 批处理加速（跳过透明块，大幅提升复杂场面渲染吞吐量）
; 注：该键仅控制 SIMD 路径；六个 Blit Hook 本体始终安装（运行时短路形态）
EnableSIMD=1
; 【建议 M-1】Blit Hook 总闸（安装门控）：置 0 时六个虚表劫持全部跳过，像素路径 100% 原版
;EnableBlitHooks=1

[Logic]
; 【现网】TargetScanInterval: 分散敌对目标全图扫描频率（帧数），默认 8（约 0.25 秒轮询一次）
; 800 单位重载对局下，将 O(N^2) 扫描开销降低 87.5%，消除逻辑慢动作（Tick 延缓）
; 注：代码 clamp 到 [1,64]；分片键现为"对象地址哈希+帧号"（联机分片不同步风险，M-5）
TargetScanInterval=8
; 【建议 M-4】Greatest_Threat 路径节流独立开关：置 0 时 0x006F8DF0 路径每帧全扫描（保留 retention 关闭）
;GreatestThreatThrottle=1
; 【建议 M-5】联机安全模式：置 1 强制 TargetScanInterval=1（关闭分片，规避指针哈希不确定性）
;OnlineSafeMode=0

[Speed]
; 【现网】UnlockGameSpeed: 死键（EnforceGameSpeedUnlock 为空实现，无任何行为）——保留仅为兼容旧配置
; 【建议 C-5】标注 deprecated，后续版本移除
UnlockGameSpeed=0

[System]
; 【现网】启用 Low Fragmentation Heap (LFH) 低碎片堆内存分配器，杜绝粒子、子弹和音效的堆碎片与分配延迟
; 注：LFH 一经开启不可按堆关闭（OS 语义）——本键无卸载还原，回滚=置 0 后重启进程
EnableLFH=1
; 【现网】锁定 Windows 系统时钟中断周期为 1ms，彻底消除 16ms 线程调度抖动与帧生成微卡顿
; 注：DLL 卸载时对称 timeEndPeriod(1)
HighPrecisionTimer=1
; 【建议 M-15/M-10】日志与遥测开关
;LogToFile=1
;TelemetryEnabled=1

[FogOfWar]
; 【现网】星际争霸式三态战争迷雾（运行时短路：置 0 后四处补丁字节仍在场，仅灰雾绘制层与
; 单位剔除判定关闭；字节级回滚需回退 DLL）
EnableStarCraftFog=1
; 【现网】间谍卫星重构为星际人族雷达（Scanner Sweep: 有 CD 的区域扫描超武，不再全图永久点亮）
; 注：数据补丁（SpySat 标志/超武绑定/CD/半径）无还原路径，关断后需重开局才能恢复原版类型数据
EnableSpySatRadarSweep=1
; 【现网】雷达扫描超武冷却时间（帧数，默认 600 ≈ 40 秒；代码下限 clamp 60）
RadarSweepCooldownFrames=600
; 【现网】雷达扫描超武探测半径（格子数，默认 16；代码 clamp [4,64]）
RadarSweepRadiusCells=16
; 【现网】L5 v1.6.0：敌方建筑迷雾化（从未侦察隐形 / 侦察过常驻可见）
EnableBuildingFog=1
; 【现网】L5 v1.6.0：迷雾中敌方弹道剔除（只拦绘制，命中判定不动）
EnableBulletFog=1
; 【现网】L5 v1.6.0：灰雾 4 帧渐变过渡（置 0 = 硬切换；注意混色桩仍安装、稳态强度 s=256）
FadeFogTransition=1
; 【现网】L5 v1.6.0：雷达小地图迷雾化（迷雾区 50% 灰化，敌点隐匿）
EnableMinimapFog=1
; 【建议 M-6】灰雾混色桩 B1/B2 安装门控（置 0 时不装动态强度桩，0x0047F40F/0x0047F4AE 保持原版字节）
;EnableFogBlendStubs=1

; 【计划 P-1】L4 视口刷新模式（dirty_rect_deep_dive.md §5/§7）：
;   auto        = 恢复原版 jge + 视野翻转格经 0x006DA7D0 局部打脏（3x3 外扩，>350 格退化全屏）
;   force-full  = 现网 v1.5.0 行为（jmp 强制全量重绘）
;   vanilla     = 原版 jge（无打脏，仅排查用）
;L4DirtyMode=auto
; 【计划 P-1】单帧视野翻转格阈值（超过则本帧退化全屏重绘，保护 VisibleCells[800]）
;L4LocalFlipThreshold=350
```
> **【勘误 X-2 · DA2 · 2026-09-27】Hook 开关名 ↔ 现网 ini 键 一一对应复核：文档少 1 键（`TargetScanKey`）+ 2 处键值/默认值过期（本档未改动任何 ini，仅登记差异）**
> **复核实测对象**：`ra2render/blitter_hooks.cpp` 快照 `86,961 B / 1,892 行 / MD5 e1c4a908bf7bc301ed3d24d7ff1fd065`（`LoadConfig()` 段 `:136-192`）+ `ra2render/ra2render.ini` 与 `ra2youli/ra2render.ini`（均 2,996 B / 51 行 / MD5 `0B239E604546CBEF77F70DB31E86C048`）。
> **① 代码实际读取 14 个 ini 键**（键名 → 行号）：`[Logic] TargetScanInterval(:140)`、`[Logic] TargetScanKey(:170)`、`[Render] EnableSIMD(:144)`、`[Speed] UnlockGameSpeed(:147)`、`[System] EnableLFH(:150)`、`[System] HighPrecisionTimer(:153)`、`[FogOfWar] EnableStarCraftFog(:156)`、`[FogOfWar] EnableSpySatRadarSweep(:159)`、`[FogOfWar] RadarSweepCooldownFrames(:162)`、`[FogOfWar] RadarSweepRadiusCells(:165)`、`[FogOfWar] EnableBuildingFog(:173)`、`[FogOfWar] EnableBulletFog(:176)`、`[FogOfWar] FadeFogTransition(:179)`、`[FogOfWar] EnableMinimapFog(:182)`；两份 ini 逐键齐备（含第二个 `[Logic]` 段 `:48-51`）。
> **② 本档 §一/§三/§五 的键清单只有 13 个 ⇒ 缺 `[Logic] TargetScanKey`**（L2 节流分片键：`position` = 确定性坐标哈希（**默认**）/ `pointer` = 旧指针哈希（仅单机）），它是联机门控 **G-02** 的核心键：`GetEffectiveTargetScanKey()`（`:89-94`）在 `MpActive()` 下强制 `position` 并把配置值告警重定向（`ra2render.ini:48-51` / `ra2youli/ra2render.ini:48-51`）。**这是本次核对唯一的「缺键」**；`OnlineSafeMode`(M-5)、`GreatestThreatThrottle`(M-4)、`EnableBlitHooks`(M-1)、`EnableFogBlendStubs`(M-6)、`L4DirtyMode`/`L4LocalFlipThreshold`(P-1)、`LogToFile`/`TelemetryEnabled`(M-15/M-16) 在本档均已标【建议/计划】，**未落地，不计为缺键**。
> **③ 键值/默认值过期 2 处**：⒜ §五 模板（本档 `:302`）把 `EnableMinimapFog=1` 标为【现网】—— 现网两份 ini 均为 **`EnableMinimapFog=0`**（`:46`），且代码 API 默认值已改为 **0**（`:16` `bool g_enableMinimapFog = false; // G-01: API 默认值修正为 0`、`:182` `GetPrivateProfileIntA("FogOfWar", "EnableMinimapFog", 0, iniPath)`）；⒝ §1.3 第 20 行「`EnableMinimapFog=1`（汇编侧镜像 `s_minimapFogGate`，L102…）」中的「=1」应按现值读作「**默认 0；显式配 1 才开启**（联机 `MpActive()` 下强制 0）」。
> **④ 未改动项声明**：本节仅登记文档↔配置差异，**未修改 `ra2render/ra2render.ini`、`ra2youli/ra2render.ini` 与任何源码**（任务纪律）。

---

## 六、最关键发现摘要（供看板回填）

1. **L2 节流分片键是指针哈希**（`(uintptr_t)this>>4 + CurrentFrame) % Interval`，BHK.cpp L404/425/463），违反台账 [v1.5.10] §6.2「禁用指针哈希参与分片时机」——单机无碍，**联机各端分片不同步，存在 OOS 风险**（M-5，建议 `OnlineSafeMode` + 逻辑序号分片）。
2. **全部 FogOfWar 开关是"运行时短路"而非"安装门控"**：置 0 后 0x004801F0 / 0x0047F40F / 0x0047F4AE / 0x006D3D99 四处补丁字节全部在场，且 SpySat 数据补丁与 ScenarioFlags/House+0x577A 每帧强写**无任何还原路径**（C-12/M-8/M-9）——"关开关=回滚"的直觉不成立，闸门四要素中的"卸载还原"对迷雾族整体不达标。
3. **安装失败静默 + 恒成功日志**：三个子 Install 的 bool 返回被忽略、`InstallVTableHooks` 恒 `return true` 并无条件打"全部挂载成功"（BHK.cpp L1669/1672/1675/1677-1678）——Q3「装了但没生效」审计无日志抓手，必须先落 M-18 安装位图。

---

*任务 Z-3 · 产出日期 2026-09-26 · 分析基线：blitter_hooks.cpp 1757 行 / ra2render.h 266 行 / dllmain.cpp 53 行 / 台账至 [v1.6.0] · 本文档为只读分析产物，未修改任何代码与台账。*
