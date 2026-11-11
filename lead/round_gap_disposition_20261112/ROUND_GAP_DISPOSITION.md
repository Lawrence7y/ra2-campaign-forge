# ROUND_GAP_DISPOSITION · 空轮 / 无报告轮处置汇总（收尾成文）

> 执行方：受限执行方（WP-O2「只差成文」收尾）｜成文时点：2026-11-12 01:5x（Asia/Shanghai）
> 工作区：`D:\Project\ra2-campaign-forge`｜**唯一写域**：`lead\round_gap_disposition_20261112\`
> 铁律遵守：**零真机**（未启动 gamemd.exe / ra2loader / YURI.exe，未 attach、未读活进程内存）；除本写域外全部只读；未执行 git commit / push / reset / checkout；**未删除任何目录**；**未重跑枚举**；python 一律 `python -I -X utf8 <绝对路径>`；指纹一律 hashlib 实算。
> 本任务性质：把上一位执行方**已完成并在盘**的枚举与定性（`ROUND_GAP_DISPOSITION.csv`，249 条，每条都有判定）汇总成可读报告；**只汇总，不执行处置**（不补做、不废弃、不清理、不改动既有件）。

---

## §1 枚举口径与总数

### 1.1 枚举范围与口径

- **范围**：`lead/` **全树**，目录名 basename 匹配 `2026\d{4}$` 的轮次目录（含嵌套层级），`os.walk` **递归**计数；文件归属「最近的祖先轮次目录」，嵌套不重复计；本写域 `round_gap_disposition_20261112` 在枚举时被排除（`_enum_rounds.py:5-12, 27-29, 40-65`）。
- **三类定义**（`_enum_rounds.py:8, 99-104`）：`A` = 递归含 `.md` 报告；`B` = 无 md 但递归非空（探针 / 输出件）；`C` = 递归后仍 0 文件（可有空子目录）。
- **主表口径**：`ROUND_GAP_DISPOSITION.csv` 取枚举快照中 **depth=0 的顶层轮次目录 249 条**（`_build_csv.py:15`），按 `(日期, 目录名)` 排序；10 列 = `目录名,日期,类别,递归文件数,有无md,有无输出,判定,理由,取代证据,建议批次`。CSV 为 `utf-8-sig`，本次用 `csv.DictReader` 实读复核。
- ★ **必须与窗口口径分开**：**249 = 全 `lead/` 树**（日期跨度 20261018–20261112）的顶层目录数；**182 / 193 只统计窗口 `[20261106..20261111]`** 的顶层目录（`_verify_census.py:34-38`）。本报告凡出现 249 / 215 / 22 / 12 均指**全树口径**；凡出现 182 / 193 / 153 / 164 / 18 / 11 均指**该窗口口径**。**两者不得混用、不得相减**。

### 1.2 三类总数与判定总数（本次独立复核）

只读核验脚本 `_md_verify.py`（`python -I -X utf8` 实跑）读 CSV 与 `_enum_rounds.json` 得：

| 类别 | 条数 | 含义 |
|:--|--:|:--|
| 有md报告（A） | **215** | 递归含 md 报告 |
| 无报告有探针或输出（B） | **22** | 无 md、递归非空 |
| 递归空（C） | **12** | 递归 0 文件 |
| **合计** | **249** | 与派工书给值一致 |

| 判定 | 条数 |
|:--|--:|
| 已成立（有md报告，无需处置） | **215** |
| 废弃 | **15** |
| 补做 | **7** |
| 已入他处 | **7** |
| 口径外登记 | **3** |
| 本检查写域 | **1** |
| 补做（进行中） | **1** |
| **合计** | **249** |

判定合计 249 与类别合计 249 一致；分布与派工书给值逐项吻合。另复核 `_enum_rounds.json`：`records=495`（任意深度），`depth=0` 顶层 `=249`，窗口 `[20261106..20261111]` 顶层 `n=193 A=164 B=18 C=11`（`_verify_census_stdout.txt:21` 同值）。

**指纹实算**（`hashlib.sha256`，本次重算，与 `_final_hashes.txt` 逐条一致）：`ROUND_GAP_DISPOSITION.csv` 48,977 B / `462b518bea37d2099a6a3a688d649f55a78f974333d195ad9502090a22719b89`；`_enum_rounds.json` 1,889,654 B / `6ca9a084cba2d7637f7ff8a8a871a62fb5c458e041e39933a367180bd395a8b1`；`_enum_rounds_stdout.txt` 320,715 B / `6a06aa0b61c14c126ee0d44054b4443fb2192810479a9afc413aa15252aabb8d`；`_probe_digest.txt` 122,703 B / `92b4c256a613958e644ebbb5c3c193a5e7ff2de024db2ccff0db012d79f58c43`；`_verify_census_stdout.txt` 4,204 B / `6b5eba5ec8b620ed69a58cef84fbca50a81c5530830aa5873ee6a77ff2722199`。

### 1.3 ★ 与独立检查报告「182 = 153 + 18 + 11」的对照：结论是**时点差**，不是报告错误

- 独立检查报告 `lead/re_progress_check_20261111/RE_PROGRESS_20261111.md` §4 / §9 声称窗口 `[20261106..20261111]` 为 **182 = 153 有报告 + 18 无报告 + 11 空**；其 mtime = **2026-11-11 20:53:18+08:00**（`status_panel_20261112\panel_forensics_stdout.txt:12`、`_panel_assemble_stdout.txt:13` 实算；`RE_PROGRESS_20261111.md:143` 自述该分解由异族核验修正过一轮，把 `const_exit_fix_20261110` 从「空」改判「探针」）。
- 现在（枚举时点快照）**同窗口为 193 = 164 A + 18 B + 11 C**（`_verify_census_stdout.txt:21`）：**B/C 完全吻合（18 / 11 不变），A 多 11 个**（153→164）。`_verify_census_stdout.txt:14-20`「A. 逐日期顶层轮次目录计数」逐日给出：20261106 `19A`、07 `12A`、08 `36A`、09 `83A`、10 `3A/14B/7C`、11 `11A/4B/4C`；合计 `164A/18B/11C`。前 4 日与 11-10 与报告 §2.2 表（`DISPOSITION.md:41-47`）逐项相同，**差异全部落在 20261111 一天**。
- 「C. 顶层 20261111 全部目录」（`_verify_census_stdout.txt:39-57`）列出该日 **19 个目录**，其中 `cat=A` 恰 **11 个**（`re_chain_synth_v2` / `re_chain_synthesis` / `re_dispatch` / `re_ledger_apply` / `re_ledger_verify` / `re_progress_check` / `re_progress_xverify` / `re_round_batch1` / `re_round_disposition` / `re_session_kickoff` / `re_slot2_finding`，各带 `md≥1`），`cat=B` 4 个、`cat=C` 4 个；对照 `DISPOSITION.md:46`（21:05 时点 20261111 为 `0 A + 4 B + 4 C = 8`）与 `ROUND_REPORT.md:132`（20:53 时点该日 8 个目录），可见该日由 8 增至 19。
- `ROUND_REPORT.md:130-137` §4.3「目录计数的一处时点差」把增量拆为：报告完成 20:53 时该日 8 个；此后 **21:09–21:28 上一会话新建 5 个**（`re_round_disposition` / `re_ledger_apply` / `re_slot2_finding` / `re_chain_synthesis` 21:26 / `re_dispatch` 21:28）；**11-12 00:24–00:46 本轮新建 4 个**（`re_session_kickoff` / `re_ledger_verify` / `re_round_batch1` / `re_chain_synth_v2`）；另有 **11-11 当天由 B 类计入 / 补齐的 2 个**（21:16 的 `slot2_fullscan` / `playerctrl_semantics`，其输出件 mtime 21:16:05 / 21:16:39 见 `docs_drift_20261112\_evidence\01_fact_side_fingerprints.md:28-29,44-45`）。8 + 5 + 4 + 2 = 19 ✓。

#### 1.3.1 那 11 个 A 类新增目录，逐条列出（目录名 + 本次只读实测 mtime）

下表 11 行 = `_verify_census_stdout.txt:39-57` C 段中该日全部 `cat=A` 目录，即 A 类 153→164 的落点。`birth(ctime)` / `mtime` 为本次 `python -I -X utf8` 脚本对目录 `os.stat` 的**只读实算**（Asia/Shanghai 本机时区），非转引、非推测；分组依派工书实测结论与 `ROUND_REPORT.md:133-134`。

| # | 目录名 | birth(ctime) 实测 | mtime 实测 | 分组（时段归属） | 现类别 |
|:--:|:--|:--|:--|:--|:--:|
| 1 | `re_round_disposition_20261111` | 2026-11-11 21:02:11 | 2026-11-11 21:07:10 | ① 21:09–21:28 上一会话 +3 组 | A (md=1) |
| 2 | `re_ledger_apply_20261111` | 2026-11-11 21:11:13 | 2026-11-11 21:17:01 | ① 21:09–21:28 上一会话 +3 组 | A (md=2) |
| 3 | `re_slot2_finding_20261111` | 2026-11-11 21:12:44 | 2026-11-11 21:12:44 | ① 21:09–21:28 上一会话 +3 组 | A (md=1) |
| 4 | `re_chain_synthesis_20261111` | 2026-11-11 21:10:44 | 2026-11-11 21:24:36 | ① 21:26（`CHAIN_SYNTHESIS.md:4` 基准时点 21:26） | A (md=3) |
| 5 | `re_dispatch_20261111` | 2026-11-11 20:50:24 | 2026-11-11 21:10:01 | ① 21:28（`ROUND_REPORT.md:133`） | A (md=5) |
| 6 | `re_session_kickoff_20261111` | 2026-11-12 00:23:41 | 2026-11-12 01:48:03 | ② 11-12 00:24–00:46 本轮 +4 组 | A (md=1) |
| 7 | `re_ledger_verify_20261111` | 2026-11-12 00:26:19 | 2026-11-12 00:31:50 | ② 11-12 00:24–00:46 本轮 +4 组 | A (md=1) |
| 8 | `re_round_batch1_20261111` | 2026-11-12 00:27:18 | 2026-11-12 00:40:49 | ② 11-12 00:24–00:46 本轮 +4 组 | A (md=1) |
| 9 | `re_chain_synth_v2_20261111` | 2026-11-12 00:28:54 | 2026-11-12 01:41:20 | ② 11-12 00:24–00:46 本轮 +4 组 | A (md=2) |
| 10 | `re_progress_check_20261111` | 2026-11-11 20:32:04 | 2026-11-11 20:32:04 | ③ 11-11 当天由 B 类补齐的 2 个（其 md `RE_PROGRESS_20261111.md` mtime 20:53:18） | A (md=1) |
| 11 | `re_progress_xverify_20261111` | 2026-11-11 20:42:44 | 2026-11-11 20:49:59 | ③ 11-11 当天由 B 类补齐的 2 个 | A (md=2) |

**补充：`ROUND_REPORT.md:133` 口径下那「+2（21:16 由 B 类计入）」的逐条 mtime**（同样为本次只读 `os.stat` 实算；两目录在 CSV / 枚举快照中均为 `cat=B md=0`，不计入 A 类增量，列出以覆盖两种读法）：

| # | 目录名 | birth(ctime) 实测 | mtime 实测 | 输出件 mtime（旁证） | 现类别 |
|:--:|:--|:--|:--|:--|:--:|
| B1 | `slot2_fullscan_20261111` | 2026-11-11 07:50:00 | 2026-11-11 08:13:38 | `_sf_scan_out.txt` / `.json` = 2026-11-11 21:16:05（`docs_drift_20261112\_evidence\01_fact_side_fingerprints.md:44-45`） | B (md=0) |
| B2 | `playerctrl_semantics_20261111` | 2026-11-11 01:32:39 | 2026-11-11 02:16:14 | `_ps_disasm_out.txt` / `.json` = 2026-11-11 21:16:39（同上 `:28-29`） | B (md=0) |

即：**按「A 类 153→164」口径的 11 个 = 5 + 4 + 2（元轮次 `re_progress_check` / `re_progress_xverify`）；按「`ROUND_REPORT.md` 8→19 目录数」口径的 11 个 = 5 + 4 + 2（B 类 `slot2_fullscan` / `playerctrl_semantics`）**。两组交集 9 个、各差 2 个，合计 **13 个目录名与各自 mtime 已全部逐条列出**（主表 11 行 + 上表 2 行），任一读法都可逐条核对。「21:16 的 `slot2_fullscan` / `playerctrl_semantics` 由 B 类计入」，而这两目录在本次 CSV 中仍是 **B 类（md=0）**（`_verify_census_stdout.txt:44,57` `cat=B`），不构成 A 类增量；上表第 10–11 行取的是该日**确为 A 类、且 11-11 当天由无报告态补齐 md** 的 2 个元轮次。两种「最后 2 个」的指向不同，属统计时点/分类口径差；本次**未独立复核会话日志**，标「未验」（§6）。目录 mtime 与输出件 mtime 不一致（如 B1 目录 08:13:38、输出件 21:16:05）系文件系统元数据与文件复制/写入时点不同源，**不互相推翻**。另外 `re_round_disposition`（21:02:11）与 `re_dispatch`（20:50:24）的实测 birth 早于 21:09 时段、`re_chain_synthesis` / `re_dispatch` 的时段标注（21:26 / 21:28）与目录 mtime 不完全一致：时段是 `ROUND_REPORT.md` 的会话活动标注，目录 mtime 是文件系统元数据，二者不同源。`re_session_kickoff` 当前 mtime 01:48:03 晚于 00:46，因其报告在成文过程中持续被追加写入（本次实测，见 §6）。

- **另有实时 churn**：`_verify_census_stdout.txt:84-93` D 段记「现在顶层日期目录数=250；枚举快照=249；枚举后新增 `re_chain_v2_xverify_20261112`」；本写域自身也从枚举时点的 0 文件（`cat=C`）变成有文件。⇒ 249 / 193 / 182 都是**各自时点的快照**。

### 1.4 ★ 方法论结论（必须写进项目纪律）

**目录计数是「活动量」不是「完成量」，会随会话持续增长；任何引用必须绑定统计时点。** 本例中 20:53 的 182 与枚举时点的 193 都对，差 11 全在 20261111 一天的新建/补齐；B/C 不变而 A 单向增长，说明「有报告的目录数」同样会随时间膨胀。这是项目既有教训「有目录 ≠ 有交付」（`ROUND_REPORT.md:137` 引 G-55 / G-57）的延伸：不仅空目录会虚高，连「带 md 的目录数」也不能脱离时点当完成量引用。因此本报告凡引用计数一律标注口径（全树 / 窗口）与时点。

---
## §2 三类清单

> 三张表按 CSV 原有顺序（日期, 目录名）逐行生成；列为「目录名 / 日期 / 递归文件数 / 判定 / 理由摘要」。
> **22 个「无报告有探针或输出」与 12 个「递归空」逐个列出**（§2.2 / §2.3），是本任务的核心价值；
> 215 个「有md报告」逐行给出全量索引（§2.1），其判定与理由在 CSV 中 215 行完全同文。
> 理由摘要为 CSV「理由」列的机械截断（不改字），完整理由见 CSV 与 §3。

### 2.1 有md报告（A）— 215 个

> 下表 215 行的 CSV 原文判定一律为「已成立（有md报告，无需处置）」、理由一律为「递归含 md 报告，属 153/164 口径内已交付轮」；为控制篇幅，判定列缩写为「已成立」、理由摘要列缩写为「有md，已交付」。
> 其中日期 <20261106 的历史轮与 20261112 当日轮也都属此类（全树口径），**不要与窗口 153/164 混算**。

| 目录名 | 日期 | 递归文件数 | 判定 | 理由摘要 |
|:--|:--|--:|:--|:--|
| goal2_poison_gen_20261018 | 20261018 | 1 | 已成立 | 有md，已交付 |
| goal3_configsplit_20261019 | 20261019 | 3 | 已成立 | 有md，已交付 |
| goal_status_tables_20261019 | 20261019 | 1 | 已成立 | 有md，已交付 |
| qc161_patch_QC213P2_20261019 | 20261019 | 3 | 已成立 | 有md，已交付 |
| spawnfix9_freeze_20261019 | 20261019 | 1 | 已成立 | 有md，已交付 |
| goal1_baseline_design_20261020 | 20261020 | 4 | 已成立 | 有md，已交付 |
| goal1_e2_verdict_20261020 | 20261020 | 4 | 已成立 | 有md，已交付 |
| goal2_crashaddr_20261020 | 20261020 | 7 | 已成立 | 有md，已交付 |
| goal2_sbh_guard_20261020 | 20261020 | 4 | 已成立 | 有md，已交付 |
| goal3_p1sbh_merge_20261020 | 20261020 | 11 | 已成立 | 有md，已交付 |
| goal3_verifyhooks_fix_20261020 | 20261020 | 6 | 已成立 | 有md，已交付 |
| goal3_versioncheck_p2rebase_20261020 | 20261020 | 6 | 已成立 | 有md，已交付 |
| l1_u0800_20261020 | 20261020 | 13 | 已成立 | 有md，已交付 |
| l1_u0800_e1b_20261020 | 20261020 | 3 | 已成立 | 有md，已交付 |
| l1_u0800_e1c_dump_20261020 | 20261020 | 1 | 已成立 | 有md，已交付 |
| l1a_20261020 | 20261020 | 2 | 已成立 | 有md，已交付 |
| p2_build_20261020 | 20261020 | 10 | 已成立 | 有md，已交付 |
| qc151_failfast_20261020 | 20261020 | 3 | 已成立 | 有md，已交付 |
| goal1_h1decay_20261021 | 20261021 | 4 | 已成立 | 有md，已交付 |
| goal1_pathlen_gate_report_20261021 | 20261021 | 1 | 已成立 | 有md，已交付 |
| goal1_v11_env_gate_20261021 | 20261021 | 1 | 已成立 | 有md，已交付 |
| goal2_corpus_provenance_20261021 | 20261021 | 1 | 已成立 | 有md，已交付 |
| goal2_dump_20261021 | 20261021 | 10 | 已成立 | 有md，已交付 |
| goal2_writer_20261021 | 20261021 | 24 | 已成立 | 有md，已交付 |
| goal3_deploy_cycle_20261021 | 20261021 | 3 | 已成立 | 有md，已交付 |
| goal_bench_longinput_20261021 | 20261021 | 25 | 已成立 | 有md，已交付 |
| qc151_u8_impl_20261021 | 20261021 | 2 | 已成立 | 有md，已交付 |
| goal1_a8_fix_20261022 | 20261022 | 35 | 已成立 | 有md，已交付 |
| goal1_boot_fingerprint_20261022 | 20261022 | 8 | 已成立 | 有md，已交付 |
| goal1_harness6_20261022 | 20261022 | 17 | 已成立 | 有md，已交付 |
| goal2_onetime_census_20261022 | 20261022 | 67 | 已成立 | 有md，已交付 |
| goal2_rc4_fixdraft_20261022 | 20261022 | 10 | 已成立 | 有md，已交付 |
| goal2_rc4_fixv5_20261022 | 20261022 | 109 | 已成立 | 有md，已交付 |
| goal2_rc4_frameproof_20261022 | 20261022 | 28 | 已成立 | 有md，已交付 |
| goal2_rc4_power_20261022 | 20261022 | 5 | 已成立 | 有md，已交付 |
| goal2_rc4_trigger_20261022 | 20261022 | 141 | 已成立 | 有md，已交付 |
| goal2_wer_observation_20261022 | 20261022 | 5 | 已成立 | 有md，已交付 |
| goal3_mimosa_tools_review_20261022 | 20261022 | 5 | 已成立 | 有md，已交付 |
| mimosa_review_20261022 | 20261022 | 5 | 已成立 | 有md，已交付 |
| goal1_harness7_20261023 | 20261023 | 20 | 已成立 | 有md，已交付 |
| codex_rulings_20261025 | 20261025 | 1 | 已成立 | 有md，已交付 |
| codex_handoff_20261026 | 20261026 | 6 | 已成立 | 有md，已交付 |
| codex_review_20261030 | 20261030 | 1 | 已成立 | 有md，已交付 |
| codex_round_20261030 | 20261030 | 223 | 已成立 | 有md，已交付 |
| goal3t_nightwatch_20261102 | 20261102 | 137 | 已成立 | 有md，已交付 |
| offline_waittrace_20261102 | 20261102 | 11 | 已成立 | 有md，已交付 |
| goal3t_nightwatch_20261105 | 20261105 | 13 | 已成立 | 有md，已交付 |
| re_line_20261105 | 20261105 | 482 | 已成立 | 有md，已交付 |
| a_residual_20261106 | 20261106 | 5 | 已成立 | 有md，已交付 |
| b2_preaudit_20261106 | 20261106 | 6 | 已成立 | 有md，已交付 |
| b2b_candidate_20261106 | 20261106 | 14 | 已成立 | 有md，已交付 |
| b2b_candidate_review2_20261106 | 20261106 | 22 | 已成立 | 有md，已交付 |
| b2b_candidate_review_20261106 | 20261106 | 11 | 已成立 | 有md，已交付 |
| b2b_design_20261106 | 20261106 | 22 | 已成立 | 有md，已交付 |
| b2b_preaudit_20261106 | 20261106 | 14 | 已成立 | 有md，已交付 |
| control_20261106 | 20261106 | 16 | 已成立 | 有md，已交付 |
| d13b_design_20261106 | 20261106 | 16 | 已成立 | 有md，已交付 |
| d13b_timing_clarify_20261106 | 20261106 | 6 | 已成立 | 有md，已交付 |
| d25_ruling_20261106 | 20261106 | 5 | 已成立 | 有md，已交付 |
| d26_ruling_20261106 | 20261106 | 5 | 已成立 | 有md，已交付 |
| d27_ruling_20261106 | 20261106 | 6 | 已成立 | 有md，已交付 |
| d28_ruling_20261106 | 20261106 | 5 | 已成立 | 有md，已交付 |
| d29_ruling_20261106 | 20261106 | 6 | 已成立 | 有md，已交付 |
| d30_ruling_20261106 | 20261106 | 6 | 已成立 | 有md，已交付 |
| early_trigger_feasibility_20261106 | 20261106 | 16 | 已成立 | 有md，已交付 |
| nextstep_plan_20261106 | 20261106 | 3 | 已成立 | 有md，已交付 |
| stall_event_def_20261106 | 20261106 | 10 | 已成立 | 有md，已交付 |
| b2b_candidate_lf_20261107 | 20261107 | 4 | 已成立 | 有md，已交付 |
| b2b_candidate_review3_20261107 | 20261107 | 8 | 已成立 | 有md，已交付 |
| b2b_isolated_20261107 | 20261107 | 27 | 已成立 | 有md，已交付 |
| b2b_n1_binding_20261107 | 20261107 | 1 | 已成立 | 有md，已交付 |
| crash_diag_n6_20261107 | 20261107 | 5 | 已成立 | 有md，已交付 |
| d14_dual_20261107 | 20261107 | 15 | 已成立 | 有md，已交付 |
| dstart_observable_20261107 | 20261107 | 6 | 已成立 | 有md，已交付 |
| dtrigger_compare_20261107 | 20261107 | 33 | 已成立 | 有md，已交付 |
| dtrigger_round2_20261107 | 20261107 | 47 | 已成立 | 有md，已交付 |
| five_read_n7_20261107 | 20261107 | 7 | 已成立 | 有md，已交付 |
| slowframe_round2_20261107 | 20261107 | 8 | 已成立 | 有md，已交付 |
| static_spec_n9_20261107 | 20261107 | 7 | 已成立 | 有md，已交付 |
| a_dim_reduced_20261108 | 20261108 | 6 | 已成立 | 有md，已交付 |
| a_residual_n1_20261108 | 20261108 | 6 | 已成立 | 有md，已交付 |
| b2b_yi_supersede_20261108 | 20261108 | 1 | 已成立 | 有md，已交付 |
| b_unclosed_trace_20261108 | 20261108 | 23 | 已成立 | 有md，已交付 |
| bexec_n4_20261108 | 20261108 | 8 | 已成立 | 有md，已交付 |
| c97_scope_recheck_20261108 | 20261108 | 13 | 已成立 | 有md，已交付 |
| corpus_anomaly_20261108 | 20261108 | 19 | 已成立 | 有md，已交付 |
| criteria_r3_verify_20261108 | 20261108 | 7 | 已成立 | 有md，已交付 |
| d13d14_cards_20261108 | 20261108 | 4 | 已成立 | 有md，已交付 |
| d_o1o4_necessity_20261108 | 20261108 | 5 | 已成立 | 有md，已交付 |
| deliverable_anchor_20261108 | 20261108 | 7 | 已成立 | 有md，已交付 |
| direction_ruling_20261108 | 20261108 | 9 | 已成立 | 有md，已交付 |
| gate_fp7_20261108 | 20261108 | 28 | 已成立 | 有md，已交付 |
| gate_template_20261108 | 20261108 | 36 | 已成立 | 有md，已交付 |
| gate_validate_20261108 | 20261108 | 177 | 已成立 | 有md，已交付 |
| ledger_appendix_20261108 | 20261108 | 26 | 已成立 | 有md，已交付 |
| matrix_binding_20261108 | 20261108 | 14 | 已成立 | 有md，已交付 |
| n10c04_ruling_20261108 | 20261108 | 9 | 已成立 | 有md，已交付 |
| n11_dimmap_20261108 | 20261108 | 3 | 已成立 | 有md，已交付 |
| n11_protocol_spec_20261108 | 20261108 | 7 | 已成立 | 有md，已交付 |
| n11_wording_fix_20261108 | 20261108 | 5 | 已成立 | 有md，已交付 |
| n1_r2_verify_20261108 | 20261108 | 6 | 已成立 | 有md，已交付 |
| n4_yi_final_20261108 | 20261108 | 12 | 已成立 | 有md，已交付 |
| n8_residual_20261108 | 20261108 | 16 | 已成立 | 有md，已交付 |
| n9_erratum_20261108 | 20261108 | 13 | 已成立 | 有md，已交付 |
| p11_stations_20261108 | 20261108 | 29 | 已成立 | 有md，已交付 |
| pending_factpack_20261108 | 20261108 | 11 | 已成立 | 有md，已交付 |
| perf_repair_n11_20261108 | 20261108 | 12 | 已成立 | 有md，已交付 |
| r2_final_grade_20261108 | 20261108 | 7 | 已成立 | 有md，已交付 |
| r2_unclosed_b_20261108 | 20261108 | 16 | 已成立 | 有md，已交付 |
| r2_unclosed_cd_20261108 | 20261108 | 11 | 已成立 | 有md，已交付 |
| s604_attribution_20261108 | 20261108 | 9 | 已成立 | 有md，已交付 |
| slowframe_r3_20261108 | 20261108 | 9 | 已成立 | 有md，已交付 |
| slowwindow_n8_20261108 | 20261108 | 10 | 已成立 | 有md，已交付 |
| spec_static_closure_20261108 | 20261108 | 16 | 已成立 | 有md，已交付 |
| v2_precision_fix_20261108 | 20261108 | 9 | 已成立 | 有md，已交付 |
| a_class_fix_20261109 | 20261109 | 7 | 已成立 | 有md，已交付 |
| advset_indep_20261109 | 20261109 | 22 | 已成立 | 有md，已交付 |
| andk_rerun_20261109 | 20261109 | 515 | 已成立 | 有md，已交付 |
| c07_gate_audit_20261109 | 20261109 | 60 | 已成立 | 有md，已交付 |
| c07_gate_fix_20261109 | 20261109 | 46 | 已成立 | 有md，已交付 |
| c07_hardening_20261109 | 20261109 | 9 | 已成立 | 有md，已交付 |
| c07_protocol_attacks_20261109 | 20261109 | 29 | 已成立 | 有md，已交付 |
| c07_slot_20261109 | 20261109 | 17 | 已成立 | 有md，已交付 |
| c07_truth_protocol_20261109 | 20261109 | 10 | 已成立 | 有md，已交付 |
| cert_realcheck_20261109 | 20261109 | 36 | 已成立 | 有md，已交付 |
| chain_vs_single_20261109 | 20261109 | 32 | 已成立 | 有md，已交付 |
| check_family_20261109 | 20261109 | 24 | 已成立 | 有md，已交付 |
| check_fp_audit_20261109 | 20261109 | 15 | 已成立 | 有md，已交付 |
| check_masking_20261109 | 20261109 | 85 | 已成立 | 有md，已交付 |
| comparability_20261109 | 20261109 | 79 | 已成立 | 有md，已交付 |
| const_exit_20261109 | 20261109 | 63 | 已成立 | 有md，已交付 |
| count_invariant_20261109 | 20261109 | 47 | 已成立 | 有md，已交付 |
| counterpart_fix_20261109 | 20261109 | 9 | 已成立 | 有md，已交付 |
| detect_triage_20261109 | 20261109 | 25 | 已成立 | 有md，已交付 |
| dg_adversarial_20261109 | 20261109 | 31 | 已成立 | 有md，已交付 |
| dneg_generative_20261109 | 20261109 | 28 | 已成立 | 有md，已交付 |
| eqdecl_gate_20261109 | 20261109 | 23 | 已成立 | 有md，已交付 |
| equiv_class_20261109 | 20261109 | 33 | 已成立 | 有md，已交付 |
| evidence_indep_20261109 | 20261109 | 47 | 已成立 | 有md，已交付 |
| f2d_rootcause_20261109 | 20261109 | 7 | 已成立 | 有md，已交付 |
| falsifiable_no_relax_20261109 | 20261109 | 32 | 已成立 | 有md，已交付 |
| fp_discriminate_20261109 | 20261109 | 62 | 已成立 | 有md，已交付 |
| fp_pattern_20261109 | 20261109 | 30 | 已成立 | 有md，已交付 |
| gate_doc_name_fix_20261109 | 20261109 | 153 | 已成立 | 有md，已交付 |
| gate_n13_20261109 | 20261109 | 20 | 已成立 | 有md，已交付 |
| gate_pipeline_20261109 | 20261109 | 31 | 已成立 | 有md，已交付 |
| gate_postmortem_20261109 | 20261109 | 14 | 已成立 | 有md，已交付 |
| gate_r9r12_20261109 | 20261109 | 18 | 已成立 | 有md，已交付 |
| gate_r9sem_20261109 | 20261109 | 41 | 已成立 | 有md，已交付 |
| gate_rejudge32_20261109 | 20261109 | 48 | 已成立 | 有md，已交付 |
| gate_subject_id_20261109 | 20261109 | 86 | 已成立 | 有md，已交付 |
| gate_v1v2_20261109 | 20261109 | 27 | 已成立 | 有md，已交付 |
| h5_governance_20261109 | 20261109 | 29 | 已成立 | 有md，已交付 |
| handoff_pack_20261109 | 20261109 | 18 | 已成立 | 有md，已交付 |
| k1bit_detect_20261109 | 20261109 | 33 | 已成立 | 有md，已交付 |
| keff_calc_20261109 | 20261109 | 14 | 已成立 | 有md，已交付 |
| layer_identity_20261109 | 20261109 | 3 | 已成立 | 有md，已交付 |
| ledger_bound_20261109 | 20261109 | 10 | 已成立 | 有md，已交付 |
| masking_effect_20261109 | 20261109 | 128 | 已成立 | 有md，已交付 |
| matrix_ab_ruling_20261109 | 20261109 | 7 | 已成立 | 有md，已交付 |
| matrix_reach_20261109 | 20261109 | 16 | 已成立 | 有md，已交付 |
| matrix_row5_20261109 | 20261109 | 13 | 已成立 | 有md，已交付 |
| merged_consumer_audit_20261109 | 20261109 | 23 | 已成立 | 有md，已交付 |
| merged_contract_20261109 | 20261109 | 20 | 已成立 | 有md，已交付 |
| merged_safety_20261109 | 20261109 | 51 | 已成立 | 有md，已交付 |
| metric_audit_20261109 | 20261109 | 7 | 已成立 | 有md，已交付 |
| minhard_check_20261109 | 20261109 | 49 | 已成立 | 有md，已交付 |
| n4_gate_verdict_20261109 | 20261109 | 36 | 已成立 | 有md，已交付 |
| needle_norm_20261109 | 20261109 | 42 | 已成立 | 有md，已交付 |
| number_channel_20261109 | 20261109 | 60 | 已成立 | 有md，已交付 |
| o1prime_reach_20261109 | 20261109 | 33 | 已成立 | 有md，已交付 |
| oldwording_sweep_20261109 | 20261109 | 13 | 已成立 | 有md，已交付 |
| oracle_spec_20261109 | 20261109 | 8 | 已成立 | 有md，已交付 |
| orch_claims_20261109 | 20261109 | 55 | 已成立 | 有md，已交付 |
| ordering_evidence_20261109 | 20261109 | 28 | 已成立 | 有md，已交付 |
| pvalue_recalc_20261109 | 20261109 | 15 | 已成立 | 有md，已交付 |
| r11_f2_fix_20261109 | 20261109 | 26 | 已成立 | 有md，已交付 |
| r33e_merge_20261109 | 20261109 | 126 | 已成立 | 有md，已交付 |
| refsync_scope_20261109 | 20261109 | 37 | 已成立 | 有md，已交付 |
| s604_exclusive_20261109 | 20261109 | 23 | 已成立 | 有md，已交付 |
| s604_refsync_20261109 | 20261109 | 9 | 已成立 | 有md，已交付 |
| s604_refsync_full_20261109 | 20261109 | 20 | 已成立 | 有md，已交付 |
| s604_script_gap_20261109 | 20261109 | 17 | 已成立 | 有md，已交付 |
| s604_script_hunt_20261109 | 20261109 | 49 | 已成立 | 有md，已交付 |
| s604_verdict_entry_20261109 | 20261109 | 15 | 已成立 | 有md，已交付 |
| samedoc_link_20261109 | 20261109 | 48 | 已成立 | 有md，已交付 |
| score_decomp_20261109 | 20261109 | 3 | 已成立 | 有md，已交付 |
| seal_chronology_20261109 | 20261109 | 11 | 已成立 | 有md，已交付 |
| seal_v2_feasibility_20261109 | 20261109 | 13 | 已成立 | 有md，已交付 |
| stale_pass_20261109 | 20261109 | 86 | 已成立 | 有md，已交付 |
| strict_exposure_20261109 | 20261109 | 10 | 已成立 | 有md，已交付 |
| tautology_audit_20261109 | 20261109 | 15 | 已成立 | 有md，已交付 |
| text_fix_unified_20261109 | 20261109 | 4 | 已成立 | 有md，已交付 |
| two_products_20261109 | 20261109 | 28 | 已成立 | 有md，已交付 |
| u5u6_mirror_20261109 | 20261109 | 9 | 已成立 | 有md，已交付 |
| v12_impact_20261109 | 20261109 | 15 | 已成立 | 有md，已交付 |
| w2_samecause_20261109 | 20261109 | 26 | 已成立 | 有md，已交付 |
| whitelist_audit_20261109 | 20261109 | 48 | 已成立 | 有md，已交付 |
| eqdecl_fix_20261110 | 20261110 | 46 | 已成立 | 有md，已交付 |
| exit_criterion_20261110 | 20261110 | 34 | 已成立 | 有md，已交付 |
| goal_line_patch_20261110 | 20261110 | 4 | 已成立 | 有md，已交付 |
| re_chain_synth_v2_20261111 | 20261111 | 12 | 已成立 | 有md，已交付 |
| re_chain_synthesis_20261111 | 20261111 | 14 | 已成立 | 有md，已交付 |
| re_dispatch_20261111 | 20261111 | 5 | 已成立 | 有md，已交付 |
| re_ledger_apply_20261111 | 20261111 | 6 | 已成立 | 有md，已交付 |
| re_ledger_verify_20261111 | 20261111 | 3 | 已成立 | 有md，已交付 |
| re_progress_check_20261111 | 20261111 | 1 | 已成立 | 有md，已交付 |
| re_progress_xverify_20261111 | 20261111 | 2 | 已成立 | 有md，已交付 |
| re_round_batch1_20261111 | 20261111 | 7 | 已成立 | 有md，已交付 |
| re_round_disposition_20261111 | 20261111 | 6 | 已成立 | 有md，已交付 |
| re_session_kickoff_20261111 | 20261111 | 1 | 已成立 | 有md，已交付 |
| re_slot2_finding_20261111 | 20261111 | 1 | 已成立 | 有md，已交付 |
| dlc_capability_audit_20261112 | 20261112 | 88 | 已成立 | 有md，已交付 |
| docs_drift_20261112 | 20261112 | 35 | 已成立 | 有md，已交付 |
| status_panel_20261112 | 20261112 | 10 | 已成立 | 有md，已交付 |

**小计：215 行**（= 判定「已成立」215）。

### 2.2 无报告有探针或输出（B）— 22 个，逐个列出

| # | 目录名 | 日期 | 递归文件数 | 判定 | 理由摘要 |
|:--:|:--|:--|--:|:--|:--|
| 1 | qc151_carrierfix_20261020 | 20261020 | 2 | 口径外登记 | 日期 <20261106，不在报告 182 口径内；carrierfix.diff + report.json；是否补报告由十月线自行定 |
| 2 | t55k_20261020 | 20261020 | 17 | 口径外登记 | 日期 <20261106，不在报告 182 口径内；10 月真机测量数据轮（T55k 全套 receipt/measure）；是否补报告由十… |
| 3 | goal1_harness8_20261031 | 20261031 | 33 | 口径外登记 | 日期 <20261106，不在报告 182 口径内；10 月 harness8 判据/启动脚本族 + .mimosa 钩子状态件；是否补报告… |
| 4 | const_exit_fix_20261110 | 20261110 | 32 | 废弃 | patched/ 内 18 个 py 全为他轮探针的字节副本（dup_audit PATCH_COPY 组 sha256=85cde303…… |
| 5 | crit_fix_20261110 | 20261110 | 7 | 废弃 | E3 出口判据 v1 修补（_ec_criterion_fixed.py 46,005 B + repro/ 四件），无输出无 md；已被 … |
| 6 | dup_audit_20261110 | 20261110 | 3 | 补做 | 读数已齐：lead/ 下 2928 个 .py 只读普查、2517 个唯一 sha256、72 组重复（PATCH_COPY 13 / RE… |
| 7 | e3_fix2_20261110 | 20261110 | 8 | 废弃 | E3 判据 v2 + 7 正控 3 负控跑测（_before/_after.json 各 16,742 B）；被 e3_unify v3（修… |
| 8 | e3_secondimpl_20261110 | 20261110 | 2 | 废弃 | 独立第二实现 _ei3_e3.py（AST-only，刻意不看参考实现），背靠背对照使命完成，被 v3 吸收 |
| 9 | exit_lint_20261110 | 20261110 | 1 | 补做 | _el_lint.py 登记前出口 lint 路由器（PASS/REJECT/MANUAL/ERROR），判据底座仍挂旧版 _ec_crit… |
| 10 | gate_exit_retrofit_20261110 | 20261110 | 46 | 补做 | 出口模板对照件已实跑（_gr_template_ctl_run.txt：-1→exit 0、1→exit 1 两次「对得上」）；patche… |
| 11 | ledger_exit_census_20261110 | 20261110 | 3 | 补做 | 读数已齐：三本台账硬编码 EXIT=0 共 76 处（分布 31/1/44），cls 计数 NO_EXIT_AT_ALL 5 / CONDI… |
| 12 | ok_falsify_20261110 | 20261110 | 2 | 补做 | 读数已齐：413 件全量出口判据三维交叉表（UNKNOWN+NEEDS_FIX 分组 n=18 等），_of_scope_out.json … |
| 13 | re_crashwriter_static_20261110 | 20261110 | 3 | 已入他处 | 0x0054A56E 数据依赖链：RTTI 基类 vtable 0x7ECBFC/派生 0x7ECBDC、全局对象 0xAA1078、0x5… |
| 14 | re_loadbench_diff_20261110 | 20261110 | 3 | 已入他处 | 大版 92,332 B（md5 3c47bff8…）与小版 25,604 B（生成器 2026-09-25 合成图）非同一张图；实载=222… |
| 15 | re_map_preset_decode_20261110 | 20261110 | 3 | 已入他处 | 三图逐槽位解析：XMP29U2.MAP [Units]=3360（14 owner×240）、两份 yrm 均 240/160，台账声称 1… |
| 16 | re_orphan_owners_20261110 | 20261110 | 6 | 已入他处 | HouseClass owner 三层法：XMP29U2.MAP 14 owner 带各 400 实体（240 车+160 步）；MaxPl… |
| 17 | unknown_locate_20261110 | 20261110 | 2 | 补做 | 读数已齐：263 件 NO_EXIT_AT_ALL 的 stdout 产物通道普查（11 件仅 stdout.write：9 UNKNOWN… |
| 18 | e3_unify_20261111 | 20261111 | 2 | 补做 | _e3_v3.py（22,608 B）统一判据本体就绪但零跑测输出、零 md；缺 413 件全量扫描与验收报告 E3_UNIFY.md；输入… |
| 19 | esi_caller_trace_20261111 | 20261111 | 3 | 废弃 | slot2 调用点首轮普查（1,392,527 条分块反汇编、1714 个 slot2 形态点、0x54A4F0/0x54A630 直接调用… |
| 20 | playerctrl_semantics_20261111 | 20261111 | 3 | 已入他处 | PlayerControl@0x824E28→HouseClass+0x1ED、PercentBuilt@0x8189A0→+0x571C … |
| 21 | slot2_fullscan_20261111 | 20261111 | 3 | 已入他处 | 100% 分块重验：1714 个 slot2 形态点中可能指向 0x54A4F0/0x54A630 的恰 1 个=0x546069；已被处置… |
| 22 | re_atlas_reassess_20261112 | 20261112 | 4 | 补做（进行中） | 11-12 当日新轮（报告口径外）：re_atlas 全量指纹 498 件 + R-036 重算 8/8 PASS + R-035 复核 2… |

**小计：22 行**（15 废弃中占 5 + 补做 7 + 已入他处 6 + 口径外登记 3 + 补做（进行中）1 = 22）。

### 2.3 递归空（C）— 12 个，逐个列出

| # | 目录名 | 日期 | 递归文件数 | 判定 | 理由摘要 |
|:--:|:--|:--|--:|:--|:--|
| 1 | backlog_sweep_20261110 | 20261110 | 0 | 废弃 | 空目录（0 文件），已启动未落盘；积压清理已被全盘进度审计与 PENDING_DECISIONS 治理吸收 |
| 2 | crit_recheck_20261110 | 20261110 | 0 | 废弃 | 空目录；判据复验已由 crit_fix→e3_fix2→e3_unify 判据链交付 |
| 3 | e3_rootcause_20261110 | 20261110 | 0 | 废弃 | 空目录；吞没异常根因已沉淀为 _e3_v3.py 七条缺陷修复规则 |
| 4 | e3_triage_20261110 | 20261110 | 0 | 废弃 | 空目录；413 件分流已由 ok_falsify 的 _of_scope_out.json 完成 |
| 5 | ledger_apply_prep_20261110 | 20261110 | 0 | 已入他处 | 空目录但目标已完成：§605–§609 五笔已于 11-11 21:1x 并入主台账（追加 28,512 B，759,518→788,030… |
| 6 | re_chain_semantics_20261110 | 20261110 | 0 | 废弃 | 空目录；0x54A56E 链语义已由 re_crashwriter_static 全量交付并升级为因果链报告 |
| 7 | recon_20261110 | 20261110 | 0 | 废弃 | 空目录；宽泛静态侦察已分流为 re_crashwriter_static / re_loadbench_diff / re_map_pres… |
| 8 | housecount_trace_20261111 | 20261111 | 0 | 废弃 | 空目录；静态侧已闭环（8 处创建点未测 PlayerControl、[Houses]↔节对应、meta_count=4 文件层澄清）；动态 … |
| 9 | ledger_num_audit_20261111 | 20261111 | 0 | 废弃 | 空目录；台账编号核验已由异族核验 VERDICT 闭环，并账与核验已由 re_ledger_apply/re_ledger_verify 完… |
| 10 | mapfile_1680_hunt_20261111 | 20261111 | 0 | 废弃 | 空目录；1680/1120 载体寻源已由 re_loadbench_diff 完成（实载=222,799 B 变体以 XMP29U2.MAP… |
| 11 | re_line_collapse_20261111 | 20261111 | 0 | 废弃 | 空目录；轮次收缩治理已被 re_round_disposition 写域全盘接管 |
| 12 | round_gap_disposition_20261112 | 20261112 | 0 | 本检查写域 | 本次处置任务的写域目录；枚举时点为空目录故入 C 类，非项目轮次 |

**小计：12 行**。其中 11 个落在窗口 `[20261106..20261111]`（即报告口径的 11 个空轮），第 12 个是本检查写域 `round_gap_disposition_20261112`（日期 20261112，窗口外）——这正是「全树 12」与「窗口 11」的差，不是矛盾。

## §3 逐个判定的依据

> 四组按**判定维度**分列，允许交叉：12 个空轮中 10 个判「废弃」、1 个判「已入他处」、1 个为「本检查写域」；15 个废弃 = 10 个空轮 + 5 个 B 轮；7 补做全为 B 轮；7 已入他处 = 1 个空轮 + 6 个 B 轮。四组合计 41 条，去重后覆盖 12 + 15 + 7 + 7 各判定项。
> 判定 / 理由 / 取代证据均取自 CSV（上一位执行方的定性），本报告只汇总与转录，**未逐条独立复核**（见 §6）。

### 3.1 12 个递归空：是否「已启动未落盘」+ 有无近名轮次已交付同类结论

> 「已启动未落盘」是**形态描述**：目录存在、递归 0 文件（CSV「递归文件数」=0、「有无md」= 无、「有无输出」= 无）。是否确曾启动过会话、由谁启动，本次**未验**。
> 近名 / 同类交付件取自 CSV「理由」「取代证据」列与 `lead/re_round_disposition_20261111/DISPOSITION.md` §4 空轮深度分析表（`L98-L111`）。

| # | 目录名 | 是否「已启动未落盘」 | 近名 / 同类轮次已交付同类结论（取代件） | 判定 |
|:--:|:--|:--|:--|:--|
| 1 | backlog_sweep_20261110 | 是（0 文件）；是否确曾启动会话未验 | 积压清理已被全盘进度审计 `re_progress_check_20261111` 与 `PENDING_DECISIONS` 治理吸收（`DISPOSITION.md:L80`；CSV 取代证据同） | 废弃 |
| 2 | crit_recheck_20261110 | 是（0 文件）；是否确曾启动会话未验 | 判据复验已由 `crit_fix_20261110` → `e3_fix2_20261110` → `e3_unify_20261111` 判据链交付（`DISPOSITION.md:L81`） | 废弃 |
| 3 | e3_rootcause_20261110 | 是（0 文件）；是否确曾启动会话未验 | 吞没异常根因已沉淀为 `e3_unify_20261111/_e3_v3.py` 七条缺陷修复规则（`DISPOSITION.md:L82`，`_e3_v3.py:L7-L35`） | 废弃 |
| 4 | e3_triage_20261110 | 是（0 文件）；是否确曾启动会话未验 | 413 件分流已由 `ok_falsify_20261110/_of_scope_out.json` 完成（`DISPOSITION.md:L83`） | 废弃 |
| 5 | ledger_apply_prep_20261110 | 是（0 文件）；但目标**已完成并核验** | §605–§609 五笔于 11-11 21:1x 并入主台账；取代件 `re_ledger_apply_20261111/APPLY_RECEIPT.md:L10-L23`、`re_ledger_verify_20261111/VERIFY.md:L16`（V1 PASS）、`GOAL_THREE_TARGETS_20261018.md:L9760/L9775/L9787/L9802/L9832` | 已入他处 |
| 6 | re_chain_semantics_20261110 | 是（0 文件）；是否确曾启动会话未验 | 0x54A56E 链语义由 `re_crashwriter_static_20261110/_cw_disasm_out.txt:L80-L105` 全量交付并升级为因果链报告（`DISPOSITION.md:L88`） | 废弃 |
| 7 | recon_20261110 | 是（0 文件）；是否确曾启动会话未验 | 宽泛静态侦察已分流为 `re_crashwriter_static` / `re_loadbench_diff` / `re_map_preset_decode` / `re_orphan_owners` 四个具体轮次（`DISPOSITION.md:L90`） | 废弃 |
| 8 | housecount_trace_20261111 | 是（0 文件）；静态侧已闭环、动态侧被阻塞 | 静态侧由 `playerctrl_semantics_20261111/_ps_disasm_out.txt:L636-L642` 交付；动态 trace 受 D-13 PAUSE/BLOCKED 阻塞（`RE_PROGRESS_20261111.md:L82`），属被阻塞非待补 | 废弃 |
| 9 | ledger_num_audit_20261111 | 是（0 文件）；是否确曾启动会话未验 | 编号核验由 `re_progress_xverify_20261111/VERDICT.md §1` 闭环；并账 / 核验由 `re_ledger_apply` / `re_ledger_verify` 完成（`DISPOSITION.md:L86`） | 废弃 |
| 10 | mapfile_1680_hunt_20261111 | 是（0 文件）；是否确曾启动会话未验 | 1680/1120 载体寻源由 `re_loadbench_diff_20261110/_ld_diff_out.txt:L101` 与 `re_map_preset_decode_20261110/_md_parse_out.txt` 尾节完成（`DISPOSITION.md:L87`） | 废弃 |
| 11 | re_line_collapse_20261111 | 是（0 文件）；是否确曾启动会话未验 | 轮次收缩治理已被 `re_round_disposition_20261111` 写域全盘接管（`re_dispatch_20261111/BRIEF_D.md:L1`；`DISPOSITION.md:L89`） | 废弃 |
| 12 | round_gap_disposition_20261112 | **不适用**：本检查写域，非项目轮次（枚举时点 0 文件） | 无同类结论可取代；本目录即本次成文写域（判定「本检查写域」） | 本检查写域 |

**逐条结论**：12 个全部递归 0 文件；11 个项目轮次中 10 个有「近名 / 同类轮次已交付同类结论」，1 个（`ledger_apply_prep`）虽为空目录但目标已由他处完成并核验，故判「已入他处」而非废弃；第 12 个是本任务写域，不计项目进度。

### 3.2 15 个废弃：每个点名取代件（取自 CSV「取代证据」列，逐字转录）

| # | 目录名 | 取代件（CSV「取代证据」原文） | 一句话理由（CSV「理由」摘要） |
|:--:|:--|:--|:--|
| 1 | backlog_sweep_20261110 | DISPOSITION.md:L80 | 空目录（0 文件），已启动未落盘；积压清理已被全盘进度审计与 PENDING_DECISIONS 治理吸收 |
| 2 | const_exit_fix_20261110 | dup_audit_20261110/_da_summary.txt 尾节（PATCH_COPY 组 4 路径含 lead/const_exit_fix_20261110/patched/…）；exit_criterion_20261110/_ec_s4_results.json（263 件已跑）；DISPOSITION.md:L62（分歧登记） | patched/ 内 18 个 py 全为他轮探针的字节副本（dup_audit PATCH_COPY 组 sha256=85cde303… 点名本目录 _reviewer_t2_… |
| 3 | crit_fix_20261110 | e3_fix2_20261110/_before.json 头部 criterion 字段指向 lead/crit_fix_20261110/_ec_criterion_fixed.py（被消费证据）；DISPOSITION.md:L63（引 e3_unify_20261111/_e3_v3.py:L7） | E3 出口判据 v1 修补（_ec_criterion_fixed.py 46,005 B + repro/ 四件），无输出无 md；已被 e3_fix2 消费为 before 基… |
| 4 | crit_recheck_20261110 | DISPOSITION.md:L81 | 空目录；判据复验已由 crit_fix→e3_fix2→e3_unify 判据链交付 |
| 5 | e3_fix2_20261110 | e3_unify_20261111/_e3_v3.py 文档串「统一两套既有实现的正确部分，修七条已知缺陷」；DISPOSITION.md:L65 | E3 判据 v2 + 7 正控 3 负控跑测（_before/_after.json 各 16,742 B）；被 e3_unify v3（修七条已知缺陷）吸收终结，数据件留作过程证… |
| 6 | e3_rootcause_20261110 | DISPOSITION.md:L82（e3_unify_20261111/_e3_v3.py:L7-L35） | 空目录；吞没异常根因已沉淀为 _e3_v3.py 七条缺陷修复规则 |
| 7 | e3_secondimpl_20261110 | e3_unify_20261111/_e3_v3.py；DISPOSITION.md:L66 | 独立第二实现 _ei3_e3.py（AST-only，刻意不看参考实现），背靠背对照使命完成，被 v3 吸收 |
| 8 | e3_triage_20261110 | DISPOSITION.md:L83 | 空目录；413 件分流已由 ok_falsify 的 _of_scope_out.json 完成 |
| 9 | re_chain_semantics_20261110 | DISPOSITION.md:L88（re_crashwriter_static_20261110/_cw_disasm_out.txt:L80-L105） | 空目录；0x54A56E 链语义已由 re_crashwriter_static 全量交付并升级为因果链报告 |
| 10 | recon_20261110 | DISPOSITION.md:L90 | 空目录；宽泛静态侦察已分流为 re_crashwriter_static / re_loadbench_diff / re_map_preset_decode / re_orpha… |
| 11 | esi_caller_trace_20261111 | slot2_fullscan_20261111/_sf_scan_out.txt T1/T4/T5-final 节；DISPOSITION.md:L68（引 _sf_scan.py:L11-L15） | slot2 调用点首轮普查（1,392,527 条分块反汇编、1714 个 slot2 形态点、0x54A4F0/0x54A630 直接调用 0、唯一候选 0x546069）；已被… |
| 12 | housecount_trace_20261111 | DISPOSITION.md:L84（playerctrl _ps_disasm_out.txt:L636-L642）；re_progress_check_20261111/RE_PROGRESS_20261111.md:L82（D-13 阻塞） | 空目录；静态侧已闭环（8 处创建点未测 PlayerControl、[Houses]↔节对应、meta_count=4 文件层澄清）；动态 trace 受 D-13 PAUSE/B… |
| 13 | ledger_num_audit_20261111 | DISPOSITION.md:L86（re_progress_xverify VERDICT §1）；re_ledger_verify_20261111/VERIFY.md:L16 | 空目录；台账编号核验已由异族核验 VERDICT 闭环，并账与核验已由 re_ledger_apply/re_ledger_verify 完成 |
| 14 | mapfile_1680_hunt_20261111 | DISPOSITION.md:L87（re_loadbench_diff_20261110/_ld_diff_out.txt:L101）；re_map_preset_decode_20261110/_md_parse_out.txt 尾节「两份 yrm 均不符」 | 空目录；1680/1120 载体寻源已由 re_loadbench_diff 完成（实载=222,799 B 变体以 XMP29U2.MAP 名载入；在盘 yrm 均 240/16… |
| 15 | re_line_collapse_20261111 | DISPOSITION.md:L89（re_dispatch_20261111/BRIEF_D.md:L1） | 空目录；轮次收缩治理已被 re_round_disposition 写域全盘接管 |

**小计：15 个，每个都有具名取代件**；`const_exit_fix_20261110` 的「取代件」列还额外登记了与 `DISPOSITION.md:L62`（判「补做」并称 VERIFY_A8 实跑 ALL PASS）的分歧：CSV 理由明确写「本目录无落盘输出，实跑未验——本次改判废弃，分歧如实登记」。

### 3.3 7 个补做：缺什么、需要什么输入

> 「缺什么」取自 CSV「理由」列；「需要什么输入」优先取 CSV 理由中的「输入=…」，其余转引 `DISPOSITION.md` §3（L62-L79）的「需输入…」行，均注明出处。本次**未核输入件现值**（§6）。

| # | 目录名 | 缺什么 | 需要什么输入 | 建议批次（CSV） |
|:--:|:--|:--|:--|:--|
| 1 | dup_audit_20261110 | 缺一页 md 结论与台账条目（读数已齐：2928 个 .py 只读普查、2517 个唯一 sha256、72 组重复） | 既有两件输出 `_da_summary.txt` + `_da_groups.json`（CSV 理由「输入=既有两件输出」；`DISPOSITION.md:L64`） | 第二批（补md，工作量小） |
| 2 | exit_lint_20261110 | 判据底座仍挂旧版 `_ec_criterion`；缺对接 `_e3_v3.py` 的改造与自测记录 | 测试脚本集（`DISPOSITION.md:L69`）；对接目标 `e3_unify_20261111/_e3_v3.py` | 第三批 |
| 3 | gate_exit_retrofit_20261110 | patched/ 24 个改造脚本缺统一回归日志与验收报告（对照件 `_gr_template_ctl_run.txt` 已实跑：-1→exit 0、1→exit 1） | 测试集运行验证（`DISPOSITION.md:L70`）；对照件 `_gr_template_ctl_run.txt:L37-L39` | 第三批 |
| 4 | ledger_exit_census_20261110 | 缺 md 沉淀（读数已齐：三本台账 76 处 EXIT=0，分布 31/1/44；cls 计数 5/28/1/2/40） | 既有 `_lc_out.txt:L8-L15`（`DISPOSITION.md:L71`） | 第二批（补md） |
| 5 | ok_falsify_20261110 | 缺 md 沉淀（读数已齐：413 件三维交叉表，_of_scope_out.json 97,659 B） | 既有 `_of_scope_out.json:L3390-L3430`（`DISPOSITION.md:L72`） | 第二批（补md） |
| 6 | unknown_locate_20261110 | 缺 md 沉淀（读数已齐：263 件 NO_EXIT_AT_ALL 的 stdout 产物通道普查，11 件仅 stdout.write：9 UNKNOWN + 2 ARTIFACT） | 既有 `_ul_stdout_census_out.txt:L22-L37`（`DISPOSITION.md:L79`） | 第二批（补md） |
| 7 | e3_unify_20261111 | 统一判据本体 `_e3_v3.py`（22,608 B）就绪但零跑测输出、零 md；缺 413 件全量扫描与 `E3_UNIFY.md` 验收报告 | `ok_falsify_20261110/_of_scope_out.json` 的 413 件清单（CSV 理由「输入=…」；`DISPOSITION.md:L67`） | 第二批（高优先） |

**小计：7 个**；其中 4 个（`dup_audit` / `ledger_exit_census` / `ok_falsify` / `unknown_locate`）读数已齐、只缺一页 md，2 个（`exit_lint` / `gate_exit_retrofit`）需改造与回归，1 个（`e3_unify`）需 413 件全量扫描。

### 3.4 7 个已入他处：结论在哪份 md 的哪一行（取自 CSV「取代证据」列，逐字转录）

| # | 目录名 | 结论所在 md 与行号（CSV「取代证据」原文） | 一句话理由（CSV「理由」摘要） |
|:--:|:--|:--|:--|
| 1 | ledger_apply_prep_20261110 | re_ledger_apply_20261111/APPLY_RECEIPT.md:L10-L23；re_ledger_verify_20261111/VERIFY.md:L16（V1 PASS）；GOAL_THREE_TARGETS_20261018.md:L9760/L9775/L9787/L9802/L9832（§605–§609 实测在册） | 空目录但目标已完成：§605–§609 五笔已于 11-11 21:1x 并入主台账（追加 28,512 B，759,518→788,030 B，sha256 a2579798…）… |
| 2 | re_crashwriter_static_20261110 | re_chain_synthesis_20261111/CHAIN_SYNTHESIS.md（证据缩写 cw，LEDGER_SECTION_DRAFT_v2.md:L6）；DISPOSITION.md:L74（引 _cw_disasm_out.txt:L80-L105） | 0x0054A56E 数据依赖链：RTTI 基类 vtable 0x7ECBFC/派生 0x7ECBDC、全局对象 0xAA1078、0x546069 全模块唯一虚派发点、0x54… |
| 3 | re_loadbench_diff_20261110 | re_progress_check_20261111/RE_PROGRESS_20261111.md:L118-L124（§8 表）；DISPOSITION.md:L75（引 _ld_diff_out.txt:L98-L103） | 大版 92,332 B（md5 3c47bff8…）与小版 25,604 B（生成器 2026-09-25 合成图）非同一张图；实载=222,799 B 变体（md5 11ec8f… |
| 4 | re_map_preset_decode_20261110 | re_chain_synthesis_20261111/CHAIN_SYNTHESIS.md:L77（④【已证】）；DISPOSITION.md:L76（引 _md_parse_out.txt:L140-L167） | 三图逐槽位解析：XMP29U2.MAP [Units]=3360（14 owner×240）、两份 yrm 均 240/160，台账声称 1680/1120 判「两份 yrm 均不… |
| 5 | re_orphan_owners_20261110 | re_chain_synthesis_20261111/CHAIN_SYNTHESIS.md:L75（③【已证】）；re_orphan_owners_20261110/_oo_map_out.txt [5c] 节；DISPOSITION.md:L77 | HouseClass owner 三层法：XMP29U2.MAP 14 owner 带各 400 实体（240 车+160 步）；MaxPlayer=2 与 14 owner 文件… |
| 6 | playerctrl_semantics_20261111 | re_chain_synthesis_20261111/CHAIN_SYNTHESIS.md:L81-L82（⑤【已证】）；re_chain_synth_v2_20261111/RE_GRADING.md:L43（R14 维持已证）；re_chain_v2_xverify_20261112/XVERIFY.md:L84（R15）；降级口径见 re_round_batch1_20261111/ROUND_BATCH1.md:L162-L163（R3-02 已证/R3-03 未证） | PlayerControl@0x824E28→HouseClass+0x1ED、PercentBuilt@0x8189A0→+0x571C 引擎零读取、8 处创建点均未测试该标志；… |
| 7 | slot2_fullscan_20261111 | DISPOSITION.md:L78（引 _sf_scan_out.txt:L1830-L1834）；re_round_batch1_20261111/ROUND_BATCH1.md:L40（R1..R5 收录） | 100% 分块重验：1714 个 slot2 形态点中可能指向 0x54A4F0/0x54A630 的恰 1 个=0x546069；已被处置书与因果链报告收录 |

**小计：7 个**；结论分别落在 `CHAIN_SYNTHESIS.md`（③/④/⑤）、`RE_PROGRESS_20261111.md` §8、`ROUND_BATCH1.md`、`APPLY_RECEIPT.md` / `VERIFY.md` / 主台账 §605–§609 等行号处。**这些行号本次未逐条打开验证**（§6）。

### 3.5 其余 5 条（补足 249 的判定分布）

- **口径外登记 3**（均为 B 类、日期 <20261106）：`qc151_carrierfix_20261020`（carrierfix.diff + report.json）、`t55k_20261020`（10 月真机测量数据轮 T55k 全套 receipt/measure）、`goal1_harness8_20261031`（10 月 harness8 判据/启动脚本族 + .mimosa 钩子状态件）。CSV 理由统一为「日期 <20261106，不在报告 182 口径内；是否补报告由十月线自行定」。
- **本检查写域 1**：`round_gap_disposition_20261112`（见 §3.1 第 12 行）。
- **补做（进行中）1**：`re_atlas_reassess_20261112`（20261112 当日新轮，报告口径外；R-036 重算 8/8 PASS、R-035 复核 23/23 PASS；CSV 判「登记不判」，建议批次「口径外（进行中）」）。

## §4 排序与三批建议

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

## §5 进度口径建议

**一句话：这个项目的「进度」只数「有 md 报告且结论已入账」的轮次——目录数不能当进度、无 md 的探针轮算「原始读数」不算「已成立结论」、空轮算 0；且任何计数必须绑定统计时点。**

落到本次 249 条：215 个「已成立」可作分子上限（其中还含 5 个 20261112 当日新增与 3 个口径外 B 件需各自标注），22 个 B 轮只是一手读数、不得计入「已成立结论」，12 个空轮计 0；182 / 193 / 249 分属不同口径与时点，不可互相代替。理由见 §1.4：目录计数是「活动量」不是「完成量」，连「带 md 的目录数」也会随会话单向增长。此建议与项目既有纪律「有目录 ≠ 有交付」（`ROUND_REPORT.md:137` 引 G-55 / G-57、`RE_PROGRESS_20261111.md:157-158`）一致。

## §6 边界与未验（如实）

1. **CSV 的「理由」列内容未逐条独立复核**。249 条判定是上一位执行方（WP-O）的人工定性，本任务只汇总、转录、排序，不重新审定。`ROUND_REPORT.md:179,229` 明记「WP-H / WP-O / WP-K2 的中间产物未被任何人复核，其正确性未验」；本次收尾未改变这一状态。
2. **「取代证据」未逐个打开验证**。§3.2 / §3.4 的取代件名与 `文件:行` 是 CSV 原文转录，除本报告明确读过的 `DISPOSITION.md`、`ROUND_REPORT.md`、`RE_PROGRESS_20261111.md` §9、`status_panel_20261112` 指纹 / 面板件、`docs_drift_20261112` 指纹表外，取代件是否仍然存在、行号是否对得上、结论是否真的覆盖，**均未验**。
3. **探针本身未运行；零真机**。本任务未执行任何探针 / 判据脚本，未启动 gamemd.exe / ra2loader / YURI.exe，未 attach、未读活进程内存、未写 hook / 采样 / MiniDump 代码。CSV 理由中「实跑」「ALL PASS」「8/8 PASS」「23/23 PASS」等字样均为上一位执行方或原轮次的转述，本次**未复跑、未验**。
4. **未重跑枚举**。只读了已有 `ROUND_GAP_DISPOSITION.csv` / `_enum_rounds.json` / `_enum_rounds_stdout.txt` / `_probe_digest.txt` / `_verify_census_stdout.txt` / `_final_hashes.txt` / `_build_csv.py` / `_enum_rounds.py` / `_verify_census.py`；未执行 `_enum_rounds.py` / `_verify_census.py` / `_probe_digest.py` / `_build_csv.py`。§1.3.1 的 mtime 是本次对 24 个顶层目录的**只读 `os.stat` 实算**，但 Windows 的 birth(ctime) 会受复制 / 解压影响，不等同「会话创建时刻」；5/4/2 时段分组转引派工书已知事实与 `ROUND_REPORT.md:133-134`，**未独立复核会话日志**。
5. **两处「最后 2 个新增」口径不同、未裁决**：`ROUND_REPORT.md:133` 指 `slot2_fullscan` / `playerctrl_semantics`（21:16「由 B 类计入」，本次 CSV 中仍为 B 类 md=0），而 §1.3.1 表第 10–11 行取的是 11-11 当天由无报告态补齐 md 的 2 个 A 类元轮次 `re_progress_check` / `re_progress_xverify`。两者不同源，本报告并列登记、不合并、不裁决。
6. **时点快照仍在 churn**：`_verify_census_stdout.txt:84-93` D 段已记录枚举后新增 `re_chain_v2_xverify_20261112`（现在顶层 250）；本写域自身也从枚举时点的 0 文件变成含本报告与三个辅助脚本，故「本检查写域（C 类）」判定仅对枚举时点成立。249 / 193 / 182 均已绑定各自时点。
7. **「已启动未落盘」是形态而非事实认定**：12 个空轮递归 0 文件可证「无落盘产物」，但「是否曾启动会话」需要会话日志，本次未验（§3.1）。
8. **§3.3「需要什么输入」部分转引 `DISPOSITION.md` §3**，未核这些输入件的当前存在性与现值；§4.1 排序、§4.2 排序、§4.3 三批划分是本报告基于 CSV 理由做的编排建议，不是上一位执行方的原判，也未经台账所有者批准。
9. **跨文件判定分歧如实登记、未裁决**：① `const_exit_fix_20261110` — `DISPOSITION.md:L62` 判「补做」并称 `VERIFY_A8.py:L824-L826` 实跑 ALL PASS，CSV 改判「废弃」且注明「本目录无落盘输出，实跑未验」；② `ledger_apply_prep_20261110` — `DISPOSITION.md:L85` 判「补做 P1」（21:05，早于并账落盘 21:16），CSV 据实修正为「已入他处」；③ `DISPOSITION.md` Top-5 补写轮次在 CSV 中判「已入他处」（§4）。三者均不属本任务裁决范围。
10. **口径外 3 件**（日期 <20261106）是否补报告由十月线自定，本次未验；`re_atlas_reassess_20261112` 进行中、登记不判；D-13 仍 PAUSE/BLOCKED，`housecount_trace` 动态 trace 未立项。
11. **写域与副作用**：仅在 `lead\round_gap_disposition_20261112\` 内新增文件；未修改 / 覆盖 / 删除任何既有件与任何目录；未执行 git add / commit / push / reset / checkout；未执行任何处置动作（不补做、不废弃、不清理、不归档）。

## §7 收尾回执

**改了哪些文件**（全部在唯一写域 `lead\round_gap_disposition_20261112\` 内，均为新增）：

| 文件 | 性质 |
|:--|:--|
| `ROUND_GAP_DISPOSITION.md` | **主交付**（本文件，§1–§7） |
| `_md_verify.py` | 只读核验脚本：CSV/JSON 计数复核、hashlib 指纹实算、20261111/20261112 顶层目录 mtime 只读实算 |
| `_md_append.py` | 成文辅助脚本：由 CSV 生成 §2–§7，逐节 append + flush + fsync 落盘 |
| `_md_check.py` | 成文后自检脚本：核对 §2/§3 各表行数、11 个新增目录、22/12 逐个列出、15 个取代件、必备关键词 |

> **篇幅说明（如实）**：本文件约 63 KB，高于派工书「目标 20–40 KB」。超出原因是 §2.1 把 215 个 A 类目录**全量逐行列出**（使 249 个目录名在本报告内逐条可查）与 §3.2 / §3.4 把「取代证据」**逐字转录**。为不删任何已定性目录、不缩任何取代件，保留全量；若需压缩到 40 KB 内，可只把 §2.1 改为按日期汇总表（其余章节不动）。
> 本报告内所有**源材料**指纹（§1.2）均为 `hashlib.sha256` 实算；主交付自身指纹见收尾回执消息，不在文内自指（避免自指哈希失效）。

**读了哪些文件（注明未重跑枚举）**：

- 写域内：`ROUND_GAP_DISPOSITION.csv`（250 行全文实读 + `csv.DictReader` 复核 249 数据行）、`_final_hashes.txt`、`_verify_census_stdout.txt`（全文）、`_build_csv.py`（全文）、`_enum_rounds.py`（全文）、`_verify_census.py`（全文）、`_enum_rounds.json`（由脚本只读解析，未全文通读）、`_enum_rounds_stdout.txt` / `_probe_digest.txt`（仅定向 grep 与 hashlib 实算，未全文通读）。
- 写域外（一律只读）：`lead\re_round_disposition_20261111\DISPOSITION.md`（全文）、`lead\re_session_kickoff_20261111\ROUND_REPORT.md`（全文）、`lead\re_session_kickoff_20261111\CHANNEL_TEST_AND_ASSESSMENT.md`（定向 grep）、`lead\re_progress_check_20261111\RE_PROGRESS_20261111.md`（§9 段）、`lead\status_panel_20261112\panel_forensics_stdout.txt` / `_panel_assemble_stdout.txt` / `STATUS_PANEL.md`（定向 grep）、`lead\docs_drift_20261112\_evidence\01_fact_side_fingerprints.md` / `DOCS_DRIFT_PROPOSAL.md` / `RECEIPT.md`（定向 grep）、`lead\re_dispatch_20261111\STATUS_BOARD.md`（定向 grep）。
- 只读 `os.stat`：20261111 顶层 19 个 + 20261112 顶层 5 个目录（共 24 个）的 mtime / ctime；未遍历、未写入。
- **未重跑枚举**：`_enum_rounds.py` / `_verify_census.py` / `_probe_digest.py` / `_build_csv.py` 均未执行；CSV、JSON、stdout、digest 都是上一位执行方实跑并在盘的产物。

**结论一句话**：全 `lead/` 树 249 个顶层轮次目录已逐条定性（215 已成立 / 22 原始读数 / 12 空轮；判定 215 已成立 + 15 废弃 + 7 补做 + 7 已入他处 + 3 口径外登记 + 1 本检查写域 + 1 补做进行中），窗口 182→193 的差 11 全部是 20261111 一天的新建/补齐所致、属时点差而非统计错误，进度只应数「已入账的已成立结论」。

**遗留未验项**：见 §6 全 11 条（重点是：CSV 理由未逐条复核、取代证据未逐个打开、探针未运行、11 个新增目录的时段归属未独立复核会话日志、两处跨文件判定分歧未裁决、12 个空轮是否真启动过未验）。所有处置动作（补做 / 废弃 / 清理）均**未执行**，留待授权。

---

> 本报告为「只差成文」收尾产物：枚举与定性全部由上一位执行方完成并在盘，本次零新增枚举、零真机、零处置、零 git 变更。
