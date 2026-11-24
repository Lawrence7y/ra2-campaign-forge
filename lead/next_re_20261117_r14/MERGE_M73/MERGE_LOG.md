# M73 MERGE LOG — 并表 2 行（NAMED_PUSH_AUDIT15 PASS 2 行：S18 007B10C0 / S09 004F45B0）

- 时间：2026-11-20T15:57:26+08:00（before 采集） / 2026-11-20T15:59:27+08:00（after 采集）。
- 角色：本轮唯一 COVERAGE 写者；仅写 `COVERAGE/coverage.tsv` 与 `COVERAGE/PANEL.md`（及本 `MERGE_M73/` 交付目录）。
- 未 git commit；未碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`BOARD_ARCHIVE.md`、任何 `NAMED_PUSH_*` 与 `AUDIT*` 目录。

## 1. 输入与交集（两行并行数 1 与 1，合计 2）

| 组 | 审计表 | delta 来源 | 应并行数 | 实算 |
|---|---|---|---:|---:|
| 1 | `NAMED_PUSH_AUDIT15/verdict.tsv` | `NAMED_PUSH_S18_B4/delta.tsv` | 1 | 1 |
| 2 | `NAMED_PUSH_AUDIT15/verdict.tsv` | `NAMED_PUSH_S09_B1/delta.tsv` | 1 | 1 |

- 行 1：`007B10C0`（S18，`IPXInterfaceClass::slot15`）；verdict = PASS，`ring2_at=007F794C`、`ring3b_form=3b2`、`ring4_at=007B0DA4`、`same_source=no`。
- 行 2：`004F45B0`（S09，`MouseClass::slot17`）；verdict = PASS，`ring2_at=007E1964`、`ring3b_form=3b2`、`ring4_at=005BDA4A`、`same_source=no`。
- 交集 `NAMED_PUSH_AUDIT15/verdict.tsv ∩ (两 delta)` = 正好 2 行（`007B10C0`、`004F45B0`），verdict 2/2 全 PASS；两 entry 各自在 coverage 恰好出现 1 次。
- atlas 内校验（entry 归一，`function_atlas.tsv` 12,916 数据行）：2/2 全在 atlas 内（`007B10C0` L12021、`004F45B0` L3948）。
- 并行数不符即停下的条件未触发（审计 2 行、delta 各 1 行、交集正好 2）。

## 2. Lead 已核前置（改前，不符即停）

| 指标 | 卡片给定 | 盘上实算 | 一致 |
|---|---:|---:|---|
| 数据行数 | 18,498 | 18,498 | ✅ |
| 全表 `[已证]` | 1,613 | 1,613 | ✅ |
| atlas 内 `[已证]` | 1,607 | 1,607 | ✅ |
| atlas 外 `[已证]` | 6 | 6 | ✅ |
| S18 atlas 内 proved | —（自算） | 56 | ✅（面板现值） |
| S09 atlas 内 proved | —（自算） | 114 | ✅（面板现值） |

任一不符即停下的条件均未触发。

## 3. coverage.tsv 改动

对 2 行各改 3 列，逐行断言其余 5 列逐字节不变：

- 第 4 列 `one_line_semantics` ← 对应 delta.tsv 第 4 列原文照抄（`007B10C0` 取 `NAMED_PUSH_S18_B4/delta.tsv`，`004F45B0` 取 `NAMED_PUSH_S09_B1/delta.tsv`；逐字节核对 PASS）。
- 第 5 列 `grade`：`[静态推断]` → `[已证]`。
- 第 6 列 `evidence_path`：原值 → `NAMED_PUSH_AUDIT15/VERDICT.md`（两行统一）。
- 第 1/2/3/7/8 列不动。数据行仍 18,498、8 列、TAB 分隔；行数不增不减。
- 改动行（文件 1-based 行号）：3948（004F45B0）、12026（007B10C0）。
- 两行新语义均不含字面 `[未证]`（核两 delta 第 4 列亦不含），故 strict 随 proved 同增。
- 说明：delta 0004F45B0 语义中「成功路 0x4A3434 ret」的引证错误由审计补正（真值 0x4A3592）；按卡片要求「语义取 delta 原文」，第 4 列保留 delta 原文，该更正写入 PANEL 备注列（见第 4 节），不改写第 4 列。

## 4. PANEL.md 同步

- 全表 `[已证]` / atlas 内 `[已证]`：`1,613 / 1,607` → `1,615 / 1,609`；atlas 外仍 6。
- 面板主表 S18 行：proved `56→57`、proved_pct `8.50→8.65`（57/659）；named 各列不动。
- 面板主表 S09 行：proved `114→115`、proved_pct `10.85→10.94`（115/1051）；named 各列不动。
- 面板主表 TOTAL 行：proved `1607→1609`、proved_pct `12.44→12.46`。
- 严格口径双列表 S18 行：proved `56→57 / 8.50→8.65`，proved_strict `46→47 / 6.98→7.13`。
- 严格口径双列表 S09 行：proved `114→115 / 10.85→10.94`，proved_strict `97→98 / 9.23→9.32`。
- 严格口径双列表 TOTAL 行：proved `1607→1609 / 12.44→12.46`，proved_strict `1290→1292 / 9.99→10.00`。
- 备注列追加（S18/S09/TOTAL 备注首部、全表/atlas 单元格备注、标题行），原文：
  `M73 并表 NAMED_PUSH_AUDIT15 PASS 2 行（S18 007B10C0 / S09 004F45B0，evidence_path 改指 NAMED_PUSH_AUDIT15/VERDICT.md；审计补证了 delta 缺失的 ②/④ 地址，并纠 004F45B0 的成功返回地址应为 0x4A3592）`
- 标题行首追加 M73 并表摘要（与既有 M72/M71/… 同格式）。
- 严格口径双列表区插入 M73 并表实算说明（第 162 行，紧接 M72 ㉓ 正向记录之后）。
- strict 用带方括号字面 `[未证]` 口径（`if "[未证]" not in sem:`）；2 行新语义逐行核两 delta 第 4 列均不含字面 `[未证]`，故 strict 随 proved 同增（S18 +1、S09 +1、TOTAL +2）。

## 5. 达标翻转（不得改变）

- 名义达标：3/22 = S15 / S16 / S17（未变）。
- 严格达标：1/22 = S17（未变）。
- S18 门槛：named 594（现 497，未过）、proved 330（现 57，未过）；S09 门槛：named 946（现 681，未过）、proved 526（现 115，未过）。两行虽各 +1 proved，但 named 门槛远未达标，均不参与达标排名。
- **无达标翻转**（算出即停下报告；本次未触发）。

## 6. 复核结果

- `MERGE_M73/verify.py after`：OVERALL **ALL PASS（35 checks）**（含两行并行数 1+1、交集、2 行三列、atlas 内校验、行数/列数、全表/atlas 内/外已证数、S18/S09 proved/strict、TOTAL、nominal/strict 达标无翻转、PANEL 各串存在性与旧串消失）。
- `MERGE_M73/apply_coverage.py`：内置前置断言（并行数 2、全 PASS、两 delta 各 1 行、两行全 atlas 内、其余 5 列不动、新语义无 `[未证]`）全部 PASS。
- `MERGE_M73/apply_panel.py`：8 处替换各命中 1 次、M73 实算说明插入 1 次。
- 改前/改后 mtime/字节/sha256 见 `MERGE_M73/BEFORE_AFTER.txt`；强制指标汇总见 `MERGE_M73/VERIFY.txt`。
- 备份：`MERGE_M73/_before_coverage.tsv`、`MERGE_M73/_before_PANEL.md`（SHA 与改前一致）。
