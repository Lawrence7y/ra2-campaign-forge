# V1/V2 全量影响面评估（影子模式，只读）

写域：`lead/v12_impact_20261109/`。产出前缀 `_vi_`。零真机、零采样、未插任何真门禁、未改任何既有件、未 commit/push。
Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。

## 0. 复核回件绑定行（被核对象 = 分类器本体）

被核对象 SHA256 = 15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0，字节数 = 9148
（`lead/gate_v1v2_20261109/_v12_rule.py`，本会话 `python -I -X utf8 -c "…hashlib…"` 实算，与编排方基线一致）

编排方 9 件指纹逐件实算，9/9 全相符（`_vi_shadow.py` 头部复算 3 件 + 首条命令复算 9 件）：
`_v12_rule.py` 15e421…/9148、`_v12_REPORT.md` 10a908…/30098、`_v12_regression.json` 994e36…/10484、
`_n13_predicates.py` e1195b…/16649、`_g7_predicates.py` 02c17e…/11743、`_g9_gate.py` a83081…/11623、
`_dn_regate_out.json` 0d129e…/22133、`PENDING_DECISIONS.md` 3765ed…/52419、
`GOAL_THREE_TARGETS_20261018.md` 2baa0d…/759518。
两台账本次会话结束时复算仍为同值（`git diff --stat` 显示的 `MM` 是会话开始时既有状态，非本任务写入）。

## 1. 实跑清单（本会话内真跑）

| # | 命令 | 输出件 | 结论 |
|---|---|---|---|
| C1 | `python -I -X utf8 -c "…hashlib 9 件…"`（cwd=仓库根） | stdout | 9/9 指纹匹配编排方基线 |
| C2 | `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/v12_impact_20261109/_vi_shadow.py"` | `_vi_shadow_out.json` / `.txt` | 32 域全量影子重跑 |
| C3 | `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/v12_impact_20261109/_vi_probe.py"`（v3） | `_vi_probe_out.json` / `.txt` | 库内既有语料 S3/回退探针 |
| C4 | `git status --porcelain` + `git diff --stat` + 复算两台账 | stdout | 只读域未被本任务写入 |

C2 实跑输出（逐字）：
```
domains_total=32 nonempty_banned=30 empty_banned=2
domains_with_hits=7  total_hits=26  r10_problems_total=8
RAW==R10 all identical = True ; baseline FP all match = True
R10 kinds  = {"assertion": 8, "negation": 17, "quote_mention": 1}
V12 verdict= {"V1": 26}
quadrants  = {"assertion_V2": 0, "assertion_V1": 8, "negquote_V2": 0,
             "negquote_V1": 18, "s3_default": 0, "co_hard_override": 2, "co_hard_weak": 9}
hard marks = {"H2_引述占位": 16, "H4_完成词做定语": 1, "H1_疑问式": 2,
             "H3_表格状态列": 4, "H6_条件选言分支": 4, "H5_否定禁止管辖": 8}
```
C3 实跑输出（逐字）：
```
N13_DEFAULT_TOKENS=['已入账','已追加','已生效'] ASSERT_TOKENS=['已生效','可应用母本','放行 N-5','已入账','已追加']
库内语料单元=50 有命中单元=45 字面命中=47
V12 verdict: V1=10 V2=37 ; 归因 S0=10 S1=20 S2=0 S3=34
逐处：S3且应PASS=3 ; V1且应CATCH(回退)=2 ; V2且应PASS(新增误报)=9 ; V2且应CATCH=28
单元级：判对=34/45 单元FP=9 单元FN=2
32 域现盘：S3=0 hard∧override=2 hard∧weak=9
```

**口径来源（都是库内既有件，非本任务构造）**：32 域清单 / main / banned 词表取自
`lead/gate_rejudge32_20261109/_rj_delivery_baseline.json`（`domains=32 rows=32`，C2 头部复算其 sha256=0d129e…/22133，
与编排方 `_dn_regate_out.json` 指纹同值）；R10 谓词 `lead/gate_fp7_20261108/_g7_predicates.py:113-130`；
V12 谓词 `lead/gate_v1v2_20261109/_v12_rule.py:108-170`；C3 语料 `lead/gate_n13_20261109/_n13_regression.py:46-113`
（26 NEG + 16 POS 逐字）、`_n13_predicates.py:25` DEFAULT_TOKENS、`_g7_reverse_validate.py:26` ASSERT_TOKENS、
TV2/TV3 两份真违规样件逐行读盘。C3 用 `ast.literal_eval` 静态取词表常量，不执行被读模块。

**探针版本修正（如实登记，不隐去）**：`_vi_probe.py` v1 误用自造词表 `T=["已入账","可应用母本","放行 N-5"]`，
得 S3=20 / 回退=2 / 新误报=6；v2 改用权威词表但 import 了无 `__main__` guard 的回归脚本，其 `main()` 连带实跑污染 stdout；
v3 最终版用 AST 取词表、零副作用，输出即上表。**本报告只采 v3 数字。**

## 2. 第一步：两域基线复核

