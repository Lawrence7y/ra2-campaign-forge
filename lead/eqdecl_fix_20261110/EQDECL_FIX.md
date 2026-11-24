# EQDECL_FIX.md — 等式门禁 `_eq_detector.py` 假阳性修版成件（20261110）

被核对象：`lead/eqdecl_fix_20261110/_ef_detector.py`（修版检测器，复制自原件后修改）。
原件：`lead/eqdecl_gate_20261109/_eq_detector.py`，SHA256 `f29a34b516c14a1320c5bd28a9788801e2c577ff8ae34eea0f41b3d035363472`、29795 字节。
本件所有「本会话实跑」均为撰写员（第三棒）在 2026-11-10 本会话用 `python -I -X utf8` + 绝对路径重跑所得；修版员与复核员的落盘件（`_ef_*.json`、`_efv_*.json`）作为对账件逐项核对。凡本会话没能重跑的，一律标「未验」。

## 1 目的与边界

**目的**：等式门禁第一版（`lead/eqdecl_gate_20261109/EQDECL_GATE.md`，三关 9/9 通过）在编排方 45 行清点上产生 5 行 FAIL。修版任务要求：独立确认这 5 行是否全为假阳性、复现围栏缺陷、在**写域副本**上修复、重跑三关 + 45 行清单 + 全量并给出逐行前后对比。本件登记修版结果与复核回件。

**边界——不改任何原件**。本会话以 hashlib 实测 10 件基线指纹，与编排方【编排方指纹】逐项全等（实跑命令：`python -I -X utf8` 内联 hashlib 脚本，输出 `ALL_ORIGINALS_MATCH_ORCHESTRATOR_FINGERPRINTS = True`）：

| 只读域（全部未动） | 实测 SHA256 前 12 位 | 字节 |
| --- | --- | --- |
| lead/PENDING_DECISIONS.md | 3765eddbe96d | 52419 |
| lead/GOAL_THREE_TARGETS_20261018.md | 2baa0de45d41 | 759518 |
| lead/eqdecl_gate_20261109/_eq_detector.py | f29a34b516c1 | 29795 |
| lead/eqdecl_gate_20261109/_eq_full_out.json | efb6542717e9 | 3293219 |
| lead/eqdecl_gate_20261109/_eq_three_gates_out.json | 2c9c4fe995f6 | 33009 |
| lead/eqdecl_gate_20261109/EQDECL_GATE.md | cf07e14d9d90 | 92317 |
| lead/comparability_20261109/COMPARABILITY_AUDIT.md | c00833b3fef5 | 51927 |
| lead/layer_identity_20261109/LAYER_IDENTITY.md | ef6e4cc8a012 | 59941 |
| lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md | f737d8a52b51 | 45362 |
| lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md | 165474e20a5b | 63401 |

只读域逐条（铁律原文列名）：两件台账（上表前两行）、`lead/eqdecl_gate_20261109/` 全部件（含 `_eq_detector.py` 原件）、`lead/tautology_audit_20261109/`、`lead/layer_identity_20261109/`、`lead/metric_audit_20261109/`、`lead/keff_calc_20261109/`、`lead/evidence_indep_20261109/`、`lead/comparability_20261109/`、`lead/score_decomp_20261109/`、`lead/chain_vs_single_20261109/`。全量跑覆盖的另两个只读目录 `lead/gate_pipeline_20261109/` 与其派生件同样只读（`_ef_full_run.py:50-59`）。

**唯一写域 = `lead/eqdecl_fix_20261110/`**（本任务新建）。修版检测器 `_ef_detector.py` 落在此处（复制原件后修改，原件零改动）。写域内现有：修版件 `_ef_detector.py`；修版员验证件 `_ef_fence_state.py`、`_ef_mech.py`、`_ef_three_gates.py`、`_ef_full_run.py`、`_ef_diff45.py`、`_ef_fence_unit.py`、`_ef_fp_resample.py` 及其落盘 JSON；复核员验证件 `_efv_detector_noborrow.py`、`_efv_gates_*.py/.json`、`_efv_full_*.json`、`_efv_sample*.json`、`_efv_fp_*.json`、`_efv_fence*.py`；撰写员本会话新增 `_eqd_probe5.py`、`_eqd_noborrow_check.py` 与 `_eqd_*_fresh.json/.txt` 重跑落盘件；以及本件。

**其他边界**：零真机、零采样代码（本任务纯静态文档分析，无涉）；不 commit、不 push；指纹一律 hashlib。

## 2 ★ 缺陷确认

### 2.1 围栏内部未被排除——实跑证据

**原逻辑**：`_eq_detector.py:164` `HARD_BOUNDARY = re.compile(r"^\s*$|^#{1,6}\s|^-{3,}\s*$|^\s*```")` 只把 ``` **标记行**当硬边界；`build_segments`（`_eq_detector.py:205-219`）据此切段；`scan_file`（`_eq_detector.py:399-419`）对每个锚点直接 `classify_window`，**没有任何围栏状态机**。

