# M63-MERGE — 并表 6 行审计 PASS 的 proved 增量

## 独占写权

本轮**只有你**可以写 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md`。
不许 git commit；不许碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT`。

## 改动前必做

两文件各记 `mtime`、字节、`sha256`；改完再记一次，写进 `MERGE_M63\BEFORE_AFTER.txt`。

## 并什么：**只并审计 PASS 的 6 行**

审计表：`NAMED_PUSH_AUDIT\verdict.tsv`（8 行数据、8 列，第 3 列 `verdict`）。

**PASS 6 行**（来源：S18 B1/B2 与 S14 B1 三批的 `delta.tsv`）：

| entry | 子系统 | delta 来源目录 |
|---|---|---|
| `005414C0` | S18 | `NAMED_PUSH_S18_B1` |
| `0071F8C0` | S18 | `NAMED_PUSH_S18_B2` |
| `0041F580` | S14 | `NAMED_PUSH_S14_B1` |
| `00503040` | S14 | `NAMED_PUSH_S14_B1` |
| `00512290` | S14 | `NAMED_PUSH_S14_B1` |
| `00512480` | S14 | `NAMED_PUSH_S14_B1` |

**FAIL 2 行整行拒绝，一个字都不许改**：

- `005C46E0`（④ 锚点 `005C164A` 实为析构器 `005C1640`，违反 ㉓）
- `0065AC40`（第 4 列把 `00410320` 的写出语义写成「流读入」，读写方向反）

以你从审计表交叉核出的 PASS 集合为准，**必须核出 6 行**；不是 6 行就**停下报告**。

## Lead 已核过的前置（不符就停下）

- 6 行当前 grade：`0071F8C0` 为 `[未证]`，其余 5 行为 `[静态推断]`
- 6 行**全部在 atlas 内**（atlas `entry` 为小写，比对须归一）
- 现盘上：数据行 **18,498**、全表 `[已证]` **1,496**、atlas 内 **1,490**、S18（atlas 内）**54**、S14（atlas 内）**107**

## 改什么

`coverage.tsv` 这 6 行只改 3 列：

- 第 4 列语义 ← 对应 delta 第 4 列**原文照抄**
- 第 5 列 `grade` → `[已证]`
- 第 6 列 `evidence_path` → `NAMED_PUSH_AUDIT/VERDICT.md`

第 1、2、3、7、8 列不动。数据行仍 18,498、仍 8 列、制表符分隔。

## `PANEL.md` 同步

- S18：atlas 内 proved **54 → 56**；S14：**107 → 111**（按你实算值写，两位小数百分比自行重算）
- 全表 `[已证]` **1,496 → 1,502**；atlas 内 **1,490 → 1,496**；atlas 外仍 **6**
- 严格双列表相应行的 proved 按新值更新（`proved_strict` 是否同步变化，**按你实算**：若新并入行的语义串不含 `未证`，则 strict 同增）
- 备注列追加：`M63 并表 NAMED_PUSH 审计 PASS 6 行（S18 005414C0/0071F8C0 + S14 0041F580/00503040/00512290/00512480，均 atlas 内，evidence_path 改指 NAMED_PUSH_AUDIT/VERDICT.md；同卡 005C46E0/0065AC40 审计 FAIL 整行拒绝），来源批次 NAMED_PUSH_S18_B1/B2 与 S14_B1`
- **达标判定不得改变**（严格仍仅 S17）。若你算出翻转，**停下报告**

## 交付

- `MERGE_M63\MERGE_LOG.md`、`BEFORE_AFTER.txt`、`VERIFY.txt`
- `VERIFY.txt` 必须含：数据行数、全表/atlas 内/atlas 外 `[已证]`、S18 与 S14 的 proved、6 行新 grade、2 行 FAIL 行 grade 未变、**有无达标翻转**
