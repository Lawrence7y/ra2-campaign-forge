# M69-MERGE — 并表 7 行（S12_B2 六 + S20_B3 一，均已审 PASS）

## 独占写权

本轮**只有你**可以写 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md`。
不许 git commit；不许碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT*`、`RESCAN_MOVED`、`INVENTORY`。

改动前记两文件 `mtime`/字节/`sha256`，改后再记，写进 `MERGE_M69\BEFORE_AFTER.txt`。

## 并什么（7 行）

| 组 | 审计表 | delta 来源 | 应并行数 |
|---|---|---|---:|
| A | `NAMED_PUSH_AUDIT9\verdict.tsv` | `NAMED_PUSH_S12_B2\delta.tsv` | **6** |
| B | `NAMED_PUSH_AUDIT10\verdict.tsv` | `NAMED_PUSH_S20_B3\delta.tsv` | **1** |

把审计表 `verdict == PASS` 的 entry 与对应 delta 的 entry 取交集；**必须正好 6 + 1**。不是就**停下报告**。

## Lead 已核过的前置（不符就停下）

- 现盘上：数据行 **18,498**、全表 `[已证]` **1,573**、atlas 内 **1,567**、atlas 外 **6**、S12（atlas 内 proved）**59**、S20 **61**
- 7 行在 atlas 内与否自己核（`entry` 小写须归一）

## 改什么

`coverage.tsv` 这 7 行各改 3 列：

- 第 4 列语义 ← 对应 delta 第 4 列原文照抄
- 第 5 列 `grade` → `[已证]`
- 第 6 列 `evidence_path` → A 组填 `NAMED_PUSH_AUDIT9/VERDICT.md`；B 组填 `NAMED_PUSH_AUDIT10/VERDICT.md`

第 1、2、3、7、8 列不动。数据行仍 18,498、8 列、制表符分隔。

## `PANEL.md` 同步

- S12（atlas 内 proved）**59 → 65**；S20 **61 → 62**（以你实算为准）
- 全表 `[已证]` **1,573 → 1,580**；atlas 内 **1,567 → 1,574**（若全在 atlas 内）
- 严格双列表按**权威口径**：`proved_strict` = atlas 内 ∧ `[已证]` ∧ 语义**不含字面 `[未证]`**（`strict_panel.py:78`）
- 备注列追加：`M69 并表 NAMED_PUSH_AUDIT9 PASS 6 行（S12_B2）+ NAMED_PUSH_AUDIT10 PASS 1 行（S20_B3 00763200），evidence_path 分别改指两审计 VERDICT`
- **达标判定不得改变**（严格仍仅 S17）；若你算出翻转，**停下报告**

## 必须在 `PANEL.md` 加的一条披露（**不许省略**）

在严格双列表之后追加：

```
> ⚠️ **M69 披露：② 与 ④ 共用 vt 槽枢轴（未收紧，已知限制）**
> `a-S20B3` 审计指出：`ff 52 10` / `83 f8 ff` / `74 xx` / `49` / `89 54 81 fc` / `7c xx` 这套字节是引擎 `DVC::Delete` 的**通用内联展开**，零函数级判别力；且 ②（类身份，走 RTTI 字节）与 ④（使用见证，走 ctor 写点字节）**在逻辑上共享 `vt[slot] == entry` 这一枢轴**。
> 按 D-40 §12.3 字面（两者不得同源），这批行会集体翻转。Lead 裁定：**整批按 ③b② 收、不单行否掉**，理由是与台账既有同形行保持一致；同时把该限制在此**显式披露**，供后续引用者自行判断。
> 受影响行：`TClassFactory<T>::slot3` 同族、`DVC::Delete` 内联展开族，以及 `00442230` 等同构行（合计约 40 行量级）。**收紧口径需一次裁决 + 一次性整批处置，不得零散改判。**
```

## 交付

- `MERGE_M69\MERGE_LOG.md`、`BEFORE_AFTER.txt`、`VERIFY.txt`
- `VERIFY.txt` 必须含：两组并行数（6+1）、数据行数、全表/atlas 内/atlas 外 `[已证]`、S12/S20 的 proved 与 strict、**有无达标翻转**、以及**披露段已写入 PANEL 的证据**（行号）
