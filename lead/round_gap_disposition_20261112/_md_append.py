# -*- coding: utf-8 -*-
"""由 ROUND_GAP_DISPOSITION.csv 生成 ROUND_GAP_DISPOSITION.md 的 §2-§7。
逐节 append + flush + fsync 落盘（防卡死）。只读 CSV，不重跑枚举。
用法: python -I -X utf8 <绝对路径>\\_md_append.py
"""
import io
import os
import csv

SELF = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(SELF, "ROUND_GAP_DISPOSITION.md")
CSV = os.path.join(SELF, "ROUND_GAP_DISPOSITION.csv")

with io.open(CSV, encoding="utf-8-sig", newline="") as f:
    ROWS = list(csv.DictReader(f))


def cell(s):
    return s.replace("|", r"\|").replace("\r", " ").replace("\n", " ")


def brief(s, n=70):
    s = cell(s)
    return s if len(s) <= n else s[:n] + "…"


fh = io.open(MD, "a", encoding="utf-8", newline="\n")


def emit(text, tag):
    fh.write(text)
    fh.flush()
    os.fsync(fh.fileno())
    print("[flushed] " + tag, flush=True)


A = [r for r in ROWS if r["类别"] == "有md报告"]
B = [r for r in ROWS if r["类别"] == "无报告有探针或输出"]
C = [r for r in ROWS if r["类别"] == "递归空"]

# ============================== §2 ==============================
s = []
s.append(r"""## §2 三类清单

> 三张表按 CSV 原有顺序（日期, 目录名）逐行生成；列为「目录名 / 日期 / 递归文件数 / 判定 / 理由摘要」。
> **22 个「无报告有探针或输出」与 12 个「递归空」逐个列出**（§2.2 / §2.3），是本任务的核心价值；
> 215 个「有md报告」逐行给出全量索引（§2.1），其判定与理由在 CSV 中 215 行完全同文。
> 理由摘要为 CSV「理由」列的机械截断（不改字），完整理由见 CSV 与 §3。

### 2.1 有md报告（A）— 215 个

> 下表 215 行的 CSV 原文判定一律为「已成立（有md报告，无需处置）」、理由一律为「递归含 md 报告，属 153/164 口径内已交付轮」；为控制篇幅，判定列缩写为「已成立」、理由摘要列缩写为「有md，已交付」。
> 其中日期 <20261106 的历史轮与 20261112 当日轮也都属此类（全树口径），**不要与窗口 153/164 混算**。

| 目录名 | 日期 | 递归文件数 | 判定 | 理由摘要 |
|:--|:--|--:|:--|:--|
""")
for r in A:
    s.append("| %s | %s | %s | 已成立 | 有md，已交付 |\n" % (cell(r["目录名"]), r["日期"], r["递归文件数"]))
s.append("\n**小计：215 行**（= 判定「已成立」215）。\n\n")
s.append(r"""### 2.2 无报告有探针或输出（B）— 22 个，逐个列出

| # | 目录名 | 日期 | 递归文件数 | 判定 | 理由摘要 |
|:--:|:--|:--|--:|:--|:--|
""")
for i, r in enumerate(B, 1):
    s.append("| %d | %s | %s | %s | %s | %s |\n" % (
        i, cell(r["目录名"]), r["日期"], r["递归文件数"],
        cell(r["判定"]), brief(r["理由"])))
s.append("\n**小计：22 行**（15 废弃中占 5 + 补做 7 + 已入他处 6 + 口径外登记 3 + 补做（进行中）1 = 22）。\n\n")
s.append(r"""### 2.3 递归空（C）— 12 个，逐个列出

| # | 目录名 | 日期 | 递归文件数 | 判定 | 理由摘要 |
|:--:|:--|:--|--:|:--|:--|
""")
for i, r in enumerate(C, 1):
    s.append("| %d | %s | %s | %s | %s | %s |\n" % (
        i, cell(r["目录名"]), r["日期"], r["递归文件数"],
        cell(r["判定"]), brief(r["理由"])))
