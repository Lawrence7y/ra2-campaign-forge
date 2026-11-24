# M67-MERGE — 并表 13 行（S20 八 + S06 五，均已审 PASS）

## 独占写权

本轮**只有你**可以写 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md`。
不许 git commit；不许碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT*`、`RESCAN_MOVED`。

改动前记两文件 `mtime`/字节/`sha256`，改后再记，写进 `MERGE_M67\BEFORE_AFTER.txt`。

## 并什么（13 行）

- 审计表：`NAMED_PUSH_AUDIT7\verdict.tsv`（13 行、8 列，第 3 列 `verdict`，全部 PASS）
- delta 来源：`NAMED_PUSH_S20_B2\delta.tsv`（8 行）+ `NAMED_PUSH_S06_B3\delta.tsv`（5 行）

**做法**：把审计表 `verdict == PASS` 的 entry 取出，与两个 delta 的 entry 做交集；**交集必须正好 13 行（S20 8 + S06 5）**。不是 13 行就**停下报告**。

**不进本次并表**：`NAMED_PUSH_S12_B1` 的 4 行——它们的审计代理失败（未产出），**尚未过审**，留在池里。

## 两条必须落实的审计勘误

审计员报了两类问题，并表时**必须一并处理**：

1. **`0062FE90` 的 ④ 引用死表**：它引的 `007E9D84` 是析构器写的死表，**活表应为 `007E9D64` → `Find 004EA010`**。这是**事实错误**，若 delta 第 4 列写了 `007E9D84`，**必须改字**为 `007E9D64`，并在备注注明「M67 按审计勘误改表址」。
2. **S06 五行原 delta 无 ④**：审计员替执行器补了 5 条 ④。若 delta 第 4 列**缺 ④**，请在照抄的基础上**不改执行器原文**，而在备注里记：`M67 备注：S06 五行 ④ 由 a-S20S06 审计补证，见 NAMED_PUSH_AUDIT7\VERDICT.md`。

## Lead 已核过的前置（不符就停下）

- 现盘上：数据行 **18,498**、全表 `[已证]` **1,556**、atlas 内 **1,550**、atlas 外 **6**
- S20（atlas 内 proved）**53**、S06 **130**（自己重算核对）
- 13 行**应全部在 atlas 内**；若有 atlas 外的，**单独列出**并标"A 口径不计"

## 改什么

`coverage.tsv` 这 13 行各改 3 列：

- 第 4 列语义 ← 对应 delta 第 4 列原文照抄（**`0062FE90` 的表址按上面第 1 条改字**）
- 第 5 列 `grade` → `[已证]`
- 第 6 列 `evidence_path` → `NAMED_PUSH_AUDIT7/VERDICT.md`

第 1、2、3、7、8 列不动。数据行仍 18,498、8 列、制表符分隔。

## `PANEL.md` 同步

- S20 atlas 内 proved **53 → 61**、S06 **130 → 135**（以你实算为准）
- 全表 `[已证]` **1,556 → 1,569**；atlas 内 **1,550 → 1,563**
- 严格双列表按**权威口径**重算：`proved_strict` = atlas 内 ∧ `[已证]` ∧ 语义**不含字面 `[未证]`**（`strict_panel.py:78`）
- 备注列追加：`M67 并表 NAMED_PUSH_AUDIT7 PASS 13 行（S20 8 + S06 5，evidence_path 改指 NAMED_PUSH_AUDIT7/VERDICT.md）；0062FE90 表址按审计勘误改为 007E9D64；S06 五行 ④ 由审计补证；S12_B1 四行审计代理失败未审不并`
- **达标判定不得改变**（严格仍仅 S17）；若你算出翻转，**停下报告**

## 交付

- `MERGE_M67\MERGE_LOG.md`、`BEFORE_AFTER.txt`、`VERIFY.txt`
- `VERIFY.txt` 必须含：实际并行数（8+5）、数据行数、全表/atlas 内/atlas 外 `[已证]`、S20/S06 的 proved 与 strict、**有无达标翻转**、以及 `0062FE90` 表址已改的证据
