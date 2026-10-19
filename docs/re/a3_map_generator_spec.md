# A3 地图生成器规格 · `a3_map_gen`（可实现规格 + 伪代码）

> **卡号**：`R-A3-GENSPEC` · 依据 `docs/re/a3_campaign_map_spec.md` + `ra2forge/maplib.py`（只读）  
> **交叉**：`out/re_work/zcode_live/gap_p21_a3/gap_p21_a3_gen.py`（已跑通基座）· `out/re_work/re_sprint/R_a3_map/**`（图面/注册清单）· `docs/re/mix_hygiene_product.md`（BATTLEMD 散装）  
> **写作用域**：本文 + `out/re_work/re_sprint/R_a3_genspec/**`；**禁写** `ra2forge/**` 源 / 台账 / 看板  
> **性质**：本文是**规格**，不含生产代码；伪代码仅供实现方对照。实现建议落 `tools/a3_map_gen.py` 或 `out/re_work/re_sprint/R_a3_genspec/` 试验脚本。

---

## 0. 一句话

把「A3 战役验收图」收敛成**确定性生成器**：吃一份 JSON 设计参数 + CLI 变体开关，吐出 `ECHGAP.MAP`（GBK）、`*.mapreport.json`、`*.ini.txt` 与 `BATTLEMD` 散装片段；生成末尾强制跑**校验器**（CellTags `y*1000+x`、`wp_letter`、图面不变量），校验失败即拒收；对外只暴露 gap_p21 harness 消费的**稳定产物契约**。

---

## 1. 目标与非目标

| | 内容 |
|---|---|
| **目标** | 输入参数化、输出稳定可 sha 对拍、校验前置；一次生成同时产出图 + 注册片段 + mapreport；C2-a/C2-b 两案片段都可吐 |
| **非目标** | 不写生产安装器；不改 `ra2forge/maplib.py`；不实现 harness runner（`gap_p21_a3_campaign.py` 既有）；不做 A4/A5 测量；不动 `gamemd.exe` |
| **基座** | `ra2forge.maplib.MissionMap` + `ra2forge.triggers`；后处理补丁（maplib 硬编码两处）+ CellTags 注入 |
| **金样** | `out/re_work/zcode_live/gap_p21_a3/ECHGAP.MAP` sha256 `fc49b149b4f23dae18313eaf8ce22082b34533f90b7fd14a425d50592944dc51`（8934 B，variant=full） |

---

## 2. 输入

### 2.1 设计 JSON（`a3_map_design.json`）

生成器**唯一**图面来源。CLI 开关只做变体/输出路径覆盖，不改语义字段。

```jsonc
{
  "schema": "a3-map-design/1",
  "map_name": "ECHGAP 裂缝验收",
  "map_file": "ECHGAP.MAP",
  "size": 90,                         // 方图、偶数；MissionMap 仅支持 width==height
  "theater": "TEMPERATE",
  "player_house": "Russians",
  "gap_owner": "Americans",
  "spy_owner": "Germans",             // 雷达方；nr 变体自动去 NARADR
  "bases": {
    "player":   { "row": 45, "col": 45 },
    "enemy":    { "row": 18, "col": 18 },
    "spy":      { "row": 72, "col": 72 }
  },
  "gap": {
    "positions": [ {"row": 41, "col": 47}, {"row": 49, "col": 43} ],
    "radius_cells": 10,               // Rules GapRadiusInCells；用于覆盖自检，不写进图
    "min_generators": 2,
    "power_per_generator": 3          // 每台 GAGAP 配 ≥3 座电站（Power=-100）
  },
  "reveal_grid": { "step": 4, "half": 12, "wp_id0": 50 },  // 7×7=49 点，id 50..98
  "triggers": {
    "probe":  { "tid": "0000B031", "tag": "0000B032", "at_s": 20,
                "text": "ZC-GAP-P21-A3 PROBE: trigger alive @20s" },
    "reveal": { "tid": "0000B021", "tag": "0000B022", "at_s": 60,
                "action": 17, "p1": 0 }   // TA17 RevealAroundWaypoint
  },
  "battlemd": {
    "form": "C2-b",                   // "C2-a" | "C2-b"
    "entry_id": "GAPA3",              // C2-a：自有条目名；C2-b 忽略
    "index": 16,                      // C2-a：[Battles] 索引 ≥15
    "cd": 2,
    "description": "ZC-GAP-P21-A3 裂缝验收（单关）",
    "redirect_section": "SOV1",       // C2-b：改哪一节的 Scenario=
    "original_scenario": "ECH01.MAP"  // C2-b：备份/还原证据用
  },
  "water_rect": [8, 8, 13, 13]        // 可选；IsoMapPack5 非空
}
```

