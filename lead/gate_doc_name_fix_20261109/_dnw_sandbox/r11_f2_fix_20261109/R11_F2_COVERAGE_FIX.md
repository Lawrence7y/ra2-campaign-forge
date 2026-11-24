# R11 F2 覆盖缺口修补交付报告（R11_F2_COVERAGE_FIX.md）

日期：2026-11-09。撰写：F2 修补报告撰写员（交付轮，独立会话）。
被修补对象：`lead/gate_fp7_20261108/_g7_predicates.py` 的 r11_scan（_g7_predicates.py:151-222）——**原件零改动**；补丁 = 本写域 `_f2_r11plus.py`（`r11_scan_plus`，SHA256 83f8217f…df8f75 / 15723 B，见 §5.1 绑定行）。
上游输入：修补回件 `lead/r11_f2_fix_20261109/_f2_F2_PATCH_REPORT.md`（0b10d1d0…7aab5 / 17451 B）＋ 复核回件（verdict = **confirmed**，见 §5.1）。
本文全部数字出自本会话（2026-11-09）实跑复现；凡本会话未能执行的核验逐条列入 §5.5「未验项」，不补造。

## 1 目的与边界

**目的**：修补 R11 谓词的 F2 覆盖缺口——原版 `r11_scan` 只在「被核对象↔SHA256 分隔段」与「同行命中点**之前**」两处找反引号路径（_g7_predicates.py:184-191），而语料主流绑定形态「被核对象 SHA256 = hex，字节数 = n（`path`）」的路径在 hex 之后的**尾括注**；后果是 30 件回归面上 path=null 占 18/19、现盘哈希重算成功 0 次，「堵假阴性」在主流形态上未生效（GATE_R9R12_REGRESSION.md:179，§4.5）。

**边界（铁律逐条）**：
- 不改动 `_g7_predicates.py` 原件与 `lead/gate_r9r12_20261109/` 全部件；本轮开场与收尾两次 hashlib 实算六保护件指纹全部 UNCHANGED（§2.1、§5.4）。
- 补丁只以「新增模块」形式落在本写域 `lead/r11_f2_fix_20261109/`，对原件**只读加载且加载前验指纹**（_f2_r11plus.py:58-74），失配即拒绝运行（本会话以篡改副本实测拒绝成立，§4.4-e）。
- 不靠放松校验提升覆盖率：原版能采到的 raw 路径增强版原样采到（_f2_compare.py 内断言，本会话复跑通过）；原版全部问题消息逐字保留（S5b/S5c，§4.4）；采不到的路径如实记「采不到」，不跳过、不越行强采、不做全文/全仓 hash 反查（§5.3）。
- 零真机（未启动任何游戏进程、未 taskkill、未读活进程内存）、零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；未 commit、未 push（git log -1 = 2657458 系既有提交）。
- 修补回件内嵌的编排方提取 JSON（`{"count":0, "nullPath":0}`）为提取空结果，不作计数依据；计数以机读件 `_g9_regression_out.json` binding_details 为准（见 §2.2 勘误）。

## 2 上游指纹与缺口复现

### 2.1 上游指纹（六件，本会话 hashlib 实算）