### (a) c07_slot 6 处 / c07_truth_protocol 3 处，逐处 verdict + 标记

`_vi_shadow_out.txt:16-65` 逐处实跑。9 处 **全部 V1**，全部由 S0 HARD_V1 判定，`weak=[]`、`override=""`、`review_flag=False`：

| 域 | 行 | tok | R10 kind | V12 | hard | weak | override | review |
|---|---|---|---|---|---|---|---|---|
| c07_slot | 79 | 已填 | assertion | V1 | H2_引述占位, H4_完成词做定语 | [] | "" | False |
| c07_slot | 103 | 已填 | assertion | V1 | H2_引述占位 | [] | "" | False |
| c07_slot | 110 | 已填 | assertion | V1 | H1_疑问式 | [] | "" | False |
| c07_slot | 112 | 已填 | assertion | V1 | H1_疑问式, H3_表格状态列 | [] | "" | False |
| c07_slot | 120a | 已填 | assertion | V1 | H2_引述占位, H3_表格状态列 | [] | "" | False |
| c07_slot | 120b | 已填 | negation | V1 | H2_引述占位, H3_表格状态列 | [] | "" | False |
| c07_truth | 151 | 已填 | assertion | V1 | H6_条件选言分支 | [] | "" | False |
| c07_truth | 228 | 已填 | assertion | V1 | H6_条件选言分支 | [] | "" | False |
| c07_truth | 240 | 已填 | negation | V1 | H3_表格状态列, H6_条件选言分支 | [] | "" | False |

与编排方 `_v12_regression.json:24-221` 逐处一致；与编排方 32 域实跑的 9 处 `v12:"V1"` 一致。
独立 R10 复算：c07_slot `problems=5 warnings=1 occurrences=6`、c07_truth `problems=2 warnings=1 occurrences=3`
（`_v12v_r10_out.txt:7,42` 既有实跑；本会话 C2 复现 `R10_problems=5/2`）。C2 另用独立 `re.finditer`
复算 raw 命中集，32 域 `RAW==R10 all identical=True`，无重叠 token 假象。

### (b) 多个标记同时命中？★ 有，且分类器**没有如实回报**

`classify_v12` 的 docstring（`_v12_rule.py:23-27`）明写「两者同时出现时 hard/override 双标记一并回报供人工审计」，
但实现是 S0 命中即 `return`（`:143-146`），`hard` 分支强制 `weak=[]`、`override=""`——**同触标记被丢弃，审计链断裂**。
故本会话在 `_vi_shadow.py:co_trigger()` 外部独立复算同一分析单元 U 内的 S1/S2 标记（用模块自身的
`V2_OVERRIDE` / `V2_OVERRIDE_RE` / `W1_RE` / `W1_NUM_RE` / `_strip_quotes` / `_unit_and_line`），结果：

- **9 域现盘 26 命中中 2 处 hard∧override 同触**（`_vi_shadow_out.txt:182,187`）：
  `lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md:155` 的 `可应用母本`(pos=14127) 与 `放行 N-5`(pos=14135)。
  两者同一 U：`3. **无越权断言**：审阅/复核回件不出现「可应用母本 / 放行 N-5 / APPROVE_SCOPE 已签」类断言；`
  U 内含 `V2_OVERRIDE` 关键词 `已签`；`override_would_fire=True`（无紧邻否定、U_bare 无 PROHIBIT）。
  **取了哪个**：S0 `H2_引述占位` → V1；**被压掉的是什么**：S1 `V2_OVERRIDE:已签` → 本应 V2。
  本会话判定：**此处取 V1 是对的**（`已签` 落在「…」引证跨度内、整句被「不出现…类断言」否定，是排除声明；
  `GATE_REJUDGE_32.md:111` 判该行 5 处命中全为误报）。但 `_v12_rule.py:112` 用 `U_bare=_strip_quotes(U)`
  只剥引文做否定管辖判定，`:149` 的 `hit_override=[k for k in V2_OVERRIDE if k in U]` 却用**未剥引文的 U**
  查 override —— 若不是 S0 先命中，这个引证跨度内的 `已签` 会把该句误判成 V2。这是**实现与自身设计不一致的隐患**。
- **9 处 hard∧weak 同触**（`_vi_probe_out.json` summary `domains_32_hard_and_weak_total=9`）：同样因 S0 提前 return，
  `weak` 字段恒空；取 S0（HARD_V1）压过 S2（WEAK_V1），两者 verdict 同为 V1，结论不受影响，但可追溯性同样缺失。
- 两域基线 9 处本身：`hard_AND_override=0`（`_v12_gate_compare_out.txt:10-18` 既有实跑「U内V2_OVERRIDE=[]」，
  本会话 C2 复核一致），`hard_AND_weak=1`（c07_slot:103，编号清单 `W1_NUM_RE` 同触，取 H2）。

## 3. 第二步：全量影子对比（独立重跑 C2，与编排方实跑对账）

### (a) 域数 / 命中数，逐域

