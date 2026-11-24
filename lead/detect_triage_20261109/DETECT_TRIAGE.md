# DETECT_TRIAGE.md — 检测结果分诊、四级归类与处置建议

**执行者**：检测分诊撰写员（subagent） · **日期** 2026-11-09 · **唯一写域** `lead/detect_triage_20261109/`
**本件性质**：汇总/分诊/建议件。不启动真机、不写采样代码、不改任何被检脚本与台账、**不执行重跑**、不 commit / 不 push。
**引用约定**：`文件:行` = 本会话逐行读到的原文；`实跑命令 → 输出` = 本会话实际执行过的命令与结果；题给材料（【编排方指纹】【分诊数据】【分诊】【复核】）标为「题给」；本会话没有跑到的检查一律写「**未验**」，不补造。

---

## 1 目的与边界

**目的**：把上游两套静态检测器对 173 件 `check_*.py` 给出的 **40/6/80/47**（即 40 件 CONFIRMED / 6 件 SUSPECT / 80 件 LEGAL_AGGREGATE / 47 件 NO_SELFTEST）按「**该件的结论是否已被引用**」分到 A/B/C/D 四级，给出最小重跑集、成本估算、误报漏报影响与处置清单；并如实并入【复核】的 `verdict=partial` 及其两处破口。

