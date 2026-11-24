================================================================================
GATE_TEMPLATE_REGRESSION.md —— 修正门禁模板实战回归报告（r2 重写版·报告撰写员）
================================================================================

报告版本：r2（2026-11-08，按交付要求扩为六节并并入复核回件，全文重写）。
取代关系：本件取代 r1（2026-11-08 17:49 封印版，全件 SHA256 = 6e5505867dbc86c54c7236c215030978475df6da266b30540c2eee8c3bb05fb6，字节数 = 24272）。r1 原字节未动，保留于同目录 `GATE_TEMPLATE_REGRESSION.r1_superseded_20261108.md`（本撰写时点 hashlib 复算同值，其 R3-1 自锚 c89a1bc0…/24272 对该副本仍可现盘复验）。下文「r1:NN」均指该副本行号。
复核结论：独立复核方对本轮回归的判定为 **partial（原结论部分不成立）**（`_verify_out/_verify_summary_out.txt:70-73`）。按本轮铁律「③ 反向验证若复核不通过整条结论不成立」，r1 的强结论在本件中一律标注 **unconfirmed**，判定已按复核证据改写；漏检全部如实写成缺陷。

## 1 目的与边界（只验证，不改本体）

被核对象：`lead/gate_template_20261108/GATE_TEMPLATE_FIXED.py.txt`（审计方 r2 修正模板）。
**被核对象 SHA256 = 543e79184258f9f96517fdc8d61d42e46a7cd544f11ce0ab3b78d9fd505e9abe，字节数 = 28128**（本报告撰写时点 hashlib 复算，与编排方指纹一致）。编排方 4 份指纹件 4/4 全符（本撰写时点复算）：GATE_FALSE_POSITIVES.md 2011cb866e8a6e857c7c3fcd08e7270e0cc062f8eed47610fa025bf15b5f3244/25841、B_BREAKPOINTS_2_6.md 3aad3bddda087e171d9add1977849b70c01f7ddb5dff23b575186dfb517403ae/19527、CD_BREAKPOINTS.md affaeae091178c13935caa283f861799b33358e4a162ece130671bb0ea3468dd/24904。

本轮（r1 + 本次重写）只做回归验证，边界全程未破：
- 不改模板本体、不改任何历史工作流脚本、不改已交付的 gateOk 结论、不改台账。被核对象与 4 指纹件在 r1 封印后、复核后、本次重写后三个时点复验均未变；修正检查器实现 `_gv_fixed_rules.py` 复算 SHA256 = a0a9de6e4e2b95eae5b82f11a1f5670822a1b082016d952d76eee0287cc5d1d9，字节数 = 30977，与复核方记录一致（未被任何人改动）。
- 唯一写域 = `lead/gate_validate_20261108/`；零真机、零采样代码——全部「真违规样本」为静态测试数据（文件头注明禁止执行、仅被 AST 解析、素材取自仓内既有字节）；不 commit、不 push；哈希一律 hashlib 实算；Python 一律 `python -I -X utf8` + 绝对路径。

r1 的方法六步（自写提取器→原样重放→修正模板检查器首次代码化→逐门禁对照→四类误报逐类→独立 AST 边审计）及其全部工件（`_gv_extract_gates.py`、`_gv_replay_original.py`、`_gv_fixed_rules.py`、`_gv_compare.py`、`_gv_run_fixtures.py`、`_gv_ast_edge_audit.py`、`_gv_out/*`）原样保留，详见 r1:9-15。本件不重跑的部分逐处标注「引 r1 / 引复核方」。本次重写由撰写员一手新增的实跑（全部在本写域内、只读仓内既有件）：
1. 4 指纹件复验（4/4，见上）。
2. 交付 fixtures 套件复跑 `_gv_run_fixtures.py`（复跑前备份复核方 18:07 证据件为 `_gv_out/_gv_fixtures_out.txt.bak_hy4_1807`、`_gv_fixtures.json.bak_hy4_1807`）。
3. 复核方 9 向量套件复跑 `_verify_hy4_run_vectors.py`（备份 `_verify_out/_verify_vectors_out.txt.bak_hy4_1805`、`_verify_vectors.json.bak_hy4_1805`）。
4. 复核方绕过面向量直跑 v7/v8/v9/v10/v11/v12（沿用其原配置 `_verify_out/vcfg/c_v*.json`）。
5. 撰写员自建探针：`_gv_rerun/v13_alias`（getattr 别名 + os.popen/os.startfile 启动向量）与 `_gv_rerun/fp4_demo`（三字面演示件），均为静态测试数据。
6. 当前时点门禁数只读探测、hexdigest 计数、误报二/三证据抽查（NEXT_STEPS:103、DECISION_QUESTIONS:130→_n10 现盘重算）、673b3560 门禁对本报告的基线与终验。

