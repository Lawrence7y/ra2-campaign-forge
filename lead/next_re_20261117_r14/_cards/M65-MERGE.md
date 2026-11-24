# M65-MERGE — 并表 15 行（S22 十四行 + S05 一行，均已审 PASS）

## 独占写权

本轮**只有你**可以写 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md`。
不许 git commit；不许碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT*`。

改动前记两文件 `mtime`/字节/`sha256`，改后再记，写进 `MERGE_M65\BEFORE_AFTER.txt`。

## 并什么（合计 15 行，全部已过异族审计）

### A. S22 十四行（审计表 `NAMED_PUSH_AUDIT4\verdict.tsv`，16 行中 PASS 14）

`006BF810`、`006BF990`、`006BFB10`、`006BFC90`、`006BFE10`、`006C0110`、`006C0290`、`006C0410`、`006C0590`、`006C0710`、`006C0890`、`006C0B90`、`006C0D10`、`006C0E90`
来源 delta：`NAMED_PUSH_S22_B1\delta.tsv`

**FAIL 2 行整行拒绝，一个字不许改**：`006BFF90`、`006C0A10`
（原因：把构造函数里的**内嵌成员表**误当对象主虚表——`007EB6D4` 写的是 `[esi+0xC4]` 的 TypeList、`007F36B4` 写的是 `[esi+0x38]` 的 DynamicVectorClass；真主虚表是 `007F5728`/`007F3650`，槽 0 均为 `00410260`。其所谓 QueryInterface 实为 `VectorClass<T>` 析构式函数，不比较 IID、不写 `*ppvOut`、不返回 HRESULT 三态。）

### B. S05 一行（审计表 `NAMED_PUSH_AUDIT3\verdict.tsv`，PASS）

`00748190`，来源 delta：`NAMED_PUSH_S05_B3\delta.tsv`

## Lead 已核过的前置（不符就停下）

- 14 行 S22 当前 grade **全部为 `[未证]`**；`00748190` 当前为 `[静态推断]`
- 15 行**全部在 atlas 内**（atlas `entry` 为小写，比对须归一）
- 现盘上：数据行 **18,498**、全表 `[已证]` **1,512**、atlas 内 **1,506**、atlas 外 **6**、S22（atlas 内）**55**、S05（atlas 内）**170**

## 改什么

`coverage.tsv` 这 15 行各改 3 列：

- 第 4 列语义 ← 对应 delta 第 4 列**原文照抄**
- 第 5 列 `grade` → `[已证]`
- 第 6 列 `evidence_path` → 14 行填 `NAMED_PUSH_AUDIT4/VERDICT.md`；`00748190` 填 `NAMED_PUSH_AUDIT3/VERDICT.md`

第 1、2、3、7、8 列不动。数据行仍 18,498、8 列、制表符分隔。

## `PANEL.md` 同步

- S22（atlas 内 proved）**55 → 69**；S05 **170 → 171**
- 全表 `[已证]` **1,512 → 1,527**；atlas 内 **1,506 → 1,521**；atlas 外仍 **6**
- 严格双列表相应行按新值更新；`proved_strict` 是否同增按你实算（S22 的 14 行是 `[未证]`→`[已证]`，若其语义不含 `未证` 则 strict 同增）
- 备注列追加：`M65 并表 NAMED_PUSH_AUDIT4 审计 PASS 14 行（S22 TClassFactory 同族工厂，均 atlas 内，evidence_path 改指 NAMED_PUSH_AUDIT4/VERDICT.md）+ NAMED_PUSH_AUDIT3 PASS 1 行（S05 00748190）；同卡 S22 的 006BFF90/006C0A10 审计 FAIL 整行拒绝（内嵌成员表误当主虚表）`
- **达标判定不得改变**（严格仍仅 S17）；若你算出翻转，**停下报告**

## 额外限定（写进备注）

`〔模板级低信息量 ③b②：S22 这批是同一 C++ 模板 TClassFactory<T> 的多次实例化，③ 走函数体内 QueryInterface 的 HRESULT 分支（非 survey 命中的 operator new 空判断）；Lead 已裁定 ③ 只认函数整体合同真实，不要求落在筛出它的站点；异族审计 16 行中 14 行真、2 行假，假的两行系 ② 误判内嵌成员表〕`

## 交付

- `MERGE_M65\MERGE_LOG.md`、`BEFORE_AFTER.txt`、`VERIFY.txt`
- `VERIFY.txt` 必须含：数据行数、全表/atlas 内/atlas 外 `[已证]`、S22 与 S05 的 proved、15 行新 grade、`006BFF90`/`006C0A10` 两行 grade **未变**、**有无达标翻转**
