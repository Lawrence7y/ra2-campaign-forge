# R16-AUDIT-EVID802-11 审计判定

> 审计员：`agent-38`（异族执行器）· 日期 2026-11-21 · 被审对象：`R16_EVID802_11\`（`fields.tsv` / `coverage_delta.tsv` / `REPORT.md`）
> 写域：仅本目录 `R16_AUDIT_EVID802_11\`。被审目录全程只读，`coverage.tsv` 未改，未跑任何逆向。
> 复跑：`python verify.py`（11 行 × 全部项目，产出 `check11.tsv`；`resolve.py` 已复制到本目录，输出写本目录下的 `_resolve_before/` `_resolve_after/`）。

---

## 0. 总体判定

**FAIL 11 / PASS 0。**

唯一的失败项是 **§D-2「11 行注记须逐行不同（不许复制）」**：11 行注记**逐字节完全相同**（同一句模板，重复 11 份）。

**本卡存在的两项核心事实均成立，且已独立复核通过：**

1. 11 个 entry 的 `PROOF_<entry>.txt` 在盘上**确实各只有 1 份**（lead 全树 + 仓库全树两次遍历），**11 个文件全部 ①②③④ 四段齐全**、非空、`name=` 与台账行一致；
2. 应用这 11 行 delta 后 **`R_OK` 852 → 863、`R_TRACE_ONLY` 802 → 791**，且 11 行的 `R_OK` 命中**确实来自 PROOF 段**（不是被别的东西带进来的）。

其余：§A、§B、§C、§D-1 全部 11 行通过。**修复成本 = 重写 11 条注记，delta 实质可直接并表。**

| 项 | 不合格行数 | 结论 |
|---|---|---|
| §A 原文保全与最小改动 | 0 / 11 | PASS |
| §B 路径真实性与唯一性 | 0 / 11 | PASS |
| §C 是否真的改善可解析率 | 0 / 11 | PASS |
| §D-1 注记与实际情形相符 | 0 / 11 | PASS |
| **§D-2 注记逐行不同** | **11 / 11** | **FAIL** |

---

## 1. §A · 原文保全与最小改动（11/11 PASS）

以盘上 `COVERAGE\coverage.tsv`（快照 `bytes=4079053`、`sha256=3A1DC1DD3F67B7684BF167640CEECF3EC85330CF5B54C31B65A02CA98C993D4A`）逐行比对：

- **第 6 列严格前缀**：11/11 为真。且实测结构精确为三段 `原第6列 + ";" + PROOF 路径 + ";" + M94 注记`，`segs[0] == 原第6列` 逐字节相等（不是"先前缀后改写"的擦边情况）。
- **原 `classification_trace` 段仍在**：11/11。原第 6 列实测恰为 `EVIDENCE/classification_trace.tsv#<entry>`（纯 trace-only，无其他段），新列首段即该串，未删、未改写。
- **第 1–5、7、8 列逐字节相同**：11/11，`A_rest_cols_diff` 全空。
- **改动面**：把 delta 应用到快照副本后与快照做全文件逐行 diff，差异**恰好 11 行**（行号 1388/1389/4982/5286/5287/5387/5388/8877/8878/8983/8984），**每行只改第 6 列**（0-based col 5），无其他列、无其他行被动。

## 2. §B · 路径真实性与唯一性（11/11 PASS）

### B1 · 唯一性（独立复核，非采信执行器）