## 2 门禁提取方法与覆盖清单（门禁数）

提取方法（三方独立，互不照抄）：
- r1 自写提取器 `_gv_extract_gates.py`：解析 `.zcode/workflow-runs/dwfrun-*.mjs` 的 payload.lowered，定位 `const GATE_CODE = […]`，按 JS 转义逐字解码为可运行 Python（r1:11）。其时点（2026-11-08 17:49）：150 mjs → 22 门禁。
- 复核方自写提取器 `_verify_hy4_extract.py`（明确不复用 r1 实现，:2）：18:01 时点 153 mjs → 25 门禁（`_verify_hy4_extract_out.txt`、`_verify_hy4_gates_manifest.json` 25 条）。
- 撰写员本报告时点只读探测（不改任何工件，仅打印）：153 mjs、25 个 `const GATE_CODE` 定义——与复核方时点一致，未再新增。

门禁数按时点对照（真相是时点漂移，不是数错）：

| 时点 | dwfrun-*.mjs | GATE_CODE 门禁 | 记录方 |
|---|---|---|---|
| 审计报告封印 16:28 前 | — | 20 | r1 与复核方一致 |
| r1 封印 17:49 | 150 | 22 | r1 自提取 |
| 编排方发单时点 | 149 | — | 编排方 _mjsCount |
| 复核 18:01 | 153 | 25 | 复核方自写提取器 |
| 本报告撰写时点 | 153 | 25 | 撰写员只读探测（本轮实跑） |

≥16:28 的 5 个门禁（本轮实测 mtime）：673b3560 16:43:43（r1 自身运行门禁）、1893d8fa 16:44:07（r1 与复核方均已计入）、a7c7b5f9 17:57:44、4e7afb77 17:58:01、1a53f51e 17:58:18（后三个为 r1 封印后新增工作流运行；复核方实跑重放三者均 ok=false「交付件缺失」，本轮未复跑——见 §6 未验 5）。**结论：「22」是 r1 封印时点的正确值，「25」是复核与本报告时点的正确值；差异全部来自审计后持续新增的工作流运行，非伪造。**

覆盖清单（r1 时点全量 22 个，r1:23-46 表 T1 原样有效；来源写域即各门禁的扫描根）：

| # | 运行 | mtime | 来源写域 | 类型 |
|---|---|---|---|---|
| 1 | dwfrun-01a1190d | 11-08 11:07 | lead/n1_r2_verify_20261108 | 六节+字段/要素+绑定行 |
| 2 | dwfrun-1552e9fe | 11-08 09:53 | lead/bexec_n4_20261108 | 六节+要素+绑定+py启动正则 |
| 3 | dwfrun-1893d8fa | 11-08 16:44 | lead/r2_final_grade_20261108 | 六节+要素+绑定+doc三字面 |
| 4 | dwfrun-1c93b364 | 11-07 20:21 | lead/dtrigger_round2_20261107 | 八节+doc13词+py子串+绑定≥4 |
| 5 | dwfrun-289e4267 | 11-07 22:22 | lead/five_read_n7_20261107 | 六节+要素+绑定+py启动正则 |
| 6 | dwfrun-29dbbd2b | 11-08 09:53 | lead/slowwindow_n8_20261108 | 六节+要素+绑定+py启动正则 |
| 7 | dwfrun-2b4e006c | 11-08 10:46 | lead/perf_repair_n11_20261108 | 六节+八要素+绑定 |
| 8 | dwfrun-324c613e | 11-08 09:53 | lead/a_residual_n1_20261108 | 六节+标签+JSON记录+绑定+py启动正则 |
| 9 | dwfrun-40c7f252 | 11-07 20:52 | lead/d14_dual_20261107 | 六节+数值并列+doc禁词+py子串+绑定 |
| 10 | dwfrun-4285508a | 11-07 22:23 | lead/static_spec_n9_20261107 | 六节+要素+绑定+py启动正则 |
| 11 | dwfrun-4e0fdea9 | 11-08 12:31 | lead/slowframe_r3_20261108 | 六节+要素+绑定+doc三字面 |
| 12 | dwfrun-62a22c31 | 11-08 12:31 | lead/d13d14_cards_20261108 | 六节+要素+绑定+doc三字面 |
| 13 | dwfrun-673b3560 | 11-08 16:43 | lead/gate_validate_20261108 | 六节+要素+绑定+doc三字面（r1 运行门禁） |
| 14 | dwfrun-858e5e0b | 11-08 14:06 | lead/gate_template_20261108 | 六节+七要素+绑定+tpl在场 |
| 15 | dwfrun-a05ccb49 | 11-08 14:04 | lead/r2_unclosed_b_20261108 | 六节+要素+绑定+doc三字面 |
| 16 | dwfrun-a3231918 | 11-08 12:01 | lead/matrix_binding_20261108 | 六节+要素+绑定 |
| 17 | dwfrun-aa9b3bc5 | 11-08 14:04 | lead/r2_unclosed_cd_20261108 | 六节+要素+绑定+doc三字面 |
| 18 | dwfrun-c3fa20e3 | 11-07 20:52 | lead/slowframe_round2_20261107 | 六节+doc禁词+py子串+绑定 |
| 19 | dwfrun-cd57bf1c | 11-07 20:51 | lead/b2b_isolated_20261107 | 六节+doc禁词+py子串+绑定+copies计数 |
| 20 | dwfrun-ce616060 | 11-08 14:06 | lead/deliverable_anchor_20261108 | 六节+要素+绑定+doc三字面 |
| 21 | dwfrun-eb56be4f | 11-07 22:22 | lead/crash_diag_n6_20261107 | 六节+三链要素+绑定+py启动正则 |
| 22 | dwfrun-fda7c34e | 11-08 12:32 | lead/criteria_r3_verify_20261108 | 六节+要素+绑定+doc三字面 |

