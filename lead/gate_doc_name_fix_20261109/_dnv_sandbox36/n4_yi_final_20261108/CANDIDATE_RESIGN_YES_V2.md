# 候选重签结论书 · V2（语义层 YES）— qc151_trip.candidate_lf.py

- 日期：2026-11-08　撰写：重签结论撰写员（独立第三角色，未复用审阅员/复核员任何脚本）
- 被核对象：`lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`（`ca23c116…`/412,759 B）
- 依据链：乙 V2 任务书五项必查（`lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md`，`c7bcf035…`/28,897 B）→ 审阅回件（`_cs_semantic_review_GLM_20261108.md`，`ee27b4ca…`/11,948 B）→ 复核回件（verdict=**confirmed**，内容以编排方转交回件为准）→ 本文撰写员本轮独立取证。
- 撰写员本轮取证脚本（均为本轮新写，落唯一写域）：`_rw_fpcheck_20261108.py`（16 件指纹实算，输出 `TOTAL MATCH 16/16`）、`_rw_struct_20261108.py`（矩阵解析＋V2/B2B/裁决/R3 关键行实读＋unified-diff 回放＋difflib 重算＋AST 静态提取＋n/a 扫描＋关键词计数）。候选全程 **未 import、未执行**（仅 `ast.parse` 文本）；零真机、零采样代码；未 commit、未 push。

---

## 1 目的与边界

**目的**：按乙 V2 任务书（`_n4v2_B_EXECUTION_SPEC_V2.md`）五项必查，对候选 `qc151_trip.candidate_lf.py` 做**重签**，如实记录矩阵十四行**逐行**比对与九 hunk **逐 hunk** 比对结果，并给出签署判定。判定性质**仅限「候选语义层 YES」**——即候选静态语义满足 V2 五项必查；不断言运行时行为。

**边界（本件不做、不断言）**：
1. **不签 `APPROVE_SCOPE`**——该签署属来源会话签发人（N-4 原文 `NEXT_STEPS_20261106.md:49` 验收条款：「独立审阅者签候选 YES、来源会话签发人签 APPROVE_SCOPE」，本轮实读）。
2. **不应用母本**——母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py`（`517889c6…`/399,508 B）本轮零改动。
3. **不放行 N-5**——N-5 需有权来源会话派发新任务书（N-4 原文 :53-58，本轮实读）。
4. 零真机：未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / ctypes 动态解析新写）。
5. 受保护件（母本/候选/乙设计/乙矩阵/V2 正文/N-4 旧草案/补登件/裁决书/台账）零修改、零追加、零覆盖；唯一写域 = `lead/n4_yi_final_20261108/`。
6. 运行时行为、整趟行为、T1/T2/T5 **未验**（静态语义层判定；详见 §5/§6）。

---

## 2 版本绑定（十二件基线指纹，撰写员本轮逐件实算）

实跑命令：`python -I -X utf8 "D:\Project\ra2-campaign-forge\lead\n4_yi_final_20261108\_rw_fpcheck_20261108.py"`（hashlib 逐件读字节），输出 **`TOTAL MATCH 16/16`**（12 件基线 + 4 件追加绑定，下表）。

| # | 路径 | SHA256 | 字节数 | 实算 |
|--:|:--|:--|--:|:--|
| 1 | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py`（母本） | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399,508 | 一致 |
| 2 | `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`（候选·被核对象） | `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2` | 412,759 | 一致 |
| 3 | `lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff` | `72b108021637cf7d225a9b109a542ec10c934abb1a8e40b8850a82c6bea9cdb9` | 18,454 | 一致 |
| 4 | `lead/b2b_design_20261106/B2B_DESIGN.md` | `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf` | 66,735 | 一致 |
| 5 | `lead/b2b_design_20261106/STATE_MATRIX.json`（乙矩阵） | `1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016` | 3,558 | 一致 |
| 6 | `lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md`（V2 正文） | `c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801` | 28,897 | 一致 |
| 7 | `lead/n4_yi_final_20261108/B_EXECUTION_SPEC_V2_YI.md` | `27f31bf560e9a71c5e9603d81a860233e7fc7b19e504eed4a15ea24a2077b067` | 35,486 | 一致 |
| 8 | `lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md` | `255356ca789955cc2c084388f547a1435feb310f210617b988f761e7ff331c7b` | 7,344 | 一致 |
| 9 | `lead/direction_ruling_20261108/RULING_DIRECTION.md` | `0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653` | 16,514 | 一致 |
| 10 | `lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md` | `96071dd9d58e30a54966a2a1e16f4af918c2f8dd5825363510e8ced8bc6a8fea` | 24,661 | 一致 |
| 11 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52,419 | 一致 |
| 12 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759,518 | 一致 |

