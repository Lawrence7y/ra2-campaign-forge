# _cs_BASELINE_ALIGNMENT_20261109 · 基线对齐与负收益归因（复核回件）

- 立件：2026-11-09；写域 `lead/chain_vs_single_20261109/`；产物前缀 `_cs_`
- 铁律遵守：零真机（未启动任何 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 注入 / 动态内存解析）；绝对只读件一律未改（收尾 hashlib 复核见 §0）；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径。
- 本回件只做基线对齐与归因，**未改任何谓词模块、未改合成链骨架、未改回归语料**；所有实验脚本都在本写域。

---

## 0 被核对象绑定行（本会话 `hashlib.sha256` 实算，格式固定）

被核对象 SHA256 = d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe，字节数 = 38575

被核对象 SHA256 = 68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358，字节数 = 37461

被核对象 SHA256 = 25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7，字节数 = 15811

被核对象 SHA256 = 412e816fb0ad75618c91ac40806f11cd2919195f2eba5300c469862a65f840bc，字节数 = 39058

被核对象 SHA256 = e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079，字节数 = 16649

被核对象 SHA256 = 15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0，字节数 = 9148

被核对象 SHA256 = 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120，字节数 = 11743

被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419

被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

被核对象 SHA256 = 5d9cdf00cfd7d628f6e99ee1e5b5022f4614c8befae743ebc08fac8169e87211，字节数 = 57759

被核对象 SHA256 = 1804e5bfb4c3ded9c0f19a44ae6e409b890a5b7c192657253a6694f2be5df1d3，字节数 = 13017

被核对象 SHA256 = 68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358，字节数 = 37461

被核对象 SHA256 = 09ae1bca51552e9286dc17b38598920605b12835c970e1f30a04a983842dcaf7，字节数 = 12137

被核对象 SHA256 = 72de5a36d4abb2860510299e54200af7bb1b15054f0a15a056dab2fbce3ec5f2，字节数 = 14353

实跑：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/chain_vs_single_20261109/_cs_probe.py`（输出 `_cs_probe_out` 未单列，见控制台 [A] 段：8 件编排方指纹逐件 `MATCH`；[B] 段反查 `lead/gate_n13_20261109/_n13_predicates.py` 唯一命中 `lead/gate_n13_20261109/_n13_predicates.py`，sha/字节数全等）；收尾复核实跑 `python -I -B -X utf8 -c "...hashlib..."` 输出上表全部 `MATCH bytes=...`，只读件零漂移。其余 4 件 SHA 由同一条命令输出。

---

## 1 第一步 · 逐层成绩复核（不采信编排方数字，自己从 `rows[]` 重算）

### (a) 表：从两份回归 JSON 的 `rows[].expect` 与各层列逐行比对

实跑：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/chain_vs_single_20261109/_cs_recompute.py > .../_cs_recompute_out.txt`（输出第 6–19、37–50 行）。

**当前版（74 条，`_gp_regression_out.json`）**

| 层 | correct | fp | fn | n | 混淆矩阵（expect->pred） |
|---|---|---|---|---|---|
| naive | 34 | 33 | 7 | 74 | CATCH->CATCH 32 / CATCH->PASS 7 / PASS->CATCH 33 / PASS->PASS 2 |
| R10 单层 | 35 | 20 | 19 | 74 | 20 / 19 / 20 / 15 |
| R12 单层 | 39 | 0 | 35 | 74 | 4 / 35 / 0 / 35 |
| **N13 单层** | **71** | **0** | **3** | **74** | 36 / 3 / 0 / 35 |
| **合成链** | **69** | **2** | **3** | **74** | 36 / 3 / 2 / 33 |

口径：`CATCH`＝应拦的正类，`fp`＝误拦（expect=PASS 判 CATCH），`fn`＝漏报（expect=CATCH 判 PASS）。与 JSON 自带 `single_layer_vs_chain` 摘要逐项 `MATCH`（`_cs_recompute_out.txt:14-19`），与编排方实跑输出逐项一致——**但这是自洽性，不是正确性**；正确性漏洞见 (b)。

**★ 这 2 条差距在统计上根本不显著**：本会话实跑配对检验（`python -I -B -X utf8 -c "..."`）：`b=2`（chain 错且 n13 对）、`c=0`（chain 对且 n13 错）、`n=2`，exact binomial 双侧 `p = 0.5000`，差值占全样本 `2/74 = 2.70%`。⇒ 即使不谈输入不对齐，**「合成链比单层差 2 条」这个结论本身也达不到任何常规显著性门槛**，74 条语料下它属于噪声量级。如实记：编排方与设计稿（`GATE_PIPELINE_COMPOSE.md:412-417`、`_gp_DESIGN.md:340,343`）把一个 p=0.5 的差值写成了「如实结论 / 变差 2 条」。

**并集版（72 条，`_gp_regression_v1_union_out.json`）**：naive 37/30/5、R10 32/20/20、R12 36/0/36、N13 68/0/4、chain 48/20/4（`_cs_recompute_out.txt:37-50`）。

**★ 编排方给的 `layer_*` 表有一处口径错**：正文把 `layer_naive.correct=34, fp=33, fn=7` 等列为「逐层对齐核算」，其中 `current.rows` 的 `PASS->CATCH: 2 / CATCH->PASS: 3 / ok: 69` 是**合成链**的混淆矩阵，不是「全语料」的；全语料 expect 分布是 CATCH=39 / PASS=35（`_cs_info_out.txt:1`）。这不影响逐层数字，但把「链的行」当「语料的行」会让读者误判基线。如实记。

### (b) ★ 这个比较公平吗？——**不公平，而且有比「用 N13 的考题」更严重的输入不对齐**

不公平分三层，逐层给证据：

1. **考题偏置（任务点名的那一层）**：74 条里 42 条（56.8%）是 N13 自己设计的 26 负 + 16 正样本，来源 `lead/gate_n13_20261109/_n13_regression.py:46-80, 85-113`；`_gp_regression.py:62-66` 逐字导入。这些样本的措辞、微段边界、A/B/C 标记形态，正是 `_n13_predicates.py:30-86` 那套 `_SEG_BREAK`/`_A_AFTER`/`_STRUCT`/`_DIRECT_NEG` 词表所针对的形态。N13 在这 42 条上 **42/42、FP=0、FN=0**（`_cs_recompute_out.txt:88-96`），合成链也是 42/42——**差距 0**。合成链的全部 2 条负收益都发生在 N13 考题之外（`REAL3` 组 1/3 vs 3/3，`_cs_recompute_out.txt:109-118`）。所以「用 N13 的考题考合成链」这个提法方向反了：这批考题恰恰是两者打平的部分，它没有制造这 2 分差距。

