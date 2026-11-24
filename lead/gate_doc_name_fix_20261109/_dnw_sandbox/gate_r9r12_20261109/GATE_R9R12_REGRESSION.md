# GATE_R9R12_REGRESSION.md — R9/R10/R11/R12 四谓词门禁全历史回归报告（定稿）

撰写：回归报告撰写员（dynamic workflow 子代理）。日期：2026-11-09。
写域：`lead/gate_r9r12_20261109/`——本报告为撰写轮唯一新增文件。
上游：实装轮回件（谓词实装员：`_g9_gate.py` 四谓词实装 + 全历史回归）与复核轮回件（七步复核，verdict=confirmed）。本报告职责 = 把两轮回件落成正式回归报告，并对关键数字做撰写轮独立核实。数据来源三类标注：【亲跑】= 本轮实跑命令与输出；【机读】= `lead/gate_r9r12_20261109/_g9_regression_out.json`（7f16da21…/123691B）直读；【转述】= 实装/复核回件内容（本轮未重跑处如实标注）。

## 1 目的与边界

**目的**：把误报修正谓词 R9/R10/R11/R12（第 5/6/7/8 类修法，产自 `lead/gate_fp7_20261108/`）实装为可复用门禁模块 `_g9_gate.py`，在历史交付件语料上跑全历史回归，逐件出具判定、逐类统计残余误报，并为剩余类别给处理建议。

**边界（本轮铁律的执行口径）**：

- **不改模板、不改任何交付件**：`lead/gate_fp7_20261108/` 全部（尤其 `_g7_predicates.py`）、`lead/gate_template_20261108/` 全部件、以及回归扫描涉及的全部历史交付件一律只读。模块对谓词原件做加载前 hashlib 指纹门（`_g9_gate.py:40-52`），失配拒绝运行——本轮做过失配负例实测（见 §3.1），门确实拦。
- 零真机：未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存；零采样代码：全部产物为静态文本/哈希检查，仅 import hashlib/importlib.util/json/re/sys/pathlib。
- 唯一写域 = `lead/gate_r9r12_20261109/`；未 commit、未 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 hashlib 实算。
- 回归结论的适用面：**30 件语料 + TV 样本 8 件 + 真实件 4 件（另 CANDIDATE 附加口径 1 趟）**。30 件之外的全量扫描为复核轮附加动作，本报告引用其输出但未独立重跑（见 §5.2 与 §6 未验项）。

## 2 上游指纹与既有谓词记录

### 2.1 上游六件指纹（【亲跑】撰写轮开场 hashlib 实算，与派发指纹全符）

| 件 | 字节数 | SHA256（实算） | 比对 |
|---|---|---|---|
| lead/gate_fp7_20261108/_g7_predicates.py | 11743 | 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120 | 符 |
| lead/gate_fp7_20261108/_g7_patch.md | 12647 | 9a7f5b9d2f7b87f8cc5baf09205322fb5507552ff3834ca28bf772d0417df849 | 符 |
| lead/gate_fp7_20261108/GATE_FALSE_POSITIVE_5_6_7.md | 27211 | 63b4cb66118ba1d64452e2d4745d84f104f7ba9d6f3941b391f781d73f2d894f | 符 |
| lead/gate_template_20261108/GATE_TEMPLATE_FIXED.py.txt | 28128 | 543e79184258f9f96517fdc8d61d42e46a7cd544f11ce0ab3b78d9fd505e9abe | 符 |
| lead/PENDING_DECISIONS.md | 52419 | 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 | 符 |
| lead/GOAL_THREE_TARGETS_20261018.md | 759518 | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 符 |

写域实装五件指纹（【亲跑】，同一条命令）：`_g9_gate.py` 11623B = a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6（与复核绑定行逐字一致）；`_g9_regression.py` 6652B = 7074d7aa28498a5e51f8d038531f11543528fa28bbf8434907569502526b401a；`_g9_regression_out.json` 123691B = 7f16da217dba02008546d643bb51c0100d7126939df947ad0c46a4fd478f11d8；`_g9_regression.md` 33056B = c5aa1ee10b64571b7e10bc2a49c4f6c045e0873829c39bbf4cfae6814dab228d；`_g9_table_fragment.md` 8307B = 7a7576643f2837d9dfb62f4b9f131b6de0de33bd896c5dca4ec998c86e568d22。均与实装回件申报值一致。复核轮另留 `_g9v_*` 十件（fp/regress/subset/empty/corpus/verify 脚本与其输出 JSON），本报告引用其中 `_g9v_corpus_out.json`、`_g9v_regress_out.json` 两件的数据（§5.2、§6）。

### 2.2 既有谓词逐条记录（【亲跑】`_g7_predicates.py` 全文实读，行号为封版 02c17e49 版实测）

