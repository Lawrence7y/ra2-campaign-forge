# CHAIN_VS_SINGLE.md · 基线对齐与负收益归因（终稿，六节）

- 立件：2026-11-09；写域 `lead/chain_vs_single_20261109/`；产物 `CHAIN_VS_SINGLE.md`。
- 本件只做**基线对齐与归因分析**，不改任何谓词模块、不改合成链骨架、不改回归语料；要做的实验全部用本写域的独立脚本（`_cs_*` / `_csv_*`）。
- 合规：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 注入 / 动态内存解析）；`lead/gate_pipeline_20261109/`、`lead/gate_n13_20261109/`、`lead/gate_v1v2_20261109/`、`lead/gate_fp7_20261108/`、`lead/gate_r9r12_20261109/`、两件台账一律只读未改；不 commit 不 push。Python 一律 `python -I -B -X utf8` + 绝对路径，指纹用 `hashlib`。
- 复核 verdict 如实记录：上游复核给 **partial → 本结论标 `unconfirmed`**（见 §6）。凡本次未实跑或拿不到的，一律写「未验」，不补造。

---

## 1 目的与边界

**目的**：把「合成链 69/74 不如 N13 单层 71/74」这个比较放到同一基线上重算，逐层给成绩、判公平性、归因 2 条负收益、核三条证据不独立路径、估计「三层都过」的信息量，并给出取舍建议与评测方法改进。

**边界（铁律）**：
- 只做基线对齐与归因；**未改任何谓词模块**（`_g7_predicates.py`、`lead/gate_n13_20261109/_n13_predicates.py`、`_v12_rule.py` 指纹不变）、**未改合成链骨架**（`_gp_pipeline.py` 指纹不变）、**未改回归语料**（两份 JSON 指纹不变）。§5 的独立性方案、§6 的取舍用法均为**方案，未实装**。
- 不许为了让合成链好看而调整评测口径：本件不重定义 fp/fn、不重标 expect、不删样本；对齐实验只改「喂给 N13 单层的 `tokens`」这一项输入，且不改 `chain` 列（见 §3 的边界声明）。
- 若结论是「合成链确实不如单层」，须如实说并说明是否该放弃。本件的实际结论是**该比较无效**（§3），因此不能据此下「放弃」结论；但也**不许反向夸大**成「已证明链更好」（两侧差值都不显著）。

**本会话实跑的检查（逐条给命令与输出）**：
1. `python -I -B -X utf8 -c "...hashlib 10 件..."` → 10 行全部 `MATCH sha256=... bytes=...`（九件编排方指纹 + 被核报告件），见 §2 指纹表。
2. `python -I -B -X utf8 D:/Project/ra2-campaign-forge/lead/chain_vs_single_20261109/_csv_recompute.py > .../_final_recompute_check.txt` → `EXIT=0`，`[A]` 段 10 件全 MATCH、`[B]/[C]` 段逐层数字见 §2、`[D]` 段 `b=2 c=0 p=0.5000`；与复核方 `_csv_recompute_final.txt` 逐字节相同（`IDENTICAL True len_a 7141 len_b 7141`）。
3. `python -I -B -X utf8 .../_csv_align.py > .../_final_align_check.txt` → `EXIT=0`，`不一致 = 0 []`、`N13(对齐 per-row)=(66,5,3,74)`、`chain=(69,2,3,74)`、`p=0.2500`。
4. `python -I -B -X utf8 .../_csv_consistency.py > .../_final_consistency_check.txt` → `EXIT=0`，`chain 翻转 = 18 任意字段变化 = 23`、3 条逐字重复项、去掉后 `16/17=94.1%`。
5. `python -I -B -X utf8 .../_csv_attrib.py > .../_final_attrib_check.txt` → `EXIT=0`，K6/K5/rows=0 归因、19 行 `tokens != T`、25 行冲突全对。
6. `python -I -B -X utf8 -c "...exact binomial / k_eff / MI / conflict rows..."` → `p=0.5000 / 0.2500`、`k_eff=0.6064`、`MI=0.0006/0.0585/0.0633 bit`、`conflict rows=25 n13 correct=25/25 chain correct=25/25`、`chain FP=2 n13 FP=0`。
7. `python -I -B -X utf8 -c "...classify_v12 on GP-A tokens..."` → 5 个 token 全 `V2`（GP-A1/A2/A3 共 3 条全覆盖）。
8. 收尾 `python -I -B -X utf8 -c "...hashlib 9 件..."` → 9 行全 `MATCH bytes=...`（含 `_n13_predicates.py` 16649 B）；`git log -1` → `2657458`；`git status --porcelain` 对五个只读目录 + 两件台账 → `MM` 两件台账、`??` 五个目录，与会话开始快照一致，无新增只读改动。

---

## 2 上游指纹（九件）+ 逐层成绩表 + 74 vs 72 差别

### 2.1 九件编排方指纹（本会话 `hashlib.sha256` 实算，全部 MATCH）

| # | 件 | SHA256 | 字节数 |
|---|---|---|---|
| 1 | `lead/gate_pipeline_20261109/_gp_regression_out.json` | `d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe` | 38575 |
| 2 | `lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json` | `68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358` | 37461 |
| 3 | `lead/gate_pipeline_20261109/_gp_pipeline.py` | `25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7` | 15811 |
| 4 | `lead/gate_pipeline_20261109/_gp_DESIGN.md` | `412e816fb0ad75618c91ac40806f11cd2919195f2eba5300c469862a65f840bc` | 39058 |
| 5 | `lead/gate_n13_20261109/_n13_predicates.py` | `e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079` | 16649 |
| 6 | `lead/gate_v1v2_20261109/_v12_rule.py` | `15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0` | 9148 |
| 7 | `lead/gate_fp7_20261108/_g7_predicates.py` | `02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120` | 11743 |
| 8 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 |
| 9 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 |

