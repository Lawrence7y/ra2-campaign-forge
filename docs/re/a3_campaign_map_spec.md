# A3 战役图规格 · GAGAP/CAFARM02 最小图（方案 C）

> **卡号**：`ZC-GAP-P21-A3` / 任务 `R-A3-MAP` · **路径**：方案 C-战役（首选）  
> **依据**：`docs/re/landing_pack_gap_p21_a3.md` §2（方案 C）· §2.4（C-J1..J5）· §5（harness）  
> **交叉**：`out/re_work/zcode_live/gap_p21_a3/A3_PLAN.md`（ECHGAP 落地变体）· `docs/re/mix_hygiene_product.md`（BATTLEMD 散装）· `docs/re/sav_gap_cell_abi_deep_dive.md`（A4）  
> **写作用域**：本文 + `out/re_work/re_sprint/R_a3_map/**`；**禁写** `gamemd*` / 台账 / 看板。  
> **基线**：`gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · ImageBase `0x00400000`。

---

## 0. 一句话

在战役轨造一张**最小可判**图：真敌方 `GAGAP` 盖印 `Cell+0x134`，触发器 `TA17` 由游戏发起 `RevealArea2`，用 **C-J1..J5** 判「缝在 / 缝仍在 / 对照废缝 / 视觉回雾 / 禁没崩当成功」；注册只走**散装 `BATTLEMD*.INI`**；harness 全部映射到既有 `tools/gap_p21_*.py` + `gap_p21_a3_campaign.py`。

---

## 1. 目标与非目标

| | 内容 |
|---|---|
| **目标** | 规格化战役验收图（图面 / 触发 / CellTags / 注册 / 判据 / harness），供执行方一次生成、A/B 两档可跑、可回滚 |
| **非目标** | 不改补丁字节面（P-2.1 已落地）；不写安装器/`ra2render`；不实现方案 H 诊断钩；不做台账/看板登记 |
| **判据核心** | `CellClass+0x134 = GapsCoveringThisCell`（敌对缝引用计数）；`ReshroudCell 0x487690` 将 `ShroudCounter` 钳位于它 ⇒ **清 0 = 永久废缝**（不自愈） |

---

## 2. 最小图面（GAGAP 主 / CAFARM02 备）

### 2.1 坐标系（全规格统一）

| 概念 | 变换 | 出处 |
|---|---|---|
| 设计格 `(row, col)` | `0 ≤ row,col < W` | `ra2forge/maplib.py` CellGrid |
| 文件格 `(x, y)` | `x = W + col - row`，`y = row + 1` | 同上；平行四边形 `1≤y≤W, W+1≤x+y≤W+H+1` |
| 运行时 cells 索引 | `i = (y-1)*512 + (x-1)` | `MapClass::MaxCells=0x40000`，512-stride |
| `[Waypoints]` / `[CellTags]` 键 | **`y*1000+x`**（同一编码） | 战役图 `30105..30108` 实证 |
| 全图扫描 | **不得**只读前 `W*H` 项；须扫满 `0x40000` 指针数组 | `tools/gap_p21_a3.py::read_gap_state` 注释（旧口径漏扫） |

### 2.2 建筑选型

| 类型 | Rules 事实 | 角色 | 结论 |
|---|---|---|---|
| **`GAGAP`** | `GapGenerator=yes`，`GapRadiusInCells=10`，`SuperGapRadiusInCells=10`，`Power=-100`，Owner 含 Americans | **主**缝宿主 | **唯一可信真盖印源**（`CreateGap 0x6FB170`） |
| **`CAFARM02`** | **无** `GapGenerator` 标记（`rules_extracted.ini` 已核） | 隐形 gap 农场（mod 战役用法） | **备选/弃用**：默认不放；若要用，须先有 rules 覆写证明其参与 `CreateGap`，否则 `C-J1` 不成立 |
| 缝宿主老家 | `GACNST` + 足量 `GAPOWR` | 防瞬间战败 → `DestroyGap` 提前 | **必配**（GAGAP `Power=-100`，每台配 ≥3 座电站） |
| 玩家基地 | `NACNST/NAPOWR/NAWEAP` + 步兵/坦克 | 落在缝半径内 | **必配**；**不配雷达**（防开局全开 + `PlayerHouse+0x240` 门） |
| 第三方雷达屋（可选） | `NARADR` 满电 | P-2.2 `RevealArea3` 在线路径 | 与 A3 主判据解耦；A3PLAN/ECHGAP 已含 |

**交战约束**：`CreateGap` 对己方/盟友**跳过盖印**（`0x6FB2D6 call 0x4F9A50` / `jne`）⇒ 缝宿主必须与玩家**交战**（`allies=self`）。

### 2.3 最小图面清单

| 要素 | 值 | 说明 |
|---|---|---|
| 尺寸/剧场 | 90×90 `TEMPERATE`（方图、偶数边） | `MissionMap` 仅支持方图 |
| `[SpecialFlags] FogOfWar` | **`yes`** | maplib 硬编码 `no`，**必须补丁翻 yes**（黑幕/裂缝前提） |
| `[Basic] IgnoreGlobalAITriggers` | **`no`** | maplib 硬编码 `yes`；`yes` 可能连普通触发器一起静默（TA11 实测） |
| `[Basic] EndOfGame` | `yes`（单关验收图） | `NextScenario=` 空 |
| `[Basic] Player` | 本地玩家（ECHGAP：`Russians`） | 与缝宿主交战 |
| 玩家基地 | 1×建造厂 + 1×电站 + 1×战车厂 + 步兵/坦克 | 中心落在缝半径内 |
| 缝宿主 | **双 `GAGAP`**（半径 10，覆盖基地 ±8）+ 6×电站 + 建造厂 + 战车厂 + 步兵 | 双台冗余，单台断电不致 `gap_cells=0` |
| 缝宿主老家 | 与缝台分离（如 (18,18) vs 缝台近基地） | 防玩家/AI 速推触发 `DestroyGap` |
| waypoints | `0`=玩家起点，`1`=敌方老家，`2`=雷达方老家，`50..` 开图网格 | 缺 0/1 可能槽位异常/加载崩溃 |
| 开图网格 | 步距 4、半幅 12 ⇒ **7×7=49** 点（`50..98`） | 覆盖缝环；单点 TA17 半径 = `4 + [cell+0x11b]` |
| 参考产物 | `out/re_work/zcode_live/gap_p21_a3/ECHGAP.MAP` sha256 `fc49b149…` | `gap_p21_a3_gen.py` 已跑通 |

**图面不变量**（生成后自检，失败即拒收）：

1. `FogOfWar=yes`；`IgnoreGlobalAITriggers=no`；`EndOfGame=yes` 且 `NextScenario=` 空。  
2. 玩家基地文件格落在双 GAGAP 覆盖并集内（按 `GapRadiusInCells=10` 估）。  
3. `[Structures]` 含 ≥2 条 `GAGAP` 且缝宿主 `allies` 不含玩家。  
4. `[CellTags]` 非空，且覆盖全部开图目标格。  
5. `[Actions]` 中 TA17 的 P7 字母与 waypoint id 逐一对应（见 §3.3）。

---

## 3. 触发器（Trigger / Tag / Event / Action）

### 3.1 两条触发（探针 + 开图）

| # | tid / tag | 事件 | 动作 | 时点 | 目的 |
|---|---|---|---|---|---|
| **T1 探针** | `0000B031` / `0000B032` | `ev_elapsed_time(20)` = `13,0,20` | `act_text("…PROBE: trigger alive @20s")` = TA **11** | t=20s | **R-4**：先证明触发器活着（bench B-2 教训），再上开图 |
| **T2 开图** | `0000B021` / `0000B022` | `ev_elapsed_time(60)` = `13,0,60` | **N×TA17** RevealAroundWaypoint（N=网格点数） | t=60s | 由游戏发起 `RevealArea2 0x5678E0`（P-2.1 补丁点） |

行格式（`ra2forge/triggers.py`，与 WAE/官方图一致）：

```
[Triggers] ID=HOUSE,LINKED,NAME,DISABLED,EASY,NORMAL,HARD,REPEATING
[Tags]     TAGID=REPEATING,NAME,TRIGGERID
[Events]   ID=COUNT,(CODE,P1,P2)*
[Actions]  ID=COUNT,(CODE,P1..P6,P7)*
```

参考明文（ECHGAP）：

```
[Triggers]
0000B031=Russians,<none>,ECHGAP probe: trigger alive,0,1,1,1,0
0000B021=Russians,<none>,ECHGAP reveal (TA17 x49),0,1,1,1,0
[Tags]
0000B032=0,ECHGAP probe: trigger alive,0000B031
0000B022=0,ECHGAP reveal (TA17 x49),0000B021
[Events]
0000B031=1,13,0,20
0000B021=1,13,0,60
[Actions]
0000B031=1,11,0,ZC-GAP-P21-A3 PROBE: trigger alive @20s,0,0,0,0,A
0000B021=49,17,0,50,0,0,0,0,AY,17,0,51,0,0,0,0,AZ,…,17,0,98,0,0,0,0,CU
```

### 3.2 语义要点

| 项 | 事实 | 规格要求 |
|---|---|---|
| TA17 | `0x6E0FE0`：`[PlayerHouse+0x240]==0` 门 → 取 waypoint 格 → 半径 `4+[cell+0x11b]` → **双 call `RevealArea2`** | 玩家**无雷达** ⇒ `+0x240` 常 0，门不被静默 |
| 一次性 | `REPEATING=0` | 开图动作只放一次，避免 after 采样被二次开图污染 |
| 顺序 | 探针在前、开图在后 | t=20 / t=60 留 40s 观察窗 |
| `IgnoreGlobalAITriggers` | 战役口径 `yes`（maplib 默认）可能静默普通触发 | **本图强制 `no`**；若仍不触发，单独记录（不回退 `yes` 碰运气） |

### 3.3 waypoint 字母编码（TA17 P7）

```
w < 26  → chr(ord('A')+w)                 # 0↔A … 25↔Z
w ≥ 26  → r=w-26; chr('A'+r//26)+chr('A'+r%26)   # 26↔AA, 50↔AY, 121↔DR, 469↔RB
```

已实证对齐：`50↔AY` / `52↔BA` / `121↔DR` / `469↔RB`。

**陷阱**：`triggers.py::act_reveal_waypoint` 恒写 `P7='A'`（=waypoint 0）⇒ 直接用 helper 只会在 wp0 放一个小圈。**必须按 `wp_letter` 逐条改写 P7**（见 `gap_p21_map_gen.py` / `gap_p21_a3_gen.py` 的 actions 列表构造）。

---

## 4. CellTags（TagClass 实例化前提）

| 项 | 规定 |
|---|---|
| **为何必须** | 无 `[CellTags]` 时 **TagClass 不实例化**，`ElapsedTime` 事件**永不求值**（RESULT_GAP_P21 B-2：TA11/TA17 全无反应） |
| 键编码 | **`y*1000+x`**（与 `[Waypoints]` 同；战役图 `30105..30108` 同行 4 格印证） |
| 值 | 对应 `tag_id`（8 位 hex，如 `0000B022`） |
| T1 绑定 | 探针 tag 绑 **1..4** 个「必然存在的格」（如基地格） |
| T2 绑定 | 开图 tag 绑 **全部 49 个开图网格格**（保证任一路径实例化 TagClass 即可） |
| 生成方式 | `gap_p21_a3_gen.py::insert_cell_tags` 风格：在 `[Actions]` 后插入 `[CellTags]`；键用**文件格** `y*1000+x`（先 `to_cell(row,col)` 再编码，**不要**直接用 row/col） |
| 换算注意 | `to_cell` 返回 `(x,y)`；编码是 `y*1000+x`。ECHGAP 实测基地格键 `46090`（探针） |

自检：`[CellTags]` 行数 ≥ 1（探针）+ N（开图网格）；每个 tag_id 必须在 `[Tags]` 出现；每个触发 id 必须在 `[Triggers]`/`[Events]`/`[Actions]` 齐全。

---

## 5. BATTLEMD 散装注册

### 5.1 机制（只认散装）

| 地址 | 行为 | 产品含义 |
|---|---|---|
| `0x52CBA0` | `push "BATTLEMD*.INI"` → **`FindFirstFileA`（FS-only）** | **`BATTLEMD98.INI` 必须散装**在 `gamemd.exe` 同级；MIX 内**永不加载** |
| `0x52CCCD` | 回退 `BATTLEMD.INI`（`CCFileClass`） | **仅当**目录里一个散装 `BATTLEMD*.INI` 都没有时 |
| `0x46CE10` | `[Battles]` 按**条目名**归并（`_stricmp`），同名后装载者覆写字段 | 追加自有 ID；**禁止**写官方 `1..14` / `ALL\d+` / `SOV\d+` |

优先级一句话：**散装 > langmd > language > expandmd99…00 > ra2md**；99 会压过 98。

### 5.2 两种注册形态（本规格两案并存，执行时二选一）

| 案 | 做法 | 优点 | 风险 | 出处 |
|---|---|---|---|---|
| **C2-a 追加条目** | 散装 `BATTLEMD98.INI` 追加自有 id（如 `16=GAPA3`）+ `[GAPA3] Scenario=ECHGAP.MAP` | 不动官方条目；海报屏多一条 | 新条目可能触发分页/DebugOnly 过滤；导航坐标需重校 | landing pack C2 |
| **C2-b 改 Scenario 指向**（A3PLAN 现行） | 只改散装 `BATTLEMD.INI` 的 `[SOV1] Scenario=` 一行 → `ECHGAP.MAP` | **不新增条目**，海报/导航坐标不变 | 动了官方条目字段（须备份 + byte-identical 还原） | `A3_PLAN.md` §1 |

**默认推荐**：导航未校准前用 **C2-b**（坐标稳定）；导航 `--calib-nav` 通过后可迁 **C2-a**（更干净）。

### 5.3 散装卫生（无论哪案）

1. **只加散装** `BATTLEMD*.INI`；`expandmd98.mix` **仅资源/地图，0 个 INI**。  
2. **不覆盖**官方 `BATTLEMD.INI` 的 `[Battles] 1..14` 与条目名 `ALL*`/`SOV*`。  
3. 改前备份（`instr/BATTLEMD.INI.pre_a3` 或 `.ra2forge.bak`），收尾 **sha256 + byte-identical** 对拍。  
4. 跨包 **ID 唯一**；同 ID 跨文件「后装载者赢」（枚举序未定，U-MIXP-1）。  
5. 回滚：还原备份；自有条目可整文件删除；**禁止**「备份后删官方 `BATTLEMD.INI` 指望 MIX 回退」——正确迁移是 `extracted/found_battlemd.ini` 恢复（FORGE-2）。
   > 【W3 勘误 · Forge P-6】改前：假定 MIX 无官方件；改后：理由订正为嵌套 MIX 内确有官方件（sha256 `7e40691a…`），但回退机制真机未闭环（U-FORGE2-3），且 `extracted/all_inis/*.ini` 首行写坏，恢复唯一指定 `extracted/found_battlemd.ini`；依据：`battlemd_authority.py` 实测；分级：[实证]

**注册前后必留证据**：`BATTLEMD*` 清单 diff（文件名 / 大小 / sha256 / `[Battles]` 行）。

---

## 6. 判据 C-J1..J5（逻辑计数为主，截图像素为辅）

| ID | 判据 | 量化 | 证据 | 失败含义 |
|---|---|---|---|---|
| **C-J1 缝在** | before：`gap_cells > 0`，且目标格 `+0x134 ≥ 1` | `gap_hist`；`bld_cells>0` 反证 B-1 已绕 | `a3_before_*.json` | 真 `CreateGap` 没建立（供电/交战/建筑未实例化） |
| **C-J2 缝仍在** | after/after2：目标格 `+0x134` **不清 0**（逐格 kept ≥ 90% 量级同 before；开图半径内抽样全部 `>0`） | `before_cells_kept_gap` / `before_cells_wiped` | `a3_after*_*.json` | P-2.1 未生效 = `GAP-WIPED` |
| **C-J3 对照** | 同图关补丁（`EnableGapProtection=0`）：被开图格 `+0x134` 归 0 / `gap_cells` 显著下降 | `GAP-WIPED` verdict | `run_*_off.json` | 对照不复现 bug ⇒ 场景/开图路径无效，A3 不可判 |
| **C-J4 视觉** | 扫描退去后该格回到**黑雾/缝层**（非永久透亮）；before/after2 截图 diff | PNG md5 + 像素差 | `shots/*.png` | 仅辅助；不单独定 PASS/FAIL |
| **C-J5 禁「没崩当成功」** | 无 `except.txt` **且** C-J2 必须成立 | — | 卡规 | 只没崩 ≠ PASS |

**PASS 定义**：C-J1..J4 全成立（C-J4 辅助确认）且 C-J5 满足；任一「只没崩」不判 PASS。  
**verdict 词表**：`PATCH-WORKS` | `GAP-WIPED` | `NO-GAP-DETECTED`。

**注入红线**：`--inject` / `inject_gap_counts` 只作方案 H 辅助；**C-J1 必须来自真 `CreateGap`**（R-6）。

---

## 7. 同图纳入 A4 / A5（依赖 A3 场景）

| 面 | 步骤 | 判据 |
|---|---|---|
| **A4 存读档** | A3 通过后：`.SAV` → 读档 → 再扫 | **A4-J1** 逐格 `+0x134` 与存档前一致（kept=100%）；**A4-J2** `except.txt` 空、`gap_cells` 同量级 |
| **A5 DestroyGap** | 摧毁缝建筑 / 断电 / 变卖（`GeneratingGap` 翻假）→ 再扫 | **A5-J1** 原覆盖格回 0 或与 decremented 一致、无悬空计数；**A5-J2** 可重新被 `ShroudCounter` 遮蔽；**A5-J3** `except.txt` 空 |

机制：`+0x134` 在 `CellClass` **0x148 裸块整块入档**（`GetSize=0x148`，`0x487E70`），读档**不**重放 `CreateGap` ⇒ 存多少读出多少。`DestroyGap 0x6FB470` 对覆盖格 `dec`（`0x6FB5EE..0x6FB5FD`）。

---

## 8. harness 映射

| 步 | 动作 | 脚本 / API | 产物 |
|---|---|---|---|
| **C1** 生成图 | `gap_p21_a3_gen.py`（战役变体基座）或 graft `gap_p21_map_gen.py` | `ra2forge/maplib.py` + `triggers.py` | `ECHGAP.MAP` + `*.ini.txt` + `*.mapreport.json`（sha256） |
| **C2** 注册 | 散装 `BATTLEMD*.INI` 追加 / 改 `Scenario=` | 手写 INI + 清单 diff | `instr/` 备份 + diff |
| **C3** 补丁态门 | `EnableGapProtection=1`（对照 0） | `gap_p21_a1a2.py`（字节窗 90×6）+ `gap_p21_a3_campaign.py::set_gap_key` | 启动日志 `GapProtection=on` |
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0
| **C4** 进局 | 战役导航 → 选关 → frame>200 | `gap_p21_a3_campaign.py::campaign_nav` / `bench_replay.BattleMonitor` | 截图 + frame |
| **C5** before | 全图扫 `+0x12C/+0x130/+0x134` | `read_gap_state`（512-stride 全 `0x40000`） | `cells_before_*.json` |
| **C6** 开图 | 等 T2 / 手动 PsychicReveal + `--settle` | `gap_p21_a3.py --settle/--post` | 开图事件（`mapped_cells` 上升） |
| **C7** after/after2 | 再扫 + 对比 | `read_gap_state` + `gap_p21_a3.py --analyze` | `cells_after*.json` + `a3_analyze_*.json` |
| **C8** A4 | 存读档 | `gap_p21_a3_campaign.py::save_load_cycle` | `cells_afterload_*.json` |
| **C9** A5 | 摧毁/断电/长时抽样 | 同上 + UI 攻击/调试出售 | `a5_*` |
| **C10** 对照 | `EnableGapProtection=0` 重跑 C4–C7 | `--profile off` | `run_*_off.json`（期望 `GAP-WIPED`） |
| 选图/导航排障 | 地图浏览器 | `gap_p21_select.py` / `mapbrowser.py` / `maplist.py` / `mapprobe.py` | 截图 |
| 回滚 | byte-identical 还原 | `gap_p21_a3_campaign.py --restore` | `instr/*.pre_a3` 对拍 |

**扫描口径**（`read_gap_state`）：

- `+0x124` Occ / `+0x128` AltOcc（`bit0x80` ⇒ `bld_cells`）/ `+0x12C` CopyFlags（`bit0x10` ⇒ `mapped_cells`）/ `+0x130` ShroudCounter / `+0x134` GapsCovering。  
- 战役版 `gap_details` 含 `{i,x,y,g,s,f}`；**注意** `tools/gap_p21_a3.py` 老版 `gap_details` 无 `x/y`，其 `--analyze` 用 `(x,y)` 键会漏/炸——对比请用战役版字段或先归一到 `i`。

**harness 缺口（本卡不写码，留给执行方）**：战役模式导航自动化（单人→战役海报→关卡）；`.SAV` 存读档 UI 坐标（`--calib-pause`）；A5 摧毁指令。建议新脚本名 `tools/gap_p21_a3_campaign.py`（已有）/ `gap_p21_a4.py` / `gap_p21_a5.py`，产物落 `out/re_work/re_sprint/R_a3_map/**` 或 `out/re_work/zcode_live/gap_p21*/**`。

---

## 9. 执行步骤（方案 C 全流程）

| 步 | 动作 | 记录 |
|---|---|---|
| C1 | 生成/改 `ECHGAP.MAP`（或 graft 到 `ECH01` 骨架） | 图明文 + sha256 |
| C2 | 注册战役条目（散装 BATTLEMD；案 C2-a 或 C2-b） | 注册前后清单 diff |
| C3 | `ra2youli/ra2render.ini` 显式 `EnableGapProtection=1`（对照 0） | 启动日志 |
| C4 | 进战役 → 选关 → frame>200 | 截图 + frame |
| C5 | before 全图扫 | `gap_cells>0`、`gap_hist` |
| C6 | 等触发开图 + reshroud 等待 | 开图事件证据 |
| C7 | after / after2 扫 | 对比 JSON |
| C8 | A4 存读档再扫 | §7 |
| C9 | A5 摧毁/断电再扫 | §7 |
| C10 | 对照组 off 重跑 C4–C7 | 期望 `GAP-WIPED` |

**插桩/还原契约**：`BATTLEMD*` / `ra2render.ini` / `ECHGAP.MAP` 改前备份、收尾 byte-identical；`gamemd.exe` 跑前跑后 sha256=基线；每档 run 末尾强杀游戏。

---

## 10. 风险

| ID | 风险 | 要求 |
|---|---|---|
| R-1 | 混端 DESYNC（`+0x134` 进 `.SAV`） | 禁止联机混端；全端同构建同开关 |
| R-2 | 存档语义不互通 | 补丁档标记/隔离；卸载后不读补丁档 |
| R-3 | 战役注册卫生 | 只加散装自有 ID；不覆盖官方条目名；可回滚 |
| R-4 | 触发器不触发误判 | **必须绑 `[CellTags]`**；先 TA11 探针再上 TA17 |
| R-5 | 注入冒充真盖印 | C-J1 必须真 `CreateGap` |
| R-6 | CAFARM02 误当缝源 | 无 `GapGenerator` 标记则不进主路径 |
| R-7 | 断电致 `DestroyGap` | 每台 GAGAP 配足电站；before 扫 `gap_cells=0` 即停 |
| R-8 | 卡片勘误 | `or [ecx+0x12C],0x10` 在 `0x0056829A`（非 `0x568297`）；上下文窗 17B——只读引用 |

---

## 11. 交付回执（填完交回）

```
ZC-GAP-P21-A3 RESULT
- path: (C-campaign | H-diag-hook | both)
- build/md5(gamemd):
- EnableGapProtection: 0|1
- gapProtectInstalled / bytes @0x568273:
- map/battle id + sha256:
- register form: (C2-a append | C2-b redirect)
- A3 before gap_cells / gap_hist:
- A3 after  gap_cells / kept / wiped:
- A3 verdict: PATCH-WORKS | GAP-WIPED | NO-GAP-DETECTED
- A3 evidence: (json/png paths)
- A4 save/load kept 100%?: y/n  (+ evidence)
- A5 DestroyGap back to 0?: y/n  (+ evidence)
- A/B off-run verdict: (expect GAP-WIPED)
- except.txt: empty|path
- rollback/cleanup: (battle entry, map, ini, saves)
```

---

*依据：landing_pack_gap_p21_a3.md 方案 C；RESULT_GAP_P21 B-1/B-2/B-3；R-GAP-PSY（`+0x134` / PsychicReveal / I-GAP-1）；R-SAV-GAP（0x148 入档）；mix_hygiene_product（BATTLEMD 散装）；harness `tools/gap_p21_*.py` + `gap_p21_a3_campaign.py`；参考产物 `out/re_work/zcode_live/gap_p21_a3/ECHGAP.*`。*
