# MERGE_M58 — 并表 S09_KPROVED8 八行 + 面板加固

## 一句话结论

8 行 S09 entry 原地 `[静态推断]`→`[已证]`（不新增行），coverage 全表 `[已证]` 1,481→1,489、atlas 内 1,476→1,484；PANEL 三处 S09 行同步、TOTAL 同步、L138 后插入界向更正指针；行数 18,498 不变。未 git commit。

## 前置复核（动手前逐项核盘，均与卡片描述一致，无停下理由）

- `S09_KPROVED8/_audit/verdict.tsv`：表头 `entry/verdict/reason` 3 列 + 8 行数据，8 行 verdict 全 `PASS`。
- `S09_KPROVED8/coverage_delta.tsv`：表头 6 列（`entry/subsystem/name/one_line_semantics/grade/evidence_path`）+ 8 行数据。
- 8 entry 在 `coverage.tsv` 中均存在且唯一，改前 grade 全 `[静态推断]`，subsystem 全 S09，name 与 delta 第 3 列逐字一致（slotN 名字保持原样，未做"规范"）。
- 8 entry（大写十六进制）大小写归一后全在 `function_atlas.tsv`（entry 列小写十六进制）内。
- 并表前盘上：`coverage.tsv` 数据行 **18,498**（表头 1 行逗号分隔，数据 TAB 8 列）；全表 `[已证]` **1,481**；atlas 内 `[已证]` **1,476**；atlas 外已证 5 行。
- P0 前置：P0 入口行（S22/atlas 外）本次未触碰。

## 改动 1 — coverage.tsv（8 行，只改第 4/5/6 列）

对下列 8 行，仅做：第 4 列 `one_line_semantics` ← delta 第 4 列原文（逐字照抄、未改写未截断）；第 5 列 `[静态推断]`→`[已证]`；第 6 列 → `S09_KPROVED8/_audit/VERDICT.md`。第 1/2/3/7/8 列逐字节未动；`n_sources`/`conflict` 保持原值。

| entry | subsystem | name（未改） | 第 4 列语义字节长 | 改前 grade | 改后 grade | evidence_path（改后） |
|---|---|---|---:|---|---|---|
| 004888B0 | S09 | ColorListClass::slot43 | 377 | [静态推断] | [已证] | S09_KPROVED8/_audit/VERDICT.md |
| 00488910 | S09 | ColorListClass::slot42 | 351 | [静态推断] | [已证] | S09_KPROVED8/_audit/VERDICT.md |
| 00488980 | S09 | ColorListClass::slot50 | 330 | [静态推断] | [已证] | S09_KPROVED8/_audit/VERDICT.md |
| 006539D0 | S09 | RTacticalClass_RadarClass::slot31 | 391 | [静态推断] | [已证] | S09_KPROVED8/_audit/VERDICT.md |
| 006D0A20 | S09 | MouseClass::slot16 | 394 | [静态推断] | [已证] | S09_KPROVED8/_audit/VERDICT.md |
| 00565AA0 | S09 | MouseClass::slot22 | 385 | [静态推断] | [已证] | S09_KPROVED8/_audit/VERDICT.md |
| 00771900 | S09 | Anim_Voices_WorldDominationTour::slot2 | 450 | [静态推断] | [已证] | S09_KPROVED8/_audit/VERDICT.md |
| 0049FB40 | S09 | CounterClass::slot3 | 375 | [静态推断] | [已证] | S09_KPROVED8/_audit/VERDICT.md |

逐行语义取自 delta 原文，字节长 377/351/330/391/394/385/450/375 用于自证未截断。8 行在 coverage 原始行号依次为 1944 / 1945 / 1947 / 7894 / 9573 / 5549 / 11607 / 2436（1-based，改前截面）。

核盘自检：改后数据行仍 18,498、全为 TAB 8 列；全表 grade 分布 `[已证]` 1,489 / `[静态推断]` 5,985 / `[未证]` 11,024（和 18,498）；8 行逐行 grade=[已证]、语义与 delta 逐字节相同、evidence_path 已改指 VERDICT.md。