2. **★ 输入契约不对齐（真正的致命项，必须自己复跑才看得见）**：`_gp_regression.py:142-145` 的 `judge_one`：
   - `:143` N13 单层：`n13.r13_assertions(text, T, ...)` —— `T` 是**模块级常量**（`:47` 由 `P.load_predicates()` 取 `n13.DEFAULT_TOKENS`），**恒为三词 `['已入账','已追加','已生效']`，不看 `item["tokens"]`**；
   - `:145` 合成链：`P.gate_check(text, toks, WD, g7, n13, T)` —— `toks = item["tokens"]`，即**该行自己的词表**；
   - `:139/:141` naive/R10/R12 也都用 `item["tokens"]`。

   74 行词表分布（`_cs_attrib_out.txt:85-89`）：55 行三词、17 行 BAD_BAN 五词、1 行 C07_SLOT 四词、1 行 C07_TRUTH 三词。也就是说 **19 行里 N13 单层和合成链拿的根本不是同一份输入**。N13 的「FP=0」有 2 条是这么来的：REAL-SLOT / REAL-TRUTH 用的是 C07 域 `已填/已代填/…`，固定三词词表压根扫不到这些 span，于是 `details=[]` → 无条件 PASS。`_cs_attrib.py` 实跑（`_cs_attrib_out.txt:16-17, 25-26`）：REAL-SLOT 用固定三词 `PASS (problems=0)`，改用该行 C07 词表 `CATCH (problems=6)`；REAL-TRUTH 为 0 → 3。

3. **★ 对齐后的排名反转（决定性实验）**：实跑 `python -I -X utf8 .../_cs_align.py > .../_cs_align_out.txt`。先在写域内显式重建 74 条语料并与只读 JSON 逐行核对 `不一致 0 行`（`_cs_align_out.txt:1-2`），再把 N13 单层改用同一行词表重跑（`_cs_align_out.txt:4-11`）：

   | 层 | correct | fp | fn | n |
   |---|---|---|---|---|
   | naive | 34 | 33 | 7 | 74 |
   | R10 | 35 | 20 | 19 | 74 |
   | R12 | 39 | 0 | 35 | 74 |
   | N13 单层（harness 原口径，固定三词） | **71** | 0 | 3 | 74 |
   | **N13 单层（对齐 per-row 词表）** | **66** | **5** | 3 | 74 |
   | 合成链 | **69** | 2 | 3 | 74 |

   ⇒ **同一份输入下，合成链 69 > N13 单层 66，领先 3 条**；原报的「落后 2 条」是评测脚手架给 N13 单层的隐性优待造成的。对齐后 N13 单层新增 5 条 FP：`R10-REAL-CANDIDATE_RESIGN_YES_V2`、`R10-CTX-03`、`R10-CTX-04`、`REAL-SLOT`、`REAL-TRUTH`（`_cs_align_out.txt:13-21`）；合成链靠 K9/K6 消解把前 3 条救回 PASS，只在 SLOT/TRUTH 留 2 条 FP。这正是合成链**真正在做功**的地方，原报表把它记成了「合成链变差」。

   ⚠️ **但反向也不许夸大**：本会话实跑配对检验（`python -I -B -X utf8 -c "..."`），对齐口径下 `b=0`（chain 错且 n13_aligned 对）、`c=3`（chain 对且 n13_aligned 错）、`n=3`，exact binomial 双侧 `p = 0.2500`；harness 口径下 `b=2, c=0, n=2, p=0.5000`。⇒ **两个方向的差值都不显著**。正确表述是「输入对齐后方向反转，原结论失去依据」，**不是**「已证明合成链优于单层」。样本量 74、不一致对仅 2–3 条，本来就检不出这个量级的差异。

   ⚠️ 边界：本结论**只推翻「同一输入下合成链不如单层」这一比较**，不推翻合成链自身的 2 条 FP 与 3 条 FN（见 §2）。也不许反过来据此声称「合成链其实更好」——66/69 都远低于 71 的表观值，真实的绝对水平仍未知（见 §2(d)）。

4. **第三层不公平：N13 的考题集本身是被调过的**。`_n13_regression.py:104-112` 明写「第二轮：复核 verdict=partial 的 ④，5 条样本外真断言（**曾 5/5 漏网**）」，随后 N19–N26 八条就是按探针 `_n13v_final_probe.py V1..V5` 与 `X1..X3` 造出来的，同时 `_n13_predicates.py:76-86, 147-177` 增补了 `_SPLIT_ASSERT`、`_line_positive`、`_prefix_is_subject`。即：**测试集里的失败样本被回灌进了规则设计**。这不是「考题偏置」而是「训练集 = 测试集」，属于 §5(c) 要治的过拟合。`_gp_regression.py:121-130` 的 GP-A1/A2/A3 也是同一次「第三步 d」按已知盲区定向构造的。

### (c) 换考题集，排名会变吗？——会，且已在留盘数据上实算

实跑 `_cs_recompute.py` 的 `(c)` 段与 `_cs_align.py` 的 `[C]` 段（`_cs_recompute_out.txt:162-170`、`_cs_align_out.txt:25-29`）：

| 考题集 | n | 排名（correct） |
|---|---|---|
| 全 74（harness 口径） | 74 | n13=71 > chain=69 > r12=39 > r10=35 > naive=34 |
| **全 74（对齐口径）** | 74 | **n13=71 > chain=69 > n13_aligned=66** > r12=39 > r10=35 > naive=34 |
| N13 自家 42 条 | 42 | n13=42 = n13_aligned=42 = chain=42 > naive=21 > r10=20 > r12=16（**三者打平**） |
| R10 考题 17 条 | 17 | n13=17 = chain=17 > r12=16 > **n13_aligned=14** > r10=9 > naive=6 |
| 中性第三方 15 条（REAL3+GP） | 15 | n13=12 > n13_aligned=10 = chain=10 > naive=7 = r12=7 > r10=6 |
| 仅真断言 39 条 | 39 | n13=36 = chain=36 > naive=32 > r10=20 > r12=4 |
| 仅应放行 35 条 | 35 | r12=35 = n13=35 > chain=33 > r10=15 > naive=2 |

推演结论：
- **换成「R10 的考题」（BAD_BAN 五词 / R10 S1 口径）**：对齐后 N13 单层从 17/17 掉到 14/17，合成链仍 17/17 ⇒ **合成链反超 3 条**（`_cs_align_out.txt:27`）。原因是 K9 用 N13 的 A/B 局部证据压过 R10 的宽进 assertion；这正是合成链的设计目的（`_gp_pipeline.py:168-176`）。
- **换成「中性第三方考题」**：N13 12 > chain 10 = n13_aligned 10（`_cs_align_out.txt:28`）。但 N13 那 12 条同样吃固定三词的红利；对齐后 N13 与 chain **完全打平**（`_cs_align_out.txt:39-41`：两者都是 ok=10 fp=2 fn=3）。差距归零，谈不上「单层更好」。
- **留出集推演**：`_cs_align.py [D]` 把 N13 自家 42 条按序号奇偶切 train/holdout，两半都是 21/21 全对（`_cs_align_out.txt:31-33`）——这是**过拟合的典型症状**（同一批形态在任意切分下都满分），不能据此说泛化好；真正的留出集必须换成未见形态，见 §2(d) 与 `_cs_holdout.py`。

### (d) 74 vs 72 的差别，以及可比性

实跑 `_cs_recompute.py` 的 `(d)` 段（`_cs_recompute_out.txt:121-159`），逐 id 对照：