追加绑定件（同轮实算）：

| 路径 | SHA256 | 字节数 | 用途 |
|:--|:--|--:|:--|
| `lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md`（审阅回件） | `ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e` | 11,948 | 复核被核对象（§5 绑定） |
| `lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md`（N-4 原文） | `c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c` | 27,225 | V2 §2.1 绑定一致性 |
| `lead/n4_yi_final_20261108/_n4v2_ast_rerun_out.txt` | `9986fc2e335afa0748bfd9164c58c3eb04127c2f3db27b4e9fd91d5ee3cafdb6` | 22,510 | 五项必查第 5 项证据 |
| `lead/bexec_n4_20261108/_n4_ast_scan_out.txt` | `9986fc2e335afa0748bfd9164c58c3eb04127c2f3db27b4e9fd91d5ee3cafdb6` | 22,510 | 与上件**逐字节相等**（同指纹） |

**口径登记（复核回件非阻断项 (a)，撰写员本轮独立核实）**：审阅回件 §0 分组行（回件:16）点名 7 件并记「11/11 与编排方指纹一致」，且台账第二件 `GOAL_THREE_TARGETS_20261018.md` 未入其指纹表；编排方基线实为 **12 键**，12−1=11 与该计数吻合（分组行内「补登件」实体映射未验，按排除法最可能为 `YI_SUPERSEDE_JIA_BINDING.md`，此为撰写员推断、未经审阅员确认）。复核员 12/12、撰写员本轮 12/12 实算相符——**实体无缺，仅审阅回件记账口径偏差**，不影响任何实体绑定。

---

## 3 矩阵十四行逐行比对（三方：STATE_MATRIX.json ↔ V2 §4.2 ↔ 候选实码）

数据源（撰写员本轮实读/实算）：`STATE_MATRIX.json` 全文 16 行、**14 数据行 :2-15**（`json.loads` 得 14 条目，键=condition/confidence/preState/state/usableAsCrashEvidence/verdict）；V2 §4.2 表 :117-130；候选实码 `ast.parse` 提取 `_finish` 调用字面量（13 处，见 §4）。

| JSON 行 | 乙 verdict | 乙 confidence | V2 逐行收录 | 是否一致 | 候选实码出口 | 关键分支 |
|--:|:--|:--|:--|:--|:--|:--|
| :2 | unknown | none | 是（V2:117） | 一致 | :4649 | ★K3 空快照 |
| :3 | unknown | none | 是（V2:118） | 一致 | :4649 | ★K3 空快照 |
| :4 | error_pre_snapshot | none | 是（V2:119） | 一致 | :4653 | |
| :5 | post_read_error | none | 是（V2:120） | 一致 | :4644 | |
| :6 | new_first_appearance | high | 是（V2:121） | 一致 | :4667 | |
| :7 | **absent_both** | **low** | 是（V2:122） | 一致 | :4659 | ★K1 甲 n/a 废止点 |
| :8 | leftover_unchanged | high | 是（V2:123） | 一致 | :4691 | |
| :9 | leftover_unchanged | **medium** | 是（V2:124） | 一致 | :4687（:4685-4689 mtime 侧缺失分支） | ★K4 |
| :10 | new_write | high | 是（V2:125） | 一致 | :4682 | |
| :11 | rewritten_same_content | medium | 是（V2:126） | 一致 | :4697 | |
| :12 | rewritten_same_content | low | 是（V2:127） | 一致 | :4694 | |
| :13 | error_pre_snapshot（缺 pre.sha256） | none | 是（V2:128） | 一致 | :4674 | |
| :14 | post_read_error（缺 post.sha256） | none | 是（V2:129） | 一致 | :4679 | |
| :15 | **vanished** | **none** | 是（V2:130） | 一致 | :4662 | ★K2 甲 high 废止点 |

**统计**：完全一致 **14/14**；缺行 0；多行 0；取值不符 0。`usableAsCrashEvidence` 14 行全 `false`（JSON 原文逐行实读），与 `_finish` 硬编码 `False`（候选 :4628-4631 实读：`"usable_as_crash_evidence": False`）一致。

