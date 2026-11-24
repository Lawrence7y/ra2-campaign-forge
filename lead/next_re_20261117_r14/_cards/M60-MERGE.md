# M60-MERGE — 并表 SEMFIX 34 行语义改写 + 修正面板旧截面

## 独占写权声明

本轮**只有你**可以写 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md`。
**不许** git commit；**不许**碰 `R14_COMMON.md`、`STATUS_BOARD.md`、`CONFLICTS.tsv`、`PENDING_CORRECTIONS.tsv`、任何 `SEMFIX_ENGFAM_B*` 或 `S15S16_3B2` 目录。

## 改动前必做

对两个目标文件各记 `mtime`、字节数、`sha256`；改完再记一次，两组写进 `MERGE_M60\BEFORE_AFTER.txt`。

---

# 第一部分：并表 34 行语义改写（**不改 grade**）

## 并什么

- `SEMFIX_ENGFAM_B1\coverage_delta.tsv`：17 行
- `SEMFIX_ENGFAM_B2\coverage_delta.tsv`：17 行
- 合计 **34 行**，6 列

## 前置条件（已由 Lead 核过，若你复现出不同结果就停下报告）

- 34 行、34 个唯一 entry、`entry` 全为 8 位大写十六进制无 `0x` 前缀
- 34 行**全部已在 `coverage.tsv` 中**，当前 grade **全部已是 `[已证]`**
- 34 行**全部在 atlas 内**
- 审计：B1 `_audit\verdict.tsv` 17 行全 PASS；B2 `_audit\verdict.tsv` 17 行全 PASS（FAIL 集合为空）

## 改什么

**只改 2 列**：

- 第 4 列 `one_line_semantics` ← delta 第 4 列**原文照抄**（不许改写、不许截断）
- 第 6 列 `evidence_path` → `SEMFIX_ENGFAM_B1/_audit/VERDICT.md`（B1 的 17 行）或 `SEMFIX_ENGFAM_B2/_audit/VERDICT.md`（B2 的 17 行），按该行来自哪个批次填

**第 5 列 `grade` 保持 `[已证]` 不动**（这次是依据改写，不是升格）。
**第 1、2、3、7、8 列一个字都不许动。**
数据行仍 **18,498**、仍 8 列、制表符分隔。

## 并后必须成立的数

- 全表 `[已证]` **仍为 1,496**
- atlas 内 `[已证]` **仍为 1,490**、atlas 外 **仍为 6**
- 全表语义匹配 `(?i)unproven|unverified|not proven` 的行数：**34 → 0**

---

# 第二部分：修正 PANEL 那张「严格双列」表的旧截面

## 问题

`PANEL.md` 中那张含列 `subsystem | n | proved | proved% | strict | strict% | proved门槛 | proved判定 | strict判定` 的表（约 L105–L127），**多行是旧截面**，未随 M55/M58 更新。Lead 已按盘上重算过一轮，你得出的数必须与下表一致；**若不一致，停下来报告，不要按任何一方硬改**。

| 子系统 | atlas 内 proved | atlas 内 strict |
|---|---:|---:|
| S02 | 35 | 5 |
| S09 | 114 | **97** |
| S13 | **100** | **99** |
| S15 | 106 | 53 |
| S16 | 47 | 21 |
| S17 | 56 | 55 |
| S19 | **27** | **18** |

- 加粗者为与现面板不一致、必须改的格
- 其余子系统（S01、S03–S08、S10–S12、S14、S18、S20–S22）也要**逐行重算核对**，若也有旧截面一并改，并在日志里列出
- 重算口径（严格照此，别自创）：
  - `n` = 该 subsystem 且 entry 在 `function_atlas.tsv` 内的行数（atlas 的 `entry` 是**小写**，必须大小写归一）
  - `proved` = 上述行中 grade `== [已证]` 的
  - `strict` = 上述行中 grade `== [已证]` **且** 语义串**不含** `未证` 的
- 判定列按新值重算：`proved判定` = proved ≥ `ceil(0.5n)`；`strict判定` = strict ≥ `ceil(0.5n)`；达成写 `达标`，未达写 `—`（沿用现表写法）
- 百分比按新值重算，保留两位小数

## 必须回答的一个问题（写进日志）

> 修正后，**有没有任何子系统的「达标」判定发生翻转**？

预期是「没有」。若你算出有翻转，**立刻停下报告**，不要改表。

## 追加说明

在该表之后追加一行注：

```
> 📌 **M60 旧截面修正**：本表 S13/S19 两行的 proved 与 strict、S09 的 strict 曾停留在 M55/M58 之前的截面（分别落后 11 / 7 / 8 行），已按盘上重算更正；修正后达标判定未发生翻转（严格口径仍仅 S17）。教训记入错源 ㉙（引用旧截面）。
```

---

## 交付

- `MERGE_M60\MERGE_LOG.md`：逐项改动、34 行 entry 清单、面板逐行改前改后值
- `MERGE_M60\BEFORE_AFTER.txt`：两文件 mtime/字节/sha256 前后
- `MERGE_M60\VERIFY.txt`：并后重算——数据行数、全表/atlas 内/atlas 外 `[已证]`、`unproven` 族行数（须为 0）、面板 22 行逐行新值、"有无翻转"结论

## 纪律

- 只改点名位置；盘上现值与卡片不符 ⇒ **停下报告**。
- 不许重排、不许美行、不许顺手改别处。
- 34 行的 `grade` 一个字都不许动。
