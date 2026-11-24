# M72 MERGE LOG — 并表 11 行（NAMED_PUSH_AUDIT13 7 行 S07 + NAMED_PUSH_AUDIT14 4 行 S11）

- 时间：2026-11-20T15:27:12+08:00（before 采集） / 2026-11-20T15:28:15+08:00（after 采集）。
- 角色：本轮唯一 COVERAGE 写者；仅写 `COVERAGE/coverage.tsv` 与 `COVERAGE/PANEL.md`（及本 `MERGE_M72/` 交付目录）。
- 未 git commit；未碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT*`、`INVENTORY`、`BOARD_ARCHIVE.md`。

## 1. 输入与交集（两组并行数 7 与 4）

| 组 | 审计表 | delta 来源 | 应并行数 | 实算 |
|---|---|---|---:|---:|
| A | `NAMED_PUSH_AUDIT13/verdict.tsv` | `NAMED_PUSH_S07_B1/delta.tsv` | 7 | 7 |
| B | `NAMED_PUSH_AUDIT14/verdict.tsv` | `NAMED_PUSH_S11_B1/delta.tsv` | 4 | 4 |

- A 组 7 entry：`00421730` `004370C0` `00491210` `005550C0` `00555110` `00555150` `006DBD20`；verdict 全 S07/PASS。
- B 组 4 entry：`004AF720` `004B62C0` `004B6470` `0054DC60`；verdict 全 S11/PASS。
- 交集 `verdict ∩ delta`：A 组正好 7、B 组正好 4；两组 verdict/delta 集合各自完全相等，A/B 不重叠；每 entry 在 coverage 恰好出现 1 次。
- atlas 内校验（entry 小写归一，以 `function_atlas.tsv` 12,916 数据行为准）：11/11 全在 atlas 内。
- **不进并表**：`NAMED_PUSH_S09_B1/delta.tsv` 的 1 行 `004F45B0`（尚未经异族审计），留在池里、整行不动。

并行数不符即停下的条件未触发（7 与 4 均吻合）。

## 2. Lead 已核前置（改前，不符即停）

| 指标 | 卡片给定 | 盘上实算 | 一致 |
|---|---:|---:|---|
| 数据行数 | 18,498 | 18,498 | ✅ |
| 全表 `[已证]` | 1,602 | 1,602 | ✅ |
| atlas 内 `[已证]` | 1,596 | 1,596 | ✅ |
| atlas 外 `[已证]` | 6 | 6 | ✅ |
| S07 atlas 内 proved | —（自算） | 67 | ✅（面板现值） |
| S11 atlas 内 proved | —（自算） | 28 | ✅（面板现值） |

任一不符即停下的条件均未触发。

## 3. coverage.tsv 改动

对 11 行各改 3 列，逐行断言其余 5 列逐字节不变：

- 第 4 列 `one_line_semantics` ← 对应 delta.tsv 第 4 列原文照抄（A 组取 `NAMED_PUSH_S07_B1/delta.tsv`，B 组取 `NAMED_PUSH_S11_B1/delta.tsv`；逐字节核对 PASS）。
- 第 5 列 `grade`：`[静态推断]` → `[已证]`。
- 第 6 列 `evidence_path`：原值 → A 组 `NAMED_PUSH_AUDIT13/VERDICT.md`、B 组 `NAMED_PUSH_AUDIT14/VERDICT.md`。

第 1/2/3/7/8 列不动。数据行仍 18,498、8 列、TAB 分隔；行数不增不减。
改动行（文件 1-based 行号）：732, 1062, 2041, 2701, 2785, 2790, 5224, 5330, 5331, 5334, 9660。

## 4. PANEL.md 同步

- 全表 `[已证]` / atlas 内 `[已证]`：`1,602 / 1,596` → `1,613 / 1,607`；atlas 外仍 6。
- 面板主表 S07 行：proved `67→74`、proved_pct `8.33→9.20`（74/804）；named 各列不动。
- 面板主表 S11 行：proved `28→32`、proved_pct `7.61→8.70`（32/368）；named 各列不动。
- 面板主表 TOTAL 行：proved `1596→1607`、proved_pct `12.36→12.44`。
- 严格口径双列表 S07 行：proved `67→74 / 8.33→9.20`，proved_strict `44→51 / 5.47→6.34`。
- 严格口径双列表 S11 行：proved `28→32 / 7.61→8.70`，proved_strict `27→31 / 7.34→8.42`。
- 严格口径双列表 TOTAL 行：proved `1596→1607 / 12.36→12.44`，proved_strict `1279→1290 / 9.90→9.99`。
- 备注列追加（S07/S11/TOTAL 备注首部、全表/atlas 单元格备注、标题行），原文：
  `M72 并表 NAMED_PUSH_AUDIT13 PASS 7 行（S07）+ NAMED_PUSH_AUDIT14 PASS 4 行（S11），evidence_path 分别改指两审计 VERDICT；S09_B1 的 1 行未审不并`
- 标题行首追加 M72 并表摘要（与既有 M71/M70/… 同格式）。
- strict 用带方括号字面 `[未证]` 口径（`if "[未证]" not in sem:`）；11 行新语义逐行核两 delta 第 4 列均不含字面 `[未证]`，故 strict 随 proved 同增（S07 +7、S11 +4、TOTAL +11）。

## 5. M72 ㉓ 正向记录（写进 PANEL 备注，不单列披露）

- 位置：`PANEL.md` 第 161 行，紧接 M72 并表实算说明（第 160 行）之后、M71 披露（第 155–159 行）之后。
- 内容（逐字节从 `M72-MERGE.md` 提取，verify.py 断言 verbatim-identical = PASS）：

  `S07 有 2 行真触发㉓陷阱（同一虚表也被析构器写入 00490406 / 006DC475），因执行器 ④ 锚点取在行外构造器（0048E93B / 006D1D54）而未触雷 ⇒ ㉓ 不是形式检查，是真会命中的判据。`

## 6. 达标翻转（不得改变）

- 名义达标：3/22 = S15 / S16 / S17（未变）。
- 严格达标：1/22 = S17（未变）。
- S07 门槛 402（proved 74 / strict 51 远低）、S11 门槛 184（proved 32 / strict 31 远低），均不参与达标排名。
- **无达标翻转。**

## 7. 复核结果

- `MERGE_M72/verify.py`：OVERALL **ALL PASS（51 checks）**（含两组并行数 7/4、交集、11 行三列、atlas 内校验、行数/列数、全表/atlas 内/外已证数、S07/S11 proved/strict、TOTAL、S09 grade 未变、达标无翻转、PANEL 各串与 ㉓ 逐字节核对）。
- `MERGE_M72/apply_coverage.py`：内置前置断言（并行数 7+4、全 PASS、S09 排除、11 行全 atlas 内、其余 5 列不动）全部 PASS。
- `MERGE_M72/apply_panel.py`：8 处替换各命中 1 次、M72 实算说明与 ㉓ 记录各插入 1 次。
- 改前/改后 mtime/字节/sha256 见 `MERGE_M72/BEFORE_AFTER.txt`。
- 强制指标汇总见 `MERGE_M72/VERIFY.txt`。