**四个关键分支标注**（三方逐点核实）：
- ★K1 `absent_both=low`：JSON:7（原文「…不能证无崩溃（E 口径另算）」）/ V2:122 / 码 :4659（AST：`verdict='absent_both' confidence='low'`）——**甲口径 `absent_both,n/a` 废止**（甲原文 N-4:47 本轮实读）。
- ★K2 `vanished=none`：JSON:15（「不给 high、不判本趟新出现、is_new=null」）/ V2:130 / 码 :4662——**甲口径 `vanished,high` 废止**。
- ★K3 空快照=`unknown/none`：JSON:2-3 / V2:117-118 / 码 :4649；归一口 :4634-4639 实读（`st = pre.get("state")`；`if st not in FRESHNESS_SNAPSHOT_STATES: st = "unknown"`）——**甲「空快照 {} 与显式 exists=False 等价」折叠废止**（N-4:47）。
- ★K4 `mtime_pre 缺失=leftover_unchanged/medium`：JSON:9（「A 旁证不可用…不虚报 high」）/ V2:124 / 码 :4687。

**值域**（候选实码实读）：`FRESHNESS_VERDICTS` 9 值（:223-226）、`FRESHNESS_CONFIDENCES` = high/medium/low/none **无 n/a**（:227）、`FRESHNESS_SNAPSHOT_STATES` 4 态（:228）——与 V2 §4.1:111 相符。

**码↔矩阵取值对互为充要**：13 处 `_finish` 调用归并出 11 个 `(verdict,confidence)` 对，与矩阵 14 行的 11 个对集合相等；撰写员实跑输出 `code-only pairs: []`、`matrix-only pairs: []`（多 0、缺 0）。

**保留登记（沿 R3:47 / V2:132，非候选缺陷，不阻断）**：JSON:2 行 condition「跑后任意文件状态」措辞过宽——码序 read_error 独立出口（:4643-4646）先于 unknown 出口（:4648-4650），`pre=None + post.read_error` 实际落 `post_read_error/none`；14 行 verdict/confidence 值本身不受影响（撰写员实读 :4643-4650 确认码序）。

---

## 4 九 hunk 逐 hunk 比对（CANDIDATE_LF.diff ↔ 母本 ↔ 候选）

方法（撰写员本轮自研，独立于审阅/复核脚本）：① 实读 `CANDIDATE_LF.diff` 的 9 个 `@@` 头（diff 行 :3/:25/:36/:169/:284/:294/:304/:314/:330）；② 自实现 unified-diff 回放：**patched==candidate 逐行相等**（patched=7,533 行，splitlines 口径；母本 7,291 行 + 净 242 = 7,533，两文件均以换行结尾；复核回件「7,534 行」为含尾行计数口径差，净值 +242 一致）；③ `difflib.SequenceMatcher`（autojunk=False）全量重算：**变更块 12、deleted=13、added=255、net=+242**，12 块逐一归入九 hunk 母本区间，**范围外块=0**；④ 各 hunk 上下文/增删行数与头部声明自洽 **9/9**。

| Hunk | hunk 头（diff 行） | 母本锚点（V2§3.1=B2B§7） | 候选实际落点（撰写员 difflib/实读） | 在范围内 |
|:--|:--|:--|:--|:--|
| H01 | `-212,6 +212,21`（diff:3） | :214 后插入 F 命名空间 5 常量 | cand :217-229（+15）；5 常量 :221-228（实读） | ✓ |
| H02 | `-4458,6 +4473,10`（diff:25） | :4460 后追加 mtime_pre 留痕 | cand :4476-4479（+4，其中 :4479 空行）；`bak[name]` 三键 :4475/:4480 原样（实读） | ✓ |
| H03 | `-4558,8 +4577,131`（diff:36） | :4561 前插入两函数＋:4561-4562 签名 | cand :4580-4700（+121，`make_pre_freshness_snapshot` :4580 起）＋签名替换 mother[4562]→cand[4702-4704]（-1+3） | ✓ |
| H04 | `-4572,20 +4714,105`（diff:169） | :4574-4599 函数体重写 | cand :4717-4791（-8+75）、:4795-4812（-1+18）、:4815（+1） | ✓ |
| H05 | `-5906,7 +6133,8`（diff:284） | :5909 finalize_trip 签名 | cand :6136-6137（-1+2，新签名止于 :6137） | ✓ |
| H06 | `-5936,7 +6164,8`（diff:294） | :5939 唯一调用点关键字传参 | cand :6167-6168（-1+2，实读：`copy_post_except_evidence(…, pre_freshness_snapshot=…)`） | ✓ |
| H07 | `-6294,6 +6523,9`（diff:304） | :6296 后、try 前预初始化 | cand :6526-6528（+3） | ✓ |
| H08 | `-6386,6 +6618,15`（diff:314） | :6388 后构造快照＋captured_at_iso_pre | cand :6621-6629（+9） | ✓ |
| H09 | `-7122,7 +7363,8`（diff:330） | :7125 后传给 finalize_trip | cand :7366-7367（-1+2，实读：`pre_freshness_snapshot=_pre_freshness_snapshot`） | ✓ |