| 谓词 | 函数签名与行号 | 判据 |
|---|---|---|
| 朴素对照（非修正谓词） | `naive_gate(text, tokens, bind_re=NAIVE_BIND)` :15-24；`NAIVE_BIND` :13 | 既有门禁家族现状：裸子串查要素 + 紧邻绑定正则。第 5/8 类误报在此全数复现；模块用它做对照（不参与判定） |
| R9（第 5 类） | `r9_normalize(text)` :31-44；`r9_element_present(text, token) -> (present, layer)` :46-53；`r9_check(text, tokens) -> (problems, warnings)` :55-65 | 两遍归一化（顺序敏感：N2 先把反引号跨度内换行删除，N1 再把包裹字符 `` ` ´ “ ” ‘ ’ 「 」 『 』 `` 替换为空格防跨词假拼接）；真缺 = raw 与归一化双缺；仅归一化命中 → 警告。包裹字符集 `_WRAP_CHARS` :28 |
| R10（第 6/7 类） | `r10_context(text, start, end) -> dict` :78-111，kind ∈ {double_neg, negation, quote_mention, assertion}；`r10_scan(text, assert_tokens) -> (problems, warnings, hits)` :113-130 | 回看窗 = min(24 字符, 当前子句)（`NEG_WINDOW=24` :70、句界 `。！？；\n` :71）；否定词表 `NEG_RE` :69（不/无/未/非/禁/勿/否决/排除/不宣告/不得）；「…」≤80 字符短引证跨度 `SPAN_RE` :72 + 自指标记 `SELF_MARKERS` 十词 :73 判 quote_mention；**双重否定构式在 R10 不豁免**（kind=double_neg 交 R12 裁决） |
| R12（第 6/7 类反例防线） | `r12_scan(text, assert_tokens) -> (problems, hits)` :134-148 | 回看窗含相邻双重否定构式（`DOUBLE_NEG_RE` :76 十式：不得不/并非不/并不是不/不是不/无不/没有不/不无/不能不/不可不/未曾不）的越权词命中重新判违规；显式弃用否定词奇偶计数（两个独立否定短语、三否定词两反例 :74-75 注明） |
| R11（第 8 类） | `r11_scan(text, doc_dir, root=None, recompute=None) -> (problems, warnings, bindings)` :157-222 | 绑定行正则 `BIND_RE` :152 = `被核对象[^。\n]{0,160}?SHA256\s*=\s*` + 可选反引号包裹的 64 位 hex（≤160 字符路径隔断容忍，不跨句不跨行）；≥1 条否则 fail :219-221。路径采集：①「被核对象↔SHA256」分隔段内最后一个反引号路径 :185-187；②否则**同行命中点之前**最后一个反引号路径 :189-191。解析顺序 doc_dir → root → 原样 :196-200；不在盘 → problem（R3-3c）:203；在盘则现盘重算 sha256+字节数（`BIND_BYTES_RE` :153、剥千分位）比对，失配 → problem（R3-3a）:206-215；无显式路径 → warning（R3-3b）:217 |

实现与文档一致性：【转述】实装回件 §2 与复核回件②均核对过 `_g7_patch.md` §2-§4 内嵌常量与模块逐字同源（NEG_RE 词表、NEG_WINDOW=24、CLAUSE_BREAK、SPAN_RE≤80、SELF_MARKERS 十词、DOUBLE_NEG_RE 十构式、BIND_RE 全一致），无判值级 bug。本轮全文实读亦未发现使判值出错的 bug。

### 2.3 复读发现的不符与瑕疵（如实登记，均未修改原文件）

| 编号 | 内容 | 本轮核验方式 |
|---|---|---|
| F-A 死代码 | `_WRAP_SPAN = re.compile(r"([^`\n]{1,200})")`（:29）全模块零引用 | 【亲跑】对封版全文做引用检索，`_WRAP_SPAN` 仅出现 1 次（即 ：29 定义行本身） |
| F-B 死计算 | `r10_context` 非引证跨度分支算出的 `marked`（:100-101）从不参与 kind 判定（`in_span` 为假时 quote_mention 分支不可达） | 【亲跑】读码证实；无害 |
| F-C 静默丢弃风险 | `r10_scan` 对 kind=double_neg 命中既不报 problem 也不报 warning（:123-129 只处理 assertion/negation/quote_mention 三分支）——设计上交 R12 裁决，**若调用方漏接 R12，双重否定命中被静默放走** | 【亲跑】读码证实；实装模块按固定顺序 R10→R12 接续规避（§3.3） |
| F-D CWD 依赖 | `r11_scan` 路径候选链第三档「原样」`cand.append(p)`（:200）对相对路径按当前工作目录解析，CWD 不同命中不同；候选顺序 doc_dir→root 缓解但未消除 | 【亲跑】读码证实 |
| 文档漂移 | 实装报告 §3 引用的 `_g9_gate.py` 行号与封版文件存在系统偏移（如指纹门写 ：33-49 实为 ：40-52、入口写 ：63 实为 ：70、计数行写 ：95/116/135/152 实为 ：112/129/143/159） | 【亲跑】本报告所有行号均按封版 a83081ee 版实读重标；复核回件引用的 ：40-52 与实读一致 |
| 上游在案残余（沿 g7 登记，照录） | 第 5 类原始误报件未定位；DOUBLE_NEG_RE 非穷尽（分离型「亦非不宣告」漏检）；quote_mention ≤80 字符无自指标记降警告；NEG_RE 24 字符窗内邻近否定词误豁免；R9 未包裹裸拆断不覆盖；R11 >160 字符或跨句分隔未验 | 【转述】GATE_FALSE_POSITIVE_5_6_7.md §6 |

## 3 实装模块结构（`_g9_gate.py`，a83081ee…/11623B）

### 3.1 谓词复用与加载指纹门

- `_load_g7_predicates()`（:40-52）：read_bytes → hashlib 实算 → 与派发值 `02c17e49…51120`/11743B 比对，失配抛 RuntimeError 拒绝运行（:44-48）；通过后 importlib 从只读路径加载。四谓词全部经 `g7.r9_check / g7.r10_scan / g7.r12_scan / g7.r11_scan` 调用，**未重写任何谓词**。
- 【亲跑】失配负例实测：把模块常量 `G7_SHA256_EXPECTED` 改为全 0 后调 `_load_g7_predicates()`（内存内覆写，不动盘）→ RuntimeError 如设计抛出（「谓词模块指纹失配：…」）。加载门真实有效，非纸面声明。

### 3.2 统一入口与 JSON 输出契约

`check_deliverable(path, required_elements, forbidden_words, root=REPO_ROOT, doc_dir=None, old_gate_contrast=True)`（:70-203）→ JSON 可序列化 dict，字段（实读）：

- `file / bytes / sha256 / utf8_strict`（非严格 UTF-8 时 errors=replace 并置 utf8_strict=false，:85-90）；
- `checklist{required_elements, forbidden_words}`（原样回显）；
- `predicates{R9, R10, R12, R11}`，各含 `rule_id/name/items/problems/warnings/verdict`，R9 另含 `present/raw_hits/normalized_only_hits`，R10 另含 `occurrences/kinds{assertion,negation,quote_mention,double_neg}/exempted`，R12 另含 `double_neg_hits`，R11 另含 `bindings/reverified/match_true/binding_details`（逐条 declared/path/match/recomputed/bytes）；
- `problems / warnings` 合并视图，每条带 `rule_id`（R7 输出契约，:170-177）；CONFIG 类警告登记词表剥包裹符事件（:96-99）；
- `verdict`：PASS 仅当四谓词全 PASS（:178-179）；谓词级取值 PASS / FAIL / **FAIL_EMPTY**（items=0 时，见 §3.3）；
- `old_gate`：同清单下 `g7.naive_gate` + 越权词朴素字面计数对照（:190-202），明确标注不参与判定。

### 3.3 检查计数机制（第 3 类「空跑通过」防线）

【亲跑】读码行号（封版）：R9 `items = len(必需要素)`（:112）、R10 `items = len(禁用词)`（:129）、R12 `items = len(禁用词)`（:143）、R11 `items = 1 + len(绑定行)`（:159，「≥1 条绑定行」存在性强制项，恒 ≥1）。任一谓词 items == 0 ⇒ 该谓词判 `FAIL_EMPTY`（计 FAIL，:113/130/144）并落「空跑：清单为空，0 项检查（0 项不得 PASS）」problem（:121-122/138-139/151-152）。R11 无 FAIL_EMPTY 分支——存在性检查本身即一项，不可能空跑。

【亲跑】自检三件套（`python -I -X utf8 lead/gate_r9r12_20261109/_g9_gate.py`，本轮复跑）：U1 空清单 → 总判定 FAIL、空跑 problems=3（精确针对三个 0 项谓词）；U2 词表带包裹符（「被核对象」整体入表）→ naive 报缺要素=true 而 R9 判在场=true；U3 谓词指纹 ok=true。all_pass=true。**如实登记**：U3 为代码自述复述（`_g9_gate.py:226-228` 注释自认「加载时已验，此处复述结论」）；真实指纹门在加载路径 ：40-52，其有效性由本轮失配负例实测单独证实（§3.1）。

### 3.4 词表卫生与执行顺序

- `sanitize_tokens()`（:59-67）：词表 token 先剥离包裹字符（第 5 类防线，patch §1 注②），发生剥离记 CONFIG warning 不静默。
- 执行顺序 R9→R10→R12→R11（:104-167 顺序固定）：R12 消费 R10 的语境分类，规避 §2.3 F-C（双重否定命中不会因调用方漏接而放走）。

## 4 全历史回归表

**运行器**：`_g9_regression.py`（7074d7aa…/6652B；清单硬编码 :26-57）。**本轮未重跑回归器**（避免覆写实装轮交付件 `_g9_regression_out.json`）；回归面的核实方式 = 【机读】全量直读 + 【亲跑】三重独立验证：① 30 件新旧 problems 归一化 subset 比对全量重算；② 30 件绑定行计数重数；③ 抽 4 件（b_unclosed_trace、TV3、TV7、C97）只读直调 `check_deliverable` 复算——全部与机读件一致。

**语料**：30 件 = 派发清点原序前 30。本轮将 `_g9_regression.py:26-57` 的 30 项清单与派发载荷【清点】docs 数组前 30 项逐项比对，一一对符；「原序」本身不可盘上复算（任务书未持久化；今日同口径枚举 345 件，见 §6 未验项 1）。
**统一清单**（【机读】payload.checklist）：必需要素 = ["被核对象","SHA256","字节数"]（绑定行三要素）；禁用词 = ["已生效","可应用母本","放行 N-5","已入账","已追加"]（BAD_BAN 探针族，GATE_FALSE_POSITIVE_5_6_7.md:40）。

**真伪判定口径（表列取值）**：
- 【A 口径】= 统一绑定清单施加于该件型不适用或存疑产生的 problems：**旧门禁同报**（新旧 problems 归一化比对，新 ⊆ 旧），非新模块新增；是否真违规取决于原 ask 是否要求该件带行式绑定——**未验**，故这些 problems 是否构成真问题未终判，暂不判真违规亦不判纯误报；无任何一件存在可现盘证实的绑定失配/不在盘。
- 【B 新误报】= 新模块引入、经实锤判误报的 problem。
- 【C】= PASS（problems 空；R11「缺显式路径」仅警告不计）。

### 4.1 主表：30 件（P=PASS，F(n)=FAIL 带 n 条 problems）

| # | 件名 | 字节 | R9 | R10 | R11 | R12 | 新门禁 problems 内容 | 旧门禁 | 真伪判定 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | lead/GOAL3T_CRITERIA_STATUS_20261021.md | 8239 | F(3) | P | F(1) | P | 缺要素 被核对象+SHA256+字节数；缺绑定行 | 4 条 | A 口径-台账/状态件 |
| 2 | lead/GOAL3T_e4_VERIFY_20261026.md | 12959 | F(3) | P | F(1) | P | 同上 4 条 | 4 条 | A 口径存疑-件名 VERIFY 无绑定标记 |
| 3 | lead/PENDING_DECISIONS.md | 52419 | F(2) | P | F(1) | P | 缺要素 被核对象+字节数；缺绑定行 | 3 条 | A 口径-台账本体非回件 |
| 4 | lead/a_dim_reduced_20261108/A_REDUCED_FORM.md | 24000 | P | P | P | P | — | 0 条 | C PASS（1 绑定无路径→警告） |
| 5 | lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md | 28384 | F(2) | P | F(1) | P | 缺要素 被核对象+字节数；缺绑定行 | 3 条 | A 口径（不适用/存疑双标）r1 件 |
| 6 | lead/a_residual_20261106/TASK.md | 5055 | P | P | F(1) | P | 缺绑定行 | 1 条 | A 口径-L97 为引用纪律文字 |
| 7 | lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md | 33431 | P | P | P | P | — | 0 条 | C PASS（r1 版本锚 3343cfbe 无路径→警告） |
| 8 | lead/b2b_candidate_20261106/TASK.md | 8905 | F(1) | P | F(1) | P | 缺要素 被核对象；缺绑定行 | 2 条 | A 口径-任务书 |
| 9 | lead/b2b_candidate_20261106/TESTS_REPORT.md | 27427 | F(1) | P | F(1) | P | 同上 2 条 | 2 条 | A 口径存疑-SHA256×6 为引证 |
| 10 | lead/b2b_candidate_lf_20261107/N1_CLOSURE.md | 16519 | F(1) | P | F(1) | P | 同上 2 条 | 2 条 | A 口径存疑-结题件无绑定行 |
| 11 | lead/b2b_candidate_review2_20261106/CANDIDATE_SEMANTIC_REVIEW_R2.md | 27593 | F(1) | P | F(1) | P | 同上 2 条 | 2 条 | A 口径存疑-评审件 |
| 12 | lead/b2b_candidate_review2_20261106/TASK.md | 13763 | F(1) | P | F(1) | P | 同上 2 条 | 2 条 | A 口径-任务书 |
| 13 | lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md | 24661 | F(1) | P | F(1) | P | 同上 2 条 | 2 条 | A 口径存疑-评审件 |
| 14 | lead/b2b_candidate_review_20261106/CANDIDATE_SEMANTIC_REVIEW.md | 32013 | F(2) | P | F(1) | P | 缺要素 被核对象+SHA256；缺绑定行 | 3 条 | A 口径存疑-评审件 |
| 15 | lead/b2b_candidate_review_20261106/TASK.md | 13763 | F(1) | P | F(1) | P | 缺要素 被核对象；缺绑定行 | 2 条 | A 口径-任务书 |
| 16 | lead/b2b_design_20261106/B2B_DESIGN.md | 66735 | F(1) | P | F(1) | P | 同上 2 条 | 2 条 | A 口径-设计稿 |
| 17 | lead/b2b_design_20261106/TASK.md | 9483 | F(1) | P | F(1) | P | 同上 2 条 | 2 条 | A 口径-任务书 |
| 18 | lead/b2b_design_20261106/_draft_semantics.md | 52841 | F(1) | P | F(1) | P | 同上 2 条 | 2 条 | A 口径-中间稿 |
| 19 | lead/b2b_design_20261106/_hunks_frag.md | 18423 | F(3) | P | F(1) | P | 缺要素×3；缺绑定行 | 4 条 | A 口径-diff 片段稿 |
| 20 | lead/b2b_isolated_20261107/INTEGRATION_REPORT.md | 24022 | P | P | P | P | — | 0 条 | C PASS（2 绑定 ca23c116 无路径→警告） |
| 21 | lead/b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md | 15179 | P | P | P | P | — | 1 条 | C PASS；**旧 1→新 0（第 8 类消除实证）** |
| 22 | lead/b2b_n1_binding_20261107/N1_BINDING.md | 8493 | F(2) | P | F(1) | P | 缺要素 被核对象+字节数；缺绑定行 | 3 条 | A 口径存疑-表格式指纹声明（第 11 类语料实例） |
| 23 | lead/b2b_preaudit_20261106/B2B_PREAUDIT.md | 20615 | F(1) | P | F(1) | P | 缺要素 被核对象；缺绑定行 | 2 条 | A 口径-预审稿 |
| 24 | lead/b2b_preaudit_20261106/TASK.md | 8974 | F(1) | P | F(1) | P | 同上 2 条 | 2 条 | A 口径-任务书 |
| 25 | lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md | 7344 | F(1) | P | F(1) | P | 同上 2 条 | 2 条 | A 口径存疑-L43 表格声明无行式绑定 |
| 26 | lead/b2_preaudit_20261106/B2_PREAUDIT.md | 28410 | P | P | F(1) | P | 缺绑定行 | 1 条 | A 口径-L139 引用纪律文字 |
| 27 | lead/b2_preaudit_20261106/TASK.md | 6846 | P | P | F(1) | P | 缺绑定行 | 1 条 | A 口径-L89 引用纪律文字 |
| 28 | lead/bexec_n4_20261108/B_EXECUTION_SPEC.md | 32183 | P | P | P | P | — | 0 条 | C PASS（6 绑定无路径→警告，见 F2） |
| 29 | lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md | 22136 | P | P | P | P | — | 0 条 | C PASS（2 绑定无路径→警告） |
| 30 | lead/b_unclosed_trace_20261108/B_BREAKPOINT2_TRACE.md | 19047 | P | P | F(1) | P | 引用锚指向不在盘对象 _dB_anchor_recompute_out.txt:18-19（R11/R3-3c） | 0 条 | **B 新误报 ×1（三重实锤，见 §4.4）** |

**主表统计**（【亲跑】机读件重算）：

- problems 全空 **6/30**（#4、7、20、21、28、29）；仍有 problems **24/30**。
- FAIL 计数：R9=20 件、R10=0 件、R11=24 件、R12=0 件；R10/R12 的 BAD_BAN **occurrences=0×30**、double_neg_hits=0×30（items 各=5，非空跑）。
- **新旧 problems 归一化比对（本轮全量重算）**：唯一例外 = #30 的 1 条（引用锚不在盘，旧门禁无对应项）——即「新 ⊆ 旧 + 恰 1 例新误报」，与实装/复核两轮声明一致，零其他例外。
- **A 口径细分（逐行标注为准）**：口径不适用 14 件 + 不适用/存疑双标 1 件（#5）+ 口径存疑 8 件（#2/9/10/11/13/14/22/25）。**登记一处出入**：实装回件统计行写「不适用 16 件、存疑 7 件」，但其存疑名单本身列了 8 个件名、逐行表亦标 8 件——总数 23 件无误，拆分数字以逐行表为准（撰写轮复核时发现，不影响方向）。
- 30 件绑定行共 **19 条**：path=null **18 条**（仅 R3-3b 警告）、采到路径 **1 条**（即 #30 的伪造路径，match=False）；**现盘哈希重算在 30 件面上触发 0 次、成功 match 0 次**。

### 4.2 附录 A：TV 违规样本 8 件（清单 req=[APPROVE_SCOPE] + BAD_BAN；【机读】+ TV3/TV7 两件【亲跑】复算一致）

| 件 | 字节 | 总判定 | R9 | R10 | R11 | R12 | 新 P | 旧 P | 真伪判定 |
|---|---|---|---|---|---|---|---|---|---|
| _g7_tv1_missing_element.md | 717 | FAIL | F(1) | P | F(1) | P | 2 | 2 | 真违规样本·正确拦截（缺要素） |
| _g7_tv2_overreach_positive.md | 476 | FAIL | F(1) | F(5) | F(1) | P | 7 | 7 | 真违规·正确拦截（正面越权 ×5 全拦，未放松） |
| _g7_tv3_double_negation.md | 748 | FAIL | F(1) | P | F(1) | F(2) | 4 | 3 | 真违规·正确拦截且更准：越权面 3 处命中中 R12 恰拦 2 处双重否定（=肯定），单重否定对照 1 处正确不拦；旧门禁把整词一刀切报 1 |
| _g7_tv4_no_binding.md | 542 | FAIL | F(1) | P | F(1) | P | 2 | 2 | 真违规样本·正确拦截（缺绑定行） |
| _g7_tv5_forged_binding.md | 543 | FAIL | F(1) | P | F(1) | P | 2 | 2 | 真违规·正确拦截：引用锚失配（现盘 1e9e102ea94a/3055 ≠ 声明） |
| _g7_tv6_binding_missing_obj.md | 387 | FAIL | F(1) | P | F(1) | P | 2 | 2 | 真违规·正确拦截：引用锚不在盘 _g7_nonexistent_object.md |
| _g7_tv7_split_token.md | 494 | FAIL | P | P | F(1) | P | 1 | 2 | 旧门禁误报消除（第 5 类：拆断要素 R9 判在场）；余 1 条缺绑定行=样本本就无绑定，口径正确 |
| _g7_tv7b_wrapper_only.md | 552 | FAIL | P | P | F(1) | P | 1 | 1 | 同上（第 5 类消除） |

**不放松实证**：TV1-TV6 全 FAIL（缺要素/R10×5/R12×2/缺绑定/失配/不在盘六种真违规形态零放走）；TV7/TV7b 消除的恰是登记的第 5 类误报形态，且 R11 缺绑定行问题在两件上如实保留。

### 4.3 附录 B：g7 四真实件 + CANDIDATE 附加口径（清单=绑定三要素 + BAD_BAN；【机读】+ C97【亲跑】复算一致，含现盘重算 match=True ×2）

| 件 | 字节 | 判定 | R10 命中(豁免) | R12 拦 | R11 绑定回验 | 旧 P | 真伪判定 |
|---|---|---|---|---|---|---|---|
| lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md | 23129 | PASS | 6(6)=5 negation+1 quote_mention | 0 | ee27b4ca… match=True | 4 | 旧 4 条朴素越权全为否定/引证语境（第 6/7 类误报消除）；绑定真锚 |
| lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md | 45719 | PASS | 3(3) 全 negation | 0 | 6888379a… match=True | 2 | 同上（第 6/7/8 类消除） |
| lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md | 54351 | PASS | 0(0) | 0 | 3d463483… 无路径→警告 | 0 | PASS |
| lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md | 21690 | PASS | 0(0) | 0 | 91d1317f…/4481B match=True；1fe6b1b6…/4034B match=True | 0 | PASS；两锚现盘重算全符（【亲跑】复算哈希 91d1317f28b12285…、1fe6b1b6160e2187… 一致） |
| CANDIDATE（附加旧门禁词表口径 APPROVE_SCOPE） | 23129 | PASS | 6(6) | 0 | match=True | 4 | 同 CANDIDATE 行 |

### 4.4 唯一新误报三重实锤（#30 b_unclosed_trace/B_BREAKPOINT2_TRACE.md，R11）

新门禁报 `引用锚指向不在盘对象 _dB_anchor_recompute_out.txt:18-19（R11/R3-3c）`；旧门禁 0 条（紧邻正则连绑定行都没认出）。判**误报**，本轮全部第一手核实：

1. **引证语境误当本件绑定行**：命中在 L60，系转述第三方件的证据引文（「`_dB_anchor_recompute_out.txt:18-19`（本轮实读：「被核对象 SHA256 = 4a342405…」」）——R11 无引证豁免（R10 有 quote_mention 思想而 R11 没有）。【亲跑】实读 L55-L62 证实。
2. **路径带 `:18-19` 行号后缀未剥离**：同行回看采到 `_dB_anchor_recompute_out.txt:18-19` 为「路径」，按文件名检索必败。而对象实际在盘 = `lead/dtrigger_round2_20261107/_dB_anchor_recompute_out.txt`。【亲跑】`Path.is_file()` = True。
3. **锚本体为真**：引文声明 4a342405…/48343 与 `lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md` 现盘实算相符。【亲跑】hashlib 实算 = 4a3424050125b98c…（前缀）×48343B，MATCH。
4. **本件自身四条真绑定行（L5-L8）全部为真**：【亲跑】逐一现盘实算全 MATCH——B_BREAKPOINTS_2_6.md/19527、R2_FINAL_GRADE.md/30140、_verify_B_out.txt/7229、_bt_B崩点2_尾串追溯_20261108.md/12706。本件不该 FAIL。
5. **谓词级复现**：【亲跑】只读直调 `check_deliverable` 得同一 problem；6 条绑定中 5 条 path=null（含 L5-L8 四条真绑定行——尾括注路径未采集，见 F2）、唯一采到路径的恰是 L60 那条伪造「路径」。

**根因与修法建议（未实施，谓词原件只读）**：①R11 增加引文内绑定行降警告；②路径剥 `:行号(范围)` 后缀再解析；③（与 F2 合并）采集 hex 之后尾括注内反引号路径。

### 4.5 F2 回验覆盖缺口（重要发现，非误报；含一处计数勘误）

`r11_scan` 只在「被核对象↔SHA256 分隔段」与「同行命中点之前」两处找路径（`_g7_predicates.py:185-191`），而本语料主流绑定形态「被核对象 SHA256 = hex，字节数 = n（`path`）」的路径在 **hex 之后的尾括注**。后果：**不产生错误 FAIL**（仅 R3-3b 警告），但 R3-3a/c「堵假阴性」在主流形态上未生效——若某件尾括注路径的哈希是伪造的，本模块会放走。真实件附录的分隔段形态回验正常（CANDIDATE/LEDGER/C97 合计 4 条 path 全 match）。

**计数勘误（复核员纠错成立，【亲跑】重数证实）**：实装回件文字（§0.6/§5.3）写「18 条绑定行中 17 条 path=null、回验 0 次触发」；机读件与本轮重数 = **19 条绑定行 / 18 条 path=null / 采到路径 1 条（伪造，match=False）**。差额在 b_unclosed_trace：实装按 5 条计，实为 **6 条**（5 条 path=null + 1 条伪造路径）。即：30 件面上路径解析分支实际触发 1 次（失败于不在盘）、现盘哈希重算触发 0 次——「0 次成功回验」的结论不变，但「0 次触发」的表述低估了 F2 缺口，如实登记。

## 5 残余误报统计

### 5.1 11 类逐类观察

11 类登记原文追到派发载荷（【转述】实装回件 §6；第 1-4 类定义另见 lead/gate_template_20261108/GATE_FALSE_POSITIVES.md §2-§5）。逐类：

| 类 | 登记定义 | 本回归观察（证据） | 结论 |
|---|---|---|---|
| 1 | 禁用词子串扫到 BANNED_PAT 常量/mock 路径 | 本模块只扫交付件文本、词表=BAD_BAN 行为词族，30+8+5 件 0 命中；未扫 .py。但同族机制在报告层显形：见第 4 类行 | 未观察到（不在检查面内）；同族活体见第 4 类 |
| 2 | 措辞不匹配（最小字段 vs 最少字段） | 23 件「缺要素」全为统一清单口径问题，无一例同义词形态；清单无同义词需求 | 未观察到（R9 不做同义词扩展；未覆盖） |
| 3 | 版本锚缺失：门禁空跑通过 | U1 空清单→FAIL（【亲跑】）；30 件无一件 items=0 判 PASS（【亲跑】重算） | **已消**（检查计数机制，回归+自检双实证） |
| 4 | 自指禁令：报告主题本身是被禁词 | 30 件 0 命中；但复核员全量扫描中 `_g9_regression.md`（实装登记报告自身）被 R10 报 assertion×12——讨论误报的报告被自家门禁越扫越红，第 1/4 类家族活体标本（【转述】复核回件 + 【亲跑】读取 _g9v_corpus_out.json rest_true_viol） | 30 件面未观察到；报告层活体在案（12 条） |
| 5 | 带反引号标识符判缺要素 | TV7/TV7b 判在场、U2 词表剥符防线（均【亲跑】）；30 件 R9 新增误报 0 | **已消**（回归实证） |
| 6 | 否定式自指当越权断言 | CANDIDATE 6 处全豁免（5 negation+1 quote_mention）problems=0；TV2 正面 ×5 全拦；TV3 双重否定 R12 恰拦 2 | **已消**（回归实证） |
| 7 | 否定句含完成时词当越权断言 | LEDGER 3 处「不宣告…已生效」全豁免 problems=0 | **已消**（回归实证） |
| 8 | 绑定行路径隔断判缺绑定 | _integ/CANDIDATE/LEDGER 旧报缺绑定→新 PASS；家族内残余 = 1 例新误报（§4.4）+ F2 覆盖缺口（§4.5） | **主体已消；家族内 1 新误报 + 1 覆盖缺口如实登记** |
| 9 | 带分隔符编号（D-01 vs \bD(\d+)\b） | 清单与四谓词均无编号匹配项 | 无观察（未实装） |
| 10 | 加粗包裹的绑定行（**SHA256 = hex**） | 【转述】实装合成探针：`被核对象**SHA256 = hex**`、`**被核对象** SHA256 = hex` 两登记形态 BIND_RE 匹配✓；变体 `SHA256 = **hex**`（仅 hex 加粗）不匹配。30 件未遇实件 | 登记形态已被 R11 机制附带容忍（合成实测）；`= **hex**` 变体为合成残余 |
| 11 | 同义措辞（【原】/【改】 vs 改前改后） | 无对应检查项；N1_BINDING 表格式指纹声明（第 22 件）即「结构在场、字面不在场」语料实例，R11 判缺绑定（口径存疑，非误报实锤） | 未观察到误报 / 未实装 |

### 5.2 新模块是否引入新误报——如实分层回答

1. **30 件回归面内：1 例**（§4.4，R11 引证语境 + 行号后缀）。全量「新 ⊆ 旧」程序化比对零其他例外（【亲跑】）。
2. **30 件面外：同族误报复现**（【亲跑】读取复核员 `_g9v_corpus_out.json`，未独立重跑）：全语料枚举 343 件，除前 30 外 313 件中 R11「不在盘」类其他命中 8 条，其中行号后缀家族 ≥3 例（b_unclosed_trace `:18-19`、_da_ANCHOR_AUDIT `:130` 与 `DECISION_QUESTIONS.md:130`）——**「1 例新误报」的结论仅在 30 件面成立，外推有限**。R10 assertion 命中 7 件（含 GATE_FALSE_POSITIVE_5_6_7.md ×14、_g9_regression.md ×12、postmortem ×4 等门禁自指讨论件），复核员判其中 4 件为词表自指件；该面逐条真伪未独立裁决（本报告不替复核员下结论）。
3. **R10 对本登记报告的自指误报 12 条**：【转述】实装回件 §5.4（初扫 2 条→终版 12 条）+ 复核回件（终版 12 条独立复算精确相符；「初扫 2 条」中间态不可复现）。机制 = R10 引证豁免只认「…」短跨度，反引号代码跨度内的词表声明被当断言；同跨度前三词仅因 24 字符窗内「禁」字侥幸豁免（NEG_RE 邻近误豁免残余的反向实例）。属第 1/4 类家族活体，不在 30 件回归面内。
4. **挑选偏差核查**（复核员⑥）：前 30 干净率 20%（6/30）vs 其余 22.7%（71/313）——无绿灯偏斜迹象；唯一新误报件在前 30 内。30 件清单与派发清点前 30 项逐项一致（本轮比对，§4）。
5. **未为绿灯放宽任何谓词**：TV1-TV6 全 FAIL（§4.2）；谓词零改写（模块 import 封版原件，加载指纹门实测有效 §3.1）；TV3 上新门禁比旧门禁多拦 1 处（真违规面）。

### 5.3 结论：11 类降到 6 类残余

已消 5 类：第 3 类（检查计数）、第 5 类（R9）、第 6/7 类（R10+R12）、第 8 类主体（R11）。**残余 6 类 = 第 1/2/4/9/10/11 类**；其中第 1/2/4 类在本回归检查面内无对应检查项故无观察（第 4 类另有报告层活体）、第 9/11 类未实装、第 10 类登记形态经合成探针已被 R11 附带容忍但无实件验证。第 8 类家族内残留 1 例新误报与 F2 覆盖缺口（均已定位并给修法，未实施）。severity=medium：核心目标达成且违禁样本零放松，但回归实打实暴露 1 例新误报与 1 个回验覆盖缺口，均已如实登记、未粉饰。

### 5.4 剩余类处理建议（全部未实施，均不改谓词原件）

| 类/项 | 建议 |
|---|---|
| 1 禁用词子串 | AST 真实调用边判罪（裸 import 除罪为警告）、派生副本对母本做差；文本层无解，勿再用全文子串（模板 R4 已给设计，GATE_TEMPLATE_FIXED.py.txt r2） |
| 2 措辞不匹配 | 同义词组 + 任务书原文优先 + 语料频次留档（半自动，需 ask 层配合） |
| 4 自指禁令 | 作用域限定谓词（只查特定区段/表格列）+ ask 层同步（掩码形式或禁「行为」不禁「字样」） |
| 9 编号形态 | 编号归一化谓词（D-01/D01/D_01/D.01 统一 token 再数；纯文本、成本低） |
| 10 加粗绑定行 | 不需要新谓词（登记形态已被 R11 容忍）；把登记形态与 `= **hex**` 变体各固化一例进 R11 回归样件防回退 |
| 11 同义措辞 | 结构存在性谓词（成对改前/改后块、两列表格）+ 人工复核兜底 |
| R11 三条增补 | ①尾括注路径采集（修 F2）；②路径剥 `:行号(范围)` 后缀；③引文内绑定行降警告（修 §4.4 新误报） |
| R10 一条增补 | ④反引号代码跨度视为数据语境豁免越权词扫描（修 §5.2 第 3 点的 12 条自指误报）；并把 24 字符窗邻近否定词误豁免改为子句内同短语判定 |

## 6 复核回件、声明与未验项

### 6.1 复核回件（如实转记）

- **verdict = confirmed**（七步复核全过，未发现粉饰、选择性报告或越界；实现为真、谓词零改写、未放松）。按回件规则：非 refuted/partial，不标 unconfirmed。
- 复核绑定行（被核对象 = 门禁模块 `_g9_gate.py`；【亲跑】本轮实算 11623B / a83081ee… 与之一致）：

被核对象 SHA256 = a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6，字节数 = 11623

- 辅助绑定（实装回件申报，【亲跑】一致）：

被核对象 SHA256 = 7074d7aa28498a5e51f8d038531f11543528fa28bbf8434907569502526b401a，字节数 = 6652

被核对象 SHA256 = 7f16da217dba02008546d643bb51c0100d7126939df947ad0c46a4fd478f11d8，字节数 = 123691

- 复核七步要点（【转述】复核回件）：①基线 6/6 与写域 5/5 指纹实算全符；②谓词全文实读零抄错，F-A/F-C/F-D 码中证实；③独立复跑 43 判定（30+TV8+真实件4+附加口径），与机读件逐字段比对 n_diff=0（【亲跑】读取 `_g9v_regress_out.json`：n_mine=43、n_theirs=43、n_diff=0 属实）；④空清单两探针均 FAIL/3 条空跑 problem，U3 属复述性质（与本报告 §3.3 同判）；⑤新⊆旧归一化比对独立成立（仅 b_unclosed_trace +1、仅 _integ −1），D30 BAD_BAN occurrences=0×30 属实（本轮再证）；⑥30 件清单盘上不可验原序（记未验，非证实有偏；本轮已用派发载荷逐项对符补上链条 §4）；⑦无越界：保护件指纹零漂移、保护目录复核窗口零写入、30 件语料 mtime ≤ 11-08 22:27。
- 复核登记瑕疵（均不改判定方向，本报告已逐条吸收）：a) F2 计数文字与机读件不一致（§4.5 勘误，本轮重数证实）；b) 334 vs 343 未验（见下未验项 1）；c) 实装「初扫 2 条」中间态不可复现（终版 12 条复核独立复算相符）；d) U3 自检为复述结论（真实指纹门在加载时 ：40-52，本轮失配负例实测补证 §3.1）。复核员未跑件：`_g9_table_fragment.md` 表片中间件未逐字审（本报告数据源 = 机读件直读 + 本轮亲跑，未依赖表片）。

### 6.2 未改任何文件声明

撰写轮除在唯一写域新增本报告一个文件外，**未写、未改、未追加、未覆盖任何其他文件**——包括 `lead/gate_fp7_20261108/` 全部件（尤其 `_g7_predicates.py`）、`lead/gate_template_20261108/` 全部件、实装轮五件与复核轮十件、全部被扫交付件与两台账。佐证：【亲跑】六件上游指纹开场实算全符（§2.1）；只读域 pycache（`lead/gate_fp7_20261108/__pycache__/_g7_predicates.cpython-312.pyc`）在本轮全部只读直调之后 mtime 仍为 2026-11-09 00:45:10（早于实装轮全部实跑时刻，源未变缓存命中、零写盘）；写域 `__pycache__/_g9_gate.cpython-312.pyc` mtime 仍为 01:52:47（本轮 import 未触发重写）。未 commit、未 push；零真机、零采样代码。本轮全部命令为 `python -I -X utf8` + 绝对路径的只读操作与一次写本报告。

### 6.3 未验项（如实，不下补造结论）

1. **清点总数不可盘上复算**：派发清点 count=334；复核员当日同口径枚举 343；撰写轮复数 345。方向上由并发轮次持续写盘解释（【亲跑】02:52 后 lead/ 深度≤1 至少新增 3 个 .md），精确逐件归因未验；「原序」本身未持久化，仅能对到派发载荷 docs 数组（30 件已逐项对符）。
2. **23 件 A 口径 problems 的真伪终判**：原 ask 是否要求各件自带行式绑定行——未验（ask 文本不在可读范围逐一追溯）；故不判真违规、亦不判纯误报，仅登记「旧门禁同报、非新模块新增」。
3. 第 5 类**原始误报件未定位**（沿 g7 §6.1 未验；机制修复经 TV7/TV7b/U2 实证）。
4. 第 10 类 R11 容忍 = **合成探针实测**，30 件未遇实件；`= **hex**` 变体仍为残余（未验实件是否存在）。
5. R10 对 `_g9_regression.md` 的自指 12 条：复核员独立复算相符，撰写轮未重算；实装「初扫 2 条」中间态不可复现。
6. 复核员全量扫描（343 件）的 r10_assert 7 件、r11other 8 条逐条真伪未独立裁决；撰写轮未重跑该扫描。
7. `_g9_table_fragment.md` 表片中间件未逐字审（复核员与撰写轮均未跑；本报告未以其为数据源）。
8. F2/R11/R10 的全部修法建议（§4.4/§4.5/§5.4）**未实施、未验证**（谓词原件只读铁律）。
9. 第 1/2/4 类「未观察到」仅指本回归检查面内零命中；若引入对应检查项（.py 禁词扫描/同义词表/自指主题词）三类会否复发未验（R9-R12 不覆盖它们）。
