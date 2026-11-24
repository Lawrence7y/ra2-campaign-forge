# R17-R43-INDEX-INTEGRITY · REPORT

## 范围与方法

- 校验对象：`lead\next_re_20261117_r14\R17_R42_F23_FIX\FACT_INDEX.tsv`（v3.1，F01–F26，26 条）。
- 路径基准：严格按任务要求，以仓库根 `D:\Project\ra2-campaign-forge` 解析；括号中的节号/行号只作为回查提示，不参与路径拼接。
- 只读：未修改 `R17_R42_F23_FIX` / `R17_R34_FACT_INDEX` / `R17_R38_FACTINDEX_FIX` / `R17_R40_FACTINDEX_V3` 下任何文件；未建进程、未调试、未启动 gamemd。
- 产物：本目录 `REPORT.md` / `paths.tsv` / `work.py`，均为 LF，无 0x0D 回车字节。
- 中间结果先落盘：`paths.tsv` 已写入 71 次路径检查。

## Q1 · 路径解析（26 条全查）

### 三桶汇总

| 桶 | 条数 | fact_id |
|---|---:|---|
| RESOLVED | 16 | F01, F02, F03, F04, F05, F06, F07, F08, F09, F10, F11, F12, F13, F14, F15, F16 |
| PARTIAL | 0 | — |
| BROKEN | 10 | F17, F18, F19, F20, F21, F22, F23, F24, F25, F26 |

- 总条数：26；实际路径检查数：71。
- F01–F16 的 evidence_paths 均以 `lead\next_re_20261117_r14\...` 开头，从仓库根可解析，全部 RESOLVED。
- F17–F26 的 evidence_paths 均为 run 内相对写法（如 `R17_DELIVERY\...` / `COVERAGE\...` / `R14_COMMON.md`），从指定仓库根逐条检查均不存在，故全部 BROKEN；本次未加 run 前缀重解析。

### 括号行号/节号抽样（6 处）

> 此抽样只核括号内行号/节号是否与指向内容对得上；三桶归类仍按“文件或目录是否存在”。

| # | fact_id | 标注 | 实际核对 | 结论 |
|---:|---|---|---|---|
| 1 | F01 | `STATUS_BOARD.md(L210-213)` | L210–L213 实际为 R17 第13轮 / R31 `0x5657A0` / R32 `0x5A5020` 段；未见 F01 的 1201/988/954/962+26 或类名恢复链。`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\STATUS_BOARD.md` | 不对得上 |
| 2 | F04 | `R17_LEDGER_1062\SECTION.md(事项1)` | L5 为 `### 1. ... 0x43F180 的调用方`，L7–L9 含调用链、`0x5A6510`、`0x5A691C`、308 条指令。`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_LEDGER_1062\SECTION.md` | 对得上 |
| 3 | F07 | `STATUS_BOARD.md(L261-265)` | 文件总行数 255，L261–L265 越界。`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\STATUS_BOARD.md` | 不对得上 |
| 4 | F22 | `R17_DELIVERY\DELIVERY_SUMMARY.md(§1 L1–L3)` | L14–L16 分别为 L1=791、L2=A458/B291（另列宽293）、L3=真两链65 与禁引304。`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_DELIVERY\DELIVERY_SUMMARY.md` | 对得上 |
| 5 | F25 | `RULING_R15_20261119\work\strict_panel.py(L78)` | L78 为 `if "[未证]" not in sem:`。`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\RULING_R15_20261119\work\strict_panel.py` | 对得上 |
| 6 | F25 | `COVERAGE\PANEL.md(L139–140, M58 界向更正)` | L139 写 `proved_strict 只是下界`；L140 写 `上面 L134/L138 把 proved_strict 说成「下界」方向标反——它是上界`。`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md` | 部分不对得上（L139 与 L140 方向相反） |

## Q2 · BROKEN / PARTIAL 逐条

- PARTIAL：0 条。
- BROKEN：10 条，坏路径与本次实际检查的绝对路径如下。