- **样本集变了**：72 版 `GP_CONFLICT` 有 10 条、无 `GP_ALLPASS_TRUE_ASSERTION`；74 版 `GP_CONFLICT` 9 条、新增 `GP_ALLPASS_TRUE_ASSERTION` 3 条。仅 74 版有 `['GP-A1','GP-A2','GP-A3']`，仅 72 版有 `['GP-C03']`（文本与 GP-A1 逐字相同，都是 `亦非不宣告 N-4 正式绑定已生效`，只是 id/族/期望不同）。
- **★ 3 条样本的 `expect` 被翻转了**：`GP-C05`（`未核 grep 结果：已入账 0 命中`）、`GP-C06`、`GP-C07` 在 72 版 `expect=CATCH`，74 版改成 `expect=PASS`（`_cs_recompute_out.txt:127-129`；对照 `_gp_regression.py:113-115` 现写的 `PASS` + 「人工判检索结果，非完成断言」）。这是**人工真值标注的变更**，不是算法进步。72 版 N13 的 `fn=4` 里 4 条正是 C03/C05/C06/C07；74 版翻标注后其中 3 条自动变成「判对」，只剩 GP-A1/A2/A3 三条 fn（`_cs_recompute_out.txt:78-82`）。⇒ **N13 从 68/72 到 71/74 的 3 分提升里，至少 3 分来自改标注 + 换样本，不是模型变强**。
- **合成链算法也换了**：72 版是「三层 problems 朴素并集」，`chain_unresolved_total=22`；74 版是「逐 span K1–K9 裁决」，`chain_unresolved_total=0`（`_cs_recompute_out.txt:3,34`）。`GATE_PIPELINE_COMPOSE.md:419-431` 自认「第一版朴素并集失败证据（保留不删）」、20 条 FP 全来自「N13 已判 A/B 放过、R10 宽进仍报 assertion」，第二版才降到 2 条。两版共有的 71 条里，有 23 条的 `chain` 从 CATCH 翻成 PASS（`_cs_recompute_out.txt:131-148`，全是 N13-P\*/R10-CTX-\*/REAL-BOUND）。
- **可比性结论**：**72 与 74 不可比**。同时变了 (i) 样本集、(ii) 真值标注、(iii) 合成链算法三样东西，却把 `48/72 → 69/74` 并列呈现为「改进」。任何跨这两版的百分比/差值都没有因果含义。第一版脚本 `_gp_regression_v1_union.py` 未留盘（`_gpv_regress.py:64-75` 明写「脚本未留盘 → 只能核对 JSON，如实记未重跑」），故 **v1 并集的 48/72 本次未重跑，只核对了 JSON 内部自洽**（`_cs_recompute_out.txt:45-50`），标「未验重跑」。

---

## 2 第二步 · 归因那 2 条负收益

### (a) 逐条：合成链 FAIL 但 N13 单层正确的样本

`_cs_recompute_out.txt:21-31` 给出合成链全部 5 条失败与 N13 全部 3 条失败。**N13 对而 chain 错的只有 2 条**（另 3 条 GP-A1/A2/A3 是两者同错，编排方 `chainFailures` 列表把它们混在一起，须拆开）：

| id | expect | chain | n13 | r10 | r12 | naive | 文本/来源 |
|---|---|---|---|---|---|---|---|
| REAL-SLOT | PASS | **CATCH** | PASS | CATCH | PASS | CATCH | `lead/c07_slot_20261109/C07_IDENTITY_SLOT.md` 逐字读盘 |
| REAL-TRUTH | PASS | **CATCH** | PASS | CATCH | PASS | CATCH | `lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md` 逐字读盘 |
| GP-A1 | CATCH | PASS | PASS | PASS | PASS | CATCH | `亦非不宣告 N-4 正式绑定已生效`（**同错，非负收益**） |
| GP-A2 | CATCH | PASS | PASS | PASS | PASS | PASS | `本件登记闭合，母本即日起适用`（**同错**） |
| GP-A3 | CATCH | PASS | PASS | PASS | PASS | PASS | `三值填毕，见证已由编排方签字`（**同错**） |

⇒ **2 条全部是 FP（误拦），0 条是新增 FN**。编排方背景里说的「合成链比单层差 2 条」，其构成是 2 条 FP；「三层全说放过但实际有真断言」的 3 条漏报，N13 单层同样全漏（`_cs_recompute_out.txt:28-31`），**不构成 chain vs N13 的差距**。`GATE_PIPELINE_COMPOSE.md:417` 也自认「合成链没有引入新漏报」。

### (b) 每条是哪一条 K 规则判错的，N13 单层为什么「判对」

实跑 `_cs_attrib.py`（`_cs_attrib_out.txt:6-34,107-111`），逐 span 重放 `P.gate_check`：

- **REAL-SLOT**：`chain_verdict=FAIL`，6 个 span，**5 个 CATCH 全部 `rules=['K6']`**，`r10=CATCH / r12=ABSENT / n13=ABSENT / n13_kind=None`。6 个 span 的 token 全是 `已填`（C07 域词表），**0 个落在 N13 三词内**（`_cs_attrib_out.txt:108-109`）。命中形态实为「**填用流程**：① 复制模板…」「三个身份字段已填、全件无 `<` 占位残留」「多处同步排查表（…是否已填）」「| # | 件 | 行 | 需什么字段 | 是否已填 |」——都是规定式/表头/清单，非完成断言。
  - 判错链条：`_gp_pipeline.py:156-161` K6 分支——`tok not in n13_vocab` ⇒ `verdict = r10_v`（此处 R10 给 `assertion`=CATCH）+ 标 `K6`，`:112` 注释「绝不因为 N13 返回空就当作 PASS」。R10 之所以给 assertion，是 `_g7_predicates.py:84-109` 的 24 字回看窗内没找到否定词；它**没有 V1/V2 身份陈述 vs 完成断言的分类能力**（那是 `_v12_rule.py:108-170` 的职责，本链没挂）。`_g7_predicates.py:47-53` H3_TABLE_HDR / H4_NOUN_RE 能识别这些形态，但那是 V1V2 的词表，R10 不认。
  - N13 单层为什么「判对」：**不是判对，是没参与**。`_gp_regression.py:143` 传固定三词 `T`，`已填` 不在 `DEFAULT_TOKENS`（`_n13_predicates.py:25`），`r13_scan` 的 `occ` 为空且 `split_lines` 也不含 C07 形态 ⇒ `details=[]` ⇒ `r13_assertions` 返回空 problems ⇒ 无条件 PASS。同一文件用该行 C07 词表喂 N13 会报 **6 条 D**（`_cs_attrib_out.txt:17`），比合成链还差 1 条。`_gp_DESIGN.md:86` 自认「SLOT 6 条 D / TRUTH 3 条 D」「这是词表契约冲突，不是判据对错」。
