# ZCode 后续真机验收卡 · P-2.1 A3 行为验收（战役轨 C / 诊断钩 H）+ A4/A5

> **卡号**：`ZC-GAP-P21-A3` · **优先级**：P0 收尾（A1/A2 已 PASS，A3 是裂缝保护唯一未闭环行为面）  
> **执行方**：ZCode（真机/补丁安装唯一写者）· **起草**：MiMo（R-P21-A3，基于 RESULT_GAP_P21 阻塞定谳）  
> **上游**：`docs/re/landing_pack_gap_p21.md`（ZC-GAP-P21 冻结卡）· `out/re_work/zcode_live/gap_p21/RESULT_GAP_P21.md`（A1/A2 PASS + A3 阻塞实证）· `docs/re/gap_psychic_reveal_deep_dive.md`（R-GAP-PSY）· `docs/re/sav_gap_cell_abi_deep_dive.md`（R-SAV-GAP，A4 依据）  
> **本卡范围**：**只做 A3/A4/A5 行为验收**（补丁本体 P-2.1 已落地，本卡不改字节面）。两套可选路径：**方案 C-战役（首选）** 与 **方案 H-诊断钩（备选，需审批）**。  
> **证据基线**：`gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · ImageBase `0x00400000` · `file_off = VA − 0x00400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **写作用域**：`docs/re/landing_pack_gap_p21_a3.md` + `out/re_work/re_sprint/R_p21_a3/**`；**禁写** `ra2render/**`、`gamemd.exe`（只读可引 `RESULT_GAP_P21`）。

---

## 0. 一句话

A3 的两条硬阻塞（bench 遭遇战**不实例化预置建筑**、**地图触发器不触发**）使「敌方 GapGenerator + 游戏自身 RevealArea2」在 `ra2bench` 造不出来；本卡给出 **C-战役**（ra2youli/ra2forge 战役图：真敌方缝 + PsychicReveal/任务开图）与 **H-诊断钩**（受控帧调 `RevealArea2`，默认关、仅诊断档）两条可执行路径，并把 **A4 存读档** 与 **A5 DestroyGap 回落** 一并纳入同一验收面。判据统一：**缝仍在 + `Cell+0x134` 不清 0**。

---

## 1. 背景与阻塞回顾（只引用，不复翻案）

| # | 阻塞 | 证据（RESULT_GAP_P21 [3]） | 对 A3 的含义 |
|---|---|---|---|
| B-1 | `ra2bench` 遭遇战**不实例化地图预置建筑** | 自建 GAPP21 图（玩家基地 + 14 家环置 GAGAP/CAFARM02）开局后全图 `bld_cells≡0`（AltOcc bit0x80），t=0 与 t=165s 一致 | 造不出**真**敌方 GapGenerator 实体（`CreateGap` 无从盖印） |
| B-2 | **地图触发器不触发** | TA11 文本 / TA17 RevealAroundWaypoint 均无反应；`mapped_cells` 恒定；已试 repeating/CellTags 两种索引/`IgnoreGlobalAITriggers=no`/清 `[PlayerHouse+0x240]` | 游戏自身不会发起 `RevealArea2`，补丁点无可测 |
| B-3 | AI 不起基地 | t=165s `bld_cells` 仍 0 | 不能指望 AI 自建 GAGAP |

⇒ A3 需要同时具备 **(a) 敌方 GapGenerator 实体（经 `CreateGap 0x6FB170` 盖印 `+0x134>0`）** 与 **(b) 由游戏发起的 `RevealArea2 0x5678E0` 调用**。ZCode 结论已给出两条出路：**战役模式**（`ra2youli` 战役的 `CAFARM02` gap 农场已验证可用）或**诊断钩**（`TriggerRadarSweep` 同款，受控帧调 `RevealArea2`）——均需另卡（本卡）。

**已留 harness（`tools/gap_p21_*.py`）**：场景图生成、地图浏览器选图、全图 CellClass 扫描、目标格 `+0x134` 注入、开图前后对拍——两方案均直接复用（见 §5）。

---

## 2. 方案 C-战役（首选：真实体 + 真开图）