| fact_id | 坏路径（FACT_INDEX 原文） | 实际检查的绝对路径 |
|---|---|---|
| F17 | `R14_COMMON.md(§2.6四·L215; §2.10一)` | `D:\Project\ra2-campaign-forge\R14_COMMON.md` |
| F18 | `GATE_BEHAV\CASES.tsv` | `D:\Project\ra2-campaign-forge\GATE_BEHAV\CASES.tsv` |
| F18 | `GATE_BEHAV\PROGRESS.md(第二/三步)` | `D:\Project\ra2-campaign-forge\GATE_BEHAV\PROGRESS.md` |
| F18 | `R14_COMMON.md(§2.6四)` | `D:\Project\ra2-campaign-forge\R14_COMMON.md` |
| F19 | `R14_COMMON.md(§2.9二)` | `D:\Project\ra2-campaign-forge\R14_COMMON.md` |
| F19 | `R17_R8_RESIDUAL` | `D:\Project\ra2-campaign-forge\R17_R8_RESIDUAL` |
| F19 | `R17_AUDIT_R9(B1)` | `D:\Project\ra2-campaign-forge\R17_AUDIT_R9` |
| F19 | `R17_R10_DISPATCH` | `D:\Project\ra2-campaign-forge\R17_R10_DISPATCH` |
| F19 | `R17_AUDIT_R10` | `D:\Project\ra2-campaign-forge\R17_AUDIT_R10` |
| F19 | `R17_R26_HOST_ROLE` | `D:\Project\ra2-campaign-forge\R17_R26_HOST_ROLE` |
| F19 | `R17_R29_UPSTREAM` | `D:\Project\ra2-campaign-forge\R17_R29_UPSTREAM` |
| F20 | `LEAD_LOCK(AG4/AE7/AD2)` | `D:\Project\ra2-campaign-forge\LEAD_LOCK` |
| F20 | `R17_R36_VERIFY_TABLEBASE` | `D:\Project\ra2-campaign-forge\R17_R36_VERIFY_TABLEBASE` |
| F20 | `R17_AUDIT_R30` | `D:\Project\ra2-campaign-forge\R17_AUDIT_R30` |
| F21 | `R17_R35_V5657A0_TABLE` | `D:\Project\ra2-campaign-forge\R17_R35_V5657A0_TABLE` |
| F21 | `R17_R36_VERIFY_TABLEBASE` | `D:\Project\ra2-campaign-forge\R17_R36_VERIFY_TABLEBASE` |
| F22 | `R17_DELIVERY\DELIVERY_SUMMARY.md(§1 L1–L3)` | `D:\Project\ra2-campaign-forge\R17_DELIVERY\DELIVERY_SUMMARY.md` |
| F22 | `COVERAGE\PANEL.md(L146–337, M69–M102)` | `D:\Project\ra2-campaign-forge\COVERAGE\PANEL.md` |
| F22 | `R14_COMMON.md(§12.6, §16.1 判据)` | `D:\Project\ra2-campaign-forge\R14_COMMON.md` |
| F23 | `R17_DELIVERY\DELIVERY_SUMMARY.md(§2)` | `D:\Project\ra2-campaign-forge\R17_DELIVERY\DELIVERY_SUMMARY.md` |
| F23 | `COVERAGE\PANEL.md(M86–M93)` | `D:\Project\ra2-campaign-forge\COVERAGE\PANEL.md` |
| F24 | `R17_DELIVERY\DELIVERY_SUMMARY.md(§3 行 5)` | `D:\Project\ra2-campaign-forge\R17_DELIVERY\DELIVERY_SUMMARY.md` |
| F24 | `R14_COMMON.md(§16.1 判据)` | `D:\Project\ra2-campaign-forge\R14_COMMON.md` |
| F24 | `MED675 相关产物` | `D:\Project\ra2-campaign-forge\MED675 相关产物` |
| F24 | `R16 续线台账 §1054` | `D:\Project\ra2-campaign-forge\R16 续线台账 §1054` |
| F25 | `RULING_R15_20261119\work\strict_panel.py(L78)` | `D:\Project\ra2-campaign-forge\RULING_R15_20261119\work\strict_panel.py` |
| F25 | `R17_DELIVERY\DELIVERY_SUMMARY.md(§1 表)` | `D:\Project\ra2-campaign-forge\R17_DELIVERY\DELIVERY_SUMMARY.md` |
| F25 | `COVERAGE\PANEL.md(L139–140, M58 界向更正)` | `D:\Project\ra2-campaign-forge\COVERAGE\PANEL.md` |
| F26 | `PENDING_DECISIONS.md(D-49 已裁决条)` | `D:\Project\ra2-campaign-forge\PENDING_DECISIONS.md` |
| F26 | `R14_COMMON.md` | `D:\Project\ra2-campaign-forge\R14_COMMON.md` |