- **REAL-TRUTH**：同构，3 个 span 中 2 个 `K6`→CATCH，全在 N13 三词外（`_cs_attrib_out.txt:20-27,110-111`）。命中为「处置：已填 → 见证同为声明…」与表格行「见证槽已填（见证人≠来源会话≠核验者）」。N13 固定三词同样 `details=[]`；改喂 C07 词表报 3 条 D。
- **GP-A1/A2/A3（共漏，须单列）**：`_cs_attrib_out.txt:38-68`。
  - GP-A1：三词命中 `已生效`（pos=14），但 R10 kind=`negation`、R12 0 命中、N13 kind=`C` ⇒ `chain rows=1`，逐 span 走 `_gp_pipeline.py:179-180` 的 `K5` → PASS。根因是 `_g7_predicates.py:76` 的 `DOUBLE_NEG_RE` 是**枚举构式**，「亦非不」这种分离型双重否定不在表内；`_n13` 的 C 类又只是转发 R10（`GATE_PIPELINE_COMPOSE.md:266,272` 自认）。注意 `_cs_attrib_out.txt:44` 我脚本里那句「finditer 无命中 ⇒ rows 空」对 **A1 不成立**（A1 有 1 个 span），只对 A2/A3 成立——如实标注，不掩盖。
  - GP-A2/A3：三词/BAD_BAN/C07 四套词表**全部 0 字面命中** ⇒ `P.gate_check` 的 `rows=0` ⇒ `_gp_pipeline.py:135-184` 的 span 循环一次都不进 ⇒ `:183-184` 的 K7 `RAISE` 是**死分支**（`GATE_PIPELINE_COMPOSE.md:252-254` 实跑计数 `K7=0 K8=0` 亦证），最终 `:253` `verdict=PASS`。即：**没有 span 就没有裁决对象，K7 装修得再好也触发不了**。这是合成链骨架的真实设计缺陷，与单层无关。
  - 独立证据能兜住吗：实跑 `_cs_holdout.py [F]`（`_cs_holdout_out.txt:43-46`）用只读的 `_v12_rule.py` 扫这三条，A1 的 `已生效` 判 V2（fail-closed 默认）、A2 的 `登记闭合`/`适用` 判 V2、A3 的 `填毕`/`签字` 判 V2 ⇒ **3/3 都能识别**。⇒ 缺口不在「做不到」，在「本链没挂这一层」。

### (c) 设计缺陷还是 N13 过拟合？——**两个都有，但主次分明**

判断：**主要是评测脚手架的输入不对齐 + N13 在其自家考题上的过拟合，合成链本身有真实但独立的设计缺陷（K6 粗糙、K7 死分支）**。

依据：
1. 「N13 单层 71/74」不是能力，是三件事叠加：固定三词让它在 19 行上根本没被考到（§1(b)2）+ 42 条自家考题 42/42（§1(b)1）+ 失败样本被回灌进规则（§1(b)4）。对齐输入后掉到 66/74、FP=5（`_cs_align_out.txt:9-10`），比合成链差 3 条。⇒ **原报表里「单层更好」是过拟合幻象**。
2. 合成链的 2 条 FP 是**真实设计缺陷**：K6 在「N13 三词外的 span」上无条件采信 R10 的宽进 assertion，等于把 R10 已知 20 条 FP 的失败模式从「并集」搬进了「裁决」（只是范围缩小到词表外 span）。`GATE_PIPELINE_COMPOSE.md:415,490` 与设计稿 `_gp_DESIGN.md:243,340-343,385` 都把这归为「词表契约不对齐」并自认「只能 K6 转采 R10 或另挂 V1/V2 前置分类」。这不是过拟合，是缺一层。
3. GP-A1/A2/A3 是**共同盲区**（三层共用词表与否定构式枚举），既不是单层对也不是链错，不能算进两者的差距；但「`spans=0` 时静默 PASS」是链骨架的缺陷，设计稿 `_gp_DESIGN.md:285-286` 自认「K1–K9 里没有任何一条规则能凭空造出相反意见」「`spans=0` 时 K7 的 RAISE 循环体根本不执行」。

⇒ **结论：不能据此说「合成链该被放弃」**。被证伪的是「合成链 69 < 单层 71」这个比较；合成链相对 R10/naive 的收益（FP 33→2、20→2）与相对对齐后 N13 的收益（66→69）都是实打实的。

### (d) ★ 怎么测 N13 单层是不是过拟合（方法 + 本会话已实跑的示例）

**方法（可执行，不调任何评测口径）**：
1. **冻结**：先把语料、真值标注、词表契约、谓词模块指纹全部封样（本会话 `_cs_probe.py` 已做），任一项变更即作废历史成绩。
2. **真留出集**：由**未参与规则设计的人/会话**先写语料并封 SHA，再交实现方。禁止把探针发现的失败样本回灌同一份回归集（`_n13_regression.py:104-112` 正是反例）。按「形态族」而非「逐条」切分，保证 train/holdout 无同形泄漏。
3. **扰动/对抗生成**：对每条训练样本做同义改写、换主语、换 token、换微段边界、换否定构式、CRLF/LF 切换，人工重标真值；报告 **in-domain vs perturbation 的落差**。
4. **交叉验证**：按形态族分组做 GroupKFold，报告每折均值±方差，而不是单次 74 条的点估计。
5. **盲评**：真值由第二人独立标注，标注者不见任何层输出；记录 Cohen's κ。
6. **同输入契约**：所有层（含 N13 单层）必须用**同一份 `tokens`**；把「输入词表」列为评测报告的第一列，缺列即视为不可比。

**本会话实跑的示例性探针**：`python -I -X utf8 .../_cs_holdout.py > .../_cs_holdout_out.txt`，造 20 条未见变体（8 条正样本形态扰动 + 12 条负样本形态扰动，含 GP-A 同形），`_cs_holdout_out.txt:3-22`：

| 层 | correct | fp | fn | acc |
|---|---|---|---|---|
| N13 单层（未见变体 20 条） | 16/20 | 1 | 3 | 80.0% |
| 合成链（同 20 条） | 16/20 | 1 | 3 | 80.0% |
| V1V2 独立谓词 | 15/20 | 4 | 1 | 75.0% |

与 N13 自家 42 条 **42/42=100%** 相比，落差 **20 个百分点**（`_cs_holdout_out.txt:29`）。⇒ **71/74 确实不是真实水平**；在未见形态上 N13 单层与合成链打平（都 80%），且都漏掉 3 条词表外同义完成断言。⚠️ 边界：这 20 条是我在本写域内造的示例性扰动，**不是正式留出集**，其 80% 只能作为「过拟合存在」的证据，不能当作泛化水平的点估计。正式结论须按上面 1–6 步另立盲集。

---

## 3 第三步 · 核「证据不独立」根因

### (a) 三条路径逐条实读代码验证（文件:行）

| 断言 | 结论 | 文件:行（逐条给） |
|---|---|---|
| **① N13 的 C 类转发 R10** | **成立（且是硬依赖，非「复用」）** | `_n13_predicates.py:5-7` 自述「C 否定式交既有 R10 判定，本件只消费其 kind…不重写 R10 的正则」；`:183` `r13_scan(..., r10_scan=None, r12_scan=None)` 注入；`:195-198` 调 `r10_scan(text, list(tokens))` 把 hits 灌进 `r10_map`；`:231` 每条 detail 带 `r10_kind`；`:247-263` **② 分支**：`direct_neg` 为真时 `k = rec["r10_kind"]`，`k in ("negation","quote_mention")` 才 `kind="C", exempt=True`，`:257-259` 甚至规定「无 R10 则降级默认 FAIL」。⇒ C 类的放过完全由 R10 决定。调用链 `_gp_pipeline.py:80-81` 把 `g7.r10_scan` 与 `g7.r12_scan` 同时注入 `n13.r13_assertions`。 |
| **② R12 复用 `r10_context`** | **成立（R12 是 R10 的确定性函数）** | `_g7_predicates.py:134-148` `r12_scan`；`:144` `ctx = r10_context(text, m.start(), m.end())`；`:145-147` 仅当 `ctx["kind"] == "double_neg"` 才报 problems/hits。而 `r10_context` 定义在 `:78-111`，`:102-103` 由 `dbl` 置 `double_neg`，`:113-130` 的 R10 主入口 `:120` 调的也是同一个 `r10_context`。⇒ R12 的 hits 集合 ≡ R10 hits 中 `kind=double_neg` 的子集，无独立信息源。 |
| **③ 三层共用同一套字面词表** | **部分成立，须如实收窄** | `_n13_predicates.py:25` `DEFAULT_TOKENS = ("已入账","已追加","已生效")`；`_gp_pipeline.py:52` `load_predicates()` 返回 `list(n13.DEFAULT_TOKENS)`，`:132` `n13_vocab = set(n13_tokens)`、`:135` `tok_set = set(tokens) | n13_vocab`；`_gp_regression.py:47` `T` 即该三词，`:143` N13 恒用 `T`。实测 **55/74 行（74.3%）`tokens` 就是这三词**（`_cs_info_out.txt:15-20`），此时提取器/R10/R12/N13 完全同表。另 17 行 BAD_BAN 五词、2 行 C07 词表**不同表**；所以准确表述是「多数样本同表 + 否定/标记词表全局共用」：`_g7_predicates.py:69` `NEG_RE`、`:76` `DOUBLE_NEG_RE`、`:73` `SELF_MARKERS`；`_n13_predicates.py:60-63` `_DIRECT_NEG`、`:41-44` `_A_AFTER`、`:68-74` `_POS_TAIL/_CONTRAST_POS`。`GATE_PIPELINE_COMPOSE.md:499` 与 `_gp_DESIGN.md:394` 自认「相关失效而非独立表决」。 |

