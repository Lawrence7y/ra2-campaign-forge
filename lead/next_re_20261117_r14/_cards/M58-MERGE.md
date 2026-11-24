# M58-MERGE — 并表 S09_KPROVED8 八行 + 面板加固

## 独占写权声明

本轮**只有你**可以写 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md`。其它卡都在只读或只写自己目录。
**不许 git commit**、不许碰 `R14_COMMON.md`、`STATUS_BOARD.md`、`CONFLICTS.tsv`、`PENDING_CORRECTIONS.tsv`。

## 改动前必做（先记录，后动手）

对 `coverage.tsv` 与 `PANEL.md` 各记录：`mtime`、字节数、`sha256`。
改动后再记录一次，并把两组值写进 `MERGE_M58\BEFORE_AFTER.txt`。

## 待并内容

来源：`S09_KPROVED8\coverage_delta.tsv`（6 列，表头 `entry / subsystem / name / one_line_semantics / grade / evidence_path`，8 行数据）。

**前置条件（已由 Lead 独立核过，你若复现出不同结果就停下来报告，不要硬改）**：

- 审计结论：`S09_KPROVED8\_audit\verdict.tsv`，8 行全部 `PASS`（表头 3 列、8 行数据）。
- 8 个 entry 全部已存在于 `coverage.tsv`，当前 grade 全为 `[静态推断]`；**本次是原地升格，不新增行**。
- 8 个 entry 全部在 `function_atlas.tsv` 内（该表 `entry` 列为**小写十六进制**，比较时必须大小写归一，否则会误判为 atlas 外）。
- 并表前盘上：`coverage.tsv` 数据行 **18,498**；全表 `[已证]` **1,481**；atlas 内 `[已证]` **1,476**。

## 要做的改动

1. `coverage.tsv` 中这 8 行，只改 3 列：
   - 第 4 列 `one_line_semantics` ← delta 第 4 列原文（**逐字照抄，不许改写、不许截断**）
   - 第 5 列 `grade`：`[静态推断]` → `[已证]`
   - 第 6 列 `evidence_path` → `S09_KPROVED8/_audit/VERDICT.md`
   - **第 7、8 列一个字都不许动**；第 1、2、3 列也不许动（name 保持不变，`ColorListClass::slot43` 这类 slotN 名字**不是**改名，不许"顺手规范"）。
   - 行数必须仍是 18,498，数据行仍是 8 列、制表符分隔。

2. `PANEL.md` 三处 S09 C 行同步（按现有值定位，别按我给的印象改）：
   - 现值特征：`S09 | 1051 | ... | 106 | 10.09`
   - 改为：proved `106` → `114`，百分比 `10.09` → `10.86`（114/1051 = 10.846…，保留两位 10.85 或 10.86 都行，但**必须按你实算值写并注明是实算**）
   - 在这些行的备注里追加：`M58 并表 S09_KPROVED8 8 行（004888B0/00488910/00488980/006539D0/006D0A20/00565AA0/00771900/0049FB40，[静态推断]→[已证]，第 4 列语义取 delta 原文、evidence_path 改指 S09_KPROVED8/_audit/VERDICT.md；8 行经异族审计 8/8 PASS；均 atlas 内，atlas 外已证仍 5 行；coverage 18,498 行不变）`
   - **不许**把 S09 的 `n=1051` 改成别的数 —— 已核实 `n` 的口径是「`coverage` ∩ `function_atlas`（大小写归一）按子系统计数」，22 个子系统逐字相等，1,051 是对的。

3. `PANEL.md` 全表已证数同步：全表 `[已证]` `1,481` → `1,489`；atlas 内 `[已证]` `1,476` → `1,484`。TOTAL 行的 proved 计数与百分比按你实算值更新，并注明 M58。

4. 在 `PANEL.md` 的 **L138 之后**插入一行指针（**只增不改，不许改动 L132–L138 任何原文**）：

```
> 📌 **界向更正（M58）**：上面 L134/L138 把 `proved_strict` 说成「下界」**方向标反**——它是**上界**。证明与两个反例见 `BOUND_DIR\REPORT.md`；本表内所有把该列当达标证据的读数，一律以该报告 §4 的改述为准。
```

## 纪律

- 只改上面点名的位置。若发现盘上现值与我写的"现值特征"不一致，**停下来报告**，不要按记忆改。
- 不许重排、不许美行、不许顺手修别处的错字。
- 交付：`MERGE_M58\MERGE_LOG.md`（改了什么、逐行 entry、实测新值）、`MERGE_M58\BEFORE_AFTER.txt`（两文件的 mtime/字节/sha256 前后对照）、`MERGE_M58\VERIFY.txt`（并表后重算：数据行数、全表 `[已证]`、atlas 内 `[已证]`、8 行新 grade、S09 行数、S09 `[已证]` 数）。