实跑命令（开场基线 + 收尾复验各一次，结果逐字一致）：
`python -I -X utf8 -c`（hashlib 六件）与 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/r11_f2_fix_20261109/_f2w_final.py`。

| 上游件 | SHA256（本会话实算） | 字节 | 与编排方基线 |
|---|---|---|---|
| lead/gate_fp7_20261108/_g7_predicates.py | 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120 | 11743 | 一致 |
| lead/gate_r9r12_20261109/_g9_gate.py | a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6 | 11623 | 一致 |
| lead/gate_r9r12_20261109/_g9_regression_out.json | 7f16da217dba02008546d643bb51c0100d7126939df947ad0c46a4fd478f11d8 | 123691 | 一致 |
| lead/gate_r9r12_20261109/GATE_R9R12_REGRESSION.md | dc222c2409db9a63c1e2cd95b979069a16b5067585bd8a46d7a9d40657fe27c0 | 37578 | 一致 |
| lead/PENDING_DECISIONS.md | 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 | 52419 | 一致 |
| lead/GOAL_THREE_TARGETS_20261018.md | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 759518 | 一致 |

六件 6/6 与编排方【编排方指纹】逐字一致；修补件与复核件的绑定对象 `_f2_r11plus.py` 本会话实算 83f8217f…df8f75 / 15723 B（§5.1）。

### 2.2 缺口复现（实跑）

命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/r11_f2_fix_20261109/_f2_repro.py`
输出（本会话）：
```
复现：绑定行总数=19，path=null=18，path 非 null=1
与回归 JSON binding_details 不一致的文件数=0
```
- 30 件回归件重跑原版 r11_scan：**19 条绑定行、18 条 path=null、1 条采到且 match=False**（即 #30 L60 的 `_dB_anchor_recompute_out.txt:18-19`，被 R3-3c 报「不在盘」）——与 `_g9_regression_out.json` binding_details 逐条一致（脚本内断言 0 漂移），与 GATE_R9R12_REGRESSION.md:138「19 条 / 18 条 null / 采到 1 条（伪造，match=False）/ 现盘重算 0 次成功」一致。
- **计数勘误（沿 regression MD:181）**：任务书背景「18 条绑定行中 17 条 path=null」系实装回件旧文字；机读实数 = 19/18/1（b_unclosed_trace 按实装口径漏数 1 条）。本报告两套口径并列给出（§4.2、§5.2），不以「17 条」为计数基础。
- 复跑确定性：复跑后 `_f2_repro_out.json`（3bc0ed8b…/28386 B）、`_f2_compare_out.json`（148ea8d6…/44958 B）、`_f2_selftest_out.json`（77fa7564…/4423 B）与复跑前字节级一致（hashlib 实算，指纹未变）——既证明输出确定性，也证明修补报告 §7 所录产出件指纹未被本轮复跑破坏。

### 2.3 18 条 path=null 的形态分类与比例（F2-a/F2-b/F2-c/F2-d）

形态分类由两条独立路径交叉证实：①修补件 `_f2_repro_out.json` 全量 dump（行号/反引号跨度/命中列）；②复核件 `_f2v_context.py` 重跑原版并打印每条绑定行 ±2 行原文（本会话复跑，19/19 逐条核对一致，错 0 处）。

| 形态 | 定义（实测） | 条数 / 占 19 条 | 占 18 条 null | 明细（文档 L 行） |
|---|---|---|---|---|
| F2-a | 路径在命中点**之后同一行**的括注（反引号或明文） | 7 / 36.8% | 38.9% | A_REDUCED_FORM L93（明文 `[…]`）；B_EXECUTION_SPEC L227（反引号）；B_BREAKPOINT2_TRACE L5/L6/L7/L8（反引号）、L64（明文照录） |
| F2-b | 采到的路径带**行号后缀**（`_dB_anchor_recompute_out.txt:18-19`） | 1 / 5.3% | —（非 null，原已采到） | B_BREAKPOINT2_TRACE L60（原版唯一采到条目，因后缀解析必败报 R3-3c，系 regression MD:167 §4.4 自认新误报） |
| F2-c | 路径在**相邻行**（后一行反引号） | 1 / 5.3% | 5.6% | INTEGRATION_REPORT L147（对象路径在其后一行 L148） |
| F2-d | **±1 行内确无任何路径**（真采不到） | 10 / 52.6% | 55.6% | A_RESIDUAL_n1 L130；INTEGRATION_REPORT L31；_integ L5；B_EXECUTION_SPEC L51/L52/L53/L228/L229；_n4_SPEC L28/L29 |

要点：①修补回件任务书预期三类形态（尾括注/行号后缀/相邻行）全部实锤存在，但**还确证存在第四形态 F2-d（真采不到）**，占 18 条 null 的 55.6%，如实登记不跳过；②F2-d 的 10 条绑定行本体即「被核对象 SHA256 = hex，字节数 = n」严格无路径格式（复核件 `_f2v_context.py` 逐条打印可证），其中 L228/L229/L29 的相邻行恰是**另一条绑定行**（L227/L228/L28），若盲目越行采集会把别条绑定的对象误绑到本条——补丁据此内置防误绑排除（§3.1-T3）。

## 3 补丁设计与实现（_f2_r11plus.py）