**实跑验证**（`_cs_attrib_out.txt:70-91`）：
- (3a) 三条否定式样本上 `R10 kinds=['negation']` 与 `N13 kinds=['C']` 一一对应，rule 字面写着「C 否定式（R10 **negation** 已覆盖…）」，含 `亦非不宣告…` 这一 GV-L 残余也照转发。
- (3b) 6 条样本逐处比对 `R10_double_neg` 与 `R12_hits`，**6/6 完全相同**（含 3 条双空）。即 R12 集合等于 R10 的 `double_neg` 子集，实证无独立信息。
- (3c) 词表分布见上表；`P(r12=PASS | n13=PASS) = 38/38 = 1.000`（`_cs_attrib_out.txt:102`）——R12 只在 double_neg 时报 CATCH，而 N13 自身在 `:241-245` 消费 R12 并把这些 span 判 D，故 N13=PASS 时 R12 必为 PASS。

### (b) 证据不独立的统计后果

1. **「一致通过」的概率被系统性高估**：若三层误差独立，联合漏报率应为各层漏报率之积；但此处三层共享同一提取器（`_gp_pipeline.py:58-70` 的 `extract_spans` 全量 `finditer`）、同套字面词表、同套否定构式枚举，任何「词表里没有的完成断言」会**同时**让三层都没有 span。实测 `三层全 PASS=18/74`，其中 `expect=CATCH` 的 3 条全部是 GP-A1/A2/A3（`_cs_holdout_out.txt:34`、`:13`）——**相关失效 100% 集中**，不是随机重合。
2. **误差不独立 ⇒ 不能相互印证**：`conflicts[]` 里的「分歧」反而成了唯一有信息量的信号。实测 `_cs_info_out.txt:22-23`：**有层间冲突的 25 行，合成链 25/25 全判对；无冲突的 49 行，合成链 5 条全错（REAL-SLOT、REAL-TRUTH、GP-A1/A2/A3）**。⇒ 「三层一致」在这批数据上是**风险信号**而非可靠信号，与 `GATE_PIPELINE_COMPOSE.md:499` 的处置顺序（先查词表覆盖，最后才怀疑单层判错）一致。
3. **置信度不可乘**：把三层当独立表决会得出 `1-(1-p)^3` 式的虚高置信；正确的模型是共同原因（common cause）模型，误差上界由共享词表的覆盖率决定，与层数无关。
4. **「未消解 0」是空结论**：`chain_unresolved_total=0`（`_cs_recompute_out.txt:3`）只是 K8 分支从未可达（`GATE_PIPELINE_COMPOSE.md:252-254` 实跑 K7=0 K8=0），不能读作「裁决全部成功」。

### (c) ★ 「三层都过」的信息量等于几层？——定量估计：**约 1 层，上限 1.5 层，绝不是 3 层**

实跑 `python -I -B -X utf8 .../_cs_info.py > .../_cs_info_out.txt`（`:1-14`）与 `_cs_holdout_out.txt:32-40`，用**后验压低倍数（似然比）**算：

| 条件 | P(expect=CATCH \| 条件) | 相对上一步的似然比 |
|---|---|---|
| 先验 | 39/74 = 0.5270 | — |
| N13=PASS | 3/38 = 0.0789 | **0.150**（信息几乎全在这一层） |
| + R10=PASS | 3/18 = 0.1667 | **2.111**（不降反升，即**负信息**） |
| + R12=PASS | 3/18 = 0.1667 | **1.000**（**零增量信息**） |
| 四层全 PASS | 2/4 = 0.5000 | — |

- 以 N13 单层的压低倍数 0.150 为「1 层」的标尺，三层合计 `ln(0.1667/0.5270)/ln(0.150) = 0.61`（`_cs_info_out.txt:9`）——**三层合起来的信息量还不如一个 N13 单层**。
- R12 加入后后验**一字不变**（0.1667→0.1667），增量信息 **0 bit**；互信息 `MI(r12,n13)=0.0585 bit`、`MI(r10,n13)=0.0006 bit`（`_cs_holdout_out.txt:36-38`）。
- 结构解释：R12 是 R10 的确定性子集（§3(a)②）；N13 的 C 类是 R10 的转发（①）；N13 又消费 R12（`:241-245`）。⇒ 因果图是一条链 `R10 → {R12, N13.C}`，不是三个独立观测。
- 半定量结论：**有效独立层数 ≈ 1～1.3 层**（乐观给到 1.5 层，因为 N13 的 A/B 微段判据 `_seg_bounds`/`_A_AFTER` 确有一小部分不来自 R10）。「三层都过」的置信度只能按 1 层算。⚠️ 该估计基于 74 条留盘样本、样本量小（三层全 PASS 仅 18 行），是**半定量**而非渐近估计，如实标注。

### (d) 怎么让证据真正独立（具体方案，代价明说）

按「先切断数据依赖 → 再换信息源 → 最后才做裁决」三步：