被核对象 `_cs_BASELINE_ALIGNMENT_20261109.md` = `3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2` / 49850 B（亦 MATCH）。占位符对应实路径：本会话 `python -I -B -X utf8 -c "...os.path.isfile / glob 16649B..."` 输出 `FILE 'lead/gate_n13_20261109/_n13_predicates.py' sha256=e119... bytes=16649` 与 `NOT A PLAIN FILE '_n13_predicates.py'`；`glob` 命中 `lead/gate_n13_20261109\_n13_predicates.py`（同一 SHA、同一 16649 B），引用按占位符原样保留。收尾九件复算全 MATCH 且字节数不变（§1 检查 8）。

### 2.2 逐层成绩表（从两份只读 JSON 的 `rows[]` 逐行独立重算）

口径：`CATCH`＝应拦正类；`fp`＝误拦（expect=PASS 判 CATCH）；`fn`＝漏报（expect=CATCH 判 PASS）；`correct`＝判对行数；`n`＝语料条数。来源：`_final_recompute_check.txt:15-25`（74 版）、`:29-39`（72 版），与 JSON 自带 `single_layer_vs_chain` 逐项 10/10 `MATCH`；`_cs_recompute_out.txt:6-19` 同值。

**当前版 74 条（`_gp_regression_out.json`）**

| 层 | correct | fp | fn | n | 混淆矩阵 CATCH→CATCH / CATCH→PASS / PASS→CATCH / PASS→PASS |
|---|---|---|---|---|---|
| naive | 34 | 33 | 7 | 74 | 32 / 7 / 33 / 2 |
| R10 | 35 | 20 | 19 | 74 | 20 / 19 / 20 / 15 |
| R12 | 39 | 0 | 35 | 74 | 4 / 35 / 0 / 35 |
| **N13 单层** | **71** | **0** | **3** | **74** | 36 / 3 / 0 / 35 |
| **合成链 chain** | **69** | **2** | **3** | **74** | 36 / 3 / 2 / 33 |

全语料 expect 分布 CATCH=39 / PASS=35（`_cs_info_out.txt:1`）。编排方 `【逐层对齐】` 给的 `current.rows`（`PASS->CATCH:2 / CATCH->PASS:3 / ok:69`）是**合成链的混淆矩阵**，不是「全语料」的；不影响逐层数字，但勿误读为基线。

**并集版 72 条（`_gp_regression_v1_union_out.json`）**：naive 37/30/5、R10 32/20/20、R12 36/0/36、N13 68/0/4、chain 48/20/4（`_final_recompute_check.txt:29-39`）。

**★ 差值不显著**：本会话实跑 `python -I -B -X utf8 -c "...math.comb..."` 输出 `harness b=2 c=0 n=2 p_two_sided=0.5000`、`2/74 = 0.0270`；即「chain 69 < n13 71」的不一致对只有 2 条，exact binomial 双侧 p=0.5。编排方 `GATE_PIPELINE_COMPOSE.md:412-416` 与 `_gp_DESIGN.md:340-343` 把这个 p=0.5 的差值写成「如实结论 / 变差 2 条」，属过度解读。

### 2.3 74 vs 72 的差别（同时改了三样，两版不可比）

`_cs_recompute_out.txt:121-159`、`_final_recompute_check.txt:64-68`、`_final_consistency_check.txt:10-14` 逐 id 对照：

1. **样本集**：74 版新增 `GP-A1/A2/A3`（`GP_ALLPASS_TRUE_ASSERTION` 3 条），删 `GP-C03`（文本与 GP-A1 逐字相同 `亦非不宣告 N-4 正式绑定已生效`，`_gp_regression.py:126` vs 72 版）；`GP_CONFLICT` 10→9。共有 id 71 条。
2. **真值标注翻转**：`GP-C05/C06/C07` 的 `expect` 从 `CATCH` 翻成 `PASS`（`_final_recompute_check.txt:67`；现 `_gp_regression.py:113-115` 写 `PASS` +「人工判检索结果，非完成断言」）。72 版 N13 的 `fn=4` 正是 C03/C05/C06/C07（`_final_consistency_check.txt:2-3`），翻标注后其中 3 条自动「判对」⇒ **N13 从 68/72 到 71/74 的 3 分里至少 3 分来自改标注 + 换样本，不是模型变强**。
3. **合成链算法换代**：72 版「三层 problems 朴素并集」`unresolved=22` → 74 版「逐 span K1–K9 裁决」`unresolved=0`（`_cs_recompute_out.txt:3,34`；`GATE_PIPELINE_COMPOSE.md:419-431` 自认 v1 失败、20 条 FP 全来自「N13 已判 A/B 放过、R10 宽进仍报 assertion」）。共有 71 条里 **`chain` 从 CATCH 翻成 PASS 的是 18 条**（`_final_consistency_check.txt:11-12`：`chain 翻转 = 18 任意字段变化 = 23`；复核指出原报告 §1(d) 写「23 条」是错的，23 是任意字段变化行数，本件更正为 18）。
4. **可比性结论**：(i) 样本集 + (ii) 标注 + (iii) 算法三样同变，`48/72 → 69/74` 没有因果含义。第一版脚本 `_gp_regression_v1_union.py` 未留盘（`_gpv_regress.py:64-75` 明写「脚本未留盘 → 只能核对 JSON」；本会话 `python -I -B -X utf8 -c "...os.path.exists..."` 输出 `v1 union script present = False`，glob 只有 `.json/.txt`）⇒ **72 版并集本次只重算 JSON、未重跑原脚本，标「未验重跑」**。

---

## 3 比较公平性（N13 在自己考题上考的分 + 换考题推演 + 过拟合测法）

### 3.1 不公平，但任务点名的「用 N13 的考题考合成链」方向反了

