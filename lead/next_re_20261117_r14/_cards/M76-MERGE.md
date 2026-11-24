# M76-MERGE — 并表 11 行（final7 七 + S07S11 四）+ 三处改字 + 第六条披露

## 独占写权

本轮**只有你**可以写 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md`。
不许 git commit；不许碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`BOARD_ARCHIVE.md`、任何 `NAMED_PUSH_*` 与 `AUDIT*`、`INVENTORY*`。

改动前记两文件 `mtime`/字节/`sha256`，改后再记，写进 `MERGE_M76\BEFORE_AFTER.txt`。

## 并什么（11 行）

| 组 | 审计表 | delta 来源 | 应并行数 |
|---|---|---|---:|
| A | `NAMED_PUSH_AUDIT19\verdict.tsv` | `NAMED_PUSH_S06_B2\delta.tsv`（3）+ `NAMED_PUSH_S01S03_B1\delta.tsv`（1）+ `NAMED_PUSH_S16S21_B1\delta.tsv`（3） | **7** |
| B | 待审（见下） | `NAMED_PUSH_S07S11_B2\delta.tsv` | **4** |

⚠️ **B 组的 4 行尚未经异族审计**（`NAMED_PUSH_S07S11_B2` 刚产出）。**本轮只并 A 组 7 行**；若你发现 B 组已有审计表就一并以停下报告为准。

**A 组 7 行 entry**：`005FEAF0`、`006B5850`、`0071CDA0`、`00432050`、`0046D000`、`0046D090`、`0071B1B0`

## 并表时必须改的三处字（审计员点名，非致命但必须改）

1. **`0071B1B0` 的槽址笔误**：delta 写 `0071B1A0`，**应为 `007F51A0`** ⇒ 第 4 列照抄时把该串改对，并在备注记「M76 按审计勘误改槽址」
2. **`0071CDA0` 的 `ff 51 10` 误称**：delta 称之为「读入」，实为**成员容器 slot4 下标查询** ⇒ 第 4 列照抄时改为「成员容器 slot4 下标查询（非读入）」
3. 其余 5 行照抄原 delta

## Lead 已核过的前置（不符就停下）

- 现盘上：数据行 **18,498**、全表 `[已证]` **1,643**、atlas 内 **1,637**、atlas 外 **6**
- 7 行 atlas 内与否自己核（`entry` 小写须归一）
- 当前 atlas 内 proved：S03、S06、S16、S21 自己重算

## 改什么

`coverage.tsv` 这 7 行各改 3 列：第 4 列语义 ← delta 原文（含上述两处改字）；第 5 列 → `[已证]`；第 6 列 → `NAMED_PUSH_AUDIT19/VERDICT.md`。
第 1、2、3、7、8 列不动。数据行仍 18,498、8 列、制表符分隔。

## `PANEL.md` 同步

- S03、S06、S16、S21 的 atlas 内 proved 按实算更新（预期 S03 +1、S06 +3、S16 +1、S21 +2）
- 全表 `[已证]` **1,643 → 1,650**；atlas 内 **1,637 → 1,644**（若全在 atlas 内）
- 严格双列表按权威口径（`[未证]` 字面）
- 备注列追加：`M76 并表 NAMED_PUSH_AUDIT19 PASS 7 行（S06_B2 3 + S01S03 1 + S16S21 3，evidence_path 改指 NAMED_PUSH_AUDIT19/VERDICT.md；0071B1B0 槽址按勘误改 007F51A0、0071CDA0 的 ff 51 10 改称成员容器 slot4 下标查询）；NAMED_PUSH_S07S11_B2 的 4 行未审不并`
- **达标判定不得改变**；若翻转，**停下报告**

## 必须追加的第六条披露（**原样写入**）

接在 M75 披露之后：

```
> ⚠️ **M76 披露：析构体内 Find −1 形态成族同构、族内区分力≈0（待裁，未收紧）**
> `a-final7` 审计指出：`0046D090`（S21 CampaignClass slot8 删除析构器）、`0071B1B0`（S16 TemporalClass slot8 删除析构器）等行的 ③b② 靠「析构体内容器 `Find` 返 −1 哨兵 → `cmp`/`je` 真实消费」成立；字节上成立，但该形态在引擎里**成族同构**（本批 3 个不同类的槽8 析构器逐指令同构），**族内区分力≈0**。
> 另：这 3 行中 2 行的主体本身就是删除析构器；㉓ 只禁止用析构器作 ④ 锚点，未禁止其作主体，故不判 FAIL。
> **Lead 处置：按现行成文规则（D-42 ② + 「Find 返 −1 下标约定算」）判 PASS，但披露该族区分力问题。若日后收紧，须一次性整批翻转（含 `NAMED_PUSH_AUDIT18` 的 2 行与 S14 的 4 行），不得零散改判。**
```

## 交付

- `MERGE_M76\MERGE_LOG.md`、`BEFORE_AFTER.txt`、`VERIFY.txt`
- `VERIFY.txt` 必须含：并行数（7）、数据行数、全表/atlas 内/atlas 外 `[已证]`、S03/S06/S16/S21 的 proved 与 strict、**有无达标翻转**、**M76 披露段落行号**、两处改字已生效的证据