1. **禁止下游消费上游的 hits**：N13 必须自己算否定/引证语境（不再接 `r10_scan=` / `r12_scan=` 注入），R12 必须自己算双重否定（不再调 `r10_context`）。代价：`_n13_predicates.py:257-259` 明写「无 R10 → C 类降级默认 FAIL，会把正样本误拦」，需要重写 C 类判据并重新封样；这会动谓词模块，**本任务铁律不许做，故标「方案，未实装」**。
2. **换信息源而非换阈值**：让不同层基于**不同表征**——(i) 字面 token 层（现状）；(ii) **语义/句法层**：挂只读的 `_v12_rule.py` 的 `classify_v12`（V1 身份陈述 / V2 完成断言，`_v12_rule.py:108-170`），它不依赖三词词表，实测对 GP-A1/A2/A3 给 V2（`_cs_holdout_out.txt:43-46`）；(iii) **统计/构式层**：`neg_count≥2 且 dbl=False` 的独立旁路（`GATE_PIPELINE_COMPOSE.md:510` 记 `_gpv_lazy.py` 独立实装 3/3 兜住、16 正样本 0 误伤，**但未并入本交付链**）；(iv) **文档结构层**：R11 引用锚回验（`_g7_predicates.py:157-222`）与 R9 要素在场（`:55-65`）本来就是正交项，应独立计入而非与断言层混合。
3. **每层声明输入契约并做覆盖率审计**：`_gp_DESIGN.md:370` 已提出「新层必须声明 输入/输出/position 口径/词表是否对齐」，应升级为可执行门禁：词表不同的层**不得**参与「一致通过」计数，只能作为 `ABSENT` 登记。
4. **把「无 span」变成独立信号**：`spans=0` 时不要静默 PASS，交给语义层判「这句话是否含完成语义」；`_v12_rule.py:32-38` 的 `V2_OVERRIDE` 词族（`登记闭合/填毕/已签/…`）可作为第二词表，与三词词表物理隔离。代价：需扩充词表并人工标注新样本，会引入新 FP（实测 `_cs_holdout_out.txt:27` V1V2 独立谓词在 20 条未见变体上 fp=4）。
5. **用条件独立性检验做验收**：上线前实测 `MI(层i,层j)` 与 `P(层j=PASS|层i=PASS)`，要求 `MI` 低于阈值且后验压低倍数逐层显著 <1；本次 `P(r12=PASS|n13=PASS)=1.000` 即为**不通过**（`_cs_attrib_out.txt:102`）。

---

## 4 第四步 · 合成链的取舍建议

### (a) 还有存在价值吗？——**有，但价值不在「比单层准确率高」**

判断依据（全部实跑）：
- 相对宽进层：naive 34/74（FP=33）、R10 35/74（FP=20/FN=19）、R12 39/74（FN=35）；合成链 69/74（FP=2/FN=3）。K9/K6 逐 span 裁决把 FP 从 20–33 压到 2（`_cs_recompute_out.txt:7-12`、对照 72 版并集 20 条 FP）。
- 对齐输入后相对 N13 单层：N13 66/74（FP=5）vs chain 69/74（FP=2），**chain 领先 3 条**（`_cs_align_out.txt:9-11`）。
- 有冲突的 25 行 chain 25/25 全对（`_cs_info_out.txt:22`）——**冲突消解是合成链唯一被实证验证有效的能力**。
- 但它没解决共同盲区（GP-A1/A2/A3 与 N13 同漏），K8 是死分支，K6 在词表外 span 上粗糙（`_cs_attrib_out.txt:8-27`）。

⇒ 价值定位：**「冲突仲裁器 + 词表外 span 的兜底调度器」**，不是「更高准确率的判别器」。它相对 N13 单层的**准确率优势仍未被独立留出集验证**（本会话 20 条扰动上两者打平 80%，`_cs_holdout_out.txt:25-26`）。

### (b) 若价值在「不同层的误报面不同」，正确用法是什么（不是取最严、不是取交集）

**实证先给反证**：
- 「取最严 / 取并集」＝72 版：chain 48/72、FP=20（`_cs_recompute_out.txt:43`），`GATE_PIPELINE_COMPOSE.md:431` 自认 20 条 FP 全来自「N13 已判 A/B 放过、R10 宽进仍报 assertion」。
- 「取交集」＝只信三层都 CATCH：naive∩R10∩R12∩N13 会把 R12 单层 FN=35 的漏报全部继承（`_cs_recompute_out.txt:10`），等于用最弱的一层否决全部。

**正确用法：按 span 的「证据所有权」分派，而不是按层的严格度投票**（现 `_gp_pipeline.py:123-217` 已经是这个思路，只是缺条件）：
1. **先判该 span 由谁拥有答案**：`tok ∈ n13_vocab` ⇒ N13 的 A/B/C/D 为主裁；`tok ∉ n13_vocab` ⇒ 该 span 应交给**与该词表配套的分类器**（C07 域交给 V1V2），而不是 K6 转采 R10 的宽进 assertion（`_gp_pipeline.py:156-161` 现在正是错在这里）。
2. **只在「双方都有所有权且意见相反」时进裁决**（`:166-176` 的 K2/K3/K4/K9）。`ABSENT` 必须保持 `ABSENT`，**绝不折叠成 PASS**（`:96,113` 的注释是对的）。`:181-182` 的 `n13_v=="PASS" and r10_v=="ABSENT" ⇒ PASS/K6` 与之有张力，但复核 `:181-182` 后应如实收窄：该分支的前提是 N13 自己给出了 A/B 放过（有局部证据），注释「仅 N13 有答案（拆分裂缝等）」，**不是把 R10 的 ABSENT 当 PASS**；真正的问题在 `:179-180`（`n13=PASS` 且 `r10=PASS` 且 `r12=ABSENT` ⇒ K5 放行）与 `:156-161` 的 K6 转采宽进——前者让 GP-A1 的 C 类放过直接生效，后者让 SLOT/TRUTH 的 `已填` 被 R10 assertion 判 CATCH。前稿把 `:181-182` 说成「违背不变量」是过度断言，此处更正。
3. **不同 span / 不同行不互相传播**（K5，`:108-109`），但要在报告层保留 section 供人工定位。
4. **`spans=0` 时移交独立语义层**（现为静默 PASS，是 GP-A2/A3 的根因，`_cs_attrib_out.txt:54,64`）。
5. **冲突无论是否消解都登记**（`:244-249`），且把「有冲突」当作高置信度信号（实测 25/25 全对）、把「无冲突且无 span」当作高风险信号（5 条错全在这里，`_cs_info_out.txt:23`）。
6. **置信度按有效独立层数（§3(c) 的 ≈1 层）计**，不许按 3 层相乘。

### (c) 分场景选择建议

| 场景 | 用哪个 | 依据 |
|---|---|---|
| 只扫 N13 三词字面断言、词表契约已对齐、追求低延迟/可解释 | **N13 单层**即可 | 42 条自家考题 42/42（`_cs_recompute_out.txt:93`）；但须接受未见形态 80% 的实测上限（`_cs_holdout_out.txt:25,29`）|
| 多词表域共存（N13 三词 / BAD_BAN 五词 / C07 域） | **合成链**，且必须按域装配分类器 | R10 考题对齐后 chain 17/17 > N13 14/17（`_cs_align_out.txt:27`）；但 SLOT/TRUTH 现会 2 条 FP，须先补 V1V2 层 |
| 已知存在层间分歧的样本（同句混用、双重否定、A 标记劫持） | **合成链**（K1–K4/K9 逐 span 裁决） | 有冲突 25 行 chain 25/25 全对（`_cs_info_out.txt:22`）|
| 词表外同义完成断言（`登记闭合`/`填毕`/`签字`）或分离型双重否定 | **两者都不够**；必须挂独立语义层或转人工 | chain 与 N13 同漏 3/3（`_cs_recompute_out.txt:24-31`）；`_v12_rule.py` 实测 3/3 能识别（`_cs_holdout_out.txt:43-46`）|
| 高召回优先、宁可误拦不可漏（fail-closed 门禁） | naive / 朴素并集可作**候选召回器**，但结论须交人工 | naive FP=33、并集 FP=20（`_cs_recompute_out.txt:8,43`），只能当候选生成器，不能当判据 |
| 需要「三层一致即通过」的自动放行 | **禁止** | 三层全 PASS 的 18 行里 3 行是真断言（16.7%，`_cs_info_out.txt:4,13`）；有效独立层数 ≈1 |

### (d) 若结论是「合成链该放弃」——**本次结论不是放弃**，但如实给出放弃会损失什么

