> 卡号：R16-R4-SLOTN-B2
> 角色：执行器（`work/cn:hy4flash-free`）
> 写域：`lead\next_re_20261117_r14\R16_SLOTN_B2\`（产物）——**严禁写 `coverage.tsv`**
> 日期：2026-11-20（R16 第 3 轮）· 批次 **2 / 3**（本批 15 行）

# 任务：给 15 行 `slotN` 命中行补写成文的 ④ 使用见证（D-47(A) 裁决后解封）

> 本卡与批次 1（`R16-R4-SLOTN-B1`，已完成、正在审计）**同规格不同行**。**先读批次 1 的卡面与产物**，把你的做法对齐它的成功经验（它的 15/15 全部取到了 vt/COL/RTTI/装表点，可复用其脚本 `R16_SLOTN_B1\scan_fields.py`）。

## 0. 绝对边界

1. **严禁写 `COVERAGE\coverage.tsv`**（只有合并员能改）。你只产出 delta。
2. 不写 `PANEL.md` / `R14_COMMON.md` / 台账 / 看板 / `_drafts\` / `_cards\` / **其它卡目录的产物**（`R16_SLOTN_B1\` 只读——可以读它的脚本、不许改它）。
3. 可以跑**只读**反汇编/扫描脚本；**不得**改 `ra2youli\` 下任何文件、不得写进程内存。
4. **不许编造**：任何地址取不到就写 `未取得`；取不到 vt 就记 `SKIP` 并说明缺哪个字段。

## 1. 为什么这批现在可做（背景，照抄）

用户 2026-11-20 已裁 **D-47 (A)**：维持 `D-43(A)` 优先、`§12.3` 对「活 vtable 槽位」形态**正式让位**。⇒ 这 43 行的 ④ 由「0 行可补」变为**全部可补**。裁决登记在 `lead\PENDING_DECISIONS.md`（已裁决记录段 D-47）；成文在 `R14_COMMON.md §12.4`（已落）。

**因此每行补写的 ④ 必须自带披露指针**，不得写成「已过 §12.3」。

## 2. 本批的 15 行

**清单来源（权威）**：`lead\next_re_20261117_r14\PROBE_802\slotN43.tsv`
- 1 行表头 + **43 行数据**，按文件顺序编号为数据行 **1..43**。
- **本批取数据行 16–30**（含两端）。批次 1 已取 1–15、批次 3 将取 31–43。
- 列：`entry	subsystem	name	vt_count	slot_no	col_ok	install_ext	ring4_ok	reason`

**必须先自核**：数据行确为 43 行；本批 15 行 entry 互不重复、且**与批次 1 的 15 行无交集**（去 `R16_SLOTN_B1\fields.tsv` 取它的 entry 集合做交集检查，须为空）；15 行全部 `col_ok=match`、`install_ext=y`。不符则标红并停。

## 3. ④ 的措辞格式（照既有先例，不许自创）

先例：盘上已有 91 行按此格式补写过 ④。**看 3 条样例**（只读）：`coverage.tsv` 第 4 列搜 `④ 活表槽位见证`，取 `00464AC0`、`004DE630`、`004F42F0`。**再看批次 1 的 `delta.tsv` 一条样例**，与它保持完全同构。

骨架：

```
④ 活表槽位见证：<Class>::slot<N>（vt=<VTADDR>，槽 <N> 值=<ENTRY>，COL=<COLADDR> offset=<off>，RTTI=<RTTIADDR>→<mangled>；装表点 <SITE> 位于 <FUNC> 体内，entry 体外） ④升级句：<Class>::slot<N>（④ 表属类与行名类一致，均为 <Class>；该槽即其 vt=<VTADDR> 表 slot<N>，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）
```

字段取法同批次 1（`PROBE_802\work_scan.json` / `PROBE_802\probe.py` / 自写只读扫描）。**建议直接复用 `R16_SLOTN_B1\scan_fields.py`**（只读引用），把行范围改成 16–30。

`gamemd.exe`：4,825,360 B，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，ImageBase `0x400000`，`.text = [0x401000, 0x7E038D)`。RTTI 的 `pTD`/`pCHD` 存**绝对 VA**；装饰名在 `TD+8` 是**内联串不是指针**。**只读**打开。

**反抄袭硬要求**：15 行 ④ 正文必须两两不同；**把 entry 归一为占位符后仍须两两不同**（批次 1 做到了这一点，你也要做同样的自检）。事实相同的（同族同 vt）属正常，但要保证文本不是复制。

## 4. 产物（`R16_SLOTN_B2\`）

### 4.1 `delta.tsv` —— TAB 分隔，8 列，与 `coverage.tsv` 完全同构

表头：`entry	subsystem	name	one_line_semantics	grade	evidence_path	n_sources	conflict`
- 每行取盘上 `coverage.tsv` 整行原值，**只改第 4 列**：在**原有语义之后追加** ④ 文本（用 `；` 衔接，原文**一字不删**，原文必须是新第 4 列的严格前缀）。
- 第 1/2/3/5/6/7/8 列与盘上**逐字节相同**。
- 只放成功行；`SKIP` 行不进 delta。

### 4.2 `fields.tsv`

列：`entry	class	slot_no	vtaddr	source_of_vtaddr	coladdr	col_offset	rtti_addr	rtti_mangled	install_site	install_func	status(OK|SKIP)	note`
`note` 逐行独立、不许复制。

### 4.3 `REPORT.md`

含：前置核对（43 行成立 / 本批与批次 1 交集为空 / 15 行全 `col_ok=match`）、成功与 SKIP 行数、6 项字节复核结果、行行不同自检（含 entry 归一后比较）、`coverage.tsv` 改前改后 sha256（证明未改）、`gamemd.exe` sha256 未变、脚本与命令。

## 5. 回复里给什么

只给：前置核对结论（含与批次 1 交集检查）、成功/SKIP 行数、vtaddr 取得行数、行行不同自检结果、三份产物路径、样例 ④ 一条。**不要贴 15 行全文**。
