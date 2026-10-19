# A3 地图生成器实现说明 · `a3_map_gen`（R-A3-IMPL）

> **卡号**：`R-A3-IMPL` · **规格**：`docs/re/a3_map_generator_spec.md`（V01–V15）  
> **代码**：`out/re_work/re_sprint/R_a3_impl/a3_map_gen.py`  
> **自检**：`out/re_work/re_sprint/R_a3_impl/run_selftest.py`（当前 **SELFTEST PASS**）  
> **基座**：`ra2forge.maplib.MissionMap` + `ra2forge.triggers`（只 import，未改源）  
> **写作用域**：`out/re_work/re_sprint/R_a3_impl/**` + 本文

---

## 0. 一句话

确定性 Python 生成器：吃 `a3_map_design.json` + CLI 变体，吐 `ECHGAP.MAP`（GBK/CRLF）
与 mapreport / BATTLEMD 片段 / check.json；生成末尾强制跑 V01–V15，失败拒收（退出码 2）。
`variant=full` 与金样 **字节一致**（sha256 `fc49b149…`）。

---

## 1. 管线（对照规格 §4.1）

```
load design → validate_schema (§2.1 不变量 1..6)
build MissionMap (placements / waypoints / hand-crafted triggers)
  → text = m.to_ini_text()
  → patch_specialflags   # FogOfWar=yes
  → patch_basic          # IgnoreGlobalAITriggers=no, EndOfGame=yes, NextScenario=
  → insert_cell_tags     # [CellTags] after [Actions]
  → crlf + encode gbk
  → check_map (V01–V15)
  → pass: write .MAP (temp→rename) + mapreport + battlemd + check.json
    fail: write .MAP.rej + check.json + mapreport(rejected) + exit 2
```

### 1.1 关键实现点

| 规格点 | 实现 |
|---|---|
| `to_cell(row,col)→(x,y)` | 只经 `m.grid.to_cell` / `CellGrid.to_cell`；无手写换算 |
| TA17 P7 | 手构 `(17, (p1, w, 0,0,0,0, wp_letter(w)))`；**未**用 `act_reveal_waypoint`（P7 恒 `'A'` 陷阱） |
| CellTags 编码 | `key = y*1000+x`（`to_cell` 返回 `(x,y)`） |
| maplib 硬编码 | 生成后补丁 `FogOfWar=yes` / `IgnoreGlobalAITriggers=no` / `EndOfGame=yes` / `NextScenario=` |
| 行尾/编码 | 写盘前 `\n`→`\r\n`；`.MAP` 用 GBK 严格编码（失败退出 4）；明文/报告 UTF-8 |
| 拒收语义 | 校验失败只落 `.MAP.rej`，定稿名不写 |

### 1.2 `wp_letter`

```
w < 26           → chr(A+w)
w ≥ 26           → r=w-26; chr(A+r//26) + chr(A+r%26)
```

锚点（V11 卡死）：`50↔AY` · `52↔BA` · `121↔DR` · `469↔RB`。T2 的 49 条动作 P7 序列
`AY..CU`（id 50..98）。

---

## 2. 默认 design 与图面

`a3_map_design.default.json`（schema `a3-map-design/1`）与金样对齐：

- size=90 方图，TEMPERATE，player=Russians / gap_owner=Americans / spy_owner=Germans
- 玩家基地 (45,45)：NACNST+NAPOWR+NAWEAP+E1×5+MTNK×2，**无雷达**
- 缝宿主 (18,18)：GAPOWR×6+GACNST+GAWEAP+GI×4 + GAGAP×2 @ (41,47)(49,43)
- 雷达方 (72,72)：GAPOWR×4+GACNST+NARADR(full)+GI×4
- water_rect [8,8,13,13]；waypoints 0/1/2 + 网格 50..98（7×7，step=4 half=12）
- 触发：探针 t=20s TA11 文本；开图 t=60s 49×TA17

### 2.1 已知金样特征（非缺陷，但校验器必须容忍）

**CellTags 同键双写**：网格中心即玩家基地格，故
`46090=0000B032`（探针）与 `46090=0000B022`（开图）**两行同键**。
金样 `ECHGAP.MAP` 亦如此（50 行 / 49 唯一键）。校验器按 **行** 计数（V08 `≥ 1+N`），
解析器对 `[CellTags]` 用保序 kv 列表（`parse_ini_kv_list`）而非 dict。

---

