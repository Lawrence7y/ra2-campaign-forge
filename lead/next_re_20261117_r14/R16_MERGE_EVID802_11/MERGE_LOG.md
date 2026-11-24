# R16-MERGE-EVID802-11（M95）合并日志

> 角色：合并员（`agent-43`）· 日期 2026-11-21
> 写域：`COVERAGE\coverage.tsv`（11 行第 6 列）+ `COVERAGE\PANEL.md`（插入 1 条 M95 披露）+ 本目录产物
> 输入：`R16_EVID802_11\coverage_delta.tsv`（11 行，注记已由执行器重写）、`R16_AUDIT_EVID802_11\VERDICT.md`、`R16_PROBE_802_ANCHOR\REPORT.md`
> 硬边界：未改 grade / 第 4 列语义 / 其它列 / 行序；PANEL 既有内容零删除零改字；未写 `R14_COMMON` / 台账 / 看板 / `_drafts\` / `_cards\` / 任何卡目录；未做逆向；`resolve.py` / `strict_panel.py` 输出只落本目录。

---

## 0. 文件前后状态

| 文件 | 改前 bytes | 改前 sha256 | 改后 bytes | 改后 sha256 |
|---|---:|---|---:|---|
| `COVERAGE\coverage.tsv` | 4,079,053 | `3A1DC1DD3F67B7684BF167640CEECF3EC85330CF5B54C31B65A02CA98C993D4A` | 4,083,215 | `2F498B18E64E7EF568A0EB7888CE9F8D710CABC91038E52A8167F8826B53B36E` |
| `COVERAGE\PANEL.md` | 181,634 | `534177A6B6AC1C902FBDB634F84AD588C3BF471CBD3678E2DD86FA8571F56854` | 183,204 | `55D8B7E02EB609F71C301071B1122C67C45D44ED945A47E9A0AD2C6272F9B2ED` |

改前 mtime：coverage `2026-11-20T17:03:44.193676Z`，PANEL `2026-11-20T17:03:44.195181Z`。
改后行数：coverage 18,499（表头 + 18,498 数据行，不变）；PANEL 664（+5 行 M95 披露）。

## 1. 11 行 before/after（仅列第 6 列）

11 行行号：`1388 / 1389 / 4982 / 5286 / 5287 / 5387 / 5388 / 8877 / 8878 / 8983 / 8984`（与 VERDICT §A 一致）。

- 改前第 6 列（11 行一律）：`EVIDENCE/classification_trace.tsv#<entry>`
- 改后第 6 列（统一 3 段结构）：`EVIDENCE/classification_trace.tsv#<entry>;<S10|S20>_KPROVED\EVIDENCE\PROOF_<entry>.txt;M94 指针修复：…`
- 逐行 before/after 全文见 `after_state.json` 的 `changed_rows` 字段（本节不贴全表）。

entry 清单与 PROOF 路径：

| entry | 改后 PROOF 指针 | 盘上字节 |
|---|---|---:|
| `0045A560` | `S10_KPROVED\EVIDENCE\PROOF_0045A560.txt` | 710 |
| `0045A610` | `S10_KPROVED\EVIDENCE\PROOF_0045A610.txt` | 596 |
| `0053C6A0` | `S20_KPROVED\EVIDENCE\PROOF_0053C6A0.txt` | 5,295 |
| `005514B0` | `S20_KPROVED\EVIDENCE\PROOF_005514B0.txt` | 4,690 |
| `00551560` | `S20_KPROVED\EVIDENCE\PROOF_00551560.txt` | 1,784 |
| `00557090` | `S20_KPROVED\EVIDENCE\PROOF_00557090.txt` | 4,675 |
| `00557140` | `S20_KPROVED\EVIDENCE\PROOF_00557140.txt` | 1,769 |
| `006B1850` | `S10_KPROVED\EVIDENCE\PROOF_006B1850.txt` | 723 |
| `006B1900` | `S10_KPROVED\EVIDENCE\PROOF_006B1900.txt` | 600 |
| `006B8660` | `S10_KPROVED\EVIDENCE\PROOF_006B8660.txt` | 723 |
| `006B8710` | `S10_KPROVED\EVIDENCE\PROOF_006B8710.txt` | 600 |