74 条构成（`_cs_dump_out.txt:7-13,27-35`；`GATE_PIPELINE_COMPOSE.md:300-313`）：N13 自家 42（26 负 + 16 正）、R10_TV 2、R10_REAL 4、R10_CTX 11、REAL3 3、GP_CONFLICT 9、GP_ALLPASS 3。**56.8% 是 N13 自己出的题**，来源 `_n13_regression.py:46-80,85-113`，`_gp_regression.py:62-66` 逐字导入。

- 在这 42 条上 **N13 42/42、chain 42/42、FP=0、FN=0，差距 0**（`_cs_recompute_out.txt:88-96`；`_final_recompute_check.txt:59-61`）。2 条差距全在 N13 考题之外的 REAL3 组（chain 1/3 vs n13 3/3，`_cs_recompute_out.txt:109-118`）。⇒ 考题偏置**没有制造这 2 分**。
- 真件 7 条全部 `expect=PASS`、无一条 CATCH（`_final_consistency_check.txt:6-8`）；「抓得住」从未在真件上考过。

### 3.2 真正致命的不公平：输入契约不对齐（19 行双方输入不同）

`_gp_regression.py:47` `T = P.load_predicates()` 返回的 `list(n13.DEFAULT_TOKENS)`（`_gp_pipeline.py:52`）；`:133-145` 的 `judge_one` 逐字实读（本会话 `python -I -B -X utf8 -c "...lines..."` 打印 `:133-150`）：

- `:143` N13 单层：`n13.r13_assertions(text, T, ...)` —— 恒用模块级常量 `T=['已入账','已追加','已生效']`，**不看 `item['tokens']`**；
- `:145` 合成链：`P.gate_check(text, toks, WD, g7, n13, T)` —— `toks = item['tokens']`，即该行自己的词表；
- `:139/:141` naive/R10/R12 也都用 `toks`。

74 行词表分布（`_csv_attrib_out.txt:76-81`）：55 行三词、17 行 BAD_BAN 五词、1 行 C07_SLOT 四词、1 行 C07_TRUTH 三词；本会话 `_final_attrib_check.txt:59-60` 实算 **`tokens != T` 的行数 = 19**。⇒ 19 行里 N13 单层在一份根本不含待判 token 的词表上被记「PASS 且判对」。

**对齐实验（决定性）**：`python -I -B -X utf8 .../_csv_align.py > .../_final_align_check.txt` 输出 `重建 len=74 / 逐行不一致 = 0 []`，再让 N13 单层改用该行 `tokens` 重跑：

| 层 | correct | fp | fn | n |
|---|---|---|---|---|
| N13 单层（harness 固定三词） | 71 | 0 | 3 | 74 |
| **N13 单层（对齐 per-row）** | **66** | **5** | 3 | 74 |
| 合成链 chain（只读 JSON 列） | **69** | 2 | 3 | 74 |

方向反转：同一份 `tokens` 下 chain 69 > N13 66。对齐后 N13 新增 5 条 FP：`R10-REAL-CANDIDATE_RESIGN_YES_V2`、`R10-CTX-03`、`R10-CTX-04`、`REAL-SLOT`、`REAL-TRUTH`（`_final_align_check.txt:9`）。

⚠️ **边界，必须如实声明（复核 §⑦ 指出，本件采纳）**：
- **chain 列未重跑**：`_cs_align.py:130` `row = dict(J[it["id"]])` 直接复制只读 JSON 的 `chain` 列（本会话逐字读 `_cs_align.py:126-141` 确认），对齐实验只重跑 N13 单层。
- **chain 还有第二词表输入**：`_gp_pipeline.py:132` `n13_vocab = set(n13_tokens)`、`:135` `tok_set = set(tokens) | n13_vocab`，而 `n13_tokens` 恒为 `T`（`_gp_regression.py:145` 传 `T`）；**K6 恰恰由 `n13_vocab=T` 驱动**（`:156` `if tok not in n13_vocab`）。因此「所有层用同一份 tokens」并不足以完全对齐 chain 的两个词表输入，§6 的评测改进须把「chain 的第二词表」也列成必填列。
- **两侧差值都不显著**：本会话实跑 `p=0.5000`（harness, b=2,c=0,n=2）与 `p=0.2500`（对齐, b=0,c=3,n=3）。正确表述是「**原结论失去依据**」，不是「已证明链更好」。

### 3.3 换考题集推演（`_cs_align_out.txt:25-29`、`_final_align_check.txt:14-18`）

| 考题集 | n | 排名（correct） |
|---|---|---|
| 全 74（harness） | 74 | n13=71 > chain=69 > r12=39 > r10=35 > naive=34 |
| 全 74（对齐） | 74 | n13_fixed=71 > chain=69 > **n13_aligned=66** |
| N13 自家 42 | 42 | n13=n13_aligned=chain=42（三者打平） |
| R10 考题 17 | 17 | n13_fixed=17 = chain=17 > r12=16 > **n13_aligned=14** |
| 中性第三方 15 | 15 | n13_fixed=12 > n13_aligned=10 = chain=10 |
| 仅应放行 35 | 35 | r12=35 = n13=35 > chain=33 |

⇒ 换成 R10 考题后 chain 17/17 反超 N13 对齐 14/17；中性第三方对齐后两者完全打平（都 `ok=10 fp=2 fn=3`，`_cs_align_out.txt:39-41`）。**排名随考题集变动，不存在稳定的「单层更好」。**

### 3.4 过拟合：定性成立，定量幅度须更正

**训练集 = 测试集**：`_n13_regression.py:104-112` 明写「第二轮：复核 verdict=partial 的 ④，5 条样本外真断言（**曾 5/5 漏网**）」，N19–N26 按探针 `V1..V5 / X1..X3` 造出并同步补 `_SPLIT_ASSERT`/`_line_positive`/`_prefix_is_subject`（`_n13_predicates.py:76-86,147-177`）；`_gp_regression.py:121-130` 的 GP-A1/A2/A3 也是「按已知盲区定向构造」。**出题人 = 改规则的人 = 批卷人**。奇偶切 N13 自家 42 条 train/holdout 各 21/21 全对（`_cs_align_out.txt:31-33`）是过拟合症状，不是泛化证据。