### 2.1 为什么战役模式可达

| 前提 | bench 遭遇战 | 战役模式（ra2youli / ra2forge） |
|---|---|---|
| 预置建筑实例化 | ❌ `bld_cells≡0` | ✅ 战役图预置建筑/单位全部实例化（`RA2F1`/`ECH01–03` 既有战役链可证） |
| 地图触发器 | ❌ 不触发 | ✅ 战役图 Trigger/Tag/CellTags 正常求值（`ra2forge/triggers.py` 导出序已定谳 R-TRG-SAV） |
| 敌方 GapGenerator | ❌ 造不出 | ✅ 预置敌对 `GAGAP` / `CAFARM02`（gap 农场；RESULT_GAP_P21 已验证 CAFARM02 在战役可用） |
| 游戏发起 `RevealArea2` | ❌ | ✅ PsychicReveal 超武（Case 11，双 `call 0x5678E0`）或任务 Trigger `RevealAroundWaypoint`（TA17） |

### 2.2 专用验收图（战役 gap 农场 + 任务开图）

用 `ra2forge.MissionMap` / `triggers` 生成（可直接 graft/改 `tools/gap_p21_map_gen.py` 的战役模式变体），装入 `ra2youli` 战役链（散装 `BATTLEMD*.INI` 注册，见 `docs/re/mix_hygiene_product.md`：战役注册**只认散装** `BATTLEMD*.INI`，MIX 内永不加载）。

**图面要素**：

| 要素 | 值 | 说明 |
|---|---|---|
| `[Basic]` | `FogOfWar=yes` | 黑幕/裂缝前提（bench 基准图默认 no，必须显式开） |
| 玩家 | `Americans`（或任一与缝宿主交战方） | 基地落在敌方缝半径内 |
| 敌方缝 | `GAGAP`（主）/ `CAFARM02`（备，隐形 gap 农场） | 与玩家**交战**（`CreateGap` 对己方/盟友跳过盖印，`0x6FB2D6 call 0x4F9A50` / `jne`） |
| 缝宿主老家 | 敌方 ConYard/Power | 防敌方瞬间战败导致 `DestroyGap` 提前发生 |
| 开图动作 A | **PsychicReveal**（超武 Case 11 @ `0x6CD70C`） | 双 `call RevealArea2`（`0x6CD773`/`0x6CD79C`），半径 `Rules+0xFEC` 被 `min(10,·)` 夹紧（`0x567A4A`） |
| 开图动作 B | Trigger **TA17 RevealAroundWaypoint** | 5×5 waypoint 网格（间距 4 格）覆盖基地 ±8 格；waypoint 字母编码 `A=0..Z=25, 26+ 两字母`（50↔AY / 121↔DR / 469↔RB 已实证对齐） |
| 触发器 | `ElapsedTime=N s` 一次性释放全部开图动作 | 必须绑 `[CellTags]`（键 = `y*1000+x`，战役图 `30105..30108` 同编码），否则 TagClass 不实例化、事件永不求值 |
| `IgnoreGlobalAITriggers` | 战役口径 `yes`（maplib 默认） | 确定性最稳（`house_team_ai_residual_deep_dive.md` P1）；若普通触发器被连带静默，再降为 `no` 并单独记录 |

### 2.3 执行步骤（方案 C）