**JSON 不变量（加载时校验，违反即拒）**：

1. `size` 偶数且 `40 ≤ size ≤ 100`（MissionMap 方图；过大超 MaxCells 语义）。
2. `gap.positions.length ≥ gap.min_generators`（≥2）。
3. 玩家基地文件格落在**全部** GAGAP 覆盖并集内（Chebyshev 距离 ≤ `radius_cells`，按文件格近似）。
4. `reveal_grid` 产出点数 N = `((2*half)/step + 1)^2`，且 `wp_id0 + N - 1` 可被 `wp_letter` 编码（无上限，但 mapreport 要记 id 区间）。
5. `triggers.probe.at_s < triggers.reveal.at_s`；两者 `tid`/`tag` 8 位 hex 且互不重复。
6. `battlemd.form=C2-a` ⇒ `index ≥ 15` 且 `entry_id` 匹配 `^[A-Za-z][A-Za-z0-9_]{0,15}$`，**禁止** `ALL\d+`/`SOV\d+`/纯数字官方位。

### 2.2 CLI

```
python a3_map_gen.py --design a3_map_design.json
    [--variant full|nr]          # 默认 full；nr=去第三方雷达（对照档 P-2.1 归因）
    [--battlemd-form C2-a|C2-b]  # 覆盖 JSON battlemd.form
    [--out-dir DIR]              # 默认 out/re_work/re_sprint/R_a3_genspec/build/
    [--emit battlemd|all|none]   # 默认 all
    [--check-only]               # 只跑校验器（对已生成产物）
    [--json-report]              # mapreport 路径打到 stdout（harness 解析）
    [--seed N]                   # 仅影响 scatter_trees 等装饰；核心图面必须确定性
```

退出码：`0` 通过 · `2` 校验失败 · `3` 输入非法 · `4` IO/编码错误。**校验失败不得留下 `.MAP` 定稿**（写 `.MAP.rej` 或先写 temp 再 rename）。

---

## 3. 输出产物契约

全部落 `--out-dir`；文件名除 `map_file` 外由 map 文件名派生。

| 产物 | 格式 | 用途 |
|---|---|---|
| `ECHGAP.MAP` | **GBK** 字节，行尾 **CRLF** | 战役图本体；部署由 harness `--install` 做 |
| `ECHGAP.ini.txt` | UTF-8 明文（同内容） | 人读/diff |
| `ECHGAP.mapreport.json` | UTF-8 JSON | sha256 / 段计数 / 关键格 / 目标格清单；harness 对拍 |
| `ECHGAP.battlemd.C2-a.ini.txt` | UTF-8 INI 片段 | C2-a 追加条目（散装 `BATTLEMD98.INI`） |
| `ECHGAP.battlemd.C2-b.patch.txt` | UTF-8 补丁说明 + 单行 | C2-b 改 `[SOV1] Scenario=` |
| `ECHGAP.check.json` | 校验器逐条结果 | 拒收证据 |

### 3.1 mapreport 字段（稳定，harness 只认这些）

```jsonc
{
  "map": "ECHGAP.MAP", "variant": "full|nr",
  "bytes": 8934, "sha256": "…",
  "size": [90, 90], "fog_of_war": "yes",
  "player": "Russians", "gap_owner": "Americans", "spysat_owner": "Germans",
  "base_rowcol": [45, 45], "base_file_cell": [90, 46],
  "gap_pos_rowcol": [[41,47],[49,43]],
  "gap_pos_file_cells": [[42,96],[50,84]],
  "gap_radius_cells": 10,
  "grid": { "step": 4, "half": 12, "n": 49, "wp_ids": [50, 98],
            "file_cells": [[90,34], …] },
  "triggers": { "probe": {"tid":"0000B031","tag":"0000B032"},
                "reveal": {"tid":"0000B021","tag":"0000B022","n_actions": 49} },
  "celltags": { "n": 50, "probe_keys": [46090], "reveal_key0": 34090 },
  "sections": { "Structures": 21, "CellTags": 50, "…": 0 },
  "battlemd": { "form": "C2-b", "scenario_line": "Scenario=ECHGAP.MAP" }
}
```