## 改动 2 — PANEL.md（三处 S09 行 + TOTAL + 界向指针）

按盘上现值定位（现值特征 `S09 | 1051 | … | 106 | 10.09`），共三处 S09 行：

1. **主覆盖面板行（原 L63）**：`proved_n` 106→114、`proved_pct` 10.09→10.85（实算 114/1051=10.8468…%，保留两位）；`atlas_n` 1051 及 named/strict 各列不动；在 DoD差距说明（备注）末尾追加 M58 并表说明：
   > M58 并表 S09_KPROVED8 8 行（004888B0/00488910/00488980/006539D0/006D0A20/00565AA0/00771900/0049FB40，[静态推断]→[已证]，第 4 列语义取 delta 原文、evidence_path 改指 S09_KPROVED8/_audit/VERDICT.md；8 行经异族审计 8/8 PASS；均 atlas 内，atlas 外已证仍 5 行；coverage 18,498 行不变；proved_pct 按实算 114/1051=10.8468…% 保留两位取 10.85）

2. **严格口径双列表 S09 行（原 L113）**：`proved_n` 106→114、`proved_pct` 10.09→10.85（同一实算值）；`proved_strict_n=89` 等其余列不动。

3. **M47 全表同步表 S09 行（原 L176，插入指针后变为 L177）**：`proved_n` 106→114；其余列不动。

4. **TOTAL 行（原 L77）**：`proved_n` 1,476→1,484、`proved_pct` 11.43→11.49（实算 1,484/12,916=11.4896…%，保留两位）；备注开头加：
   > M58 +8（S09_KPROVED8 8 行全 atlas 内）：全表 [已证] 1,481→1,489、atlas 内 1,476→1,484，TOTAL proved_pct 11.43→11.49（实算 1,484/12,916=11.4896%→11.49）；named/L/strict 各列不变。

5. **L138 之后插入一行指针（只增不改）**：
   > 📌 **界向更正（M58）**：上面 L134/L138 把 `proved_strict` 说成「下界」**方向标反**——它是**上界**。证明与两个反例见 `BOUND_DIR\REPORT.md`；本表内所有把该列当达标证据的读数，一律以该报告 §4 的改述为准。

L132–L138 原文逐字节未动（已逐行复核）；该指针为 L138 之后新插入的一行，其后所有行号顺移 +1（原 L176 S09 行现为 L177）。`BOUND_DIR/REPORT.md` 盘上存在，指针指向有效。

面板实算说明：S09 的 `n=1051` 按卡片给定口径（coverage ∩ function_atlas，大小写归一，按子系统计数）盘上复核确为 1,051，未改。百分比 10.85 与 11.49 均为实算值（114/1051、1484/12916），非照抄卡片印象值。

## 实测新值（并表后）

- `coverage.tsv` 数据行：**18,498**（不变）；全表 `[已证]`：**1,489**；atlas 内 `[已证]`：**1,484**；atlas 外已证 **5**（不变）。
- 8 行 grade：全部 `[已证]`；evidence_path 全部 `S09_KPROVED8/_audit/VERDICT.md`。
- S09 行数：coverage 全表 1,102；coverage ∩ atlas **1,051**（面板 n，未改）。
- S09 `[已证]`：全表 **114**、atlas 内 **114**（改前 106，+8）。
- 面板 S09 proved_pct **10.85**、TOTAL proved_pct **11.49**（均实算、两位）。

## 边界与纪律

- 未新增/删除 entry；未重排、未美化、未顺手修别处错字；第 7/8 列一字未动。
- 未 git commit；未碰 `R14_COMMON.md`、`STATUS_BOARD.md`、`CONFLICTS.tsv`、`PENDING_CORRECTIONS.tsv`。
- 本轮仅本卡持有 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md` 写权，未写其它卡目录。
- 两文件改前/改后 mtime、字节数、sha256 见 `BEFORE_AFTER.txt`；并表后重算见 `VERIFY.txt`。