| 步 | 动作 | 工具/资产 | 记录 |
|---|---|---|---|
| C1 | 生成/改战役验收图 `ECHGAP.MAP`（或 graft 到 `ECH01` 骨架） | `ra2forge/maplib.py` + `triggers.py`；参考 `tools/gap_p21_map_gen.py` | 图明文 + sha256 |
| C2 | 注册战役条目（`BATTLEMD98.INI` 追加 id，`expandmd98.mix` 仅资源） | 散装 INI；**不覆盖官方 `BATTLEMD.INI` 条目名** | 注册前后 BATTLEMD 清单 diff |
| C3 | 部署补丁态：`ra2youli/ra2render.ini` 显式 `EnableGapProtection=1`（对照组另跑 0） | 已有安装器（RESULT_GAP_P21 [2]） | 启动日志 `GapProtection=on` |
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0
| C4 | 进战役 → 选该关 → 开局至对局稳定（帧 > 200） | 复用 `bench_replay.BattleMonitor` | 截图 + frame |
| C5 | **before**：全图扫描 `+0x12C/+0x130/+0x134` | `gap_p21_a3.read_gap_state` | `gap_cells>0`、`gap_hist` |
| C6 | 等触发器开图（或手动发射 PsychicReveal）+ reshroud 等待 | `--settle` / `--post` | 开图事件证据（mapped 上升 / 超武动画） |
| C7 | **after / after2**：再扫 | 同 C5 | 对比 JSON |
| C8 | A4：存 `.SAV` → 读档 → 再扫 | 游戏内存读档 | 见 §4 |
| C9 | A5：摧毁缝建筑（或断电/变卖使 `GeneratingGap` 翻假）→ 再扫 | 同上 | 见 §4 |
| C10 | 对照组：`EnableGapProtection=0` 重跑 C4–C7 | 同一图同一路径 | 预期 `GAP-WIPED`（bug 复现） |

### 2.4 判据（方案 C；逻辑计数为主，截图像素为辅）

| ID | 判据 | 量化 | 证据 |
|---|---|---|---|
| **C-J1 缝在** | before：`gap_cells > 0`，且目标格 `+0x134 ≥ 1` | `a3_before_*.json` `gap_hist` | [实证] |
| **C-J2 缝仍在** | after/after2：目标格 `+0x134` **不清 0**（逐格 kept ≥ 90% 量级同 before；开图半径内抽样全部 `>0`） | `before_cells_kept_gap` / `wiped` | [实证] |
| **C-J3 对照** | 同图关补丁：被开图格 `+0x134` 归 0 / `gap_cells` 显著下降 = 废缝 bug 复现 | `GAP-WIPED` verdict | [实证] |
| **C-J4 视觉** | 扫描退去后该格回到黑雾/缝层（非永久透亮）；before/after2 截图 diff | PNG md5 + 像素差 | [实证] |
| **C-J5 禁「没崩当成功」** | 无 `except.txt` **且** C-J2 必须成立 | — | 卡规 |

**核心口径重申**：`Cell+0x134 = GapsCoveringThisCell` 是敌对缝引用计数（`CreateGap inc` @ `0x6FB365` / `DestroyGap dec` @ `0x6FB5FB`）；`ReshroudCell 0x487690` 将 `ShroudCounter` 钳位于它 ⇒ **清 0 = 永久废缝**（不自愈）。判据「不清 0」就是 P-2.1 行为的直接观测量。

---

## 3. 方案 H-诊断钩（备选：受控帧 RevealArea2 A/B；需审批）

> **定位**：战役轨若因导航/图面原因无法稳定复现，用**受控帧**直接调 `MapClass::RevealArea2` 完成 A/B。  
> **性质**：诊断手段，**不是**产品路径；默认关、仅诊断档构建启用。

### 3.1 形态（对齐既有 `TriggerRadarSweep` 同款诊断风格）

| 项 | 约定 |
|---|---|
| 调用点 | `MapClass::RevealArea2` @ `0x005678E0`（**只调用，不 Hook 改写其内部**） |
| 触发方式 | 诊断键/受控帧指令（如 ini `GapDiagRevealFrame=N` 或外部指令触发一次）；**单次、可计数** |
| 参数 | 目标格集合（复用 `INJECT_TARGET_CELLS` 5×5 网格）+ 半径（对齐 PsychicReveal 的 `min(10, Rules+0xFEC)` 或固定 4/10） |
| 默认 | **`0=关`**；`MpActive()` 为真 **强制关**（与 `EnableGapProtection` 同级门控） |
| 档位 | 仅诊断档构建（独立 DLL/构建号）编译该路径；生产构建 **不含** 调用代码（或编译期剥离） |
| 遥测 | `gapDiagRevealCalls`（计数）、`gapDiagRevealFrame`、调用前后 `+0x134` 快照哈希（独立环，**不进**帧 CRC `0x64DAB0`） |