32 域全扫（编排方 32 域影子数据只列 30 行，缺的 2 域正是 `banned=[]` 的
`c07_protocol_attacks_20261109`、`gate_fp7_20261108`——C2 把它们如实补入并给 RAW=0/hits=0）。
**30 域有非空 banned 词表，7 域有字面命中，共 26 处**（与编排方 `totalHits:26` 一致；
编排方 `domainsWithHits:30` 实际是「扫描域数」而非「有命中域数」，本会话实测有命中域=7，逐处可核）。

| 域 | banned 词数 | RAW=R10 命中 | R10 assertion | V12 V1 | V12 V2 | S3 |
|---|---|---|---|---|---|---|
| c07_gate_audit_20261109 | 3 | 0 | 0 | 0 | 0 | 0 |
| c07_gate_fix_20261109 | 3 | 0 | 0 | 0 | 0 | 0 |
| c07_protocol_attacks_20261109 | 0 | 0 | 0 | 0 | 0 | 0 |
| **c07_slot_20261109** | 4 | **6** | 5 | 6 | 0 | 0 |
| **c07_truth_protocol_20261109** | 3 | **3** | 2 | 3 | 0 | 0 |
| counterpart_fix_20261109 | 4 | 0 | 0 | 0 | 0 | 0 |
| f2d_rootcause_20261109 | 3 | 0 | 0 | 0 | 0 | 0 |
| gate_fp7_20261108 | 0 | 0 | 0 | 0 | 0 | 0 |
| gate_postmortem_20261109 | 3 | 0 | 0 | 0 | 0 | 0 |
| gate_r9r12_20261109 | 3 | 0 | 0 | 0 | 0 | 0 |
| handoff_pack_20261109 | 4 | 0 | 0 | 0 | 0 | 0 |
| **ledger_appendix_20261108** | 3 | **3** | 0 | 3 | 0 | 0 |
| **matrix_ab_ruling_20261109** | 4 | **3** | 0 | 3 | 0 | 0 |
| matrix_reach_20261109 | 4 | 0 | 0 | 0 | 0 | 0 |
| matrix_row5_20261109 | 4 | 0 | 0 | 0 | 0 | 0 |
| **n10c04_ruling_20261108** | 5 | **5** | 0 | 5 | 0 | 0 |
| n11_dimmap_20261108 | 4 | 0 | 0 | 0 | 0 | 0 |
| n11_wording_fix_20261108 | 3 | 0 | 0 | 0 | 0 | 0 |
| **n4_yi_final_20261108** | 4 | **5** | 0 | 5 | 0 | 0 |
| o1prime_reach_20261109 | 4 | 0 | 0 | 0 | 0 | 0 |
| pending_factpack_20261108 | 5 | 0 | 0 | 0 | 0 | 0 |
| r11_f2_fix_20261109 | 4 | 0 | 0 | 0 | 0 | 0 |
| s604_attribution_20261108 | 5 | 0 | 0 | 0 | 0 | 0 |
| s604_exclusive_20261109 | 3 | 0 | 0 | 0 | 0 | 0 |
| s604_script_gap_20261109 | 4 | 0 | 0 | 0 | 0 | 0 |
| **s604_script_hunt_20261109** | 3 | **1** | 1 | 1 | 0 | 0 |
| samedoc_link_20261109 | 3 | 0 | 0 | 0 | 0 | 0 |
| strict_exposure_20261109 | 4 | 0 | 0 | 0 | 0 | 0 |
| text_fix_unified_20261109 | 4 | 0 | 0 | 0 | 0 | 0 |
| u5u6_mirror_20261109 | 4 | 0 | 0 | 0 | 0 | 0 |
| v2_precision_fix_20261108 | 4 | 0 | 0 | 0 | 0 | 0 |
| w2_samecause_20261109 | 4 | 0 | 0 | 0 | 0 | 0 |
| **合计** | — | **26** | **8** | **26** | **0** | **0** |

逐域原句/行号/pos/U/标记见 `_vi_shadow_out.txt:7-231` 与 `_vi_shadow_out.json`。

### (b) 四象限（严格按任务给的四种组合，逐处清单在 `_vi_shadow_out.json:quadrant_items`）

| 组合 | 处数 | 逐处 |
|---|---|---|
| R10=assertion 且 V12=V2（两轨一致抓） | **0** | 无 |
| R10=assertion 且 V12=V1（V12 放过） | **8** | c07_slot:79,103,110,112,120a；c07_truth:151,228；s604_script_hunt:143 |
| R10=negation/quote 且 V12=V2（V12 判抓） | **0** | 无 |
| R10=negation/quote 且 V12=V1（两轨一致放过） | **18** | c07_slot:120b；c07_truth:240；ledger_appendix:146,177,194；matrix_ab_ruling:4×3；n10c04_ruling:5,44,348×2,425；n4_yi_final:17,130,150,155×2 |

R10 kind 全集：`assertion 8 / negation 17 / quote_mention 1`；V12 verdict 全集：`V1 26 / V2 0`。
即**在这 32 域现盘上，V12 相对 R10 只做一件事：把 8 处 assertion 全放过**，其余 18 处两轨一致放过。