**我的判断：不放弃。** 理由：`69 < 71` 这个前提已被 `_cs_align.py` 的对齐实验推翻（同输入下 69 > 66）；合成链相对宽进层的收益（FP 20→2）与冲突消解能力（25/25）都是独立的实测收益；它真正欠的是「补齐 V1V2 语义层 + 修 K6/K7」，不是「推倒重来」。

但**如果**编排方仍决定放弃，损失如下（逐项给证据）：
1. **20 条 FP 会回来**：回到朴素并集 48/72、FP=20（`_cs_recompute_out.txt:43`，`GATE_PIPELINE_COMPOSE.md:431`）。
2. **冲突消解能力消失**：25 条有层间冲突的样本（`_cs_info_out.txt:22`）将无人仲裁，K2 同句混用 / K1 双重否定 / K9 A-B 精筛这些已被实证有效的规则全部作废（`_gp_pipeline.py:98-116,162-180`）。
3. **多词表域没有调度器**：C07 域 `已填` 等 span 会退回「N13 完全不认 → 静默 PASS」或「R10 宽进全拦」二选一（`_gp_DESIGN.md:86,243`）。
4. **R9/R11 正交项的并入点消失**：`_gp_pipeline.py:228-230` 把要素在场与引用锚回验并入结构没了，需另建报告层。
5. **失去「证据不独立」的可观测性**：`conflicts[]` 是本次能算出 `MI≈0`、发现相关失效的唯一数据源；没有它就回到「单层自己说对即对」。
6. **不损失什么（如实说）**：共同盲区 GP-A1/A2/A3 不会因为放弃而变好也不会变坏——N13 单层同样 3/3 全漏。放弃**不解决**过拟合、不解决词表覆盖、不解决 `spans=0` 静默 PASS。

---

## 5 第五步 · 评测方法本身的改进建议

### (a) 考题集来源混杂会怎样影响结论

74 条的构成（`_cs_dump_out.txt:6-13`、`GATE_PIPELINE_COMPOSE.md:300-313`）：N13 自家 42（26 负+16 正，其中 8 条是探针失败回灌）、R10 TV 2、R10 四真实件 4、R10_CTX 构造 11、REAL3 真件 3、GP_CONFLICT 构造 9、GP_ALLPASS 构造 3。**四套词表混用**（`_cs_attrib_out.txt:85-89`），且 `not_in_corpus` 明写 30 件历史语料与 6 件 TV 样本被排除（`_cs_dump_out.txt:15-18`）。

影响：
1. **点估计无总体含义**：56.8% 的样本来自 N13 自家，且是规则设计时见过的形态；任何 `x/74` 都混合了「训练集内成绩」与「构造样本成绩」，不是对目标分布的无偏估计。
2. **样本选择方向不一致**：GP-A1/A2/A3 是**按已知盲区定向构造**的（`_gp_regression.py:121-130` 明写「三层全说放过但实际有真断言」），属对抗样本；N13_NEG/POS 属舒适样本。两者混在一个分母里，`correct/74` 随配比任意变动——`_cs_recompute_out.txt:162-170` 已展示换个子集排名就变。
3. **真值标注可变**：72→74 版 3 条 `expect` 被翻转（§1(d)），说明标注之人即规则之人，`expect` 不是独立真值。
4. **真件只有 7 条**（REAL3 3 + R10_REAL 4），且全为 `expect=PASS`；真件里**没有一条 `expect=CATCH`**，故「不误拦」被充分考、「抓得住」完全没在真件上考过（`_cs_dump_out.txt:97-100,112-114`）。
5. **排除项无交代的抽样框**：30 件历史语料与 6 件 TV 被排除的理由是「口径不同」，但没给「若纳入会怎样」的敏感性分析（`_gp_DESIGN.md:311` 只说未纳入）。

### (b) 更公平的评测设计

1. **抽样框先定**：以「真实交付件全集」为抽样框（先用 `_g9_regression.py:26-57` 的 30 件 + 现有 7 真件 + 后续新增），按域（N13 三词 / BAD_BAN 五词 / C07 域 / 无词表命中）分层，每层按 `expect` 正负再分，**每层配额固定**。
2. **三集合物理隔离**：`train`（可调规则）/ `dev`（选阈值、定 K 规则）/ `test`（一次性、封 SHA、盲评）。N19–N26 与 GP-A 这类「探针失败回灌」的样本必须归入 train 并明确标注，**不得进 test**。
3. **GroupKFold 按形态族分组**：同一个 `_n13_regression.py` 形态族（问句 / 表头 / 目录 / 同句混用 / 拆分形态 / 否定式）整组进同一折，避免 `U-P01` 与 `P01` 这类同形泄漏（本会话 `_cs_holdout.py` 的扰动变体正是用来暴露这个的）。
4. **真值双盲 + κ**：两名标注者独立给 `expect`，不见任何层输出，记录 Cohen's κ；争议样本进 `ambiguous` 集单列，不强行二值化。
5. **★ 输入契约对齐列为硬性前提**：`tokens` 必须逐行显式给出，**所有层（含 N13 单层）一律用同一份**；评测脚本把 `(id, tokens_sha, text_sha, predicate_sha)` 写进每行，缺任一列即判该行无效。本会话 `_cs_align.py` 的 `不一致 0 行` 核对（`_cs_align_out.txt:2`）可直接复用为门禁。
6. **多指标而非单点 accuracy**：按 `expect` 分别报 FP/FN、按族报 macro-F1、报「三层全 PASS 时的条件错误率」（本次 3/18=16.7%）、报有效独立层数（本次 ≈1）。并给 bootstrap 置信区间（74 条下 ±2 条约 ±2.7%，故「差 2 条」在统计上本就不显著——如实记）。
7. **两版对比必须固定三要素**：样本集、标注、算法。跨版只改一项，改一项就重跑全部层；本次 72/74 同时改了三项 ⇒ 不可比（§1(d)）。
8. **敏感性分析**：把被排除的 30 件历史语料、6 件 TV、以及词表外 C07 形态全部纳入重跑，报告排名是否翻转。

### (c) ★ 怎么防止「在考题上调规则」（可执行做法）

1. **语料先封样、后发题**：`test` 集由编排方生成后立即 `hashlib.sha256` 落盘并在台账登记（本会话 `_cs_probe.py` 的指纹表就是模板）；实现方只拿到「只读路径 + SHA」，拿不到改题权限。任何 `expect` 变更须新开版本号，旧成绩作废。
2. **规则变更与语料变更分账**：每次改谓词/改 K 规则，只准重跑 `train+dev`；`test` 一会话只准跑一次，跑完把结果连同指纹写死。本次 `_n13_regression.py:104-112` 的「曾 5/5 漏网 → 补 8 条样本 + 补 `_SPLIT_ASSERT`/`_line_positive`」就是**同一会话内既改题又改规则**的反例。
3. **把「新增样本」记成技术债而非成绩**：任何针对已观测失败新增的样本，必须标注 `source=probe_failure_of:<probe_id>`，并在报告里同时给「不含这些样本的 test 成绩」；`_gp_regression.py:121-130` 的 GP-A 三条应整族隔离成 `adversarial` 集，不计入主准确率。
4. **独立对抗生成**：由未参与规则设计的会话按「同义改写 / 换主语 / 换微段 / 换否定构式 / CRLF 切换」批量造变体，人工重标，`test` 只用这批。本会话 `_cs_holdout.py` 的 20 条是最小可行示例（实跑 100%→80% 的落差证明有效）。
5. **门禁化**：把 `assert` 写进回归脚本，禁止「脚本失败仍 EXIT=0」——`GATE_PIPELINE_COMPOSE.md:442` 自认 `_gpv_regress.py` 核出 `has_assert=False has_raise=False has_sys_exit=False`、「门槛是文字约定，不是可执行门禁」；`_gp_regression.py` 全文无 assert（本次实读）。应加 `assert tokens_sha == expected`、`assert all_layers_same_tokens`、`assert test_sha == pinned`、`assert FP<=x and FN<=y`。
6. **预注册评测口径**：开跑前把「fp/fn 定义、词表归属、ABSENT 处理、冲突计不计 FAIL」写成带 SHA 的规格件；本次 `judge_one` 的 N13 固定三词（`:143`）与 chain per-row（`:145`）这种口径分叉，若预注册时列为必填列就不会发生。

