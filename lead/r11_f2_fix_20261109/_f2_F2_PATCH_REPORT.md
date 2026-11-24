# F2 覆盖缺口修补报告 —— R11 增强版路径采集（r11_scan_plus）

日期：2026-11-09。写域：lead/r11_f2_fix_20261109/（本任务唯一写域）。
被修补对象：lead/gate_fp7_20261108/_g7_predicates.py 的 r11_scan（:151-224）——**原件零改动**（文末指纹复验），补丁全部落在本写域 `_f2_r11plus.py`。

---

## 0 结论摘要

- **缺口**：原版 r11_scan 只在「被核对象…SHA256 =」分隔段与命中点**之前**的同一行找反引号路径（_g7_predicates.py:184-191）。30 件回归机读实数 = **19 条绑定行，18 条 path=null**（现盘重算成功 0 次），唯一采到的 1 条（`_dB_anchor_recompute_out.txt:18-19`）因行号后缀 is_file 失败被判「不在盘」——GATE_R9R12_REGRESSION.md §4.4 自认的新误报、§4.5 登记的覆盖缺口。
- **修补**：`_f2_r11plus.py` 实现 `r11_scan_plus`，补三类采集（T2 尾括注反引号 / T2N 尾括注明文路径形 / T3 相邻行反引号）+ 行号后缀剥除 + 引文语境降级（仍回验），证据分级保证零凭空 FAIL。
- **实跑（同一份 30 件清单）**：采到路径 **1/19 → 9/19**；现盘重算成功（match=True）**0/19 → 9/19**（9 条全部 MATCH，0 条 MISMATCH）；problems **24 → 23**（唯一变化 = #30 的 R3-3c 按 §4.4/§4.5 处方降级为警告），**零凭空新增**；29/30 件 problems 逐字不变。R11 级与 overall 级 verdict 仅 #30 FAIL→PASS（修的正是 §4.4 已自认的原版误报）。
- **如实登记**：仍有 **10 条绑定行采不到路径**（F2-d，见 §3/§6）——这些行 ±1 行内确无路径（其绑定行按铁律为无路径严格格式），本补丁不猜测、不越行强采、不放松。
- **计数勘误（沿 regression MD §4.5 L181）**：任务书背景「18 条绑定行中 17 条 null」系实装回件旧文字；机读件与本轮复现均为 **19 条 / 18 条 null / 1 条采到**。本任务 ask 内嵌的编排方提取 JSON（`{"count":0}`）为提取失败空结果，不作为计数依据；本轮回现与 `_g9_regression_out.json` binding_details **逐条一致（0 漂移）**。

## 1 第一步：缺口复现（实跑）