## Q3 · F22–F26 与交付摘要一致性

### 逐条结论

| fact_id | 对照位置 | 结论 |
|---|---|---|
| F22 | 交付摘要 §1 L1–L3 | 一致。F22 三项限定与 L1=791、L2=A458/B291、L3=真两链65/勿引304 对上；L2 另列宽293，F22 三项限定未要求该项，未见冲突。 |
| F23 | 交付摘要 §1 L2 / §2 | 一致。A458/B291/宽293/完全无④1196 与摘要对上；F23 的 A−B=167 由 458−291 得同值。 |
| F24 | 交付摘要 §1 L1 / §2 / §3 行5 | 核心数字一致：R_OK 863、R_MISSING 0、R_TRACE_ONLY 791、675 子集与四环回指 0、正控 11/11 均可在摘要中对应；摘要未展开 23,791 文件 / 1.29 GB，该细节本次未在摘要内核到。 |
| F25 | 交付摘要 §1 表 / §2 / §3 行6；PANEL L139–140 | strict 1,331 与摘要一致；界向与摘要 §3 行6、PANEL L140 一致，但与 PANEL L139 原文不一致（两处原文并列如下，未裁定）。 |
| F26 | 交付摘要 §2 尾段 / §4 尾段 | 与摘要一致：DoD 判据不改、上限/名义 3/22（S15/S16/S17）、严格 1/22、目标改为事实底座可交付完整度。其 `PENDING_DECISIONS.md` 证据路径在指定仓库根下未取得，D-49 原文本次未核。 |

### F25 界向：不一致处原文并列（不裁定）

**FACT_INDEX F25 原文：**
> TOTAL strict = 1,331（口径：atlas 内 ∧ [已证] ∧ 语义不含字面「[未证]」），名义 3/22（S15/S16/S17）、严格 1/22（S17）；该 1,331 是**上界不是下界** —— 它排不掉「语义引自文档、从不自陈未证」的行 ⇒ 1,331 不是「合规已证总量」。

**交付摘要 §3 行6 原文（与 F25 同向）：**
> | 6 | **`proved_strict` 的界向** | 它是**上界不是下界**（排不掉「语义引自文档、从不自陈未证」的行）；1,331 不是「合规已证总量」 | 照录 `COVERAGE/PANEL.md` L139–140（M58 界向更正） |

**PANEL L139 原文（与 F25 反向）：**
> > **M54 限定（对外引用必带）**：`proved_strict` 只是下界——它排不掉「语义引自文档、从不自陈未证」的行（`004AB9B0` 是实例）；**1,138 不是「合规已证总量」**，对外引用此数必须带此限定。

**PANEL L140 原文（与 F25 同向）：**
> > 📌 **界向更正（M58）**：上面 L134/L138 把 `proved_strict` 说成「下界」**方向标反**——它是**上界**。证明与两个反例见 `BOUND_DIR\REPORT.md`；本表内所有把该列当达标证据的读数，一律以该报告 §4 的改述为准。

### F22 三项限定与摘要 L1–L3 原文（一致对照）

**FACT_INDEX F22 原文：**
> 全表 [已证] 1,654 行；引用时必须与三项限定同框：① 其中 791 行以 classification_trace 为唯一 evidence_path；② ④ 口径 A 458（27.69%）vs 口径 B 291（17.59%）并列；③ 同格两条 ④ 的真两链 65 行（字面数 304 虚高 4–5 倍，勿引 304）。单独引用 1,654 = 把「按现行口径计分」误读成「四环齐全」。

**交付摘要 L1：**
> | L1 | 其中以 `classification_trace` 为**唯一** `evidence_path` | **791** | 这 791 行在**事实层面没有逐 entry 四环证据**（R16 已用 675 行全量内容级搜索 + 异族审计确认四环回指 = 0、正控 11/11 召回），**不是指针没连上**。规范出处：卡面写作 `R14_COMMON §12.5`，盘上该表述实际在 **`§16.1` 判据 4**（`§12.5` 现为 S17 名字口径更正）——两处编号**并列照录**，本卡不自行统一 | 791 自行复算；编号分歧照录 |