### 3.2 A/B 流程

1. 建立缝态：真实 `CreateGap`（战役图）或 harness `--inject 5`（诊断捷径，**不替代** C-J1 真盖印，仅测 NOP 点）。  
2. 记录 before `+0x134`。  
3. 受控帧调用 `RevealArea2`（诊断钩触发一次）。  
4. 记录 after `+0x134`：  
   - 未打补丁：清 0（bug）；  
   - 已打补丁（`0x568273=90×6`）：保持（修复）。  
5. 对照 `EnableGapProtection=0/1` 两轮同参数。

### 3.3 风险与审批点（执行前必须拿到）

| ID | 风险 | 控制 |
|---|---|---|
| H-R1 | `RevealArea2` 在**确定性红线禁改域**（`ARCHITECTURE_ATLAS` §红线：`RevealArea*` 不可改） | **只调用不改写**；单机/战役诊断 only；联机强制关 |
| H-R2 | 调用会写 Cell 状态（`+0x12C/+0x130` 仍生效）⇒ 演进改变 | 仅诊断局；**禁止**把诊断局存档当产品档；不进回放/联机 |
| H-R3 | 若误做成 Hook 改写/跳帧/限频 | 红线禁止；本方案明确排除 |
| H-R4 | 诊断代码混入生产构建 | 编译期剥离 + 构建号区分；`MpActive` 强制关 |
| H-R5 | RNG 流污染 | `RevealArea2` 与 Case11 **0 次**调用 `ScenarioClass::Random`（R-sw-radius 已实证）；诊断钩自身**禁止**调 `0x65C780`（B-N16） |

**审批点（缺一不可）**：① Lead 书面同意进代码轨（`ra2render` 写权仍归 ZCode，本卡起草不写）；② 明确「诊断档 only + 默认关」契约写入 ini 说明块；③ 验收结束回归生产构建零诊断路径；④ 任何联机会话出现 `gapDiagRevealCalls>0` 即判违规。

### 3.4 判据（方案 H）

与 C-J2/C-J3 相同：目标格 `+0x134` 在补丁态**不清 0**、在原版态归 0；另要求 `gapDiagRevealCalls` 与预期触发次数一致（证明钩子真的调到了 `RevealArea2`，而非空转）。

---

## 4. A4 存读档 · A5 DestroyGap（同图同局纳入）

依赖 A3 场景（真缝态已建立）。依据 `docs/re/sav_gap_cell_abi_deep_dive.md`。

### 4.1 A4 · 存 `.SAV` → 读档

| 项 | 内容 |
|---|---|
| 步骤 | A3 判定通过后：游戏内存档 `.SAV` → 读档 → 再扫 `+0x12C/+0x130/+0x134` |
| 机制事实 | `+0x134` 在 `CellClass` **0x148 裸块内整块入档**（`GetSize=0x148`，`0x487E70`），无字段过滤、无压缩；读档**不**重放 `CreateGap` ⇒ **存多少读出多少，不自愈** |
| **判据 A4-J1** | 读档后目标格 `+0x134` **与存档前一致**（逐格相等；kept=100%） |
| **判据 A4-J2** | `except.txt` 空；读档后 `gap_cells` 与存档前同量级 |
| **判据 A4-J3** | 补丁局存档**标记**（若已实现 `GapProt Version` OLE 流）；无标记则在回执注明「未实现，按值域验收」 |
| 风险 | 补丁档与原版档**格式互通、语义不互通**（`+0x134` 演化不同）；混端禁联；卸载后不读补丁档 |

### 4.2 A5 · DestroyGap / 摧毁缝建筑