### (c) ★ S3 DEFAULT 触发处数 = **0**（逐处清单：空集）

`_vi_shadow_out.json:summary.quadrants.s3_default=0`，`quadrant_items.s3_default=[]`；逐域 S3 列全 0。
原因不是「判不了没发生」，而是 **26 处全部先命中 S0 HARD_V1**（`_vi_probe_out.json`
`domains_32_stage_attribution` 逐域 `S0=hits`、`S1=0 S2=0 S3=0`），S0 提前 return 使 S3 根本不可达。
四类 hard 触发频次：H2 16、H5 8、H3 4、H6 4、H1 2、H4 1（合计 35 个标记，26 处，多处多标记）。

**但「0 次」不等于「风险为零」**：C3 拿库内既有语料形态实测，S3 是可达的、且触发频率很高：
50 个库内语料单元 / 47 处字面命中里，**S3 DEFAULT 触发 34 处**（`_vi_probe_out.txt:6-146` 逐处，
`review_flag=True`），占 72.3%；这 34 处中 3 处是「本应 PASS 的 S3 误拦」（详见第三步 c）。
所以任务里「对全库其它域可能是大量新误报」的担心**成立，但不是在这 32 域现盘上成立**——
现盘 26 处恰好全落在 HARD_V1 的形状里。

## 4. 第三步：逐处判谁对

### (a) 两轨不一致的命中 = 8 处（全是 assertion & V1），逐处判谁对

依据：`lead/gate_rejudge32_20261109/GATE_REJUDGE_32.md:91-99,116`（权威真伪重判，逐条标「误报」）、
`_rj_findings.md:55,57,71,79-80,97-98`（「8 条 R10 断言全是本轮实证的 R10 新误报」）+ 本会话读原句。
**8 处全部 V12 对、R10 错**（V12 放过的是误报，不是真断言）：

| 域:行 | 原句要点 | 权威裁决 | 判定 |
|---|---|---|---|
| c07_slot:79 | `<已填件路径>` 是命令行尖括号占位符（`C07_IDENTITY_SLOT.md:79`） | `GATE_REJUDGE_32.md:91` A 命令占位符 **误报** | V12（H2+H4）对 |
| c07_slot:103 | §5.2 人工自检清单第 1 条「三个身份字段已填…」是**验收条件**（`:101-103`） | `:92` E 自检清单条文 **误报**；同件 L114-119 逐行记「**未填**」 | V12（H2）对 |
| c07_slot:110 | `### 5.4 …（…是否已填）` 小节标题（`:110`） | `:93` B 小节标题 **误报**；任务书自相矛盾，删词即抹证据 | V12（H1）对 |
| c07_slot:112 | `| … | 是否已填 |` 表格列头（`:112`） | `:94` B 表格表头 **误报** | V12（H1+H3）对 |
| c07_slot:120a | 先例件状态引述 `reviewerSessionId 已填`（`:120`，明写「先例件，非 C07 落点」） | `:95` A 先例件引述 **误报 ×2** | V12（H2+H3）对 |
| c07_truth:151 | `- 处置：已填 → …；未填且… → …` 状态机两分支标签（`:151`） | `:97` E 条件分支标签 **误报**；`:6` 自证不含真实身份值（本会话已读 `:145-158`） | V12（H6）对 |
| c07_truth:228 | 可核项 G 清单格「见证槽已填（…）；…→**拒绝**」（`:228`） | `:98` E 可核项清单格 **误报** | V12（H6）对 |
| s604_script_hunt:143 | 「**不可能/未覆盖（如实申报）**：已删除文件的磁盘… carving **未做**」（`S604_SCRIPT_HUNT.md:143`） | `:116` A 检索对象/定语 **误报**；任务书 (b) 原文要求写「已删除文件的磁盘残块」 | V12（H5）对 |

注：V12 在部分处给出的**理由**并不精确（如 `:103` 靠 H2「引述占位」而非「清单条文」、`:143` 靠 H5「否定禁止管辖」
而非「完成词做定语」、`:112` 靠 H1+H3 而非纯表头），但**结论（放过）与权威重判一致**，本会话按结论判对，不美化理由。

### (b) ★ R10=assertion 且 V12=V1 的回退核查（重点）

**在 32 域现盘上：回退 = 0 处。** 8 处 R10 assertion 全被 `GATE_REJUDGE_32.md`/`_rj_findings.md` 判为
「R10 新误报」（`_rj_findings.md:98` 逐字：「前 2 域 + 末 1 域的 8 条 R10 断言全是本轮实证的 **R10 新误报**」），
即 R10 原本**判错**（误报），V12 放过是纠错，不是「原本判对、插入后放过」。

**但绝不能据此说分类器无回退风险。** C3 在库内既有语料上实测到 **2 处真回退**（单元级 FN=2，
`_vi_probe_out.txt:148,158`），都是 S0 H5「紧邻否定/禁止管辖」把真断言误当 V1：