**本会话示例性探针的更正**（复核 §④，本件采纳）：`_cs_holdout.py` 原报告称「20 条不在任何回归语料中」并给 `N13 16/20=80%`、与自家 42 条 100% 相比「落差 20 个百分点」。`_final_consistency_check.txt:16-29` 实算 **U-N10/U-N11/U-N12 与 GP-A2/GP-A3/GP-A1 逐字相同**（脚本自己标「同形」），且这 3 条正是 4 个错误里的 3 个；剔除后 **17 条未见变体为 16/17 = 94.1%**（N13 与 chain 同分，V1V2 12/17）。`_csv_holdout_replay.txt` 与 `_cs_holdout_out.txt` 逐字节相同（本会话实算 `holdout replay IDENTICAL = True bytes= 2982`），排除环境差异。⇒ **过拟合定性成立**（回灌 + 翻标注撑住），但「100%→80%、落差 20 个百分点」**定量夸大**；20 条是本写域内造的示例性扰动，其数值**不能当泛化点估计**。正式盲留出集本次**未做，标「未验」**。

**过拟合测法（可执行，不调评测口径）**：① 冻结语料/标注/词表/谓词指纹并封 SHA；② 由未参与者先出题、封 SHA 的**真留出集**；③ 按形态族（问句 / 表头 / 目录 / 同句混用 / 拆分 / 否定式）做扰动生成与 GroupKFold；④ 双盲标注 + Cohen's κ；⑤ 所有层强制同一 `tokens`（含 chain 的第二词表）；⑥ 报 macro-F1 / 条件错误率 / bootstrap CI；**禁止把探针失败样本回灌 test**。

---

## 4 负收益归因（逐条失败样本 + K 规则 + N13 为何「判对」+ 设计缺陷 vs 过拟合）

### 4.1 合成链失败样本逐条（`_cs_recompute_out.txt:21-31`；`_final_recompute_check.txt:43-52`）

编排方 `chainFailures` 5 条须拆开：**N13 对而 chain 错的只有 2 条**（负收益），另 3 条是两者**同漏**，不计入差距。

| id | expect | chain | n13 | r10 | r12 | naive | 文本 / 归属 | 是否负收益 |
|---|---|---|---|---|---|---|---|---|
| REAL-SLOT | PASS | **CATCH** | PASS | CATCH | PASS | CATCH | `c07_slot_20261109/C07_IDENTITY_SLOT.md` 逐字读盘 | **是，FP** |
| REAL-TRUTH | PASS | **CATCH** | PASS | CATCH | PASS | CATCH | `c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md` 逐字读盘 | **是，FP** |
| GP-A1 | CATCH | PASS | PASS | PASS | PASS | CATCH | `亦非不宣告 N-4 正式绑定已生效` | 否（同漏） |
| GP-A2 | CATCH | PASS | PASS | PASS | PASS | PASS | `本件登记闭合，母本即日起适用` | 否（同漏） |
| GP-A3 | CATCH | PASS | PASS | PASS | PASS | PASS | `三值填毕，见证已由编排方签字` | 否（同漏） |

⇒ 2 条负收益**全是 FP（误拦），0 条新增 FN**；`GATE_PIPELINE_COMPOSE.md:417` 自认「合成链没有引入新漏报」。

### 4.2 每条是哪条 K 规则判错、N13 为何「判对」（`_final_attrib_check.txt:7-47`；`_cs_attrib_out.txt:8-34,107-111`）

**(a) REAL-SLOT / REAL-TRUTH → K6**：逐 span 重放 `P.gate_check`：
- SLOT：6 个 span（token 全 `已填`），**5 个 CATCH 全部 `rules=['K6']`**，全在 N13 三词外（0/6），`r10=CATCH / r12=ABSENT / n13=ABSENT / kind=None`；命中形态是「填用流程①…」「三个身份字段已填…」「### 5.4 多处同步排查表（…是否已填）」「| # | 件 | 行 | 需什么字段 | 是否已填 |」等规定式/表头/清单，非完成断言。
- TRUTH：3 个 span / **2 个 K6 CATCH**，全在三词外（0/3）。
- 判错链条：`_gp_pipeline.py:156-161` K6（`tok not in n13_vocab ⇒ verdict = r10_v`）无条件采信 R10 的宽进 `assertion`；R10 给 assertion 是因 `_g7_predicates.py:78-111` 的 24 字回看窗（`:70 NEG_WINDOW = 24`）没找到否定词，而 R10 **没有 V1/V2 身份陈述 vs 完成断言的分类能力**（`_v12_rule.py:108-170` 的职责，本链未挂）。`GATE_PIPELINE_COMPOSE.md:415,490`、`_gp_DESIGN.md:86,243,340-343,385` 自认「词表契约冲突，只能 K6 转采 R10 或另挂 V1/V2 前置分类」。
- **N13 单层「判对」不是判对，是没参与**：`_gp_regression.py:143` 传固定三词 `T`，`已填` 不在 `_n13_predicates.py:25 DEFAULT_TOKENS` ⇒ `details=[]` ⇒ 无条件 PASS。同一文件改喂该行 C07 词表会报 **SLOT 6 条 D / TRUTH 3 条 D**（`_csv_attrib_out.txt:18-19,29-30`），比链还差。

**(b) GP-A1 → K5**：`spans=1`，R10 kind=`negation`、R12 0 命中、N13 kind=`C` ⇒ `_gp_pipeline.py:179-180` `K5` 放行（`_final_attrib_check.txt:35-39`）。根因 `_g7_predicates.py:76 DOUBLE_NEG_RE` 是**枚举构式**，「亦非不」不在表内；N13 的 C 类又只是转发 R10（`_n13_predicates.py:247-263`）。注意原撰写人已主动更正：`_cs_attrib_out.txt:44` 那句「rows 空」**只对 A2/A3 成立**，A1 有 1 个 span。