**后果（实跑复现）**：`COMPARABILITY_AUDIT.md:157` 开围栏、`:165` 闭围栏，`:158-:164` 是脚本 stdout。本会话用修版件里的 `build_segments` 原样复现切段：

```
实跑：python -I -X utf8 _eqd_probe5 同段内联脚本（code_fence_lines + build_segments 现场）
输出：COMPARABILITY_AUDIT.md n_lines 502 … line 158 in_fence= True build_segments_seg= [(158, 164)]
```

即 ：158-:164 被切成**独立散文段**，`:158` 的 `chain_changed=18 | unresolved_changed=18 | 集合恒等? True`（原文见 COMPARABILITY_AUDIT.md:158）以 M3d_恒等 + M4d_集合恒等 + M5d_实跑输出 成为锚点，被当散文判 F1。修版员的独立围栏状态机 `_ef_fence_state.py` 实跑落盘 `_ef_fence_state_out.json`：CA 502 行、19 个围栏区间、:158 落在区间 **[157,165]**；编排方【围栏探针】同口径（502 行 / inside 156）。**计数口径对齐说明**：探针的 156 = 围栏内 118 行（content-only，v1）+ 38 个围栏标记行（19 区间 × 2，v2_incl_marks）；LAYER_IDENTITY.md 5 = 3 + 2。两口径的**成员判定完全一致**：本会话以修版件 `code_fence_lines`（`_ef_detector.py:272-296`）现场重算，CA:158 ∈ 围栏内、LI:13/223/242/338 全在围栏外（LI 唯一围栏区间 [250,254]）。

### 2.2 五行 FAIL 逐行的确切假阳机制

五行修复前 flags 与判定，本会话现场重跑（命令：`python -I -X utf8 _eqd_probe5.py`，加载**原件** `classify_window`；与修版员 `_ef_mech_out.json` 逐项一致）：

| # | 行 | 修复前判定 | 锚点形态 | 机制（本会话实测 flags） | 为什么是假阳性 |
| --- | --- | --- | --- | --- | --- |
| 1 | COMPARABILITY_AUDIT.md:158 | FAIL/F1/SUBSTANTIVE | M3d+M4d+M5d | E_eq=True(窗) O=True R_same=False | 围栏内 stdout（§2.1）；行文本身是「18 行翻转清单」的程序输出，非散文断言 |
| 2 | LAYER_IDENTITY.md:13 | FAIL/F1/SUBSTANTIVE | M2e+M3d+M5a+M5c | E_eq=True R_same=True I=True O=True | **目的陈述 + 选择疑问**：「**目的**：判定…究竟是**逻辑必然**还是**本批语料 + 输入契约的巧合**」（LAYER_IDENTITY.md:13 逐字）。旧 QUESTION 表（`_eq_detector.py:162`）只有 `是否/？` 两类，两项都不命中 ⇒ K3 没接住；「问 A 还是 B」被当成「断言 A」 |
| 3 | LAYER_IDENTITY.md:223 | FAIL/F3/SUBSTANTIVE | M3d | I=True O=True **R_same=False**，窗 [215,230] | **表格转述行**：`| 12 | _cs_info.py:39-43 / _cs_info_out.txt:9-11 | k_eff=0.61…恒等破则数值破 |`（LAYER_IDENTITY.md:223 逐字）。I/O 从 ±8/±2 窗内邻行 :216/:218 **借来**——那两行的 38/38=1、0 bit 是引用 KEFF/EI 的被评估口径；本行自身无范围词 ⇒ f3=I∧O∧¬R_same_line 误触发 |
| 4 | LAYER_IDENTITY.md:242 | FAIL/F1/SUBSTANTIVE | M3d+M5c | E_eq=True(**整窗**) R_same=True I=False，窗 [240,242] | **整窗被邻行字面 A=B 毒化**：`:240`「它**不是** `A=B` 的等价式」（LAYER_IDENTITY.md:240 逐字）让 E_eq（旧口径 `_eq_detector.py:256` 取整窗）为 True；`:242` 自身带「**本批语料事实**」范围声明（R_same=True）但 **f1 判据（`_eq_detector.py:362`）完全不看 R** ⇒ 救不了 |
| 5 | LAYER_IDENTITY.md:338 | FAIL/F3/SUBSTANTIVE | M2e+M3d+M4d+M5a | I_raw=True(**借**) O=True R_same=False，窗 [335,339] | **复核转述前缀 + I 跨行借用**：行首「【复核】明确『主结论已独立复现、成立』…」（LAYER_IDENTITY.md:338 逐字）在转述复核结论；I_raw 从 :339 的「定理」（「应改『在给定生产契约下是定理』」，:339 逐字）经 ±2 局部窗（`_eq_detector.py:267-268`）借入；CORRECTION 词表（`_eq_detector.py:157-160`）不含【复核】前缀 ⇒ denial=False |

**build_segments 切分复现**（本会话现场）：LI:13 → seg [(13,13)]；LI:223 → [(210,230)]；LI:242 → [(240,242)]；LI:338 → [(335,339)]；CA:158 → [(158,164)]。四行 LI 全部在围栏外（§2.1），围栏不是它们的成因——成因是词面判据的四类独立缺陷。