注记唯一性复算：`unique=11`、entry 归一后 `unique=11`、全 8 位 hex 归一后 `unique=11`（Lead 自核已独立复核）。

## 2. PANEL 披露

在 M93 块（第 267–273 行，末行为 `> **76/76 收官**…`）**之后**、M77 并表实算说明之前插入 5 行 M95 披露（第 274–278 行）。内容覆盖：11 行原为 trace-only、④ 早已写在 PROOF 文件里、本次只把台账指针连过去；选行来自 `R16_PROBE_802_ANCHOR` 全量锚点验证（127 行文件名命中全部 STRONG、只有 11 行带完整 ①②③④ 的 PROOF 文件、其余 116 行属逐 entry dump，改指等于 trace-only→dump-only，明确不做）；审计裁决与 resolve 复算；达标未翻转。PANEL 既有内容零删除零改字。

## 3. 八项验证（全部 PASS）

| # | 验证项 | 结果 | 实测 |
|---|---|---|---|
| ① | coverage 逐字节还原性 | **PASS** | 11 行第 6 列换回改前值后 `sha=3A1DC1DD…93D4A` == 改前；改后 `sha=2F498B18…B36E` |
| ② | 不变量 | **PASS** | 数据行 `18,498`、列数分布 `{8:18498}`、`[已证]` `1,654`、atlas 内 `[已证]` `1,648`、atlas 外 `6` |
| ③ | 只有 11 行第 6 列变 | **PASS** | 全文件逐行 diff 差异恰 11 行（行号同上），每行 `changed_cols=[5]`（0-based 第 6 列） |
| ④ | 新指针 isfile 且非空 | **PASS** | 11/11 命中 r14 基准，字节数 600–5,295，全 > 0 |
| ⑤ | resolve.py 重跑 | **PASS** | 改前 `R_OK=852 / R_MISSING=0 / R_TRACE_ONLY=802 / R_EMPTY=0`；改后 `R_OK=863 / R_MISSING=0 / R_TRACE_ONLY=791 / R_EMPTY=0` |
| ⑥ | PANEL 还原性 | **PASS** | 删除插入的 5 行后 `sha=534177A6…56854` == 改前；改后 `sha=55D8B7E0…82ED` |
| ⑦ | 达标未翻转 | **PASS** | 改前/改后一致：名义 `S15,S16,S17`、严格 `S17` |
| ⑧ | 行尾不混用 | **PASS** | coverage 前后 `LF=18498 / CRLF=0 / loneCR=0`；PANEL 前 `LF=659`、后 `LF=664`，`CRLF=0 / loneCR=0` |

验证脚本 `verify.py` 可一键复跑全部 8 项；机器可读结果在 `verify_result.json`。

## 4. 产物

- `MERGE_LOG.md`（本文件）
- `verify.py`（全量可复跑验证）
- `do_merge.py` / `explore.py`（合并与探查脚本）
- `before_state.json` / `after_state.json`
- `verify_result.json`
- `_coverage_before.tsv` / `_panel_before.md`（改前逐字节备份）
- `resolve.py`（EVID_RESOLVE 副本）、`_resolve_before\summary.tsv` / `_resolve_after\summary.tsv`、`_resolve_before\resolve.tsv` / `_resolve_after\resolve.tsv`
- `_strict_panel_before.py` / `_strict_panel_after.py`、`_strict_before\strict_panel.{tsv,json}` / `_strict_after\strict_panel.{tsv,json}`

（未贴全表；所有 11 行 before/after 详见 `after_state.json`。）