1. `N13_NEG/N18`「本笔已入账 0 命中不得写成未入账」（`_n13_regression.py:103` 标注「真断言：检索标记与真断言同句，
   mixed 作废豁免」，expect=CATCH）：R10=`assertion`（抓，对）；V12=`V1`，`hard=['H5_否定禁止管辖']`（`:135-136`
   `prohibit_U` 在整个 U 里找 `PROHIBIT` 词，句尾「**不得**写成未入账」被当作管辖本句开头的完成词）→ **放过真断言**。
2. `R10_TV/TV3:L12`「审阅不得不承认本候选已生效。」（`_g7_tv3_double_negation.md:12`，双重否定=肯定，
   `_g7_reverse_validate.py:119` 要求 R12 拦下）：R10=`double_neg`（交 R12 抓，对）；
   V12=`V1`，`hard=['H5_否定禁止管辖']`（「不得不」命中 PROHIBIT「不得」）→ **放过真断言**。

这两处是「原本 R10 判对（真断言被抓）而插入 V1/V2 后放过」的**确凿回退**，按铁律如实登记，不因总体变好而隐去。
根因：`_v12_rule.py:42-43,116,135-136` 的 H5 用「U 内任意位置出现 PROHIBIT / 任意否定字符」做无条件 V1，
不区分否定/禁止是否**支配该命中 token**，且不含 R12 式双重否定识别。

### (c) ★ S3 DEFAULT 每一处：真断言 还是 被误拦的规定式？

32 域现盘 S3=0（无逐处可列）。C3 库内语料 34 处 S3 逐处清单见 `_vi_probe_out.txt`（`taken=S3 S3=True` 的行），
按 expect 分：**31 处本应 CATCH 的真断言**（N13 NEG 11 处 + TV2 4 处 + TV3:L8 1 处 + N13 NEG 里 S3 的其余），
**3 处本应 PASS 却被 fail-closed 误拦**：

1. `N13_POS/P09`「② RULING_DIRECTION.md 整体状态 **unconfirmed**…——**本节登记「以乙替代甲」是登记动作，
   **不宣告** N-4 正式绑定已生效**」（`_n13_regression.py:64-65`，C 否定式，expect=PASS）：
   R10=`negation`（豁免，对）；V12 走 S3 → `V2 + review_flag=True`。**被误拦的规定式/否定式**。
   对照 `N13_POS/P10` 同型句却因 H2 命中判 V1（`_vi_probe_out.txt:103-104`）——同一语义两种结论，
   说明 S3 误拦对行文格式极敏感。
2. `N13_POS/P15`「### 3 已追加 grep 结果（清单）」（`_n13_regression.py:77`，B 小节标题+清单，expect=PASS）：
   R10=`assertion`（此处 R10 反而判错）；V12 S3 → V2。**被误拦的检索标题/清单**。
3. `R10_TV/TV3:L10`「作为对照，上一轮回件不宣告 N-4 正式绑定已生效（单重否定，应豁免）。」
   （`_g7_tv3_double_negation.md:10` 原文括注逐字）：R10=`negation`（豁免，对）；V12 S3 → V2。
   **被误拦的单重否定控制行**。

其余 31 处 S3 命中按 `_n13_regression.py:85-113` 与 TV2/TV3 标注均为**真断言**，判 V2 抓对
（如 N02「已生效，可应用母本。」、N13「该笔已生效，可应用母本」、TV2:L6「本候选已生效。」），
fail-closed 在这里确实起了「宁可误拦」的作用。结论：**S3 在库内尺度上是「31 对 / 3 错」的混合体，
不是纯粹的安全网**。

### (d) 另实测量出的新增误报（S3 之外，更大量）

C3 单元级：45 个有命中单元中 **单元 FP=9**（应 PASS 却被 V12 抓），逐条 `_vi_probe_out.txt:149-157`：
`N13_POS/P02,P03,P04,P05,P07,P16`（6 处全是 `已入账 grep 结果 / 核查实跑命令 / 目录枚举` 等检索动作形态，
被 `_v12_rule.py:36` 的 `V2_OVERRIDE` 词族里的 **`已入账` 本身**命中 → S1 判 V2）；
`N13_POS/P09`、`N13_POS/P15`、`R10_TV/TV3:L10`（3 处 S3，见上）。
根因：`V2_OVERRIDE` 词表把禁用词 `已入账` 自己列为「硬性完成宣称」（`:36`），
于是任何含该词的**标题/目录/检索标签**都被无条件判 V2 —— 这正是「全库尺度噪声洪水」的具体形态。
相对 R10 的逐处差分（C3 另算）：`R10放_V12抓` 8 处、`R10抓_V12放` 7 处、
`R10抓_V12抓` 29 处、`R10放_V12放` 3 处。

## 5. 第四步：影响面汇总与风险评级

### (a) 插入 V12 后 32 域里几个域的门禁结论会变

分两条基准，如实都给（不混）：

