> 卡号：R16-R4-SLOTN-B3
> 角色：执行器（`work/cn:hy4flash-free`）
> 写域：`lead\next_re_20261117_r14\R16_SLOTN_B3\`（产物）——**严禁写 `coverage.tsv`**
> 日期：2026-11-20（R16 第 4 轮）· 批次 **3 / 3**（本批 13 行，43 行收官）

# 任务：给最后 13 行 `slotN` 命中行补写成文的 ④ 使用见证

> 批次 1（`R16_SLOTN_B1`，数据行 1–15）已完成并已过异族审计（PASS 15/0）；批次 2（`R16_SLOTN_B2`，数据行 16–30）已产出、待审。**先读这两批的卡面与产物，把你的做法对齐**（批次 1 的 `scan_fields.py` 可只读复用）。

## 0. 绝对边界

1. **严禁写 `COVERAGE\coverage.tsv`**（只有合并员能改）。你只产出 delta。
2. 不写 `PANEL.md` / `R14_COMMON.md` / 台账 / 看板 / `_drafts\` / `_cards\` / **其它卡目录产物**（`R16_SLOTN_B1\`、`R16_SLOTN_B2\` 只读）。
3. 可以跑**只读**反汇编/扫描；不得改 `ra2youli\` 下任何文件、不得写进程内存。
4. **不许编造**：地址取不到写 `未取得`；vt 取不到记 `SKIP` 并说明缺哪个字段。

## 1. 背景（照抄）

用户 2026-11-20 已裁 **D-47 (A)**：维持 `D-43(A)` 优先、`§12.3` 对「活 vtable 槽位」形态**正式让位**。裁决登记在 `lead\PENDING_DECISIONS.md`；成文在 `R14_COMMON.md`（**节号已重号为 §12.6**，早前卡片里写的 §12.4 是重号，已纠正）。

⇒ **本批 ④ 的披露指针必须写 `§12.6`**（不是 §12.4）。

## 2. 本批的 13 行

**清单来源（权威）**：`lead\next_re_20261117_r14\PROBE_802\slotN43.tsv`（1 表头 + **43 行数据**，按文件顺序编数据行 1..43）
- **本批取数据行 31–43**（含两端，共 **13 行**）。
- 批次 1 = 1–15、批次 2 = 16–30，本批 = 31–43，三批合起来正好 43。

**必须先自核**：
1. 数据行确为 43 行；
2. 本批 13 行 entry 互不重复；
3. 本批 entry 与批次 1（`R16_SLOTN_B1\fields.tsv`）、批次 2（`R16_SLOTN_B2\fields.tsv`）的 entry 集合**交集为空**；
4. 13 行全部 `col_ok=match`、`install_ext=y`；
5. 13 行都存在于 `coverage.tsv` 且 grade 为 `[已证]`。

任一不符 ⇒ 标红并停，不要自行调行范围。

## 3. ④ 的措辞格式（照先例，不许自创）

先看三处：
- 盘上既有 91 行先例：`coverage.tsv` 第 4 列搜 `④ 活表槽位见证`，取 `00464AC0`、`004DE630`、`004F42F0`
- 批次 1 的 `R16_SLOTN_B1\delta.tsv` 一条
- 批次 2 的 `R16_SLOTN_B2\delta.tsv` 一条

骨架（与你前两批一致，**唯节号改 §12.6**）：

```
④ 活表槽位见证：<Class>::slot<N>（vt=<VTADDR>，槽 <N> 值=<ENTRY>，COL=<COLADDR> offset=<off>，RTTI=<RTTIADDR>→<mangled>；装表点 <SITE> 位于 <FUNC> 体内，entry 体外） ④升级句：<Class>::slot<N>（④ 表属类与行名类一致，均为 <Class>；该槽即其 vt=<VTADDR> 表 slot<N>，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

`gamemd.exe`：4,825,360 B，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，ImageBase `0x400000`，`.text = [0x401000, 0x7E038D)`。RTTI 的 `pTD`/`pCHD` 存**绝对 VA**；装饰名在 `TD+8` 是**内联串不是指针**。**只读**打开。

### 3.1 一个已知坑（批次 2 踩到，你要继承它的处理）

若 `PROBE_802\work_scan.json` 的 `site_of` 所指的**表属类与行 name 的类不一致**，不要照抄那个 site。按「类一致优先」另选：取**行名类自己的表**及其**该表自己的装表点**（装表指令 imm32 须等于该表地址），并在 `fields.tsv`/`REPORT.md` **逐字披露为何改选**。
（批次 2 的行 30 `005B2FD0` 就是这种：`work_scan` 给的 site 落在 BuildingClass 表，实际改取 InfantryClass 表 `007EB058` + 装表点 `00517D9D`。）

### 3.2 反抄袭硬要求

13 行 ④ 正文必须两两不同；**把 entry 归一为占位符后仍须两两不同**。同族同 vt 属事实、不算抄袭，但要保证文本不是复制。

## 4. 产物（`R16_SLOTN_B3\`）

### 4.1 `delta.tsv` —— TAB 分隔，8 列

表头：`entry	subsystem	name	one_line_semantics	grade	evidence_path	n_sources	conflict`
- 每行取盘上 `coverage.tsv` 整行原值，**只改第 4 列**：原文 + `；` + ④ 文本（**原第 4 列必须是结果的严格前缀**，原文一字不删）。
- 第 1/2/3/5/6/7/8 列与盘上**逐字节相同**（记录你读到的 `coverage.tsv` sha256 与字节数；该文件正被并发合并，若期间变化要重新校验并在报告留痕）。
- 只放成功行；`SKIP` 行不进 delta。

### 4.2 `fields.tsv`

列：`entry	class	slot_no	vtaddr	source_of_vtaddr	coladdr	col_offset	rtti_addr	rtti_mangled	install_site	install_func	status(OK|SKIP)	note`

### 4.3 `REPORT.md`

含：前置 5 项自核结果；成功/SKIP 行数；6 项字节复核结果；行行不同自检（含 entry 归一后）；`work_scan` site 类不符而改选的逐行披露（若有）；`coverage.tsv` 与 `gamemd.exe` 的 sha256（证明未改）；脚本与命令；一句明示「只补 ④ 成文、未改 grade/判定、未并表」。

## 5. 回复里给什么

只给：前置 5 项自核结论（含三批并集=43 与交集为空）、成功/SKIP 行数、vtaddr 取得行数、行行不同自检、有无 3.1 那种改选（几行）、三份产物路径、样例 ④ 一条。**不要贴 13 行全文**。