### 3.2 BATTLEMD 片段

**C2-a**（散装 `BATTLEMD98.INI` 追加；官方 `BATTLEMD.INI` 零改动）：

```ini
; a3_map_gen emit · form=C2-a · 只允许散装部署（FindFirstFileA "BATTLEMD*.INI"）
[Battles]
16=GAPA3

[GAPA3]
CD=2
Scenario=ECHGAP.MAP
FinalMovie=
Description=ZC-GAP-P21-A3 裂缝验收（单关）
```

**C2-b**（只改一行；须配套 `instr/BATTLEMD.INI.pre_a3` 备份）：

```ini
; a3_map_gen emit · form=C2-b · 只改 [SOV1] Scenario= 一行
; backup: instr/BATTLEMD.INI.pre_a3
; restore: byte-identical 对拍后写回
[SOV1]
Scenario=ECHGAP.MAP    ; 原 ECH01.MAP
```

**红线（写进片段头注释，校验器也查）**：不占 `[Battles] 1..14`；不占 `ALL\d+`/`SOV\d+` 条目名；`expandmd98.mix` **0 个 INI**；跨包 ID 唯一。

---

## 4. 生成管线（阶段 + 伪代码）

### 4.0 maplib 能力边界（实现方必读）

| 能力 | `maplib` 现状 | 生成器动作 |
|---|---|---|
| 坐标 `to_cell(row,col)→(x,y)` | `x=W+col-row`, `y=row+1` | **只用**它；禁止手写换算 |
| `[Waypoints]` 编码 | `y*1000+x` | CellTags 复用同一编码 |
| `[SpecialFlags] FogOfWar` | **硬编码 `no`** | 生成后**必补丁** `yes` |
| `[Basic] IgnoreGlobalAITriggers` | **硬编码 `yes`** | 生成后**必补丁** `no` |
| `[Basic] EndOfGame` | `end_of_game` 标志 | 设 `True`；`next_scenario=""` |
| `[CellTags]` | **不支持** | 后处理插入（§4.4） |
| TA17 P7 | `act_reveal_waypoint` 恒写 `'A'` | **禁止**直接用 helper 出动作列表；按 `wp_letter` 手构 action 元组 |
| 行尾 | `to_ini_text` 用 `\n` | 写盘前统一 `\r\n`；编码 **GBK** |

### 4.1 总流程

```
load design JSON → validate_schema
build MissionMap (placements / waypoints / triggers)
  → text = m.to_ini_text()
  → text = patch_specialflags(text)      # FogOfWar=yes
  → text = patch_basic(text)             # IgnoreGlobalAITriggers=no, EndOfGame=yes
  → text = insert_cell_tags(text, …)     # [CellTags] after [Actions]
  → text = crlf(text)
  → bytes = text.encode("gbk")
  → write temp → run_checker → on pass: rename to ECHGAP.MAP; on fail: .rej + exit 2
  → emit mapreport / battlemd fragments / check.json
```

### 4.2 图面装配（对齐 a3_campaign_map_spec §2.3）