**基准 A = R10 轨（任务第二步的对照轨）**：3 个域的「越权断言」结论变松（各消去 assertion 误报）：
`c07_slot_20261109`（-5）、`c07_truth_protocol_20261109`（-2）、`s604_script_hunt_20261109`（-1），
共消 8 处；其余 29 域 R10 本来 0 assertion，V12 也 0 V2，**不变**；**变紧的域 = 0**。
这三域也正是 `_rj_predicatized_sim_out.json:still_fail` 里因 R10 仍失败的三域——V12 影子叠加恰好把它们消掉，
而该文件另 4 域（`matrix_ab_ruling / matrix_reach / n11_wording_fix / s604_script_gap`）是 R9 缺要素问题，
**与越权断言面无关，V12 不改变它们的结论**（如实说明，不把四域算进收益）。

**基准 B = 交付门禁基线**（`_rj_delivery_baseline.json` 的 `gateProblems`，朴素字面匹配）：
7 个域原本报「含越界断言」（11 条按词去重的条目）：c07_slot / c07_truth_protocol / ledger_appendix /
matrix_ab_ruling(3) / n10c04_ruling(2) / n4_yi_final(2) / s604_script_hunt。
V12 在 26 处命中上全判 V1 → 这 7 域的越界断言结论**全部变松（11 条消去）**；变紧 = 0。
但这 7 域中 4 域（ledger_appendix / matrix_ab_ruling / n10c04_ruling / n4_yi_final）R10 本来已豁免，
V12 相对 R10 无增量——增量收益只在前述 3 域。

**两个基准都无任何域「变紧」**，因为 32 域现盘 V12_V2=0、S3=0。

### (b) 三个数字

| 指标 | 32 域现盘（对 R10 轨） | 库内既有语料 C3（对标注 expect，单元级） |
|---|---|---|
| 新增误报（原放过→插入后抓） | **0 处** | **9 单元**（逐处 V2 且应 PASS = 9；其中 S3 贡献 3） |
| 消除误报（原误报→插入后放过） | **8 处** | **0 单元**（应 PASS 且 V1 放过的 8 处单元，R10 轨多数已放过，不计「消除」） |
| 回退（原对→插入后错） | **0 处** | **2 单元**（N13_NEG/N18、TV3:L12；另逐处 7 处「R10抓→V12放」中 5 处是纠错、2 处是回退） |

任务要求的三个数字，**以 32 域现盘为准：新增误报 0、消除误报 8、回退 0**。
另如实给出 C3 的库内尺度数字：新增误报 9、消除误报 0（该语料 R10 轨本就基本判对）、回退 2。
两者不互相替代：前者是「这次插入在这 32 个已交付域上的实际影响」，后者是「同一分类器在库内其它已有形态上的风险」。

### (c) 风险评级与理由

**评级：high（对「全库直接插入」而言）；对「32 域现盘影子叠加」这一窄范围而言是净收益。**

- **净收益（窄范围）**：32 域现盘 8 处 R10 断言误报全消、0 新增误报、0 回退、0 S3 噪声，
  且这 8 处有 `GATE_REJUDGE_32.md:91-99,116` 与 `_rj_findings.md:98` 的权威真伪重判背书。仅就这 32 件、这批词表，插入是纯收益。
- **净损失（全库尺度）**：C3 在库内既有 45 个有命中单元上实测 34/45 判对、9 单元新增误报、2 单元回退；
  S3 fail-closed 触发 34/47 处（72.3%），其中 3 处是误拦；`V2_OVERRIDE` 把禁用词 `已入账` 自己列为宣称词，
  使 6 个纯检索/标题形态被误判 V2。若把同一分类器套到 N13 三词词表（另一套已交付门禁族）上，
  **噪声洪水 + 真断言漏放同时发生**。
- **两边都有 → 值得插入的条件**：① 只对**已验证的那批词表/域**启用（见第五步 a）；
  ② 先修掉 H5 管辖误判与 `V2_OVERRIDE` 自指词（否则 2 处回退与 6 处 FP 会带进新域）；
  ③ S3 不得无条件 fail-closed，须降级为「review_flag 交人工/或保留原 R10 结论」；
  ④ 建立逐处回归门槛（第五步 b）并先影子 N 轮（第五步 c）。四条缺一，全库插入即净损失。

### (d) S3 DEFAULT=fail-closed 在全库尺度是否合理

**判断：全库尺度上不合理，应改；在两 c07 域上「宁可误拦」的结论也不成立（因为那里 S3 根本没触发）。**

依据（都是本会话实跑）：
- 两域基线 9 处 S3=0（第一步），32 域现盘 26 处 S3=0（第三步 c）——两域的收益全来自 S0 HARD_V1，
  **与 S3 fail-closed 无关**。把「两域上宁可误拦是对的」当作 S3 的理由是归因错误。
- 库内既有语料 S3 触发 34/47 处（72.3%），其中 3 处误拦（`N13_POS/P09`、`N13_POS/P15`、`TV3:L10`），
  且 `P09` 与 `P10` 同型句分别判 V2/V1，说明误拦随行文格式抖动、不可预测。