命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/r11_f2_fix_20261109/_f2_repro.py`
- 加载 `_g7_predicates.py` 前验指纹（02c17e49…c51120 / 11743 B，通过）；
- 对 `_g9_regression_out.json` results_30 的 30 件重跑原版 `r11_scan`：**绑定行 19 条、path=null 18 条**，与回归 JSON 每条的 declared/path/match **完全一致**（脚本内断言，0 不一致文件）；
- 逐条 dump 绑定行原文（前一行/本行/后一行 + 反引号跨度 + 命中列）→ `_f2_repro_out.json`；
- 补充探针 `_f2_context_probe.py` 实测关键对象现盘指纹（`_f2_context_probe_out.txt`）：8 个候选对象在盘且 hash/字节数与声明全 MATCH；`_dB_anchor_recompute_out.txt`、`CRITERIA_COMPARE.md` 不在被扫文档目录。

## 2 形态核实（19 条逐条）

| # | 文档 | 行 | declared 前 12 | 形态 | 原 path | 新采集 path（tier） | 新回验 |
|--:|---|--:|---|---|---|---|---|
| 1 | a_dim_reduced_20261108/A_REDUCED_FORM.md | 93 | 28cd3794a571 | F2-a（明文 `[…]` 括注） | null | lead/a_dim_reduced_20261108/_ar_out.txt（T2N） | **MATCH** |
| 2 | a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md | 130 | 3343cfbe467d | **F2-d** | null | —（±1 行无路径） | 采不到 |
| 3 | b2b_isolated_20261107/INTEGRATION_REPORT.md | 31 | ca23c116064b | **F2-d**（回件摘要行） | null | — | 采不到 |
| 4 | b2b_isolated_20261107/INTEGRATION_REPORT.md | 147 | ca23c116064b | F2-c（路径在后一行） | null | lead/b2b_isolated_20261107/qc151_trip.isolated.py（T3） | **MATCH** |
| 5 | b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md | 5 | ca23c116064b | **F2-d** | null | — | 采不到 |
| 6 | bexec_n4_20261108/B_EXECUTION_SPEC.md | 51 | 517889c68f03 | **F2-d** | null | — | 采不到 |
| 7 | 同上 | 52 | ca23c116064b | **F2-d** | null | — | 采不到 |
| 8 | 同上 | 53 | cb4f3011a75f | **F2-d** | null | — | 采不到 |
| 9 | 同上 | 227 | cb4f3011a75f | F2-a（尾括注反引号） | null | _n4_SPEC_N4_B2B_MATRIX.md（T2） | **MATCH** |
| 10 | 同上 | 228 | 517889c68f03 | **F2-d**（前行 227 是另一条绑定行，防误绑排除） | null | — | 采不到 |
| 11 | 同上 | 229 | ca23c116064b | **F2-d** | null | — | 采不到 |
| 12 | bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md | 28 | 517889c68f03 | **F2-d** | null | — | 采不到 |
| 13 | 同上 | 29 | ca23c116064b | **F2-d** | null | — | 采不到 |
| 14 | b_unclosed_trace_20261108/B_BREAKPOINT2_TRACE.md | 5 | 3aad3bddda08 | F2-a | null | lead/r2_unclosed_b_20261108/B_BREAKPOINTS_2_6.md（T2） | **MATCH** |
| 15 | 同上 | 6 | 7ce09812f7bd | F2-a | null | lead/r2_final_grade_20261108/R2_FINAL_GRADE.md（T2） | **MATCH** |
| 16 | 同上 | 7 | 4ee6a6b78d80 | F2-a | null | lead/dtrigger_round2_20261107/_verify_B_out.txt（T2） | **MATCH** |
| 17 | 同上 | 8 | 793e06d27845 | F2-a | null | lead/b_unclosed_trace_20261108/_bt_B崩点2_尾串追溯_20261108.md（T2） | **MATCH** |
| 18 | 同上 | 60 | 4a3424050125 | F2-b（原已采到；后缀 `:18-19` + 错锚） | _dB_anchor_recompute_out.txt:18-19 | 同左（T1 原样保留）；同行替代锚 lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md 回验 | **MATCH**（经替代锚） |
| 19 | 同上 | 64 | 793e06d27845 | F2-a（明文括注，照录语境） | null | lead/b_unclosed_trace_20261108/_bt_B崩点2_尾串追溯_20261108.md（T2N） | **MATCH** |

**形态比例（19 条）**：F2-a（路径在同一条命中点之后的同行括注，反引号或明文）= 7 条（36.8%）；F2-b（行号后缀）= 1 条（5.3%，且即原版唯一采到条目、其 R3-3c 系 §4.4 自认误报）；F2-c（路径在相邻行）= 1 条（5.3%）；**F2-d（±1 行内确无路径，采不到）= 10 条（52.6%）**。若只按 18 条 null 条目计：F2-a 7/18=38.9%、F2-c 1/18=5.6%、F2-d 10/18=55.6%。

**F2-b 补充实测**：`_dB_anchor_recompute_out.txt` 现盘在**邻目录** lead/dtrigger_round2_20261107/（scoped 实查）；被扫文档目录（lead/b_unclosed_trace_20261108/）内确无此件。原版解析顺序（doc_dir→root→原样）按锚面语义报「不在盘」并无错——错在把**引文出处指针**当**被核对象锚**（§4.4）。增强版不越目录猜测（防误绑），改由同行替代锚回验成立（CRITERIA_COMPARE.md 实测 sha=4a34…94726、48343 B，与声明逐字一致）。

## 3 第二步：补丁设计（_f2_r11plus.py）

`r11_scan_plus(text, doc_dir, root=None, recompute=None)` —— 契约与原版一致（返回 problems/warnings/bindings；缺绑定行 problem 消息逐字保留；原版能采到的 raw 路径在 raw 存在时行为逐字节等同）。

- **T1 原版语义原样**：分隔段反引号路径 → 命中点前反引号路径（_g7_predicates.py:184-191 逐行同构）；R3-3c/R3-3a 消息原文逐字保留。
- **T2（F2-a 主形态）**：命中点之后同一行的反引号路径（尾括注，窗宽 400 字符）。
- **T2N（F2-a 变体）**：同一命中点之后的同行**明文**路径形 token（正则要求至少一层 `/` 或 `\` 分隔 + 扩展名，如 L93 的 `[lead/…/_ar_out.txt]`、L64 的 `（lead/…/_bt_….md，…）`）；与 T2 跨度重叠者去重。
- **T3（F2-c）**：相邻行（前一行/后一行）反引号路径；**相邻行自身是绑定行则整行排除**（防把别条绑定的对象误绑到本条——沿原版 docstring「限同一行，防止把上一行的无关路径误绑到本行绑定」同一防误绑精神；L228/L229/L29 等正是靠此排除避免误绑 L227 的 `_n4_SPEC…md`）。
- **剥行号后缀（F2-b）**：`:`/`#` + 可选 `L` + 行号（含 `-–~` 范围段）结尾，循环剥至多 6 层（`_x.txt:962/:963/:965` → `_x.txt`）；候选 = [原串, 剥一层, …] 逐一按原版解析顺序（doc_dir→root→原样）试探，**原串优先**——原串存在时行为与原版完全一致。Windows 盘符冒号（`C:\`、`C:\x`）后无数字 ⇒ 正则不匹配 ⇒ 不剥（S1 实测）。
- **引文语境（要求 c）**：绑定行命中点前 24 字符内（同行）出现显式标记（原文照录/照录/引文/转录/本轮实读/内嵌 JSON 传入）→ 该绑定行的 FAIL 级问题降为警告；**回验照跑、事实结果照记**（rec.match/rec.recomputed 照写）。词表从严、只认显式标记，反例见 §5-S3。
- **证据分级（不放松、不凭空 FAIL）**：T1/T2 = 绑定行显式反引号锚，回验 MISMATCH → problem（R3-3a，任务书明示「应只在采到路径且 MISMATCH 时增加」）；T2N/T3 = 弱证据（启发式明文/跨行歧义），MISMATCH 或不在盘 → 一律 warning，绝不 FAIL（原版对这些形态连采集都不做，本补丁只增信息不减信息）；any-match-wins（多候选时任一 sha+字节数全 MATCH 即验证成立，S4 实测防误伤）；T1 不在盘时仍按引文语境要求尝试同行 T2→T2N 替代锚回验并记录 rec.alt。
- **零改动保证**：不 import 修改原件；加载前 hashlib 验指纹（02c17e49…/11743 B），失配即拒绝运行（同 _g9_gate.py:40-52 纪律）；`_g7_predicates.py` 与 gate_r9r12_20261109/ 全部件复验未动（§7）。

