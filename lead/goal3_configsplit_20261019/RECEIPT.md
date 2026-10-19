# RECEIPT —— G3-SPLIT：P2 玩法改动从默认配置拆出（补丁副本起草）

- 任务：③ 安全改动能力 · P2 玩法改动从默认配置拆出
- 角色：起草（执行者）；**母本零改动**；除本目录外零写入；未执行真机动作
- 日期：2026-10-19
- 交付目录：`out\re_work\work_chain\CONTINUE_20261003\lead\goal3_configsplit_20261019\`

## 0. 交付物与母本锚点（SHA-256 前 16 位；**R1 重交版**）

| 文件 | 角色 | SHA-256(16) | 母本 | 母本 SHA-256(16) |
|---|---|---|---|---|
| `ra2render.ini` (205 行) | 优化包默认配置 + [Gameplay] **活动节头**(:151) + 注释模板（补丁副本） | `27c9a60c55a8a1b4` | `ra2render\ra2render.ini` | `fd9ebb32dcb6cda7` |
| `blitter_hooks.cpp` (4006 行) | DLL 源补丁副本（唯一功能性改动面） | `656e6b4e48cdd251` | `ra2render\blitter_hooks.cpp` | `b461ed21aa92bd5f` |
| `ra2render.h` (495 行) | 注释副本（默认值口径同步，零二进制影响） | `10410c98642dc51a` | `ra2render\ra2render.h` | `b70cbf8d620e340e` |
| `RECEIPT.md` | 本回执 | — | — | — |

**R1 重交（2026-10-19，响应 QC_P2_VERIFY.md 判定 REFUTED）**：F1（:133 节头 `;[Gameplay]` 被注释 ⇒ 无活动 [Gameplay] 节）已修——现 `ra2render.ini:151` 为活动 `[Gameplay]` 节头，键保持全注释；全部 6 个节头注释状态复核（:10/:30/:49/:56/:62 活动，其余方括号行均为 `;` 注释行）；RECEIPT 勘误 D2-D6 五项已按副本实测行号订正（见 §4/§1）；三态 parse/迁移样例已用**真实 GetPrivateProfileStringA** 重跑全过（见 §5-T6）。本版仅 `ra2render.ini` 变更（`956e5d9aa2811045`→`27c9a60c55a8a1b4`），`blitter_hooks.cpp`/`ra2render.h` 与首版逐字节一致，母本三件哈希复核仍为首版所列（零改动）。

母本均未写入（起草后复核母本哈希与起草前一致；母本时间戳未变）。
**语法门**：补丁副本 `blitter_hooks.cpp` 已过 x86 交叉编译器 `/Zs` 纯语法检查（cl 19.44，`/W3 /EHsc /utf-8`，exit 0，零 error 零 warning）。未做完整链接产物（执行者职责，见 §5-T0）。

## 1. 只读盘点结论（复核 Lead「13/13」：**实测为 23/23**）

母本 `ra2render\ra2render.ini` 共 **23 键**（5 节：Render 2 / Logic 3 / Speed 1 / System 2 / FogOfWar 15），
代码读取点共 **24 处 / 23 键**（LoadConfig 内 23 键各 1 处 + `SyncFogStrengthMirror` 运行期重读 FogStrengthPct 1 处；唯一双读键 = FogStrengthPct），
一一对应、无孤儿键、无幽灵读。Lead 的「13/13 对应」与母本现状不符（13 恰为本次迁入 [Gameplay] 的键数，疑为口径错位）。

全部 ini 路径解析走两个哨兵封装（可区分「键缺失」与「键值=默认」，RADAR-FIX F3 口径）：
- `GetIniStringEx` / `GetIniIntEx`（母本 blitter_hooks.cpp:368/380）→ 所有键；
- 例外：`SyncFogStrengthMirror` 直读 `FogOfWar/FogStrengthPct`（blitter_hooks.cpp:500）。
- 无 `GetPrivateProfileIntA` 使用；无重复同名节（API 只读第一节陷阱不适用）。

配置装载与安装/卸载对称路径（盘点）：
- 装载：`DllMain(DLL_PROCESS_ATTACH)` → `InstallVTableHooks`（dllmain.cpp:31 → blitter_hooks.cpp:3696/3781 原行号）→ **`LoadConfig()` 只在 init 读一次**（改键须重启）。
- ini 部署链：`ra2render\build.bat` 只部署 DLL（`copy /y ra2render.dll ..\ra2youli\`）；**ini 不在构建部署链内**（游戏目录 `ra2youli\ra2render.ini` 为手工部署件，实测 23 键与母本同键同值、仅注释/顺序不同、5 节各出现一次）。
- 卸载对称：`RemoveVTableHooks`（blitter_hooks.cpp:3801）——3 个 inline 钩子移除器（CellClassDraw/GreatestThreat/RadarFog）+ **13 个虚表指针按安装正序逐对还原**（母本即如此，非逆序；本补丁未触碰）+ .text 补丁包严格逆序硬回滚（sw→vxl→gap，gap 内部 P-2.3→P-2.2→P-2.1）；MP 边沿同步 `MpGateEdgeSyncGapProtection`（:3489）单机→联机逆序回滚 / 联机→单机门禁重装。
- **不对称点（盘点发现，拆分后自动消解）**：`PatchSpySatBuildingTypes`（:1462，UpdateVisionGrid 懒加载调用 :1611-1613）改写 BuildingType 运行期数据（+0x16A5 常亮位→false、+0x16F0 超武索引→PsychicReveal），**无 Remove 对应件**（进程级生命周期，init 懒加载一次性）。新默认 =0 时该函数 :1463 直接 return ⇒ 零改写 ⇒ 卸载对称性对默认部署自动成立（判据④）。

## 2. 四项玩法键实测现状（拆分前）

| 项 | 键 | 母本 ini | 母本 ini 行 | 代码读取(母本) | 代码 API 默认 | 全局初始化器(母本) | 实测判定 |
|---|---|---|---|---|---|---|---|
| ①星际迷雾·总闸 | `FogOfWar.EnableStarCraftFog` | `=1` | :64 | :563 | 1 | `=true`(:11) | **非原版，默认开启** |
| ①星际迷雾·模式 | `FogOfWar.VisibilityMode` | `=starcraft` | :117 | :600 | "starcraft" | `="starcraft"`(:27)/`false`(:26) | **非原版，默认开启** |
| ②间谍卫星主动雷达 | `FogOfWar.EnableSpySatRadarSweep` | `=1` | :120 | :566 | 1 | `=true`(:12) | **非原版，默认开启**（:1462 起改写 BuildingType +0x16A5/+0x16F0） |
| ③迷雾隐形·建筑 | `FogOfWar.EnableBuildingFog` | `=1` | :130 | :580 | 1 | `=true`(:15) | **非原版，默认开启** |
| ③迷雾隐形·弹道 | `FogOfWar.EnableBulletFog` | `=1` | :133 | :583 | 1 | `=true`(:16) | **非原版，默认开启** |
| ③迷雾隐形·机动单位 | `FogOfWar.EnableUnitFog` | `=1` | :138 | :592 | 1 | `=true`(:17) | **非原版，默认开启** |
| ④寻敌频率节流 | `Logic.TargetScanInterval` | `=8` | :25 | :547 | 8 | `=8`(:6) | **非原版（原版=1 每帧全量），默认节流** |

结论：**四项全部坐实**——不仅 ini 出厂值非原版，代码 API 默认值与全局初始化器同样非原版。
因此纯 ini 拆分不充分，本补丁同时矫正代码默认（三级回退的第三级 = 原版）。

## 3. 键位迁移映射表（13 玩法键 → [Gameplay]；10 优化键原位保留）

### 3.1 迁入 [Gameplay]（补丁副本 ini **活动节头 :151**，出厂键全注释 = 缺键 = 原版默认）

| # | 旧位置 | 旧值 | 新位置 | 新出厂默认(代码) | 语义变化说明 |
|---|---|---|---|---|---|
| 1 | `Logic.TargetScanInterval` | 8 | `[Gameplay].TargetScanInterval` | **1**（原版=每帧全量寻敌） | 默认值 8→1（判据①）；值域钳 1..64 不变；**G-08 联机恒强制 1 不变** |
| 2 | `Logic.TargetScanKey` | position | `[Gameplay].TargetScanKey` | "position"（不变） | 节流关（Interval=1）时无消费方；**G-02 联机强制 position 不变** |
| 3 | `FogOfWar.EnableStarCraftFog` | 1 | `[Gameplay].EnableStarCraftFog` | **0** | 总闸默认关；FOG-SPLIT 三态语义一字未改 |
| 4 | `FogOfWar.VisibilityMode` | starcraft | `[Gameplay].VisibilityMode` | **"vanilla"** | 模式默认原版；未知值收敛方向 starcraft→**vanilla**（安全侧改原版）；F1 优先级/vanilla 覆盖逻辑不变 |
| 5 | `FogOfWar.EnableSpySatRadarSweep` | 1 | `[Gameplay].EnableSpySatRadarSweep` | **0** | 默认不做间谍卫星重构（:1462 早退，零数据改写） |
| 6 | `FogOfWar.RadarSweepCooldownFrames` | 600 | `[Gameplay].RadarSweepCooldownFrames` | 600（不变，伴生） | 仅 Sweep=1 时有意义 |
| 7 | `FogOfWar.RadarSweepRadiusCells` | 16 | `[Gameplay].RadarSweepRadiusCells` | 16（不变，伴生） | 仅 Sweep=1 时有意义 |
| 8 | `FogOfWar.EnableBuildingFog` | 1 | `[Gameplay].EnableBuildingFog` | **0** | FOG-SPLIT「不受总闸影响」语义不变 |
| 9 | `FogOfWar.EnableBulletFog` | 1 | `[Gameplay].EnableBulletFog` | **0** | 同上 |
| 10 | `FogOfWar.EnableUnitFog` | 1 | `[Gameplay].EnableUnitFog` | **0** | 同上（旧 API 默认 1 的非原版行为一并矫正） |
| 11 | `FogOfWar.FadeFogTransition` | 1 | `[Gameplay].FadeFogTransition` | 1（不变，伴生） | 仅总闸=1 时有意义（总闸默认 0 ⇒ 自然失效） |
| 12 | `FogOfWar.EnableMinimapFog` | 0 | `[Gameplay].EnableMinimapFog` | 0（不变） | G-01 联机强制 0 不变；ZC-3 未验收维持默认关 |
| 13 | `FogOfWar.RadarFogGuardMode` | 3 | `[Gameplay].RadarFogGuardMode` | 3（不变，伴生） | 仅 MinimapFog 生效时被消费 |

### 3.2 留在优化包原位（读取路径一字不动）

| 键 | 值 | 代码读取(母本) | 留位理由（不改变原版行为） |
|---|---|---|---|
| `Render.EnableSIMD` | 1 | :551 | 渲染吞吐，像素等价 |
| `Render.EnableVxlCachePrewarm` | 0 | :634 | 默认不碰 .text |
| `Logic.EnableSWChargeOpt` | 0 | :642 | 默认不碰 .text；零语义变化选装 |
| `Speed.UnlockGameSpeed` | 0 | :554 | 默认=保护原版速度控制权 |
| `System.EnableLFH` / `System.HighPrecisionTimer` | 1 / 1 | :557 / :560 | 分配器/时钟粒度，无玩法语义 |
| `FogOfWar.EnableGapProtection` | 0 | :622 | 修复选装，默认=原版；联机强制不装+MP 边沿回滚/重装不变。**迁 [Gameplay] 与否挂未裁决项 U2** |
| `FogOfWar.FogStrengthPct` | auto | :709 + 运行期 :500 | 表现校准，auto=不补偿；总闸全关后无消费方。**运行期重读仍读 [FogOfWar]，故必须留在原节** |
| `FogOfWar.L4DirtyMode` | force-full | :775 | 默认=现状逐位等价 |
| `FogOfWar.FogProbe` | 0 | :791 | 探针默认关 |

### 3.3 设计抉择：同文件 [Gameplay] 节 vs 独立 ra2render_gameplay.ini → **择同文件节**

理由：(a) 现有读取封装以 `(sec,key,iniPath)` 为参，换节零管道改动；(b) 单文件部署保持现状（ini 本就不在 build.bat 部署链，独立文件会新增卸载孤儿面与 QC 取证只拷单文件的漏配风险）；(c) F3 哨兵机制已能区分缺键，「出厂模板全注释」即缺键语义，独立文件带来的隔离收益为零。否决独立文件方案记录在案。

## 4. 代码改动面（补丁副本 blitter_hooks.cpp；行号为副本行号）

| 改动 | 副本行号 | 内容 |
|---|---|---|
| D0 文件头横幅 | :6-19 | 改动面 A-D 声明（判据可追溯） |
| D1 全局初始化器 | :26, :31-37, :48-49 | 玩法族收敛原版：interval=1、各 Enable*=false、visibilityVanilla=true、modeRaw="vanilla"；伴生键值不变仅注释迁移标注 |
| D2 三级回退读取器 | :423-459 | `GetGameplayIntEx`(:423) / `GetGameplayStrEx`(:438)：①[Gameplay] → ②旧节 [Logic]/[FogOfWar] **只读**迁移（不写 ini）→ ③原版默认；复用 F3 哨兵（显式 opt-out 值也算命中，不会误判回落） |
| D3 LoadConfig 13 读点 | :625, :642, :645, :648, :651, :656, :659, :662, :665, :670, :680, :693, :735 | 全部改走 D2；值域钳位/解析逻辑零改动 |
| D4 迁移留痕行 | :738-770 | `[ra2render-gameplay]` 启动行：旧节命中数 + 逐键名（判据②取证锚点；只读迁移提示，绝不写 ini） |
| D5 未知 VisibilityMode 收敛 | :683-689 / :815-817 | 未知值收敛 starcraft→**vanilla**（原版安全侧），告警行保留 |
| D6 头注默认口径 | ra2render.h :358-381 | 注释同步（零二进制影响） |

**零改动承诺**：`GetEffectiveTargetScanInterval`(G-08)/`GetEffectiveTargetScanKey`(G-02)/`GetEffectiveMinimapFog`(G-01)/`GetEffectiveRadarFogGuardMode`/`GetEffectiveFogMasterGate`/`SyncFogMasterMirror`/`MpGateEdgeSyncGapProtection`/`CheckMpGateTransition`/全部 Install*/Remove* 补丁器与钩子体一字未动（只消费全局，不关心全局来自哪一节）。优化键 10 处读取点原样（副本 :706 EnableGapProtection、:726 EnableSWChargeOpt、:829 与运行期 :571 两处 FogStrengthPct、:895 L4DirtyMode、:911 FogProbe——行号已按副本逐条复核）。

## 5. 自测计划（供执行者；起草人未自核真机）

- **T0 构建**：`ra2render\build.bat` 编译 DLL（本目录补丁三件覆盖母本后）；产物哈希登记；`verify_hooks.py` 常规配对正则（Install*/Remove* 零变化，D2 命名刻意避开 Install*/Remove* 前缀）。
- **T1 判据①（默认=原版，以启动日志为证，不看 ini 文本）**：部署优化包 ini + 新 DLL → 冷启 → `ra2render.log` 必须同时满足：
  - `[ra2render] 配置加载完成: ... TargetScanInterval=1 ... EnableStarCraftFog=false ... EnableSpySatRadarSweep=false ... EnableBuildingFog=false, EnableBulletFog=false ... EnableUnitFog=false`（"配置来源"行各项=「默认值」）；
  - `[ra2render-fog] 灰雾总闸: EnableStarCraftFog=0 (来源: 默认值 ...)`；
  - `[ra2render-visibility] VisibilityMode=vanilla (来源: 默认值) | 生效: 原版可见性...`；
  - `[ra2render-gameplay] [G3-SPLIT] 玩法配置拆分: 旧节只读迁移命中 0 项`；
  - `[ra2render] 门控: ... TargetScanInterval=配置(1)->生效(1)`；
  - 无 `[ra2render-fog] 成功将间谍卫星建筑...重构` 行（SpySat 零改写）；
  - 遥测行：`机动单位剔除/建筑剔除/弹道剔除 ≡0`、`被 mode 覆盖而放行 >0`（判 visibility 档）。
- **T2 判据②（老用户迁移）**：取母本 ini（含 TargetScanInterval=8@[Logic]、四项=1@[FogOfWar]）+ 新 DLL → 冷启 → 上述各键日志读回**保持开启态**；`[ra2render-gameplay] ... 命中 13 项（迁移键: ...）`；并且 ini 文件 mtime/内容**零变化**（DLL 不写 ini）。边界：仅迁一半（如只留 EnableStarCraftFog=1）→ 命中 1 项，其余走原版默认。
- **T3 判据③（联机门控不破）**：`[ra2render-mpgate] MP 门控生效值` 行字段与拆分前同构；联机对局日志 `TargetScanInterval=配置(N)->生效(1)`、`TargetScanKey=配置(*)->生效(position)`、`EnableMinimapFog=配置(*)->生效(0)`；EnableGapProtection=1 单机装上→进联机 `mp-edge-rollback`→回单机 `mp-edge-reinstall`（三点 installed 0↔3）与拆分前逐字节同行为。logs schema 除新增 `[ra2render-gameplay]` 行外零变化（遥测解析器兼容）。
- **T4 判据④（卸载对称）**：默认 ini 下 `RemoveVTableHooks`（DLL 卸载）日志无任何「还原我方未写字节」告警；SpySat 路径零改写 ⇒ 无需回滚件；EnableSpySatRadarSweep=1 时维持旧行为（进程级生命周期，无运行期卸载——与母本一致，见 §7-R2）。
- **T5 显式新节**：[Gameplay] 显式 `;` 去注释（如 TargetScanInterval=8、EnableStarCraftFog=1）→ 日志来源=「ini」且生效；显式 =0 也能压过旧节残留值（opt-out 命中语义，D2 专门保证）。
- **T6（R1 重交新增，起草人已离线实跑——真实 `GetPrivateProfileStringA`，非 ini 文本推断；真机复跑仍归核验员）**：
  - **A 态·新交付 ini**（[Gameplay] 活动节头 :151、键全注释）：13 玩法键三级回退全部落「default=原版」（TargetScanInterval=1 / 各 Enable*=0 / VisibilityMode=vanilla / 伴生键默认值不变）；10 优化键抽查逐键命中原节原值；`[Gameplay]` 节可被 API 寻址（F1 回归通过）。
  - **B 态·迁移**（母本 ini + 新读取顺序）：13 键全部命中旧节（TargetScanInterval←[Logic]=8，其余 12 键←[FogOfWar] 原值）⇒ 判据②迁移路径 API 级成立。
  - **C1 态·opt-in**（临时副本去注释 TargetScanInterval=8 / EnableStarCraftFog=1）：`Gameplay.TargetScanInterval=8`、`Gameplay.EnableStarCraftFog=1` 命中，旧节 ABSENT ⇒ 「去行首 ; 即生效」主路径修复证实。
  - **C2 态·opt-out**（[Gameplay] 显式 =0/=1 vs 旧节 =1/=8）：①[Gameplay] 命中且优先（0 压过旧节 1）⇒ opt-out 命中语义成立。
  - 测试临时件已即建即删，交付目录仅含 4 个交付件。

## 6. 回退

- 本补丁为**纯源码/配置副本**，未触磁盘 gamemd.exe、未触真机。回退 = 停用交付目录三件、母本原样（母本哈希见 §0，可再验）。
- 已施用后的回退：用母本三件覆盖回 `ra2render\` 并重跑 build.bat 即完全回到拆分前；`ra2youli\ra2render.ini` 施用前由执行者另行备份（本目录不含部署态文件副本）。
- [Gameplay] 节设计为**加法兼容**：旧 DLL 读新 ini 时 [Gameplay] 节不可见（旧代码只读 [FogOfWar]/[Logic]/[Render]/[Speed]/[System]），注释模板零风险；新 DLL 读旧 ini 走旧节迁移回退。双向可回退。

## 7. 挂账/未裁决项（须 Lead 或核验员裁决，起草人仅记录）

- **U1「显式开启」口径**：拆分前出厂 ini 把四项置 1，无法与用户手改区分。D2 采用「旧节命中即迁移」（最大化保留开启态，判据②字面满足）。若 Lead 要求「仅真手改用户保留」，需另立一次性迁移标志（如安装器写 [Gameplay] 快照），本补丁未擅自实现。
- **U2 `EnableGapProtection` 归属**：修复选装（默认 0=原版）暂留 [FogOfWar]；其改仿真 +0x134、进 .SAV，若按「玩法」从严应同迁 [Gameplay]，待 Lead 裁决（暂留的理由：避免动 MP 握手/存档标记的既有口径）。
- **R1（存量残余，本补丁不动）**：`UpdateVisionGrid` 每帧无条件清 Scenario FogOfWar 位（母本 :1620）与 FOG-SPLIT ①②解耦恒调用——该写为「黑幕走 SHROUD」机制的前提，非四项玩法键范围；核验默认档黑幕观感时注意。
- **R2（存量残余，本补丁不动）**：母本 :1624 每帧无条件 `House+0x577A(SpySatActive)=0`（裂缝失效锁死 workaround），不受 EnableSpySatRadarSweep 门控——严格说是第 5 处玩法向写点；按「最小补丁面」纪律未纳入本卡，请 Lead 定夺是否另立 P3 卡。
- **R3（性能注记）**：玩法全关时视觉网格/渐变计算仍在跑（纯开销，无消费者），与母本行为一致，不在本卡范围。

## 8. 核验员清单（起草人不自核；勾选需附证据件）

- [ ] **F1 回归（R1 新增）**：交付 ini :151 为活动 `[Gameplay]` 节头；全文件 6 活动节头注释状态逐行核过；真实 GetPrivateProfileStringA 三态复跑（T6 A/B/C1/C2）全过
- [ ] ① 默认配置四项**运行时生效值**全关——以 `ra2render.log` 启动行读回为证（§5-T1 七条全过；不接受只看 ini 文本）
- [ ] ② 老用户升级保持开启——母本 ini + 新 DLL 实测，命中 N 项日志 + ini 文件零写变（§5-T2）
- [ ] ③ 联机门控不变——G-08/G-02/G-01 生效值行 + gap mp-edge-rollback/reinstall 双向（§5-T3）
- [ ] ④ 卸载对称覆盖新配置——RemoveVTableHooks 无告警、SpySat 默认零改写、旧 DLL↔新 ini 双向可回退（§5-T4/§6）
- [ ] 键位映射表逐键与 §3 一致（含伴生键默认不变）
- [ ] 补丁副本哈希 = §0 所列（R1 版：ini=`27c9a60c55a8a1b4`）；母本三件哈希仍 = §0 所列（零改动复核）
- [ ] build.bat 产物过 verify_hooks.py 配对正则（D2 新函数名不触发 Install*/Remove* 误配）
- [ ] U1/U2/R1/R2 已呈 Lead 并有结论

## 9. R1 重交记录（响应 lead\goal3_configsplit_20261019\QC_P2_VERIFY.md）

| 判定项 | 处置 | 证据 |
|---|---|---|
| F1（实质缺陷，必修）| 已修：ini :133 注释横幅行改为说明行，**:151 新增活动 `[Gameplay]` 节头**（仅节头去注释，13 键保持注释）；全文件节头状态复核 = 6 活动（:10/:30/:49/:56/:62/:151）+ 其余方括号行均为 `;` 注释行 | T6-A/C1 真实 API 实测：缺键落 default、去注释命中 [Gameplay] |
| D2 勘误 | §4 D2 行号 :413-464→**:423-459**（GetGameplayIntEx :423 / GetGameplayStrEx :438） | 副本 grep 实测 |
| D3 勘误 | §4 零改动行号 5 项：:690→**:706**（GapProtection）、:710→**:726**（SWChargeOpt）、:813/:583→**:829/:571**（FogStrengthPct 双读点）、:879→**:895**（L4DirtyMode）、:895→**:911**（FogProbe） | 副本 grep 实测（含判定书未列的 L4DirtyMode 一并订正） |
| D4 勘误 | §1 读点口径 23 处→**24 读点 / 23 键**（唯一双读键 = FogStrengthPct） | LoadConfig 23 键 + SyncFogStrengthMirror :571 |
| D5 勘误 | §4 D5 行号 →**:683-689 / :815-817** | 副本 grep 实测（:685 else-if / :688 else / :816 告警行） |
| D6 勘误 | §1「安装严格逆序」→ **13 个虚表指针按安装正序逐对还原（母本即如此）**，严格逆序仅指 .text 补丁包（sw→vxl→gap、gap 内部 P-2.3→P-2.2→P-2.1）；本补丁未触碰 | RemoveVTableHooks 实测 13 处 PatchVTablePointer 还原调用 |
| 重交哈希 | `ra2render.ini` 956e5d9aa2811045→**27c9a60c55a8a1b4**（唯一变更件）；`blitter_hooks.cpp`/`ra2render.h` 不变（656e6b4e48cdd251 / 10410c98642dc51a）；母本三件复核不变 | sha256sum 起草后复跑 |
