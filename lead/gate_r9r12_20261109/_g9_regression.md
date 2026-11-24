# _g9_regression.md — R9/R10/R11/R12 四谓词实装门禁模块与全历史回归报告

撰写：谓词实装员·GLM（dynamic workflow 子代理）。日期：2026-11-09。
写域：`lead/gate_r9r12_20261109/`（本任务唯一写域）。被核对象 = 门禁模块 `_g9_gate.py`。

> 被核对象 SHA256 = a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6，字节数 = 11623

## 0 结论速览

1. **四谓词已实装为可复用门禁模块** `_g9_gate.py`：直接 import `lead/gate_fp7_20261108/_g7_predicates.py` 原文（加载前 hashlib 指纹验证，失配拒绝运行），未重写任何谓词；统一入口带检查项计数（0 项即 FAIL，第 3 类空跑防线）与 JSON 输出契约。
2. **模块自检 3/3 过**：U1 空清单→FAIL（第 3 类）、U2 词表带包裹符→朴素门禁误报而 R9 判在场（第 5 类）、U3 谓词指纹。
3. **全历史回归（30 件）**：problems 全空 6 件；仍有 problems 24 件，其中 **23 件为旧门禁同报**（统一清单口径不适用于该件型/口径存疑，非新模块新增），**1 件为新误报**（`b_unclosed_trace/B_BREAKPOINT2_TRACE.md`，R11 把引证语境的第三方绑定行当本件绑定行 + 路径带 `:行号` 后缀，三重实锤见 §5.2）。客观真违规 0 件。
4. **误报消除实证**：30 件内 `_integ_INTEGRATION_REPORT.md` 旧 1→新 0（第 8 类）；真实件附录 CANDIDATE 4→0、LEDGER 2→0（第 6/7/8 类）；TV 附件 TV7 拆断件 2→1（第 5 类）；TV1–TV6 违规样本全数保持 FAIL（未放松）。
5. **诚实结论：11 类误报降到 6 类残余**。已消 5 类：第 3 类（计数机制）、第 5/6/7/8 类（R9/R10+R12/R11，回归实证）。残余 6 类：第 1/2/4/9/10/11 类——其中第 10 类经合成探针实测已被 R11 机制附带容忍（`**SHA256 = hex**` 形态匹配），第 1/2/4 类在本回归检查面内无对应检查项故无观察，第 9/11 类未实装。
6. **重要发现（新模块未修、如实上报）**：R11 的路径采集只看「被核对象↔SHA256 分隔段」与「同行、命中点之前」两个位置（`_g7_predicates.py:185-191`）；本语料主流绑定形态「被核对象 SHA256 = hex，字节数 = n（`path`）」的路径在 hex **之后**的尾括注 → 18 条绑定行中 17 条 path=null，**现盘回验在 30 件语料上 0 次触发**（真实件附录的分隔段形态 4/4 正常触发）。不产生错误 FAIL（仅警告），但 R3-3「堵假阴性」在主流形态上未生效——见 §5.3 F2。

## 1 边界与纪律（实跑口径）

- 零真机：未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存。零采样代码：全部产物为静态文本/哈希检查，仅 import hashlib/importlib.util/json/re/sys/pathlib。
- 绝对只读：`lead/gate_fp7_20261108/`（含 `_g7_predicates.py`，本模块每轮加载前验指纹 `02c17e49…51120`/11743B）、`lead/gate_template_20261108/`、全部被扫交付件零改动。importlib 缓存核查：只读域 `__pycache__/_g7_predicates.cpython-312.pyc` mtime=2026-11-09 00:45:10（上一轮 g7 验证所留，早于本任务全部实跑时刻 01:52+；源未变缓存命中，本轮未写盘）。
- 命令口径：全部 Python 以 `python -I -X utf8` + 绝对路径运行；指纹 hashlib 实算。未 commit、未 push。
- 本任务全部实跑命令清单：①指纹核验 6 件（开场）②30 件侦察扫描 ③`_g9_gate.py` 自检 ④`_g9_regression.py`（30 件+TV8+真实件5 趟，输出 `_g9_regression_out.json`）⑤b_unclosed_trace 锚验（4 绑定 MATCH + out.txt 在盘定位 + CRITERIA_COMPARE 实算）⑥pycache 核查 ⑦新旧 problems 归一化比对 + 第 10 类合成探针 ⑧表片生成。

## 2 第一步：谓词复读记录（`_g7_predicates.py` 全文实读）