## 4 第三步：30 件实跑对比

命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/r11_f2_fix_20261109/_f2_compare.py`（断言：30 件每件绑定行条数与 declared 序列与原版逐一相同；原版采到 path 的条目增强版原样采到——两断言全过，0 漂移）

| 指标 | 原版 r11_scan | 增强版 r11_scan_plus |
|---|---|---|
| 绑定行总数 | 19 | 19（条数/declared 序列逐一相同） |
| 采到路径的绑定行 | 1 | **9** |
| 现盘重算成功 match=True | 0 | **9**（MATCH 9 / MISMATCH 0） |
| problems 合计 | 24 | 23（唯一变化 = #30 R3-3c 引文降级） |
| 凭空新增 problem | — | **0**（S6 逐件清点） |
| 29/30 件 problems | — | 逐字不变 |
| verdict 变化 | — | 仅 #30：R11 FAIL→PASS、overall FAIL→PASS |

逐条表见 §2 右三列（文件/行/原 path/新 path/新是否回验/结果）。9 条 MATCH 的现盘重算值全部与声明 sha+字节数逐字一致（实测值存 `_f2_compare_out.json` binding_details，例如 #4：_ar_out.txt = 28cd…2a72/24614；#30-L60 替代锚：CRITERIA_COMPARE.md = 4a34…94726/48343）。

## 5 第四步：无新误报证明（_f2_selftest.py，24 项全过）

命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/r11_f2_fix_20261109/_f2_selftest.py`（退出码 0；明细 `_f2_selftest_out.json`）

