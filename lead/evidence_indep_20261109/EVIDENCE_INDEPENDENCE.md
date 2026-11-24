# EVIDENCE_INDEPENDENCE.md

写域：`lead/evidence_indep_20261109/`。本会话唯一写入目录；只读域与两件台账一律未改（见 §6 只读完整性实跑）。
交付性质：**量化与设计**。不改任何谓词模块、不改任何语料、不改任何编排层代码；所有实验用本任务写域的独立脚本。

---

## 1 目的与边界

**目的**：回答「三层（R10 / R12 / N13）一致通过能不能按 3 个独立证据计」，并把「独立」从声明降成**代码级可机检判据**，再给出相关性量化、去相关后的剩余判别力、第四层（V1V2）兜底实验、工程准入方案与折算结论。

**铁律边界（本会话遵守情况逐项如实登记）**：

| 铁律 | 本会话 |
|---|---|
| 零真机：不启 `gamemd.exe` / `ra2loader` / `YURI.exe`、不 `taskkill`、不读活进程内存 | 遵守；运行态一律标「未验」 |
| 零采样代码：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入、不写动态内存解析 | 遵守；脚本只用 `ast` / `re` / `json` / `hashlib` / `importlib.util` 静态读盘 |
| 绝对只读：`lead/gate_pipeline_20261109/`、`lead/chain_vs_single_20261109/`、`lead/gate_n13_20261109/`、`lead/gate_v1v2_20261109/`、`lead/gate_fp7_20261108/`、`lead/count_invariant_20261109/` + 两件台账 | 遵守，实跑见 §6 |
| 唯一写域 = `lead/evidence_indep_20261109/` | 遵守，本会话新增 7 件产物（6 件 `_eind_` 前缀 + 本交付件 `EVIDENCE_INDEPENDENCE.md`） |
| 不 commit、不 push | 遵守，`git log -1` 仍 `2657458` |
| Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib` | 遵守（脚本另加 `-B` 防 `__pycache__` 污染只读域） |
| 只做量化与设计，不改谓词模块与语料 | 遵守 |

**本会话实跑命令（全部 `python -I -X utf8 -B` + 绝对路径）**：

1. `python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/evidence_indep_20261109/_eind_manifest.py before` → `manifest before n_files = 169`
2. `python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/evidence_indep_20261109/_eind_verify.py` → `EXIT=0`，产出 `_eind_verify_out.json` / `_eind_verify_stdout.txt`
3. `python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/evidence_indep_20261109/_eind_manifest.py after` → `{"added": [], "removed": [], "changed": [], "PASS": true}`
4. 辅助只读探查：`python -I -X utf8 -B -c "..."`（回归 JSON 结构、φ 定义复算、单层成绩、磁盘真实标识符），输出见本文逐处引用。

`_eind_verify.py` 本会话迭代 4 次（2 次占位键解析失败、1 次变量名遮蔽 `H()`、1 次 φ 边际分组笔误），最终版 `EXIT=0`；每次失败都如实留痕在 `_eind_verify_stdout.txt` 覆盖前的中间输出，最终数字以最后的 `_eind_verify_out.json` 为准。**φ 自纠**：我首算得 `0.0292398`，与撰写人 `0.0293256` 不符；定位为我自己在 `math.sqrt` 里把 `(a+b)(c+d)(a+c)(b+d)` 写错分组，改为 `(b+c)(a+d)(a+b)(c+d)` 后一致（`_eind_verify_out.json:stats74.phi = 0.029325639294907786`）。这是本会话自己的检测脚本 bug，非撰写人错误。

---

## 2 上游指纹（九件）+ 代码级依赖核查

### 2.1 九件指纹（本会话 `hashlib` 实算，9/9 match）

命令：`python -I -X utf8 -B .../_eind_verify.py` → `_eind_verify_out.json:fingerprints_all_match = true`。占位键 `lead/gate_n13_20261109/_n13_predicates.py` 无路径，按 SHA+bytes 在 `lead/gate_n13_20261109/` 全扫**唯一命中**真名 `_n13_predicates.py`（`n13_real_name`），`hits=1`。

| # | 对象 | SHA256 | 字节数 | match |
|---|---|---|---|---|
| 1 | `lead/gate_n13_20261109/_n13_predicates.py` → `_n13_predicates.py` | `e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079` | 16649 | true |
| 2 | `lead/gate_v1v2_20261109/_v12_rule.py` | `15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0` | 9148 | true |
| 3 | `lead/gate_fp7_20261108/_g7_predicates.py` | `02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120` | 11743 | true |
| 4 | `lead/gate_pipeline_20261109/_gp_pipeline.py` | `25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7` | 15811 | true |
| 5 | `lead/gate_pipeline_20261109/_gp_regression_out.json` | `d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe` | 38575 | true |
| 6 | `lead/chain_vs_single_20261109/_cs_align_out.json` | `9dc062202fd9c00b2b74ce6393f29a90f18012a9914cf18dc9cd7ffa653f2698` | 11594 | true |
| 7 | `lead/chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md` | `3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2` | 49850 | true |
| 8 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 | true |
| 9 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 | true |

### 2.2 逐行依赖：N13 **转发** R10

编排方自己已承认（`lead/gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md:272` 原文）：「三层证据**不独立**（N13 C 类直接转发 R10 kind，`_n13_predicates.py:247-263`；R12 复用 `r10_context`，`_g7_predicates.py:144`；共用同一套字面词表），一致通过≠正确」。本会话逐行复核（行号来自 `_eind_verify_out.json:line_evidence`，源码为只读文件）：

| 证据 | 位置 | 内容 |
|---|---|---|
| 文档自认转发 | `lead/gate_n13_20261109/_n13_predicates.py:5-7` | 「C 否定式交既有 R10…判定，本件只消费其 kind…双重否定交 R12…不重写 R10 的正则」 |
| 函数签名收 R10/R12 当参数 | `_n13_predicates.py:183` | `def r13_scan(text, tokens=DEFAULT_TOKENS, r10_scan=None, r12_scan=None)` |
| 回调 R10 | `_n13_predicates.py:196` | `_, _, rhits = r10_scan(text, list(tokens))` |
| 回调 R12 | `_n13_predicates.py:200` | `_, dhits = r12_scan(text, list(tokens))` |
| 记录 R10 kind | `_n13_predicates.py:231` | `"r10_kind": r10_map.get((tok, gpos))` |
| **C 类放过仅在 R10 同意时** | `_n13_predicates.py:253-256` | `if r10_scan is not None and k in ("negation", "quote_mention"): rec.update(kind="C", exempt=True, …)`（`:254` 置 `kind="C"`） |
| 消费 R12 命中 | `_n13_predicates.py:242-243` | `if (tok, gpos) in r12_pos: rec.update(kind="D", …)` |
| 无 R10 时降级 | `_n13_predicates.py:257-259` | `r10_scan is None` → `kind="D", degraded=True`，默认 FAIL |
| 编排层注入 | `lead/gate_pipeline_20261109/_gp_pipeline.py:80-81`（命中行 `:81`） | `r13_assertions(text, n13_tokens, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)` |
| 编排层自述 C 是转发 | `_gp_pipeline.py:147-149` | 「C 只是『R10 说 negation』的转发，不构成独立证据」 |
| 共用提取器 | `_gp_pipeline.py:58-70` `extract_spans`、`:224` `ext = extract_spans(text, tokens)`、`:135-137` `resolve_conflicts` 内再 `re.finditer` | 同一 `tokens`、同一 `re.finditer` 位置口径 |
| `spans==0` 静默 PASS | `_gp_pipeline.py:179-180`（K5）+ `:253-256` `verdict="PASS"` 初始值；`_gpv_lazy_out.txt:13-17` 实测 `rows=0 / raise=0 / NEEDS_HUMAN=0` | GP-A2/A3 词表外同义改写时循环体根本不执行 |

**R12 复用 R10（同模块同函数）**：`lead/gate_fp7_20261108/_g7_predicates.py:144` `ctx = r10_context(text, m.start(), m.end())` 在 `r12_scan` 内；`:145` 仅取 `ctx["kind"] == "double_neg"` 这一 R10 分类的**子集**。`_g7_predicates.py:120` 是 `r10_scan` 内同一 `r10_context` 调用。故 R12 是 R10 的确定性函数，无独立信息源。

### 2.3 逐行依赖：V12 **复用**什么、不复用什么

| 项 | 结论 | 位置 |
|---|---|---|
| V12 唯一 import | `import re`（不 import g7 / N13 / 任何谓词模块） | `lead/gate_v1v2_20261109/_v12_rule.py:29` |
| V12 不引用 R10 对象 | 不以 `Name` 引用 `r10_context` / `DOUBLE_NEG_RE` / `NEG_RE`；`:43` 的 `ADJ_NEG_RE` 是自有正则（仅共享否定单字语义，非共享对象） | `_v12_rule.py:41-43` |
| V12 与 G7 共享模块级函数/正则名 | 0 个 | `_ei_02_code_indep_out.json:shared_top_level_names_g7_v12=[]` |
| **V12 与 G7 共用同一套子句切分字面** | **是**。`G7:71 CLAUSE_BREAK = "。！？；\n"` 与 `V12:66 _CLAUSE_SEPS = "。！？；\n"` 是**同一字面常量**，且同为子句边界定义 | `_g7_predicates.py:71` 定义 / `:87` `for ch in CLAUSE_BREAK` 用于 R10 否定回看窗；`_v12_rule.py:66` 定义 / `:69-75` `_segment` / `:97` `_segment(line, rel, _CLAUSE_SEPS)` |
| **V12 与 N13 共用词表字面** | **是**，共享 `'已入账'` | `_v12_rule.py:32-36` `V2_OVERRIDE` 含 `已入账`（命中行 `:36`）；`_n13_predicates.py:25` `DEFAULT_TOKENS = ("已入账","已追加","已生效")` |
| V12 与 N13 共享模块级函数/正则名 | 0 个 | `_ei_02_code_indep_out.json:d_indep_assert/N13|V12/shared_names=[]` |

**★ 精确 A2 复判（本会话 AST 实跑，修正旧检测器）**：撰写人 `_ei_05_admission.py:59-72` 的 `lits()` 只收 `Tuple/List/Set` 元素与 `re.compile` 首参，**漏掉裸字符串赋值**，故 A2 对 `V12|G7` 误判通过（其 `_ei_05_admission_out.json:a_assert_result/V12_vs_G7/PASS=true`）。我本会话 `precise_literals()` 补上 `ast.Constant(str)` 后实跑（`_eind_verify_out.json:A2_precise`）：

| 配对 | 精确共享模块级字面 | `precise_A2_pass` |
|---|---|---|
| `V12|G7` | `'。！？；\n'`（V12:66 `_CLAUSE_SEPS` ↔ G7:71 `CLAUSE_BREAK`） | **false** |
| `V12|N13` | `'已入账'`（V12:32 ↔ N13:25） | **false** |
| `G7|N13` | `[]` | **true** |

撰写人自己的 `_ei_02_code_indep_out.json:622-631` 明记 `G7|V12/exact_shared_literals=['。！？；\n']`、`:796-807` 明记 `G7|V12/no_shared_literal_string=false`；其 `what` 却写「与 G7 零共享模块级常量」、`evidence` 写「V12|G7 = true（五检全过）」——**内部矛盾**（复核方 `_eiv_04_final_out.json:writer_internal_consistency/contradiction=true` 亦独立指出）。本会话精确复判与复核方一致。这是「独立不能靠声明」的实测失效点。

### 2.4 是否共用词表：分两层回答

- **模块级常量层**：N13|G7 精确共享 **0** 条（`_eind_verify_out.json:A2_precise/G7|N13`）；N13|V12 共享 1 条；G7|V12 共享 1 条。所以「三层共用同一个 `DEFAULT_TOKENS` 常量定义」不成立。
- **运行时输入契约层**：**成立且是大面积共用**。本会话按 `_gp_regression_out.json:rows[].tokens` 独立重算（`_eind_verify_out.json:token_contract`）：55 行 `tokens=['已入账','已追加','已生效']` 与 `N13.DEFAULT_TOKENS` **完全相同**（55/74 = 74.3%）；另 17 行 `BAD_BAN=['已生效','可应用母本','放行 N-5','已入账','已追加']` 是同一三词的**超集**；合计 **72/74 = 97.3%** 行的提取器 / R10 / R12 / N13 喂的是同一套三词字面词表。余 2 行是 C07 域四词/三词各 1 行。`lead/chain_vs_single_20261109/_cs_info_out.txt:16-20` 独立记载同一 55/17/1/1 分布。
- 另有契约分叉：`_gp_regression.py:143` 让 N13 单层**恒用固定三词 `T`**，`:145` 让 chain 用该行 `tokens`；`CHAIN_VS_SINGLE.md:282` 与 `_final_align_check.txt:6-8` 记对齐后成绩由 71/74 反转为 66 vs 69。故 74 行上「N13 fp=0」含免考成分，不是泛化证据。

### 2.5 代码级独立性判据（可机检，不是声明）

`assert_independent(mod_a, mod_b, pipeline)` 五检（撰写人 `_ei_05_admission_out.json:b_machine_assert`，本会话以精确 A2 修订）：

- **A1** 双向零 `import` / 零属性引用；编排层不得把 A 的返回容器注入 B。
- **A2′（修订）** 模块级字面精确比对：收 `ast.Constant(str)`、`Tuple/List/Set` 的 str 元素、`re.compile` 字面首参；**不得只收后两类**（旧检测器漏洞）。任一共享字面或共享正则模式 → 不独立。
- **A3** 零输出转发：编排层不得把 A 的函数/返回容器作参数注入 B；按被测两模块的函数名配对检测（不能把流水线里任何注入都算违规，否则误判 V12|G7）。
- **A4** 零同名顶层函数/类。
- **A5** 异源文件（SHA 不同）。

本会话精确复判结果：`V12|G7` **不过 A2′**；`V12|N13` **不过 A2′**（`'已入账'`）；`G7|N13` A2′ 过但**不过 A3**（`_gp_pipeline.py:80-81` 注入，N13 `:183` 收参）；`R10|R12` 不过 A3/A2（`_g7_predicates.py:144` 同模块调 `r10_context`）。**结论：现有 4 层中没有任何一对能同时过 5 检**，故一律不得按 2 层计。撰写人的 `V12|G7=true` 判据失效已在 §2.3 登记；这不翻转主结论（V12 更不独立只会强化「≈1 层」）。

---

## 3 相关性量化

### 3.1 74 行 r10×n13 交叉表与一致率（本会话重算）

命令：`python -I -X utf8 -B .../_eind_verify.py` → `_eind_verify_out.json:stats74`，与编排方 `【相关性量化】r10_x_n13` 逐格 `cross_table_match=true`（撰写人 `_ei_03_corr_out.json:15`）。

| r10 \ n13 | CATCH | PASS | 合计 |
|---|---|---|---|
| **CATCH** | 20 | 20 | 40 |
| **PASS** | 16 | 18 | 34 |
| 合计 | 36 | 38 | 74 |

- **一致率 = (20+18)/74 = 38/74 = 51.351%**（分歧 36/74 = 48.649%）。编排方担心的「高一致」在这份语料上**不成立**。
- φ = `0.029325639294907786`（≈ +2.93%，几乎零线性相关）；MI(R10;N13) = `0.0006204988812550678 bit`；H(N13) = `0.9994730201859836 bit`，H(N13|R10) = `0.9988525213047287 bit`，**残差信息 99.938%**。
- 单层/组合判别力（本会话 `python -I -X utf8 -B -c "..."` 从 `_gp_regression_out.json:rows` 实算）：R10 `35/74`（fp20 fn19）、N13 `71/74`（fp0 fn3）、R12 `39/74`（fp0 fn35）、chain `69/74`（fp2 fn3）；OR `51/74`、AND `55/74`、XOR `31/74`（撰写人 `_ei_03_corr_out.json:d_residual_power` 一致）。

**★ 一致率低 ≠ 误差独立**：标签层 H(N13|R10)/H(N13)=99.94% 只说明两层**判定几乎 statistically independent**，不说明**误差独立**。真值层证据：`both_CATCH=20` 全为真（0 FP），但 `both_PASS=18` 中有 **3 条 FN**（`GP-A1/GP-A2/GP-A3`），三层全 PASS 的条件错误率 **3/18 = 16.67%**；独立假设下应为 `q_r10·q_n13 = 0.487179×0.076923 = 0.037475`（3.75%），实测 `3/39 = 0.076923`（7.69%），**乐观 2.0526 倍**（`_eind_verify_out.json:posterior.observed_over_indep`）。这 3 条正是 N13.C 转发 R10 kind 与 `spans==0` 死分支的**共同盲区**——代码级确定性依赖，不是随机重合。

### 3.2 一致率高说明什么 + 额外信息量定量框架

一般框架（撰写人 `_ei_03_corr_out.json:c_90pct_framework`，本会话 `_eind_verify_out.json:extra_info_90pct` 独立重算）：设两层标签一致率 ρ，且假设**对称不一致 + 两层各为均衡二值（H(C)=1 bit）**——这两个假设必须写明，否则公式不成立（两个各 95% 准确、误差独立的分类器也有约 90.5% 标签一致率，标签一致不能直接当误差相关）。

- 第二层**新增信息** = `H(C2|C1) = H(ρ)`。ρ=0.9 → `H(0.9) = 0.4689955935892811 bit`。
- **冗余信息** = `I(C1;C2) = 1 − H(ρ) = 0.5310044064107189 bit`（53.10%）。
- 完全独立的第二层应给 1.000 bit，故 ρ=0.9 时**只有 46.90% 存活**。
- 折算相关系数 `ρ_eff = (ρ − 0.5)/0.5 = 0.8`；设计效应 `n_eff = n/(1+(n−1)ρ̄)`：以 ρ̄=ρ_eff=0.8 代入得 `2/1.8 = 1.1111`（撰写人口径），以 ρ̄=标签一致率 0.9 代入得 `2/1.9 = 1.0526`（复核方 `_eiv_03_stats_out.json:110`）。两者口径不同，须并列不得混用。
- 似然比折损：`log LR₂|₁ = (1−ρ_eff)·log LR₂ = 0.2·log LR₂`。例 s=0.9/f=0.1 → `LR₂=9`（`3.169925 bit`）→ 实际只增 `0.633985 bit`。
- 对照本语料实测 ρ=0.5135 ≈ 独立基线 0.5：按此框架「标签层几乎无冗余」，但**这与 §3.1 的真值层 2.05 倍风险放大并存**——正是「标签独立 ≠ 误差独立」的量化表现，两套口径不可混用。

### 3.3 去相关后的剩余判别力

命令：`python -I -X utf8 -B .../_eind_verify.py` → `_eind_verify_out.json:posterior`；上游对照 `lead/chain_vs_single_20261109/_cs_info_out.txt:1-11`。

- 先验 `π = 39/74 = 0.527027`；后验阶梯（`P(CATCH | 全 PASS)`）：`0.5270 → N13 0.0789 → +R10 0.1667 → +R12 0.1667`。
- **R12 增量判别力 = 0 bit**：`P(r12=PASS | n13=PASS) = 38/38 = 1.000`（`_ei_07_final_out.json:95`），加 R12 后 `n_pass=18 → 18`、`wrong=3 → 3`，后验 odds 比 = 1，`log2 = 0.0`。
- **R10 相对 N13 是负贡献**：把「都过」后验从 0.0789 **抬高**到 0.1667（信息增益 `I₁=0.4481 → I₃=0.3604`，比值 `0.8042`），因为 `n13=PASS & r10=PASS` 的条件反而富集了 GP-A 三条共同盲区。
- 三个等效独立层数估计量（**并列，口径不同，不可张冠李戴**）：
  - `k_eff`（上游概率比 `ln(p₃/π)/ln(p₁/π)`，`_cs_info.py:39`） = `0.6064124084365424`（≈0.61）
  - `k_eff`（后验几率比）= `0.6696629280720958`（≈0.670）
  - 信息增益比 `I₃/I₁` = `0.8042328042328043`（≈0.804）
  - 三者方向一致：均 ≈1 或更少；`n_eff(ρ̄=0.9)=1.0526`。**有效独立层数 ≈ 1**。
- 去相关后的可用判别力（74 行消融）：N13 单层 `71/74` 已接近 chain `69/74`；R10 `35/74`、R12 `39/74`、AND `55/74`、OR `51/74`。「三层一致」不比 N13 单层更能判对。
- **留出集误差相关双检：未跑成，标「未验」**。只读 `_cs_holdout_out.json` 每行仅 `id/expect/n13/chain/v12/note/text`（本会话 `_eind_verify_out.json:holdout_columns`），**无 r10/r12 列**，`holdout_error_corr_feasible=false`，无法算 `ρ=corr(1{err_i},1{err_j})`；且 20 条中 `U-N10/U-N11/U-N12` 与 GP-A2/A3/A1 逐字重复（本会话实算 `verbatim_duplicate_ids`，与 `_final_consistency_check.txt:16-29` 一致）。我补算了 **train=test 上的描述性**相关系数（`_eind_verify_out.json:train_test_error_corr_DESCRIPTIVE_ONLY`）：`ρ(r10,n13)=0.19473`、`ρ(r10,r12)=−0.18681`、共同出错 3 / 15 行——**明确标注这 74 行是 train=test（`CHAIN_VS_SINGLE.md:129,282`），不是生产置信界，也不能替代盲留出集双检**。

---

## 4 独立证据兜底（V1V2 作第四层）

### 4.1 实跑：能否兜住 GP-A1/A2/A3

命令：`python -I -X utf8 -B .../_eind_verify.py` → `_eind_verify_out.json:fourth_layer`。语料按 `_gp_regression.py:52-130` 逐条重建，74 个 id 与 `_gp_regression_out.json:rows` **全集合相等**（脚本内 `assert`）；V1V2 判定口径与 `lead/chain_vs_single_20261109/_cs_holdout.py:65-72` 完全相同（`set(V2_OVERRIDE + DEFAULT_TOKENS)` 逐处 `classify_v12(...).verdict=='V2'` → CATCH）。

| id | 三层全 PASS | spans | V12 | 硬命中 | 机制 |
|---|---|---|---|---|---|
| GP-A1 | 是 | 1 | **CATCH** | 否（`only_default=true`） | 命中 `已生效`，`override=""`、`review_flag=true` → **S3 DEFAULT「判不了→fail-closed」**（`_v12_rule.py:167-170`），**不是语义识别** |
| GP-A2 | 是 | 0 | **CATCH** | 是 | `V2_OVERRIDE:登记闭合`（`_v12_rule.py:33`） |
| GP-A3 | 是 | 0 | **CATCH** | 是 | `V2_OVERRIDE:填毕` + `V2_OVERRIDE_RE`（`_v12_rule.py:34,38`） |

**3/3 全覆盖，但实质新信息只有 2/3**：A2/A3 靠第二套词表 `V2_OVERRIDE` 硬命中（真正独立于三词表）；A1 只是把「拿不准」翻成 fail-closed，任何拿不准的行都会同样 CATCH，不构成对该形态的语义判别。复核方 `_eiv_01_corpus_out.json` 独立重建得同一结论。

### 4.2 新误报量（本会话实跑）

- V12 **单层 74 行**：`47/74`（acc 63.51%，**fp=18、fn=9**）——`_eind_verify_out.json:fourth_layer.v12_single_layer`。
- 20 条未见变体：V12 `15/20`（**fp=4、fn=1**），取自只读 `_cs_holdout_out.json`；去掉 3 条逐字重复后 `12/17`（`_final_consistency_check.txt:26-29`）。
- `spans0_ids` 共 9 行、`all_pass_ids` 共 18 行（`_ei_06_net_out.json:3-33`）。

### 4.3 净收益（装配方式决定符号）

基线 chain `69/74`（fp2 fn3）。本会话 `_eind_verify_out.json:fourth_layer.variants` 全量重跑：

| 装配 | correct | fp | fn | 净 Δ 正确 | 救回 | 新增 FP |
|---|---|---|---|---|---|---|
| `0_baseline_chain` | 69 | 2 | 3 | 0 | — | — |
| `1_naive_OR_all4` | **56** | 18 | 0 | **−13** | GP-A1/A2/A3 | 16 条（`_ei_06_net_out.json:58-75`） |
| `2_monotone_spans0_or_allPASS` | 67 | 7 | 0 | **−2** | GP-A1/A2/A3 | 5 条 |
| `3_monotone_spans0_only` | **70** | 3 | 1 | **+1** | GP-A2/A3 | **1 条 = `R10-REAL-OBSERVATION_PROTOCOL_SPEC`** |
| `4_monotone_spans0_hard_override` | 70 | 3 | 1 | +1 | GP-A2/A3 | 同 1 条 |
| `5_monotone_allPASS_hard_override` | 69 | 4 | 1 | 0 | GP-A2/A3 | 2 条 |
| `6_monotone_gated_hard_override` | 69 | 4 | 1 | 0 | GP-A2/A3 | 2 条 |

**结论**：只有把第四层**限死在 `spans==0` 且用单调 OR（不 veto 既有 CATCH）**才净 `+1` 正确 / `−1` 错误（69→70，+1.35%；74 行下 ±2.7% 不显著），且 **GP-A1 在此配置仍漏**；朴素四层 OR 净 −13。**覆盖 3/3 但净收益 ≈0 到 +1，不能据此宣称「第四层已提升门禁」**。所有变体均为本任务写域独立脚本的**设计实验**，未实装到 `_gp_pipeline.py`。

### 4.4 第五个独立证据来源建议（按正交性排序）

1. **结构/密码学层 R11 + R9**（最干净）：`lead/gate_fp7_20261108/_g7_predicates.py:55-65`（`r9_check` 要素在场）与 `:157-222`（`r11_scan`：`hashlib.sha256` 现盘重算 + 文件存在 + 绑定行回验）。零文本词表、零否定正则，与断言层完全正交；`_gp_pipeline.py:228-230` 已把 R9/R11 作为「独立项」直接并入 problems，但**未计入本次 74 行判定**（`:146` 合成链只看越权断言面）。编排方 `GATE_PIPELINE_COMPOSE.md` 亦承认应「正交计入而非与断言层混合」。
2. **双盲人工标注 + Cohen's κ**：真值来源正交；κ 同时给出标注者间一致性，可校准 `q_i`。
3. **物理隔离的盲留出集 / 另一套语料**：`hashlib.sha256` 封样登记台账后发题，实现方只拿只读路径 + SHA；`GroupKFold` 按形态族分组，一次性盲评（`CHAIN_VS_SINGLE.md:282` ①⑤⑥ 已列可执行门禁化步骤）。
4. **同行评审**：不同会话、不同人，输入契约与词表另锁 SHA。
5. **仅作诊断、不得计入一致层数**：`neg_count≥2 且 dbl=False` 的统计旁路（`GATE_PIPELINE_COMPOSE.md:284-294`、`_gpv_lazy_out.txt:1-11` 实跑 3/3 兜住 GP-A1/A2/A3、16 正样本 0 误伤、26 负样本 0 触发；`:510` 记**未并入交付链**）。它复用 R10 的 `NEG_RE`（`_g7_predicates.py:69`），按 A2′ 判**不独立**，只能诊断。

**以上第五层增益均无留盘盲评数据 → 全部标「未验」。**

---

## 5 工程方案

### 5.1 独立性准入条件 C1–C7（撰写人 `_ei_05_admission_out.json:a_admission_conditions`，本会话采纳并强化 A2）

- **C1** 模块间双向零 `import` / 零属性引用；编排层不得把 A 的返回容器作参数注入 B（A1/A3）。
- **C2** 零共享词表常量与零共享正则对象；**必须按 §2.5 的 A2′ 精确比对，包含裸字符串赋值**（旧 `lits()` 漏洞已致 V12|G7 误准入）。
- **C3** 输入表征正交：不同 tokenizer / 不同特征提取，**不得共用 `extract_spans` 或同一个 `tokens` 变量**（现状 72/74 行共用同一三词，见 §2.4）。
- **C4** 数据来源正交：不同真值来源（人工标注 / 结构回验 hashlib / 另一套语料），各自在盲留出集有独立 fp/fn 记录。
- **C5** 失败模式正交：既有共同盲区上单层命中率 > 0，且舒适样本上新 FP 不超上限（V12 现状 fp=18 不过）。
- **C6** 误差相关可测：给出两两 MI / φ / 联合漏报率；准入阈值 `MI ≤ 0.05 bit` 且 `P(两层同错|真值) ≤ 各层漏报率之积 × 1.5`。（本语料 MI=0.00062 bit 达标，但联合漏报 2.05 倍超标 → 不过。）
- **C7** 声明输入契约并锁指纹：每层固定 `(predicate_sha, tokens_sha, text_sha)`，缺列判该行无效，不得参与「一致」计数。

### 5.2 可机检独立性断言

```text
assert_independent(mod_a, mod_b, pipeline):
  A1 双向零 import / 零属性引用                     ← ast.Import / ImportFrom / Attribute
  A2' 模块级字面精确比对（含 ast.Constant(str)）     ← 修订点，见 §2.3
  A3 零输出转发（按被测两模块函数名配对查注入）      ← 不能把流水线任意注入都算违规
  A4 零同名顶层函数/类
  A5 异源 SHA
  return A1 and A2' and A3 and A4 and A5