**(c) GP-A2/A3 → K7 死分支**：四套词表全部 0 字面命中 ⇒ `rows=0` ⇒ `_gp_pipeline.py:135-184` 的 span 循环不进 ⇒ `:183-184` 的 K7 `RAISE` 是**死分支**，`:253` `verdict="PASS"`（`_final_attrib_check.txt:40-47`）。`GATE_PIPELINE_COMPOSE.md:252-254` 实跑 `K7=0 K8=0`；`_gp_DESIGN.md:285-286` 自认「spans=0 时 K7 的 RAISE 循环体根本不执行」。独立证据能兜住：本会话 `python -I -B -X utf8 -c "...classify_v12..."` 对 `已生效/登记闭合/适用/填毕/签字` 5 个 token 全给 `V2`，即 GP-A1/A2/A3 **3/3 可识别**（`_cs_align_out.txt:43-46`）⇒ 缺口在「本链没挂这一层」。

### 4.3 设计缺陷 vs 过拟合的判断

**判断：主要是评测脚手架输入不对齐 + N13 在自家考题上的过拟合；但合成链确有真实且独立的设计缺陷，不能护着。**

1. 「N13 71/74」不是能力，是三件事叠加：固定三词让它在 19 行免考（§3.2）+ 42 条自家考题满分（§3.1）+ 失败样本回灌规则（§3.4）。对齐后掉到 66/74、FP=5，比链差 3 条。⇒ 原报表「单层更好」是**过拟合幻象 + 免考卷**。
2. 合成链 2 条 FP 是**真实设计缺陷**：K6 在词表外 span 无条件采信 R10 宽进，等于把 R10 已知 20 条 FP 的失败模式搬进裁决；K7 在 `rows=0` 时是死分支、`spans=0` 静默 PASS。这两条与单层无关，是缺一层分类器。
3. GP-A1/A2/A3 是**共同盲区**（三层共用词表与否定构式枚举），既不是单层对也不是链错；但「无 span 静默 PASS」属于链骨架缺陷。
4. **不能据此说「合成链该被放弃」**：被证伪的是「69 < 71」这个比较；相对宽进层 FP 33→2 / 20→2、相对对齐后 N13 66→69 是实打实的。但也**不许反向夸大**：准确率优势未被独立留出集验证（20 条扰动上 chain 与 N13 打平 80%，剔除 3 条重复后 94.1%，见 §3.4）。

---

## 5 证据独立性（三条不独立路径 + 统计后果 + 信息量估计 + 独立化方案）

### 5.1 三条路径逐条追到文件:行（本会话逐字实读）

| 路径 | 结论 | 文件:行 |
|---|---|---|
| ① N13 的 C 类转发 R10 | **成立，硬依赖** | `_n13_predicates.py:5-7` 自述「C 否定式交既有 R10 判定，本件只消费其 kind…双重否定交 R12，不重写 R10 正则」；`:183` `r13_scan(..., r10_scan=None, r12_scan=None)`；`:195-198` 调 `r10_scan(text, list(tokens))` 灌 `r10_map`；`:231` 每条 detail 带 `r10_kind`；`:247-263` ② 分支 `k = rec["r10_kind"]`，`k in ("negation","quote_mention")` 才 `kind="C", exempt=True`，`:257-259` 无 R10 则「降级默认 FAIL」。调用链 `_gp_pipeline.py:80-81` 同时注入 `g7.r10_scan` 与 `g7.r12_scan`。 |
| ② R12 复用 `r10_context` | **成立，确定性子集** | `_g7_predicates.py:134-148` `r12_scan`；`:144` `ctx = r10_context(text, m.start(), m.end())`；`:145-147` 仅 `ctx["kind"]=="double_neg"` 才报。`r10_context` 在 `:78-111`（`:102-103` 由 `dbl` 置 `double_neg`），R10 主入口 `:120` 调同一函数。⇒ R12 hits ≡ R10 hits 中 `double_neg` 子集。 |
| ③ 三层共用字面词表 | **部分成立，须收窄** | `_n13_predicates.py:25 DEFAULT_TOKENS`；`_gp_pipeline.py:52` `list(n13.DEFAULT_TOKENS)`、`:132 n13_vocab=set(n13_tokens)`、`:135 tok_set=set(tokens)|n13_vocab`；`_gp_regression.py:47,143` 恒用 `T`。实测 **55/74 = 74.3%** 行 `tokens` 就是这三词（`_cs_info_out.txt:15-20`）；另 17 行 BAD_BAN 五词、2 行 C07 词表不同表。否定/标记词表全局共用：`_g7_predicates.py:69 NEG_RE`、`:73 SELF_MARKERS`、`:76 DOUBLE_NEG_RE`；`_n13_predicates.py:41-44 _A_AFTER`、`:60-63 _DIRECT_NEG`、`:68-74 _POS_TAIL/_CONTRAST_POS`。`GATE_PIPELINE_COMPOSE.md:499`、`_gp_DESIGN.md:394` 自认「相关失效而非独立表决」。 |

**实跑验证**：`_cs_attrib_out.txt:70-91` / `_csv_attrib_out.txt:63-80`：3 条否定式样本 `R10 kinds=['negation']` 与 `N13 kinds=['C']` 一一对应（rule 字面写「R10 negation 已覆盖」）；6 条样本 `R10_double_neg` 与 `R12_hits` **6/6 全同**；`tokens != T` 19 行（`_final_attrib_check.txt:59-60`）。

### 5.2 统计后果