- **(a) 30 件逐件核对（S6）**：增强版 problems 数大于原版的文件 = **0 件**；原 R11-PASS 的 6 件（#4/#7/#20/#21/#28/#29）增强后仍 PASS 且逐条获得回验 MATCH；原 FAIL 件（缺绑定行 23 件 + #30）中 29 件 problems 逐字不变，#30 减少 1 条 R3-3c（§4.4 自认误报的处方性修复，非放松——该绑定行声明 hash 经同行替代锚实算逐字吻合）。
- **(b) 剥后缀与 Windows 冒号（S1/S2）**：`C:\`、`C:\x` 不剥；`C:\Users\a\f.md:18-19`→`C:\Users\a\f.md`；`:L18-L19`、`#L18`、`:18`、`:962/:963/:965` 全部正确剥除；`plain.md` 不动。F2-b 正例：真实在盘文件 + `:10-20` 后缀 → 原版误报 R3-3c（假阳性），增强版剥后缀回验 MATCH（**修原版假阳性**，非放松）。
- **(c) 引文语境反例（S3）**：真违规（在盘文件+错误 hash）无标记 → 仍 FAIL（R3-3a）；对抗性伪标记 `引：`、`引用锚已修复：`、`引述待核：` → 仍 FAIL（白名单外不降级）；标记距命中点 >24 字符 → 仍 FAIL；标记仅在前一行 → 仍 FAIL（同行规则）；显式「原文照录」→ 降级为警告且 rec.match=False 照记。**结论：只有绑定行自身以显式照录/引文/实读标记声明「此为转引」时才降级，真违规无法借词表外措辞逃逸。**
- **(d) any-match-wins（S4）**：同行两锚一失配一匹配 → 验证成立、零 problem（防多候选误伤）。
- **(e) 原版行为保留（S5）**：raw 可解析路径两版同 MATCH；raw 不可解析时 R3-3c 消息逐字一致；缺绑定行消息逐字一致。

## 6 第五步：剩余未覆盖的如实清单（10 条 F2-d）

#2/#3/#5/#6/#7/#8/#10/#11/#12/#13 —— 这些绑定行本体即「被核对象 SHA256 = hex，字节数 = N」严格无路径格式，**±1 行内确无任何路径**；被核对象（母本 5178…/候选 ca23…、n1 复核件 3343… 等）或全文未给路径，或在远处表格/其他目录。本补丁**不越行强采、不做全文猜测、不做全仓反查 hash**（那属另一机制且误绑风险高），按任务书要求如实记「采不到」：仍保留原版 R3-3b 警告（需人工锚定）。附带事实（不影响判定）：L130 声明 3343cfbe…/26435 ≠ lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md 实测 746b66d4…/28384，其对象无法从文档上下文辨识。

## 7 保护件复验与绑定行

本轮前后两次实算（开场与收尾）受保护件指纹全部一致，未发生任何修改、追加、覆盖：

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

本任务写域产出件：