```

本会话精确复判：`V12|G7=false`、`V12|N13=false`、`G7|N13=false`（A3）、`R10|R12=false`。**当前没有任何一对过准入**；`G7|N13` 的 A2′ 过（共享 0 条字面）但 A3 不过，说明「零共享常量」不足以证明独立——必须同时查数据流。

### 5.3 n 层一致的置信度公式与假设

设 `E` = 真值应为 CATCH，`π = P(E)`；第 i 层灵敏度 `s_i`（E 时判 CATCH）、特异度 `c_i`（¬E 时判 PASS）、漏报率 `q_i = 1−s_i`。

```
P(all n PASS | E) = Π q_i  ≤  q_max^n
P(any missed, m spans)     ≤  m · q_max^n                       (union bound)
P(E | all PASS) = π Π q_i / [π Π q_i + (1−π) Π c_i]
odds(post) = odds(π) · Π (q_i / c_i)  =  odds(π) · Π LR_i
```

**假设（缺一不可，撰写人 `_ei_05_admission_out.json:c_confidence.assumptions` H1–H4）**：
- **H1** 各层误差在给定真值 E 下条件独立（本语料已被 §2.2/§3.1 证伪）；
- **H2** `q_i` 是**目标总体上**的上界，不是训练集上的点估计；
- **H3** 任何层的 `ABSENT` 不得静默折成 `PASS`（`_gp_pipeline.py:113` K7、`:179-180` K5、`spans==0` 死分支正是反例）；
- **H4** `s_i/c_i` 来自**盲留出集**，不是 train=test。

**本会话实算数值**（`_eind_verify_out.json:confidence`，`python -I -X utf8 -B .../_eind_verify.py`）：`π=0.527027`、`nE=39`、`nN=35`、`q_n13=3/39=0.076923`（Wilson95 z=1.96 → `[0.026507, 0.203214]`）、`q_r10=19/39=0.487179`、`c_n13=1.000000`、`c_r10=0.428571`；独立两层联合漏报**期望** `q_n13·q_r10 = 0.037475345167652864`（3.75%）；`P(E|2 独立层全 PASS) = 0.08878504672897194`（与撰写人 `0.0887850467289718` 吻合至浮点末位）。**★ 措辞更正**：3.75% 是**独立假设下的期望**，不是分布无关上界；真上界是 **Fréchet–Hoeffding `min_i q_i = 0.076923`**（`_eind_verify_out.json:confidence.Frechet_upper_bound_min_q`），恰等于实测 7.69%。撰写人 `decorrelated` 段把它称「上界」是错的（复核方亦指出）。74 行 train=test，以上为描述值，**不是生产置信界**。

### 5.4 相关时如何修正

- **分布无关兜底**：`P(all PASS|E) ≤ min_i q_i`（Fréchet–Hoeffding）；不得用 `Π q_i`。本例 0.0769 vs 0.0375，差 2.05 倍。
- **等相关 probit**：`P(all PASS|E) = ∫ Φ((Φ⁻¹(q)−√ρ·t)/√(1−ρ))^n φ(t) dt`；`_ei_05_admission_out.json:d_correlation_correction` 给 ρ=0/0.3/0.6/0.9 的 `joint_miss` = 0.0375 / 0.0774 / 0.1174 / 0.1573，均被 Fréchet 0.0769 兜住（ρ>0 时等相关近似越界，须取 min）。
- **设计效应**：`n_eff = n/(1+(n−1)ρ̄)`（ρ̄ = 平均两两**误差**相关）。
- **似然比折损**：`log LR₂|₁ = (1−ρ_eff)·log LR₂`，即 `P(E|C1,C2)` 用 `LR₁·LR₂^(1−ρ_eff)`；ρ_eff=0.8 时第二层只剩 20% 对数几率（3.170→0.634 bit）。
- **结构性 ρ=1 的子总体**：N13.C 是 R10 kind 的确定性函数（`_n13_predicates.py:253`），该子总体不能用随机相关近似，必须**整支剔除**后再计层数。
- **逐层消融 + AND/OR/XOR 对照**（§3.3）：`N13 71/74` vs `chain 69/74` 直接显示合成无增量。
- **估计 ρ 的正确数据**：盲留出集上 `ρ = corr(1{err_i},1{err_j})`，列须含全部层判定与 `expect`；本会话已证只读 holdout 缺 r10/r12 列 → **未验**。

---

## 6 复核回件 + 结论 + 未验

### 6.1 复核 verdict 如实登记

**复核 verdict = `partial` → 本交付按铁律标 `unconfirmed`。** 复核方 `ranCommands=28`；决定性理由（复核方 `whatBreaksIt`，本会话 §2.3 精确 AST 复判一致）：

- 撰写人核心断言为假：`what(2)`「V12 与 G7 零共享模块级常量」及「`V12|G7 = true`（五检全过）」不成立。`_g7_predicates.py:71` `CLAUSE_BREAK` 与 `_v12_rule.py:66` `_CLAUSE_SEPS` 同为 `"。！？；\n"` 且同为子句切分定义（G7 `:87` 界定否定回看窗；V12 `:69-75/:97` 界定分析单元）——正是铁律所指「共用同一套词表/同一个正则就不是两个证据」。撰写人自己的 `_ei_02_code_indep_out.json:622-631,796-807` 已记该共享与 `no_shared_literal_string=false`，却与 `what` 矛盾。根因 `_ei_05_admission.py:59-72` `lits()` 漏裸字符串赋值。
- **留出集误差相关双检未实跑**：只在 `decorrelated` 作为「估计方法②」提出；只读 holdout 无 r10/r12 列、3 条逐字重复（§3.3 本会话复核）。撰写人已诚实标「未验／不是生产置信界」，但双检本身缺失。
- 数值/标签瑕疵（不翻盘但登记）：(a) `decorrelated` 把 3.75% 称「上界」，真上界 Fréchet `min q_i=0.0769`（§5.3）；(b) `_ei_07_final.py:94` 写「2.6 倍乐观」，正确 `0.0769230769/0.0374753452 = 2.0526`（正文写对）；(c) `discount` 把 `0.61`（概率比）标成「按后验信息量折算」，后验几率版 `0.670`、信息增益比 `0.804`，三者张冠李戴（§3.3）；(d) 90% 框架 `H(C2|C1)=H(ρ)` 隐含「对称不一致 + H(C2)=1」，且把标签一致率当误差相关，假设未写清（§3.2 本会话已补写）。
- **不判 refuted**：主结论（按 1 层计、绝不可按 3 层、R12 增量 0 bit、V12 净收益≈0）复核方 ③⑤⑦ 逐项独立复算一致；V12 更不独立只会**强化**「≈1 层」。

### 6.2 绑定行（本会话 `hashlib` 实算，9 件全等于编排方基线）

被核对象 SHA256 = e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079，字节数 = 16649
被核对象 SHA256 = 15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0，字节数 = 9148
被核对象 SHA256 = 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120，字节数 = 11743
被核对象 SHA256 = 25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7，字节数 = 15811
被核对象 SHA256 = d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe，字节数 = 38575
被核对象 SHA256 = 9dc062202fd9c00b2b74ce6393f29a90f18012a9914cf18dc9cd7ffa653f2698，字节数 = 11594
被核对象 SHA256 = 3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2，字节数 = 49850
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

### 6.3 结论：三层分类 + 折算数字与理由

| 层 | 分类 | 代码级依据 |
|---|---|---|
| **R10** | 上游／被转发与复用，**非独立证据根** | `_g7_predicates.py:78-130`；被 N13 `:196/:231/:253` 与 R12 `:144` 消费；`_gp_pipeline.py:80-81` 注入 |
| **R12** | **不独立** | 同模块 `:144` 调 `r10_context`，是 R10 `double_neg` 子集；`P(r12=PASS|n13=PASS)=1.000`，增量 **0 bit** |
| **N13** | **部分独立** | A/B 微段判据自带局部证据（`_n13_predicates.py:96-106,137-139`），但 C 类 `:253-256` 确定性转发 R10 kind、`:242-243` 消费 R12；D 类的「默认 FAIL」是 fail-closed 不是精筛（`_gp_pipeline.py:147-149` 亦自认） |
| **R9 / R11** | 独立但**未计入** 74 行判定 | `_g7_predicates.py:55-65,157-222`（hashlib/文件存在，零文本词表）；`_gp_pipeline.py:146` 只看越权断言面 |
| **V1V2** | 相对 G7/N13 **都不过 A2′** | V12:66 ↔ G7:71 共享子句字面；V12:32 ↔ N13:25 共享 `'已入账'` |

**★ 折算：三层一致按 `1 层` 计（numeric = 1），绝不可按 3 层。** 理由（全部本会话实跑或有文件:行）：

1. 依赖图为单一根 `R10 → {R12, N13.C}`（§2.2/§2.3），独立证据根 = 1；
2. `R12` 增量信息 **0.0 bit**（后验 0.1667→0.1667）；`R10` 相对 N13 把「都过」后验 0.0789 **抬高**到 0.1667（负贡献）；
3. 72/74 行（97.3%）共用同一三词运行时词表，且共用 `extract_spans`（§2.4）；
4. 三个并列估计量 `0.6064`（上游概率比）/ `0.6697`（后验几率）/ `0.8042`（信息增益比），`n_eff(ρ̄=0.9)=1.0526` —— 均 ≈1 或更少；
5. 真值层：三层全 PASS 错误率 `3/18=16.67%`，独立假设期望 `3.75%`，**放大 2.0526 倍**；分布无关上界 Fréchet `min q_i = 7.69%`；
6. 消融：N13 单层 `71/74` ≥ chain `69/74`，「三层一致」无增量判别力。

**还需补什么层**（按 §4.4 顺序）：① 结构/密码学层 R11+R9 正交计入；② 双盲人工标注 + Cohen's κ；③ 物理隔离的封 SHA 盲留出集（含全部层判定列，用于跑 `ρ=corr(1{err_i},1{err_j})` 双检）；④ 同行评审；⑤ `neg_count≥2` 旁路仅诊断、不计层。**补层前，人工复核是必需最后一道，链输出应写 `PASS + coverage_note`，不得写「合成链已全覆盖」**（`GATE_PIPELINE_COMPOSE.md:501`）。

**判不了什么**：本任务只做量化与设计，不能判定改谓词后的实际效果（未实装）；不能判定生产语料上的 `q_i/ρ`（74 行 train=test 且含定向构造对抗样本）；不能判定 V1V2 在 `spans>0` 区域的语义正确性（本次只按字面词族 + 三词做 span 扫描，无人工语义标注）；不能判定「三层是否在任何语料上都 ≈1 层」（只在这 74 行上成立）；不能判定第五层的增益（无留盘盲评）。

### 6.4 未验项（逐项如实列）

- **真机运行态**：`gamemd.exe` / `ra2loader` / `YURI.exe` 的运行态、活进程内存 —— 铁律零真机，**未验**。
- **留出集误差相关双检**：`ρ=corr(1{err_i},1{err_j})` 在盲留出集上 —— 只读 `_cs_holdout_out.json` 缺 r10/r12 列且 3 条逐字重复，**未验**（本会话只补了 train=test 的描述性 `ρ`，明确不作双检）。
- **生产 `q_i` / `s_i` / `c_i` 与 Wilson 界的泛化有效性**：74 行 train=test（`CHAIN_VS_SINGLE.md:129,282`），**未验**。
- **Cohen's κ / 双盲人工标注一致性**：未做，**未验**。
- **第五层（R9/R11 正交计入、另一套语料、同行评审、结构回验）的实际增益**：无留盘盲评数据，**未验**。
- **`neg_count≥2` 编排层旁路的门禁化**：`GATE_PIPELINE_COMPOSE.md:510` 明记「未并入本交付链 → 未实装/未验」；本任务因铁律未实装，**未验**。
- **CRLF 位置归一、K8/FAIL_CLOSED 可达性、四个 `rule_id` 与 `pos` 升序**：`GATE_PIPELINE_COMPOSE.md:510-514` 自列未实装/未验，本会话未重跑，**未验**。
- **改谓词后的效果**：本任务不改任何谓词模块与语料，所有工程方案均为设计，**未实装/未验**。

### 6.5 纪律实跑

- 只读完整性：`python -I -X utf8 -B .../_eind_manifest.py before` → `n_files = 169`；`.../_eind_manifest.py after` → `{"added": [], "removed": [], "changed": [], "PASS": true}`（六个只读目录 + 两件台账，排除 `__pycache__` / `.mimosa`）。
- 本会话新增 6 件产物全在 `lead/evidence_indep_20261109/` 且 `_eind_` 前缀：`_eind_manifest.py` / `_eind_manifest_before.json` / `_eind_manifest_after.json` / `_eind_verify.py` / `_eind_verify_out.json` / `_eind_verify_stdout.txt`，以及本交付件 `EVIDENCE_INDEPENDENCE.md`。
- `git log -1 --oneline` → `2657458`（未 commit、未 push）。
- 未启真机、未写采样代码、未改任何谓词模块与语料、未修改任何只读文件（含 `_eiv_*` / `_ei_*` 前序产物）。
- 复核 verdict `partial` 已如实登记并标 `unconfirmed`（§6.1），未把任何未跑项写成通过。

