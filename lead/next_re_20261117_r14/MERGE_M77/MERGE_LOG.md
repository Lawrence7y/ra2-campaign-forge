# M77 MERGE LOG — 并表 4 行（NAMED_PUSH_AUDIT20 verdict 4 行全 PASS）+ M77 披露

- 角色：本轮**唯一 COVERAGE 写者**；仅写 `COVERAGE/coverage.tsv` 与 `COVERAGE/PANEL.md`（及本 `MERGE_M77/` 交付目录）。
- 未 git commit；未碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`BOARD_ARCHIVE.md`、任何 `NAMED_PUSH_*` 与 `AUDIT*`、`INVENTORY*`（对 NAMED_PUSH_AUDIT20 / NAMED_PUSH_S07S11_B2 仅只读取 verdict/delta）。
- 用户明确指令：并 `NAMED_PUSH_AUDIT20/verdict.tsv` 4 行全 PASS（S07 `006DBE00` + S11 `0069EE30`/`00719E30`/`0075C7F0`），来源 `NAMED_PUSH_S07S11_B2/delta.tsv`；coverage 只改第 4/5/6 列，第 1/2/3/7/8 列不动；语义取 delta 原文、grade 改 `[已证]`、evidence_path 改 `NAMED_PUSH_AUDIT20/VERDICT.md`；strict 按 `strict_panel.py` 第 78 行权威口径；备注列追加指定文本；M77 披露原样写入 PANEL 接在 M76 披露之后；若算出达标翻转则停下报告。全部照办。
- 时间：BEFORE 采集 2026-11-20T19:00+08:00（改前）；coverage 改后 19:04:11+08:00、PANEL 改后 19:04:41+08:00；复核 19:05+08:00。严格时间见 `BEFORE_AFTER.txt`。

## 1. 输入与交集（并行数 = 本轮并表行数 = 4）

| 项 | 值 |
|---|---|
| 审计表 | `NAMED_PUSH_AUDIT20/verdict.tsv`，4 数据行，4/4 PASS |
| delta 来源 | `NAMED_PUSH_S07S11_B2/delta.tsv`，4 数据行，6 列 |
| 交集 | `AUDIT20.verdict ∩ S07S11_B2.delta` = 正好 4 行，entry 集一致 |
| 4 entry | S07 `006DBE00`；S11 `0069EE30`/`00719E30`/`0075C7F0` |
| grade / 六列 | delta 4 行 grade 全 `[已证]`、全 6 列、col4 全不含字面 `[未证]` |
| atlas 内校验 | 4/4 全在 `function_atlas.tsv`（12,916 行）内 ⇒ atlas 内已证 +4、atlas 外仍 6 |

- 交集正好 4、4/4 PASS、4/4 atlas 内，硬条件满足。

## 2. Lead 已核前置（改前，不符即停）

| 指标 | 卡片给定 | 盘上实算 | 一致 |
|---|---:|---:|---|
| 数据行数 | 18,498 | 18,498 | ✅ |
| 全表 `[已证]` | 1,650 | 1,650 | ✅ |
| atlas 内 `[已证]` | 1,644 | 1,644 | ✅ |
| atlas 外 `[已证]` | 6 | 6 | ✅ |
| S07 atlas 内 proved | —（自算） | 74 | ✅ |
| S11 atlas 内 proved | —（自算） | 32 | ✅ |
| 名义达标集 | S15,S16,S17 | S15,S16,S17 | ✅ |
| 严格达标集 | S17 | S17 | ✅ |

- 两文件改前 sha256 与 `MERGE_M76/BEFORE_AFTER.txt` 记录的改后值逐字一致（coverage `22cde4b8…`、PANEL `2a9cdb96…`），确认起点承接 M76，无中间写者介入。任一「停下」条件（交集不符 / 前置不符 / 达标翻转）均未触发。

## 3. coverage.tsv 改动（4 行 × 3 列）

对 4 行各改 3 列，逐行断言第 1/2/3/7/8 列逐字节不变：

- 第 4 列 `one_line_semantics` ← 对应 delta 第 4 列原文（323/522/485/477 字符）。
- 第 5 列 `grade`：`[静态推断]` → `[已证]`。
- 第 6 列 `evidence_path`：`EVIDENCE/classification_trace.tsv#<entry>` → `NAMED_PUSH_AUDIT20/VERDICT.md`。
- 数据行仍 18,498、8 列、TAB 分隔；无 BOM、LF、逐字节保持。
- 改动行（文件 1-based 行号）：`0069EE30`=8704、`006DBE00`=9661、`00719E30`=10339、`0075C7F0`=11249。