## 3. 产物契约（规格 §3）

| 产物 | 格式 | 备注 |
|---|---|---|
| `ECHGAP.MAP` | GBK + CRLF | 金样 sha256 `fc49b149b4f23dae18313eaf8ce22082b34533f90b7fd14a425d50592944dc51` |
| `ECHGAP_NR.MAP` | 同上 | `variant=nr`；sha256 `b6d43d7cca066de6071d3015887090c5743459ee4386598d9aaec712217c206a` |
| `*.ini.txt` | UTF-8 | 人读/diff |
| `*.mapreport.json` | UTF-8 JSON | 字段见下 |
| `*.check.json` | UTF-8 JSON | V01–V15 逐条 |
| `*.battlemd.C2-a.ini.txt` / `*.battlemd.C2-b.patch.txt` | UTF-8 | 含红线头注释 |

### 3.1 mapreport 字段（冻结）

`map, variant, bytes, sha256, size, fog_of_war, player, gap_owner, spysat_owner,
base_rowcol, base_file_cell, gap_pos_rowcol, gap_pos_file_cells, gap_radius_cells,
grid{step,half,n,wp_ids,file_cells}, triggers{probe,reveal}, celltags{n,probe_keys,reveal_key0},
sections, battlemd{form,scenario_line}` + 新增 `file_cell_order`。

**坐标序约定（实现修正）**：`base_file_cell` / `gap_pos_file_cells` / `grid.file_cells`
统一为 **`[x, y]`**（即 `to_cell` 返回序）。金样 `gap_pos_file_cells` 曾写 `[y, x]`，
与 `base_file_cell` 不一致；本实现以 `file_cell_order: "xy"` 显式冻结，harness 侧换算
`i=(y-1)*512+(x-1)` 时按 `[x,y]` 取分量。

---

## 4. 校验器 V01–V15

全部 15 条在生成末尾与 `--check-only` 共用 `check_map`；结果落 `*.check.json`。

| ID | 判据（实现） | 默认结果 |
|---|---|---|
| V01 | `[SpecialFlags] FogOfWar=yes` | PASS |
| V02 | `IgnoreGlobalAITriggers=no` ∧ `EndOfGame=yes` ∧ `NextScenario=` 空 | PASS |
| V03 | `GAGAP` 条数 ≥ `min_generators`（附 gap_owner 电站配额报告） | PASS (2≥2) |
| V04 | 缝宿主 `Allies=` 不含玩家；基地文件格 ∈ GAGAP 覆盖**并集**（Chebyshev≤radius） | PASS (d=6,6) |
| V05 | 玩家结构无 `*RADR`/`NARADR`/`GARADR` | PASS |
| V06 | Waypoints 含 0/1/2；网格 id `50..98` 连续 | PASS |
| V07 | 每个 CellTags 键 `key==y*1000+x` 且落在平行四边形，反查 row/col ∈ `[0,W)` | PASS |
| V08 | 值集合 ⊆ `[Tags]` 键；行数 ≥ 1+N；探针键邻域(≤4) 基地文件格 | PASS (50≥50) |
| V09 | 每个 tid 在 Triggers/Events/Actions 为键，且被某 Tag 值引用 | PASS |
| V10 | T2 每条 action：`code=17` ∧ `P7==wp_letter(P2)` ∧ (N>1 时) P7 不全为 `'A'` | PASS |
| V11 | `wp_letter` 锚点 50↔AY / 52↔BA / 121↔DR / 469↔RB | PASS |
| V12 | GBK 可解码、无 U+FFFD、纯 CRLF、首段 `[Preview]` | PASS |
| V13 | mapreport.sha256 == 实际文件 sha256；`sections.CellTags == celltags.n` | PASS |
| V14 | BATTLEMD：C2-a 索引≥15 且 entry_id 合法（禁 `1..14`/`ALL*`/`SOV*`/纯数字）；C2-b 仅改一行 | PASS |
| V15 | `nr` ⇒ 无任何雷达屋；`full` ⇒ 恰好第三方雷达方 1 座 | PASS |

---

## 5. CLI