| 谓词 | 函数签名 | 输入 | 输出 | 判据 |
|---|---|---|---|---|
| R9（第 5 类） | `r9_normalize(text)`；`r9_element_present(text, token) -> (present, layer)`；`r9_check(text, tokens) -> (problems, warnings)` | 全文 + 必现要素 token 列表 | 缺要素 problems / 仅归一化命中 warnings | 两遍归一化（N2 先拼反引号跨度内换行拆断，N1 再把包裹字符 `` ` ´ “ ” ‘ ’ 「 」 『  ``』`` 替换为空格成词边界）；真缺 = raw 与归一化双缺（:31-65） |
| R10（第 6/7 类） | `r10_context(text, start, end) -> dict(kind∈{double_neg,negation,quote_mention,assertion},…)`；`r10_scan(text, assert_tokens) -> (problems, warnings, hits)` | 全文 + 越权词表 | 断言 problems / 否定与引证豁免 warnings / 逐处 hits | 回看窗 = min(24 字符, 当前子句)（句界 `。！？；\n` 截断）；「…」≤80 字符短引证跨度 + 自指标记（SELF_MARKERS）判 quote_mention；双重否定不在此豁免（:78-130） |
| R12（第 6/7 类反例防线） | `r12_scan(text, assert_tokens) -> (problems, hits)` | 全文 + 同一越权词表 | 双重否定命中的越权词重新判违规 | 相邻构式表 `不得不\|并非不\|并不是不\|不是不\|无不\|没有不\|不无\|不能不\|不可不\|未曾不`（弃否定词奇偶计数，:134-148） |
| R11（第 8 类） | `r11_scan(text, doc_dir, root=None, recompute=None) -> (problems, warnings, bindings)` | 全文 + 被扫文档目录 + 仓库根 | 缺绑定/失配/不在盘 problems；缺显式路径 warnings；bindings 明细 | 绑定行正则 `被核对象[^。\n]{0,160}?SHA256\s*=\s*`?hex`?`（≤160 字符路径隔断容忍）；≥1 条否则 fail；带显式路径者现盘重算回验（失配 R3-3a / 不在盘 R3-3c / 无路径 R3-3b 警告）；字节数声明同窗比对（剥千分位）（:152-222） |

**实现与文档一致性**：`_g7_patch.md` §2–§4 内嵌代码与模块逐字同源（NEG_RE 词表、NEG_WINDOW=24、CLAUSE_BREAK、SPAN_RE≤80、SELF_MARKERS 十词、DOUBLE_NEG_RE 十构式、BIND_RE 全部一致）；`GATE_FALSE_POSITIVE_5_6_7.md` §4 的片段亦一致。**未发现使判值出错的功能性 bug。**

**复读发现的实现瑕疵（如实登记，均不改判值方向，未修改原文件）**：

- **F-A 死代码**：`_WRAP_SPAN = re.compile(r"([^`\n]{1,200})")`（`_g7_predicates.py:29`）全模块零引用。
- **F-B 死计算**：`r10_context` 非引证跨度分支算出的 `marked`（`_g7_predicates.py:100-101`）从不参与 kind 判定（`in_span` 为假时 quote_mention 分支不可达），无害。
- **F-C 静默丢弃风险**：`r10_scan` 对 `double_neg` 命中既不报 problem 也不报 warning（`_g7_predicates.py:123-129` 只处理三种 kind）——设计上交 R12 裁决，但**若调用方漏接 R12，双重否定命中会被静默放走**。本模块按 patch §1 固定顺序 R10→R12 接续，规避该风险。
- **F-D CWD 依赖**：`r11_scan` 路径候选链第三档「原样」`cand.append(p)`（`_g7_predicates.py:200`）对相对路径按**当前工作目录**解析，CWD 不同则命中不同；候选顺序 doc_dir→root→CWD 缓解但未消除。
- 上游已登记残余照录（`GATE_FALSE_POSITIVE_5_6_7.md` §6）：第 5 类原始误报件未定位；DOUBLE_NEG_RE 非穷尽（分离型「亦非不宣告」GV-L 实证漏检）；quote_mention ≤80 字符无自指标记降警告；NEG_RE 词表「排除/非」24 字符窗内误豁免；R9 未包裹裸拆断不覆盖（GV-K2）；R11 >160 字符或跨句分隔未验。

## 3 第二步：模块实装（`_g9_gate.py`）

- **复用而非重写**：`_load_g7_predicates()`（`_g9_gate.py:33-49`）以 importlib 从只读路径加载，**加载前 hashlib 比对派发指纹**（`02c17e49…51120`/11743B），失配抛 RuntimeError 拒绝运行；四谓词全部经 `g7.r9_check / g7.r10_scan / g7.r12_scan / g7.r11_scan` 调用，要素层细节经 `g7.r9_element_present`，朴素对照经 `g7.naive_gate` + `g7._WRAP_CHARS`。
- **统一入口**（`_g9_gate.py:63`）：`check_deliverable(path, required_elements, forbidden_words, root=REPO_ROOT, doc_dir=None, old_gate_contrast=True)` → JSON 可序列化 dict：`file/bytes/sha256/utf8_strict/checklist/predicates{R9,R10,R12,R11}/problems/warnings/verdict/old_gate`。problems/warnings 每条带 `rule_id`（R7 输出契约）。
- **检查项计数（第 3 类修法）**（`_g9_gate.py:95,116,135,152`）：R9 items=len(必需要素)；R10 items=len(禁用词)；R12 items=len(禁用词)；R11 items=1+len(绑定行)（存在性强制项恒≥1）。任一 items=0 ⇒ 该谓词判 `FAIL_EMPTY`（计 FAIL）并落「空跑」problem——**0 项检查永远不得 PASS**。
- **词表卫生（第 5 类防线，patch §1 注②）**（`_g9_gate.py:52-60`）：词表 token 先剥包裹字符再交谓词，发生剥离记 `CONFIG` warning，不静默。
- **执行顺序**：R9→R10→R12→R11（patch §1），R12 消费 R10 语境分类，规避 F-C。
- **自检 3/3 实跑输出**（命令 `python -I -X utf8 _g9_gate.py`）：`U1_第3类空跑防线 ok=true（空清单判定=FAIL，空跑 problems=3）`；`U2_第5类包裹符词表 ok=true（naive 报缺要素=True，R9 判在场=True）`；`U3_谓词指纹 ok=true`。

## 4 第三步：全历史回归（30 件）

**语料**：任务书清点 334 件（lead/ depth≤1、3000B<size<200KB 的 .md）**原序前 30 件**（清单逐字取自任务书，硬编码于 `_g9_regression.py:21-53`）。
**统一清单**（两清单一为本会话既有纪律实措）：必需要素 = `["被核对象","SHA256","字节数"]`（本任务书铁律的绑定行三要素）；禁用词 = `["已生效","可应用母本","放行 N-5","已入账","已追加"]`（探针 BAD_BAN 族，`GATE_FALSE_POSITIVE_5_6_7.md:40` 逐字）。
**对照**：同清单同件跑 g7.naive_gate（紧邻绑定正则 + 裸子串要素）+ 越权词朴素字面计数（`old_gate` 字段，不参与判定）。
**逐件结果**（命令 `python -I -X utf8 _g9_regression.py`，全量机读件 `_g9_regression_out.json`）：

| # | 件名 | 字节 | R9 | R10 | R12 | R11 | 新门禁报了什么 | 旧门禁 | 判定 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | lead/GOAL3T_CRITERIA_STATUS_20261021.md | 8239 | **FAIL(3)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺要素 SHA256<br>缺要素 字节数<br>缺 SHA256 绑定行 | 4 条 | 口径不适用：台账/状态件，非复核回件；旧门禁同报 |
| 2 | lead/GOAL3T_e4_VERIFY_20261026.md | 12959 | **FAIL(3)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺要素 SHA256<br>缺要素 字节数<br>缺 SHA256 绑定行 | 4 条 | 口径存疑：件名 VERIFY 但无绑定行标记；旧门禁同报 |
| 3 | lead/PENDING_DECISIONS.md | 52419 | **FAIL(2)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺要素 字节数<br>缺 SHA256 绑定行 | 3 条 | 口径不适用：台账本体非回件；旧门禁同报 |
| 4 | lead/a_dim_reduced_20261108/A_REDUCED_FORM.md | 24000 | pass | pass | pass | pass | — | 0 条 | PASS；绑定行 1 条无显式路径→警告（R3-3b） |
| 5 | lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md | 28384 | **FAIL(2)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺要素 字节数<br>缺 SHA256 绑定行 | 3 条 | 口径不适用/存疑：r1 件；旧门禁同报 |
| 6 | lead/a_residual_20261106/TASK.md | 5055 | pass | pass | pass | **FAIL(1)** | 缺 SHA256 绑定行 | 1 条 | 口径不适用：L97 为引用纪律文字（要求其复核件含绑定），非本件绑定行；旧门禁同报 |
| 7 | lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md | 33431 | pass | pass | pass | pass | — | 0 条 | PASS；绑定声明=3343cfbe(r1 版本锚) 无路径→警告（历史锚，GATE_FALSE_POSITIVES.md §4 在案） |
| 8 | lead/b2b_candidate_20261106/TASK.md | 8905 | **FAIL(1)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺 SHA256 绑定行 | 2 条 | 口径不适用：任务书；旧门禁同报 |
| 9 | lead/b2b_candidate_20261106/TESTS_REPORT.md | 27427 | **FAIL(1)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺 SHA256 绑定行 | 2 条 | 口径存疑：报告件无绑定行（SHA256×6 为引证）；旧门禁同报 |
| 10 | lead/b2b_candidate_lf_20261107/N1_CLOSURE.md | 16519 | **FAIL(1)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺 SHA256 绑定行 | 2 条 | 口径存疑：结题件无绑定行；旧门禁同报 |
| 11 | lead/b2b_candidate_review2_20261106/CANDIDATE_SEMANTIC_REVIEW_R2.md | 27593 | **FAIL(1)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺 SHA256 绑定行 | 2 条 | 口径存疑：评审件无绑定行；旧门禁同报 |
| 12 | lead/b2b_candidate_review2_20261106/TASK.md | 13763 | **FAIL(1)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺 SHA256 绑定行 | 2 条 | 口径不适用：任务书；旧门禁同报 |
| 13 | lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md | 24661 | **FAIL(1)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺 SHA256 绑定行 | 2 条 | 口径存疑：评审件无绑定行；旧门禁同报 |
| 14 | lead/b2b_candidate_review_20261106/CANDIDATE_SEMANTIC_REVIEW.md | 32013 | **FAIL(2)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺要素 SHA256<br>缺 SHA256 绑定行 | 3 条 | 口径存疑：评审件无绑定行；旧门禁同报 |
| 15 | lead/b2b_candidate_review_20261106/TASK.md | 13763 | **FAIL(1)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺 SHA256 绑定行 | 2 条 | 口径不适用：任务书；旧门禁同报 |
| 16 | lead/b2b_design_20261106/B2B_DESIGN.md | 66735 | **FAIL(1)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺 SHA256 绑定行 | 2 条 | 口径不适用：设计稿；旧门禁同报 |
| 17 | lead/b2b_design_20261106/TASK.md | 9483 | **FAIL(1)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺 SHA256 绑定行 | 2 条 | 口径不适用：任务书；旧门禁同报 |
| 18 | lead/b2b_design_20261106/_draft_semantics.md | 52841 | **FAIL(1)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺 SHA256 绑定行 | 2 条 | 口径不适用：中间稿；旧门禁同报 |
| 19 | lead/b2b_design_20261106/_hunks_frag.md | 18423 | **FAIL(3)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺要素 SHA256<br>缺要素 字节数<br>缺 SHA256 绑定行 | 4 条 | 口径不适用：diff 片段稿；旧门禁同报 |
| 20 | lead/b2b_isolated_20261107/INTEGRATION_REPORT.md | 24022 | pass | pass | pass | pass | — | 0 条 | PASS；绑定 2 条均 ca23c116（=qc151 母本实算相符）无路径→警告 |
| 21 | lead/b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md | 15179 | pass | pass | pass | pass | — | 1 条 | PASS，旧门禁误报消除（第 8 类）；绑定 ca23c116 无路径→警告 |
| 22 | lead/b2b_n1_binding_20261107/N1_BINDING.md | 8493 | **FAIL(2)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺要素 字节数<br>缺 SHA256 绑定行 | 3 条 | 口径存疑：表格式指纹声明（L12/L21/L53）但无行式绑定标记；旧门禁同报 |
| 23 | lead/b2b_preaudit_20261106/B2B_PREAUDIT.md | 20615 | **FAIL(1)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺 SHA256 绑定行 | 2 条 | 口径不适用：预审稿；旧门禁同报 |
| 24 | lead/b2b_preaudit_20261106/TASK.md | 8974 | **FAIL(1)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺 SHA256 绑定行 | 2 条 | 口径不适用：任务书；旧门禁同报 |
| 25 | lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md | 7344 | **FAIL(1)** | pass | pass | **FAIL(1)** | 缺要素 被核对象<br>缺 SHA256 绑定行 | 2 条 | 口径存疑：件名 BINDING、L43 表格声明指纹，但无行式绑定；旧门禁同报 |
| 26 | lead/b2_preaudit_20261106/B2_PREAUDIT.md | 28410 | pass | pass | pass | **FAIL(1)** | 缺 SHA256 绑定行 | 1 条 | 口径不适用：L139 引用纪律文字非本件绑定行；旧门禁同报 |
| 27 | lead/b2_preaudit_20261106/TASK.md | 6846 | pass | pass | pass | **FAIL(1)** | 缺 SHA256 绑定行 | 1 条 | 口径不适用：L89 引用纪律文字；旧门禁同报 |
| 28 | lead/bexec_n4_20261108/B_EXECUTION_SPEC.md | 32183 | pass | pass | pass | pass | — | 0 条 | PASS；绑定 6 条全部无显式路径→警告（回验未触发，见 §5.3 F2） |
| 29 | lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md | 22136 | pass | pass | pass | pass | — | 0 条 | PASS；绑定 2 条无路径→警告 |
| 30 | lead/b_unclosed_trace_20261108/B_BREAKPOINT2_TRACE.md | 19047 | pass | pass | pass | **FAIL(1)** | 引用锚指向不在盘对象 _dB_anchor_recompute_out.txt:18-19 | 0 条 | 新误报 ×1（R11）：L60 引证语境第三方绑定行 + 路径带 :18-19 行号后缀；三重实锤见 §5.2 |

## 附录A TV 违规样本（清单 req=[APPROVE_SCOPE] + BAD_BAN）

| 件 | 判定 | R9 | R10 | R12 | R11 | 新 problems | 旧 problems |
|---|---|---|---|---|---|---|---|
| _g7_tv1_missing_element.md | FAIL | FAIL(1) | pass | pass | FAIL(1) | 2 | 2 |
| _g7_tv2_overreach_positive.md | FAIL | FAIL(1) | FAIL(5) | pass | FAIL(1) | 7 | 7 |
| _g7_tv3_double_negation.md | FAIL | FAIL(1) | pass | FAIL(2) | FAIL(1) | 4 | 3 |
| _g7_tv4_no_binding.md | FAIL | FAIL(1) | pass | pass | FAIL(1) | 2 | 2 |
| _g7_tv5_forged_binding.md | FAIL | FAIL(1) | pass | pass | FAIL(1) | 2 | 2 |
| _g7_tv6_binding_missing_obj.md | FAIL | FAIL(1) | pass | pass | FAIL(1) | 2 | 2 |
| _g7_tv7_split_token.md | FAIL | pass | pass | pass | FAIL(1) | 1 | 2 |
| _g7_tv7b_wrapper_only.md | FAIL | pass | pass | pass | FAIL(1) | 1 | 1 |

## 附录B 四真实件（清单=绑定三要素 + BAD_BAN；末行 CANDIDATE 附加旧门禁词表口径）

| 件 | 字节 | 判定 | R10 命中(豁免) | R12 拦截 | R11 绑定回验 | 旧门禁 problems |
|---|---|---|---|---|---|---|
| CANDIDATE_RESIGN_YES_V2.md | 23129 | PASS | 6(6) | 0 | ee27b4ca…match | 4 |
| LEDGER_APPENDIX_DRAFT.md | 45719 | PASS | 3(3) | 0 | 6888379a…match | 2 |
| OBSERVATION_PROTOCOL_SPEC.md | 54351 | PASS | 0(0) | 0 | 3d463483…无路径 | 0 |
| C97_SCOPE_RECHECK.md | 21690 | PASS | 0(0) | 0 | 91d1317f…match; 1fe6b1b6…match | 0 |
| CANDIDATE_RESIGN_YES_V2.md | 23129 | PASS | 6(6) | 0 | ee27b4ca…match | 4 |

**统计**：

- **problems 全空（新模块）：6/30**（A_REDUCED_FORM、A_RESIDUAL_REFERENCES(n1)、INTEGRATION_REPORT、_integ_INTEGRATION_REPORT、B_EXECUTION_SPEC、_n4_SPEC_N4_B2B_MATRIX）。
- **仍有 problems：24/30**，逐条判定见上表「判定」列，归并为三类：
  - **旧门禁同报 · 清单口径不适用/口径存疑：23 件**——统一绑定清单施加于任务书/设计稿/台账/评审件等非复核回件型，或原 ask 是否要求行式绑定无法确证（口径存疑 7 件：e4_VERIFY、TESTS_REPORT、N1_CLOSURE、REVIEW_R2/R3、CANDIDATE_SEMANTIC_REVIEW、N1_BINDING、YI_SUPERSEDE_JIA_BINDING）。**非新模块误报**（新旧 problems 归一化比对：新 ⊆ 旧，程序化验证零例外），亦不判真违规（原 ask 文本未验）。
  - **新误报：1 件 1 条**——`b_unclosed_trace/B_BREAKPOINT2_TRACE.md`，详见 §5.2。
  - **客观真违规：0 件**。30 件中无一存在可现盘证实的绑定失配/不在盘（唯一被报「不在盘」的 b_unclosed_trace 条目经三重实锤判为新误报）。
- **误报消除（旧→新）**：30 件内 `_integ_INTEGRATION_REPORT.md` 1→0（第 8 类）；附录真实件 CANDIDATE 4→0、LEDGER 2→0（第 6/7/8 类）；TV 附件 TV7 2→1（第 5 类）、TV3 旧 3→新 2（旧门禁把单重否定对照也判违规，新模块恰拦 2 处双重否定）。
- **R10/R12 在 30 件语料**：BAD_BAN 五词命中 0 处（occurrences=0×30），items 各=5 非空跑；第 6/7 类的消误报/防漏判能力由 TV2（正面 ×5 全拦）与 TV3（双重否定 ×2 恰拦、单重对照不拦）及真实件 CANDIDATE（6 处全豁免=5 negation+1 quote_mention）、LEDGER（3 处全 negation 豁免）实证。

## 5 关键判定证据

### 5.1 误报消除实例（机制层）

- **第 8 类**：`_integ_INTEGRATION_REPORT.md` 绑定行被长分隔段隔断，紧邻正则漏（旧报「缺 SHA256 绑定行」），R11 容忍匹配捕获并判 PASS（警告：无显式路径）。声明锚 `ca23c116…` 经现盘实算 = `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`/412759B（本轮 hashlib 实跑相符）。
- **第 6/7 类**：CANDIDATE 六处 BAD_BAN 命中（旧朴素计数 6 条违规）→ R10 分类 5×negation + 1×quote_mention 全豁免、R12 拦 0；LEDGER 三处「不宣告…已生效」全 negation 豁免。两件新门禁 problems=0。
- **第 5 类**：TV7 拆断件旧报「缺要素 APPROVE_SCOPE」，R9 经 N2 拼接判在场；自检 U2 证明词表带包裹符形态（「被核对象」整体入表）朴素误报、本模块剥符后判在场。

### 5.2 唯一新误报三重实锤（`b_unclosed_trace/B_BREAKPOINT2_TRACE.md`，R11）

新门禁报：`引用锚指向不在盘对象 _dB_anchor_recompute_out.txt:18-19（R11/R3-3c）`（旧门禁 0 条——紧邻正则连绑定行都没认出）。判定**新误报**，依据（全部本轮实跑）：

1. **引证语境误当本件绑定行**：该命中在 L60，形态为转述第三方件的证据引文——「`_dB_anchor_recompute_out.txt:18-19`（本轮实读：「被核对象 SHA256 = 4a342405…，字节数 = 48343（被核…」」。R10 有 quote_mention 豁免思想，**R11 无引证豁免**，把引文内的绑定行当本件绑定行回验。
2. **路径带 `:18-19` 行号后缀未剥离**：同行回看采到的「路径」是 `_dB_anchor_recompute_out.txt:18-19`，文件名检索必败；而该对象实际在盘 = `lead/dtrigger_round2_20261107/_dB_anchor_recompute_out.txt`（本轮定位存在）。
3. **锚本体为真**：引文声明 `4a342405…`/48343 = `lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md` 现盘实算相符（4a3424050125…/48343）。
4. **谓词级复现**：对同形态合成串直调 `g7.r11_scan` → 同一 problem + path=`_dB_anchor_recompute_out.txt:18-19`（本轮实跑在案）。
5. 对照事实：本件 L5-L8 **四条真绑定行**（「被核对象 SHA256 = hex，字节数 = n（`path`）」形态）声明的四锚经现盘逐一实算**全 MATCH**（B_BREAKPOINTS_2_6.md/19527、R2_FINAL_GRADE.md/30140、_verify_B_out.txt/7229、_bt_B崩点2_尾串追溯/12706）——本件不该 FAIL。

**修法建议（不改谓词，见 §7 R11 项）**：①绑定行落于「…」引文内且非本件声明时降为警告；②路径剥 `:行号(范围)` 后缀后再解析；③（与 F2 合并）采集 hex 之后尾括注内反引号路径。

### 5.3 F2 回验覆盖缺口（重要发现，非误报）

30 件语料共检出绑定行 **18 条**（6 个 PASS 件 13 条 + b_unclosed_trace 5 条），其中 **17 条 path=null → 仅警告，现盘回验 0 次触发**；唯一采到路径的恰是 §5.2 那条伪造路径。根因：`r11_scan` 只在①被核对象↔SHA256 分隔段、②同行命中点之前，两处找路径（`_g7_predicates.py:185-191`）；本语料主流形态「被核对象 SHA256 = hex，字节数 = n（`path`）」的路径在 hex **之后**。后果分层：不产生错误 FAIL（警告可见），但 R3-3a/c「堵假阴性」在主流形态上未生效——**若某件尾括注路径的哈希是伪造的，本模块会放走**。真实件附录的分隔段形态（CANDIDATE/LEDGER/C97）回验正常触发 4/4 match，与 g7 S1 一致。此缺口属第 8 类谓词家族的覆盖面问题，如实上报，不为本轮回归绿灯而掩盖。

### 5.4 自检追加发现：R10 对词表声明语境的 2 条误报（封印前实跑）

- 封印前用本模块回扫本报告（清单同 §4）做端到端自证时，R10 报 `越权断言 已入账`、`越权断言 已追加` 各 1 条，位置均在 **L55**——§4 的清单声明行，两词位于**反引号代码跨度** `["已生效","可应用母本","放行 N-5","已入账","已追加"]` 内。
- 机制：R10 的引证豁免只认「…」短跨度（SPAN_RE ≤80 字符），**反引号代码跨度不在数据语境豁免之列**；同跨度前三个词（已生效/可应用母本/放行 N-5）仅因 24 字符窗内恰有「禁用词」的「禁」而免报（NEG_RE 邻近误豁免残余 g7 §6.4 的反向实例，纯窗距运气）——后两词超出窗距即被判「无否定、无引证语境」的断言。
- 判定：**误报**（声明/讨论词表是数据不是断言）。这是第 1/4 类（词表/自指家族）机制在本会话的一次活体显形，发生在本报告这个新件上，**不在 30 件历史语料回归面内**。自指放大实况：本节写入后对终版报告回扫，R10 同类命中增至 **12 条**（本节文字与附录表格自身又复载了这五个词）——讨论误报的报告被自家门禁越扫越红，恰是「第 4 类自指禁令」机制在报告层的再现。修法 = R10 增加反引号代码跨度的数据语境豁免 + 报告层词表声明节的扫描豁免（均未实施，`_g7_predicates.py` 只读）。

## 6 第四步：残余误报类统计（11 类逐类）

11 类登记原文 = 上一轮门禁复盘派发载荷（`.zcode/workflow-runs/dwfrun-65d9f3a9-…mjs`，逐字核对）。逐类观察：

| 类 | 登记定义 | 本回归观察 | 结论 |
|---|---|---|---|
| 1 | 禁用词子串扫到 BANNED_PAT 常量/mock 路径 | 本模块只扫交付件文本、词表=BAD_BAN 行为词族，30+8+5 件 0 命中；未扫 .py、无 mock 形态 | **未观察到**（不在本模块检查面内；未覆盖） |
| 2 | 措辞不匹配（最小字段 vs 最少字段） | 23 件「缺要素」全部为统一清单口径问题，无一例同义词形态；回归清单无同义词需求 | **未观察到**（R9 不做同义词扩展；未覆盖） |
| 3 | 版本锚缺失：门禁空跑通过 | U1 实证空清单→FAIL；30 件无一件在 items=0 下 PASS；a_residual_n1 的 r1 版本锚（3343cfbe）正确落警告不误 FAIL | **已消**（计数机制，回归+自检双实证） |
| 4 | 自指禁令：报告主题本身是被禁词 | 禁用词表与全部被扫件主题无交集，0 命中 | **未观察到**（未覆盖） |
| 5 | 带反引号标识符判缺要素 | TV7/TV7b 判在场、U2 词表剥符防线、30 件 R9 新增误报 0 | **已消**（回归实证） |
| 6 | 否定式自指当越权断言 | CANDIDATE 6 处全豁免（5 negation+1 quote_mention）、problems=0；TV2 正面 ×5 全拦；奇偶法反例 TV3 由 R12 恰拦 2 | **已消**（回归实证） |
| 7 | 否定句含完成时词当越权断言 | LEDGER 3 处「不宣告…已生效」全豁免；problems=0 | **已消**（回归实证） |
| 8 | 绑定行路径隔断判缺绑定 | _integ/CANDIDATE/LEDGER 旧报缺绑定→新 PASS；**但回归发现 R11 家族内两残余叠加造成 1 例新误报（§5.2）+ 回验覆盖缺口 F2（§5.3）** | **主体已消，家族内报 1 新误报** |
| 9 | 带分隔符编号（D-01 vs \bD(\d+)\b） | 本回归清单与四谓词均无编号匹配项 | **无观察**（未实装） |
| 10 | 加粗包裹的绑定行（**SHA256 = hex**） | 合成探针实测：登记形态 `被核对象**SHA256 = hex**` → BIND_RE 匹配 ✓；`**被核对象** SHA256 = hex` → 匹配 ✓；变体 `SHA256 = **hex**`（仅 hex 加粗）→ **不匹配**。30 件未遇实件 | **登记形态已被 R11 机制附带容忍（合成实测）；`=`后加粗 hex 变体为合成残余** |
| 11 | 同义措辞（【原】/【改】 vs 改前改后） | 无对应检查项；N1_BINDING 表格式指纹声明（L12/L21/L53）即「结构在场、字面不在场」家族的语料实例，R11 判缺绑定 | **未观察到误报 / 未实装** |

**(b) 新模块引入的新误报：30 件回归面内 1 例**——§5.2（R11 引证语境 + 行号后缀）；30 件+TV+真实件全量「新 problems ⊆ 旧 problems」程序化比对零例外（新模块没有比旧门禁多报任何一条，除该例）。另：封印前自检（门禁回扫本登记报告）暴露 R10 词表声明误报 2 条（§5.4，反引号代码跨度无数据豁免）——属 R10 引证/数据语境豁免缺口的同族残余，不在 30 件回归面内，如实并入登记。

**(c) 结论**：四谓词实装后，**11 类降到 6 类残余（第 1/2/4/9/10/11 类）**。已消 5 类：第 3 类（检查计数）、第 5/6/7/8 类（R9/R10+R12/R11）；其中第 8 类家族内尚有 1 例新误报与回验覆盖缺口（§5.2/§5.3），第 10 类登记形态经合成探针已被 R11 附带容忍但无实件验证。

## 7 第五步：剩余类处理建议

| 类 | 建议 | 路线 |
|---|---|---|
| 1 禁用词子串 | **可结构谓词修**：AST 真实调用边判罪（裸 import 除罪为警告）、派生副本先对母本做差（逐字节相同⇒新增边恒零）、不遍历字符串常量——模板 R4 已给设计（GATE_TEMPLATE_FIXED.py.txt r2）。文本层无解，勿再用全文子串 | 实装 AST 谓词 |
| 2 措辞不匹配 | **半结构可修**：同义词组 + 任务书原文优先 + 语料频次留档（模板 R2）。「任务书原文优先」需 ask 源供给 → 半自动 | 实装词组编译 + ask 层配合 |
| 4 自指禁令 | **可结构谓词修**：作用域限定（只查特定区段/表格列，不查全文）；根治需 ask 层同步（提供掩码形式或改禁「行为」不禁「字样」，GATE_FALSE_POSITIVES.md §6 R5-4） | 实装作用域谓词 + ask 层同步 |
| 9 编号形态 | **可结构谓词修（纯文本）**：编号归一化——把 D-01/D01/D_01/D.01 统一成同一 token 再数（上轮复盘已给方案），实现成本低 | 实装归一化谓词 |
| 10 加粗绑定行 | **不需要新谓词**：登记形态已被 R11 附带容忍（本轮合成实测）。建议把该形态与 `= **hex**` 变体各固化一例进 R11 回归样件，防未来正则改动回退 | 固化样件 |
| 11 同义措辞 | **结构存在性谓词可修但判据非平凡**：不查字面词，查「成对改前/改后块」（相邻标注块对、两列表格）——N1_BINDING 的表格式指纹声明即此家族实例。建议半自动：结构探测 + 人工确认 | 实装结构探测 + 人工复核兜底 |
| （新增）R11 三条 | ①尾括注路径采集（hex 后 `（`path`）`）——修 F2 覆盖缺口；②路径剥 `:行号(范围)` 后缀；③引文内绑定行降警告——修 §5.2 新误报。三条均属 R11 家族增量，**未实装**（`_g7_predicates.py` 只读铁律），留给谓词所有者 | 谓词增补（未实施） |
| （新增）R10 一条 | ④反引号代码跨度视为数据语境、豁免越权词扫描——修 §5.4 的 2 条词表声明误报（本会话活体实证）。同时建议把「24 字符窗内邻近否定词误豁免」从纯窗距运气改为子句内最近否定词与命中点同短语判定（§5.4 前三词靠「禁」侥幸豁免即此问题） | 谓词增补（未实施） |

## 8 未验项（如实）

1. 第 5 类**原始误报件仍未定位**（沿 g7 §6.1；本回归 30 件未再现该类，机制修复经 TV7/TV7b/U2 实证）。
2. 23 件「口径不适用/存疑」判定基于件名与文中引用语境，**原 ask 是否要求各件自带绑定行未验**（ask 文本不在本任务可读范围内逐一追溯）。
3. R11 机制对第 10 类的容忍为**合成探针实测**，30 件未遇实件。
4. 30 件之外的历史交付件（余 304 件）未跑——任务书指定前 30 件。
5. F2 缺口的修复（R11 尾括注路径采集）未实施、未验证。
6. 第 1/2/4 类「未观察到」仅指本回归检查面内零命中；若引入对应检查项（.py 禁词扫描/同义词表/自指主题词），三类会否复发未验（R9-R12 不覆盖它们）。

## 9 纪律声明与绑定

- 零真机、零采样代码；未 commit、未 push。
- **未改任何既有模板与交付件**：`lead/gate_fp7_20261108/`、`lead/gate_template_20261108/`、30 件语料、TV 样本、真实件、两台账全部只读；只读域 pycache 经 mtime 核查非本轮所写（§1）。
- 本任务新增全部落 `lead/gate_r9r12_20261109/`：`_g9_gate.py`、`_g9_regression.py`、`_g9_regression_out.json`、`_g9_table_fragment.md`、本件。
- 绑定行：

> 被核对象 SHA256 = a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6，字节数 = 11623

> 被核对象 SHA256 = 7074d7aa28498a5e51f8d038531f11543528fa28bbf8434907569502526b401a，字节数 = 6652

> 被核对象 SHA256 = 7f16da217dba02008546d643bb51c0100d7126939df947ad0c46a4fd478f11d8，字节数 = 123691

（三行依次 = 门禁模块 `_g9_gate.py`、回归运行器 `_g9_regression.py`、机读回归结果 `_g9_regression_out.json`；封印前 hashlib 实算。）
