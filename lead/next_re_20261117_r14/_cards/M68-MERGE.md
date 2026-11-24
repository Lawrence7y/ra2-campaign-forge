# M68-MERGE — 并表 S12 四行（已审 PASS 4/0）

## 独占写权

本轮**只有你**可以写 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md`。
不许 git commit；不许碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT*`、`RESCAN_MOVED`。

改动前记两文件 `mtime`/字节/`sha256`，改后再记，写进 `MERGE_M68\BEFORE_AFTER.txt`。

## 并什么：4 行

- 审计表：`NAMED_PUSH_AUDIT8\verdict.tsv`（4 行、8 列，全部 PASS）
- delta 来源：`NAMED_PUSH_S12_B1\delta.tsv`
- entry：`00442230`、`00447210`、`00447F10`、`0044E8F0`

**交集必须正好 4 行**；不是就**停下报告**。

## Lead 已核过的前置（不符就停下）

- 4 行当前 grade **全部为 `[静态推断]`**
- 现盘上：数据行 **18,498**、全表 `[已证]` **1,569**、atlas 内 **1,563**、atlas 外 **6**、S12（atlas 内 proved）**55**
- 4 行在 atlas 内与否**自己核**（atlas `entry` 为小写，须归一）；atlas 外的行单独列出并标"A 口径不计"

## 改什么

`coverage.tsv` 这 4 行各改 3 列：

- 第 4 列语义 ← delta 第 4 列原文照抄
- 第 5 列 `grade` → `[已证]`
- 第 6 列 `evidence_path` → `NAMED_PUSH_AUDIT8/VERDICT.md`

第 1、2、3、7、8 列不动。数据行仍 18,498、8 列、制表符分隔。

## `PANEL.md` 同步

- S12（atlas 内 proved）**55 → 59**（以你实算为准）
- 全表 `[已证]` **1,569 → 1,573**；atlas 内 **1,563 → 1,567**（若全是 atlas 内）
- 严格双列表按**权威口径**：`proved_strict` = atlas 内 ∧ `[已证]` ∧ 语义**不含字面 `[未证]`**（`strict_panel.py:78`）
- 备注列追加：`M68 并表 NAMED_PUSH_AUDIT8 PASS 4 行（S12 00442230/00447210/00447F10/0044E8F0，evidence_path 改指 NAMED_PUSH_AUDIT8/VERDICT.md；00447210 与 00447F10 的 ③ 站点为「返回值搬入 ebx/ebp 再判」，审计独立枚举被调全部 ret 确认为多值状态码 {0,4,5,7,8,0x1A,0x37} 与 {0,1,3,5,6,8,9}，非 {0,1} 布尔）`
- **达标判定不得改变**（严格仍仅 S17）；若你算出翻转，**停下报告**

## 交付

- `MERGE_M68\MERGE_LOG.md`、`BEFORE_AFTER.txt`、`VERIFY.txt`
- `VERIFY.txt` 必须含：并行数、数据行数、全表/atlas 内/atlas 外 `[已证]`、S12 的 proved 与 strict、**有无达标翻转**