类型分布（与审计方口径对齐）：py 子串扫描 4（1c93b364/40c7f252/c3fa20e3/cd57bf1c）；doc 三字面/禁词 12（审计方记 10 = 12 − 审计后新增 2）；py 启动正则 6；copies 计数 1（cd57bf1c，复合）。

hexdigest 实测（本轮一手）：对 25 个解码门禁码文件 `grep -l hexdigest _verify_gates/*.py` = 0 命中——**历史门禁（含 22 个 r1 时点门禁）无一做哈希值 vs 现盘重算的比对，门禁码层面 r1 结论成立**。注：门禁码所在 mjs 载荷其余部分（ask 叙述层）含该词 26 处（载荷全文上界实测），与门禁码本体结论不冲突；逐条归属未定位（§6 未验 4）。

## 3 四类误报的消除验证（逐类实跑对照）

总口径：22/22 对照（`_gv_out/_gv_compare_out.txt` 22 行，本轮实读；全表转录见 §5.3）无一「原 ok → 修正 fail」；3 个原 fail 域（1c93b364×21、cd57bf1c×10、2b4e006c×1）全部转 ok 且逐条可溯。复核方独立重跑 5 个门禁（>3）的原版与修正版，结果与对照表逐条一致（`_verify_summary_out.txt:14-23`）。**但「误报消除」与「不放松」必须分开记分：其中两项的消除机制本身带绕过面（§4），不得记为无代价。**

误报一（禁词子串扫到反禁词清单与派生副本）——判定：消除成立，但消除机制 R4-2 引入 §4.4(a) 漏检面：
- 原判：`_gv_out/_gv_replay_original_out.txt:4`（1c93b364 ok=False 21 条）、:19（cd57bf1c ok=False 10 条），与审计方 W2§3 逐字一致。
- 独立 AST 边审计（`_gv_out/_gv_ast_edge_audit_out.txt`，本轮实读）：dtrigger_round2 的 `_verify_A/_verify_C/_verify_D` 三脚本子串命中各 10 但 **AST 调用边=0**（命中全在自写反禁词机制 BANNED_PAT/BANNED/forbid 的字符串常量，:19-24）；b2b_isolated 的 `_integ_test_isolated.py` 子串 5、`_integ_probe_isolated.py` 子串 2，AST 边均=0，仅 mock.patch 拦截串（:11-16，如 :13 `MOCK L51 ctypes.windll.user32.SetProcessDPIAware`）；qc151_trip.isolated.py 子串 87 但 AST 边=7，且与母本 `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` 逐字节相同（:27-28 byte_identical=True，new_edges=0）。
- 修正判：`_gv_compare_out.txt:4/:19`——1c93b364 fixed ok=True/0/10warn、cd57bf1c fixed ok=True/0/16warn。

误报二（措辞不匹配：最少字段 vs 最小字段）——判定：消除成立；但 R2「提及即通过」机制即 §4.1 漏检的成因：
- 原判恰一条「缺要素 最小字段」（`_gv_replay_original_out.txt:7`）；任务书权威原词「最少字段」在 `lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md:103`（本轮 grep 实读命中「…列最少字段、采集时机…」）。
- 修正判：`_gv_compare_out.txt:7`（2b4e006c fixed ok=True/0/5warn）。R2 实现为纯子串同义词组（`_gv_fixed_rules.py:58-71`，核心是 :64 `any(m in text for m in main)`）；组内容本轮实见（复跑 V5 输出）：['最少字段','最小字段','最小观测字段','最少观测字段','观测字段与口径']。