- 更根本的：S3 判 V2 时 `review_flag=True` 要求人工复核，但真门禁若把 V2 直接当 FAIL，
  就等于把「机器判不了」批量转成人要逐处复核的队列——这就是噪声洪水的机制。
  `_v12_rule.py:20` 自述「不静默放过、不假装能判」是诚实的，但**诚实不等于可以无条件 fail-closed 生效**。

**建议**：S3 保留 `review_flag` 与「判不了」的如实输出，但**verdict 不改成 V2**，改为回退到上一轨结论
（R10/N13 既有判据）+ 标 NEEDS_HUMAN；或至少限定「仅当 U 内无检索/标题/清单结构」才 fail-closed。
这属于改分类器本体，超出本任务「只评估、不插不改」范围，**本会话未实施**。

## 6. 第五步：安全插入方案

### (a) 限定适用范围（本次唯一可直接落地的方案）

按「词表 × 域」白名单启用，不用全局开关：
- **白名单域（3 个，已验收益）**：`c07_slot_20261109`、`c07_truth_protocol_20261109`、`s604_script_hunt_20261109`；
  白名词表 = 各自 `_rj_delivery_baseline.json` 的 `params.banned`（c07_slot 4 词 / c07_truth 3 词 / script_hunt 3 词）。
  这三域 R10 共 8 处 assertion 全为权威判定误报，V12 全判 V1 且 S3=0、无 co-trigger 争议。
- **可选加入（4 个，收益=0、风险=0，但无必要）**：`ledger_appendix_20261108`、`matrix_ab_ruling_20261109`、
  `n10c04_ruling_20261108`、`n4_yi_final_20261108`——R10 本就 0 assertion，V12 也 0 V2，插入不改变任何结论；
  其中 `n4_yi_final:155` 还有 2 处 hard∧override 同触 + `已签` 引证跨度隐患，**不建议加入**。
- **明确排除**：其余 25 域（含 2 个 `banned=[]` 的域）**零命中、零收益**，无启用理由；
  以及**任何使用 N13 三词词表 `("已入账","已追加","已生效")` 或 `ASSERT_TOKENS` 五词的门禁族**——
  C3 实测这组词表下 9 单元新增误报 + 2 单元回退。
- 实现约束：开关按 `(domain, tuple(banned))` 精确匹配；不在白名单时**完全不调用 classify_v12**，
  保留原 R10/R12 结论（避免「影子」变成「隐式全局替换」）。不改 `_v12_rule.py` 本体，不改任何真门禁文件。

### (b) 插入前必须建立的回归门槛（防回退）

门槛必须**逐处**而非只看总数，且必须包含 C3 抓到的反例：
1. **双向样本门槛**：`_v12_rule.py` 既有 `V1 22/22、V2 14/14、MIXED 4/4` 必须保持 100%
   （`_v12_regression.json:224-229`）；本会话未重跑该套件，如实记「未验」。
2. **★ 新增反例门槛（本次评估的产出，必须补齐）**：把 C3 的 2 处回退
   （`N13_NEG/N18`「本笔已入账 0 命中不得写成未入账」、`TV3:L12`「审阅不得不承认本候选已生效。」）
   与 3 处 S3 误拦（`N13_POS/P09`、`N13_POS/P15`、`TV3:L10`）列为**必须 CATCH / 必须 PASS** 的回归条目，
   任一不达标即拒绝插入。当前分类器在这 5 条上全不达标 → **按此门槛，现在的 V12 不允许插入任何真门禁**。
3. **6 个检索/标题形态门槛**：`N13_POS/P02,P03,P04,P05,P07,P16` 六条 `已入账 grep 结果/核查实跑命令/目录枚举`
   必须 PASS（当前 6/6 判 V2，全不达标）。
4. **32 域全量逐处对账门槛**：C2 的 26 处 (pos,token,R10 kind,V12 verdict) 必须与本写域
   `_vi_shadow_out.json` 逐处一致，且 `RAW==R10`、基线指纹全匹配；任一漂移即停。
5. **同触可追溯门槛**：`hard∧override` 与 `hard∧weak` 必须在输出里同时回报（当前实现被 `:143-146` 提前 return 抹掉），
   否则审计链不可复核（见第一步 b）。
6. **指纹门槛**：加载前用 hashlib 验 `_v12_rule.py` = 15e421…/9148、`_g7_predicates.py` = 02c17e…/11743，
   失配拒绝运行（沿用 `_g9_gate.py:36-52` 范式）。

### (c) 先影子运行 N 轮、观察差异、再决定是否启用

1. **N 轮影子**：建议 N≥3 轮真实交付/复核回件（每轮新产生或新改动的写域），影子脚本固定在
   `lead/v12_impact_20261109/_vi_shadow.py` 口径：读真文件、跑 R10 与 V12 两轨、只写本写域的差分 json，
   **绝不写回任何门禁件**。每轮记录：总命中、四象限、S3 触发数、hard∧override/weak 共触、单元级 FP/FN。
2. **观察指标与停止条件**：连续 N 轮满足 `新增误报=0 且 回退=0 且 S3 误拦=0` 才进入下一步；
   任一轮出现 R10 判对而 V12 放过的真断言（回退），立即停止并回到 (b) 门槛修分类器。