| 项 | 内容 |
|---|---|
| 步骤 | 同局摧毁敌方缝建筑（或断电/变卖使七级门控翻假 → `GeneratingGap` true→false）→ 再扫 |
| 机制事实 | `DestroyGap 0x6FB470` 对覆盖格 `dec [cell+0x134]`（`0x6FB5EE..0x6FB5FD`）；归零后 `ReshroudCell` 钳位失效于 0 ⇒ 可重遮；`House+0x577A`（SpySatActive）且计数归零时恢复 `CopyFlags` bit3/4（`0x6FB67A/0x6FB699`） |
| **判据 A5-J1** | 原覆盖格 `+0x134` **回到 0**（或 decremented 与摧毁前覆盖数一致），**无残留永久缝**（计数不悬空） |
| **判据 A5-J2** | 该格可重新被 `ShroudCounter` 遮蔽（钳位 `≤ GapsCovering` 不再截断为 0）；截图像素允许回黑 |
| **判据 A5-J3** | `except.txt` 空 |
| 备注 | A5 验证的是「计数簿记正确」，**不是**补丁删除面；若 A5 FAIL 而 A3 PASS，优先怀疑 `DestroyGap` 侧/覆盖半径，而非 P-2.1 NOP |

---

## 5. 复用 harness：`tools/gap_p21_*.py` 资产清单

| 脚本 | 职责 | C/H/A4/A5 复用点 |
|---|---|---|
| `tools/gap_p21_map_gen.py` | GAPP21 场景图生成（graft 到 bench 骨架；[Header]/[Digest]/CellTags/触发器；GAGAP+CAFARM02 环置；TA17 5×5 waypoint；FogOfWar 补丁） | **C1** 战役变体基座：改 PLAYER/GAP_OWNER、注册战役、保留 CellTags/TA17/字母编码 |
| `tools/gap_p21_a3.py` | A3 全流程：槽位置换/选图/开局/BattleMonitor/`read_gap_state`/`inject_gap_counts`/before-after-after2/`--analyze` 离线对比 | **C4–C7 / H / A4**：`read_gap_state`（+0x12C/+0x130/+0x134 全图扫描，512-stride 索引）；`inject_gap_counts`（诊断捷径）；`--analyze` 判 kept/wiped |
| `tools/gap_p21_a1a2.py` | A1/A2 字节窗与日志验收（off/on/forced-off-mp） | 补丁态确认（C3 前置门） |
| `tools/gap_p21_select.py` | 地图浏览器行定位 `find_u0800_row` + 点选/使用地圖 | 战役选关 UI 若走浏览器式列表可改坐标复用 |
| `tools/gap_p21_mapbrowser.py` | 打开地图浏览器并翻页枚举 | C 导航排障 |
| `tools/gap_p21_maplist.py` | 枚举地图全表，定位目标行 | C 导航排障 |
| `tools/gap_p21_mapprobe.py` | 定位「打开地图浏览器」可点击部件 | C 导航排障 |
| `out/re_work/zcode_live/gap_p21/**` | 既有证据（json/png/map/inibak） | 对照基线（`bld_cells=0` 阻塞实证可引） |
| `bench_replay`（`tools/bench_replay.py`） | 启动/窗口/BattleMonitor/截图/RPM/WPM | 全流程底层 |
| `ra2forge/maplib.py` + `triggers.py` | 战役图生成/触发器 ABI（`make_trigger`/`ev_elapsed_time`/`act_reveal_waypoint`） | **C1**；注意 `act_reveal_waypoint` 恒写 P7='A'，多 waypoint 需按 `wp_letter` 改写字条 |

**harness 缺口（本卡不写码，留给执行方）**：战役模式导航（单人游戏 → 战役海报 → 关卡选择，与遭遇战浏览器不同）；`.SAV` 存读档自动化步骤；A5 摧毁指令（可用 UI 攻击/调试出售）。可将新脚本命名为 `tools/gap_p21_a3_campaign.py` / `gap_p21_a4.py` / `gap_p21_a5.py`，产物落 `out/re_work/re_sprint/R_p21_a3/**` 或 `out/re_work/zcode_live/gap_p21/**`。

---

## 6. 总判据矩阵（A3/A4/A5 × 方案）