s.append("\n**小计：12 行**。其中 11 个落在窗口 `[20261106..20261111]`（即报告口径的 11 个空轮），第 12 个是本检查写域 `round_gap_disposition_20261112`（日期 20261112，窗口外）——这正是「全树 12」与「窗口 11」的差，不是矛盾。\n\n")
emit("".join(s), "§2")

# ============================== §3 ==============================
s = []
s.append(r"""## §3 逐个判定的依据

> 四组按**判定维度**分列，允许交叉：12 个空轮中 10 个判「废弃」、1 个判「已入他处」、1 个为「本检查写域」；15 个废弃 = 10 个空轮 + 5 个 B 轮；7 补做全为 B 轮；7 已入他处 = 1 个空轮 + 6 个 B 轮。四组合计 41 条，去重后覆盖 12 + 15 + 7 + 7 各判定项。
> 判定 / 理由 / 取代证据均取自 CSV（上一位执行方的定性），本报告只汇总与转录，**未逐条独立复核**（见 §6）。

### 3.1 12 个递归空：是否「已启动未落盘」+ 有无近名轮次已交付同类结论

> 「已启动未落盘」是**形态描述**：目录存在、递归 0 文件（CSV「递归文件数」=0、「有无md」= 无、「有无输出」= 无）。是否确曾启动过会话、由谁启动，本次**未验**。
> 近名 / 同类交付件取自 CSV「理由」「取代证据」列与 `lead/re_round_disposition_20261111/DISPOSITION.md` §4 空轮深度分析表（`L98-L111`）。

| # | 目录名 | 是否「已启动未落盘」 | 近名 / 同类轮次已交付同类结论（取代件） | 判定 |
|:--:|:--|:--|:--|:--|
""")
C_NOTES = [
    ("backlog_sweep_20261110", "是（0 文件）；是否确曾启动会话未验", "积压清理已被全盘进度审计 `re_progress_check_20261111` 与 `PENDING_DECISIONS` 治理吸收（`DISPOSITION.md:L80`；CSV 取代证据同）", "废弃"),
    ("crit_recheck_20261110", "是（0 文件）；是否确曾启动会话未验", "判据复验已由 `crit_fix_20261110` → `e3_fix2_20261110` → `e3_unify_20261111` 判据链交付（`DISPOSITION.md:L81`）", "废弃"),
    ("e3_rootcause_20261110", "是（0 文件）；是否确曾启动会话未验", "吞没异常根因已沉淀为 `e3_unify_20261111/_e3_v3.py` 七条缺陷修复规则（`DISPOSITION.md:L82`，`_e3_v3.py:L7-L35`）", "废弃"),
    ("e3_triage_20261110", "是（0 文件）；是否确曾启动会话未验", "413 件分流已由 `ok_falsify_20261110/_of_scope_out.json` 完成（`DISPOSITION.md:L83`）", "废弃"),
    ("ledger_apply_prep_20261110", "是（0 文件）；但目标**已完成并核验**", "§605–§609 五笔于 11-11 21:1x 并入主台账；取代件 `re_ledger_apply_20261111/APPLY_RECEIPT.md:L10-L23`、`re_ledger_verify_20261111/VERIFY.md:L16`（V1 PASS）、`GOAL_THREE_TARGETS_20261018.md:L9760/L9775/L9787/L9802/L9832`", "已入他处"),
    ("re_chain_semantics_20261110", "是（0 文件）；是否确曾启动会话未验", "0x54A56E 链语义由 `re_crashwriter_static_20261110/_cw_disasm_out.txt:L80-L105` 全量交付并升级为因果链报告（`DISPOSITION.md:L88`）", "废弃"),
    ("recon_20261110", "是（0 文件）；是否确曾启动会话未验", "宽泛静态侦察已分流为 `re_crashwriter_static` / `re_loadbench_diff` / `re_map_preset_decode` / `re_orphan_owners` 四个具体轮次（`DISPOSITION.md:L90`）", "废弃"),
    ("housecount_trace_20261111", "是（0 文件）；静态侧已闭环、动态侧被阻塞", "静态侧由 `playerctrl_semantics_20261111/_ps_disasm_out.txt:L636-L642` 交付；动态 trace 受 D-13 PAUSE/BLOCKED 阻塞（`RE_PROGRESS_20261111.md:L82`），属被阻塞非待补", "废弃"),
    ("ledger_num_audit_20261111", "是（0 文件）；是否确曾启动会话未验", "编号核验由 `re_progress_xverify_20261111/VERDICT.md §1` 闭环；并账 / 核验由 `re_ledger_apply` / `re_ledger_verify` 完成（`DISPOSITION.md:L86`）", "废弃"),
    ("mapfile_1680_hunt_20261111", "是（0 文件）；是否确曾启动会话未验", "1680/1120 载体寻源由 `re_loadbench_diff_20261110/_ld_diff_out.txt:L101` 与 `re_map_preset_decode_20261110/_md_parse_out.txt` 尾节完成（`DISPOSITION.md:L87`）", "废弃"),
    ("re_line_collapse_20261111", "是（0 文件）；是否确曾启动会话未验", "轮次收缩治理已被 `re_round_disposition_20261111` 写域全盘接管（`re_dispatch_20261111/BRIEF_D.md:L1`；`DISPOSITION.md:L89`）", "废弃"),
    ("round_gap_disposition_20261112", "**不适用**：本检查写域，非项目轮次（枚举时点 0 文件）", "无同类结论可取代；本目录即本次成文写域（判定「本检查写域」）", "本检查写域"),
]
for i, (n, started, near, j) in enumerate(C_NOTES, 1):
    s.append("| %d | %s | %s | %s | %s |\n" % (i, n, started, near, j))