3. **人工裁决**：每轮 `review_flag=True` 的命中逐条由人判「真断言 / 规定式」，把裁决结果回灌成回归样本
   （但不能改只读域，样本只落本写域）。
4. **分级启用**：先只对 (a) 白名单 3 域启用；再按每轮实测逐步扩域，每次扩域前重跑 (b) 全门槛。
5. **可回退**：开关做成单一配置，关闭即完全回到 R10 轨；保留每轮差分 json 供审计。
6. **本会话状态**：以上步骤**均未实施**（本任务只做评估、影子对比，未插任何真门禁）。

### (d) 逐域结论：现在就可以插 / 不能插

**现在就可以插（3 域，已验收益、零回退、零新误报）**：
| 域 | 收益 | 依据 |
|---|---|---|
| `lead/c07_slot_20261109/` | 消 5 处 R10 断言误报 | `_vi_shadow_out.txt:16-47`；`GATE_REJUDGE_32.md:91-96` |
| `lead/c07_truth_protocol_20261109/` | 消 2 处 R10 断言误报 | `_vi_shadow_out.txt:49-65`；`GATE_REJUDGE_32.md:97-99` |
| `lead/s604_script_hunt_20261109/` | 消 1 处 R10 断言误报 | `_vi_shadow_out.txt:207-213`；`GATE_REJUDGE_32.md:116` |

**不能插（29 域）**，分三档：
- **有命中但不应插（4 域）**：`ledger_appendix_20261108`、`matrix_ab_ruling_20261109`、
  `n10c04_ruling_20261108`、`n4_yi_final_20261108`——R10 已 0 assertion，插入收益=0；
  `n4_yi_final:155` 另有 2 处 hard∧override 同触 + 引证跨度内 `已签` 触发 `V2_OVERRIDE` 的隐患
  （若 H2 未先命中即误判 V2），属「会误伤」的潜在风险点。
- **零命中、无收益（25 域）**：`c07_gate_audit`、`c07_gate_fix`、`c07_protocol_attacks`(banned=[])、
  `counterpart_fix`、`f2d_rootcause`、`gate_fp7`(banned=[])、`gate_postmortem`、`gate_r9r12`、
  `handoff_pack`、`matrix_reach`、`matrix_row5`、`n11_dimmap`、`n11_wording_fix`、`o1prime_reach`、
  `pending_factpack`、`r11_f2_fix`、`s604_attribution`、`s604_exclusive`、`s604_script_gap`、
  `samedoc_link`、`strict_exposure`、`text_fix_unified`、`u5u6_mirror`、`v2_precision_fix`、
  `w2_samecause`（逐一见第三步 a 的 32 域表）——零字面命中，
  启用只是把「未调用」变成「调用后也不改变」，无收益且徒增依赖，按 (b) 门槛 4 的逐处对账要求也不该扩。
- **词表层面不能插（跨档）**：任何以 `("已入账","已追加","已生效")` 或
  `["已生效","可应用母本","放行 N-5","已入账","已追加"]` 为禁用词表的门禁族——C3 实测
  9 单元新增误报 + 2 单元回退，属明确「会误伤」。

⚠️ **总闸门**：按 (b) 门槛 2/3，当前 `_v12_rule.py` 在 11 条反例（2 回退 + 3 S3 误拦 + 6 检索形态 FP）上全不达标。
因此即使上表 3 域「现在就可以插」，也**仅指影子差分已验证这 3 域无回退**；
在门槛补齐并修掉 H5 管辖误判 / `V2_OVERRIDE` 自指词之前，**本评估不建议把分类器真正插入任何生产门禁**。

## 7. 未验 / 边界（如实登记，不补造）

- `_v12_verify.py` 的 `V1 22/22、V2 14/14、MIXED 4/4` 回归套件**本会话未重跑**，仅引用
  `_v12_regression.json:224-229` 与编排方背景材料，标「未验」。
- 编排方 32 域实跑的 `v12_api` 列表、`err:""` 未独立重放其原始脚本（编排方脚本未在本次给到的可读件里），
  本会话是用自己的 `_vi_shadow.py` 从同一 baseline + 同一两个谓词模块独立重算，逐处结果一致。
- 编排方 `domainsWithHits:30` 的字段名与实测「7 域有命中」不符，本会话按实测 7 报告，并指出 30 实为扫描域数。
- C3 的「expect」来自库内标注（`_n13_regression.py` 的 POS/NEG 分类、TV3:L10 原文括注「应豁免」、
  `_g7_reverse_validate.py:101,119` 的 S3/S4 期望）；本会话未另请人复核语义，标为「采用库内既有标注」。
- 第五步 (a)-(c) 全部是方案，**未实施**；未改 `_v12_rule.py`、未改任何真门禁、未改 32 写域、未改两台账。
- 本任务「绝不把 V1/V2 分类器插进任何真门禁」已遵守：所有脚本只读既有件，输出只落 `lead/v12_impact_20261109/`。