入口：`r11_scan_plus(text, doc_dir, root=None, recompute=None)`，返回 `(problems, warnings, bindings)` 契约与原版一致（_f2_r11plus.py:139-142）；bindings 每条在原三键（declared/path/match）之上**只增不改**地追加 tier/citation/tried/alt 等字段（_f2_r11plus.py:40-41）。

### 3.1 三类采集路径（T1 保留 + T2/T2N/T3 新增）

- **T1（原版语义逐行保留）**：分隔段反引号路径 → 命中点前同行反引号路径，与 _g7_predicates.py:184-191 逐行同构（_f2_r11plus.py:164-172）；解析顺序 doc_dir → root → 原样不变（_f2_r11plus.py:105-121 对照 _g7_predicates.py:194-200）。raw 路径先试，raw 存在 ⇒ 行为与原版完全一致（_f2_compare.py 断言「原版采到 path 的绑定增强版原样采到」，本会话复跑通过）。
- **T2（F2-a 主形态）**：命中点**之后**同一行的反引号路径（尾括注，窗宽 400 字符，_f2_r11plus.py:174-176）。
- **T2N（F2-a 明文变体）**：命中点之后同一行的**明文**路径形 token，正则要求至少一层 `/` 或 `\` 分隔符 + 扩展名（_f2_r11plus.py:83）；与 T2 反引号跨度重叠者去重（_f2_r11plus.py:178-181）。覆盖 L93 的 `[lead/…/_ar_out.txt]` 与 L64 的 `（lead/…/_bt_….md，…）`。
- **T3（F2-c）**：相邻行（前一行/后一行）反引号路径；**相邻行自身是绑定行则整行排除**（_f2_r11plus.py:183-194）——防把别条绑定的对象误绑到本条，沿原版 docstring「限同一行，防止把上一行的无关路径误绑到本行绑定」（_g7_predicates.py:163-164）的同一防误绑精神。
- **any-match-wins**：多候选按 T2→T2N→T3 逐个回验，首个 sha(+声明字节数) 全 MATCH 者即验证成立（_f2_r11plus.py:250-265），防多候选误伤（S4 实测，§4.4）。

### 3.2 剥行号后缀（F2-b）

`LN_SUFFIX` 正则匹配 `:`/`#` + 可选 `L` + 行号（含 `-`/`–`/`~` 范围段）结尾（_f2_r11plus.py:80）；`strip_line_suffixes` 循环剥至多 6 层，候选 = [原串, 剥一层, …]，**原串恒在首位优先**（_f2_r11plus.py:90-102）——原串存在时行为与原版完全一致。Windows **盘符**冒号（`C:\`、`C:\x`）后无数字 ⇒ 正则不匹配 ⇒ 不剥（本会话实测 §4.4-b）。实测样例（`_f2v_edge.py` ⑥ 本会话复跑输出）：`_x.txt:962/:963/:965` → `[_x.txt:962/:963/:965, _x.txt:962/:963, _x.txt:962, _x.txt]`；`f.md:L18-L19` → `[f.md:L18-L19, f.md]`。

### 3.3 引文语境识别（修 §4.4 新误报的处方③）

绑定行命中点**前 24 字符内（同行）**出现显式标记（词表从严：原文照录/照录/引文/转录/本轮实读/内嵌 JSON 传入，_f2_r11plus.py:86-87）→ 该绑定行的 FAIL 级问题降为警告（_f2_r11plus.py:199, 224-230）；**回验照跑、事实结果照记**（rec.match/rec.recomputed 照写；T1 不在盘时仍按引文语境要求尝试同行 T2→T2N 替代锚回验并记录 rec.alt，_f2_r11plus.py:211-230）。降级 ≠ 跳过。本语料中该形态仅 #30 L60 一处（「…本轮实读：「被核对象 SHA256 = 4a34…」」，regression MD:169 实锤真引文）。反例检验见 §4.4-c。

### 3.4 证据分级（不放松、不凭空 FAIL）