### 2.3 结论（缺陷确认）

5/5 全为假阳性，**真阳 0**。四类机制：① 围栏内部当散文（:158）；② 问句/目的陈述不在旧 QUESTION 词表（:13）；③ 表格转述行借邻行强度证据、且无同行范围（:223）；④ 整窗 E_eq 毒化 + f1 不看 R（:242）；⑤ 复核转述行借 :339 强度词、CORRECTION 无此前缀（:338）。

## 3 ★ 修复清单

修版全部在写域副本 `lead/eqdecl_fix_20261110/_ef_detector.py`（SHA256 `27e1f45d7a5dbf7abb51240bf3cb9940c77d227e2edfab33395410de2ba89492`、39265 字节，本会话 hashlib 实测），共 **6 处**（(d2) 嵌于 (d) 通道内；文件 docstring 第 6 行写「修 5 处」系笔误，复核员指出，本件如实记——纯文字瑕疵，不影响行为）。

### (a) K7：代码围栏内部整段 SKIP

- **原逻辑**：`_eq_detector.py:164/205-219/399-419`——``` 标记行只是硬边界，围栏内容自成段被当散文解析。
- **问题**：CA:158 脚本 stdout 被判 F1（§2.1/§2.2 行 1）。
- **新逻辑**：`_ef_detector.py:196-197` 新增 `FENCE_OPEN/FENCE_CLOSE`（开行可带信息串；闭行须同字符、长度 ≥ 开行、其后仅空白）；`:272-296` 新增 `code_fence_lines()` 状态机，**未闭合围栏兜底到文件尾**（宁可多跳不可误判散文）；`:516-548` `scan_file` 对围栏内锚点一律 `SKIP / K7_code_fence_interior / category=CODE`。
- **实跑验证**（本会话）：① 围栏单测 `python -I -X utf8 _ef_fence_unit.py` → **8/8，ALL_PASS=True**（含 unclosed_eof 兜底、shorter_close_not_close 不闭合、tilde 围栏、info_string 开行、栏内裸等式 SKIP/K7、**栏外裸等式 FAIL/F1 正控**）；② CA:158 现场 → `SKIP / None / CODE skip=K7_code_fence_interior`；③ 全量 `n_code_fence_lines` 逐件落盘；④ diff45 (d)：**围栏外锚点窗口 × 围栏内容重叠 = 0**（`_ef_diff45_out.json` fence_window_overlap n=0）——修版未改窗口构成。

### (b) QUESTION 词表增补：目的陈述与选择疑问

- **原逻辑**：`_eq_detector.py:162` `QUESTION = [是否, 是否定理, \?\s*$, ？\s*$]`。
- **问题**：LI:13 目的陈述 +「究竟是 A 还是 B」两项都不命中，K3 没接住（§2.2 行 2）。
- **新逻辑**：`_ef_detector.py:183-188` 增补 `究竟.{0,80}还是`、`\*{0,2}目的\*{0,2}[:：]`、`要回答的问题是`。目的陈述与选择疑问都是「问 A 还是 B」，不是断言 A。
- **实跑验证**（本会话）：LI:13 现场 → `SKIP / K3_question_not_assertion`；自检 10 控不退化（N5 提问负控仍 SKIP）——`python -I -X utf8 _ef_detector.py --selftest` → n_controls 10 / n_passed 10 / n_failed 0。

### (c) K9：表格转述行（不能只按首字符 `|` 判）

- **原逻辑**：`_eq_detector.py:300-317` skip 链只有 K1–K5；表格行没有任何专门通道，:223 型行靠 K1 都接不住（E/I 从邻行借）。
- **问题**：LI:223（引 `_cs_info.py:39-43`）被判 F3（§2.2 行 3）。同型：LI:384（整改行）、METRIC_CONVENTION_AUDIT.md:126（引 CHAIN_VS_SINGLE.md:214 判「错置」）。
- **新逻辑**：`_ef_detector.py:213-214` 新增 `TABLE_ROW` + `SOURCE_PTR`（`文件名.ext:` 形态）；`:397-401` 新增 `K9_table_relay_row`：**表格行 ∧（行内引其他文件 file:line 指针 ∨ 行内含 QUOTE_OR_REVIEW 整改语气）**才降级 SKIP。真断言也在表格里的行不受影响。
- **实跑验证**（本会话）：LI:223 → `SKIP/K9_table_relay_row`；**K9 正控不误伤**：EVIDENCE_INDEPENDENCE.md:294（本件自己的三层分类结论表行，无文件名指针、无整改语气）现场仍 `FAIL/F3`；45 行里 LI:213（SKIP/K1→SKIP/K9）、LI:376（UNDEC→SKIP/K9）为非 FAIL 行的换道，无退化。

### (d) E_eq 改锚点行自身判定（旧整窗口径保留为对照）

- **原逻辑**：`_eq_detector.py:256` `E_eq = _has(wtext, E_EQ_STRICT)` 取整窗（±8）。
- **问题**：LI:242 被 :240 的字面 `A=B`（否定句里的引用）毒化整窗；且 f1（`_eq_detector.py:362`）不看 R，R_same=True 也救不了（§2.2 行 4）。
- **新逻辑**：`_ef_detector.py:339-340` `E_eq = _has(atext, E_EQ_STRICT)`（锚点行自身），`E_eq_window = _has(wtext, …)` 保留旧口径**仅供对照不参与判定**；两段式「声明」义务只施加在写出该声明的行上。
- **实跑验证**（本会话）：LI:242 现场 → `SUBSTANTIVE_OK`，flags `E_eq=False E_eq_window=True`——毒化源被隔离，范围声明行不再吃 F1。

### (d2) f1 补同行范围豁免 `scope_qualified_eq`（修「f1 不看 R」的机制本体）

- **原逻辑**：`_eq_detector.py:362` `f1 = E_eq and (not T) and (not S)`——完全不看 R；(d) 只修了窗口毒化这一半。
- **问题**：TAUTOLOGY_AUDIT.md:642「**本 74 行观测等式**…`A=B` 的正确等价式是」（TAUTOLOGY_AUDIT.md:642 逐字，本会话重读原文确认）同行自带范围声明仍被判 F1，暴露机制本体。
- **新逻辑**：`_ef_detector.py:463-465` `scope_qualified_eq = E_eq ∧ R_same_line ∧ ¬I ∧ ¬(T∧S)`；`f1 = E_eq ∧ ¬T ∧ ¬S ∧ ¬scope_qualified_eq`；并入 `corrected_scope`。**T∧S 两段式行不走此豁免**（范围词不得顶替 Q3 依据义务）。
- **实跑验证**（本会话）：EVIDENCE_INDEPENDENCE.md:98（「运行时输入契约层…完全相同」同行带「契约」范围词）由 F1 → `CORRECTLY_SCOPED`（diff45 归因 `F1->CORRECTLY_SCOPED/None = 1`）。**如实记：TA:642 本身修后仍是 FAIL/F1**——:643 的 38/38=1 在 ±2 内借入使 I=True、阻断豁免（`_ef_fp_resample_out.json` 误报行注记）；即 (d2) 修好了判据本体、但该行还需 I 借用问题解决才脱榜（见 §5、§6 复核 (2)）。

### (e) K8：复核/审计转述前缀

- **原逻辑**：`_eq_detector.py:157-160` CORRECTION 词表不含【复核】类前缀；转述行的强度信号靠 ±2 局部窗借入（`_eq_detector.py:267-268`）。
- **问题**：LI:338 的 I 从 :339「定理」借来，被判 F3（§2.2 行 5）。
- **新逻辑**：`_ef_detector.py:203-204` 新增 `REVIEW_PREFIX`（行首可带 `-/*` 列表符的【复核】/【审计】/【评】/【复评】/【核】/[复]）；`:391-396` 在 skip 链中**置于 denial∧R_same_line 之后**——正确限定行不受 K8 影响。
- **实跑验证**（本会话）：LI:338 → `SKIP/K8_review_paraphrase_prefix`；**K8 正控不误伤**：LI:339 自身（「均**未验**」denial∧R_same_line）修复前后均 `CORRECTLY_SCOPED`（`_eqd_probe5.py` 现场）。

**共性设计**：六处全部是**字面/结构判据**，不引入语义猜测；判据本体（M1–M5、Q1–Q4、F1/F2/F3 定义）未动。

## 4 ★ 前后对比

### 4.1 表一：三关 × 9 案例（命令：`python -I -X utf8 _ef_three_gates.py --det <检测器> --out <落盘>`，本会话对两版各跑一次）

| 关 | 案例 | file:line | 期望 | 修复前实际 | 修复后实际 | 通过 |
| --- | --- | --- | --- | --- | --- | --- |
| 关一 | G1a | LAYER_IDENTITY.md:104 | TAUTOLOGY_OK | TAUTOLOGY_OK/-/TAUTOLOGY | 同前 | ✓ |
| 关一 | G1b | _li_LAYER_IDENTITY_PROOF:125 | TAUTOLOGY_OK | TAUTOLOGY_OK/-/TAUTOLOGY | 同前 | ✓ |
| 关一 | G1c | SCORE_DECOMP.md:235 | TAUTOLOGY_OK | TAUTOLOGY_OK/-/TAUTOLOGY | 同前 | ✓ |
| 关二 | G2a | METRIC_CONVENTION_AUDIT.md:104 | SUBSTANTIVE_OK | SUBSTANTIVE_OK/-/SUBSTANTIVE | 同前 | ✓ |
| 关二 | G2b | LAYER_IDENTITY.md:128 | PASS_QUALIFIED | PASS_QUALIFIED/-/SUBSTANTIVE | 同前 | ✓ |
| 关二 | G2c | KEFF_CALC.md:262 | SUBSTANTIVE_OK | SUBSTANTIVE_OK/-/SUBSTANTIVE | 同前 | ✓ |
| 关三 | G3a | METRIC_CONVENTION_AUDIT.md:108 | FAIL/F3 | FAIL/F3/SUBSTANTIVE | 同前 | ✓ |
| 关三 | G3b | EVIDENCE_INDEPENDENCE.md:149 | FAIL/F3 | FAIL/F3/SUBSTANTIVE | 同前 | ✓ |
| 关三 | G3c | METRIC_CONVENTION_AUDIT.md:107 | FAIL/F3 | FAIL/F3/SUBSTANTIVE | 同前 | ✓ |

**9/9 → 9/9（关一 3/3、关二 3/3、关三 3/3），零退化**；落盘 `_eqd_gates_before_fresh.json` / `_eqd_gates_after_fresh.json`，与修版员 `_ef_before/after_three_gates.json`、复核员 `_efv_gates_orig/fixed.json` 逐项一致。

### 4.2 表二：编排方 45 行清点逐行（命令：`python -I -X utf8 _ef_diff45.py`，本会话重跑；缩写见 §1 路径）

| file:line | 修复前 | 修复后 | 变化 |
| --- | --- | --- | --- |
| LI:1 | SKIP/K2 | SKIP/K2 | |
| **LI:13** | **FAIL/F1** | **SKIP/K3** | ★ (b) |
| LI:22 | SKIP/K2 | SKIP/K2 | |
| LI:26 | SKIP/K2 | SKIP/K2 | |
| LI:87 | SKIP/K1 | SKIP/K1 | |
| LI:104 | TAUTOLOGY_OK | TAUTOLOGY_OK | |
| LI:110 | SKIP/K3 | SKIP/K3 | |
| LI:112 | SKIP/K2 | SKIP/K2 | |
| LI:116 | SKIP/K2 | SKIP/K2 | |
| LI:122 | UNDECIDABLE | UNDECIDABLE | |
| LI:126 | TAUTOLOGY_OK | TAUTOLOGY_OK | |
| LI:127 | PASS_QUALIFIED | PASS_QUALIFIED | |
| LI:128 | PASS_QUALIFIED | PASS_QUALIFIED | |
| LI:182 | UNDECIDABLE | UNDECIDABLE | |
| LI:189 | CORRECTLY_SCOPED | CORRECTLY_SCOPED | |
| LI:197 | SKIP/K2 | SKIP/K2 | |
| LI:200 | SKIP/K2 | SKIP/K2 | |
| LI:208 | SKIP/K3 | SKIP/K3 | |
| LI:213 | SKIP/K1 | SKIP/K9 | ★ (c) 换道（非 FAIL） |
| LI:216 | CORRECTLY_SCOPED | CORRECTLY_SCOPED | |
| **LI:223** | **FAIL/F3** | **SKIP/K9** | ★ (c) |
| LI:225 | CORRECTLY_SCOPED | CORRECTLY_SCOPED | |
| LI:226 | CORRECTLY_SCOPED | CORRECTLY_SCOPED | |
| LI:228 | SKIP/K3 | SKIP/K3 | |
| LI:233 | UNDECIDABLE | UNDECIDABLE | |
| LI:234 | CORRECTLY_SCOPED | CORRECTLY_SCOPED | |
| **LI:242** | **FAIL/F1** | **SUBSTANTIVE_OK** | ★ (d) |
| LI:273 | SKIP/K1 | SKIP/K1 | |
| LI:279 | SKIP/K2 | SKIP/K2 | |
| LI:304 | SKIP/K1 | SKIP/K1 | |
| LI:326 | SKIP/K1 | SKIP/K1 | |
| LI:337 | UNDECIDABLE | UNDECIDABLE | |
| **LI:338** | **FAIL/F3** | **SKIP/K8** | ★ (e) |
| LI:339 | CORRECTLY_SCOPED | CORRECTLY_SCOPED | |
| LI:365 | UNDECIDABLE | UNDECIDABLE | |
| LI:372 | CORRECTLY_SCOPED | CORRECTLY_SCOPED | |
| LI:376 | UNDECIDABLE | SKIP/K9 | ★ (c) 换道（非 FAIL） |
| LI:393 | UNDECIDABLE | UNDECIDABLE | |
| LI:400 | UNDECIDABLE | UNDECIDABLE | |
| LI:409 | UNDECIDABLE | UNDECIDABLE | |
| LI:414 | SKIP/K3 | SKIP/K3 | |
| KC:340 | CORRECTLY_SCOPED | CORRECTLY_SCOPED | |
| SD:135 | SKIP/K3_intensity_without | SKIP/K3_intensity_without | |
| SD:239 | SKIP/K3_intensity_without | SKIP/K3_intensity_without | |
| **CA:158** | **FAIL/F1** | **SKIP/K7** | ★ (a) |

45 行 anchored 45/45；**findings 5 → 0**（before 落盘 `_eqd_full_before_fresh.json` listed_45_lines.n_findings=5；after 现场 `anchored = 45 / 45  findings = 0`）；变化 7 行，其余 38 行逐行无变化；**before-FAIL → after-FAIL = 0 行**（`_ef_diff45_out.json` n_new_fail=0）。

### 4.3 表三：全量 15 件计数（命令：`python -I -X utf8 _ef_full_run.py --det <检测器> --out <落盘> [--sample orig|none]`，本会话两版各跑一次；918 锚点两版相同）

| 指标 | 修复前 | 修复后 | 变化 |
| --- | --- | --- | --- |
| 文件数 | 15 | 15 | — |
| 锚点数 | 918 | 918 | — |
| **findings** | **212** | **144** | **−68** |
| — F1 | 57 | 29 | −28 |
| — F2 | 5 | 5 | 0 |
| — F3 | 150 | 110 | −40 |
| tautology_ok | 27 | 22 | −5（逐行归因见下） |
| passes | 188 | 196 | +8 |
| skips | 346 | 462 | +116 |
| undecidables | 145 | 94 | −51 |

修复前 totals 与存档原件 `_eq_full_out.json` 逐项全等（本会话比对 MATCH=True）——**基线复现成立**。

**回归检查（有没有新增误报/退化）——四道全绿**：
1. **918 锚点迁移矩阵新增 FAIL = 0**（`_ef_diff45_out.json` n_new_fail=0；原 SKIP/PASS 无一被新误报）。
2. 自检 10 控 10/10（`_eqd_selftest_fresh.txt`：n_controls 10 / n_passed 10 / n_failed 0）。
3. 围栏单测 8/8（§3(a)）＋ 围栏外窗口 × 围栏内容重叠 = 0。
4. 68 条 findings 收敛逐行归因（`_ef_diff45_out.json` loose_attribution，本会话重跑同数）：F3→SKIP/K9 = 38；F1→SUBSTANTIVE_OK = 10；F1→SKIP/K7 = 9；F1→UNDECIDABLE = 4；F1→SKIP/K9 = 3；F3→SKIP/K7 = 1；F1→SKIP/K3 = 1；F3→SKIP/K8 = 1；F1→CORRECTLY_SCOPED = 1。

**通过案例的变化（如实报，不隐瞒）**：tautology_ok 27→22，流失 5 行逐行查明（diff45 (c2) 本会话重跑同数）：TA:158（`F(A⊆B) = [] （必空 ⇒ 重言式）`）、TA:328（`assert not (inA and not inB)…`）、_ta:244（`assert inA <= inB…`）——三行在**围栏内**（TA 围栏区间 [157,164] 等，`_ef_fence_state_out.json`），是程序断言/输出不是散文重言断言，K7 判 SKIP **正确**；TA:289、_ta:203（「| **定义使然** | 一方就是另一方的定义/展开 |…」重言式分类学表行）引 LAYER_IDENTITY.md:104,126 指针，K9 判转述行**合理**。**无真流失**（关一 G1a/G1b/G1c 三个真重言锚点全部保持 TAUTOLOGY_OK）。

### 4.4 表四：精确率重估（估计不是测量）

修版后 findings 全量 144 条，两个独立抽样（均为估计，`IS_MEASUREMENT=false`）：

| 口径 | 样本 | 真命中 | 误报 | 精确率 | 来源 |
| --- | --- | --- | --- | --- | --- |
| 修版员重抽样（mention-非-use 统一口径） | 33/144 | 12（含弱真 5：MC:109、TA:388、TA:396、LI:54、_li:88） | 21 | **0.3636** | `_ef_fp_resample_out.json`（n_true=12 / n_false=21 / precision_estimate=0.3636） |
| 复核员独立分层抽样（seed=20261110，Hamilton 33/144） | 33/144 | 5（严口径 3 + 弱 2） | 28 | **0.1515**（严口径 0.0909） | `_efv_sample_judged.json` |

- **两个 headline 不可直接比**：全量 findings 中 TA/_ta 自指件占 98/144=0.6806，修版员样本只占 10/33=0.3030（`_efv_sample_judged.json` population_TA_TA_share / fixer_sample_TA_TA_share）——修版员样本系统性偏低估误报率。**复核判定 headline 0.3636 为 unconfirmed（partial）**。
- 重叠 9 条判定 **9/9 一致、零翻案**（KEFF:432/434 误报、_ke:96 误报、GP:247 误报、SD:122 误报、_ma:151 误报、MC:108 真、MC:109 真弱、EI:294 真）——分歧纯由抽样代表性造成。
- 修版员自报「全量误报约 9 成」的外推，与复核员 84.8%（28/33）一致。修版员并**如实**弃用上一任务 13/19 旧样本（其 KEFF:432/434/440 判真 vs LI:384 判误报系同机制双重标准，`_ef_fp_resample_out.json` precision_basis 逐字）。
- 21 条误报逐条清单与机制见 §5；12 条真命中逐条清单见 `_ef_fp_resample_out.json` rows（MC:107/108、_ma:76/77、EI:149/294/302 等为本件自己的裸观测等式+强度声明）。

## 5 ★ 残留假阳

### 5.1 逐条（修版员 33 条抽样中的 21 条误报，`_ef_fp_resample_out.json`，本会话重读逐条）

| 机制类 | 行 | 机制 |
| --- | --- | --- |
| ⑤ K9 指针/清单形态 | KEFF_CALC.md:432/434/440 | **非表格**整改清单行（「→ 1.000 是观测值非定理，须标…」引 EI:149/294）——K9 只覆盖表格行 |
| ④ 词面同形 | LAYER_IDENTITY.md:267 | 「决定性」作**方法名**（方法 A（决定性、结构性）） |
| ① mention-vs-use | TA:356/366 | 禁用串自检清单、强模式扫描 29 串清单回显——门禁要防的串出现在清单位=引用 |
| ① mention-vs-use | TA:474 | 批判性转述行：本行正是在指责 MC:108 形态 |
| ② 词表缺口 | TA:610/434、KEFF:325 | 「被撤回的是三个强度标签…」「不是恒等」「不能当定理」——CORRECTION 缺词 |
| ② 词表缺口 | KEFF:311、_ke:96 | 「A还是B」标题问句无「究竟」、标题引用被评估对象——QUESTION 缺形态 |
| ④ 论域外 | GP:247、SD:122 | 「等价于」用于算子定义、「结构完全相同」用于改写相似性 |
| ④ 子串命中 | CA:37 | only_A 是 ids_only_A 的子串（字段名） |
| ⑤ 无围栏回显 | LI:52 | 「输出：A_n 18 B_n 18 A==B True…」无围栏的运行输出行 |
| ① mention | TA:617/629 | 两段式示范/模板行、纠偏指令行 |
| ③ K9 指针变体 | _ma:151、_cmp:115 | 裸 `:214` 指针、无冒号 json 指针不匹配 SOURCE_PTR |
| ⑤ I 借用阻断 (d2) | TA:642 | 同行有范围词，:643 的 38/38=1 在 ±2 借入使 I=True |

机制类汇总（`_ef_fp_resample_out.json` residual_fp_mechanisms）：① mention-vs-use（TA/_ta 审计件自指，最大宗）；② 词表开放枚举缺口；③ K9 指针形态变体＋非表格清单行；④ E_EQ_STRICT 子串/论域外；⑤ I 借用阻断 (d2)、方法名同形、无围栏回显。

### 5.2 修不掉的清单（结构上限）——含复核员修正

1. **mention/use 词面不可判**（成立）：词面检测无法区分「使用」与「提及」。
2. **词表开放性**（成立）：逐词打补丁修不完。
3. **K9 指针形态变体 / 非表格清单行**（成立，属可修未修项而非上限——复核员与修版员残差清单一致）。
4. **行级判据看不到 doc 级两半结构**（成立）。
5. ~~「I 跨行借用…与保 G3c:107 借用结构同一约束，不可两全」~~——**被复核员对照实验证伪，本件标 refuted**：把 I_raw/U_local 改为锚点行自身判定后（`_efv_detector_noborrow.py`），本会话独立重跑（`python -I -X utf8 _eqd_noborrow_check.py`）：三关 **9/9**（G3c:107 行内自带 `38/38=1` 命中 UNIVERSAL_CLAIM，仍 FAIL/F3）、findings 144→106、**新增 FAIL = 0**（仅 TA:433/434 两行 F3→F1 换型仍 FAIL）、TA:642 被救回 CORRECTLY_SCOPED；消解 38 行中 31 行在 TA/_ta 提及区（本会话按文件清点 31/38），真实代价仅 MC:109 这类借 I 的真弱阳死亡（→SUBSTANTIVE_OK）。即「不可两全」是把**未做、未量化的 precision/recall 取舍**写成了结构上限，且引用的 G3c 依据错误。取舍本身真实存在（救 TA:642 死 MC:109），但必须作为**可做的取舍**呈现，不是上限。

### 5.3 能用于什么 / 不能用于什么

**修完能用于**：① 新写结论章的候选违规定位（真命中集中在「本件自己的裸观测等式 + 强度声明、同行无范围」形态：MC:107/108、_ma:76/77、EI:149/294/302）；② 已知格式违规初筛（45 行级 5/5 报出、三关零退化、918 锚点零新增 FAIL）。

**不能用于**：① 自动拒收 / 合并判据（抽样精确率 0.15–0.36，误报占绝对多数）；② mention/use 区分；③ 替代人工逐行复核。**结论：仍然只能只报不拒，不支持升级。**

## 6 复核回件 + 结论

### 6.1 复核回件（绑定行）

复核方独立复跑修版件与全套验收，verdict = **partial**；被核对象 `_ef_detector.py` 的指纹，复核方回件与本会话 hashlib 实测全等（实跑输出：`EF_DETECTOR sha256 = 27e1f45d7a5dbf7abb51240bf3cb9940c77d227e2edfab33395410de2ba89492`、`bytes = 39265`）：

被核对象 SHA256 = 27e1f45d7a5dbf7abb51240bf3cb9940c77d227e2edfab33395410de2ba89492，字节数 = 39265

**partial 的两处不完全成立（按交付规则标 unconfirmed / refuted）**：
1. **unconfirmed**：headline 精确率 0.3636 受样本构成偏差系统性偏高（修版员样本 TA/_ta 占 30%，全量占 68%；复核员独立分层 0.1515 / 严口径 0.0909；重叠 9 条 9/9 一致、零翻案——非隐瞒，是口径不可比）。复核员确认「全量误报约 9 成」外推与其 84.8% 一致。
2. **refuted**：残留清单中「I 跨行借用…不可两全」——复核员 noborrow 对照实验证伪（本会话独立复现，§5.2 条 5：三关 9/9、findings 144→106、新增 FAIL=0、TA:642 救回、代价 MC:109 弱阳死亡、31/38 消解行在 TA/_ta 提及区）。取舍存在但非上限。
其余全部验收数字（三关 9/9、findings 212→144 分型、tautology_ok 流失 5 行身份、45 行 5→0、918 锚点新增 FAIL=0、68 行归因、diff 仅 6 处修复无暗改、十件基线指纹 before/after 零差异）复核员均独立复现属实；小疵：`_ef_detector.py` docstring 写「修 5 处」实为 6 处（纯文字）。

### 6.2 五行最终判定

**5 行 FAIL 全部为假阳性，真阳 = 0**（本会话三棒独立一致：修版员实测、复核员复现、撰写员现场重跑 `_eqd_probe5.py`）。修后去向：CA:158 → SKIP/K7、LI:13 → SKIP/K3、LI:223 → SKIP/K9、LI:242 → SUBSTANTIVE_OK、LI:338 → SKIP/K8。45 行清单上修后 findings = 0，其中真阳性 = **0**——这是本门禁在该清单上的真实水平，不为好看保留假阳，也不虚增真阳。

### 6.3 能否升级

**不能**。修版后精确率估计 0.15–0.36（两个独立抽样口径），误报占绝对多数且集中在审计件自指（mention-vs-use 是词面检测的结构上限）；三关与 45 行级召回未变、全量 recall 数值没有人工全量标注（未验）。门禁维持**只报不拒**：报出候选供人工逐行复核，不得作为拒收/合并判据，不支持升级为拦截门。

### 6.4 元层面反思

1. **词面门禁的天花板在语义**：本次 5 个假阳没有一个是判据写错，全是「判据够不到的语境」（围栏、问句、表格转述、引用毒化、转述前缀）。修一批漏一批是词面方法的常态，6 处修复换来 findings −68 但残留 144，边际收益递减。
2. **精确率数字必须配抽样代表性说明**：修版员 0.3636 与复核员 0.1515 都是真的，差别只在样本里 TA/_ta 占 30% 还是 68%。结论里凡给比率，必须同时给分母构成；否则 headline 会被读成另一件事。
3. **「没做的取舍」不能写成「结构上限」**：noborrow 实验一小时就能做，做了就发现「不可两全」是假的——真实 tradeoff 是救 TA:642 死 MC:109，且 31/38 收益在提及区。把未量化的取舍包装成上限，会误导下一轮决策。
4. **自检有效**：K7/K8/K9 三处各配了正控（栏外裸等式、LI:339、EI:294），本会话全部现场验证未被误伤；「修复会不会打过正控」必须每次实跑，不能靠推理。
5. **诚实记账**：修版员如实报精确率较旧口径下降并弃用双重标准的旧样本、如实报 tautology_ok 流失 5 行并逐行归因、如实报 TA:642 修后仍 FAIL——复核员据此能把分歧精确定位到抽样代表性而不是事实翻案。

### 6.5 判不了什么（如实列）

- 全量 144 条 findings 的**逐条**真假（两棒各抽 33 条，其余 111 条未判）。
- 弱真阳（MC:109、TA:388、TA:396、LI:54、_li:88）的**语义层**对错——格式层成立（同行无范围词），语义层「算不算违规」门禁判不了。
- K8/K9/围栏豁免是否放过**本语料未见的新违规形态**（无负样本集，未验）。
- **召回率数值**（无全量人工标注；三关/45 行只是锚点级覆盖，未验为全量召回）。
- 复核员 noborrow 变体若落地，弱真阳（MC:109 类）损失对真实门禁价值的影响（取舍未量化到门禁目的层，未验）。

### 6.6 未验项汇总

- 全量 144 条逐条真假：未验（仅 33×2 口径抽样）。
- 召回率数值：未验（无全量标注）。
- 修版件对**其他目录**（chain_vs_single 派生件等不在 15 件清单内的 .md）的表现：未跑。
- `_ef_detector.py` docstring「修 5 处」文字瑕疵未改（改它需要重算指纹、且属被核对象本体，留待下任决定；行为无影响）。

——本件由撰写员落笔；引用全部来自本会话实跑命令+输出或 文件:行（`_eq_detector.py:162/164/205-219/256/267-268/300-317/359-363/399-419`、`_ef_detector.py:183-188/196-197/203-204/213-214/272-296/339-340/391-401/463-465/516-548`、被检文档逐字行、`_eqd_*/_ef_*/_efv_*` 落盘件）；未跑到的一律标「未验」。