| ID | 方案 C-战役 | 方案 H-诊断钩 | 必要证据 |
|---|---|---|---|
| **A3 缝仍在** | 真敌方 `CreateGap` 后 + PsychicReveal/TA17 开图 | 注入或真盖印后受控 `RevealArea2` | `gap_cells` before/after；逐格 kept/wiped |
| **A3 `+0x134` 不清 0** | 目标格开图后仍 `>0` | 同左 | `a3_*_cells_*.json` |
| **A3 对照** | `EnableGapProtection=0` → `GAP-WIPED` | 同左 | 对照 run JSON |
| **A4 存读档** | 同局 `.SAV` 读档后 `+0x134` 逐格一致 | 同左（诊断局档不外传） | 读档后扫描 JSON；`except.txt` |
| **A5 DestroyGap** | 摧毁缝建筑后计数回 0、无残留 | 同左 | 扫描 JSON |
| 附加 | `except.txt` 空；补丁字节窗仍 `90×6`（收尾复核） | 同左 + `gapDiagRevealCalls` | A2 脚本 + 日志 |

**PASS 定义**：A3（C-J1..J4 或 H 对应项）+ A4-J1..J2 + A5-J1..J3 全部成立；任一「只没崩」不判 PASS。

---

## 7. 风险（执行方必读）

| ID | 风险 | 要求 |
|---|---|---|
| R-1 | 混端 DESYNC（`+0x134` 进 `.SAV`） | 禁止联机混端；全端同构建同开关（沿用 P21 R-1） |
| R-2 | 存档语义不互通 | 补丁局存档标记/隔离；卸载后不读补丁档；诊断局存档不外传 |
| R-3 | 战役注册卫生 | 只加散装 `BATTLEMD*.INI` 自有条目 id（如 `RA2F1` 族），**不覆盖**官方条目名；收尾可删自有条目回滚 |
| R-4 | 触发器不触发的误判 | 战役图必须绑 `[CellTags]`；先用 TA11 文本做「触发器活着」探针再上开图动作 |
| R-5 | H 方案越权改 `RevealArea2` 内部 | 只调用；禁 Hook 改写/跳帧/限频（H-R1/H-R3） |
| R-6 | 注入捷径冒充真盖印 | `--inject` 只作 H 辅助；**C-J1 必须来自真 `CreateGap`** |
| R-7 | 卡片勘误沿用 | `or [ecx+0x12C],0x10` 实在 `0x0056829A`（非卡内 `0x568297`）；上下文窗 17B（非 21B）——只读引用，不改冻结卡 |

---

## 8. 交付回执（填完交回）

```
ZC-GAP-P21-A3 RESULT
- path: (C-campaign | H-diag-hook | both)
- build/md5(gamemd):
- EnableGapProtection: 0|1
- gapProtectInstalled / bytes @0x568273:
- map/battle id + sha256:
- A3 before gap_cells / gap_hist:
- A3 after  gap_cells / kept / wiped:
- A3 verdict: PATCH-WORKS | GAP-WIPED | NO-GAP-DETECTED
- A3 evidence: (json/png paths)
- A4 save/load kept 100%?: y/n  (+ evidence)
- A5 DestroyGap back to 0?: y/n  (+ evidence)
- A/B off-run verdict: (expect GAP-WIPED)
- except.txt: empty|path
- H only: gapDiagRevealCalls / approval ref
- rollback/cleanup: (battle entry, map, ini, saves)
```

---

## 9. 不在本卡

- P-2.2/P-2.3 字节面（`ZC-GAP-P223`）——行为面若同装 `installed=3` 可顺带记，但本卡判据只锁 P-2.1  
- 补丁安装器/`ra2render` 代码改动（含 H 方案实现）——H 需 Lead 审批后另卡落地  
- MP 握手字段扩展、SpySat 门控 P-2/P-3、H-20-B/C 绘制面  
- 台账/看板登记 —— 由 Lead 收口

---

*依据：RESULT_GAP_P21 [3] 阻塞定谳；R-GAP-PSY §2–§3（`+0x134` 语义 / PsychicReveal 链 / I-GAP-1 钳位）；R-SAV-GAP §1–§2（0x148 裸块入档、读档不重放 CreateGap）；ATLAS 红线（`RevealArea*`/`CreateGap/DestroyGap` 禁改写）；harness `tools/gap_p21_*.py`。*