- T1/T2 = 绑定行**显式反引号锚**：回验 MISMATCH → problem（R3-3a，消息原文与原版一致，_f2_r11plus.py:241, 278）；T1 不在盘 → problem（R3-3c 消息原文，_f2_r11plus.py:210 对照 _g7_predicates.py:203）。定级与原版同级，任务书明示允许。
- T2N/T3 = **弱证据**（启发式明文/跨行歧义）：MISMATCH 或均不在盘 → 一律仅 warning（_f2_r11plus.py:284-302），绝不凭空 FAIL——原版对这些形态连采集都不做，本补丁只增信息不减信息。
- 缺显式路径 → 保留原版 R3-3b 警告「绑定行缺显式路径，需人工锚定（R11/R3-3b）」（_f2_r11plus.py:305 对照 _g7_predicates.py:217）；缺绑定行 problem 消息逐字保留（_f2_r11plus.py:307-309 对照 _g7_predicates.py:219-221，S5c 实测一致）。

## 4 覆盖率提升验证与新误报检验

### 4.1 逐条表（19 条绑定行，机读实数口径）

数据源：本会话复跑 `_f2_compare.py` 输出（`_f2_compare_out.json`）＋ `_f2_repro_out.json` 行号，提取脚本 `_f2w_extract.py`。回验结果均为**现盘 hashlib 重算**值与声明 sha+字节数逐字比对。

| # | 文件 | 行 | declared 前 12 | 形态 | 原 path | 新采集 path（tier） | 回验 | 结果 |
|--:|---|--:|---|---|---|---|---|---|
| 1 | a_dim_reduced_20261108/A_REDUCED_FORM.md | 93 | 28cd3794a571 | F2-a | null | lead/a_dim_reduced_20261108/_ar_out.txt（T2N） | 是 | **MATCH** 28cd…2a72 / 24614 B |
| 2 | a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md | 130 | 3343cfbe467d | **F2-d** | null | —（±1 行无路径） | 否 | 采不到（R3-3b 保留） |
| 3 | b2b_isolated_20261107/INTEGRATION_REPORT.md | 31 | ca23c116064b | **F2-d**（回件摘要行，对象即声明 hex 本身） | null | — | 否 | 采不到 |
| 4 | b2b_isolated_20261107/INTEGRATION_REPORT.md | 147 | ca23c116064b | F2-c | null | lead/b2b_isolated_20261107/qc151_trip.isolated.py（T3） | 是 | **MATCH** ca23…76d2 / 412759 B |
| 5 | b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md | 5 | ca23c116064b | **F2-d** | null | — | 否 | 采不到 |
| 6 | bexec_n4_20261108/B_EXECUTION_SPEC.md | 51 | 517889c68f03 | **F2-d** | null | — | 否 | 采不到 |
| 7 | 同上 | 52 | ca23c116064b | **F2-d** | null | — | 否 | 采不到 |
| 8 | 同上 | 53 | cb4f3011a75f | **F2-d** | null | — | 否 | 采不到 |
| 9 | 同上 | 227 | cb4f3011a75f | F2-a | null | _n4_SPEC_N4_B2B_MATRIX.md（T2） | 是 | **MATCH** cb4f…d306 / 22136 B |
| 10 | 同上 | 228 | 517889c68f03 | **F2-d**（前行 L227 是另一条绑定行，防误绑排除） | null | — | 否 | 采不到 |
| 11 | 同上 | 229 | ca23c116064b | **F2-d** | null | — | 否 | 采不到 |
| 12 | bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md | 28 | 517889c68f03 | **F2-d** | null | — | 否 | 采不到 |
| 13 | 同上 | 29 | ca23c116064b | **F2-d** | null | — | 否 | 采不到 |
| 14 | b_unclosed_trace_20261108/B_BREAKPOINT2_TRACE.md | 5 | 3aad3bddda08 | F2-a | null | lead/r2_unclosed_b_20261108/B_BREAKPOINTS_2_6.md（T2） | 是 | **MATCH** 3aad…03ae / 19527 B |
| 15 | 同上 | 6 | 7ce09812f7bd | F2-a | null | lead/r2_final_grade_20261108/R2_FINAL_GRADE.md（T2） | 是 | **MATCH** 7ce0…ab24 / 30140 B |
| 16 | 同上 | 7 | 4ee6a6b78d80 | F2-a | null | lead/dtrigger_round2_20261107/_verify_B_out.txt（T2） | 是 | **MATCH** 4ee6…c107 / 7229 B |
| 17 | 同上 | 8 | 793e06d27845 | F2-a | null | lead/b_unclosed_trace_20261108/_bt_B崩点2_尾串追溯_20261108.md（T2） | 是 | **MATCH** 793e…59ea / 12706 B |
| 18 | 同上 | 60 | 4a3424050125 | F2-b（引文语境） | _dB_anchor_recompute_out.txt:18-19（match=False，原报 R3-3c） | 同左（T1 原样）＋ 同行替代锚 lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md（alt/T2N） | 是 | **MATCH**（经替代锚）4a34…94726 / 48343 B；R3-3c 降为警告 |
| 19 | 同上 | 64 | 793e06d27845 | F2-a（明文括注，原文照录语境） | null | lead/b_unclosed_trace_20261108/_bt_B崩点2_尾串追溯_20261108.md（T2N） | 是 | **MATCH** 793e…59ea / 12706 B；无问题无警告 |