1. **「一致通过」概率被系统性高估**：三层共享提取器（`_gp_pipeline.py:135-137` 全量 `finditer`）、同套词表、同套否定构式；任何「词表里没有的完成断言」会让三层**同时**无 span。实测 `三层全 PASS = 18/74`，其中 `expect=CATCH` 的 3 条全是 GP-A1/A2/A3（16.7%，`_cs_holdout_out.txt:34`；`_final_attrib_check.txt:84`）——相关失效 100% 集中。
2. **分歧反而是唯一有信息的信号**：本会话 `python -I -B -X utf8 -c "..."` 输出 `conflict rows=25 n13 correct=25/25 chain correct=25/25`、`no-conflict rows=49 chain 错=5 ['REAL-SLOT','REAL-TRUTH','GP-A1','GP-A2','GP-A3']`（`_cs_info_out.txt:22-23`、`_final_attrib_check.txt:90-91`）。⚠️ 复核 §⑦ 更正：这 25 条上 **N13 单层本身也是 25/25**，故「冲突消解」不是相对单层的独占收益。
3. **置信度不可乘**：共同原因（common cause）模型下误差上界由共享词表覆盖率决定，与层数无关。
4. **「未消解 0」是空结论**：`unresolved=0` 只说明 K8 分支从未可达（`GATE_PIPELINE_COMPOSE.md:252-254` 实跑 `K7=0 K8=0`）。

### 5.3 「三层都过」的信息量 ≈ 1 层（本会话重算）

`python -I -B -X utf8 -c "...math.log/MI..."` 输出（`_cs_info_out.txt:1-13`、`_cs_holdout_out.txt:36-40` 同值）：

| 条件 | P(CATCH\|条件) | 相对上一步似然比 |
|---|---|---|
| 先验 | 39/74 = 0.5270 | — |
| N13=PASS | 3/38 = 0.0789 | **0.150**（信息几乎全在这层） |
| +R10=PASS | 3/18 = 0.1667 | **2.111**（不降反升，负信息） |
| +R12=PASS | 3/18 = 0.1667 | **1.000（零增量，0 bit）** |

`k_eff = ln(0.1667/0.5270)/ln(0.150) = 0.6064`（本会话实算，报告写 0.61）；`MI(r10,n13)=0.0006`、`MI(r12,n13)=0.0585`、`MI(r10,r12)=0.0633 bit`；`P(r12=PASS|n13=PASS)=38/38=1.000`（本会话实算）。因果图是 `R10 → {R12, N13.C}` 一条链，不是三个独立观测。⇒ **有效独立层数 ≈ 1～1.3 层（乐观 1.5）**，「三层都过」只能按 1 层计。⚠️ 半定量基于 74 条、三层全 PASS 仅 18 行，非渐近估计。

### 5.4 让证据独立的方案（**方案，未实装**）

1. **切断数据依赖**：N13 自算否定/引证语境（去掉 `r10_scan=` / `r12_scan=` 注入），R12 自算双重否定（不调 `r10_context`）。代价：`_n13_predicates.py:257-259` 明写「无 R10 → C 类降级默认 FAIL，会误拦正样本」，须重写 C 类并重新封样；**动谓词模块，本任务铁律不许，标未实装**。
2. **换信息源而非换阈值**：(i) 字面 token 层；(ii) 语义/句法层挂只读 `_v12_rule.py:108-170` 的 `classify_v12`（实测 GP-A 3/3 给 V2）；(iii) 统计/构式层 `neg_count≥2 且 dbl=False` 独立旁路（`GATE_PIPELINE_COMPOSE.md:510` 记 `_gpv_lazy.py` 3/3 兜住，未并入本链）；(iv) 文档结构层 R11 引用锚回验（`_g7_predicates.py:157-222`）与 R9 要素在场（`:55-65`）正交计入。
3. **每层声明输入契约并做覆盖率审计**（`_gp_DESIGN.md:370` 已有设计）：词表不同的层不得参与「一致通过」计数，只登记 `ABSENT`。
4. **把 `spans=0` 变成独立信号**：交语义层判「是否含完成语义」，用 `_v12_rule.py:32-38` 的 `V2_OVERRIDE` 词族作物理隔离的第二词表。代价：实测 `_cs_holdout_out.txt:27` V1V2 在 20 条上 `fp=4`，会引入新 FP。
5. **条件独立性验收门禁**：上线前实测 `MI(层i,层j)` 与 `P(层j=PASS|层i=PASS)`，要求逐层后验压低倍数显著 <1；本次 `P=1.000` 即**不通过**。

---

## 6 复核回件（绑定行）+ 取舍建议 + 评测方法改进 + 未验项

### 6.1 复核 verdict 与绑定行（格式固定）

**复核 verdict：partial → 按交付规则标 `unconfirmed`。** 复核方 `ranCommands=38`，主结论「69/74 < 71/74 比较无效（输入契约不对齐 + p=0.5）」被独立复现且不报 refuted；判 partial 的 5 点本件已全部采纳更正：① 20 条探针中 3 条逐字重复、定量夸大（§3.4）；② 报告 §1(d)「23 条 chain 翻转」实为 18 条（§2.3）；③ 25 条冲突行 N13 单层也是 25/25、「20 条 FP 会回来」是回退到 v1 并集而非回退到 N13 单层（§6.3）；④ 未列「放弃改用 N13 单层在 74 行上 FP 2→0」（§6.3）；⑤ 对齐实验 chain 列取自只读 JSON 且 chain 仍有第二词表输入 `T`（§3.2）。复核 §⑧ 认可方法论自评到位、§⑨ 确认无越界。复核方给出的升级条件（更正 3 处事实错误、剔除/改标 3 条重复、补写 FP 2→0 与第二词表）本件均已如实写入；**但本件不自行把 verdict 升为 confirmed**——复核 verdict 是编排方给出的，如实记为 `partial / unconfirmed`。

被核对象 SHA256 = d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe，字节数 = 38575

被核对象 SHA256 = 68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358，字节数 = 37461

被核对象 SHA256 = 25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7，字节数 = 15811

被核对象 SHA256 = 412e816fb0ad75618c91ac40806f11cd2919195f2eba5300c469862a65f840bc，字节数 = 39058

被核对象 SHA256 = e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079，字节数 = 16649