两次独立遍历：
- `lead\` 全树 `PROOF_*.txt`（共 92 份）→ 11 个 entry 每个**命中 1 份**；
- `repo\` 全树、按 `(?i)^proof[_-]?<entry>` 宽匹配（放宽容忍 `PROOF_`/`proof-`/`PROOF` 前缀变体与任意扩展名）→ 同样**每个 1 份**，与首次遍历同一路径。

因此执行器「11 行都只有 1 份、无需二分」的自述**成立**，我未能找到第二份。

### B2 · 路径为真且非空

11/11 `isfile` 为真，字节数分别为：
`0045A560` 710 · `0045A610` 596 · `0053C6A0` 5295 · `005514B0` 4690 · `00551560` 1784 · `00557090` 4675 · `00557140` 1769 · `006B1850` 723 · `006B1900` 600 · `006B8660` 723 · `006B8710` 600。全 > 0。
delta 声明的路径与唯一命中路径 `normcase(abspath())` 相等，11/11。

### B3 · 内容以该 entry 为对象 + 四段齐全（本卡的存在理由）

**「四段齐全」判据（明示）**：文件内存在**以 ①②③④ 各自标记 + 空白开头**的独立行（正则 `^([①②③④])\s`，MULTILINE）；四者齐备才算齐全。另要求 ④ 段**有实质内容**（不止段头）、③ 段带 body 证据。

**实测 11/11 齐全**，且标记序列可解释：

| 组 | 文件 | 标记行序 | ④ 实测量 | ③ 实质 |
|---|---|---|---|---|
| S10（6 份） | 0045A560 / 0045A610 / 006B1850 / 006B1900 / 006B8660 / 006B8710 | `①②③④④` | 2 行：`④ RING_TYPE=EXACT` + `④ exact external dispatch sites: <addr,...>` | `③ BODY: body N insns; sha256prefix=…; anchors=…` |
| S20（5 份） | 0053C6A0 / 005514B0 / 00551560 / 00557090 / 00557140 | `①②②③④④`（② 出现两次：`CLASS/RTTI` 与 `CLASS/RTTI all slots`，属同段复述，非缺段） | 2 行：`④ RING_TYPE=EXACT` + `④ exact dispatch sites (global vptr write evidence…)` 及其下 site 明细（含 `global=/off=/slot=/vt=/write_src=/insn=`） | `③ BODY: body N insns; sha256=…` + `FULL BODY DISASSEMBLY` 反汇编 |

**「以该 entry 为对象」的实测**：
- entry 出现次数：S10 组 2 次、S20 组 3 次（= `fields.tsv` 自述，11/11 相符）。S20 的第 3 次来自反汇编首行地址字面量（如 `0053C6A0  53 push ebx`），S10 无全量反汇编故为 2 次。
- 文件内 `name=` 与台账 `name` 列**逐字节相等 11/11**（`B_name_match` 全 True）——排除了"文件名对但内容是别的 entry"。
- ① 段自带 `atlas entry=<entry>` 自证。

**额外核过的一处疑似复制**：`00551560` 与 `00557140` 的 ③ `sha256` 同为 `F26D5AD50169`，看起来像复制错误。我逐条比对了二者 `FULL BODY DISASSEMBLY`：**opcode 字节 17/17 完全相同、地址 17/17 完全不同**（各自从自己的 entry 起址）。这是同一 CRT `FindItemIndex` 模板在两个类 vtable 槽上的实例化（相对跳转编码与绝对地址无关），**不是复制粘贴错误**。同理 S10 三份 `body 73 insns`（0045A560/006B1850/006B8660）`sha256prefix` 互不相同（`7C7A0369881E` / `F2D57E4B46E9` / `BF3172E57FB8`），符合预期。

## 3. §C · 是否真的改善可解析率（11/11 PASS，852 → 863 成立）

口径：`EVID_RESOLVE\resolve.py` 逐字节复制到本目录运行，`--repo` 指向仓库根，`--coverage` 指向本目录副本，`--out` 指向本目录子目录（**未写 `EVID_RESOLVE\` 原目录**）。

**一致性保证**：先 `shutil.copyfile` 取单一快照 `_coverage_snapshot.tsv`，改前与改后两次 `resolve.py` **都基于同一快照**，避免 `coverage.tsv` 并发漂移混入结论。

| | R_OK | R_TRACE_ONLY | R_MISSING | R_EMPTY | [已证] 总数 |
|---|---|---|---|---|---|
| 改前（盘上当前 `coverage.tsv`） | **852** | **802** | 0 | 0 | 1654 |
| 改后（+ 这 11 行 delta） | **863** | **791** | 0 | 0 | 1654 |
| 差 | **+11** | **−11** | 0 | 0 | 0 |

→ **卡面要求的 852 → 863、802 → 791 完全复现，一分不差。**

**C-1 改前是否确实都是 `R_TRACE_ONLY`**：11/11 是。逐行用 `resolve.py` 的 `resolve_row()` 直接判：改前 11 行均为 `R_TRACE_ONLY`，**没有任何一行改前已是 `R_OK`**，故 11 行全部产生真实增量，+11 无虚增。

**C-2 R_OK 的增量是否真由 PROOF 段带来（关键，防"假阳性"）**：
`resolve.py` 的归类是「若所有段都是 trace → `R_TRACE_ONLY`」，否则「有任一段 `isfile` → `R_OK`」。所以**只要 `EVIDENCE/classification_trace.tsv` 在盘上存在，追加任何非 trace 词就能翻成 `R_OK`**，`R_OK` 本身并不能证明 PROOF 路径可解析。我按此专门验了两件事：

1. `EVIDENCE/classification_trace.tsv` 在 `r14` / `lead` / `repo` 三个基准下**均不存在**（`isfile=False`）→ 第 1 段必然 miss；
2. 逐段命中表 `C_part_hits`：11/11 全为 **`T:miss/F:HIT/T:miss`**，`first_existing` 全部指向 `…\S1x_KPROVED\EVIDENCE\PROOF_<entry>.txt`，`C_hit_is_proof=True`。

→ **11 行的 `R_OK` 全部且仅由 PROOF 段命中造成**，+11 是真实增量，不是口径漏洞带进来的。

**并表影响面**：全文件 diff 显示改动仅这 11 行 × 第 6 列，故并表不改变其他任何行的分类。

## 4. §D · 注记质量

### §D-1 注记与该行实际情形是否相符（11/11 PASS）

注记内容为 `M94 指针修复：④ 已写在盘上（PROOF 文件含 ①②③④ 四段），原指针只连 classification_trace`，含两个可证伪断言，逐行核：

1. 「PROOF 文件含 ①②③④ 四段」→ 见 §B3，11/11 为真；
2. 「原指针只连 classification_trace」→ 原第 6 列实测恰为 `EVIDENCE/classification_trace.tsv#<entry>`（逐字节），11/11 为真。