```
function build_map(design, variant) -> MissionMap:
    m = MissionMap(design.map_name, width=size, height=size, theater=theater)
    m.player_house = design.player_house
    m.next_scenario = ""
    m.end_of_game = True
    m.basic.briefing = design.briefing  # 可选

    # 房屋：player / gap_owner / spy_owner 三家其余默认；allies 必须自含（互敌）
    for h in STANDARD_HOUSES:
        if h == player:  house_configs += {player: True, credits: 20000, iq: 5, allies: h}
        elif h in (gap_owner, spy_owner): house_configs += {iq: 1, credits: 20000, allies: h}
        else: house_configs += defaults

    # 玩家基地：建造厂+电站+战车厂+步兵/坦克；**无雷达**
    add_structure(player, "NACNST", base)
    add_structure(player, "NAPOWR", base-4row)
    add_structure(player, "NAWEAP", base+4row)
    add_infantry ×5, add_unit(MTNK) ×2

    # 缝宿主老家（远离缝台，防速推 DestroyGap）
    for i in 0..5: add_structure(gap_owner, "GAPOWR", enemy + (i,0))
    add_structure(gap_owner, "GACNST", enemy + (0,4))
    add_structure(gap_owner, "GAWEAP", enemy + (3,4))
    # 缝台：≥2 GAGAP（覆盖基地）；电站数 ≥ min_generators * power_per_generator
    for (gr,gc) in design.gap.positions:
        add_structure(gap_owner, "GAGAP", gr, gc)

    # 雷达方（variant=nr 则跳过 NARADR）
    4×GAPOWR + GACNST + (variant!=nr ? NARADR : nothing) + GI×4

    optional water_rect

    # waypoints: 0=player, 1=enemy, 2=spy, 50..=reveal grid
    add_waypoint(0, player_base); add_waypoint(1, enemy_base); add_waypoint(2, spy_base)
    for i, cell in enumerate(reveal_grid_cells(design)):
        add_waypoint(wp_id0 + i, cell)

    # T1 探针 + T2 开图
    m.add_trigger(make_trigger(tid=probe.tid, tag_id=probe.tag, house=player,
        name="ECHGAP probe: trigger alive",
        events=[ev_elapsed_time(probe.at_s)],
        actions=[act_text(probe.text)]))

    actions = [ (17, (0, w, 0, 0, 0, 0, wp_letter(w)))   # ← P7 必须逐条 wp_letter
                for w in range(wp_id0, wp_id0 + N) ]
    m.add_trigger(make_trigger(tid=reveal.tid, tag_id=reveal.tag, house=player,
        name=f"ECHGAP reveal (TA17 x{N})",
        events=[ev_elapsed_time(reveal.at_s)],
        actions=actions))
    return m
```

### 4.3 后处理补丁

```
patch_specialflags(text):
    # [SpecialFlags] 段内 FogOfWar=no → yes；找不到行 = 硬失败
patch_basic(text):
    # IgnoreGlobalAITriggers=yes → no
    # EndOfGame 确保存在且 =yes；NextScenario 必为空串
```

### 4.4 CellTags 注入（TagClass 实例化前提；缺一不可）

```
function celltag_entries(m, design) -> list[(key, tag_id)]:
    g = m.grid
    # 探针：绑「必然存在」的格（基地建造厂格）；规格允许 1..4 个
    (x,y) = g.to_cell(*design.bases.player)
    emit (y*1000 + x, probe.tag)

    # 开图：绑全部 N 个网格格（任一路径实例化 TagClass 即可）
    for (row,col) in reveal_grid_cells(design):
        (x,y) = g.to_cell(row, col)
        emit (y*1000 + x, reveal.tag)

function insert_cell_tags(text, entries):
    # 在 [Actions] 段之后插入；键排序稳定（按 key 升序）以保证 sha 确定
    section = "[CellTags]\n" + join(f"{k}={tag}" for k,tag in sorted(entries))
    # 若 [Actions] 后已有段则插在该段前；无 [Actions] = 硬失败
```

**编码口诀（校验器同款）**：`to_cell` 返回 `(x, y)` → 键 **`y*1000+x`**。ECHGAP 实测探针键 `46090`。**不要**用 `row*1000+col`（旧陷阱）。

### 4.5 `wp_letter`（TA17 P7）

```
function wp_letter(w: int) -> str:
    if w < 26: return chr(ord('A') + w)                 # 0↔A … 25↔Z
    r = w - 26
    return chr(ord('A') + r//26) + chr(ord('A') + r%26) # 26↔AA, 50↔AY, 121↔DR, 469↔RB
```

已实证锚点：`50↔AY` · `52↔BA` · `121↔DR` · `469↔RB`。生成器自检必须覆盖这 4 组。

**陷阱**：`triggers.act_reveal_waypoint(w)` 恒 `P7='A'`（= wp0）。生成器**不得**用它拼 T2 动作；必须按 §4.2 手构 `(17, (0, w, 0,0,0,0, wp_letter(w)))`。

---

## 5. 校验器（`check_map` / `EmitCheck`）