### 4.2 汇总（同一份 30 件清单，双版对跑，本会话复跑）

命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/r11_f2_fix_20261109/_f2_compare.py`（复跑输出与修补轮字节级一致）

| 指标 | 原版 r11_scan | 增强版 r11_scan_plus |
|---|---|---|
| 绑定行总数 | 19 | 19（条数/declared 序列逐一相同，断言通过） |
| 采到路径 | 1/19 | **9/19** |
| 现盘重算成功 match=True | 0/19 | **9/19**（MATCH 9 / MISMATCH 0） |
| problems 合计 | 24 | **23**（唯一变化 = #18 行那条 R3-3c 按处方③降级） |
| warnings 合计 | 18 | **11**（10 条 F2-d 的 R3-3b ＋ 1 条 L60 引文降级警告） |
| 凭空新增 problem | — | **0**（S6 逐件清点 = 0 件；29/30 件 problems 逐字不变） |
| R11 级 verdict PASS | 6/30 | **7/30**（唯一翻转 = #30，修的正是 §4.4 自认原版误报） |

**覆盖率（两套口径并列）**：
- 任务书背景口径（「18 条绑定行」= 旧文字，含勘误）：采到/回验 **1/18 → 9/18**（原 1 条本就未成功重算；增强版 9 条全部现盘重算成功）。
- 机读实数口径（19 条绑定行）：采到 **1/19 → 9/19**；现盘重算成功 **0/19 → 9/19**（MATCH 9 / MISMATCH 0）。18 条 path=null 中新采到 **8 条**，余 **10 条 F2-d 真采不到**（§5.3）。

### 4.3 独立回验（不经补丁模块比较逻辑的第三方复算）

- 撰写员独立复算（`_f2w_checks.py`，本会话实跑）：9 条 match=True 中 **8 条直接现盘重算**的 sha 与 declared **逐字一致**、字节数逐字一致；#18 经同行替代锚——本会话独立 hashlib 实算 `lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md` = **4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726 / 48343 B**，与 #18 声明逐字吻合。同时实查 `_dB_anchor_recompute_out.txt` **不在**被扫文档目录 lead/b_unclosed_trace_20261108/、**在**邻目录 lead/dtrigger_round2_20261107/（3e9588ce…/14479 B）——证实原版 R3-3c 系把「引文出处指针」当「被核对象锚」的误报（regression MD:170 第 2 条实锤）。
- 复核件独立复算（`_f2v_verify9.py`，本会话复跑）：对 9 条 match=True 用自己的 hashlib 直读 verified_path 重算，`checked 9`，9/9 sha_ok=True 且 bytes_ok=True；tier 分布 = 5×T2 + 2×T2N + 1×T3 + 1×T1(alt)。

### 4.4 新误报检验（全部本会话实跑）

- **(a) 原 PASS 件是否被误判**：`_f2_selftest.py` 复跑 **24/24 PASS**（退出码 0）。S6：增强版 problems 多于原版的文件 = **0 件**；原 R11-PASS 6 件（A_REDUCED_FORM、A_RESIDUAL_REFERENCES、INTEGRATION_REPORT、_integ_INTEGRATION_REPORT、B_EXECUTION_SPEC、_n4_SPEC）增强后**全部保持 PASS 且 problems=0**（`_f2w_pass.py` 实跑），其中 3 件新增回验 MATCH（#1/#4/#9）。整体 verdict 仅 #30 FAIL→PASS。
- **(b) 盘符误剥实测**（`_f2v_edge.py` ⑥ 本会话复跑）：`C:\path:18` → `[C:\path:18, C:\path]`（不误剥成 `C`）；`C:\x`、`C:`、`C:\` → 原样不剥；`C:\Users\a\f.md:18-19` → 保盘符剥后缀；`:L18`/`#L18`/`:L18-L19`/`:962/:963/:965`/`:18:19` 循环剥全对、原串恒首位；`plain.md` 不动。**已登记微瑕**：`12:30` 会剥出变体 `12`（原串优先 + 需 64 位 hex 撞盘才可能误判，实害可忽略——复核回件同条登记）。F2-b 正例（S2）：真实在盘文件 + `:10-20` 后缀 → **原版误报 R3-3c（假阳性），增强版剥后缀回验 MATCH**——修的是原版误报而非放松。
- **(c) 引文降级反例**（`_f2v_edge.py` ⑦ 本会话复跑，对象在盘、声明 hash 为错值，基线必须 FAIL）：无标记 → FAIL；伪标记 `引：`/`引用锚已修复：`/`引述待核：` → **FAIL**（白名单外不降级）；标记距命中点 >24 字符 → **FAIL**；标记仅在前一行 → **FAIL**（同行规则）；显式「原文照录」及「自身断言+窗内『引文』/『本轮实读』」→ 降级为警告且 match=False 照记。**已登记残余风险**：窗内含「引文」「本轮实读」字样的自身断言会被误降级（g/g2 两例）——该降级系 regression MD:175/225 处方③明文要求、不增覆盖率、事实照记、语料仅 #30 L60 一处真引文，属处方性启发式固有风险，词表可被措辞穿透。⑦b 对照：hash 正确 + 窗内「引文」→ 两版都 PASS（无误报）。
- **(d) any-match-wins**（S4）：同行两锚一失配一匹配 → 验证成立、零 problem（防多候选误伤）。
- **(e) 指纹门与消息保真**（`_f2v_final.py` 本会话复跑）：以本写域篡改副本实测 load_g7 **拒绝运行**（RuntimeError 指纹失配）；不在盘候选警告含完整路径非截断 `C`（`采集到候选锚但均不在盘：C:\no\such_dir\missing.md:5-6（R11+/F2，仅警告）`）；S5b R3-3c 消息、S5c 缺绑定行消息与原版**逐字一致**。
- **(f) 对抗性探针（语料外残余风险，如实登记）**（`_f2v_edge.py` ⑧ 本会话复跑）：合成文本「无 T1 路径 + 尾括注偶然反引号引用**另一在盘文件**」→ 增强版新增 1 条 R3-3a problem（原版仅 R3-3b 警告）。该形态 30 件语料 **0 触发**；T1/T2 显式锚失配 → problem 为任务书明示允许定级。登记为语料外残余风险，不掩盖。