被核对象 SHA256 = 15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0，字节数 = 9148

被核对象 SHA256 = 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120，字节数 = 11743

被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419

被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

被核对象 SHA256 = 3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2，字节数 = 49850

（前 9 行为九件编排方指纹，第 10 行为被核报告件；均为本会话 `hashlib` 实算。收尾复算 9 件全 MATCH 且字节数不变，`git log -1` 仍 `2657458`。）

### 6.2 取舍建议：能否放弃 / 正确用法 / 分场景选择

**能否放弃：本次结论是「不放弃」，但必须说清 `unconfirmed`。** 理由：`69 < 71` 的前提被对齐实验推翻（同 `tokens` 下 69 > 66，`p=0.2500`）；链相对宽进层 FP 33→2 / 20→2、25 条冲突行 25/25 全对是实测收益；它欠的是「补 V1V2 语义层 + 修 K6/K7 / 对齐第二词表」，不是推倒重来。**但**准确率优势未被独立留出集验证（20 条扰动打平 80%，剔除重复后 94.1%），故也不能说「已证明链更好」。**本次评测不能用来下「合成链 vs 单层」的最终取舍结论**（最大方法论缺陷见 §6.4）。

**正确用法（不是取最严、不是取交集）**：
- 反证：取最严/并集＝72 版 48/72、FP=20（`GATE_PIPELINE_COMPOSE.md:431`）；取交集＝继承 R12 单层 FN=35。
- ① 按 span 的**证据所有权**分派：`tok ∈ n13_vocab` 由 N13 A/B/C/D 主裁；`tok ∉ n13_vocab` 交与该词表配套的分类器（C07 域交 V1V2），**不得**由 `_gp_pipeline.py:156-161` K6 转采 R10 宽进 assertion。② 只在双方都有所有权且意见相反时裁决（`:166-176` K2/K3/K4/K9），`ABSENT` 保持 `ABSENT`。③ 不同 span/行不互相传播（K5，`:108-109`）。④ `spans=0` 移交独立语义层（现为静默 PASS）。⑤ 冲突无论是否消解一律登记（`:244-249`），把「有冲突」当高置信信号、「无冲突且无 span」当高风险信号。⑥ 置信度按有效独立层数 ≈1 计，不许按 3 层相乘。

**分场景选择**：

| 场景 | 用哪个 | 依据 |
|---|---|---|
| 只扫 N13 三词字面断言、词表契约已对齐、要低延迟/可解释 | **N13 单层**即可 | 自家 42 条 42/42；但须接受未见形态的实测上限（§3.4，正式留出集未验） |
| 多词表域共存（N13 三词 / BAD_BAN 五词 / C07 域） | **合成链**，且按域装配分类器 | R10 考题对齐后 chain 17/17 > N13 14/17；但 SLOT/TRUTH 现 2 条 FP，须先补 V1V2 层并修 K6 |
| 已知存在层间分歧（同句混用、双重否定、A 标记劫持） | **合成链**（K1–K4/K9 逐 span 裁决） | 25 条冲突行 chain 25/25（**注意 N13 单层亦 25/25，非独占收益**） |
| 词表外同义完成断言（`登记闭合`/`填毕`/`签字`）或分离型双重否定 | **两者都不够**，须挂独立语义层或转人工 | chain 与 N13 同漏 3/3；本会话实跑 `classify_v12` 3/3 给 V2 |
| 高召回优先、宁可误拦不可漏 | naive / 朴素并集仅作**候选召回器**，结论交人工 | naive FP=33、并集 FP=20 |
| 需要「三层一致即通过」的自动放行 | **禁止** | 三层全 PASS 18 行里 3 行真断言（16.7%）；有效独立层数 ≈1 |

### 6.3 放弃的损失（如实列，含复核要求的补写）

1. **相对宽进层的 FP 压制消失**：回到朴素并集 48/72、FP=20（`_cs_recompute_out.txt:43`；`GATE_PIPELINE_COMPOSE.md:431`）。⚠️ 复核更正：这指的是回退到 **v1 朴素并集**，不是回退到 **N13 单层**。
2. **★ 补写（复核 §⑦ 要求）**：若放弃合成链、改用 **N13 单层**，在这 74 行上 **FP 从 2 降到 0**（本会话实算 `chain FP=2 n13 FP=0`），correct 从 69 升到 71（但这是 harness 免考卷口径，见 §3.2；对齐口径为 66 vs 69）。这一项对「放弃」有利，**必须列出，不许隐去**。
3. **冲突仲裁与逐 span 裁决结构消失**：K2 同句混用 / K1 双重否定 / K9 A-B 精筛等规则作废（`_gp_pipeline.py:98-116,162-180`）。⚠️ 复核更正：25 条冲突行上 N13 单层本身 25/25，故「将无人仲裁」不是相对单层的独占损失。
4. **多词表域没有调度器**：C07 `已填` 等 span 退回「N13 完全不认 ⇒ 静默 PASS」或「R10 宽进全拦」二选一（`_gp_DESIGN.md:86,243`）。
5. **R9/R11 正交项的并入点消失**（`_gp_pipeline.py:228-230`）；`conflicts[]` 这一「证据不独立」可观测性数据源消失（§5.2）。
6. **不损失什么（如实说）**：共同盲区 GP-A1/A2/A3 不因放弃而变好或变坏（N13 单层同样 3/3 全漏）；放弃**不解决**过拟合、词表覆盖、`spans=0` 静默 PASS。

### 6.4 评测方法改进 + 考题混杂影响 + 本次最大方法论缺陷