`lead/r11_f2_fix_20261109/_f2_r11plus.py`
被核对象 SHA256 = 83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75，字节数 = 15723

`lead/r11_f2_fix_20261109/_f2_repro.py`
被核对象 SHA256 = 4d2b49816367769a4f5975f902d97dc206ce1a5ff82b8ee55c63bccf2d907233，字节数 = 4824

`lead/r11_f2_fix_20261109/_f2_context_probe.py`
被核对象 SHA256 = 82974e6374303c743f19bf81fbac2d2a77fa2a1adf1e22f4253312468a52e6aa，字节数 = 3826

`lead/r11_f2_fix_20261109/_f2_compare.py`
被核对象 SHA256 = 12e55acf42441aca846986a2447abffef77d774ee694cedf56a012c1c8907106，字节数 = 4821

`lead/r11_f2_fix_20261109/_f2_selftest.py`
被核对象 SHA256 = 625704697e412c30a278c616cf8be594b8b870a2734df2219aa0607aa74a19bd，字节数 = 8579

`lead/r11_f2_fix_20261109/_f2_repro_out.json`
被核对象 SHA256 = 3bc0ed8b26f90e235888ed1c386ee0f3179cdcc54bf9092b6ca167dda2ecfa72，字节数 = 28386

`lead/r11_f2_fix_20261109/_f2_context_probe_out.txt`
被核对象 SHA256 = e48e15469c28508303c4eb2c733e44d0129191107a5700a7beeed36e7cc89580，字节数 = 44054

`lead/r11_f2_fix_20261109/_f2_compare_out.json`
被核对象 SHA256 = 148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1，字节数 = 44958

`lead/r11_f2_fix_20261109/_f2_selftest_out.json`
被核对象 SHA256 = 77fa7564b4d15e16092969450561097ca5354ad6c268945a09fdc6743eb058af，字节数 = 4423

## 8 实跑命令清单（本轮全部实跑）

1. `python -I -X utf8 -c`（编排方 6 件指纹复验，开场）
2. `python -I -X utf8 -c`（_g9_regression_out.json 结构探查）
3. `python -I -X utf8 -c`（30 件清单 + 原版 binding_details 提取）
4. `python -I -X utf8 _f2_repro.py`（缺口复现 + 语境 dump）
5. `python -I -X utf8 _f2_context_probe.py`（现盘指纹 + 上下文探针）
6. `python -I -X utf8 -c`（#30 谓词判定 + regression MD F2 条目提取）
7. `python -I -X utf8 _f2_compare.py`（30 件原版 vs 增强版对比，修后复跑一次）
8. `python -I -X utf8 _f2_selftest.py`（24 项自检；剥后缀修 bug 后复跑，24/24 PASS）
9. `python -I -X utf8 -c`（L60/L64 binding detail 复核）
10. `python -I -X utf8 -c`（lead/ 域 scoped 搜索两件「不在盘」对象实际位置）
11. `python -I -X utf8 -c`（交付件+保护件指纹收尾复验）
12. `python -I -X utf8 -c`（本报告 R11 自扫，结果见 §9 补记）

零真机、零采样代码、未 commit、未 push、未改动任何写域之外文件。

## 9 补记：本报告自扫（dogfood，实跑）

对本报告（`_f2_F2_PATCH_REPORT.md`）以同参数直调两版谓词：

- 原版 `r11_scan`：bindings=15（§7 全部绑定行），problems=0，warnings=15（15 条全部「缺显式路径需人工锚定」），现盘重算 0 次——F2 缺口在本件上的现场复现；
- 增强版 `r11_scan_plus`：bindings=15，problems=0，**warnings=0**，**15/15 全部经 T3（相邻行路径）现盘重算 MATCH**（含本写域 9 件与保护件 6 件）。

即：本报告的绑定行采用「路径行在前、严格格式绑定行在后」的写法，恰好全部落在 F2-c 形态——原版一条都验不了，增强版一条不漏全验，且零新增 problem。