**统计**：落在范围内 **9/9**；越界 hunk 0；缺失 hunk 0。九 hunk 头与 V2 §3.1（:81-89）及 B2B §7（:662-670）逐字一致（三方本轮实读）。实测 **+255/−13** 与 R3:43、V2 §3.2-4、V2 §3.1:93 授权链转述一致。**九 hunk −侧覆盖区间均不含 E 判据块 5984-5990**（撰写员实算：E 块落入任一 hunk −侧区间 = False；V2:91 引 `B2B_DESIGN.md:635` 同向）。

**候选实码与乙矩阵一致性（hunk 视角）**：
- H03 插入的 `classify_except_freshness` 内 13 处 `_finish` 出口（def :4628 一处；调用 :4644/:4649/:4653/:4659/:4662/:4667/:4674/:4679/:4682/:4687/:4691/:4694/:4697）逐处 `(verdict,confidence)` 与 §3 表末列一致，11 对与矩阵互为充要。
- H06：`copy_post_except_evidence` 调用点全文件**恰 1 处**（AST 实证 @:6167）且带 `pre_freshness_snapshot` 关键字（实读 :6167-6168）。
- H09：`finalize_trip` 调用点全文件**恰 1 处**（AST 实证，Call 起始 :7358；:7366-7367 追加 `pre_freshness_snapshot` 实参，实读）。

**登记（不阻断，文档精度事项）**：V2 §3.1:91「删除行数 0」与实测 −13 存在歧义——实测九 hunk 内删除 13 行（H03 签名位 1、H04 内 8+1、H05/H06/H09 各 1，合计 13，撰写员 difflib 实算），范围外删除 0；V2 §3.2-4 自记「+255/-13」。按「范围外删除=0」读则自洽，按字面「九 hunk 内删除=0」读则与 §3.2-4 冲突。属定版件措辞精度事项，非候选缺陷（审阅回件 §2 登记同项；复核回件未列为阻断）。

---

## 5 复核回件与五项必查逐一结论

**被核对象（审阅回件 `lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md`）SHA256 = `ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e`，字节数 = 11948**——复核回件绑定值，撰写员本轮 hashlib 实算相符（`_rw_fpcheck` MATCH 行）。

**复核 verdict = confirmed**（非 refuted / partial，故记 confirmed，不标 unconfirmed）。复核方法：全部为复核员自写 `_cv_*.py`（写域内现存 5 件：`_cv_hashes/_cv_diff/_cv_ast/_cv_matrix/_cv_na`，撰写员未复用），`python -I -X utf8` + 绝对路径，ranCommands=12；决定性证据 = 自实现 unified-diff 回放 patched==candidate 逐行相等＋difflib 12 块 +255/−13 全落九区间＋AST 13 调用 11 对互为充要＋严格 n/a 全文扫描恰 1 处母本固有 TERM 行。复核回件正文未单独落盘（写域内仅见上述 5 个脚本），其内容以编排方转交回件为准——**落盘件未验**。

**复核登记三处非阻断项（撰写员逐一独立核实）**：
- **(a) 口径**：审阅回件自称「编排方 11 件基线指纹全部实算相符」，回件 §0 分组行（回件:16）仅点名 7 件、台账第二件 `GOAL_THREE_TARGETS_20261018.md` 未入其指纹表（撰写员实读回件 §0 证实）；编排方基线 12 键经复核员 12/12 与撰写员本轮 12/12 实算相符——实体无缺，仅回件记账口径偏差。
- **(b) 行号脱漏**：审阅回件 :67（§3 散文）列 12 个 `_finish` 调用行号却写「调用 13 处」——:4667 在该列表脱漏（撰写员实读证实）；但其 §1 表（回件:30，JSON:6 行）与 V2:132 均含 :4667；复核员 AST 实证 13 处成立，撰写员本轮 AST 独立实证 13 处（含 :4667）。
- **(c) 静态边界**：运行时行为/整趟行为/T1/T2/T5 未跑为审阅回件已如实登记的边界（回件:83-84），零真机约束下的固有未验项。
- **翻案条款（复核回件原文）**：若上述任一实体件（母本/候选/矩阵/V2/台账）指纹漂移、或矩阵↔V2↔实码三方出现取值分叉、或回件出现「可应用/放行 N-5」断言，本 confirmed 即翻。

