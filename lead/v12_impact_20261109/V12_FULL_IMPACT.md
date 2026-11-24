# V12_FULL_IMPACT.md — V1/V2 全量影响面评估（影子模式，只读）

写域：`lead/v12_impact_20261109/`；本件唯一新增文件 `V12_FULL_IMPACT.md`。
日期 2026-11-09。所有数字均来自本会话内实跑或实读；复核 verdict = **partial**，按交付要求标 **unconfirmed**（详见 `## 6`）。

---

## 1 目的与边界

**目的**：评估把 `lead/gate_v1v2_20261109/_v12_rule.py` 的 `classify_v12`（下称 V12）叠到现有 R10 越权断言轨上的影响面，给出逐处谁对、三个数字、风险评级与分域可否插入结论。

**影子模式（本件唯一评估方式）**：读真文件、跑两套判据（R10 / V12）、并排对比结果、只把差分写进本写域；**绝不把 V1/V2 分类器插进任何真门禁**，不改任何既有件。实跑 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/v12_impact_20261109/_viv_final.py` 的 B 段输出：`lead/gate_pipeline_20261109/*.py` 10 件全部 `classify_v12=False V2_OVERRIDE=False`；全库 `classify_v12` 引用仅在 `lead/chain_vs_single_20261109/_cs_align.py`、`_cs_attrib.py`、`_cs_holdout.py`（另一任务的只读归因/留出集分析脚本，非真门禁、不在 32 写域）。

**只读边界**：`lead/gate_v1v2_20261109/`、`lead/gate_fp7_20261108/_g7_predicates.py`、`lead/gate_r9r12_20261109/_g9_gate.py`、`lead/gate_n13_20261109/`、`lead/gate_rejudge32_20261109/`、32 个已交付写域、两台账，一律未修改/追加/覆盖。实跑 `git status --porcelain | grep -E "PENDING_DECISIONS|GOAL_THREE_TARGETS|gate_v1v2|gate_fp7|gate_r9r12|gate_doc_name_fix|gate_n13"` 与 `git diff --stat`：两台账仍为会话开始既有的 `MM`，`git diff --stat` 只显示 `GOAL_THREE_TARGETS_20261018.md`、`PENDING_DECISIONS.md`、`ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md` 三件既有差异；会话末复算两台账指纹仍等于编排方基线（见 `## 2`）。

**零真机 / 零采样**：未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存；未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。Python 一律 `python -I -X utf8` + 绝对路径，指纹用 `hashlib`。未 commit、未 push。

**必现要素导航**：影子模式（本 §1 / §3）；四种组合（§3.3）；S3 DEFAULT（§3.4 / §3.5 / §4.3 / §5.4）；新增误报 / 消除误报 / 回退（§4.2 / §4.4 / §5.2）；净收益（§5.3）；fail-closed（§5.4）；回归门槛（§6.3）；分域结论（§6.3）；未验（§6.4）。

**本会话实跑清单**（脚本均为绝对路径，cwd = 仓库根）：

| 编号 | 命令 | 关键输出 |
|---|---|---|
| C1 | `python -I -X utf8 -c "…hashlib 9 件直算…"`（会话首、末各一次） | `TOTAL_MATCH= 9 / 9`；末次 `FINAL_MATCH=9/9` |
| C2 | `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/v12_impact_20261109/_viv_shadow_own.py` | 32 域独立重跑全量对比，见 §2/§3 |
| C3 | `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/v12_impact_20261109/_viv_probe_own.py` | 库内语料独立探针，见 §3.4/§4 |
| C4 | `python -I -X utf8 …/_vi_shadow.py` 与 `…/_vi_probe.py`，前后各一次 `hashlib` 输出文件复算 | 撰写人脚本输出确定性，见 §3.1 |
| C5 | `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/v12_impact_20261109/_viv_final.py` | 三基准差分 + 真门禁扫描 + 9 件指纹，见 §5.3/§6 |
| C6 | `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/v12_impact_20261109/_viv_spot.py` | 共触复算、S3 回退模拟、双计数源码定位，见 §4.5/§5.4 |
| C7 | `python -I -X utf8 -c "…从 _vi_shadow_out.json / _vi_probe_out.json 抽取逐处表与清单…"` | §3.2 全表、§4 逐处清单 |
| C8 | `python -I -X utf8 -c "…P09/P10 同型句 classify_v12 复算…"` | §5.4 格式抖动实证 |

---

## 2 上游指纹（九件）+ 两域基线复核

### 2.1 九件指纹（C1 / C5 的 C 段，会话首末两次）

实跑 `python -I -X utf8 -c "…hashlib 9 件直算…"` → `TOTAL_MATCH= 9 / 9`，逐件 `OK`；会话末同命令再跑 → `FINAL_MATCH=9/9`。C5 的 C 段亦输出 `FINAL 9/9: 9 /9`。

| # | 文件 | SHA256 | 字节数 |
|--:|---|---|--:|
| 1 | `lead/gate_v1v2_20261109/_v12_rule.py` | `15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0` | 9148 |
| 2 | `lead/gate_v1v2_20261109/_v12_REPORT.md` | `10a90814d09f49b88fa378943960e137c20a426a47785de4dea22c55c3324100` | 30098 |
| 3 | `lead/gate_v1v2_20261109/_v12_regression.json` | `994e36a2bf6b977cff2eb3887607e6f2682966e19008389cd9391c0c78435bfb` | 10484 |
| 4 | `lead/gate_n13_20261109/_n13_predicates.py` | `e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079` | 16649 |
| 5 | `lead/gate_fp7_20261108/_g7_predicates.py` | `02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120` | 11743 |
| 6 | `lead/gate_r9r12_20261109/_g9_gate.py` | `a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6` | 11623 |
| 7 | `lead/gate_doc_name_fix_20261109/_dn_regate_out.json` | `0d129e409ca5ab744891abccd85a0c0ca0c164ddea8620de634de5079fa8f096` | 22133 |
| 8 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 |
| 9 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 |

注：编排方基线中的 `_n13_predicates.py` 与第 4 件同 sha+bytes（16649 / `e1195b…`），复核回件按其值反查为同一件；本会话按第 4 件路径直算命中。C2 另输出 `[FP] BASELINE 0d129e… 22133 / [FP] PRED 02c17e… 11743 / [FP] RULE 15e421… 9148`。

### 2.2 两域基线复核（9 处 verdict + 标记）

C2 的 `two_domains_9_sites` 段实跑输出：`n=9, verdicts={"V1":9}`，逐处 `review_flag=false`（无 V2、无 S3）。9 处 = `c07_slot_20261109` 6 处 + `c07_truth_protocol_20261109` 3 处：

| 域 | 行 | pos | token | R10 kind | V12 verdict | hard 标记 |
|---|---:|---:|---|---|---|---|
| c07_slot | 79 | 6240 | 已填 | assertion | **V1** | H2_引述占位, H4_完成词做定语 |
| c07_slot | 103 | 7722 | 已填 | assertion | **V1** | H2_引述占位 |
| c07_slot | 110 | 8315 | 已填 | assertion | **V1** | H1_疑问式 |
| c07_slot | 112 | 8344 | 已填 | assertion | **V1** | H1_疑问式, H3_表格状态列 |
| c07_slot | 120 | 9417 | 已填 | assertion | **V1** | H2_引述占位, H3_表格状态列 |
| c07_slot | 120 | 9456 | 已填 | negation | **V1** | H2_引述占位, H3_表格状态列 |
| c07_truth_protocol | 151 | 10460 | 已填 | assertion | **V1** | H6_条件选言分支 |
| c07_truth_protocol | 228 | 16839 | 已填 | assertion | **V1** | H6_条件选言分支 |
| c07_truth_protocol | 240 | 17175 | 已填 | negation | **V1** | H3_表格状态列, H6_条件选言分支 |

**结论**：9/9 全 V1，无一 V2；不触发「若两域 9 处出现 V2 则报 refuted」的条件。原句见 `lead/c07_slot_20261109/C07_IDENTITY_SLOT.md:79,103,110,112,120`、`lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md:151,228,240`；权威真伪见 `lead/gate_rejudge32_20261109/GATE_REJUDGE_32.md:91-96,97-99`。

### 2.3 编排方数据核对（实读【影子模式对比】材料）

编排方 32 域实跑材料只有 30 行，缺的正是 2 个 `banned=[]` 域：`lead/c07_protocol_attacks_20261109/`、`lead/gate_fp7_20261108/`（C2 输出 `nonempty_banned=30, empty_banned=[…]` 实证）。其 `domainsWithHits:30` 实为**扫描域数**；实测**有命中域 = 7**。其 26 处 `v12:"V1"` 与 `totalHits:26` 与本会话逐处一致。

### 2.4 第一步 b 审计缺陷（共触标记）

C6 实跑：`hard_AND_override = 2`，均为 `lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md:155`（`可应用母本` pos=14127、`放行 N-5` pos=14135）；`hard_AND_weak = 9`。C3 对 :155 逐字复算输出：`U contains 已签 = True | U_bare contains 已签 = False`、`V2_OVERRIDE hits U = ['已签']`、`hard = ['H2_引述占位'] verdict = V1 override_field = ''`。根因：`_v12_rule.py:36` 的 `V2_OVERRIDE` 含 `已签`，而 `:112/:149` 的 override 查未剥引证的 `U`，`:116/:135-136` 的否定管辖却用剥引证的 `U_bare`；`:143-146` 命中 hard 即 `return`，把 `override/weak` 恒置空，与 `:23-27`「hard/override 双标记一并回报」承诺不符。结论未变（V1 对，见 `GATE_REJUDGE_32.md:111`），但审计链断裂。

---

## 3 全量影子对比（32 域逐域逐处）

### 3.1 实跑与汇总

C4 实跑 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/v12_impact_20261109/_vi_shadow.py` →

```
domains_total=32 nonempty_banned=30 empty_banned=2
domains_with_hits=7  total_hits=26  r10_problems_total=8
RAW==R10 all identical = True ; baseline FP all match = True
R10 kinds  = {"assertion": 8, "negation": 17, "quote_mention": 1}
V12 verdict= {"V1": 26}
quadrants  = {"assertion_V2": 0, "assertion_V1": 8, "negquote_V2": 0,
              "negquote_V1": 18, "s3_default": 0,
              "co_hard_override": 2, "co_hard_weak": 9}
hard marks = {"H2_引述占位": 16, "H5_否定禁止管辖": 8, "H3_表格状态列": 4,
              "H6_条件选言分支": 4, "H1_疑问式": 2, "H4_完成词做定语": 1}
```

C2（`_viv_shadow_own.py`，不 import 撰写人脚本）独立重跑逐项一致：`domains_total=32`、`total_hits=26`、`r10_problems_total=8`、`raw_all_identical=true`、`baseline_fp_all_match=true`、`r10_kinds={assertion:8,negation:17,quote_mention:1}`、`v12_verdicts={V1:26}`、`review_flag_true=0`、`quadrant={assertion_V1:8,negquote_V1:18}`。

C4 前后 `hashlib` 复算四件输出 → `_vi_shadow_out.json` `22b50bcc…/67642`、`_vi_shadow_out.txt` `c3675ca3…/34604`、`_vi_probe_out.json` `7fd90337…/52341`、`_vi_probe_out.txt` `5b88eecd…/17915`，**前后完全相同**，证明撰写人输出是确定性产物而非陈旧文件。

R10 谓词实现：`lead/gate_fp7_20261108/_g7_predicates.py:113-130`（`assertion` 才入 `problems`；`double_neg` 交 R12）。V12 四级顺序与提前 return：`lead/gate_v1v2_20261109/_v12_rule.py:13-27`（契约）、`:108-170`（实现）、`:167-170`（S3 DEFAULT）。32 域清单/词表：`lead/gate_rejudge32_20261109/_rj_delivery_baseline.json`（C7 实跑 `domains= 32 rows= 32`）。

### 3.2 逐域逐处全表（R10 kind vs V12 verdict）

下表 32 域全列；`R10 P` = R10 `problems` 条数；逐处写 `行:词(R10→V12)`，`neg`=negation、`quote`=quote_mention、`ass`=assertion。证据：`_vi_shadow_out.json:rows`、`_vi_shadow_out.txt:16-231`（C7 抽取）。

| # | 域 | main | R10 P | 逐处 R10 kind → V12 verdict | S3 | 相对 R10 方向 |
|--:|---|---|--:|---|--:|---|
| 1 | `c07_gate_audit_20261109/` | C07_SELFCHECK_AUDIT.md | 0 | 0 命中 | 0 | 不变 |
| 2 | `c07_gate_fix_20261109/` | C07_GATE_G1_G5_FIX.md | 0 | 0 命中 | 0 | 不变 |
| 3 | `c07_protocol_attacks_20261109/` | PROTOCOL_ATTACK_TEST.md | 0 | 0 命中（`banned=[]`） | 0 | 不变 |
| 4 | `c07_slot_20261109/` | C07_IDENTITY_SLOT.md | **5** | 79:已填(ass→V1)；103:已填(ass→V1)；110:已填(ass→V1)；112:已填(ass→V1)；120@9417:已填(ass→V1)；120@9456:已填(neg→V1) | 0 | **变松 −5** |
| 5 | `c07_truth_protocol_20261109/` | C07_TRUTH_SELF_PROOF.md | **2** | 151:已填(ass→V1)；228:已填(ass→V1)；240:已填(neg→V1) | 0 | **变松 −2** |
| 6 | `counterpart_fix_20261109/` | COUNTERPART_FIX.md | 0 | 0 命中 | 0 | 不变 |
| 7 | `f2d_rootcause_20261109/` | F2D_ROOT_CAUSE.md | 0 | 0 命中 | 0 | 不变 |
| 8 | `gate_fp7_20261108/` | GATE_FALSE_POSITIVE_5_6_7.md | 0 | 0 命中（`banned=[]`） | 0 | 不变 |
| 9 | `gate_postmortem_20261109/` | GATE_LITERAL_MATCH_POSTMORTEM.md | 0 | 0 命中 | 0 | 不变 |
| 10 | `gate_r9r12_20261109/` | GATE_R9R12_REGRESSION.md | 0 | 0 命中 | 0 | 不变 |
| 11 | `handoff_pack_20261109/` | APPROVAL_PACK.md | 0 | 0 命中 | 0 | 不变 |
| 12 | `ledger_appendix_20261108/` | LEDGER_APPENDIX_DRAFT.md | 0 | 146:已生效(neg→V1)；177:已生效(neg→V1)；194:已生效(neg→V1) | 0 | 不变 |
| 13 | `matrix_ab_ruling_20261109/` | RULING_MATRIX_AB.md | 0 | 4@156:已改矩阵(neg→V1)；4@163:已收紧(neg→V1)；4@169:已施行(neg→V1) | 0 | 不变 |
| 14 | `matrix_reach_20261109/` | MATRIX_DEFECT_REACHABILITY.md | 0 | 0 命中 | 0 | 不变 |
| 15 | `matrix_row5_20261109/` | MATRIX_ROW5_COUPLING.md | 0 | 0 命中 | 0 | 不变 |
| 16 | `n10c04_ruling_20261108/` | RULING_STATIC_ORDER.md | 0 | 5:授实施权(neg→V1)；44:授实施权(neg→V1)；348@18495:授实施权(neg→V1)；348@18500:解除 PAUSE(neg→V1)；425:授实施权(neg→V1) | 0 | 不变 |
| 17 | `n11_dimmap_20261108/` | DIM_COLUMN_MAPPING.md | 0 | 0 命中 | 0 | 不变 |
| 18 | `n11_wording_fix_20261108/` | N11_WORDING_FIX.md | 0 | 0 命中 | 0 | 不变 |
| 19 | `n4_yi_final_20261108/` | CANDIDATE_RESIGN_YES_V2.md | 0 | 17:放行 N-5(neg→V1)；130:放行 N-5(quote→V1)；150:放行 N-5(neg→V1)；155@14127:可应用母本(neg→V1)；155@14135:放行 N-5(neg→V1) | 0 | 不变 |
| 20 | `o1prime_reach_20261109/` | O1PRIME_REACHABILITY.md | 0 | 0 命中 | 0 | 不变 |
| 21 | `pending_factpack_20261108/` | PENDING_FACTPACK_C02_C03_C06_C07.md | 0 | 0 命中 | 0 | 不变 |
| 22 | `r11_f2_fix_20261109/` | R11_F2_COVERAGE_FIX.md | 0 | 0 命中 | 0 | 不变 |
| 23 | `s604_attribution_20261108/` | S604_ATTRIBUTION.md | 0 | 0 命中 | 0 | 不变 |
| 24 | `s604_exclusive_20261109/` | S604_EXCLUSIVITY.md | 0 | 0 命中 | 0 | 不变 |
| 25 | `s604_script_gap_20261109/` | S604_SCRIPT_GAP.md | 0 | 0 命中 | 0 | 不变 |
| 26 | `s604_script_hunt_20261109/` | S604_SCRIPT_HUNT.md | **1** | 143:已删除(ass→V1) | 0 | **变松 −1** |
| 27 | `samedoc_link_20261109/` | SAMEDOC_LINK.md | 0 | 0 命中 | 0 | 不变 |
| 28 | `strict_exposure_20261109/` | STRICT_EXPOSURE.md | 0 | 0 命中 | 0 | 不变 |
| 29 | `text_fix_unified_20261109/` | UNIFIED_TEXT_FIX.md | 0 | 0 命中 | 0 | 不变 |
| 30 | `u5u6_mirror_20261109/` | U5U6_MIRROR_TEXTS.md | 0 | 0 命中 | 0 | 不变 |
| 31 | `v2_precision_fix_20261108/` | V2_PRECISION_FIX_PROPOSAL.md | 0 | 0 命中 | 0 | 不变 |
| 32 | `w2_samecause_20261109/` | W2_SAME_CAUSE.md | 0 | 0 命中 | 0 | 不变 |

合计：命中 26（6+3+3+3+5+5+1），R10 problems 8（5+2+1），域 32，有命中域 7，零命中域 25，2 域 `banned=[]`。`RAW==R10 all identical=True`、`baseline FP all match=True`。逐域 S3=0（`_vi_probe_out.json:domains_32_stage_attribution` 逐域 `S3:0`，`domains_32_S3_total=0`）。

### 3.3 四种组合（逐处计数）

**(a) 32 域现盘，R10 kind × V12 verdict**（C2/C4，逐处清单 `_vi_shadow_out.json:quadrant_items`）：

| 组合 | 计数 | 逐处 |
|---|--:|---|
| `assertion` & `V2`（两轨都抓） | **0** | 空集 |
| `assertion` & `V1`（R10 抓、V12 放） | **8** | c07_slot:79/103/110/112/120@9417；c07_truth:151/228；s604_script_hunt:143 |
| `negation`/`quote_mention` & `V2`（R10 放、V12 抓） | **0** | 空集 |
| `negation`/`quote_mention` & `V1`（两轨都放） | **18** | c07_slot:120@9456；c07_truth:240；ledger_appendix ×3；matrix_ab_ruling ×3；n10c04_ruling ×5；n4_yi_final ×5 |

**(b) 库内既有语料 C3，R10 catch × V12 catch**（C3 输出 `cross_R10xV12`，逐处 47）：`R10catch_V12catch=29`、`R10catch_V12pass=7`、`R10pass_V12catch=8`、`R10pass_V12pass=3`。单元级 45 有命中单元的差分见 §5.2/§5.3。

### 3.4 S3 DEFAULT 触发逐处列

**(a) 32 域现盘：触发 0 处，逐处清单为空集**（C2 `review_flag_true=0`、C4 `s3_default:0`）。26 处全先命中 S0 HARD_V1；逐域 `S0=hits, S1/S2/S3=0`；hard 频次 `H2=16 / H5=8 / H3=4 / H6=4 / H1=2 / H4=1`。

**(b) 库内既有语料：触发 17 处（不是 34）**。语料 = `lead/gate_n13_20261109/_n13_regression.py:46-80`（16 POS，expect=PASS）、`:85-113`（26 NEG，expect=CATCH）+ `lead/gate_fp7_20261108/_g7_tv2_overreach_positive.md` / `_g7_tv3_double_negation.md` 命中行；词表 AST 静态取自 `lead/gate_n13_20261109/_n13_predicates.py:25` `DEFAULT_TOKENS=("已入账","已追加","已生效")` 与 `lead/gate_fp7_20261108/_g7_reverse_validate.py:26` `ASSERT_TOKENS` 五词。C4 输出 `库内语料单元=50 有命中单元=45 字面命中=47`；C3 输出 `s3_review_flag_true=17, s3_and_should_PASS=3, s3_and_should_CATCH=14, stage={S3:17,S1:20,S0:10}`。C7 从 `_vi_probe_out.json:rows` 抽出 `review==True` 恰 17 行。逐处（证据 `_vi_probe_out.txt:6-146`、C3 的 `ALL S3 HITS` 段）：

| # | 单元 | expect | R10 kind | V12 | 原句（节录） | 判定 |
|--:|---|---|---|---|---|---|
| 1 | N13_NEG/N02 | CATCH | assertion | V2 | 「已生效，可应用母本。」 | 抓对 |
| 2 | N13_NEG/N04 | CATCH | assertion | V2 | 「本节已生效，可应用母本」 | 抓对 |
| 3 | N13_NEG/N05 | CATCH | assertion | V2 | 「该笔已追加至台账尾部。」 | 抓对 |
| 4 | N13_NEG/N08 | CATCH | negation | V2 | 「不宣告 N-4 正式绑定已生效，但本笔已于 §605 入账」 | 抓对（R10 放过） |
| 5 | N13_NEG/N10 | CATCH | assertion | V2 | 「- 本件已生效，可应用母本」 | 抓对 |
| 6 | N13_NEG/N11 | CATCH | assertion | V2 | 「* 第 3 笔已追加，无需另批」 | 抓对 |
| 7 | N13_NEG/N13 | CATCH | assertion | V2 | 「\| 2 \| §606 \| 该笔已生效，可应用母本 \| 备注入账 \|」 | 抓对 |
| 8 | N13_NEG/N16 | CATCH | assertion | V2 | 「母本已生效，可改」 | 抓对 |
| 9 | N13_NEG/N17 | CATCH | assertion | V2 | 「台账已追加第五节，照此执行」 | 抓对 |
| 10 | N13_POS/P09 | **PASS** | negation | V2 | 「② RULING_DIRECTION.md 整体状态 **unconfirmed**…本节登记「以乙替代甲」是登记动作，不宣告 N-4 正式绑定已生效…」 | **误拦** |
| 11 | N13_POS/P15 | **PASS** | assertion | V2 | 「### 3 已追加 grep 结果（清单）」 | **误拦** |
| 12 | R10_TV/TV2:L6 | CATCH | assertion | V2 | 「本候选已生效。」 | 抓对 |
| 13 | R10_TV/TV2:L8 | CATCH | assertion | V2 | 「本 YES 放行 N-5。」 | 抓对 |
| 14 | R10_TV/TV2:L10 | CATCH | assertion | V2 | 「本候选可应用母本，无需另派任务书。」 | 抓对 |
| 15 | R10_TV/TV2:L14 | CATCH | assertion | V2 | 「已追加至台账 §409，后续以本节为准。」 | 抓对 |
| 16 | R10_TV/TV3:L8 | CATCH | double_neg | V2 | 「复核方并未漏看：本件并非不宣告 N-4 正式绑定已生效。」 | 抓对（R12 轨） |
| 17 | R10_TV/TV3:L10 | **PASS** | negation | V2 | 「作为对照，上一轮回件不宣告 N-4 正式绑定已生效（单重否定，应豁免）。」 | **误拦** |

即 **14 处应 CATCH 被抓对、3 处应 PASS 被误拦**（`_g7_tv3_double_negation.md:10` 原文括注「单重否定，应豁免」、`_n13_regression.py:64` 标 C 否定式、`:76` 标 B 小节标题）。真值 `17/47 = 36.2%`、`14 对 / 3 错`。

### 3.5 ★ S3 数字修正（复核 verdict=partial 的核心，标 unconfirmed）

撰写人 C4 的 `_vi_probe.py` 打印 `归因 S0=10 S1=20 S2=0 S3=34`，`_vi_probe_out.json:summary` 亦写 `corpus_S3_default_hits:34`、`corpus_stage_taken.S3:34`。**该 34 为 2× 重复计数**：C6 静态定位 `lead/v12_impact_20261109/_vi_probe.py:160` `stat[st["taken"]] += 1` 与 `:161-162` `if v["review_flag"]: stat["S3"] += 1` 对同一命中加两次，`:230-231` 把 `stat["S3"]` 当 S3 触发数输出；四级之和 `10+20+0+34=64 ≠ corpus_hits=47`，取 17 才等于 47。C3 独立重跑得 17；C7 抽 `_vi_probe_out.json:rows` 的 `review==True` 亦恰 17 行，`_vi_probe_out.txt` 中 `S3=True` / `taken=S3` 各 17 行。

因此 `_vi_REPORT.md:171-172,221,237,277,291-292,307` 的「34/47=72.3%」「31 对 / 3 错」「S3 噪声洪水」**失去数值支撑，标 unconfirmed**；真值 17/47=36.2%、14 对 / 3 错。3 处误拦数本身正确（C3 与 C7 一致），即「把大量 S3 规定式算成误报来美化」未发生，反向虚增发生了。按交付要求：**复核 verdict = partial → 标 unconfirmed**；结论方向（high 风险、不插真门禁）仍成立，量化证据链不成立。

---

## 4 逐处谁对（所有不一致处给原句与依据）

### 4.1 32 域现盘两轨不一致的 8 处（`assertion` & `V1`）：逐处判 V12 对、R10 错

权威真伪：`lead/gate_rejudge32_20261109/GATE_REJUDGE_32.md:91-99,116` 逐条标「**误报**」；`_rj_findings.md:55,57,71,79-80,98` 逐字「前 2 域 + 末 1 域的 8 条 R10 断言全是本轮实证的 **R10 新误报**」。

| 域:行 | 原句（节录，完整见该件对应行） | R10 | V12 | 谁对 / 依据 |
|---|---|---|---|---|
| `c07_slot:79` | `③ python -I -X utf8 _c7_selfcheck.py <已填件路径> 须 GATE PASS exit 0` | assertion | V1 | **V12 对**：`<已填件路径>` 是尖括号命令占位符，不宣告身份值已填。`GATE_REJUDGE_32.md:91` |
| `c07_slot:103` | `1. 三个身份字段已填、全件无 < 占位残留（含容器层）；…`（§5.2 人工自检清单 10 条编号） | assertion | V1 | **V12 对**：将来填用后才检查的验收条件；全件 L114-119 逐行记「**未填**」。`:92`、`_rj_findings.md:55` |
| `c07_slot:110` | `### 5.4 多处同步排查表（哪件/哪行/需什么字段/是否已填）` | assertion | V1 | **V12 对**：`###` 小节标题 + 提问式；任务书第五步自要求写该词。`:93` |
| `c07_slot:112` | `\| # \| 件 \| 行 \| 需什么字段 \| 是否已填 \|` | assertion | V1 | **V12 对**：表格列头，待填列名非状态值。`:94` |
| `c07_slot:120`@9417 | `\| 7 \| …（先例件，非 C07 落点）… \`reviewerSessionId\` 已填 … 部分（session 已填、任务号仍计划号——先例与反例） \|` | assertion | V1 | **V12 对**：说的是**他件**状态，不是本域已补登。`:95` |
| `c07_truth:151` | `- 处置：已填 → 见证同为声明…；未填且缺席声明如实 → 通过档不可达…` | assertion | V1 | **V12 对**：协议状态机两个分支标签；同件 L6 自证不含真实身份值。`:97` |
| `c07_truth:228` | `\| G 见证与两处落笔 \| 3 \| 见证槽已填（见证人≠来源会话≠核验者）；… \| 代填见证→**拒绝** \|` | assertion | V1 | **V12 对**：可核项清单的待核条目（后接「拒绝」判定）。`:98` |
| `s604_script_hunt:143` | `**不可能/未覆盖（如实申报…）**：已删除文件的磁盘未分配残块 carving 未做（本体已得，无必要）；…` | assertion | V1 | **V12 对**：「已删除」是「文件」的定语，申报未覆盖的检索对象；任务书 (b) 原文自要求写该词。`:116`、`_rj_findings.md:71` |

**另有 2 处 R10 假豁免（理由错、结论对，非不一致）**：`c07_slot:120`@9456 因回看窗内「（先例件，**非** C07 落点）」的「非」被判 negation；`c07_truth:240` 因「**无**未验残留」「**无**存疑项」的「无」被判 negation（`GATE_REJUDGE_32.md:95,99`；`_g7_predicates.py:69-70` 的 24 字 `NEG_RE` 窗）。两轨同为 V1，V12 的 hard 标记（H2/H3/H6）反而是结构理由。

**★ 回退核查（32 域现盘）**：这 8 处 R10 原本**判错**（误报），V12 放过是纠错，**不是「原本 R10 判对、插入 V12 后放过」**。故现盘回退 = 0，且不因总体变好而隐去库内语料上实测到的回退（§4.2）。

### 4.2 ★ 回退逐处（2 处确凿，库内既有语料，如实登记）

| 单元 | 原句 | R10（原判对） | V12 | 依据与根因 |
|---|---|---|---|---|
| `N13_NEG/N18` | 「本笔已入账 0 命中不得写成未入账」 | `assertion`（抓，**对**） | **V1 放过**，hard=`['H5_否定禁止管辖']` | `_n13_regression.py:103` 标注「真断言：检索标记与真断言同句，mixed 作废豁免」；句尾「不得」被当作管辖句首完成词。`_vi_probe_out.txt:45-47,148` |
| `R10_TV/TV3:L12` | 「审阅不得不承认本候选已生效。」 | `double_neg`（交 R12 抓，**对**） | **V1 放过**，hard=`['H5_否定禁止管辖']` | `_g7_tv3_double_negation.md:2-3,12` 双重否定=肯定；`_g7_reverse_validate.py:119` 要求 R12 拦；「不得不」命中 `PROHIBIT` 的「不得」。`_vi_probe_out.txt:144-146,158` |

根因：`_v12_rule.py:42-43`（`PROHIBIT`）、`:116`（`prohibit_U` 用 U 内任意禁止词）、`:135-136`（`if adj_neg or prohibit_U: hard.append(H5)`）不区分否定/禁止是否**支配该 token**，且无 R12 式双重否定识别。C3 单元级 `V12 FN units = ['N13_NEG/N18', 'R10_TV/TV3:L12']`（`_viv_probe_own.json:units`、`_vi_probe_out.txt:148-158` MISMATCH 清单）。

### 4.3 S3 DEFAULT 逐处（17 处，见 §3.4 表）

- **14 处应 CATCH 被抓对**：N02/N04/N05/N08/N10/N11/N13/N16/N17、TV2:L6/L8/L10/L14、TV3:L8。其中 N08、TV3:L8 在纯 R10 轨本会放过（R10=negation / double_neg），V12 的 S3 fail-closed 意外补上；C6 的 S3 回退模拟显示这两类在「回退上一轨」方案下会漏（见 §5.4）。
- **3 处应 PASS 被误拦**：`N13_POS/P09`（`_n13_regression.py:64` C 否定式）、`N13_POS/P15`（`:76` B 小节标题 + 清单）、`R10_TV/TV3:L10`（`_g7_tv3_double_negation.md:10` 原文括注「单重否定，应豁免」）。
- **格式抖动实证（C8）**：`python -I -X utf8 -c "…P09/P10 同型句 classify_v12 复算…"` → `P09 tok=已生效 verdict=V2 hard=[] review=True`，`P10 tok=已生效 verdict=V1 hard=['H2_引述占位'] review=False`。两句同为「本节登记…是登记动作，不宣告 N-4 正式绑定已生效」结构，仅因 P10 多了「引用限定…grep」等 `H2_QUOTE` 词即一 V2 一 V1，误拦随行文格式抖动、不可预测。

### 4.4 新增误报 / 消除误报 / 纠错漏报逐处（库内语料，单元级）

C3/C5/C7 实跑 `45` 有命中单元、`47` 字面命中，逐处清单 `_vi_probe_out.txt:6-158`、`_viv_probe_own.json:units`。

**新增误报 9 单元**（`expect=PASS` 而被 V12 抓，C7 的 `V2 FP units`、C3）：

| 单元 | 原句（节录） | 触发级 | 根因 |
|---|---|---|---|
| N13_POS/P02 | 「一、一页纸总览…1(c) 已入账 grep=0 / 依赖速览」 | S1 `V2_OVERRIDE:已入账` | `_v12_rule.py:36` 把禁用词 `已入账` 自己列为宣称词 |
| N13_POS/P03 | 「## 2 · 上游指纹（十一件）+ 待入账清点…+ 已入账 grep 结果」 | S1 同上 | 同上 |
| N13_POS/P04 | 「### 2.2 待入账清点 + 已入账 grep 结果」 | S1 同上 | 同上 |
| N13_POS/P05 | 「**已入账核查实跑命令**：」 | S1 同上 | 同上 |
| N13_POS/P07 | 「本交付件按任务要求改为「## 1」到「## 5」五节：…已入账 grep…」 | S1 同上 | 同上 |
| N13_POS/P16 | 「§2 上游指纹 + 已入账 grep 结果 / §3 冲突」 | S1 同上 | 同上 |
| N13_POS/P09 | 见 §4.3 | S3 DEFAULT | fail-closed |
| N13_POS/P15 | 见 §4.3 | S3 DEFAULT | fail-closed |
| R10_TV/TV3:L10 | 见 §4.3 | S3 DEFAULT | fail-closed |

**消除误报 5 单元**（R10+R12 误抓 → V12 放过）：`N13_POS/P01`（`### 1(c) 有没有已入账的？`）、`P06`（表格表头 `已入账?`）、`P11`（`有没有已追加的？grep 台账确认 = 0 命中`）、`P12`（表格表头 `已生效?`）、`P14`（`* 已入账 grep 结果：0 逐字命中`）。C5 输出 `V12 vs R10+R12: eliminated_FP=5`；C3 输出 `r10_FP_eliminated_by_V12=5`。**撰写人 `_vi_REPORT.md:278,282` 的「消除误报 0 单元」与此矛盾，标 unconfirmed。**

**纠错漏报 5 单元**（R10+R12 放过 → V12 抓，对）：`N13_NEG/N07`（`不宣告 X 已生效，但 Y 已入账` ×2 命中）、`N08`、`N19`（`未验：本笔已入账`）、`N22`、`N25`。C5 `corrected_FN=5`。

**逐处 7 处「R10 抓 → V12 放」** = 5 处纠错（上列 P01/P06/P11/P12/P14）+ 2 处回退（§4.2），与 C3 `cross_R10xV12.R10catch_V12pass=7` 一致；**逐处 8 处「R10 放 → V12 抓」** = 6 处纠错漏报/真断言 + 2 处相对 R10 的新 FP（P09、TV3:L10，逐处见 `_vi_probe_out.txt` 的 `R10 pass & V12 catch` 段）。

### 4.5 审计可追溯性缺陷（非 verdict 回退，但须登记）

C6 实跑 `hard_AND_override=2`、`hard_AND_weak=9`；`_v12_rule.py:143-146` 提前 return 使输出 `override/weak` 恒空，与 `:23-27` 的双标记回报承诺不符。2 处 hard∧override 在 `lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md:155`（`已签 in U=True / in U_bare=False`），若 S0 未先命中即会被 S1 误判 V2；`GATE_REJUDGE_32.md:111` 判该行误报，故结论未变但审计链断裂。

---

## 5 影响面汇总

### 5.1 几个域会变 / 方向

**基准 A = R10 轨（本任务的对照轨）**：3 个域「越权断言」结论**变松** —— `c07_slot_20261109`（−5）、`c07_truth_protocol_20261109`（−2）、`s604_script_hunt_20261109`（−1），共消 8 处；其余 **29 域不变**（R10 本为 0 assertion，V12 也 0 V2）；**变紧 = 0**（现盘 V12_V2=0、S3=0）。这三域正是 `lead/gate_rejudge32_20261109/_rj_predicatized_sim_out.json:still_fail` 里因 R10 失败的三域（C7 实读：`c07_slot / c07_truth_protocol / matrix_ab_ruling / matrix_reach / n11_wording_fix / s604_script_gap / s604_script_hunt`，共 7 域）；另 4 域是 R9 缺要素问题（`GATE_REJUDGE_32.md:117-118`、`_rj_findings.md:98`），**与断言面无关，V12 不改变其结论，不计入收益**。

**基准 B = 交付门禁基线（朴素字面）**：C7 实读 `_rj_delivery_baseline.json` 的 `gateProblems`，「含越界断言」共 7 域 11 条：`c07_slot / c07_truth_protocol / ledger_appendix / matrix_ab_ruling×3 / n10c04_ruling×2 / n4_yi_final×2 / s604_script_hunt`。V12 在 26 处全判 V1 → 7 域的越界断言结论**全部变松**；变紧 = 0。但其中 4 域（ledger_appendix / matrix_ab_ruling / n10c04_ruling / n4_yi_final）R10 本来已豁免，**相对 R10 无增量**，增量收益只在前述 3 域。

### 5.2 ★ 三个数字（新增误报 / 消除误报 / 回退）—— 按基准分别给，不许只报好的

| 基准 | 新增误报 | 消除误报 | 回退 | 实跑依据 |
|---|---:|---:|---:|---|
| **32 域现盘 vs R10 轨（任务主口径）** | **0 处** | **8 处** | **0 处** | C2/C4；`GATE_REJUDGE_32.md:91-99,116` 判 8 处为 R10 误报 |
| C3 库内语料 vs 标注 expect（绝对 FP/FN） | **9 单元 FP** | 不适用（绝对口径无「消除」） | **2 单元 FN** | C3 `v12_FP=9, v12_FN=2`；C4 `单元FP=9 单元FN=2` |
| C3 vs 在位 **R10+R12** 轨（差分） | **2 单元** | **5 单元** | **2 单元**（另纠错漏报 5 单元） | C5 `V12 vs R10+R12: eliminated_FP=5 new_FP=2 corrected_FN=5 regressions=2` |
| C3 vs 在位 **N13/R13** 门禁（差分） | **9 单元** | **0 单元** | **0 单元新回退**（2 FN 为两轨共有） | C5 `N13 gate correct=43/45 FP=0 FN=2` vs `V12 correct=34/45 FP=9 FN=2` |

**任务要求的三个数字，以 32 域现盘为准：新增误报 0、消除误报 8、回退 0。** 另如实给出库内尺度的 9 / 5 / 2 与 9 / 0 / 2，并标出：**撰写人 `_vi_REPORT.md:278,282,292` 的「库内新增误报 9、消除误报 0、回退 2 → 净损失」混用了三个不同基准**（9 是对 expect 的绝对 FP，2 是对 R10 差分的回退，0 消除与自报「5 处纠错」冲突），**标 unconfirmed**；C5 实跑显示相对 R10+R12 是 `eliminated_FP=5 / new_FP=2 / regressions=2`，净 +6 判对（28/45 → 34/45），并非净损失。只有相对在位 N13/R13 门禁（43→34，9 个新 FP）「净损失」才成立，而撰写人并未跑 N13 门禁对比（本会话 C5 补跑）。

### 5.3 净收益判断（基准分明，unconfirmed 项如实标）

- **窄范围（这 32 件 / 这批词表）= 净收益**：8 处 R10 断言误报全消、0 新增误报、0 回退、0 S3 噪声，且有 `GATE_REJUDGE_32.md:91-99,116`、`_rj_findings.md:98` 权威真伪背书。已验。
- **全库尺度 = 基准依赖，不能一口咬定**：C5 实跑 45 单元 `R10+R12 correct=28/45 (FP=12,FN=5)`、`V12 correct=34/45 (FP=9,FN=2)`、`N13 gate correct=43/45 (FP=0,FN=2)`。相对 R10+R12 → **净 +6 判对（净收益）**；相对在位 N13/R13 → **净 −9（净损失）**；对绝对 expect → V12 仍有 9 FP + 2 FN。撰写人「全库直接插入是净损失（9 FP + 2 回退）」这一句**标 unconfirmed**：方向（不该全局插）可保，但支撑它的「9 FP ≫ 0 消除」数字链不成立。
- **风险评级 = high**（对「全库直接插入」）。理由：2 处确凿回退（§4.2）、3 处 S3 误拦、6 处 `V2_OVERRIDE` 自指词误判、`hard∧override/weak` 双标记被抹（§4.5）、S3 误拦随格式抖动（§4.3）。四条前置条件（只对白名单 3 域启用 / 先修 H5 管辖误判与 `V2_OVERRIDE` 自指词 / S3 不再无条件 fail-closed / 补齐逐处回归门槛并先影子 N≥3 轮）缺一即净损失。

### 5.4 ★ fail-closed 在全库尺度的质疑

**判断：全库尺度上 S3 DEFAULT 无条件 fail-closed 不合理；把「两 c07 域宁可误拦是对的」当作理由是归因错误。**

- 归因错误：两域 9 处 S3=0（§2.2）、32 域现盘 26 处 S3=0（§3.4a），两域收益**全来自 S0 HARD_V1**，与 S3 无关。
- 定量基础被修正：S3 真值 **17/47 = 36.2%，14 对 / 3 错**（不是 34/47=72.3%、31 对/3 错，`_vi_probe.py:160-162` 双计数，标 unconfirmed，见 §3.5）。故 `_vi_REPORT.md:300-315` 的论证方向成立但**定量基础失效**。
- 机制：`_v12_rule.py:20` 自述「判不了 → 默认 V2 + review_flag」「不静默放过、不假装能判」是诚实的，但真门禁若把 V2 直接当 FAIL，等于把「机器判不了」批量转成人工逐处复核队列；诚实 ≠ 可以无条件 fail-closed 生效。3 处误拦 + P09/P10 同型句一 V2 一 V1（C8）证明误拦不可预测。
- **建议（属改分类器本体，本会话未实施）**：S3 保留 `review_flag` 与「判不了」如实输出，但 verdict 回退到上一轨结论 + `NEEDS_HUMAN`；或至少限定「仅当 U 内无检索/标题/清单结构」才 fail-closed。C6 的 S3 回退模拟实跑：3 处误拦在 R10+R12 轨 2/3 已放过、在 N13 轨 3/3 放过（`N13_POS/P09 R10_problems=0, R13 problems=0`；`P15 R10_problems=1, R13 problems=0`；`TV3:L10 R10_problems=0, R13 problems=0`）；但 14 条应 CATCH 的 S3 命中里 `N13_NEG/N08`、`TV3:L8` 在纯 R10+R12 下会漏（需 R12/N13）。**方向合理但非无代价**，完整「回退上一轨」后果本会话未实测，标未验。

---

## 6 复核回件 + 安全插入方案 + 未验项

### 6.1 复核回件绑定行（被核对象 = 分类器本体）

被核对象 SHA256 = 15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0，字节数 = 9148

### 6.2 复核 verdict 如实记

**复核 verdict = partial → 按交付要求标 `unconfirmed`。** 复核回件原文要点（【复核】材料 `whatBreaksIt`）：9 件指纹 9/9、两域 9 处全 V1、全量影子对比 26/8/0、回退如实登记、未插真门禁/未改只读件全部独立复现通过；但「库内语料 S3 数字被 2× 重复计数（34 应为 17，31/3 应为 14/3，72.3% 应为 36.2%）」，且「消除误报 0 单元」与撰写人自己的「5 处纠错」矛盾，「净收益/净损失混用了三个不同基准」，故量化证据链不成立；核心结论方向（不建议插真门禁）仍成立。

本会话独立复核结果（C1–C8）与之一致：C3/C7 得 S3=17、C5 得 `eliminated_FP=5`、C4/C6 定位双计数源码，均复现；`_vi_REPORT.md:171-172,221,237,277,278,282,291-292,307` 涉及「34/47」「72.3%」「31 对/3 错」「消除误报 0 单元」「全库净损失」的数字与结论一律**标 unconfirmed**，本件 §3.5/§5.2/§5.3/§5.4 已给出修正值。复核回件另记 `_viv_hash.py` 全库 walk 跑满 120 s 未完成、已 TaskStop，标「未跑完」，本会话未重跑，不拿它当证据。

### 6.3 安全插入方案（仅方案，未实施）

**(a) 限定适用范围**：按 `(domain, tuple(banned))` **精确匹配白名单**，不在白名单**完全不调用 `classify_v12`**，保留原 R10/R12 结论；不改 `_v12_rule.py`、不改任何真门禁文件。

| 白名单域（3，已验收益） | `params.banned`（`_rj_delivery_baseline.json`） | 收益 |
|---|---|---|
| `lead/c07_slot_20261109/` | `['已补登','已填入','已填','已代填']` | 消 5 处 R10 断言误报（`_vi_shadow_out.txt:16-47`） |
| `lead/c07_truth_protocol_20261109/` | `['已填','已代填','已提交']` | 消 2 处（`:49-65`） |
| `lead/s604_script_hunt_20261109/` | `['已改','已删除','已清理']` | 消 1 处（`:207-213`） |

**明确排除**：任何使用 `DEFAULT_TOKENS=("已入账","已追加","已生效")` 或 `ASSERT_TOKENS` 五词的门禁族（C3/C5 实测 9 单元新增误报 + 2 单元回退）；以及 `n4_yi_final:155` 这类 `hard∧override` + 引证跨度内 `已签` 隐患域。

**(b) 回归门槛（逐处，不是只看总数）**：
1. `_v12_regression.json:224-229` 的 `v1_samples=22 / v1_pass=22`、`v2_samples=14 / v2_pass=14`、`mixed_pass=4 / mixed_total=4` 须保持 100%（`_v12_verify.py` 套件本会话**未重跑**，标未验）。
2. **2 处回退反例必须 CATCH**：`N13_NEG/N18`「本笔已入账 0 命中不得写成未入账」、`TV3:L12`「审阅不得不承认本候选已生效。」（当前 2/2 判 V1）。
3. **3 处 S3 误拦必须 PASS**：`N13_POS/P09`、`N13_POS/P15`、`TV3:L10`（当前 3/3 判 V2）。
4. **6 处检索/标题形态必须 PASS**：`N13_POS/P02,P03,P04,P05,P07,P16`（当前 6/6 判 V2，根因 `_v12_rule.py:36`）。
5. **32 域全量逐处对账**：26 处 `(pos,token,R10 kind,V12 verdict)` 与 `_vi_shadow_out.json` 一致，且 `RAW==R10`、基线指纹全匹配；任一漂移即停。
6. **同触双标记回报**：`hard∧override`（2 处）与 `hard∧weak`（9 处）须在输出里同时可见，修 `_v12_rule.py:143-146` 提前 return 抹标记问题。
7. **指纹门槛**：加载前 `hashlib` 验 `_v12_rule.py` = `15e421…`/9148、`_g7_predicates.py` = `02c17e…`/11743，失配拒绝运行（沿用 `_g9_gate.py:36-52` 范式）。

按 2/3/4，**当前 V12 在 11 条反例上全不达标 → 本评估不建议把分类器真正插入任何生产门禁**。

**(c) 先影子运行 N 轮（N≥3）**：每轮真实交付/复核回件跑 `_vi_shadow.py` 口径（读真文件、跑 R10 与 V12 两轨、只写本写域差分 json，绝不写回门禁件）；逐轮记录总命中、四象限、S3 触发数、`hard∧override/weak` 共触、单元级 FP/FN；停止条件 = 连续 N 轮 `新增误报=0 且 回退=0 且 S3 误拦=0`，任一轮出现「R10 判对而 V12 放过」的真断言立即停止并回 (b) 修分类器；每轮 `review_flag=True` 逐条人工裁决并回灌回归样本（只落本写域）；分级启用（先 3 域白名单，每次扩域前重跑全门槛）；开关做成单一配置，关闭即完全回 R10 轨。**以上步骤本会话均未实施。**

**(d) 分域结论（能否插）**：

- **现在可插（3 域，仅指影子差分已验、仍受 §6.3(b) 总闸门约束）**：`lead/c07_slot_20261109/`、`lead/c07_truth_protocol_20261109/`、`lead/s604_script_hunt_20261109/`。依据 `GATE_REJUDGE_32.md:91-99,116` 与 `_vi_shadow_out.txt:16-65,207-213`。
- **不能插 29 域**：
  - *有命中但零收益/有隐患 4 域*：`ledger_appendix_20261108`、`matrix_ab_ruling_20261109`、`n10c04_ruling_20261108`、`n4_yi_final_20261108`（R10 本就 0 assertion，V12 也 0 V2；后者 :155 有 2 处 `hard∧override` 与引证内 `已签` 隐患，`GATE_REJUDGE_32.md:111`）。
  - *零命中零收益 25 域*：`c07_gate_audit_20261109`、`c07_gate_fix_20261109`、`c07_protocol_attacks_20261109`(banned=[])、`counterpart_fix_20261109`、`f2d_rootcause_20261109`、`gate_fp7_20261108`(banned=[])、`gate_postmortem_20261109`、`gate_r9r12_20261109`、`handoff_pack_20261109`、`matrix_reach_20261109`、`matrix_row5_20261109`、`n11_dimmap_20261108`、`n11_wording_fix_20261108`、`o1prime_reach_20261109`、`pending_factpack_20261108`、`r11_f2_fix_20261109`、`s604_attribution_20261108`、`s604_exclusive_20261109`、`s604_script_gap_20261109`、`samedoc_link_20261109`、`strict_exposure_20261109`、`text_fix_unified_20261109`、`u5u6_mirror_20261109`、`v2_precision_fix_20261108`、`w2_samecause_20261109`（逐域见 §3.2）。
  - *词表层面跨档不能插*：`("已入账","已追加","已生效")` 与 `ASSERT_TOKENS` 五词的门禁族。
- ⚠️ **总闸门**：即使上表 3 域「现在可插」，在 §6.3(b) 门槛补齐并修掉 H5 管辖误判 / `V2_OVERRIDE` 自指词之前，**不建议把分类器真正插入任何生产门禁**；且编排方口径「10 个域」未给枚举，`_rj_findings.md:99` 标「10 域枚举未验」，本会话按 32 域全量跑。

### 6.4 未验项（如实登记，不补造）

1. `_v12_verify.py` 的 `V1 22/22、V2 14/14、MIXED 4/4` 回归套件**本会话未重跑**，仅实读 `_v12_regression.json:224-229`（C7 输出 `v1_samples=22 … mixed_total=4`），标**未验**。
2. 编排方 32 域实跑的 `v12_api` 列表与 `err:""` **未独立重放其原始脚本**（该脚本未在本次可读件里）；本会话用 `_vi_shadow.py` / `_viv_shadow_own.py` 从同一 baseline + 同一两个谓词模块独立重算，逐处一致。
3. C3 的 `expect` 采用库内既有标注（`_n13_regression.py` 的 POS/NEG 分类、`_g7_tv3_double_negation.md:10` 括注「应豁免」、`_g7_reverse_validate.py:101,119` 的期望），**本会话未另请人复核语义**，标「采用库内既有标注」。
4. 「S3 verdict 回退上一轨 + NEEDS_HUMAN」的完整后果未实测：仅跑 C6 的 3 处误拦点模拟（`N13_POS/P09 / P15 / TV3:L10`），14 条应 CATCH 的 S3 命中在回退后的整体漏放率**未验**。
5. `_vi_probe.py` v1/v2 历史版本数字（自造词表 S3=20 / import 污染 stdout）**未采**，仅采 v3；复核回件 `_viv_hash.py` 全库 walk 跑满 120 s 未完成，本会话未重跑，标**未跑完**。
6. 编排方 `domainsWithHits:30` 字段名与实测「7 域有命中」不符（30 实为扫描域数，2 个 `banned=[]` 域未出现在其 rows 中），本会话按实测 7 报告。
7. §6.3(a)–(c) 全部是**方案、未实施**；未改 `_v12_rule.py`、未改任何真门禁、未改 32 写域、未改两台账；本任务「绝不把 V1/V2 分类器插进任何真门禁」已遵守，所有脚本只读既有件，输出只落 `lead/v12_impact_20261109/`。
