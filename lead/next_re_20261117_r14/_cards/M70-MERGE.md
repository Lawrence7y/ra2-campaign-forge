# M70-MERGE — 并表 11 行（S22_B3，已审 PASS 11/0）

## 独占写权

本轮**只有你**可以写 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md`。
不许 git commit；不许碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT*`、`INVENTORY`。

改动前记两文件 `mtime`/字节/`sha256`，改后再记，写进 `MERGE_M70\BEFORE_AFTER.txt`。

## 并什么（11 行）

- 审计表：`NAMED_PUSH_AUDIT11\verdict.tsv`（11 行、8 列，全部 PASS）
- delta 来源：`NAMED_PUSH_S22_B3\delta.tsv`
- entry：`006C2B10`、`006C2C90`、`006C2E10`、`006C2F90`、`006C3110`、`006C3290`、`006C3410`、`006C3590`、`006C3890`、`006C3A10`、`006C3B90`

交集必须正好 11 行；不是就**停下报告**。

## Lead 已核过的前置（不符就停下）

- 现盘上：数据行 **18,498**、全表 `[已证]` **1,580**、atlas 内 **1,574**、atlas 外 **6**、S22（atlas 内 proved）**87**
- 11 行 atlas 内与否自己核（`entry` 小写须归一）

## 改什么

`coverage.tsv` 这 11 行各改 3 列：

- 第 4 列语义 ← delta 原文照抄
- 第 5 列 `grade` → `[已证]`
- 第 6 列 `evidence_path` → `NAMED_PUSH_AUDIT11/VERDICT.md`

第 1、2、3、7、8 列不动。数据行仍 18,498、8 列、制表符分隔。

## `PANEL.md` 同步

- S22（atlas 内 proved）**87 → 98**（以你实算为准）
- 全表 `[已证]` **1,580 → 1,591**；atlas 内 **1,574 → 1,585**（若全在 atlas 内）
- 严格双列表按权威口径（`[未证]` 字面）
- 备注列追加：`M70 并表 NAMED_PUSH_AUDIT11 PASS 11 行（S22 TClassFactory 同族），evidence_path 改指 NAMED_PUSH_AUDIT11/VERDICT.md`
- **达标判定不得改变**；若翻转，**停下报告**

## 必须追加的第二条披露（**不许省略、不许改写**）

在 M69 那条披露之后追加：

```
> ⚠️ **M70 披露：工厂族 ③b② 的"消费方"在函数内部，本 entry 自身返回码无消费方**
> `a-S22B3` 审计指出两处措辞级缺口（不判 FAIL，但必须披露）：
> 1. 这批行语义里写的「主虚表 slot0 = 00410260」指的是**函数体内新建对象**的表，工厂自身 `vt[0]` 是各自的 `QueryInterface`（如 `006C2A50`）；
> 2. ③b② 所说的「调用方分支」实为**本函数对 `QueryInterface` 返回值的消费**；本 entry 自身的 HRESULT 在镜像内**无消费方**（11 行 direct caller 全为 0，21 处 `CoCreateInstance` 没有一处使用这 11 个 CLSID）。
> ⇒ 引用这批行时，不得表述为「该工厂函数被外部调用并检查其返回码」。
```

## 交付

- `MERGE_M70\MERGE_LOG.md`、`BEFORE_AFTER.txt`、`VERIFY.txt`
- `VERIFY.txt` 必须含：并行数、数据行数、全表/atlas 内/atlas 外 `[已证]`、S22 的 proved 与 strict、**有无达标翻转**、**M70 披露段落的行号**