**五项必查项逐一结论**：

| # | 必查项 | 审阅结论 | 复核结论 | 撰写员本轮独立取证 |
|--:|:--|:--|:--|:--|
| 1 | 矩阵↔V2↔实码三方一致（十四行） | 14/14 全一致，四关键分支 OK | confirmed（11 对互为充要） | 14/14：矩阵 14 条目解析＋V2:117-130 实读＋AST 13 调用；`code-only=[]`、`matrix-only=[]`；usable 全 False |
| 2 | 九 hunk 范围 | 9/9 在范围内，越界 0 | confirmed（回放相等） | 9/9：9 个 @@ 头实读、回放 patched==candidate 逐行相等、12 块范围外=0、E 块 5984-5990 不含于 −侧 |
| 3 | `_finish` 调用点 | 13 处（回件:67 散文脱漏 :4667，登记见 (b)） | 13 处成立（AST） | 13 处：AST 提取 def @:4628＋调用 :4644/:4649/:4653/:4659/:4662/**:4667**/:4674/:4679/:4682/:4687/:4691/:4694/:4697；R3:43 点名 6 处逐一属实（:4659 absent_both/low、:4662 vanished/none、:4687 leftover/medium、:4691 leftover/high、:4694 rewritten/low、:4697 rewritten/medium） |
| 4 | **甲不再绑定** | 甲残留 0（A–D 不再绑定＋5 条理由，V2 §3.2:95-103 实读） | confirmed（严格 n/a 扫描恰 1 处母本固有 TERM 行） | ① V2 §3.2:95-103 实读：甲（`B2_FIX_DESIGN.md` 的 A—D 四处改动）自本件起不再绑定，5 条理由在文；② N-4:47 甲口径（`absent_both,n/a`、`vanished,high`、空快照折叠）本轮实读，候选实码 :4659 `absent_both/low`、:4662 `vanished/none`、:4648-4649 空快照独立——甲值零残留；③ 全文 `b2_fix_design` 0 命中（撰写员计数）；④ `n/a` 大小写不敏感全文恰 1 处（cand:7320 `rec.add("TERM","termination_verdict","N/A",…)` 与 mother:7079 **逐字相同**，撰写员实读比对 identical），非 FRESHNESS 置信域；⑤ `FRESHNESS_CONFIDENCES` :227 四值无 n/a |
| 5 | 禁止边增量 | 十一禁止符号 UNCHANGED、新增禁止边=0（rerun 实读＋自实现 AST 扫描） | confirmed（自实现扫描 new=10/gone=0） | ① `_n4v2_ast_rerun_out.txt` ≡ `_n4_ast_scan_out.txt` 逐字节同指纹（9986fc2e…/22,510，hashlib 实算）；② rerun out 实读：:612-618 存量 6 包装函数、:623-633 十一符号 UNCHANGED、**:635「候选新增禁止边符号: 无」**、:639 subprocess.Popen 1→1、:641-668 ctypes/getattr/importlib 逐类一致、:670-671 import 集合一致、**:673 新增边 10 种/消失边 0（基线 536/候选 546）**、:675-684 十条新增边（_finish×13、classify×3、make_pre×1、_emit_f×3、pre.get×4、post.get×4、post_observed.get×2、post_observed.update×1、out.update×1、src.stat×2）全落 H03/H04 新鲜性逻辑与错误出口；③ 撰写员独立计数（不区分大小写子串）：gamemd 32/32、ra2loader 16/16、taskkill 2/2、yuri 1/1、os.system 0/0、subprocess.popen 16/16、ctypes 199/199 **双方相等**，import 集合相等（与复核回件「双方相等」同向；其 21/14/2 计数口径未复算） |

