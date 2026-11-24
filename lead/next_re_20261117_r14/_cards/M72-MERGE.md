# M72-MERGE — 并表 11 行（S07 七 + S11 四，均已审 PASS）

## 独占写权

本轮**只有你**可以写 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md`。
不许 git commit；不许碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT*`、`INVENTORY`、`BOARD_ARCHIVE.md`。

改动前记两文件 `mtime`/字节/`sha256`，改后再记，写进 `MERGE_M72\BEFORE_AFTER.txt`。

## 并什么（11 行）

| 组 | 审计表 | delta 来源 | 应并行数 |
|---|---|---|---:|
| A | `NAMED_PUSH_AUDIT13\verdict.tsv` | `NAMED_PUSH_S07_B1\delta.tsv` | **7** |
| B | `NAMED_PUSH_AUDIT14\verdict.tsv` | `NAMED_PUSH_S11_B1\delta.tsv` | **4** |

交集必须正好 7 + 4；不是就**停下报告**。

**不进并表**：`NAMED_PUSH_S09_B1\delta.tsv` 的 1 行——**尚未经异族审计**，留在池里。

## Lead 已核过的前置（不符就停下）

- 现盘上：数据行 **18,498**、全表 `[已证]` **1,602**、atlas 内 **1,596**、atlas 外 **6**
- S07、S11 的 atlas 内 proved 自己重算核对
- 11 行 atlas 内与否自己核（`entry` 小写须归一）

## 改什么

`coverage.tsv` 这 11 行各改 3 列：第 4 列语义 ← delta 原文；第 5 列 → `[已证]`；第 6 列 → A 组 `NAMED_PUSH_AUDIT13/VERDICT.md`、B 组 `NAMED_PUSH_AUDIT14/VERDICT.md`。
第 1、2、3、7、8 列不动。数据行仍 18,498、8 列、制表符分隔。

## `PANEL.md` 同步

- S07、S11 的 atlas 内 proved 按实算更新
- 全表 `[已证]` **1,602 → 1,613**；atlas 内 **1,596 → 1,607**（若全在 atlas 内）
- 严格双列表按权威口径（`[未证]` 字面）
- 备注列追加：`M72 并表 NAMED_PUSH_AUDIT13 PASS 7 行（S07）+ NAMED_PUSH_AUDIT14 PASS 4 行（S11），evidence_path 分别改指两审计 VERDICT；S09_B1 的 1 行未审不并`
- **达标判定不得改变**；若翻转，**停下报告**

## 追加一条㉓的正向记录（写进 PANEL 备注即可，不必单列披露）

`S07 有 2 行真触发㉓陷阱（同一虚表也被析构器写入 00490406 / 006DC475），因执行器 ④ 锚点取在行外构造器（0048E93B / 006D1D54）而未触雷 ⇒ ㉓ 不是形式检查，是真会命中的判据。`

## 交付

- `MERGE_M72\MERGE_LOG.md`、`BEFORE_AFTER.txt`、`VERIFY.txt`
- `VERIFY.txt` 必须含：两组并行数（7+4）、数据行数、全表/atlas 内/atlas 外 `[已证]`、S07/S11 的 proved 与 strict、**有无达标翻转**、`S09_B1` 那 1 行 grade **未变**
