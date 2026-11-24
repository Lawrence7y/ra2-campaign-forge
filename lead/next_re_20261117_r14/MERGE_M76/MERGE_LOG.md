# M76 MERGE LOG — 并表 7 行（A 组 7，均 PASS；B 组 4 行未审不并）+ 两处改字 + 第六条披露

- 角色：本轮**唯一 COVERAGE 写者**；仅写 `COVERAGE/coverage.tsv` 与 `COVERAGE/PANEL.md`（及本 `MERGE_M76/` 交付目录）。
- 未 git commit；未碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`BOARD_ARCHIVE.md`、任何 `NAMED_PUSH_*` 与 `AUDIT*`、`INVENTORY*`。
- 用户明确指令：本轮只并 A 组 7 行，`NAMED_PUSH_S07S11_B2` 的 4 行未审不许并；两处改字必须落实；M76 披露原样写入 PANEL 接在 M75 之后；strict 用带方括号字面 `[未证]` 口径。全部照办。
- 时间：改前 BEFORE 采集 2026-11-20T18:41:27+08:00（coverage）/18:42:05+08:00（PANEL，见 BEFORE_AFTER.txt 的本地时区换算）；coverage 改后 18:41:23+08:00、PANEL 改后 18:41:56+08:00；复核 18:42+08:00。

## 1. 输入与交集（并行数 = 本轮并表行数 = 7）

| 组 | 审计表 | delta 来源 | 应并行数 | 实算 | 本轮处置 |
|---|---|---|---:|---:|---|
| A | `NAMED_PUSH_AUDIT19/verdict.tsv` | `NAMED_PUSH_S06_B2/delta.tsv`（3）+ `NAMED_PUSH_S01S03_B1/delta.tsv`（1）+ `NAMED_PUSH_S16S21_B1/delta.tsv`（3） | 7 | **7** | 并表 |
| B | 待审（无独立异族审计表） | `NAMED_PUSH_S07S11_B2/delta.tsv`（4） | 4 | 4 | **未审不并** |

- 交集 `AUDIT19.verdict ∩ (S06_B2 ∪ S01S03_B1 ∪ S16S21_B1)` = **正好 7 行**；7/7 verdict 全 PASS；delta 全 6 列、entry 8 位大写十六进制无 `0x`、grade 全 `[已证]`。
- 7 entry：S06 三行 `005FEAF0`/`006B5850`/`0071CDA0` + S03 一行 `00432050` + S21 两行 `0046D000`/`0046D090` + S16 一行 `0071B1B0`。
- B 组 `NAMED_PUSH_S07S11_B2` 仅有产出方自产物 `work/verdicts.json`，无独立异族审计表 `NAMED_PUSH_AUDIT20`（已核目录不存在），按卡片「尚未经异族审计」**不并**，未触发「停下报告」。
- atlas 内校验（entry 小写归一，`function_atlas.tsv` 12,916 数据行）：**7/7 全在 atlas 内**，故 atlas 内已证 +7、atlas 外仍 6。
- delta 第 4 列逐行核：7 行语义均不含字面 `[未证]`，故 strict 随 proved 同增。
- 交集正好 7 的硬条件满足。

## 2. Lead 已核前置（改前，不符即停）

| 指标 | 卡片给定 | 盘上实算 | 一致 |
|---|---:|---:|---|
| 数据行数 | 18,498 | 18,498 | ✅ |
| 全表 `[已证]` | 1,643 | 1,643 | ✅ |
| atlas 内 `[已证]` | 1,637 | 1,637 | ✅ |
| atlas 外 `[已证]` | 6 | 6 | ✅ |
| S03 atlas 内 proved | —（自算） | 38 | ✅ |
| S06 atlas 内 proved | —（自算） | 135 | ✅ |
| S16 atlas 内 proved | —（自算） | 47 | ✅ |
| S21 atlas 内 proved | —（自算） | 28 | ✅ |
| 名义达标集 | S15,S16,S17 | S15,S16,S17 | ✅ |
| 严格达标集 | S17 | S17 | ✅ |

- 两文件改前 sha256 与 `MERGE_M75/VERIFY.txt` 记录的改后值一致（coverage `e6cbd17c…`、PANEL `ae0e05ee…`），确认起点承接 M75。任一「停下」条件（B 组已有独立审计表 / 前置不符 / 达标翻转）均未触发。

## 3. coverage.tsv 改动（7 行 × 3 列）

对 7 行各改 3 列，逐行断言第 1/2/3/7/8 列逐字节不变：

- 第 4 列 `one_line_semantics` ← 对应 delta 第 4 列原文 + 两处强制改字（见第 4 节）。
- 第 5 列 `grade`：`[静态推断]` → `[已证]`。
- 第 6 列 `evidence_path`：7 行全部 → `NAMED_PUSH_AUDIT19/VERDICT.md`。
- 数据行仍 18,498、8 列、TAB 分隔；无 BOM、LF、无尾随换行（逐字节保持）。
- 改动行（文件 1-based 行号）：`00432050`=990、`0046D000`=1548、`0046D090`=1552、`005FEAF0`=7187、`006B5850`=8935、`0071B1B0`=10372、`0071CDA0`=10401。

## 4. 两处改字（审计员点名，必须落实）

