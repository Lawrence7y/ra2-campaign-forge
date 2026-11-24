# M66-MERGE — 并表 29 行（S22 十八 + S06 四 + S20 七，均已审 PASS）

## 独占写权

本轮**只有你**可以写 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md`。
不许 git commit；不许碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT*`。

改动前记两文件 `mtime`/字节/`sha256`，改后再记，写进 `MERGE_M66\BEFORE_AFTER.txt`。

## 并什么（合计 29 行）

| 组 | 审计表 | delta 来源 | 应并行数 |
|---|---|---|---:|
| A | `NAMED_PUSH_AUDIT6\verdict.tsv` | `NAMED_PUSH_S22_B2\delta.tsv` | **18** |
| B | `NAMED_PUSH_AUDIT5\verdict.tsv` | `NAMED_PUSH_S06_B1\delta.tsv` + `NAMED_PUSH_S20_B1\delta.tsv` | **4 + 7 = 11** |

**做法**：对每一组，把审计表里 `verdict == PASS` 的 entry 取出来，与对应 `delta.tsv` 的 entry 做交集；交集就是该组应并的行。**三组数必须分别是 18、4、7**；若不符，**停下报告**，不要按任何一方的数字硬改。

若某个 PASS entry 在 delta 里找不到，或 delta 里有 entry 不在审计 PASS 集合里，**都要停下来报告**。

## Lead 已核过的前置（不符就停下）

- 现盘上：数据行 **18,498**、全表 `[已证]` **1,527**、atlas 内 **1,521**、atlas 外 **6**
- 当前各子系统 atlas 内 proved：S22 **69**、S06 **126**、S20 **46**（自己重算核对）
- 待并 29 行**应全部在 atlas 内**（atlas `entry` 为小写，比对须归一）；若有 atlas 外的行，**单独列出**并在日志里标明"A 口径不计"

## 改什么

`coverage.tsv` 这 29 行各改 3 列：

- 第 4 列语义 ← 对应 delta 第 4 列**原文照抄**
- 第 5 列 `grade` → `[已证]`
- 第 6 列 `evidence_path` → A 组填 `NAMED_PUSH_AUDIT6/VERDICT.md`；B 组填 `NAMED_PUSH_AUDIT5/VERDICT.md`

第 1、2、3、7、8 列不动。数据行仍 18,498、8 列、制表符分隔。

## `PANEL.md` 同步

- S22、S06、S20 的 atlas 内 proved 按你实算更新（预期 S22 69→87、S06 126→130、S20 46→53，**以实算为准**）
- 全表 `[已证]` **1,527 → 1,556**；atlas 内 **1,521 → 1,550**（若全是 atlas 内）；atlas 外仍 6
- 严格双列表按 **权威口径** 重算：`proved_strict` = atlas 内 ∧ `[已证]` ∧ 语义**不含字面 `[未证]`**（**注意：是带方括号的字面，不是裸「未证」**，见 `RULING_R15_20261119\work\strict_panel.py` 第 78 行）
- 备注列追加：`M66 并表 NAMED_PUSH_AUDIT6 PASS 18 行（S22 TClassFactory 同族）+ NAMED_PUSH_AUDIT5 PASS 11 行（S06 4 + S20 7），evidence_path 分别改指两审计 VERDICT；strict 按权威口径 [未证] 字面重算`
- **达标判定不得改变**（严格仍仅 S17）；若你算出翻转，**停下报告**

## 交付

- `MERGE_M66\MERGE_LOG.md`、`BEFORE_AFTER.txt`、`VERIFY.txt`
- `VERIFY.txt` 必须含：三组实际并行数（18/4/7）、数据行数、全表/atlas 内/atlas 外 `[已证]`、S22/S06/S20 的 proved 与 strict、**有无达标翻转**、以及 **strict 用的是 `[未证]` 字面口径的证据**