```
python a3_map_gen.py --design a3_map_design.json
    [--variant full|nr]          # 默认 full；nr 产出 *_NR.MAP
    [--battlemd-form C2-a|C2-b]  # 覆盖 JSON battlemd.form（并按覆盖后形态校验）
    [--out-dir DIR]              # 默认 .../R_a3_impl/build/
    [--emit battlemd|all|none]   # 默认 all
    [--check-only]
    [--json-report]              # stdout 末行 = mapreport 绝对路径
    [--seed N]                   # 仅装饰 scatter_trees（默认关闭）
    [--scatter-trees]
    [--celltags-order insert|sorted]  # 默认 insert=金样序；sorted=规格§4.4 key 升序
```

退出码：`0` 通过 · `2` 校验失败 · `3` 输入非法 · `4` IO/编码错误。

**`--celltags-order` 说明**：规格 §4.4 写「按 key 升序」，但金样为
「探针键在前 + 开图键生成序」（因 46090 双写，升序会改变行序与 sha）。
默认 `insert` 以命中金样；`sorted` 可复现规格字面序（sha 必然漂移，V01–V15 仍全过）。

---

## 6. 自检证据（run_selftest.py）

| 项 | 结果 |
|---|---|
| generate full exit=0 | PASS |
| sha256 == 金样 `fc49b149…` | PASS |
| 与 `zcode_live/gap_p21_a3/ECHGAP.MAP` 字节一致 | PASS |
| check.json V01..V15 全 PASS | PASS (15/15) |
| generate nr exit=0 + V15 | PASS |
| check-only exit=0 | PASS |
| 非法 design → exit 3 | PASS |
| 损坏图 → check-only exit 2（V01 FAIL，写 check.json） | PASS |
| 3 次重跑 sha 稳定 | PASS |
| wp_letter 锚点 ×4 | PASS |

跑法：`python out/re_work/re_sprint/R_a3_impl/run_selftest.py`

> 【W3 勘误 · PATCH_SUGGESTIONS BLK-C9-1 / Forge P-1】改前：与 `zcode_live/gap_p21_a3/ECHGAP.MAP` 字节一致 PASS；改后：该行现态应为 FAIL（基准已漂移：`zcode_live/gap_p21_a3/ECHGAP.MAP` 现为 10,436 B / sha256 `6c5e2f2d…`，晚于 build 产物 8,934 B / `fc49b149…`；差 1,502 B，差异在 Structures 电站数 10→28、Triggers/Tags/Actions 拆 4 组等；两版三要素均齐备，实机运行 `src` 指向 zcode_live 版）；依据：`out/re_work/qc/W2_20261001/forge/scripts/echgap_diff.py`；分级：[实证]

---

## 7. 与规格的偏差 / 备忘

| 项 | 规格 | 本实现 | 理由 |
|---|---|---|---|
| CellTags 排序 | §4.4 key 升序 | 默认金样 insert 序，可选 sorted | 需命中金样 sha；46090 双写使升序改变语义行序 |
| `gap_pos_file_cells` | 示例 `[y,x]` | 统一 `[x,y]` + `file_cell_order` | 与 `base_file_cell`/`grid.file_cells` 一致；旧序易在 harness 换算时出错 |
| 默认 out-dir | `R_a3_genspec/build/` | `R_a3_impl/build/` | 本卡写作用域仅 `R_a3_impl/**` |
| maplib 修改 | 禁止 | 未修改 | 补丁/CellTags 全部后处理旁路 |
| house_configs | §4.2 简写 | 对齐金样全字段（techlevel/edge/color） | 保 sha |

---

## 8. 风险对照（规格 §7）

| ID | 状态 |
|---|---|
| G-1 P7 恒 A | 已规避（手构 action；V10） |
| G-2 CellTags 缺失 | 已插入；V08 行数下限 |
| G-3 键编码 row*1000+col | 已规避；V07 平行四边形反查 |
| G-4 maplib 硬编码 | 两处补丁；V01/V02 |
| G-5 单 GAGAP 断电 | ≥2 台 + 电站 6≥6；V03 |
| G-6 同盟跳过 CreateGap | allies 自含；V04 |
| G-7 BATTLEMD 占官方 ID | V14 + 片段头红线 |
| G-8 GBK 替换污染 | 严格编码；V12 |
| G-9 校验失败仍落定稿 | temp→rename / 失败写 .rej |
| G-10 CAFARM02 当缝源 | 默认 design 未使用 |

---

*实现依据：`docs/re/a3_map_generator_spec.md`；`ra2forge/maplib.py`；`ra2forge/triggers.py`；
`out/re_work/zcode_live/gap_p21_a3/gap_p21_a3_gen.py`（基座对照）；金样 `ECHGAP.MAP`。*