s.append("\n**逐条结论**：12 个全部递归 0 文件；11 个项目轮次中 10 个有「近名 / 同类轮次已交付同类结论」，1 个（`ledger_apply_prep`）虽为空目录但目标已由他处完成并核验，故判「已入他处」而非废弃；第 12 个是本任务写域，不计项目进度。\n\n")

s.append(r"""### 3.2 15 个废弃：每个点名取代件（取自 CSV「取代证据」列，逐字转录）

| # | 目录名 | 取代件（CSV「取代证据」原文） | 一句话理由（CSV「理由」摘要） |
|:--:|:--|:--|:--|
""")
ABANDON = [r for r in ROWS if r["判定"] == "废弃"]
for i, r in enumerate(ABANDON, 1):
    s.append("| %d | %s | %s | %s |\n" % (
        i, cell(r["目录名"]), cell(r["取代证据"]), brief(r["理由"], 90)))
s.append("\n**小计：15 个，每个都有具名取代件**；`const_exit_fix_20261110` 的「取代件」列还额外登记了与 `DISPOSITION.md:L62`（判「补做」并称 VERIFY_A8 实跑 ALL PASS）的分歧：CSV 理由明确写「本目录无落盘输出，实跑未验——本次改判废弃，分歧如实登记」。\n\n")