两句均与该行实际情形相符，**未发现与事实冲突的注记**。

### §D-2 注记是否逐行不同（11/11 FAIL）

卡面明确「不许复制」。实测：11 行注记**字符串完全相同**，`unique = 1`，每行重复数 `11`。注记里**不含任何本行信息**（无 entry、无 PROOF 路径、无 ④ 类型），一行注记配 11 个不同 entry，属复制。

这不是笔误级瑕疵：它使注记丧失可追溯性——单看注记无法判断说的是哪一行，也无法在 PROOF 文件被移动/替换后定位受影响行。

---

## 5. 必改清单（11 条）

| # | 行 | 项 | 必改内容 |
|---|---|---|---|
| 1 | `0045A560` | §D-2 | 注记需带本行信息、与其他 10 行不同 |
| 2 | `0045A610` | §D-2 | 同上 |
| 3 | `0053C6A0` | §D-2 | 同上 |
| 4 | `005514B0` | §D-2 | 同上 |
| 5 | `00551560` | §D-2 | 同上 |
| 6 | `00557090` | §D-2 | 同上 |
| 7 | `00557140` | §D-2 | 同上 |
| 8 | `006B1850` | §D-2 | 同上 |
| 9 | `006B1900` | §D-2 | 同上 |
| 10 | `006B8660` | §D-2 | 同上 |
| 11 | `006B8710` | §D-2 | 同上 |

**改法建议**（保持句式不破坏其他 10 行的可读一致，同时每行可辨）：把 entry、PROOF 文件名、④ 的实测类型写进去，例如

```
M94 指针修复：0045A560 的 ④（RING_TYPE=EXACT + 外部派发点 00517B1E）早已在
S10_KPROVED\EVIDENCE\PROOF_0045A560.txt 盘上（①②③④ 四段齐全），原指针只连 classification_trace
```

每行替换 `0045A560` → 各 entry、`S10_`/`S20_` 前缀、④ 的派发点地址（S10 取 `④ exact external dispatch sites:` 后的地址串；S20 取 `④ exact dispatch sites` 下 site 之一）。11 行可逐行区分。

**注**：此改动只动注记文字（第 6 列尾段），`R_OK` 增量与四段结论不受影响，改后仍应为 863 / 791。

