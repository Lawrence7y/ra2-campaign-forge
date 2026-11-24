# M64-MERGE — 并表 10 行审计 PASS

## 独占写权

本轮**只有你**可以写 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md`。
不许 git commit；不许碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT*`。

改动前记两文件 `mtime`/字节/`sha256`，改后再记，写进 `MERGE_M64\BEFORE_AFTER.txt`。

## 并什么：**10 行**（审计 PASS）

审计表：`NAMED_PUSH_AUDIT2\verdict.tsv`（11 行、8 列，第 3 列 `verdict`）。

| entry | 子系统 | delta 来源 |
|---|---|---|
| `00691EE0` | S14 | `NAMED_PUSH_S14_B2` |
| `00691FA0` | S14 | `NAMED_PUSH_S14_B2` |
| `006A4930` | S14 | `NAMED_PUSH_S14_B2` |
| `006E87F0` | S14 | `NAMED_PUSH_S14_B2` |
| `006E9140` | S14 | `NAMED_PUSH_S14_B2`（③b①，65 路跳表） |
| `00410C30` | S05 | `NAMED_PUSH_S05_B1` |
| `00414290` | S05 | `NAMED_PUSH_S05_B1` |
| `0041CFE0` | S05 | `NAMED_PUSH_S05_B1` |
| `00524D70` | S05 | `NAMED_PUSH_S05_B2` |
| `005F9950` | S05 | `NAMED_PUSH_S05_B2` |

**FAIL 1 行整行拒绝，一个字不许改**：`006A48A0`（第 4 列把 `00410320` 的「流写出」写成「流读入」，读写方向反了）。

**另有一行不进本次并表**：`00748190`（`NAMED_PUSH_S05_B3` 产出）——它**尚未经异族审计**，本轮**不许并**，留在池里等下一张审计卡。

以你交叉核出的 PASS 集合为准，**必须核出 10 行**；不是 10 行就**停下报告**。

## Lead 已核过的前置（不符就停下）

- 10 行当前 grade **全部是 `[静态推断]`**
- 10 行**全部在 atlas 内**（atlas `entry` 为小写，比对须归一）
- 现盘上：数据行 **18,498**、全表 `[已证]` **1,502**、atlas 内 **1,496**、atlas 外 **6**、S18（atlas 内）**56**、S14（atlas 内）**111**、S05（atlas 内）**165**

## 改什么

`coverage.tsv` 这 10 行只改 3 列：

- 第 4 列语义 ← 对应 delta 第 4 列**原文照抄**
- 第 5 列 `grade` → `[已证]`
- 第 6 列 `evidence_path` → `NAMED_PUSH_AUDIT2/VERDICT.md`

第 1、2、3、7、8 列不动。数据行仍 18,498、8 列、制表符分隔。

## `PANEL.md` 同步

- S14：atlas 内 proved **111 → 116**；S05：**165 → 170**（按你实算值写）
- 全表 `[已证]` **1,502 → 1,512**；atlas 内 **1,496 → 1,506**；atlas 外仍 **6**
- 严格双列表相应行按新值更新；`proved_strict` 是否同增按你实算（若新并入行语义不含 `未证` 则同增）
- 备注列追加：`M64 并表 NAMED_PUSH_AUDIT2 审计 PASS 10 行（S14 00691EE0/00691FA0/006A4930/006E87F0/006E9140 + S05 00410C30/00414290/0041CFE0/00524D70/005F9950，均 atlas 内，evidence_path 改指 NAMED_PUSH_AUDIT2/VERDICT.md；同卡 006A48A0 审计 FAIL 整行拒绝；00748190 未审不并）`
- **达标判定不得改变**（严格仍仅 S17）；若你算出翻转，**停下报告**

## 额外要记的一条限定（写进备注）

审计员对 S14 那批 5 行中的**析构型**（`00691EE0`/`00691FA0`/`006A4930`/`006E87F0` 一类）给出限定：其 ③b② 属**模板级低信息量**——靠全局 `DynamicVectorClass<T*>` 容器 `Find` 返 `-1` 哨兵分支成立，与台账既有 6 行同型（含 M59 的 `006E4660`）一致。请在备注里加一句：

`〔模板级低信息量 ③b②：析构体内容器 Find 返 -1 哨兵分支成立；与既有 6 行同型，未收紧口径〕`

## 交付

- `MERGE_M64\MERGE_LOG.md`、`BEFORE_AFTER.txt`、`VERIFY.txt`
- `VERIFY.txt` 必须含：数据行数、全表/atlas 内/atlas 外 `[已证]`、S14 与 S05 的 proved、10 行新 grade、`006A48A0` 与 `00748190` 两行 grade **未变**、**有无达标翻转**