## 4. PANEL.md 同步

- 全表 `[已证]` / atlas 内 `[已证]`：`1,650 / 1,644` → `1,654 / 1,648`；atlas 外仍 6。
- 主表 S07 行：proved `74→75`（75/804=9.33%）；S11：`32→35`（35/368=9.51%）；named 各列不动。
- 主表 TOTAL 行：proved `1,644→1,648`、proved_pct `12.73→12.76`。
- 严格口径双列表：S07 proved `74→75 / 9.20→9.33`、proved_strict `51→52 / 6.34→6.47`；S11 proved `32→35 / 8.70→9.51`、proved_strict `31→34 / 8.42→9.24`；TOTAL proved `1,644→1,648 / 12.73→12.76`、proved_strict `1,327→1,331 / 10.27→10.31`；门槛与达标旗标（3/22、1/22）不动。
- 备注列追加（全表/atlas 单元格、S07/S11/TOTAL 主表备注首部、标题行），原文（自用户指令逐字提取）：
  `M77 并表 NAMED_PUSH_AUDIT20 PASS 4 行（S07 006DBE00 + S11 0069EE30/00719E30/0075C7F0，evidence_path 改指 NAMED_PUSH_AUDIT20/VERDICT.md）；具名通道至此收口（剩余预期 < 3 行）`
- 标题行首追加 M77 并表摘要（与既有 M76/M75/… 同格式，接在 `# PANEL — R14 coverage` 之后、M76 摘要之前）。
- **M77 披露**：自用户指令围栏逐字提取 4 行，**原样写入**（不许改写），接在 M76 披露 4 行块之后；落点第 **173–176** 行（M76 披露为 169–172 行）。披露记 `006DBE00` 两个边界：① 0x1C HRESULT 包装映射近似恒等、形态贴近纯转发（严口径应改判 FAIL）；② 无静态 slot-6 派发点，④ 依赖 ctor 装活表 + new 堆实例 + 全局被读 447 次，弱于另 3 行可见 `ff 10` 派发；均不影响本轮判 PASS，引用须同读。
- 新增 M77 并表实算说明（紧跟 M77 披露后），记 S07/S11/TOTAL 的 proved/strict 改前改后、4 行新语义无字面 `[未证]`、strict 同增、atlas 内外计数、达标未翻转、strict 口径出处。
- strict 用带方括号字面 `[未证]` 口径（`if "[未证]" not in sem:`）；4 行新语义逐行核 delta 第 4 列均不含字面 `[未证]`，故 strict 随 proved 同增（S07 +1、S11 +3、TOTAL +4）。
- 历史截面表（PANEL 约 215–219 行附近）按 M75/M76 先例未动。

## 5. 达标翻转（不得改变）

| 口径 | 改前 | 改后 | 翻转 |
|---|---|---|---|
| 名义达标（proved） | S15,S16,S17 | S15,S16,S17 | 无 |
| 严格达标（strict） | S17 | S17 | 无 |

- 判据：`named_n_S(R14) >= ceil(0.9*n)` 且 `proved/strict_n >= ceil(0.5*n)`；本次只改第 4/5/6 列，named 三列不变。`S07` proved 75 < 门槛 402、`S11` proved 35 < 门槛 184，均不达标。严格口径仍仅 S17（1/22），名义仍 S15/S16/S17（3/22）。**有无达标翻转：无**，未触发「停下报告」。

## 6. 交付与自检

- 交付文件：`MERGE_M77/MERGE_LOG.md`（本文件）、`BEFORE_AFTER.txt`、`VERIFY.txt`（含 `precheck.py`/`apply_coverage.py`/`apply_panel.py`/`verify.py` 脚本留痕）。
- `precheck.py`：38/38 前置检查通过；`verify.py`：75/75 全量复算通过（OVERALL: ALL PASS）。
- VERIFY.txt 覆盖用户要求的全部项：并行数 4、数据行数 18,498、全表/atlas 内/atlas 外 `[已证]`、S07/S11 的 proved 与 strict、有无达标翻转、M77 披露段落行号（173–176）。
- 未触碰禁改文件；未 git commit。