---

## 6. `R_OK` 复算结果（结论）

| 指标 | 卡面/执行器声称 | 我的复算 | 结论 |
|---|---|---|---|
| 改前 `R_OK` | 852 | **852** | 一致 |
| 改后 `R_OK` | 863 | **863** | 一致 |
| 改前 `R_TRACE_ONLY` | 802 | **802** | 一致 |
| 改后 `R_TRACE_ONLY` | 791 | **791** | 一致 |
| [已证] 总数 | 1654 | **1654** | 一致（852+802 = 863+791 = 1654） |
| 11 行改前均 `R_TRACE_ONLY` | 声称是 | **11/11 是** | 一致 |
| `R_OK` 命中来源 | 未声称 | **11/11 来自 PROOF 段** | 已独立证实 |

---

## 7. 观察与附注（不构成本次 FAIL，供 lead 决策）

1. **`coverage.tsv` 在审计期间再次漂移**：`REPORT.md` §3 记其"改前/改后"为 `bytes=4077137 / sha256=822B2112…646D8 / mtime 2026-11-20T16:55:34Z`；我审计开始时的盘上文件为 `bytes=4079053 / sha256=3A1DC1DD…93D4A / mtime 2026-11-20T17:03:44Z`，且与我的快照逐字节相同（未再变）。漂移涉及的 4 行是 `00763200`/`00763D90`/`00772CD0`/`00772EB0`（改的是 `one_line_semantics`），**与本卡 11 行无关**；这 11 行的 1–5、7、8 列在当前版本上仍逐字节匹配（§A 11/11），**故 delta 对当前盘上版本依然可直接适用**。`REPORT.md` 已主动披露并发写，此处仅补充"漂移比其披露的又往前走了一版"。
2. **`REPORT.md` §3 的"未改"证明强度有限**：两次采样在同一会话内、且中间确认发生了第三方写入，等值只能说明"两个采样点之间没写"，不足以独立坐实全程未写。这属证明方法问题，不影响本次 A/B/C/D 结论（delta 来自文件内容而非其写入历史）。
3. **注记用词会让注记本身被 `resolve.py` 当作 trace 段**：注记含 `classification_trace` 字样，故第 6 列被拆成 3 段、`trace_flags = TFT`。本次**无害**（`classification_trace.tsv` 不存在，命中只可能来自 PROOF 段）。但一旦将来盘上出现 `EVIDENCE/classification_trace.tsv`，一个**已失效的 PROOF 指针**也会因第 1 段命中而被读成 `R_OK`，形成静默假阳性。建议改写注记时避免在 evidence_path 内出现 `classification_trace` 字样（如写"原指针只连 trace 表"）。
4. **`REPORT.md` §1 措辞**：称 ④ 段为"外部派发/装表记录"。S20 组确实是装表记录（含 `global/off/slot/vt/write_src`）；S10 组 ④ 只有 `RING_TYPE=EXACT` + `exact external dispatch sites: <addr,…>`，是派发点地址，**没有**装表字段。表述略宽，但不算失实，未计 FAIL。
5. `fields.tsv` 的 `proof_files_found` / `file_bytes` / `entry_occurrences` / `has_all_four_sections` 四项自述与我的实测**11 行全部相符**（0 处不符）。

---

## 8. 边界遵守自述

- 只读 `R16_EVID802_11\` 三个文件、`COVERAGE\coverage.tsv`、11 个 PROOF 文件、`lead\` 全树目录；**未写** `R16_EVID802_11\`、`COVERAGE\coverage.tsv`、`EVID_RESOLVE\`（`resolve.py` 是复制到本目录运行的，其 `resolve.tsv`/`summary.tsv` 输出落在本目录 `_resolve_before/`、`_resolve_after/`）、任何卡目录、台账、看板。
- 本目录产出：`VERDICT.md`、`verify.py`、`check11.tsv`，以及复跑产生的中间件 `resolve.py`（副本）、`_coverage_snapshot.tsv`、`_coverage_after.tsv`、`_resolve_before/`、`_resolve_after/`、`_resolve_before_stdout.txt`、`_resolve_after_stdout.txt`。
- 未做任何逆向，未读 `gamemd.exe`。