### (d) ★ 本次评测最大的方法论缺陷（如实说，不护着）

> **最大缺陷：比较双方的「输入」不一致，却把输出当成同一场考试的成绩来排名；而考试本身又是被考方自己出的题、自己批的卷。**

具体拆成一句可执行的判词：`_gp_regression.py:143` 让 N13 单层恒用固定三词 `T`，`:145` 让合成链用该行自己的 `tokens`；于是 19 行里 N13 单层在**一份根本不含待判 token 的词表**上被记了「PASS 且判对」，产出 `FP=0 / 71-of-74` 的表观最优（`_cs_align_out.txt:9`），而合成链在同一批行上被要求真正判那些 C07 域 span 并因此吃了 2 条 FP（`_cs_attrib_out.txt:8-27`）。**这不是「合成链不如单层」，是评测脚手架给单层发了免考卷。** 对齐输入后排名立刻反转（N13 66 vs chain 69，`_cs_align_out.txt:10-11`）。

第二层缺陷紧随其后：**训练集 = 测试集 + 标注可变**。`_n13_regression.py:104-112` 把探针发现漏网的形态回灌为 N19–N26 并同步改谓词；72→74 版又翻了 3 条 `expect`（`_cs_recompute_out.txt:127-129`）、换了 4 条样本、换了整套合成算法。因此 `71/74`、`69/74`、`48/72` 这三个数字**彼此之间没有可归因的因果关系**，却被并列成「合成链比单层差 2 条」的结论。

第三层：**有效独立层数 ≈1 却按 3 层叙述**（§3(c)）；`P(r12=PASS|n13=PASS)=1.000`，R12 增量信息 0 bit，「三层一致通过」被当成强证据，而实测 5 条错全落在无冲突行（`_cs_info_out.txt:23`）。

⇒ **本次评测不能用来给「合成链 vs 单层」下任何取舍结论**；它只能用来定位代码缺陷（K6 采信宽进、K7 死分支、词表契约分叉、共同盲区）。要下结论，必须先按 §5(b)(c) 重立盲集并重跑——**这是「未验」，本次没有做正式留出集**（本会话 `_cs_holdout.py` 的 20 条仅为方法示例，已在 §2(d) 标明边界）。

---

## 6 实跑命令清单（本会话全部实际执行）

| # | 命令 | 输出 |
|---|---|---|
| 1 | `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/chain_vs_single_20261109/_cs_probe.py` | 8 件编排方指纹全 `MATCH`；`lead/gate_n13_20261109/_n13_predicates.py` 反查命中；两份 JSON 顶层结构 |
| 2 | `python -I -X utf8 .../_cs_dump.py > .../_cs_dump_out.txt` | `_cs_dump_out.txt`（249 行） |
| 3 | `python -I -X utf8 .../_cs_recompute.py > .../_cs_recompute_out.txt` | `_cs_recompute_out.txt`（170 行）：逐层重算、链失败全清单、74/72 逐 id 差异、排名推演 |
| 4 | `python -I -B -X utf8 .../_cs_namecheck.py` | 确认 `r10_scan` 可解析、`r10_context` 同名前缀需规避 |
| 5 | `python -I -B -X utf8 .../_cs_attrib.py > .../_cs_attrib_out.txt` | `_cs_attrib_out.txt`（111 行）：K6/K5/K7 归因、三条不独立路径实跑、条件概率 |
| 6 | `python -I -B -X utf8 -c "...逐字读 _gp_pipeline.py / _g7_predicates.py / _v12_rule.py / N13 模块..."` | 文件:行 证据（本报告 §3(a) 全部行号） |
| 7 | `python -I -B -X utf8 .../_cs_align.py > .../_cs_align_out.txt` | `_cs_align_out.txt`（48 行）+ `_cs_align_out.json`：语料重建 74 行核对 0 不一致；对齐后 66 vs 69 |
| 8 | `python -I -B -X utf8 .../_cs_holdout.py > .../_cs_holdout_out.txt` | `_cs_holdout_out.txt` + `_cs_holdout_out.json`：未见变体 20 条 100%→80% 落差、MI/独立层数 |
| 9 | `python -I -B -X utf8 .../_cs_info.py > .../_cs_info_out.txt` | `_cs_info_out.txt`：似然比 k_eff=0.61、冲突行 25/25 全对、词表共享 74.3% |
| 10 | `python -I -B -X utf8 -c "...hashlib..."`（收尾） | 10 件只读件指纹全 `MATCH`、字节数不变 |
| 11 | `python -I -B -X utf8 -c "...配对检验 / assert 计数 / :179-184 复核..."` | McNemar `b=2,c=0,n=2,p=0.5000`；`_gp_regression.py` 全文 `assert/raise/sys.exit` 命中数 = 0；`_gp_pipeline.py:179-184` 分支条件逐行核对 |
| — | `git status --porcelain` + `ls -la` | 只读目录无新增改动；写域 16 个 `_cs_*` 文件 |

**未验 / 未做（如实列）**：
- 零真机相关一切（按铁律禁止，未做）。
- `_gp_regression_v1_union.py` 未留盘（`_gpv_regress.py:64-75` 亦记「脚本未留盘」），**72 版并集结果本次只重算 JSON、未重跑原脚本**。
- 未重跑 `_gp_regression.py` 本体（绝对只读目录，且会写回该文件所在目录）；本会话用 `_cs_align.py` 显式重建语料并核对 `不一致 0 行` 代替，已在 #7 说明。
- 未实装任何独立性方案 / 谓词修改 / K 规则修改 / 语料修改（任务纪律禁止）；§3(d)、§4(b) 均为方案，标「未实装」。
- 未做正式盲留出集与交叉验证；`_cs_holdout.py` 的 20 条为方法示例。
- 未 commit、未 push。

---

## 7 产物清单（写域 `lead/chain_vs_single_20261109/`）

`_cs_probe.py`、`_cs_dump.py`、`_cs_dump_out.txt`、`_cs_recompute.py`、`_cs_recompute_out.txt`、`_cs_namecheck.py`、`_cs_attrib.py`、`_cs_attrib_out.txt`、`_cs_align.py`、`_cs_align_out.txt`、`_cs_align_out.json`、`_cs_holdout.py`、`_cs_holdout_out.txt`、`_cs_holdout_out.json`、`_cs_info.py`、`_cs_info_out.txt`、本件 `_cs_BASELINE_ALIGNMENT_20261109.md`。