s.append(r"""### 3.3 7 个补做：缺什么、需要什么输入

> 「缺什么」取自 CSV「理由」列；「需要什么输入」优先取 CSV 理由中的「输入=…」，其余转引 `DISPOSITION.md` §3（L62-L79）的「需输入…」行，均注明出处。本次**未核输入件现值**（§6）。

| # | 目录名 | 缺什么 | 需要什么输入 | 建议批次（CSV） |
|:--:|:--|:--|:--|:--|
""")
TODO = [
    ("dup_audit_20261110", "缺一页 md 结论与台账条目（读数已齐：2928 个 .py 只读普查、2517 个唯一 sha256、72 组重复）", "既有两件输出 `_da_summary.txt` + `_da_groups.json`（CSV 理由「输入=既有两件输出」；`DISPOSITION.md:L64`）", "第二批（补md，工作量小）"),
    ("exit_lint_20261110", "判据底座仍挂旧版 `_ec_criterion`；缺对接 `_e3_v3.py` 的改造与自测记录", "测试脚本集（`DISPOSITION.md:L69`）；对接目标 `e3_unify_20261111/_e3_v3.py`", "第三批"),
    ("gate_exit_retrofit_20261110", "patched/ 24 个改造脚本缺统一回归日志与验收报告（对照件 `_gr_template_ctl_run.txt` 已实跑：-1→exit 0、1→exit 1）", "测试集运行验证（`DISPOSITION.md:L70`）；对照件 `_gr_template_ctl_run.txt:L37-L39`", "第三批"),
    ("ledger_exit_census_20261110", "缺 md 沉淀（读数已齐：三本台账 76 处 EXIT=0，分布 31/1/44；cls 计数 5/28/1/2/40）", "既有 `_lc_out.txt:L8-L15`（`DISPOSITION.md:L71`）", "第二批（补md）"),
    ("ok_falsify_20261110", "缺 md 沉淀（读数已齐：413 件三维交叉表，_of_scope_out.json 97,659 B）", "既有 `_of_scope_out.json:L3390-L3430`（`DISPOSITION.md:L72`）", "第二批（补md）"),
    ("unknown_locate_20261110", "缺 md 沉淀（读数已齐：263 件 NO_EXIT_AT_ALL 的 stdout 产物通道普查，11 件仅 stdout.write：9 UNKNOWN + 2 ARTIFACT）", "既有 `_ul_stdout_census_out.txt:L22-L37`（`DISPOSITION.md:L79`）", "第二批（补md）"),
    ("e3_unify_20261111", "统一判据本体 `_e3_v3.py`（22,608 B）就绪但零跑测输出、零 md；缺 413 件全量扫描与 `E3_UNIFY.md` 验收报告", "`ok_falsify_20261110/_of_scope_out.json` 的 413 件清单（CSV 理由「输入=…」；`DISPOSITION.md:L67`）", "第二批（高优先）"),
]
for i, (n, miss, need, batch) in enumerate(TODO, 1):
    s.append("| %d | %s | %s | %s | %s |\n" % (i, n, miss, need, batch))
s.append("\n**小计：7 个**；其中 4 个（`dup_audit` / `ledger_exit_census` / `ok_falsify` / `unknown_locate`）读数已齐、只缺一页 md，2 个（`exit_lint` / `gate_exit_retrofit`）需改造与回归，1 个（`e3_unify`）需 413 件全量扫描。\n\n")

s.append(r"""### 3.4 7 个已入他处：结论在哪份 md 的哪一行（取自 CSV「取代证据」列，逐字转录）

| # | 目录名 | 结论所在 md 与行号（CSV「取代证据」原文） | 一句话理由（CSV「理由」摘要） |
|:--:|:--|:--|:--|
""")
ELSEWHERE = [r for r in ROWS if r["判定"] == "已入他处"]
for i, r in enumerate(ELSEWHERE, 1):
    s.append("| %d | %s | %s | %s |\n" % (
        i, cell(r["目录名"]), cell(r["取代证据"]), brief(r["理由"], 90)))
s.append("\n**小计：7 个**；结论分别落在 `CHAIN_SYNTHESIS.md`（③/④/⑤）、`RE_PROGRESS_20261111.md` §8、`ROUND_BATCH1.md`、`APPLY_RECEIPT.md` / `VERIFY.md` / 主台账 §605–§609 等行号处。**这些行号本次未逐条打开验证**（§6）。\n\n")