**边界（本任务铁律，逐条遵守）**：
- **零真机**：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存。
- **零采样代码**：未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入、未写动态内存解析。
- **★ 绝对只读**：`lead/k1bit_detect_20261109/`、`lead/check_family_20261109/`、`lead/stale_pass_20261109/`、`lead/check_masking_20261109/`、`lead/d27|d28|d29|d30_ruling_20261106/`、`lead/refsync_scope_20261109/` 全部件与两件台账 `lead/PENDING_DECISIONS.md` / `lead/GOAL_THREE_TARGETS_20261018.md` **一律不修改、不追加、不覆盖**。本会话实跑 `git status --short -- <9 只读域 + 两账>` → 9 个目录全 `??`、两账 `MM`（与会话初始快照一致）；`git rev-parse HEAD` → `26574589aa8401e8f3f2934680a1ea7109bafa2d`。
- **唯一写域** `lead/detect_triage_20261109/`：本会话只新增 `DETECT_TRIAGE.md`（本件）、`_dtx_check.py`、`_dtx_check_out.json`；未改既有 `_dt_*` / `_dtv_*` 件。
- **只做分诊与建议**：★★ **不改任何被检脚本、不执行重跑**。本会话的 Python 只对冻结 JSON / 源码字节做只读 `hashlib` 与 `kd.analyse()` 静态复算（`_dtx_check.py:18-47`），没有调用过一件被检门禁的 `main()`，没有坏针注入，没有 `subprocess` 跑门禁。所有「重跑」均为**给 Leader 的建议**。
- **纪律**：Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib`；脚本一律 `sys.dont_write_bytecode = True`（`_dtx_check.py:12`）。本会话实跑 `find <9 只读域> -name '*.pyc' -newermt '2026-11-09 21:00:00'` → `0` 行（本次未新增 .pyc；历史 pyc 见 §6 未验项）。

**「检测到缺陷」≠「必须重跑」**：分级唯一标准是「结论是否已被引用」，不是检测器 verdict 的高低。故 36 件沙箱静态候选一律 D 级不动；SUSPECT 6 件两账 0 行引用 ⇒ 不升 A、不重跑、不加注（`_dt_REPORT.md:4,220-226`）。

---

## 2 上游指纹（七件）+ 检测复核

### 2(a) 七件编排方指纹，本会话 `hashlib` 独立实算 7/7 相符

**实跑命令**（cwd=`D:/Project/ra2-campaign-forge`）：
```
python -I -X utf8 -c "import sys; sys.dont_write_bytecode=True; import hashlib; ... 对 13 件逐件 open(...,'rb').read() 后 sha256/len(b) ..."
```
**输出**（前 7 行即题给【编排方指纹】七件，逐字符相符；完整 13 行另含 A 级 4 件 + carrier + 主报告，见 `_dtx_check_out.json:hashes` 与 `_dt_triage.py:70-85`）：

| # | 文件 | SHA256（完整 64 位） | 字节数 | 与题给 |
|---|---|---|---|---|
| 1 | `lead/k1bit_detect_20261109/_kd_detect_out.json` | `00f77fe0d5582d8eaec42f1b908d9f48c4b94b65b0b09b3b1e4609280f7ac239` | 251854 | 相符 |
| 2 | `lead/k1bit_detect_20261109/K1BIT_DETECTOR.md` | `40d79857bebc28fb1dd1d2f03afc7f1dc825b4b9cf9a56e55a0a93179ca32ad1` | 60565 | 相符 |
| 3 | `lead/k1bit_detect_20261109/_kd_literal_vs_semantic_out.json` | `af84560f288a0f74cac5f9f1f95f64f68c767e8a0aee32e869d1b0fc2ab9cc2f` | 39990 | 相符 |
| 4 | `lead/check_family_20261109/_cf_detect_out.json` | `17e83a81ecf0cca951825d3191bb0772011de1af3269d793922a8db068e5c3c2` | 130498 | 相符 |
| 5 | `lead/stale_pass_20261109/STALE_PASS_INVENTORY.md` | `a72d79b23b1329207a2c612d4244dec407ffaa4e0b91c397c3febb7a9cddd798` | 63656 | 相符 |
| 6 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 | 相符 |
| 7 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 | 相符 |

`_dt_REPORT.md:292-302` 的 11 行绑定行本会话用正则 `^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$` 复算 → `n_binding_lines=11`、`binding_strict=True`、`binding_first7_equal_my_hashes=True`（`_dtx_check_out.json`）；后 4 行=A 级 4 件的本会话实算值（§3(a)）。复核方另报 `strict=True / values_match=True`（题给【复核】①）。

### 2(b) 四数字：40 / 6 / 80 / 47

本会话实跑 `python -I -X utf8 -c "...读 _kd_detect_out.json 并 Counter(rows.verdict)..."` → `{'NO_SELFTEST':47,'LEGAL_AGGREGATE':80,'CONFIRMED_K1BIT':40,'SUSPECT':6}`，`sum=173 == kd['n']`（`_dtx_check_out.json:frozen_counts`）。题给【分诊数据】`n_confirmed=40 / n_suspect=6 / n_production=4 / n_sandbox=36`、分组 `_cm_tmp=22 / _cmv_tmp=5 / _sp_sandbox=9` 与本会话读 `_dt_triage_out.json:counts,group_counts` 逐项相符。

**独立重跑而非只信冻结 JSON**：上游 `python -I -X utf8 .../_dt_repro.py D:/Project/ra2-campaign-forge` 以 `spec_from_file_location` 对 173 件原始字节重跑 `kd.analyse()` → `matches_frozen_counts=True / verdicts_match_frozen_rows=True / sha_match_frozen_rows=True`（题给【分诊】evidence(a)，`_dt_repro_out.json:kd`）；复核方 `_dtv_verify.py` 再独立重跑 kd + cf → `kd_verdict_mismatches=[] / kd_sha_mismatches=[] / cf_verdict_mismatches=[] / cf_conf_mismatches=[]`（`_dtv_verify_out.json:detector`）。本会话自身只重跑了 3 个确切 fixture 与 2 个范围外候选（`_dtx_check.py:22-55`），**未对 173 件全量重跑 `kd.analyse()`**，全量重跑结论引用上游/复核方实跑输出并标注来源。

### 2(c) 与 cf 逐件一致（附诚实限定）

`_dt_repro_out.json:cf_identical` → `frozen_kd_vs_frozen_cf=True`、`refound_vs_frozen_cf=True`、`cf_only=[]`、`kd_only=[]`，即 **40 件 CONFIRMED 集合逐件相同**（`_dt_REPORT.md:49`）。复核方独立重跑：`confirmed_equal_frozen_cf=True`、`n_cf_kd_confirmed_disagreements=0`（`_dtv_verify_out.json:detector`）。

**限定（必须并列，不可写成「两器逐件全等」）**：
- 两器标签词表不同，173 行中 **171 行标签名不一致**，只 **CONFIRMED 名单**逐件相同；`_cf_detect_out.json` 自报 `suspect=3`，`_kd_detect_out.json` 自报 `suspect=6`（`_dt_repro_out.json:cf_identical`、`_dtv_verify_out.json:detector.n_cf_kd_verdict_disagreements=171`）。
- `K1BIT_DETECTOR.md:763` 自认两器的 `identical=True` 只是**共享模板前提下的口径一致，不是独立语义复核**；`K1BIT_DETECTOR.md:664-673` 自认复核 `partial` 的四个实质破口（死代码分支、名字启发式、fixture 漏判、`has_k` 被 `&=` 绕过）。
- 故本节「**逐件一致**」的准确含义 = **40 件 confirmed 名单逐件一致**（用于分诊宇宙），不是 173 件四分类逐件一致。

### 2(d) N5 有归因即合法、P1 无归因即缺陷

`_dt_repro_out.json:selftest.N5` → `want=LEGAL_AGGREGATE / got=LEGAL_AGGREGATE / has_k=False / collapse=['OR_COLLAPSE_gen'] / hits_retained=[{line:4},{line:6},{line:7}]`；`P1` 同为 `OR_COLLAPSE_gen` 但 `hits_retained=[]` → `CONFIRMED_K1BIT`。`_dtv_screens_out.json:selftest` 复核方独立重跑 `n=10 passed=10 failed=0`，`N5_same_OR_collapse_as_P1=True`。**结论**：同一个 OR 塌缩，**有逐 token 归因（N5 归因）** 即合法、**无归因** 即缺陷；自检 10/10 通过（`_dt_REPORT.md:50`）。这是「AST/数据流判据优于字面筛」的直接证据。

### 2(e) 宽窄口径漏检对比

本会话读 `_dt_repro_out.json:literal` 与复核方 `_dtv_screens_out.json:screens`（复核方独立重算复现）：

| 口径 | n_hits | tp | fn | fp | 漏掉的 4 件 |
|---|---|---|---|---|---|
| L1 `GENERATOR_FORM`（窄，`\bany\s*\(` 生成器式） | 49 | 36 | **4** | 13 | `check_d28.py` + 3 件 `_sp_sandbox/d28*` 副本 |
| L2 `ORCH_ANY_LINE`（窄，任一 any 行 + PASS） | 48 | 36 | **4** | 12 | 同上 |
| L3 `BROAD_ANY_PASS`（**宽口径**，`\bany\s*\(` + `^\s*print\(.*PASS`） | 54 | 40 | **0** | 14 | `misses=[]` |

**宽窄口径结论**：窄口径漏 4 件（全是 d28 模板，因 `any(present)` 是 `ast.Name` 而非生成器、d28 用三元式）、宽口径 `fn=0` 但 `fp` 反升到 14；`K1BIT_DETECTOR.md:762` 记 L1 13 / L3 14 件 FP ≈ **25–26% 误报率**，据此批量替换会改动无辜脚本（`CHECK_FAMILY_LINEAGE.md:418`）。`CHECK_FAMILY_LINEAGE.md:336` 实读已把「字面筛必然漏 d28/d27」标 **unconfirmed**（只在自定义窄口径成立，通用宽口径四件全命中）⇒ 编排方上一轮「必然漏」说法过宽，本件按 `:336` 原文订正。宽筛**只能当召回用的候选枚举，不能当判据/确诊/计数结论**（`K1BIT_DETECTOR.md:763-764`）。

---

## 3 四级分级（A/B/C/D 定义 + 逐件归类 + 计数表）

### 3(a) 定义（唯一标准 = 该件的结论是否已被引用）

| 级 | 定义 | 处置 | 件数 |
|---|---|---|---|
| **A 级** | 生产件 + 有台账登记 + **该登记行覆盖一条裁决**（PASS 以「已验证」身份被引用） | **必须重跑**（先加注后重跑） | **4** |
| **B 级** | 生产 + 有台账登记但**不**覆盖裁决（中间态） | 加注 + 重跑 | **0** |
| **C 级** | 生产 + **仅交付件引用**（两台账 0 行） | 加注（范围外实例见 §4(d)） | **0**（40 件内） |
| **D 级** | 沙箱/审计副本，PASS 从未被登记为「已验证」结论 | **不动、不加注、不重跑** | **36** |
| | | **合计** | **40** |

**计数自洽**（本会话实跑 `_dtx_check.py` 读 `_dt_triage_out.json` + `_dt_table.md`）：`counts={'A':4,'B':0,'C':0,'D':36}`、`groups={'沙箱 _cm_tmp':22,'沙箱 _cmv_tmp':5,'沙箱 _sp_sandbox':9,'生产件':4}`、`n_triage_rows=40`、`n_table_rows=40`、`A+B+C+D=40`、D 组 `22+5+9=36`（`_dtx_check_out.json`）；复核方 `_dtv_verify_out.json:arithmetic` 独立复算 `a_plus_b_plus_c_plus_d_equals_40=True / group_sum_equals_40=True / table_rows_equal_40=True`。

**B=0、C=0 不是漏判**：四件生产门禁的台账登记行 `PENDING:92/105/117/129` 同时就是 D-27..D-30 的裁决条目行（`_dt_scope_out.json:pending_ruling_section_start=88`），不存在「登记但不覆盖裁决」或「仅交付件引用」的中间态（`_dt_REPORT.md:101`）。**36 件 D 级沙箱的完整路径在两台账 0 行引用**（`_dt_scope_out.json:sandbox_in_ledgers.n_full_rel_cited=0`）；诚实限定：按 **basename** 两账有 27 件同名命中（复核方 `_dtv_verify_out.json:triage.sandbox_basename_hits=27`），故「两台账 0 行引用」严格指**完整路径**引用，措辞不可外推为「连同名都没提」。

### 3(b) 逐件归类表（40 件，一件不缺）

源 = `_dt_triage_out.json:rows` 全 40 条（每条含完整 64 位 SHA256 / 字节数 / 级 / 组 / 台账行），展示件 = `_dt_table.md:3-42` 全 40 行；本会话实跑逐行打印复核（`_dtx_check.py:57-76` → `n_triage_rows=40 / n_table_rows=40`）。下列路径均相对仓库根；SHA 列取前 16 位便于阅读，**完整 64 位**见 `_dt_triage_out.json:rows[*].sha256`。

| # | 级 | 组 | 路径 | SHA(前16) | 字节 | 台账行 / 裁决 |
|---|---|---|---|---|---|---|
| 1 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d27/a_kill_1/check_d27.py` | `3b769d7c64c27251` | 3764 | — |
| 2 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d27/a_kill_2/check_d27.py` | `3b769d7c64c27251` | 3764 | — |
| 3 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d27/b_kill_1/check_d27.py` | `e7284d28098e72e7` | 3792 | — |
| 4 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d27/b_kill_2/check_d27.py` | `f404f58783ab4da0` | 3783 | — |
| 5 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d27/control/check_d27.py` | `3b769d7c64c27251` | 3764 | — |
| 6 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d27/neg_ctrl/check_d27.py` | `3b769d7c64c27251` | 3764 | — |
| 7 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d29/a_kill_1/check_d29.py` | `2a50b09adff555db` | 3906 | — |
| 8 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d29/a_kill_2/check_d29.py` | `2a50b09adff555db` | 3906 | — |
| 9 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d29/and_kill_1/check_d29.py` | `2a50b09adff555db` | 3906 | — |
| 10 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d29/b_kill_1/check_d29.py` | `1648224881829853` | 3934 | — |
| 11 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d29/b_kill_2/check_d29.py` | `2399e95a43eaafa4` | 3934 | — |
| 12 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d29/control/check_d29.py` | `2a50b09adff555db` | 3906 | — |
| 13 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d29/neg_ctrl/check_d29.py` | `2a50b09adff555db` | 3906 | — |
| 14 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d29/neg_ctrl_all/check_d29.py` | `2a50b09adff555db` | 3906 | — |
| 15 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d30/a_kill_1/check_d30.py` | `6cb737963fc62a0e` | 3926 | — |
| 16 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d30/a_kill_2/check_d30.py` | `6cb737963fc62a0e` | 3926 | — |
| 17 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d30/and_kill_1/check_d30.py` | `6cb737963fc62a0e` | 3926 | — |
| 18 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d30/b_kill_1/check_d30.py` | `132685366f014171` | 3955 | — |
| 19 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d30/b_kill_2/check_d30.py` | `b1670537e12a6d7c` | 3951 | — |
| 20 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d30/control/check_d30.py` | `6cb737963fc62a0e` | 3926 | — |
| 21 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d30/neg_ctrl/check_d30.py` | `6cb737963fc62a0e` | 3926 | — |
| 22 | **D** | _cm_tmp | `lead/check_masking_20261109/_cm_tmp/d30/neg_ctrl_all/check_d30.py` | `6cb737963fc62a0e` | 3926 | — |
| 23 | **D** | _cmv_tmp | `lead/check_masking_20261109/_cmv_tmp/d27/v_a_kill_2/check_d27.py` | `3b769d7c64c27251` | 3764 | — |
| 24 | **D** | _cmv_tmp | `lead/check_masking_20261109/_cmv_tmp/d27/v_b_kill_2/check_d27.py` | `f404f58783ab4da0` | 3783 | — |
| 25 | **D** | _cmv_tmp | `lead/check_masking_20261109/_cmv_tmp/d29/v_b_kill_2/check_d29.py` | `2399e95a43eaafa4` | 3934 | — |
| 26 | **D** | _cmv_tmp | `lead/check_masking_20261109/_cmv_tmp/d29/v_neg_ctrl_all/check_d29.py` | `2a50b09adff555db` | 3906 | — |
| 27 | **D** | _cmv_tmp | `lead/check_masking_20261109/_cmv_tmp/d30/v_b_kill_2/check_d30.py` | `b1670537e12a6d7c` | 3951 | — |
| 28 | **A** | 生产件 | `lead/d27_ruling_20261106/check_d27.py` | `3b769d7c64c27251` | 3764 | `PENDING_DECISIONS.md:129` / D-27 |
| 29 | **A** | 生产件 | `lead/d28_ruling_20261106/check_d28.py` | `5b42a34a40046d7a` | 4539 | `PENDING_DECISIONS.md:117` / D-28 |
| 30 | **A** | 生产件 | `lead/d29_ruling_20261106/check_d29.py` | `2a50b09adff555db` | 3906 | `PENDING_DECISIONS.md:105` / D-29 |
| 31 | **A** | 生产件 | `lead/d30_ruling_20261106/check_d30.py` | `6cb737963fc62a0e` | 3926 | `PENDING_DECISIONS.md:92` / D-30 |
| 32 | **D** | _sp_sandbox | `lead/stale_pass_20261109/_sp_sandbox/check_d27_baseline.py` | `3b769d7c64c27251` | 3764 | — |
| 33 | **D** | _sp_sandbox | `lead/stale_pass_20261109/_sp_sandbox/check_d27_injected.py` | `f404f58783ab4da0` | 3783 | — |
| 34 | **D** | _sp_sandbox | `lead/stale_pass_20261109/_sp_sandbox/d28/check_d28_baseline.py` | `5b42a34a40046d7a` | 4539 | — |
| 35 | **D** | _sp_sandbox | `lead/stale_pass_20261109/_sp_sandbox/d28x/a/b/check_d28_baseline.py` | `5b42a34a40046d7a` | 4539 | — |
| 36 | **D** | _sp_sandbox | `lead/stale_pass_20261109/_sp_sandbox/d28x/a/b/check_d28_injected.py` | `f5ae184ca7ddc6cf` | 4569 | — |
| 37 | **D** | _sp_sandbox | `lead/stale_pass_20261109/_sp_sandbox/d29/check_d29_baseline.py` | `2a50b09adff555db` | 3906 | — |
| 38 | **D** | _sp_sandbox | `lead/stale_pass_20261109/_sp_sandbox/d29/check_d29_injected.py` | `2399e95a43eaafa4` | 3934 | — |
| 39 | **D** | _sp_sandbox | `lead/stale_pass_20261109/_sp_sandbox/d30/check_d30_baseline.py` | `6cb737963fc62a0e` | 3926 | — |
| 40 | **D** | _sp_sandbox | `lead/stale_pass_20261109/_sp_sandbox/d30/check_d30_injected.py` | `b1670537e12a6d7c` | 3951 | — |

**计数表**：A=4（#28–31）/ B=0 / C=0 / D=36（#1–27 共 27 件 + #32–40 共 9 件）；组内 D：`_cm_tmp` 22（#1–22）、`_cmv_tmp` 5（#23–27）、`_sp_sandbox` 9（#32–40）。`CHECK_FAMILY_LINEAGE.md:338` 自述 40 件是 AST 静态结构命中、含 13 件已注入哨兵的沙箱变体，「全库 40 件都带同一缺陷代码」**不成立** ⇒ D 级不动有独立依据。

---

## 4 最小重跑集、重跑成本、★ 该在 A 级被漏的检查

### 4(a) A 级 4 件逐件路径 + 台账行号 + 完整 SHA256/字节数

本会话 `hashlib` 实算 4 件（与 `STALE_PASS_INVENTORY.md:44-46,69` / `_cf_census.py:36-39` 登记值相符，`_dt_triage_out.json:prod_check` 全 `match=True`）：

| # | 路径 | 台账行号（逐字原文见下） | 裁决 | 完整 SHA256 | 字节 |
|---|---|---|---|---|---|
| A1 | `lead/d27_ruling_20261106/check_d27.py` | `lead/PENDING_DECISIONS.md:129` | D-27 | `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` | 3764 |
| A2 | `lead/d28_ruling_20261106/check_d28.py` | `lead/PENDING_DECISIONS.md:117` | D-28 | `5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268` | 4539 |
| A3 | `lead/d29_ruling_20261106/check_d29.py` | `lead/PENDING_DECISIONS.md:105` | D-29 | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` | 3906 |
| A4 | `lead/d30_ruling_20261106/check_d30.py` | `lead/PENDING_DECISIONS.md:92` | D-30 | `6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd` | 3926 |

**四行台账原文**（本会话 `sed -n '92p;105p;117p;129p' lead/PENDING_DECISIONS.md` 实读，与 `_dt_scope_out.json:pending_lines_verbatim` 一致）：`:92` 「…门禁 `check_d30.py` 实跑 **exit=0**（2026-11-07 复跑仍 PASS）。」；`:105` 「…门禁 `check_d29.py` 实跑 **exit=0**。」；`:117` 「…门禁 `check_d28.py` 实跑 **exit=0**。」；`:129` 「…门禁 `check_d27.py` 实跑 **exit=0**。」四行均位于 `PENDING_DECISIONS.md:88` 起的「已裁决记录」段，各自包裹 D-27..D-30 裁决 ⇒ 覆盖裁决成立；`GOAL_THREE_TARGETS_20261018.md` 逐行 basename 命中 **0 行**（`_dt_scope_out.json:ledger_citations`）。

**「覆盖裁决」不得夸大**：四件门禁自述是「格式/机械检查」（`check_d27.py:1` / `check_d28.py:1` / `check_d29.py:1` / `check_d30.py:1`），`STALE_PASS_INVENTORY.md:196,219-220` 记其无任何数值/逻辑断言、裁决定谳行不引用 gate、形式要件失效 7 处而实质结论失效 **0 处** ⇒ 重跑修的是**「已验证」登记行的证据资格**，不是重审或推翻 D-27..D-30 实质结论（`_dt_REPORT.md:127`）。

### 4(b) 重跑成本估算（估算，未验）

**依据**（本会话逐行实读）：四件源码 107/122/110/110 行、只读（`_dt_REPORT.md:131` 引 `check_d27.py:53-100` / `check_d28.py:53-115` / `check_d29.py:49-105` / `check_d30.py:49-105`）；`STALE_PASS_INVENTORY.md:251-268` 本会话 `sed` 实读的甲' 外壳「逐输入独立跑 + AND_k + 坏针注入」及两条陷阱；`_sp_andk.py:7-40` / `_spi_andk_out.txt` 上游已落盘 4/4 演示（`AND_k(over 2 real per-word runs)=True`、`BAD_NEEDLE_CAUGHT=True`、`DISTINGUISHABLE_PASS=True`，见 `STALE_PASS_INVENTORY.md:265`）。

| 项 | 估算 |
|---|---|
| 输入 | 各件 `RULING_D*.md` + `FACTCHECK.md`（当前盘、绑 SHA256+字节数；`STALE_PASS_INVENTORY.md:139` 记输入未变） |
| 执行数 | **k=2 各 1 次**（d27 `check_d27.py:84` `("外推","卡顿不存在")`；d28 `check_d28.py:90` `("历史数字","1681")`；d29 `check_d29.py:76` `("互斥","前提")`；d30 `check_d30.py:76` `("93.98","误报率")`，逐字见 `STALE_PASS_INVENTORY.md:253`）+ **每根坏针哨兵 1 次** ⇒ **每件 4 次、四件共 16 次**极短只读脚本执行 |
| 前置条件 | ① 先生成 12 份 `_w_dNN_[ABS].py` 沙箱副本（`_sp_andk.py:7-15` hardcode，`STALE_PASS_INVENTORY.md:268` 自认「演示外壳、非可部署门禁」，缺「生成→落盘→驱动」序列）；② 三套路径布局：`check_d27.py:8` CWD 相对、`check_d29.py:50` / `check_d30.py:50` `__file__.parent`、`check_d28.py:54-55` `parents[2]`（`STALE_PASS_INVENTORY.md:255` 记漏此点曾得 6 个 `EXIT=2` 作废）；③ 口径陷阱 `STALE_PASS_INVENTORY.md:267`（`--include-refuting` 会引入第三套口径）；④ 每次绑「被核脚本 SHA256 + 字节数 + 输入指纹 + 命令全文 + stdout sha256」（`:261`） |
| 耗时 | **「分钟级（约 10–30 分钟人工/脚本编排）」= 估算、未验**。本会话**没有执行重跑、没有计时输出** ⇒ 不给秒数。无真机、无采样、无网络；主要成本是编排与口径比对 |
| 唯一写域 | 重跑产物须落执行方自己的有效写域；四件 `lead/d2[7890]_ruling_20261106/` 在本任务绝对只读，本会话未改 |

### 4(c) 只重跑 A 级够不够

- **对「40 件集合」：够**。B=0、C=0 ⇒ 「B/C 全部加注」是**空动作**；D=36 按定义**不动**，给 D 加注会把审计副本污染成看似生产件（`CHECK_FAMILY_LINEAGE.md:338,418`）。A 级 4 件须「**先加注、再重跑**」，不是只重跑（`_dt_REPORT.md:146`）。
- **对「所有已引用的 PASS」：不够**。题给【分诊】triage 与【复核】④ 同判：至少还须覆盖 ① `_rs_carrier_scan.py` 的 3 行交付件 PASS + 6 行同源件数结论；② `PENDING:162/186/199` 三行 C 级顺手定级（本会话 `sed` 实读 `:162` `check_d26.py` exit=0、`:186` `check_d25.py` exit=0、`:199` N-1「门禁 exit=0」；`_dt_leak_out.json:registered_not_confirmed` 两器判 `LEGAL_AGGREGATE`/cf 对 d26 `SUSPECT`，无注射实证 ⇒ **不是漏 A，是判据分歧**，不得凭 verdict 直接升 A）。
- 结论：**最小重跑集（40 件宇宙）= A 级 4 件**；若目标扩到「所有已引用 PASS 可信」，最小**处置**集 = 4 件 A + 1 件范围外 carrier 加注/重跑 + 3 行 C 级定级。本任务按纪律**不执行任何重跑**。

### 4(d) ★ 该在 A 级被漏的检查（漏检检查；复核方 `partial` 的核心破口）

**漏检检查方法**：不要只按 `check_*.py` 枚举；须并集 ① 173 件清单 ② 两台账 + 只读交付件所有 `PASS / exit=0 / SELF_TEST` 登记行的被核脚本 basename ③ 所有 `*_scan.py` / `*_gate.py` / `*_verify*.py` 等非 `check_` 前缀脚本，再逐件跑 `kd.analyse()` 并查其 PASS 是否被引（`_dt_REPORT.md:164`）。上游 `_dt_leak.py` 实跑：两账 121 个 `*.py` basename、6 个被引门禁，`a_candidates_not_A=[]`（复核方 `_dtv_verify_out.json:leak`：**就 40 件集合而言漏 A = 0**）；`find . -path ./.git -prune -o -type f -name 'check_*.py' -print` → `173 = _cf_filelist.txt = _dt_find_list.txt`，三集合差为空（`_dt_scope_out.json:census`）。

**★ 但按「结论是否已被引用」这一分级口径，有 1 件本该进处置集却没有级**：

| 对象 | 本会话独立 `--one` 复跑（`_dtx_check.py:49-55` → `_dtx_check_out.json:probes[0]`） | 引用与上游实证 |
|---|---|---|
| `lead/refsync_scope_20261109/_rs_carrier_scan.py` | `sha256=9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57` / 16053 B / `verdict=CONFIRMED_K1BIT` / `has_k=true` / `attribution=false` / 三处塌缩 `ARGMIN_REVERSE_MASK` + `BIT_ACCUM_AugAssign_BitAnd` + `OR_COLLAPSE_gen` | 文件名非 `check_` 前缀 ⇒ `in_confirmed_40=false / in_kd_rows_173=false`（`_dt_scope_out.json:carrier_one`）；PASS 登记于 `REFSYNC_SCOPE_FIX.md:251/252/253`（本会话 `sed` 实读 3 行 `SELF_TEST = PASS` 6/6），复核方另记 `:117` `EXIT=0`（`_dtv_scope2_out.json:probes[0].cited_lines`）；`STALE_PASS_INVENTORY.md:130-132` 判 **A+B 级 P0**、`:165-170` 实测「正确 AND_k 下应为 FAIL」，下游 `:273/:274/:276/:282-286` 六行件数结论同源 |

复核方【复核】④ 原话：该件「有已被引 PASS + 上游 A+B 注射实证，却未进 A 级/最小重跑集」，是 **按题给分级口径的唯一有上游实证的漏 A 候选**；`_dt_REPORT.md:148,163` 已充分披露它是「范围外 C 类实例」，但头部「最小重跑集 = A 级 4 件」**只在 40 件宇宙内成立**。⇒ 本件结论：40 件内 **A=4 不变**；把 carrier 并入最小**处置**集（加注 + 按甲' 外壳重跑），由 Leader 决策与执行（该件绝对只读，本任务无权改）。

**第 2 件范围外静态候选（复核方 ④ 补充，本会话复现）**：复核方按回件自述枚举法对 `_dtv_allpy.txt`（`find . -path ./.git -prune -o -type f -name '*.py' -print`，13328 行、`stderr=0 B`）另找到 `out/re_work/work_chain/CONTINUE_20261003/lead/decide_all/scripts/selfgate.py`。本会话 `_dtx_check.py` 独立复跑 → `sha256=6aeecd99ec6c723974e8ea00c14e3e1674917cfeb4600b04d4c341d11dc8da58` / 12858 B / `verdict=CONFIRMED_K1BIT` / `has_k=false` / `collapse=['BIT_ACCUM_bool_and','OR_COLLAPSE_gen']`（`_dtx_check_out.json:probes[1]`），与 `_dtv_verify_out.json:leak.noncheck_confirmed_cited[1]` 相符。本会话实跑 `grep -rn -F "decide_all/scripts/selfgate.py" lead --exclude-dir=detect_triage_20261109` → **0 命中**；`grep -c -F "selfgate"` 两台账 + `REFSYNC_SCOPE_FIX.md` → `0/0/0`。⇒ **按「结论已被引用」不构成 A/B/C**，属静态候选/疑似假阳（`has_k=false` 且 §5 已证 `&=` 假阳机制），标 **未验**、不动作；但它使 `_dt_REPORT.md:164` 「本会话用这个方法找出 1 件范围外」在其自身方法下不完整（至少 2 件：1 件被引、1 件无引用）。

### 4(e) 【复核】verdict 如实登记

题给【复核】`verdict = "partial"`（非 `refuted`、非 `confirmed`）：「①–③、⑥ 独立重现通过；两处使回件不能判『完全确认』：(a) 绝对只读域内出现 2 个新增 .pyc，回件未申报；(b) 按『结论是否已被引用』，`_rs_carrier_scan.py` … 却未进 A 级/最小重跑集，且回件自述的枚举法独立跑出第 2 件范围外静态候选」。
**按交付规则：`partial` 标 `unconfirmed`** ⇒ 本件把「最小重跑集 = 4」限定为 **40 件宇宙内结论 / 标 unconfirmed（对全库已引用 PASS 宇宙）**；`_dt_REPORT.md` 的 §0/:7 用 `git status --short` 的 `??` 证明「只读域未改」在目录粒度上**检测不到新增 .pyc**，该表述不完整，本件 §1 已改为「未改任何源文件字节；历史 pyc 见未验项」。本会话实跑 `find <9 只读域> -name '*.pyc' -printf ...` → 共 8 个历史 pyc，其中 `lead/k1bit_detect_20261109/__pycache__/_kd_selftest.cpython-312.pyc`（20:16:53.744）与 `lead/check_family_20261109/__pycache__/_cf_detect.cpython-312.pyc`（20:16:53.755）正是复核方指出的、落在 `_dt_repro.py`（20:16:33 落盘）导入窗口内的 2 件；本会话窗口（21:00 之后）新增 pyc = **0**，7 件冻结指纹与 11 行绑定值复核后仍全等 ⇒ 未改任何源文件字节。

---

## 5 误报漏报影响 + SUSPECT 6 件怎么处理

### 5(a) 误报（合法聚合被判 CONFIRMED）的后果

**本会话实跑假阳**（`_dtx_check.py:22-27` 复跑 `_kdv_probe3.py:19-30` 确切 fixture）→ `verdict=CONFIRMED_K1BIT / want=LEGAL_AGGREGATE / has_k=false / n_accum=1 / false_positive=true`（`_dtx_check_out.json:probe3`）；复核方 `_dtv_fixtures_out.json:probe3` 同值。成因 `_kd_detect.py:484-487` 的 `has_k` 硬门槛被 `ok &= good` 绕过（`K1BIT_DETECTOR.md:671,738` 自认）。
**后果链**：合法件误入 40 → 若生产且 PASS 已登记则被误升 A → 多一次重跑（4 次只读执行 + 加注 + 指纹绑定）+ 一条本不该有的 `UNTRUSTWORTHY` 加注；若按字面筛批量替换，L1 `fp=13` / L3 `fp=14`（25–26%，`K1BIT_DETECTOR.md:762`）会改动无辜脚本并连带证据副本（`CHECK_FAMILY_LINEAGE.md:418`）。
**对本次 4 件 A 级影响有限**：「坏针仍 PASS」来自 `STALE_PASS_INVENTORY.md:94-101` 的独立注射实证（本会话 `sed` 实读四组 BASE/INJ 输出逐字一致 + `EXIT=0/0`），不是检测器 verdict ⇒ 即便检测器对这 4 件误报，A 级结论不倒。**诚实限定**：题给【复核】⑤ 指出，「加注可逆」措辞乐观 —— 台账加注只能由 Leader 改（`STALE_PASS_INVENTORY.md:5,247`），非执行方可自行回退；本件不沿用「可逆」，改记「可据实更正、但须 Leader 执行」。

### 5(b) 漏报（真缺陷未检出）的后果

**本会话实跑假阴**（`_dtx_check.py:29-43` 复跑 `_kdv_semantic_probe.py:101-111 / 113-123`）→ V7 `verdict=LEGAL_AGGREGATE / want=CONFIRMED_K1BIT / has_k=false`、V8 同（均 `false_negative=true`，`_dtx_check_out.json:V7,V8`）；复核方 `_dtv_fixtures_out.json` 同值。`K1BIT_DETECTOR.md:669-670` 另记改名启发式破口（`words`→`zzz` 即翻盘）。**范围性漏报** = `_rs_carrier_scan.py` 因命名不在 173 件普查（§4(d)）。
**后果链**：真缺陷件未进 40 → 未分级 → 该加注的没加注、该重跑的没重跑 → PASS 继续以「已验证」身份沿引用链放大。本会话 `sed -n '251,253p' lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md` 实读 3 行 `SELF_TEST = PASS`；`STALE_PASS_INVENTORY.md:165-170` 实读 `:273/:274/:276/:282-286` 六行同源件数结论与「AND_k = FAIL」实测 ⇒ 一漏即连带 3 行 PASS + 6 行结论失去自检护航。

### 5(c) 哪个更严重

**判断：漏报更严重**（`_dt_REPORT.md:198-203`，题给【分诊】risk 同判，复核方【复核】⑤ 认定「成立且限定诚实」）：
1. 误报代价**有界、自曝**：多 4 次只读执行 + 一条加注；重跑会产出「逐输入全 PASS + 坏针被抓」的证据，反证该件合法，加注可据实更正（须 Leader）。
2. 漏报代价**无界、隐蔽**：漏掉的件不触发任何动作，「已验证」身份默认延续（`STALE_PASS_INVENTORY.md:165-170`）。
3. 四级分诊只对「已进入 40 件」生效：误报是「集合内多一件」有兜底，漏报是「集合外整件消失」**无兜底通道**。
4. 策略：**召回优先** —— 最宽口径 L3 `fn=0` + 文件名并集枚举做候选；但宽筛只当候选枚举，须经 AST/数据流 + 独立负控 + 动态 AND_k 才升 A 级（`K1BIT_DETECTOR.md:763-764`）。
5. 限定：这是**处置决策**判断，不是检测器精度判断；本会话未量化全库真值，无法给实际漏报率（`K1BIT_DETECTOR.md:826` 自认）。

### 5(d) SUSPECT 6 件怎么处理（**未验**）

**逐件清单**（`_dt_repro_out.json:suspect_rows` 全 6 条；两账引用 0 行见 `_dt_scope_out.json:suspect6_in_ledgers` 逐件 `full_rel_cited=false / basename_cited=false`）：

| # | 路径 | 字节 | has_k | onebit_exit | 塌缩 | cf 口径 |
|---|---|---|---|---|---|---|
| 1 | `out/re_work/_lead_baseline/W3/forensics/snapshot_R182/coverage_ledger/_verify_cmdwindows_20261002/check_windows_cmds.py` | 5811 | false | true | OR_COLLAPSE_gen | OTHER |
| 2 | `out/re_work/_lead_baseline/W3/forensics/snapshot_R196/coverage_ledger/_verify_cmdwindows_20261002/check_windows_cmds.py` | 5811 | false | true | OR_COLLAPSE_gen | OTHER |
| 3 | `out/re_work/qc/W3_20261001/coverage_ledger/_verify_cmdwindows_20261002/check_windows_cmds.py` | 5811 | false | true | OR_COLLAPSE_gen | OTHER |
| 4 | `out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.py` | 31955 | false | true | 2×OR_COLLAPSE_gen | **SUSPECT** |
| 5 | `out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.template.py` | 11843 | false | true | 2×OR_COLLAPSE_gen | **SUSPECT** |
| 6 | `out/re_work/re_sprint/S1/check_134_inc.py` | 455 | false | **false** | OR_COLLAPSE_gen | OTHER |

**口径差如实并列**：`_cf_detect_out.json:suspect=3`（`check_d26.py` + 2×`check_fileoffset_axiom*.py`）、`_kd_detect_out.json:suspect=6`；`check_d26.py` 被 kd 判 `LEGAL_AGGREGATE`（`_dt_scope_out.json:suspect_compare.cf_suspect_kd_verdict`），两件 axiom 两器同为 SUSPECT，其余 4 件 kd 独有（`K1BIT_DETECTOR.md:719`）。
**处理建议（本任务不执行）**：① **不升 A、不重跑、不加注、不删除**，标 `UNVERIFIED`：6 件 PASS 没有被登记引用 ⇒ 按「结论已被引用」连 C 级都不算（`_dt_REPORT.md:221`）；② 3 件 `check_windows_cmds.py:82` 是对错误签名的单固定谓词存在性、更像合法件，2 件 axiom 有 `GOLDEN_POS/NAIVE_FLOOR` 反掩蔽硬闸、`K1BIT_DETECTOR.md:728` 记修正版把它们判静态候选但**该结论自标未验**，`check_134_inc.py:8` 9 行且无 PASS 出口；③ **本会话只读 4 件代表源码行、未逐件通读全部 6 件、未做坏针注入** ⇒ 逐件定级 = **未验**（复核方【复核】④ 亦标未验）；④ 建议 Leader 单列一条待办「SUSPECT 6 逐件通读 + 是否纳入下一轮清单」，**本轮不因 SUSPECT 增改 40 件集合、不改 A 级 4 件**。

---

## 6 复核回件（绑定行，格式固定）+ 结论 + 未验项

### 6(a) 复核回件：**绑定行**

被核对象 = 题给【编排方指纹】7 件 + A 级 4 件生产门禁，共 11 行；全部由本会话 `hashlib` 独立实算（`_dtx_check.py:64-88` → `_dtx_check_out.json:hashes,binding_first7_equal_my_hashes=True`；`_dt_triage_out.json:binding` 11 条全 64 位），格式经本会话正则 `^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$` 校验 `strict=True`。按题给【复核】`sha256Line` 的项目 §6 惯例，首件绑定值即本回件的绑定行：

被核对象 SHA256 = 00f77fe0d5582d8eaec42f1b908d9f48c4b94b65b0b09b3b1e4609280f7ac239，字节数 = 251854

完整 11 行（与 `_dt_REPORT.md:292-302` 逐字符一致，值前不插路径、括号、星号、反引号或空格）：

被核对象 SHA256 = 00f77fe0d5582d8eaec42f1b908d9f48c4b94b65b0b09b3b1e4609280f7ac239，字节数 = 251854
被核对象 SHA256 = 40d79857bebc28fb1dd1d2f03afc7f1dc825b4b9cf9a56e55a0a93179ca32ad1，字节数 = 60565
被核对象 SHA256 = af84560f288a0f74cac5f9f1f95f64f68c767e8a0aee32e869d1b0fc2ab9cc2f，字节数 = 39990
被核对象 SHA256 = 17e83a81ecf0cca951825d3191bb0772011de1af3269d793922a8db068e5c3c2，字节数 = 130498
被核对象 SHA256 = a72d79b23b1329207a2c612d4244dec407ffaa4e0b91c397c3febb7a9cddd798，字节数 = 63656
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
被核对象 SHA256 = 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c，字节数 = 3764
被核对象 SHA256 = 5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268，字节数 = 4539
被核对象 SHA256 = 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14，字节数 = 3906
被核对象 SHA256 = 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd，字节数 = 3926

**复核 verdict 如实记**：题给【复核】`verdict="partial"`（ranCommands=41）⇒ 按交付规则标 **`unconfirmed`**：①–③、⑥ 独立重现通过（7/7 指纹、173 件重跑、40 行逐件分级、算术自洽）；两处破口 = (a) 绝对只读域 2 个新增 `.pyc` 未申报（本会话 §4(e) 已复现其 mtime 并订正表述）、(b) carrier 按「结论已被引用」口径未进 A/最小重跑集 + 自述枚举法漏报第 2 件范围外候选（本会话 §4(d) 已复现两件）。**不是 `refuted`**：40 件四级计数与 A 级 4 件逐件归类在 40 件宇宙内**全部独立重现通过**；受 `partial` 影响的是「最小重跑集对全库已引用 PASS 的完备性」与「只读域目录粒度表述」，标 unconfirmed。被核主件 `_dt_REPORT.md` 本会话 `hashlib` 实算 `sha256=6cb50481f574bba0fd33995ea788f87d0da0a6cbf6a7d922cb5a8628a06405ea / 40462 B`（与题给【复核】末段自报一致）。

### 6(b) 结论：最终数字与处置清单

**最终数字**：**A + B + C + D = 4 + 0 + 0 + 36 = 40**（逐件表见 §3(b)，40 行一件不缺）；上游四数字 **40 / 6 / 80 / 47**（和 = 173）。**最小重跑集（40 件宇宙）= A 级 4 件**；对全库已引用 PASS 宇宙该结论 **unconfirmed**（`partial`）。

| 序 | 谁 | 动作 | 件数 / 依据 |
|---|---|---|---|
| P0-1 | Leader | `PENDING:92/105/117/129` **就地加注**（不删原文、不改数字、不撤回裁决），状态 `UNTRUSTWORTHY`，先加注后重跑 | 4 行；`STALE_PASS_INVENTORY.md:5,228,234-237,247-249`；本会话 §4(a) 逐字原文 |
| P0-2 | Leader / 执行方 | 4 件按甲' 外壳重跑：12 份沙箱副本生成→落盘→驱动、三套路径布局、逐输入独立跑 + `AND_k` + 每根坏针哨兵、绑 SHA256+字节数+命令全文+stdout sha256、登记逐输入判定表 | 4 件 / 16 次只读执行；`STALE_PASS_INVENTORY.md:251-268`（`:267` 口径陷阱、`:268` 部署陷阱）；`_sp_andk.py:7-40` 4/4 已演示 |
| P0-3 | Leader | 加注**不要漏 `PENDING:117`（D-28）**：它在 D-27↔D-29↔D-30 引用链上游 | `STALE_PASS_INVENTORY.md:176,211` |
| P1-1 | Leader | 对范围外 `REFSYNC_SCOPE_FIX.md:243/251/252/253/273/274/276/282-286` 加注「同源输出，效力待重跑」，并把 `_rs_carrier_scan.py` 并入最小处置集（按甲' 外壳重跑） | 1 件 / 3 行 PASS + 6 行同源结论；`STALE_PASS_INVENTORY.md:130-132,165-170,174,238-241`；本会话 §4(d) `--one` 复跑 |
| P1-2 | Leader | `PENDING:162/186/199` 用同一甲' 外壳顺手定级（C 级、未注射实证、**不得直接升 A**）；`selfgate.py` 等无引用静态候选只登记不动作 | 3 行 + 1 件标未验；`_dt_leak_out.json:registered_not_confirmed`；`_dtx_check_out.json:probes[1]` |
| P2 | 检测器维护方 | SUSPECT 6 逐件通读 + 注射实证；核 `_kd_pasteable.py` 多出 2 件是否真属本缺陷；修 `has_k` 被 `&=` 绕过的假阳与改名/换写法假阴 | `K1BIT_DETECTOR.md:664-673,728,738,824-833`；本会话 §5(a)(b)(d) |
| P3 | 检测器维护方 | 清单枚举从 `check_*.py` 扩到「两账+交付件登记行被引脚本 ∪ `*_scan.py`/`*_gate.py`/`*_verify*.py` 并集」，重跑 173→新全集；补 `.git/` / 符号链接边界说明 | `_dt_REPORT.md:164`；`K1BIT_DETECTOR.md:831`；复核方 `find` 全树 `13328` 件 `.py` 索引 |
| — | 全员 | **36 件 D 级沙箱保持不动**（不加注、不重跑、不替换）；**SUSPECT 6 标 UNVERIFIED 不动作** | `CHECK_FAMILY_LINEAGE.md:338,418`；`K1BIT_DETECTOR.md:819` |

> 两台账与 `REFSYNC_SCOPE_FIX.md` 在本任务绝对只读，**所有加注/重跑只由 Leader 执行**；本任务只建议、未执行、未验证执行结果（`STALE_PASS_INVENTORY.md:5,174,228`）。

### 6(c) 以后新增 check 脚本的前置检查（建议，未执行）

1. **上线前先跑语义候选器 + 独立正/负控**：`ast.parse` → k 源 → 有损归约 → 1-bit 出口 → 归因四信号；负控必须覆盖 `all()`、跨样本单字面存在性、逐输入打印、保基数、改名/换写法/标量同名；`has_k` 为硬门槛，`&=`/argmin/三元不得绕过（`K1BIT_DETECTOR.md:816-818`；本会话 §5(b) V7/V8 复现假阴）。
2. **报 PASS 前必须做坏针对照**：k≥2 给「逐输入判定表」+ 显式 `AGGREGATE = AND_k(...)` + `DISTINGUISHABLE_PASS`；门禁与诊断量（`EXCLUSIVE`/`HITSET`/`MASKED_*`）严格分离；禁止裸 `exit=0` 当验收结论（`STALE_PASS_INVENTORY.md:363-364`）。
3. **强制指纹绑定**：登记行带「被核对象 SHA256 + 字节数 + 输入语料/文档快照指纹 + 命令全文（逐字含所有参数）+ CWD + stdout 落盘路径及其 sha256」（`:362`；本件 §6(a) 绑定行格式）。
4. **效力状态字段**：每条 PASS 打 `status ∈ {VERIFIED, UNTRUSTWORTHY, STALE_INPUT, UNVERIFIED, HISTORICAL_OBSERVATION}`，并标 `形式要件/实质结论` 与 `我亲跑/来源声明`（`:355,360`）。
5. **命名/清单并集双向对账**：非 `check_` 前缀（`_rs_carrier_scan.py` 的教训）必须显式登记；每次新增后用 `find . -type f -name 'check_*.py'` 与「被引脚本并集」双向对账，不只比 173 件清单（`_dt_scope_out.json:census` 实跑 `173=173 / live_only=[] / list_only=[]`）。
6. **失效回写通道**：任何复核判某 PASS 不可信，必须在原登记行就地加注并同步扫描/加注所有下游引用（`:361`；`:346` 自反承认上一轮漏了 `FIX:243/273-276/282-286`）。
7. **只写域与字节码约束**：跑前跑后重核被检脚本指纹（`git diff --name-only HEAD -- '*check_*.py'` = 0）、结果落 JSON、写域外只读；导入只读域模块时设 `sys.dont_write_bytecode = True`，避免 CPython 把 `.pyc` 写进绝对只读目录（`_dtx_check.py:12`；题给【复核】⑦ 的 2 件 `.pyc` 教训）。

### 6(d) 判不了什么 / 未验项（如实列）

1. **不能确诊「坏针仍 PASS」**：本会话零真机、零采样、未跑被检门禁、未做动态坏针注入；40 件是**静态结构候选**（`K1BIT_DETECTOR.md:18,825`）。A 级 4 件的「已证明不可信」来自 `STALE_PASS_INVENTORY.md:94-101` 的**上游实跑**，本会话只 `sed` 读其输出文本，**未复跑注射命令** ⇒ 题给/上游材料记录，本会话未验。
2. **不能给重跑真实耗时**：§4(b) 「分钟级」为**估算、未验**；本会话无计时输出、未执行任何重跑。
3. **不能量化全库误报率/漏报率**：只复现 3 个确切 fixture（probe3 假阳、V7/V8 假阴）与 3 种字面筛混淆矩阵，未建立全库真值（`K1BIT_DETECTOR.md:826-828`）。
4. **SUSPECT 6 未逐件通读 / 未注射**：本会话只读 4 件代表源码行；修正版多出的 2 件是否真属本缺陷 = **未验**（`K1BIT_DETECTOR.md:727-728,827`）；cf=3 / kd=6 口径差如实并列、未裁决。
5. **不能判 D-27..D-30 裁决实质**：本任务只判 PASS 的证据资格/引用结构；`STALE_PASS_INVENTORY.md:213` 自认未重跑 `_d27_facts.py` 等数值断言。
6. **清单边界**：`.git/` 内部、符号链接目标未纳入（本会话 `find` 复算的是 `check_*.py` 与复核方 `*.py` 两种口径，复核方索引 13328 件 `.py` 中仅对 2 件做了 `--one` 复跑，**未对 13328 件全量跑 `kd.analyse()`**）；`selfgate.py` 是否被别处以 PASS 引用 = 本会话按三件文档 + `lead` 全树 grep **0 命中**，其余文档全集**未验**。
7. **不能覆盖运行时 k 源**：别名/闭包/`eval`/跨模块常量/`globals()` 注入不在静态数据流内（`K1BIT_DETECTOR.md:830`）。
8. **「绝对只读域未改」限定**：本会话未改任何源文件字节（7 件指纹 + 11 行绑定值复核后全等、`HEAD` 未变、本会话窗口新增 pyc=0）；但 9 个只读域内存在 8 个**历史** `.pyc`（最早 12:47、最晚 20:16:53，含复核方指出的 2 件），其产生归因于上游会话导入，本任务**无权删除、未删除**；`git status --short` 的 `??` 在目录粒度检测不到这类新增文件 ⇒ 该表述在目录粒度**未验**。
9. **不能代 Leader 改台账/交付件**：两账与 `REFSYNC_SCOPE_FIX.md` 绝对只读；所有加注/重跑均为建议，未执行、未验证执行结果。
10. **题给 `ranCommands`（分诊 14 / 复核 41）无日志**，本会话**未验**条数；`partial` 的两处破口按题给【复核】原文登记，本会话对 (a) 复现了 pyc mtime、对 (b) 独立复跑了两件 carrier/selfgate 候选，未重新执行复核方的 41 条命令全集。
11. **本会话未对 173 件全量重跑 `kd.analyse()`**：全量结论引用 `_dt_repro.py` / `_dtv_verify.py` 的上游实跑输出；本会话独立重跑范围为 3 fixture + 2 候选 + 指纹/计数/表格/绑定行的只读校验（`_dtx_check.py` / `_dtx_check_out.json`）。

---

**本写域本会话新增件**：`DETECT_TRIAGE.md`（本件）、`_dtx_check.py`、`_dtx_check_out.json`。既有 `_dt_*` / `_dtv_*` 件一律只读引用，未改、未追加、未覆盖。未 commit、未 push；`git rev-parse HEAD` = `26574589aa8401e8f3f2934680a1ea7109bafa2d`（与本会话开始时相同）。