**交付摘要 L2：**
> | L2 | 其中 ④ 的三口径（**只限第 4 列**） | **A 458（27.69%）／B 291（17.59%）／宽 293（17.71%）** | **A** = 第 4 列含字符 `④`（**形态混杂**，含子句编号与标签）；**B** = 含 `④ 活表槽位见证`；**宽口径**另含 2 行 `④ direct call`（`004AF540`／`004B5AB0`）= 293。**禁止把 A 当「四环齐全」**，也禁止用 A 代表「④ 已写实」 | 自行复算 |

**交付摘要 L3：**
> | L3 | 其中「同格两条 ④」的**真两链** | **65** | 字面数 **304 复现不出来**：R17 实测**并表前 373／306、并表后 375／308**（373 = 第 4 列 `④` 字面 ≥2 次；306 = `④` 后带空格 ≥2 次；两者都是**字面口径**，不是真两链）。**304 与 373 都不得当事实引用**，**也禁止引用字面 304** | 65 照录 `R16_HYGIENE_R16/REPORT.md` §3／§7-B1（R16 卫生普查卡）；373/306/375/308 自行复算 |

## Q4 · F01–F21 随机抽样（6 条）

- 随机方法：固定 LCG 种子 `20261121`，在 F01–F21 无放回抽 6 条；关键数字为每条 statement 中预置的代表性数字。
- 命中判定：按指定仓库根解析 evidence_paths，读取存在的文件；命中任一存在文件即记“命中”。若路径全不存在，记“未取得（路径不解析）”，不把 run 内相对路径自行补前缀。
- 抽样结果：F11、F06、F21、F16、F19、F18；命中 3/6。

| fact_id | 关键数字 | 结果 | 核对详情 |
|---|---|---|---|
| F11 | 397 | 命中 | `lead\next_re_20261117_r14\R17_LEDGER_1062\SECTION.md`、`lead\next_re_20261117_r14\STATUS_BOARD.md` 均含 397。 |
| F06 | 117 | 命中 | `lead\next_re_20261117_r14\STATUS_BOARD.md`、`lead\next_re_20261117_r14\R17_LEDGER_1064\SECTION.md`、`lead\next_re_20261117_r14\R14_COMMON.md` 均含 117。 |
| F21 | 0x40000 | 未取得（路径不解析） | `D:\Project\ra2-campaign-forge\R17_R35_V5657A0_TABLE`、`D:\Project\ra2-campaign-forge\R17_R36_VERIFY_TABLEBASE` 均不存在。 |
| F16 | 51 | 命中 | `lead\next_re_20261117_r14\STATUS_BOARD.md`、`lead\next_re_20261117_r14\R14_COMMON.md`、`lead\next_re_20261117_r14\R17_LEDGER_1063\SECTION.md`、`lead\next_re_20261117_r14\R17_LEDGER_1062\SECTION.md` 均含 51。 |
| F19 | 387 | 未取得（路径不解析） | `D:\Project\ra2-campaign-forge\R14_COMMON.md`、`D:\Project\ra2-campaign-forge\R17_R8_RESIDUAL`、`D:\Project\ra2-campaign-forge\R17_AUDIT_R9`、`D:\Project\ra2-campaign-forge\R17_R10_DISPATCH`、`D:\Project\ra2-campaign-forge\R17_AUDIT_R10`、`D:\Project\ra2-campaign-forge\R17_R26_HOST_ROLE`、`D:\Project\ra2-campaign-forge\R17_R29_UPSTREAM` 均不存在。 |
| F18 | 4/6 | 未取得（路径不解析） | `D:\Project\ra2-campaign-forge\GATE_BEHAV\CASES.tsv`、`D:\Project\ra2-campaign-forge\GATE_BEHAV\PROGRESS.md`、`D:\Project\ra2-campaign-forge\R14_COMMON.md` 均不存在。 |

未命中 fact_id 与数字：F21 `0x40000`；F19 `387`；F18 `4/6`。三者在指定仓库根下均因 evidence_paths 不解析而未取得，非“查到文件但数字缺失”。

## 产物自检

- `paths.tsv`：71 条路径检查 + 1 行表头。
- `work.py`：可复跑路径解析部分（读取 v3.1 索引，覆盖写 `paths.tsv`）。
- 三产物逐字节检查 0x0D：均为 0。