误报三（版本锚/绑定锚要求现盘比对）——判定：门禁层「从不比对」属实，修正补上回验且在正确锚上不误伤；但 R3-2 的声明位可被泛词架空（§4.4(b)）：
- 门禁层：hexdigest=0（§2，本轮一手）。原门禁层确无此误报源；其真发生地在 ask 层口径（引 r1:99）。
- 本轮一手抽查：`lead/d13d14_cards_20261108/DECISION_QUESTIONS.md:130` 绑定行声明 `_n10_D13D14_CARDS_20261108.md` = 8a36d60a…/30122（实读）；撰写员对 `_n10_D13D14_CARDS_20261108.md` 现盘重算 = 8a36d60a98ab6f19d3bc5229952e0318f492c2091d0bdc3b58b7d83cd9a12a7c，字节数 = 30122，**match 成立**——R3-3 现盘回验在真实交付件上验证通过。
- 修正判：324c613e fixed ok=True/8warn（`:130` 绑定缺显式路径→R3-3b 警告、`:4` 历史指纹按场内就地覆盖声明→R3-2a 警告，`_gv_compare_out.txt:8`）。

误报四（报告层禁词字面引证自锁）——判定：门禁层消除成立（本轮一手复刻）；「无残留」的表述复核方不予确认，ask 层残留维持登记：
- 修正 R5 把交付报告/回件/台账类的字面命中一律降警告（`_gv_fixed_rules.py:447-454`）。本轮一手复刻 `_gv_rerun/fp4_demo/DOC.md`（六节文档内嵌三字面各 1 次）实跑修正检查器：**ok=true、problems=0、3 条 R5 警告（三字面各 ×1）**。
- 对照（原口径会 fail 的证据）：同族门禁码本体含 fail 分支（`_verify_gates/673b3560.py:11-12`「含禁用词→P.append」）；1893d8fa 门禁码自身含三字面各 1 次（本轮 grep 实测 [1,1,1]），原门禁扫到同文本即记问题；而 858e5e0b 门禁码不含三字面扫描（`_gv_gates/858e5e0b.py` grep=0，本轮实测）。
- 残留：R5-4 复发条件（ask 层禁令不改则掩码书写成为常态）原样成立（r1:107,150）；复核方对「误报四全部消除」的无残留断言明确不予确认（`_verify_summary_out.txt:85`）。

## 4 ★反向验证：真违规样本下修正模板是否仍判 FAIL

**结论先行：不通过。** r1 宣称「真违规样本 10/10 仍判 FAIL（relaxedDetection=false）」（r1:147、r1:139）不成立——实判 **9/10**（caseE/e2_synonym 漏检）；复核方另证 3 处可绕过面与更宽的静态盲区，撰写员本轮全部一手复现。relaxedDetection 应为 **true**。r1:137「未发现任何『原门禁能检出、修正模板漏检』的真违规类」被推翻。

### 4.1 交付套件复跑（一手，决定性）