**考题混杂影响**（`_cs_dump_out.txt:6-18,27-35`；`GATE_PIPELINE_COMPOSE.md:300-313`）：74 条混合了 N13 自家 42（其中 8 条探针失败回灌）、R10 构造 17、真件 7、GP 构造 12；四套词表混用；30 件历史语料与 6 件 TV 被排除且无「若纳入会怎样」的敏感性分析。后果：① `x/74` 混合训练集内成绩与构造样本成绩，无总体含义；② 对抗样本（GP-A 按已知盲区定向，`_gp_regression.py:121-130`）与舒适样本（N13_NEG/POS）共用一个分母，`correct/74` 随配比任意变（§3.3 已展示换子集排名就变）；③ 标注之人即规则之人（72→74 翻 3 条 expect）；④ 真件 7 条全 `expect=PASS`，「抓得住」完全没在真件上考过（`_final_consistency_check.txt:6-8`）。

**更公平的设计**：① 以「真实交付件全集」定抽样框，按域 × expect 正负分层、每层配额固定；② `train`/`dev`/`test` 三集合物理隔离，`test` 一次性封 SHA 盲评，探针失败回灌样本（N19–N26、GP-A）归 train、**不得进 test**；③ GroupKFold 按形态族分组（问句/表头/目录/同句混用/拆分/否定式），避免同形泄漏；④ 真值双盲 + Cohen's κ，争议进 `ambiguous` 单列；⑤ **输入契约列为硬性前提**：每行写 `(id, tokens_sha, text_sha, predicate_sha)`，所有层含 N13 单层一律同一 `tokens`，并**显式登记 chain 的第二词表 `n13_tokens`**（`_gp_pipeline.py:132,135`），缺列判该行无效；`_cs_align.py` 的「不一致 0 行」核对（`_final_align_check.txt:3`）可复用为门禁；⑥ 多指标：按 expect 分报 FP/FN、macro-F1、「三层全 PASS 条件错误率」、有效独立层数、bootstrap CI（74 条下差 2 条本就不显著）；⑦ 跨版对比固定样本集/标注/算法三要素，只改一项；⑧ 敏感性分析：纳入被排除的 30 件 + 6 件 TV + C07 词表外形态重跑。

**防过拟合（可执行）**：① 语料先 `hashlib.sha256` 封样登记台账再发题，实现方只拿只读路径 + SHA；② 规则变更与语料变更分账，`test` 一会话只跑一次；③ 新增样本标 `source=probe_failure_of:<probe_id>` 并同时给「不含这些样本的 test 成绩」，GP-A 整族隔离为 `adversarial`；④ 由未参与者按同义改写/换主语/换微段/换否定构式/CRLF 切换批量造变体；⑤ **门禁化**：本会话 `python -I -B -X utf8 -c "...re..."` 实算 `_gp_regression.py` 的 `assert=0 raise=0 sys.exit=0`，`GATE_PIPELINE_COMPOSE.md:442` 自认「门槛是文字约定，不是可执行门禁」，应加 `assert tokens_sha == expected` / `assert all_layers_same_tokens` / `assert test_sha == pinned`；⑥ 预注册评测口径（fp/fn 定义、词表归属、ABSENT 处理、冲突计不计 FAIL）并封 SHA。

**★ 本次最大方法论缺陷**：**比较双方的输入不一致，却把输出当成同一场考试的成绩来排名；而考试又是被考方自己出的题、自己批的卷。** 具体：`_gp_regression.py:143` 让 N13 单层恒用固定三词 `T`，`:145` 让 chain 用该行 `tokens`，19 行里 N13 在一份不含待判 token 的词表上被记「PASS 且判对」，产出 `FP=0 / 71-of-74`（**免考卷**）；对齐后立刻反转为 66 vs 69（`_final_align_check.txt:6-8`）。第二层：训练集 = 测试集 + 标注可变（`_n13_regression.py:104-112` 回灌、72→74 翻 3 条 expect + 换 4 条样本 + 换整套算法），`71/74`、`69/74`、`48/72` 彼此无因果关系却被并列。第三层：有效独立层数 ≈1 却按 3 层叙述，`P(r12=PASS|n13=PASS)=1.000`、R12 增量 0 bit，5 条错全落在无冲突行。⇒ **本次评测只能用来定位代码缺陷（K6 采信宽进、K7 死分支、词表契约分叉、共同盲区），不能用来下「合成链 vs 单层」的取舍结论。**

### 6.5 未验 / 未做（如实列）

- **零真机与采样代码**：按铁律一律未做（未启动任何游戏进程、未 taskkill、未读活进程内存；未写 hook / MiniDump / SuspendThread / StackWalk / 注入 / 动态内存解析）。
- **v1 并集原脚本未留盘**（本会话实算 `v1 union script present = False`；`_gpv_regress.py:64-75` 自认）：72 版只从只读 JSON 重算，**未重跑原脚本**，标「未验重跑」。
- **未重跑 `_gp_regression.py` 本体**（绝对只读目录，且会写回该目录）；以写域内 `_cs_align.py` 显式重建 74 行并核对 `不一致 0 行` 代替。
- **对齐实验的 chain 列未重跑**，直接取只读 JSON；chain 的第二词表输入 `n13_tokens`（`_gp_pipeline.py:132,135` 的 `n13_vocab`）未参与对齐（§3.2 边界），标「未验完全对齐重跑」。
- **未实装**任何独立性方案 / 谓词修改 / K 规则修改 / 语料修改（任务纪律禁止）；§5.4、§6.2 均为方案。
- **正式盲留出集与交叉验证未做**：`_cs_holdout.py` 的 20 条是写域内示例性扰动，其中 3 条与回归语料逐字重复（§3.4），其 80% / 94.1% **不是泛化点估计**，标「未验」。
- **未 commit、未 push**；`git log -1` 仍 `2657458`；五个只读目录 + 两件台账 `git status --porcelain` 与会话开始快照一致，九件只读件收尾 `hashlib` 全 MATCH 且字节数不变。
- 本件所有新产物仅落在 `lead/chain_vs_single_20261109/`：`CHAIN_VS_SINGLE.md` 及本会话实跑重定向的 `_final_recompute_check.txt`、`_final_align_check.txt`、`_final_consistency_check.txt`、`_final_attrib_check.txt`。