## 5 复核回件、剩余未覆盖与声明

### 5.1 复核回件（如实转记）

复核 verdict = **confirmed**（非 refuted/partial，不标 unconfirmed）。复核两条残余风险已如实登记并在 §4.4-(c)/(f) 复现：①引文降级词表可被措辞穿透（自身断言+窗内标记误降级，处方性启发式固有风险）；②语料外对抗形态（无 T1+尾括注偶然反引号他盘文件+失配→新增 R3-3a），30 件语料 0 触发。复核未验项：未重放撰写人自带 _f2_selftest.py/_f2_compare.py（以 _f2v_* 独立实现替代）——本交付轮已亲自复跑两者（24/24 PASS；对比输出字节级一致），此缺口已闭合。

复核回件绑定行（被核对象 = 补丁模块，本会话 hashlib 实算逐字一致）：

`lead/r11_f2_fix_20261109/_f2_r11plus.py`
被核对象 SHA256 = 83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75，字节数 = 15723

### 5.2 覆盖率结论

**回验覆盖率 1/18 → 9/18**（任务书背景口径；机读实数口径 = 采到 1/19 → 9/19、现盘重算成功 0/19 → 9/19，MATCH 9 / MISMATCH 0）。problems 24→23（只减不增，唯一减少 = regression MD §4.4 自认原版误报的处方性降级）；warnings 18→11；零凭空新增；R11 PASS 6→7。

### 5.3 剩余未覆盖（10 条 F2-d）与原因