**未验登记（如实，不补造）**：T1/T2/T5 本轮未跑（审阅回件:83；T5 同类核验以 AST 静态提取替代 R3 fixture 实跑，方法不同、结论同向）；母本既有 6 包装函数运行时行为未验（rerun out :612-618 仅静态计数）；运行时整趟行为未验（零真机）；RULING_D24/D25 原文未逐行复读（审阅登记，撰写员同）；补登件实体定位未验（`find` 无 `*补登*` 命名命中；审阅回件 §0「补登件」之实体映射按排除法推断为 `YI_SUPERSEDE_JIA_BINDING.md`，未经确认）；复核回件正文落盘件未验。

---

## 6 结论

**resign 判定：YES——仅限「候选语义层」**。依据：五项必查全部通过——矩阵三方一致 **14/14**（逐行见 §3）、九 hunk 在范围内 **9/9**（逐 hunk 见 §4）、`_finish` 调用 **13/13**（含 :4667）、**甲不再绑定**（甲残留 0，§5 必查 4）、禁止边增量 **0**（§5 必查 5）；复核 verdict=**confirmed**；撰写员本轮以自研脚本独立取证同向（指纹 16/16、回放相等、12 块范围外 0、11 对互为充要）。执行者≠核验者链完整：R3（实现对照）→ 审阅（GLM，新写脚本）→ 复核（自写 `_cv_*`）→ 本文（自写 `_rw_*`）。

**性质限定（越权断言排除声明）**：本 YES **不签 `APPROVE_SCOPE`**（属来源会话签发人）；**不应用母本**（母本指纹 517889c6…/399,508 本轮零改动）；**不放行 N-5**；不断言运行时行为、整趟行为或崩溃修复效果；不签真机验收。`RULING_DIRECTION.md:23` 本轮实读：Q1「采用乙、禁止混用甲预期」仅为**待有权签发人确认的方向意见**，不宣告 N-4 正式绑定已生效，且「本次不补登、不签署、不应用」（:25）——本文同此限定。未 commit、未 push；除本文与 `_rw_fpcheck_20261108.py`、`_rw_struct_20261108.py` 两个取证脚本外未写任何文件，全部在唯一写域 `lead/n4_yi_final_20261108/` 内。

**附条件全文（本 YES 成立条件，任一破坏即失效，本文与复核 confirmed 一并作废）**：
1. **指纹稳定**：母本/候选/乙矩阵/V2/台账（§2 表 12 件，另含 CANDIDATE_LF.diff）保持 §2 绑定值，任一漂移即失效；
2. **三方不分叉**：STATE_MATRIX.json ↔ V2 §4.2 ↔ 候选实码的 `(verdict,confidence)` 取值无任何分叉；
3. **无越权断言**：审阅/复核回件不出现「可应用母本 / 放行 N-5 / APPROVE_SCOPE 已签」类断言；
4. **甲不再绑定保持**：甲 A—D 不复活为验收基准，候选内无 n/a 置信、无 `B2_FIX_DESIGN` 引用；
5. **范围不变**：候选 = 母本 + 且仅 + H01–H09（+255/−13），出现任何额外变更块即失效。

**仍未完成的生效条件清单（本 YES 之后仍欠，逐项未验）**：
1. 来源会话签发人签发 `APPROVE_SCOPE`（N-4 原文 :49 验收条款；本文不代签）；
2. 有权签发人对甲/乙方向作出正式确认并补登（`RULING_DIRECTION.md:23/:25`：四项决断留白待签发人）；
3. N-5 放行：须有权来源会话派发新任务书后方可执行（N-4 原文 :53-58 实读）；
4. T1/T2/T5 核验未跑（审阅回件:83 登记）；
5. 运行时整趟行为验证未做（零真机约束，须另行授权真机趟）；
6. 母本既有 6 包装函数的运行时行为未验（仅静态计数，rerun out :612-618）；
7. RULING_D24/D25 原文未逐行复读；
8. 补登件实体定位与 §4/§5 原文复读未做；
9. V2 §3.1:91「删除行数 0」措辞修订待定版件处理（非阻断，§4 登记）。

**非阻断登记汇总**：审阅回件口径偏差 (a)（11 vs 12 键）、:4667 散文脱漏 (b)、静态边界 (c)、V2:91「删除行数 0」措辞歧义、JSON:2 行 condition 措辞过宽（沿 R3:47/V2:132）——五项均不阻断本重签，均已原样上账。

---
*本文由重签结论撰写员于 2026-11-08 撰写；全部断言可追至本轮实跑命令输出或「文件:行」实读；拿不到者已记「未验」。签署性质仅限「候选语义层 YES」。*