生成末尾与 `--check-only` 共用同一函数；产物 `ECHGAP.check.json` 记录每条。

| ID | 检查 | 失败 |
|---|---|---|
| **V01** | `[SpecialFlags] FogOfWar=yes` | 拒收 |
| **V02** | `[Basic] IgnoreGlobalAITriggers=no` 且 `EndOfGame=yes` 且 `NextScenario=` 空 | 拒收 |
| **V03** | `[Structures]` 中 `GAGAP` 条数 ≥ `min_generators` | 拒收 |
| **V04** | 缝宿主 `Allies=` **不含**玩家；玩家基地文件格对每台 GAGAP Chebyshev ≤ radius（并集覆盖） | 拒收 |
| **V05** | 玩家基地结构中**无雷达类**（`*RADR`/`NARADR`/`GARADR`） | 拒收 |
| **V06** | `[Waypoints]` 含 0/1（及 2 若配置 spy）；网格 id 连续 `wp_id0..wp_id0+N-1` | 拒收 |
| **V07** | **CellTags 键**：每键满足 `key == y*1000+x` 且 `(x,y)` 落在平行四边形 `1≤y≤W, W+1≤x+y≤W+H+1`；且反查 `row=y-1, col=x-W+row` 在 `[0,W)` | 拒收 |
| **V08** | CellTags 值集合 ⊆ `[Tags]` 的 tag_id；行数 ≥ 1+N；探针键 ∈ 基地格邻域 | 拒收 |
| **V09** | 每个 tid 在 `[Triggers]`/`[Events]`/`[Actions]`/`[Tags]` 四处齐全 | 拒收 |
| **V10** | T2 的每条 action：`code=17`，`P2=waypoint_id`，`P7 == wp_letter(P2)`，且 P7 **≠** 恒 `'A'`（N>1 时） | 拒收 |
| **V11** | `wp_letter` 自检锚点 `50↔AY/52↔BA/121↔DR/469↔RB` | 拒收 |
| **V12** | 文件编码可 GBK 解码且无 `?` 替换残留；行尾 CRLF；`[Preview]` 为首段 | 拒收 |
| **V13** | mapreport.sha256 == 实际文件 sha256；`sections.CellTags == celltags.n` | 拒收 |
| **V14** | BATTLEMD 片段：C2-a 索引 ≥15、条目名合法、**未**占 `1..14`/`ALL*`/`SOV*`；C2-b 仅 `Scenario=` 一行语义 | 拒收 |
| **V15** | 变体 `nr` ⇒ `[Structures]` 无任何雷达屋；`full` ⇒ 恰好第三方雷达方 1 座带电雷达 | 警告/拒收可配 |

伪代码：

```
function check_map(ini_text, bytes, design, variant) -> CheckReport:
    secs = parse_ini_sections(ini_text)
    fail_if fog_of_war != "yes"                         # V01
    fail_if basic.IgnoreGlobalAITriggers != "no"        # V02
    …
    for (k, tag) in secs.CellTags:
        y, x = divmod(k, 1000)    # 注意：键=y*1000+x ⇒ y=k//1000, x=k%1000
        fail_if not in_parallelogram(x, y, W)           # V07
        fail_if tag not in secs.Tags.keys()             # V08
    for act in secs.Actions[tid_reveal].actions:
        w = act.P2
        fail_if act.code != 17 or act.P7 != wp_letter(w)  # V10
    …
    return report   # 每条 {id, pass, detail}
```

**拒收语义**：任一 V 失败 → 进程退出码 2，`.MAP` 不落定稿名，mapreport 不写或标记 `"rejected": true`。

---

## 6. 与 gap_p21 harness 接口

生成器**不**启动游戏；只保证 harness 取用的产物与字段稳定。

### 6.1 消费点