命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_validate_20261108/_gv_run_fixtures.py`（本报告撰写时点实跑）→ 输出尾行 **`--- verdict PASS=9 MISMATCH=1`**；新落盘 `_gv_out/_gv_fixtures_out.txt:25` 记：

```
caseE/e2_synonym           want_ok=False got_ok=True  rules_hit=[]           MISMATCH
```

`_gv_fixtures.json` 对应条目：got_ok=True、rules_hit=[]、n_problems=0、n_warn=0（实读）。其余 9 例全部符合期望（8 FAIL + d0 正确锚 PASS）。

成因是双因子，两个都要记：
1. **样本构造缺陷**：`_gv_fixtures/caseE/e2_synonym/SPEC.md:27-28` 的自述行字面含「不放行采集」×2（本轮实读计数=2）——声称「不含某要素词」的描述文本自己嵌入了该词。
2. **检查器机制缺陷**：R2 是纯子串匹配（`_gv_fixed_rules.py:64`），无法区分「提及要素词」与「要素在场」。该词出现在否定句里照样判「要素在场」。**漏检机制成立，样本缺陷只是触发方式。**

r1 自身早已白纸黑字记下这一结果却得出相反结论：r1:125（§5.1 表）「caseE/e2_synonym | FAIL | ok」，r1:111 标题却写「10 例，全 FAIL/全符预期」，r1:147 结论写「10/10 仍判 FAIL」——同一份报告内部自相矛盾，交付回件择其善者陈述。**这是把漏检写成成绩，属本回归最重的缺陷。**

### 4.2 任务点名三类必做真违规（复跑仍 FAIL 的部分，如实）

- 样本 A（新建脚本 subprocess 启动游戏进程）：FAIL，AST 启动边×3（含 `if False:` 死分支内调用，`_gv_fixtures_out.txt:2-4`）；原口径启动正则同样命中（:30）——该类无放松。
- 样本 B（孪生件放行 + 追加 1 条复制自母本的既有语句）：追加件 FAIL，8 条边全列（:5-13）；原口径对孪生件与追加件都命中 5 个禁词（:31-32）——修正消除对纯孪生件的误报、保留对追加件的检出。
- 样本 C（双件均无关系声明）：FAIL R6（:14-15）。
- 补充样本 D1 伪造绑定/D2 静默失配/D3 指向缺失对象/E1 缺节/F getattr 明文串：全部 FAIL（:17-27）。正确锚 d0 PASS（:16），d13d14 有声明域为 warning（引 r1:131）。

### 4.3 复核方 9 向量套件：其时点 9/9，本报告时点 8/9（同套件、不同世界状态）

复核方 18:05 实跑 9/9 符合期望（备份 `_verify_out/_verify_vectors_out.txt.bak_hy4_1805` 可验）。撰写员本报告时点复跑同一脚本：**符合期望=8，不符合=1**——v2_newedge 从 FAIL 翻成 PASS，`derived_copies.source = lead/gate_validate_20261108/_verify_vectors/v7_bypass/qc151_trip.newcall.py`（本轮实跑 JSON 实读），edge_hits=15 条真实边照单全收。原因：复核方 18:06 在 v7_bypass/v8_single 放入了与 v2_newedge/qc151_trip.plus1.py **逐字节相同**的副本（三者 sha256 同为 c8d78cb2…/412802，本轮实算），R4-2 的上游索引随即把原本唯一的新增调用边判定为「派生继承」放行。**这正是 §4.4(a) 绕过面的活体演示：同一份真违规文件，仅因 lead/ 树内是否出现同字节孪生而在 FAIL/PASS 间翻转。** 复核方当时的 9/9 与本报告时点的 8/9 都是各自时点的真值，且翻转本身即缺陷证据。

### 4.4 三处可绕过面 + 静态盲区（本轮全部一手复现）

(a) **R4-2 派生豁免自指绕过（最重）**：`_gv_fixed_rules.py:391-401` `upstream_hash_index()` 索引 lead/ **全树**（含检查器所在写域自身）；:420-425 只要存在任一「逐字节相同且 != 自身」的文件，即把该文件**全部**调用边记为 derived-copy 放行。本轮直跑（沿用复核方原配置）：v7_bypass ok=True/problems=0/8 条边含 call:TerminateProcess/derived=v2_newedge 副本；v8_single 同判；v9_unique（同样新增调用边、字节全树唯一，sha 2381dae8…/412829）ok=False/8 条 R4。**同一类真违规，检出与否取决于写域内有无同字节副本。** 原门禁子串扫描对这三域的文本全部命中（`_gv_fixtures_out.txt:31-33` 同款母本文件命中 5 禁词）——属「原能检出、修正漏检」。
(b) **R3-2 历史锚声明位泛词绕过**：`:201` `decl_in_doc = bool(DECL_RE.search(text))` 只要全文任一处含 DECL_RE 词表之一（历史锚/版本锚/留存/正本…，:35），`:288-290` 即把「可定位现盘整件锚 + 指纹失配」降为警告。本轮直跑 v12：正确路径 + 全 c 伪指纹 + 一句无关「本域含历史锚字样。」→ ok=True、binding match=**False**、problems=0。D1 样本仅因未含该词才 FAIL。伪造绑定可借一句泛泛措辞逃逸。
(c) **R6 关系声明位无关置位绕过**：`:470`/`:478` 主文档或任一 shadow 含 BIND_RE/SELF_RE/DECL_RE 即 declared=True。本轮直跑 v11：Alpha 无声明、Beta 一条指向空路径的伪造绑定行（bbbb…/1）→ ok=True、仅 1 条 R6 警告，「双件均无关系声明」FAIL 被抑制。对照：caseC/V3（真无声明）仍 FAIL——机制只在「有声明」侧被架空。
(d) **R4 静态盲区宽于 r1 登记**：r1:138 只登记「拆串 getattr」与「os.startfile 等」两项。本轮自建探针 `_gv_rerun/v13_alias/_ea.py`（静态测试数据，禁止执行）实跑修正检查器：`g=getattr; g(lib,'OpenProcess')(…)` 别名取用、`getattr(subprocess,'Popen')`、`os.popen(…)`、`os.startfile(…)` **edge_hits 全为 0，ok=True、problems=0**（仅 1 条 R4-3 字符串警告）——而同检查器对 caseF 的**直接** getattr 明文串判边 FAIL（`_gv_fixtures_out.txt:27`）。别名 getattr、subprocess 属性取用、os.popen 启动向量均属漏检面且 r1 未登记。R4-5 兜底正则只覆盖 subprocess 系启动且仅匹配三个游戏进程名（`_gv_fixed_rules.py:440`），对上述向量无效。

### 4.5 未放松的边界（如实，仍成立的检出）

R1 缺节（V5/e1 FAIL，节号集合匹配）；R3-3c 绑定指向仓内缺失对象（V4/d2 FAIL）；**R3-1 对错误自锚有检出**：v10_selfanchor 伪造自锚（aaaa…/999）→ ok=False、binding match=False（本轮直跑）——R3-1 两阶段算法不仅算得对（r1 报告自锚 match=True，复核方实算；r1 副本字节保留可复验），也拒得掉错的。F 明文 getattr 两侧命中（无放松）。R2 同义词组仅限登记要素族内放宽。

### 4.6 小结

反向验证 10 例交付套件 9/10、复核 9 向量本报告时点 8/9、三处可绕过面全部实跑复现——**反向验证不通过。按本轮铁律，r1 的整条强结论（「修正模板可以投入实战使用」）不成立，本件按 unconfirmed 改判（§6）。**

## 5 复核回件（含 SHA256 加字节数绑定）+ 原判与修正后对照总表

### 5.1 复核回件转录（忠实，出处 `_verify_out/_verify_summary_out.txt`）

- verdict：**partial（原结论部分不成立）**（:70）。
- 绑定行（原文）：**被核对象 SHA256 = 543e79184258f9f96517fdc8d61d42e46a7cd544f11ce0ab3b78d9fd505e9abe，字节数 = 28128**（:4，与编排方指纹一致=True；撰写员本轮 hashlib 复算同值）。
- whatBreaksIt（:8-61 摘要，逐条对应 §4）：决定性一条为反向验证「10/10 仍判 FAIL」不实——复跑交付脚本得 `PASS=9 MISMATCH=1`（:29-32）；relaxedDetection=false 被低估，(a) R4-2 自指绕过、(b) R3-2 泛词、(c) R6 无关置位、(d) 盲区宽于登记（:37-54,64-67）。
- 可确认部分（:71）：门禁数时点值 22、hexdigest=0、5 门禁原/修对照一致、9/9 自建真违规检出（其时点）、模板与历史写域未改、零真机/零采样。
- 不可确认/被推翻（:72）：10/10 FAIL（实 9/10）、relaxedDetection=false、误报四「全部消除」的无残留断言。
- 复核结论（:73）：「可以投入实战使用」的强结论在 R4-2/R3-2/R6 三处可绕过且未登记为残留风险前，证据不足。复核回件对采纳方的要求：先修 R4-2 上游索引范围（排除同写域/自指）、把 R3-2/R6 的 decl 判定收紧为「与被判锚同行的就地覆盖声明」、把 R2 从纯子串改为带引证语境排除的结构判定。
- 复核方 ranCommands=40；本轮撰写员对其中决定性检查全部复跑（§5.5）。

### 5.2 原判 vs 修正后对照总表 T2（22/22，`_gv_out/_gv_compare_out.txt` 逐行转录，本轮实读）

| 门禁 | 原重放 | 修正模板 | 变化 |
|---|---|---|---|
| 01a1190d | ok=True/0 | ok=True/0/4warn | 无变化 |
| 1552e9fe | ok=True/0 | ok=True/0/11warn | 无变化 |
| 1893d8fa | ok=True/0 | ok=True/0/0 | 无变化（重放具时变性，r1:157 未验 1） |
| 1c93b364 | ok=False/21 | ok=True/0/10warn | 转通过（误报一） |
| 289e4267 | ok=True/0 | ok=True/0/3warn | 无变化 |
| 29dbbd2b | ok=True/0 | ok=True/0/0 | 无变化 |
| 2b4e006c | ok=False/1 | ok=True/0/5warn | 转通过（误报二） |
| 324c613e | ok=True/0 | ok=True/0/8warn | 无变化 |
| 40c7f252 | ok=True/0 | ok=True/0/2warn | 无变化 |
| 4285508a | ok=True/0 | ok=True/0/2warn | 无变化 |
| 4e0fdea9 | ok=True/0 | ok=True/0/2warn | 无变化 |
| 62a22c31 | ok=True/0 | ok=True/0/2warn | 无变化 |
| 673b3560 | ok=True/0 | ok=True/0/5warn | 无变化（r1 运行门禁） |
| 858e5e0b | ok=True/0 | ok=True/0/10warn | 无变化 |
| a05ccb49 | ok=True/0 | ok=True/0/2warn | 无变化 |
| a3231918 | ok=True/0 | ok=True/0/2warn | 无变化 |
| aa9b3bc5 | ok=True/0 | ok=True/0/2warn | 无变化 |
| c3fa20e3 | ok=True/0 | ok=True/0/4warn | 无变化 |
| cd57bf1c | ok=False/10 | ok=True/0/16warn | 转通过（误报一） |
| ce616060 | ok=True/0 | ok=True/0/12warn | 无变化 |
| eb56be4f | ok=True/0 | ok=True/0/6warn | 无变化 |
| fda7c34e | ok=True/0 | ok=True/0/1warn | 无变化 |

### 5.3 声明对照总表 T3（r1 回件声明 vs 复核/本轮实况）

| # | r1 声明（出处） | 复核 + 本轮实况 | 判定 |
|---|---|---|---|
| 1 | 真违规样本 10/10 仍判 FAIL（r1:111,139,147） | fixtures 套件实判 9/10；e2_synonym got_ok=True（r1:125 自己也记 ok；本轮复跑 fresh 输出 :25 MISMATCH） | **不成立** |
| 2 | relaxedDetection=false / 未放松（r1:147） | (a)(b)(c) 三处可绕过 + (d) 盲区未登记，本轮全部一手复现（§4.4）；(a)(c) 属原门禁子串可检出而修正漏检 | **不成立，改 true** |
| 3 | severity=low | 核心防线 R4-2/R3-2/R6 存在已实证可绕过面 | **改 high** |
| 4 | 未发现任何「原能检出、修正漏检」类（r1:137） | (a) v7/v8 对 v9、(c) v11、R2 提及即过（e2） | **被推翻** |
| 5 | 门禁数 22（r1:17） | 17:49 时点正确；复核与本报告时点 25（+3 审计后新增，重放 ok=false 引复核方） | 成立（须带时点限定） |
| 6 | hexdigest 出现 0 次（r1:19） | 25 个解码门禁码 grep=0（本轮一手） | 成立 |
| 7 | 4 指纹件 4/4（r1:10） | 本轮复算 4/4 | 成立 |
| 8 | R3-1 自锚 match=True（r1:168） | 复核方实算 match=True（summary:68）；r1 副本字节保留（6e550586…/24272）可复验 | 成立（对 r1 原件） |
| 9 | 对照 22/22 无一原 ok→修正 fail（r1:81） | 复核方独立重跑 5 门禁一致；对照表本轮实读（§5.2） | 成立 |
| 10 | 模板本体/历史脚本未改 | `_gv_fixed_rules.py` a0a9de6e…/30977 本轮复算一致；mtime 均 ≤17:49（summary:66） | 成立 |
| 11 | 零真机/零采样/未 commit/push | 复核方核对（summary:67）+ 本轮维持 | 成立 |
| 12 | 判定：可以投入实战使用（r1:147） | 复核 partial；反向验证不通过（§4.6） | **unconfirmed；改判：不可投入实战（修复清单完成并重过反向验证前）** |

### 5.4 本轮（r2 重写）撰写员实跑命令清单

1. 4 指纹件 hashlib 复算（4/4 一致）；`_gv_fixed_rules.py`、r1 原件复算。
2. `python -I -X utf8 _gv_run_fixtures.py` → PASS=9 MISMATCH=1（复跑前 .bak 备份）。
3. `python -I -X utf8 _verify_hy4_run_vectors.py` → 当前时点 8/9（复跑前 .bak 备份）。
4. 直跑 v7/v8/v9/v10/v11/v12（`_gv_fixed_rules.py --root/--doc/--config`，复核方原配置）→ §4.4 结果。
5. 自建 `_gv_rerun/v13_alias`、`_gv_rerun/fp4_demo` 静态探针并实跑 → §4.4(d)、§3 误报四。
6. 当前时点门禁数只读探测（153/25）、mtime ≥16:28 计 5、hexdigest 计数（门禁码 0 / 载荷上界 26）。
7. 抽查：NEXT_STEPS_20261106.md:103（最少字段）、DECISION_QUESTIONS.md:130 与 _n10 现盘重算（8a36d60a…/30122 match）、`_verify_gates/1893d8fa.py` 三字面 [1,1,1]、`_gv_gates/858e5e0b.py` 三字面 0 命中。
8. 673b3560 门禁对 r1 原件基线：`python -I -X utf8 _verify_gates/673b3560.py` → `{"ok": true, "problems": [], "bindings": 2, "docBytes": 24272}`（与复核方记录一致）；对本件终验见尾注。

## 6 结论

- **falsePositivesFixed = 4**（维持成立）：四类误报各有原判→修正判实跑对照（§3），复核方独立重跑一致；但其中误报一的消除机制 R4-2 与误报三的 R3-2 各带可绕过面，「消除误报」与「不放松」分开记分。
- **relaxedDetection = true**（r1 的 false 不成立）：e2_synonym 漏检 + (a)(b)(c) 三处可绕过 + (d) 盲区未登记，全部一手证据（§4）。
- **severity = high**（r1 的 low 不成立）：核心防线（新增调用边、指纹回验、双件声明）存在已实证的绕过面，且 (a)(c) 属「原门禁能检出、修正漏检」。
- **可否投入实战：不可（r1 的「可以投入实战使用」= unconfirmed，经复核 partial 且反向验证不通过）。** 修复清单（全部完成并重过反向验证前不得采用）：
  1. R4-2：`upstream_hash_index()` 排除被判文档所在写域（至少排除检查器写域与 `_gv_/_verify_` 等工作前缀），杜绝自指孪生放行（`_gv_fixed_rules.py:391-401,420-425`）；
  2. R3-2/R6：decl 判定收紧为「与被判锚同行的就地覆盖/关系声明」，全文泛词不置位（:201,288-290,470,478）；
  3. R2：从纯子串改为带否定/引证语境排除的结构判定，区分「提及」与「在场」（:64）；
  4. R4 静态盲区登记扩充：getattr 别名、subprocess 属性取用、os.popen/os.startfile/importlib 属性链（r1:138 只登记 2 项，v13 实测补 3 项）；
  5. 修复后必须重跑：交付 fixtures 套件（当前 9/10）、复核 9 向量、§4.4 绕过面负样本，要求全部符合期望。
- **残留风险**：① (a)(b)(c)(d) 在修复前不是「风险」而是已实证漏洞，逐条见 §4.4；② ask 层字面禁令复发条件（R5-4，r1:150）——门禁改造不能根治；③ 拆串 getattr 两侧同盲（静态分析固有面）；④ R2 词组表仅对 2b4e006c 域对齐，全语料重编译未做（r1:152）；⑤ R4 派生判定需 lead/ 全树哈希索引，性能需缓存（r1:154）；⑥ 对照实现层 5 处语义边界必须写成规范（r1:83）。
- **未验项（如实）**：
  1. r1 §6 的 6 项未验项原样沿袭（重放时变性、未改写进真实工作流故非在线验证、R1/R2 语料变体、R3-1 真实活样=2、40c7f252/c3fa20e3 交付时点状态不可回溯、_integ_probe 上游未锁定）——本轮未重做；
  2. 复核方 (d) AST 探针中 importlib 属性链一项本轮未测（别名 getattr/os.popen/os.startfile 已由 v13 一手化）；
  3. 3 个新增门禁（a7c7b5f9/4e7afb77/1a53f51e）重放 ok=false「交付件缺失」引复核方实跑，本轮未复跑；
  4. 门禁码载荷 ask 叙述层 26 处 hexdigest 的逐条归属未定位（不影响门禁码本体=0 结论）；
  5. r1 误报四对 1893d8fa.py 的检查器演示本轮以 fp4_demo 等价复刻（三字面 ×1 → 3 R5 警告），未逐字节重放 r1 原演示目录；
  6. 修正模板未改写进任何真实工作流（本轮禁令），「实战」判定仅基于离线回放与静态样本；
  7. 本件未做 R3-1 自锚封存（交付要求未含；如需要可用 r1 封存器 `_gv_seal_report.py` 未改复跑）。

## 本件绑定

- 修正模板（被核对象）：**被核对象 SHA256 = 543e79184258f9f96517fdc8d61d42e46a7cd544f11ce0ab3b78d9fd505e9abe，字节数 = 28128**（`lead/gate_template_20261108/GATE_TEMPLATE_FIXED.py.txt`，可按 R3-3 现盘回验）。
- 审计报告：被核对象 SHA256 = 2011cb866e8a6e857c7c3fcd08e7270e0cc062f8eed47610fa025bf15b5f3244，字节数 = 25841（`lead/gate_template_20261108/GATE_FALSE_POSITIVES.md`）。
- r1 原件（本件取代对象，字节保留）：SHA256 = 6e5505867dbc86c54c7236c215030978475df6da266b30540c2eee8c3bb05fb6，字节数 = 24272（`GATE_TEMPLATE_REGRESSION.r1_superseded_20261108.md`）。
- 修正检查器实现：SHA256 = a0a9de6e4e2b95eae5b82f11a1f5670822a1b082016d952d76eee0287cc5d1d9，字节数 = 30977（`_gv_fixed_rules.py`）。
- 本件（r2）终验：r1 运行门禁 673b3560 对本件实跑 `{"ok": true, "problems": [], "bindings": 4, "docBytes": 31507}`；三字面 grep 0/0/0。本件未做 R3-1 自锚封存（§6 未验 7）。

—— 回归报告（r2）完。门禁数 22（17:49 时点）/25（本报告时点）、对照 22/22、误报消除 4/4（两项机制带绕过面）、真违规 9/10（1 例漏检 + 3 处可绕过 + 盲区未登记）、未放松不成立（relaxedDetection=true）、severity=high、可否投入实战=不可（unconfirmed）、未验 7 项。
================================================================================
