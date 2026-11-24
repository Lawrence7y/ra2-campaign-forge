> 卡号：R16-R4-SLOTN-B1
> 角色：执行器（`work/cn:hy4flash-free`）
> 写域：`lead\next_re_20261117_r14\R16_SLOTN_B1\`（产物）——**严禁写 `coverage.tsv`**
> 日期：2026-11-20（R16 第 2 轮）· 批次 **1 / 3**（本批 15 行）

# 任务：给 15 行 `slotN` 命中行补写成文的 ④ 使用见证（D-47(A) 裁决后解封）

## 0. 绝对边界

1. **严禁写 `COVERAGE\coverage.tsv`**（单写者纪律：只有合并员能改）。你只产出 delta，Lead 在下一轮派合并员并表。
2. 不写 `PANEL.md` / `R14_COMMON.md` / 台账 / 看板 / `_drafts\` / `_cards\` / 其它卡目录。产物只在 `R16_SLOTN_B1\` 下。
3. 不做逆向以外的越界：可以跑 capstone 等**只读**反汇编/扫描脚本（这是允许的），但**不得**改 `ra2youli\` 下任何文件、不得写进程内存。
4. **不许编造**：任何地址取不到就写 `未取得`，**不许**用「看起来合理」的地址填空。取不到就没法补的行，明确列为 `SKIP` 并说明缺哪个字段。

## 1. 为什么这批现在可做（前置裁决，照抄，不许改判断）

- `D-43(A)`（`R14_COMMON` §8.8 条 4）把「`vt[slot] == entry`」写进 ④「使用见证」的定义。
- `§12.3` 原本禁止 ②（类身份）与 ④ 共用同一虚表槽 ⇒ 这 43 行的 ④ 在这条下**0 行可补**。
- **用户 2026-11-20 已裁定 D-47 (A)：维持 D-43(A) 优先，§12.3 对「活 vtable 槽位」形态正式让位 + 整批披露。**
  ⇒ 这 43 行的 ④ **全部可补**。裁决登记在 `lead\PENDING_DECISIONS.md`（已裁决记录段 D-47 条）；成文在 `R14_COMMON.md §12.4`（另一张卡在写，你**不必**等它，但引用时要写「D-47(A) 裁决」）。

**因此每行补写的 ④ 必须自带披露指针**（见第 3 节的格式末尾），不得写成「已过 §12.3」。

## 2. 本批的 15 行

**清单来源（权威）**：`lead\next_re_20261117_r14\PROBE_802\slotN43.tsv`
- 该文件 1 行表头 + **43 行数据**，按文件顺序编号为数据行 **1..43**。
- **本批取数据行 1–15**（含两端）。

列（该文件）：`entry	subsystem	name	vt_count	slot_no	col_ok	install_ext	ring4_ok	reason`

**你必须先自己核**：该文件数据行确为 43 行；本批 15 行的 entry 互不重复；15 行全部 `col_ok=match`、`install_ext=y`。若不符，立即在报告里标红并停。

## 3. ④ 的措辞格式（**必须照既有 91 行的先例**，不许自创体例）

盘上已有 91 行按同一格式补写过 ④（`R4_FILL_91_R2` / `R3` 并入）。**先去看三条样例**（只读）：

- `00464AC0`、`004DE630`、`004F42F0`（在 `COVERAGE\coverage.tsv` 第 4 列里搜 `④ 活表槽位见证`）

先例格式（照此骨架，字段逐个填实）：

```
④ 活表槽位见证：<Class>::slot<N>（vt=<VTADDR>，槽 <N> 值=<ENTRY>，COL=<COLADDR> offset=<off>，RTTI=<RTTIADDR>→<mangled>；装表点 <SITE> 位于 <FUNC> 体内，entry 体外） ④升级句：<Class>::slot<N>（④ 表属类与行名类一致，均为 <Class>；该槽即其 vt=<VTADDR> 表 slot<N>，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）
```

字段要求：

| 字段 | 怎么取 | 取不到怎么办 |
|---|---|---|
| `<VTADDR>` | 该 entry 所在活虚表基址（`.rdata`，8 位大写十六进制，不带 `0x`） | 写 `未取得`，该行记 `SKIP` |
| `<N>` | `slotN43.tsv` 的 `slot_no` | — |
| `<COLADDR>` + `offset` | 该表的 COL（Complete Object Locator）地址与 `offset` | 可写 `未取得`（先例里这是可缺项，缺了就写 `未取得`，**不因此 SKIP**） |
| `<RTTIADDR>` → `<mangled>` | RTTI 类型描述符地址与装饰名 | 同上，可 `未取得` |
| `<SITE>` | `slotN43.tsv` 的 `install_ext`（装表指令地址） | 已有，直接用 |
| `<FUNC>` | 装表点所属函数（入口地址即可） | 可写 `未取得` |
| `<Class>` | 该行 name 的前缀（如 `FootClass::slot139` ⇒ `FootClass`） | 必填 |

**取数途径（建议顺序，任选可行者）**：
1. `PROBE_802\work_scan.json`（上一轮探针的扫描产物，里面应有该 entry 的 vt/slot/RTTI 明细）；
2. 直接读 `PROBE_802\probe.py` 的实现，复用它的取数函数；
3. 自己写只读扫描脚本（capstone + 读 `ra2youli\gamemd.exe`）。

> `gamemd.exe`：4,825,360 B，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，ImageBase `0x400000`，`.text = [0x401000, 0x7E038D)`。**只读**打开。

**反抄袭硬要求**：15 行的 ④ 文本**必须行行不同**（vt/slot/class/site 至少 3 个字段不同）。若你产出两行正文完全相同（除 entry 外），说明你复制了，直接判不合格。

## 4. 产物（`R16_SLOTN_B1\`）

### 4.1 `delta.tsv` —— TAB 分隔，8 列，与 `coverage.tsv` 完全同构

表头：`entry	subsystem	name	one_line_semantics	grade	evidence_path	n_sources	conflict`

- 每行：从盘上 `coverage.tsv` 取该 entry 的**整行原值**，**只改第 4 列**——在**原有语义之后追加**你的 ④ 文本（用 `；` 或空格衔接，保证原文**一字不删**）。
- 第 1/2/3/5/6/7/8 列必须与盘上**逐字节相同**。
- 只放本批 15 行中的**成功行**（`SKIP` 行不进 delta）。

### 4.2 `fields.tsv` —— 逐行取数明细（15 行全放，含 SKIP）

列：`entry	class	slot_no	vtaddr	source_of_vtaddr	coladdr	col_offset	rtti_addr	rtti_mangled	install_site	install_func	status(OK|SKIP)	note`

- `source_of_vtaddr` 必须写清**你从哪取得的**（文件:行 或 你脚本的哪一步）。
- `note` 逐行独立，不许复制。

### 4.3 `REPORT.md`

必须含：
- 前置核对结果（43 行是否成立、本批 15 行是否全 `col_ok=match`/`install_ext=y`）
- 成功 / SKIP 行数，SKIP 的逐行原因
- 15 行 ④ 正文的**两两不同性自检**（说明你如何验证行行不同）
- `coverage.tsv` 改前改后 sha256（你**不该**改它，须证明前后一致）
- 你用的脚本与命令
- 一句明示：本批**只补 ④ 成文**，**不改 grade**、不改判定、不并表

## 5. 回复里给什么

只给：前置核对结论、成功行数 / SKIP 行数（SKIP 逐条一行原因）、`fields.tsv` 里 vtaddr 取得了几行、行行不同的自检结果、三份产物路径。**不要贴 15 行 ④ 全文**（贴 1 行作为样例即可）。