#2（L130）/#3（L31）/#5（L5）/#6（L51）/#7（L52）/#8（L53）/#10（L228）/#11（L229）/#12（L28）/#13（L29）——绑定行本体即严格无路径格式，**±1 行内确无任何路径**（`_f2v_context.py` 本会话逐条打印可证；L228/L229/L29 的相邻行是另一条绑定行，属防误绑排除而非漏采）。被核对象（母本 5178…/候选 ca23…/cb4f…、n1 复核件 3343… 等）或全文未给路径、或在远处表格/其他目录。本补丁**不越行强采、不做全文猜测、不做全仓反查 hash**（误绑风险高且属另一机制），按任务书要求如实记「采不到」：保留原版 R3-3b 警告，不跳过、不放松。附带事实（本会话 hashlib 实算）：L130 声明 3343cfbe…/26435 ≠ lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md 现盘实测 **746b66d4…/28384**，其对象无法从文档上下文辨识——需人工锚定，非本补丁职责范围。

### 5.4 未改任何文件声明

本任务（修补轮 + 复核轮 + 本交付轮）未修改、追加、覆盖任何写域之外文件；`_g7_predicates.py` 与 `lead/gate_r9r12_20261109/` 全部件在修补轮开场/收尾两次、本交付轮开场/收尾两次共四轮 hashlib 实算中指纹全部 UNCHANGED（本会话两轮：§2.1 基线与 `_f2w_final.py` 收尾复验，`六保护件全部 UNCHANGED = True`）。30 件语料零漂移以「复跑输出与既有产出件字节级一致 + binding_details 0 漂移断言」间接证实（未逐件独立比对 30 件指纹，见 §5.5）。本交付轮写域新增件：`R11_F2_COVERAGE_FIX.md`（本件）与 4 个 `_f2w_*` 核验脚本（指纹见 `_f2w_final.py` ③ 输出）。未 commit、未 push。

`lead/gate_fp7_20261108/_g7_predicates.py`
被核对象 SHA256 = 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120，字节数 = 11743

`lead/gate_r9r12_20261109/_g9_gate.py`
被核对象 SHA256 = a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6，字节数 = 11623

`lead/gate_r9r12_20261109/_g9_regression_out.json`
被核对象 SHA256 = 7f16da217dba02008546d643bb51c0100d7126939df947ad0c46a4fd478f11d8，字节数 = 123691

`lead/gate_r9r12_20261109/GATE_R9R12_REGRESSION.md`
被核对象 SHA256 = dc222c2409db9a63c1e2cd95b979069a16b5067585bd8a46d7a9d40657fe27c0，字节数 = 37578

`lead/PENDING_DECISIONS.md`
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419

`lead/GOAL_THREE_TARGETS_20261018.md`
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

`lead/r11_f2_fix_20261109/_f2_r11plus.py`
被核对象 SHA256 = 83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75，字节数 = 15723

### 5.5 未验项（本会话未执行，如实登记）

1. **30 件语料逐件独立指纹比对未做**——零漂移结论系间接证实（复跑输出与既有产出件字节级一致 + 脚本内 binding_details 逐条断言 0 漂移），未对 30 件语料逐一 hashlib 比对修补轮前后的指纹。
2. `_f2_context_probe_out.txt`（修补轮现盘探针，44054 B）全文未逐行独立核对；其关键两件（CRITERIA_COMPARE.md、_dB_anchor_recompute_out.txt 邻目录定位）已由本会话 `_f2w_checks.py` ③ 独立复算取代，9 条 match 对象已由复核件 `_f2v_verify9.py` 独立 hashlib 全覆盖（本会话复跑 9/9）。
3. GATE_R9R12_REGRESSION.md 仅实读与本任务直接相关的行（L130/L134-L138/L165-L181/L217-L233），未全文逐节核对。
4. 修补轮与复核轮声称的部分裸 `-c` 内联命令（如编排方六件指纹复验、lead/ 域 scoped 搜索）未逐条重放原样命令行；同目标的核验已由本会话等价脚本（基线指纹、`_f2w_checks.py`）以 `python -I -X utf8` 实跑替代完成。
5. 本报告（本件）自身的 R11 自扫未在写入时点执行（写入后如需 dogfood，须另行实跑并登记，不在本件内预写结果）。