s.append(r"""### 3.5 其余 5 条（补足 249 的判定分布）

- **口径外登记 3**（均为 B 类、日期 <20261106）：`qc151_carrierfix_20261020`（carrierfix.diff + report.json）、`t55k_20261020`（10 月真机测量数据轮 T55k 全套 receipt/measure）、`goal1_harness8_20261031`（10 月 harness8 判据/启动脚本族 + .mimosa 钩子状态件）。CSV 理由统一为「日期 <20261106，不在报告 182 口径内；是否补报告由十月线自行定」。
- **本检查写域 1**：`round_gap_disposition_20261112`（见 §3.1 第 12 行）。
- **补做（进行中）1**：`re_atlas_reassess_20261112`（20261112 当日新轮，报告口径外；R-036 重算 8/8 PASS、R-035 复核 23/23 PASS；CSV 判「登记不判」，建议批次「口径外（进行中）」）。

""")
emit("".join(s), "§3")

# ============================== §4 ==============================
emit(r"""## §4 排序与三批建议

> 排序只在本 CSV 的判定集合内做，不新造判据。「最值得补做」取 7 个「补做」；「最可安全废弃」取 15 个「废弃」。
> 如实登记一处**跨文件分歧**：`DISPOSITION.md:L149-L158` 的 Top-5 补写轮次是 `re_crashwriter_static` / `slot2_fullscan` / `playerctrl_semantics` / `re_loadbench_diff` / `re_map_preset_decode`，而本 CSV 把这 5 个判为「已入他处」（结论已入因果链报告，不另补 md）。两份定性不一致，本报告按 CSV 汇总、不裁决（§6）。

### 4.1 最值得补做的前 5 个（一句话理由 + 需要什么输入）

| 序 | 目录名 | 一句话理由 | 需要什么输入 |
|:--:|:--|:--|:--|
| 1 | `e3_unify_20261111` | 统一 E3 判据（修七条已知缺陷）是出口判据治理的收口件，且 CSV 唯一标「第二批（高优先）」，但零跑测输出、零 md | `ok_falsify_20261110/_of_scope_out.json` 的 413 件清单 + 既有 `_e3_v3.py` |
| 2 | `dup_audit_20261110` | 2928 个 .py / 2517 个唯一 sha256 / 72 组重复的物理哈希基准，读数已齐，只缺一页 md，性价比最高 | 既有 `_da_summary.txt` + `_da_groups.json` |
| 3 | `ok_falsify_20261110` | 413 件全量出口判据三维交叉表（含 18 个 UNKNOWN+NEEDS_FIX），是 `e3_unify` 与门禁标准化的共同输入 | 既有 `_of_scope_out.json`（97,659 B） |
| 4 | `ledger_exit_census_20261110` | 三本台账 76 处 EXIT=0 分布（31/1/44）与 const_exit 413 普查对齐，读数已齐 | 既有 `_lc_out.txt:L8-L15` |
| 5 | `unknown_locate_20261110` | 263 件 NO_EXIT_AT_ALL 的 stdout 产物通道普查（11 件仅 stdout.write），读数已齐 | 既有 `_ul_stdout_census_out.txt:L22-L37` |

（第 6–7 位为 `gate_exit_retrofit_20261110` 与 `exit_lint_20261110`，二者需改造/回归而非仅补 md，故排后。）

### 4.2 最可安全废弃的前 5 个（一句话理由 + 取代证据）

| 序 | 目录名 | 一句话理由 | 取代证据（CSV 原文缩写） |
|:--:|:--|:--|:--|
| 1 | `esi_caller_trace_20261111` | slot2 调用点首轮普查已被 100% 分块重验逐数复现并加固，读数被完整继承 | `slot2_fullscan_20261111/_sf_scan_out.txt` T1/T4/T5-final 节；`DISPOSITION.md:L68` |
| 2 | `crit_fix_20261110` | E3 判据 v1 修补，被 e3_fix2 消费为 before 基线、最终被 v3 统一取代 | `e3_fix2_20261110/_before.json` 头部 criterion 字段指向本目录 `_ec_criterion_fixed.py`；`DISPOSITION.md:L63` |
| 3 | `e3_fix2_20261110` | E3 判据 v2 的 7 正控 3 负控跑测，被 `_e3_v3.py` 吸收终结，数据件留作过程证据 | `e3_unify_20261111/_e3_v3.py` 文档串「统一两套既有实现的正确部分，修七条已知缺陷」；`DISPOSITION.md:L65` |
| 4 | `e3_secondimpl_20261110` | 独立第二实现（AST-only，刻意不看参考实现）背靠背对照使命完成，被 v3 吸收 | `e3_unify_20261111/_e3_v3.py`；`DISPOSITION.md:L66` |
| 5 | `re_chain_semantics_20261110` | 空目录；0x54A56E 链语义已由全量静态反汇编交付并升级为因果链报告 | `re_crashwriter_static_20261110/_cw_disasm_out.txt:L80-L105`；`DISPOSITION.md:L88` |

（其余 10 个废弃同样各有取代件，见 §3.2；本任务**不执行**任何废弃 / 清理动作。）

### 4.3 三批推进建议

| 批次 | 内容 | 前置 / 输入 | 理由 |
|:--|:--|:--|:--|
| **第一批（立刻做）** | 4 个「读数已齐、只缺一页 md」：`dup_audit` / `ledger_exit_census` / `ok_falsify` / `unknown_locate`，各写 1 页结论 md 并登记台账条目 | 仅需各自已落盘的 `_out.txt` / `.json`；零跑测、零真机 | 工作量最小、可立即把 4 个「原始读数」转成「已成立结论」；不触碰任何既有件 |
| **第二批** | `e3_unify` 的 413 件全量扫描 + `E3_UNIFY.md`；`gate_exit_retrofit` 24 个 patched 脚本统一回归；`exit_lint` 对接 `_e3_v3.py` 并自测；`re_atlas_reassess_20261112` 待其进行中状态结束后再判 | `_of_scope_out.json` 413 件清单、测试集、`_e3_v3.py` | 需要实际跑测或改造，依赖更重；`e3_unify` 是判据收口，优先级最高 |
| **暂缓** | 15 个废弃 + 12 个空轮的物理清理 / 归档；`housecount_trace_20261111` 的动态 trace；口径外 3 件是否补报告 | D-13 解禁、台账所有者授权、十月线自定 | 本任务只汇总不处置；删除 / 归档需授权；D-13 仍 PAUSE/BLOCKED；口径外日期 <20261106 不属本窗口 |

""", "§4")