1. **`0071B1B0` 槽址笔误 `0071B1A0`→`007F51A0`**：delta 源 col4 已是 `007F51A0`（`0071B1A0` 出现 0 次；审计员基于早期版本记为 `0071B1A0` 笔误）；apply 仍显式执行 `replace('0071B1A0','007F51A0')`（0 次命中，幂等）。盘上 col4 含 `007F51A0`=True、含 `0071B1A0`=False ⇒ 勘误落实。
2. **`0071CDA0` 的 `ff 51 10` 误称「读入」→「成员容器 slot4 下标查询（非读入）」**：delta 源 col4 含 `ff 51 10 读入`（1 次）；apply 改为 `ff 51 10 成员容器 slot4 下标查询（非读入）`。盘上 col4 含 `成员容器 slot4 下标查询（非读入）`=True、含 `ff 51 10 读入`=False ⇒ 改称落实。
3. 其余 5 行第 4 列照抄 delta 原文。

## 5. PANEL.md 同步

- 全表 `[已证]` / atlas 内 `[已证]`：`1,643 / 1,637` → `1,650 / 1,644`；atlas 外仍 6。
- 主表 S03 行：proved `38→39`（39/194=20.10%）；S06：`135→138`（138/847=16.29%）；S16：`47→48`（48/90=53.33%）；S21：`28→30`（30/129=23.26%）；named 各列不动。
- 主表 TOTAL 行：proved `1637→1644`、proved_pct `12.67→12.73`。
- 严格口径双列表：S03 proved `38→39 / 19.59→20.10`、proved_strict `36→37 / 18.56→19.07`；S06 proved `135→138 / 15.94→16.29`、proved_strict `120→123 / 14.17→14.52`；S16 proved `47→48 / 52.22→53.33`、proved_strict `21→22 / 23.33→24.44`；S21 proved `28→30 / 21.71→23.26`、proved_strict `28→30 / 21.71→23.26`；TOTAL proved `1637→1644 / 12.67→12.73`、proved_strict `1320→1327 / 10.22→10.27`；门槛与达标旗标（3/22、1/22）不动。
- 备注列追加（S03/S06/S16/S21/TOTAL 主表备注首部、全表/atlas 单元格备注、标题行），原文（自卡片逐字提取）：
  `M76 并表 NAMED_PUSH_AUDIT19 PASS 7 行（S06_B2 3 + S01S03 1 + S16S21 3，evidence_path 改指 NAMED_PUSH_AUDIT19/VERDICT.md；0071B1B0 槽址按勘误改 007F51A0、0071CDA0 的 ff 51 10 改称成员容器 slot4 下标查询）；NAMED_PUSH_S07S11_B2 的 4 行未审不并`
- 标题行首追加 M76 并表摘要（与既有 M75/M74/… 同格式）。
- 新增 M76 并表实算说明（紧跟披露后），记 S03/S06/S16/S21/TOTAL 的 proved/strict 改前改后、7 行新语义无字面 `[未证]`、strict 同增、两处改字已落实、B 组未并、达标未翻转、strict 口径出处。
- **第六条披露**：自卡片「必须追加的第六条披露」围栏逐字提取 4 行，**原样写入**（不许改写），接在 M75 披露块之后；落点第 **169–172** 行（M75 披露为 165–168 行）。披露记析构体内 Find −1 形态成族同构、族内区分力≈0（待裁，未收紧），Lead 按现行成文规则判 PASS 但披露该族区分力问题，日后收紧须一次性整批翻转。
- strict 用带方括号字面 `[未证]` 口径（`if "[未证]" not in sem:`）；7 行新语义逐行核 delta 第 4 列（含两处改字）均不含字面 `[未证]`，故 strict 随 proved 同增（S03 +1、S06 +3、S16 +1、S21 +2、TOTAL +7）。
- 历史截面表（PANEL 约 205–224 行）按 M75 先例未动。

## 6. 达标翻转（不得改变）

| 口径 | 改前 | 改后 | 翻转 |
|---|---|---|---|
| 名义达标（proved） | S15,S16,S17 | S15,S16,S17 | 无 |
| 严格达标（strict） | S17 | S17 | 无 |

- 判据：`named_n_S(R14) >= ceil(0.9*n)` 且 `proved/strict_n >= ceil(0.5*n)`；本次只改第 4/5/6 列，named 三列不变。`S03/S06/S21` 仍不达标；`S16` 名义仍达标（48≥45）、严格仍不达标（22<45）。**有无达标翻转：无**，未触发「停下报告」。

## 7. 交付与自检

- 交付文件：`MERGE_M76/MERGE_LOG.md`（本文件）、`BEFORE_AFTER.txt`、`VERIFY.txt`（含 precheck/apply/verify 脚本与输出留痕）。
- `precheck.py`：88/88 前置检查通过；`verify.py`：111/111 全量复算通过（OVERALL: ALL PASS）。
- VERIFY.txt 覆盖用户要求的全部项：并行数 7、数据行数 18,498、全表/atlas 内/atlas 外 `[已证]`、S03/S06/S16/S21 的 proved 与 strict、有无达标翻转、M76 披露段落行号（169–172）、两处改字已生效的证据。
- 未触碰禁改文件；未 git commit。