| harness 步 | 读取 | 约定 |
|---|---|---|
| **C1 生成** | 调本生成器或复用产物 | `--json-report` stdout 一行 mapreport 路径 |
| **C2 注册** | `*.battlemd.*.ini.txt` | 复制为散装 `BATTLEMD98.INI` 条目（C2-a）或按 patch 改一行（C2-b）；**改前备份** `instr/BATTLEMD.INI.pre_a3` |
| **C3 补丁态门** | 不消费 | `EnableGapProtection` 由 `gap_p21_a3_campaign.py::set_gap_key` |
| **C4–C7 测量** | `mapreport.grid.file_cells` / `gap_pos_file_cells` / `base_file_cell` | 对齐 `read_gap_state` 目标格；`gap_details` 归一到 `i=(y-1)*512+(x-1)` |
| **对照档** | `--variant nr` 产物 `ECHGAP_NR.MAP` | C-J3 归因干净 |
| **回滚** | mapreport.sha256 + battlemd 备份 | `--restore` 后 byte-identical 对拍 |

### 6.2 路径约定

| 内容 | 路径 |
|---|---|
| 生成器规格 | `docs/re/a3_map_generator_spec.md`（本文） |
| 生成器工作区 | `out/re_work/re_sprint/R_a3_genspec/**` |
| 金样/既有产物（只读） | `out/re_work/zcode_live/gap_p21_a3/ECHGAP.*` |
| 部署目标（harness 写） | `ra2youli/` 游戏目录（生成器**不**写） |

### 6.3 稳定性契约

1. **确定性**：同 design JSON + 同 variant ⇒ 字节级同 sha256（装饰性 `scatter_trees` 若启用必须固定 seed 且默认关闭）。
2. **字段只增不改**：mapreport 新增键允许；既有键语义/类型冻结。
3. **编码冻结**：`.MAP` = GBK+CRLF；`.ini.txt`/report/片段 = UTF-8。
4. **失败可见**：校验失败必须有 `ECHGAP.check.json`，禁止静默吐图。

---

## 7. 风险与红线

| ID | 风险 | 规格要求 |
|---|---|---|
| G-1 | 直接用 `act_reveal_waypoint` ⇒ P7 恒 `'A'` | 必须 `wp_letter` 手构；V10 卡死 |
| G-2 | CellTags 缺失 ⇒ TagClass 不实例化、触发永不跑 | insert 必选；V08 行数下限 |
| G-3 | 键编码误用 `row*1000+col` | V07 平行四边形反查 |
| G-4 | maplib 硬编码 `FogOfWar=no` / `IgnoreGlobalAITriggers=yes` | 两处补丁；V01/V02 |
| G-5 | 单 GAGAP 断电 ⇒ `DestroyGap` 提前 | ≥2 台 + 电站配额；V03/V04 |
| G-6 | 缝宿主与玩家同盟 ⇒ `CreateGap` 跳过盖印 | `allies` 自含；V04 |
| G-7 | BATTLEMD 占官方 ID/条目名 | V14 + 片段头红线 |
| G-8 | GBK 编码替换字符污染图 | V12；文案用 BMP 内中文 |
| G-9 | 校验失败仍落定稿 `.MAP` | temp→rename；失败写 `.rej` |
| G-10 | CAFARM02 当缝源 | 不进默认 design；若用须 rules 覆写证明参与 `CreateGap`（R-6） |

---

## 8. 实现清单（给执行方）

1. `tools/a3_map_gen.py`（或 `R_a3_genspec/a3_map_gen.py`）：CLI + §4 管线 + §5 校验器。  
2. `a3_map_design.json` 默认参数 = §2.1 示例（与金样 ECHGAP 对齐）。  
3. 黄金对拍：生成 `variant=full` 应得 sha256 `fc49b149…`（若 maplib 未变）；对不上则 diff `ini.txt` 找漂移点。  
4. 自测用例：`wp_letter` 锚点 ×4；CellTags 探针键 `46090`；N=49 时 id `50..98` 与 P7 `AY..CU` 区间。  
5. 不写：`ra2forge/**`、台账/看板、`gamemd.exe`、游戏目录部署。

---

*依据：`docs/re/a3_campaign_map_spec.md`（图面/触发/CellTags/BATTLEMD/判据）；`ra2forge/maplib.py`（CellGrid/MissionMap/to_ini_text）；`ra2forge/triggers.py`（make_trigger/ev_elapsed_time/act_text/act_reveal_waypoint 陷阱）；`out/re_work/zcode_live/gap_p21_a3/gap_p21_a3_gen.py`（已跑通基座）；`out/re_work/re_sprint/R_a3_map/**`（清单）。*