# ============================== §5 ==============================
emit(r"""## §5 进度口径建议

**一句话：这个项目的「进度」只数「有 md 报告且结论已入账」的轮次——目录数不能当进度、无 md 的探针轮算「原始读数」不算「已成立结论」、空轮算 0；且任何计数必须绑定统计时点。**

落到本次 249 条：215 个「已成立」可作分子上限（其中还含 5 个 20261112 当日新增与 3 个口径外 B 件需各自标注），22 个 B 轮只是一手读数、不得计入「已成立结论」，12 个空轮计 0；182 / 193 / 249 分属不同口径与时点，不可互相代替。理由见 §1.4：目录计数是「活动量」不是「完成量」，连「带 md 的目录数」也会随会话单向增长。此建议与项目既有纪律「有目录 ≠ 有交付」（`ROUND_REPORT.md:137` 引 G-55 / G-57、`RE_PROGRESS_20261111.md:157-158`）一致。

""", "§5")

# ============================== §6 ==============================
emit(r"""## §6 边界与未验（如实）

1. **CSV 的「理由」列内容未逐条独立复核**。249 条判定是上一位执行方（WP-O）的人工定性，本任务只汇总、转录、排序，不重新审定。`ROUND_REPORT.md:179,229` 明记「WP-H / WP-O / WP-K2 的中间产物未被任何人复核，其正确性未验」；本次收尾未改变这一状态。
2. **「取代证据」未逐个打开验证**。§3.2 / §3.4 的取代件名与 `文件:行` 是 CSV 原文转录，除本报告明确读过的 `DISPOSITION.md`、`ROUND_REPORT.md`、`RE_PROGRESS_20261111.md` §9、`status_panel_20261112` 指纹 / 面板件、`docs_drift_20261112` 指纹表外，取代件是否仍然存在、行号是否对得上、结论是否真的覆盖，**均未验**。
3. **探针本身未运行；零真机**。本任务未执行任何探针 / 判据脚本，未启动 gamemd.exe / ra2loader / YURI.exe，未 attach、未读活进程内存、未写 hook / 采样 / MiniDump 代码。CSV 理由中「实跑」「ALL PASS」「8/8 PASS」「23/23 PASS」等字样均为上一位执行方或原轮次的转述，本次**未复跑、未验**。
4. **未重跑枚举**。只读了已有 `ROUND_GAP_DISPOSITION.csv` / `_enum_rounds.json` / `_enum_rounds_stdout.txt` / `_probe_digest.txt` / `_verify_census_stdout.txt` / `_final_hashes.txt` / `_build_csv.py` / `_enum_rounds.py` / `_verify_census.py`；未执行 `_enum_rounds.py` / `_verify_census.py` / `_probe_digest.py` / `_build_csv.py`。§1.3.1 的 mtime 是本次对 24 个顶层目录的**只读 `os.stat` 实算**，但 Windows 的 birth(ctime) 会受复制 / 解压影响，不等同「会话创建时刻」；5/4/2 时段分组转引派工书已知事实与 `ROUND_REPORT.md:133-134`，**未独立复核会话日志**。
5. **两处「最后 2 个新增」口径不同、未裁决**：`ROUND_REPORT.md:133` 指 `slot2_fullscan` / `playerctrl_semantics`（21:16「由 B 类计入」，本次 CSV 中仍为 B 类 md=0），而 §1.3.1 表第 10–11 行取的是 11-11 当天由无报告态补齐 md 的 2 个 A 类元轮次 `re_progress_check` / `re_progress_xverify`。两者不同源，本报告并列登记、不合并、不裁决。
6. **时点快照仍在 churn**：`_verify_census_stdout.txt:84-93` D 段已记录枚举后新增 `re_chain_v2_xverify_20261112`（现在顶层 250）；本写域自身也从枚举时点的 0 文件变成含本报告与两个脚本，故「本检查写域（C 类）」判定仅对枚举时点成立。249 / 193 / 182 均已绑定各自时点。
7. **「已启动未落盘」是形态而非事实认定**：12 个空轮递归 0 文件可证「无落盘产物」，但「是否曾启动会话」需要会话日志，本次未验（§3.1）。
8. **§3.3「需要什么输入」部分转引 `DISPOSITION.md` §3**，未核这些输入件的当前存在性与现值；§4.1 排序、§4.2 排序、§4.3 三批划分是本报告基于 CSV 理由做的编排建议，不是上一位执行方的原判，也未经台账所有者批准。
9. **跨文件判定分歧如实登记、未裁决**：① `const_exit_fix_20261110` — `DISPOSITION.md:L62` 判「补做」并称 `VERIFY_A8.py:L824-L826` 实跑 ALL PASS，CSV 改判「废弃」且注明「本目录无落盘输出，实跑未验」；② `ledger_apply_prep_20261110` — `DISPOSITION.md:L85` 判「补做 P1」（21:05，早于并账落盘 21:16），CSV 据实修正为「已入他处」；③ `DISPOSITION.md` Top-5 补写轮次在 CSV 中判「已入他处」（§4）。三者均不属本任务裁决范围。
10. **口径外 3 件**（日期 <20261106）是否补报告由十月线自定，本次未验；`re_atlas_reassess_20261112` 进行中、登记不判；D-13 仍 PAUSE/BLOCKED，`housecount_trace` 动态 trace 未立项。
11. **写域与副作用**：仅在 `lead\round_gap_disposition_20261112\` 内新增文件；未修改 / 覆盖 / 删除任何既有件与任何目录；未执行 git add / commit / push / reset / checkout；未执行任何处置动作（不补做、不废弃、不清理、不归档）。

""", "§6")

# ============================== §7 ==============================
emit(r"""## §7 收尾回执

**改了哪些文件**（全部在唯一写域 `lead\round_gap_disposition_20261112\` 内，均为新增）：

| 文件 | 性质 |
|:--|:--|
| `ROUND_GAP_DISPOSITION.md` | **主交付**（本文件，§1–§7） |
| `_md_verify.py` | 只读核验脚本：CSV/JSON 计数复核、hashlib 指纹实算、20261111/20261112 顶层目录 mtime 只读实算 |
| `_md_append.py` | 成文辅助脚本：由 CSV 生成 §2–§7，逐节 append + flush + fsync 落盘 |

**读了哪些文件（注明未重跑枚举）**：

- 写域内：`ROUND_GAP_DISPOSITION.csv`（250 行全文实读 + `csv.DictReader` 复核 249 数据行）、`_final_hashes.txt`、`_verify_census_stdout.txt`（全文）、`_build_csv.py`（全文）、`_enum_rounds.py`（全文）、`_verify_census.py`（全文）、`_enum_rounds.json`（由脚本只读解析，未全文通读）、`_enum_rounds_stdout.txt` / `_probe_digest.txt`（仅定向 grep 与 hashlib 实算，未全文通读）。
- 写域外（一律只读）：`lead\re_round_disposition_20261111\DISPOSITION.md`（全文）、`lead\re_session_kickoff_20261111\ROUND_REPORT.md`（全文）、`lead\re_session_kickoff_20261111\CHANNEL_TEST_AND_ASSESSMENT.md`（定向 grep）、`lead\re_progress_check_20261111\RE_PROGRESS_20261111.md`（§9 段）、`lead\status_panel_20261112\panel_forensics_stdout.txt` / `_panel_assemble_stdout.txt` / `STATUS_PANEL.md`（定向 grep）、`lead\docs_drift_20261112\_evidence\01_fact_side_fingerprints.md` / `DOCS_DRIFT_PROPOSAL.md` / `RECEIPT.md`（定向 grep）、`lead\re_dispatch_20261111\STATUS_BOARD.md`（定向 grep）。
- 只读 `os.stat`：20261111 顶层 19 个 + 20261112 顶层 5 个目录（共 24 个）的 mtime / ctime；未遍历、未写入。
- **未重跑枚举**：`_enum_rounds.py` / `_verify_census.py` / `_probe_digest.py` / `_build_csv.py` 均未执行；CSV、JSON、stdout、digest 都是上一位执行方实跑并在盘的产物。

**结论一句话**：全 `lead/` 树 249 个顶层轮次目录已逐条定性（215 已成立 / 22 原始读数 / 12 空轮；判定 215 已成立 + 15 废弃 + 7 补做 + 7 已入他处 + 3 口径外登记 + 1 本检查写域 + 1 补做进行中），窗口 182→193 的差 11 全部是 20261111 一天的新建/补齐所致、属时点差而非统计错误，进度只应数「已入账的已成立结论」。

**遗留未验项**：见 §6 全 11 条（重点是：CSV 理由未逐条复核、取代证据未逐个打开、探针未运行、11 个新增目录的时段归属未独立复核会话日志、两处跨文件判定分歧未裁决、12 个空轮是否真启动过未验）。所有处置动作（补做 / 废弃 / 清理）均**未执行**，留待授权。

---

> 本报告为「只差成文」收尾产物：枚举与定性全部由上一位执行方完成并在盘，本次零新增枚举、零真机、零处置、零 git 变更。
""", "§7")

fh.close()
print("final_size=%d B" % os.path.getsize(MD), flush=True)
