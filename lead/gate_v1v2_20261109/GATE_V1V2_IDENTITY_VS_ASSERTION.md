# GATE_V1V2_IDENTITY_VS_ASSERTION.md — V1（身份陈述）/ V2（完成断言）分界件

- 日期 2026-11-09；唯一写域 = `lead/gate_v1v2_20261109/`；本件 = 该写域内 `GATE_V1V2_IDENTITY_VS_ASSERTION.md`。
- 撰写身份：分界件撰写员。本件逐条给 7 处判定的结论与依据，写判据、样本集、适用边界；**判不了就写判不了**。
- 复核 verdict = **partial**（编排方【复核】字段 `"verdict":"partial"`，ranCommands = 11）⇒ 按交付要求标 **unconfirmed**；若 verdict 为 refuted 亦同样标 unconfirmed。复核确认面与破坏面都如实转录，见 §6。
- 严重度：medium（编排方【设计】`severity`）——R10 在这两域 problems = 7/7 全为误报、会使两件合法交付件被判 FAIL，属需修正的门禁分类缺陷；但无真 V2 完成断言逃逸、无数据被改，故不升 high。

---

## 1 目的与边界

### 1.1 目的

把 **V1 身份陈述**（规定式 / 疑问式 / 否定式 / 引述式 / 表格单元格 / 完成词做定语 / 条件选言分支里的「已填」类字样——它们描述「要核什么、字段叫什么、什么条件下怎么处置」，不是宣称某动作已完成）与 **V2 完成断言**（「三值现已填并已交付」「登记件已落盘」这类宣称动作已闭合的句子）分开，解决生产门禁 R10 把前者一律当越权断言的 **R10 误报** 缺陷。

本件**不改交付件、不改历史 payload**：两域主件、`_g7_predicates.py`、`_g9_gate.py`、`.zcode/workflow-runs/` 全部 mjs、两件台账一律绝对只读。分界件本身只落在唯一写域。

### 1.2 铁律（来自任务书，逐条遵守）

1. 零真机：本轮未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存。
2. 零采样代码：未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入，未写动态内存解析。
3. 绝对只读域：`lead/c07_slot_20261109/`、`lead/c07_truth_protocol_20261109/`、`lead/gate_fp7_20261108/_g7_predicates.py`、`lead/gate_r9r12_20261109/_g9_gate.py`、`lead/gate_doc_name_fix_20261109/`、`.zcode/workflow-runs/` 全部 mjs、两件台账，一律不修改、不追加、不覆盖。
4. 唯一写域 = `lead/gate_v1v2_20261109/`；不 commit、不 push。
5. Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib`。
6. 引用必须追到「实跑命令 + 输出」或「文件:行」；拿不到写「未验」，不补造。
7. 复核回件必须含固定格式绑定行（§6）。
8. **不许为了让门禁通过而放宽判据**：判据必须同时做到「放过 V1 身份陈述」与「抓住 V2 完成断言」，两边都要有样本证明。本件如实记录：原样本集内两边都成立，但分布外新句证明第二边失效（§4.4），故候选判据标 unconfirmed，**不并入生产门禁**（§5.3）。
9. **「判不了」必须如实写**：分不出来的写法就写分不出来，不编一条规则假装能判（§3.5、§5.2）。

### 1.3 适用边界

- 本件只做**单文件静态文本谓词设计 + 逐条判定**，不做运行时校验、不做跨文件状态同步（后者属 R11 / 独立核验轮）。
- 本件不实施判据修复、不把候选判据写进 `_g9_gate.py`；候选判据实装于写域 `_v12_rule.py`，其**可执行性为 unconfirmed**（§4.4、§6）。
- 本轮实跑命令清单与逐字输出见 §2.1、§4、§6；文件:行引用见各节。

---

## 2 上游指纹（九件）+ 两域命中全表

### 2.1 九件上游指纹（本轮独立实算）

实跑命令（本撰写轮，仓库根 `D:\Project\ra2-campaign-forge`）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_v1v2_20261109/_v12w_fpcheck.py > D:/Project/ra2-campaign-forge/lead/gate_v1v2_20261109/_v12w_fpcheck_out.txt 2>&1; echo "EXIT=$?"
```

输出 `EXIT=0`；`_v12w_fpcheck_out.txt:2-11` 逐字：

```
[FP-9] 本轮独立实算九件上游指纹 (hashlib.sha256) / 绝对路径
  lead/c07_slot_20261109/C07_IDENTITY_SLOT.md                      exists=True  sha256=05ecdfca451476bb80d84281068fcd9c59d1364b2247cb5482943de6417781fc bytes=20651 MATCH=True
  lead/c07_truth_protocol_20260909/C07_TRUTH_PROTOCOL.md           exists=False sha256=MISSING bytes=0 MATCH=True
  lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md         exists=True  sha256=5102beae1ecf4952862d4ff1319283df816c53a49bdc81bae38d9709bef974e3 bytes=38232 MATCH=True
  lead/c07_truth_protocol_20261109/_tp_C07_TRUTH_PROTOCOL.md       exists=True  sha256=68395681bbfd6b348a91664ec8c0dfafe1b9aa22a939691d0683414071f96547 bytes=25630 MATCH=True
  lead/gate_fp7_20261108/_g7_predicates.py                         exists=True  sha256=02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120 bytes=11743 MATCH=True
  lead/gate_r9r12_20261109/_g9_gate.py                             exists=True  sha256=a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6 bytes=11623 MATCH=True
  lead/gate_doc_name_fix_20261109/_dn_regate_out.json              exists=True  sha256=0d129e409ca5ab744891abccd85a0c0ca0c164ddea8620de634de5079fa8f096 bytes=22133 MATCH=True
  lead/PENDING_DECISIONS.md                                        exists=True  sha256=3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 bytes=52419 MATCH=True
  lead/GOAL_THREE_TARGETS_20261018.md                              exists=True  sha256=2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede bytes=759518 MATCH=True
[FP-9] ALL_BASELINE_MATCH = True ; count = 9
```

九件基线逐条对齐编排方【编排方指纹】：`ALL_BASELINE_MATCH = True ; count = 9`。其中 `lead/c07_truth_protocol_20260909/C07_TRUTH_PROTOCOL.md` 为清单中 `MISSING`（`exists=False`，`sha256=MISSING`，`bytes=0`），同域实际件是 `lead/c07_truth_protocol_20261109/_tp_C07_TRUTH_PROTOCOL.md`（`sha256=68395681…f96547`，`bytes=25630`）——年份笔误，见 `_v12_probe_out.txt:55-57`；此项不作为任何判据输入。

生产谓词现状（供 §5 并入顺序引用）：`_g7_predicates.py:69-70` 定义 `NEG_RE` / `NEG_WINDOW = 24`；`:78-111` 的 `r10_context` 只做「24 字符回看窗否定词计数 + `「…」` 短引证跨度」两类豁免；`:113-130` 的 `r10_scan` 对每个字面命中一律产 `kind`。`_g9_gate.py:125` 现状直接 `g7.r10_scan(text, forb)`，无 V1/V2 前置层；`:141-152` 的 R12 消费 `r10_context` 的 `dbl` 分类。上述文件本轮只读取，指纹 MATCH=True 证明零改动。

### 2.2 两域命中全表（逐条：行号 / 命中词 / R10 kind / 原句）

禁用词表（编排方【两域命中定位】、`_v12v_r10_out.txt:5,40`）：
- `c07_slot_20261109/`：`已补登 / 已填入 / 已填 / 已代填`；
- `c07_truth_protocol_20261109/`：`已填 / 已代填 / 已提交`。

独立实跑 R10 复算（`_v12v_r10.py`，本轮重跑输出 `_v12w_r10_rerun.txt`）：slot `problems=5 warnings=1 occurrences=6`，truth `problems=2 warnings=1 occurrences=3`，两域 `RAW-VS-R10 … IDENTICAL=True`、`R12-MINE problems=0 double_neg_hits=0`（`_v12v_r10_out.txt:6-8,41-43,61`）。即 **7 条 R10 problem = 5 + 2 条 `assertion`**；另 2 处 `negation` 是 warning，**9 处字面命中 = 6 + 3**。

| # | 域 / 行 | 命中词 | R10 kind | 24 字符窗内否定词 |
|---|---|---|---|---|
| S1 | slot `C07_IDENTITY_SLOT.md:79` | 已填 | assertion | `[]` |
| S2 | slot `:103` | 已填 | assertion | `[]` |
| S3 | slot `:110` | 已填 | assertion | `[]` |
| S4 | slot `:112` | 已填 | assertion | `[]` |
| S5 | slot `:120`（第 1 处，pos 9417） | 已填 | assertion | `[]` |
| S6 | slot `:120`（第 2 处，pos 9456） | 已填 | negation | `['非']`（来自「非 C07 主体」） |
| T1 | truth `C07_TRUTH_SELF_PROOF.md:151` | 已填 | assertion | `[]` |
| T2 | truth `:228` | 已填 | assertion | `[]` |
| T3 | truth `:240` | 已填 | negation | `['无','未']`（来自「无未验残留」） |

R10 kind / 窗内否定词逐处出处：`_v12v_r10_out.txt:17-34`（slot）、`:49-57`（truth）；原句逐字见下（本轮 `_v12w_fpcheck_out.txt:15-24` 全量回算，`[HITS] 两域合计 = 9`）：

```
[L79] **填用流程**：① 复制 `_c7_record_template.json` 到落点名 `ACCEPTANCE_RECORDS_C07.json`；② 仅替换 `<…>` 占位符与定档字段（grade/decision/independentReview/writeDomain）；③ `python -I -X utf8 _c7_selfcheck.py <已填件路径>` 须 GATE PASS exit 0；④ 回件含绑定行（§6.2 格式）。
[L103] 1. 三个身份字段已填、全件无 `<` 占位残留（含容器层）；2. `reviewerSessionId` 是**本会话**运行态 ID，非他件 ID；3. `sourceTaskId` 若只能给计划号 → `unresolved` 已如实登记「正式任务书编号未落实」；4. 9 字段名与顺序 == NEXT:23 实文 == r2 schemaNote；5. `inputHashes` 四件为填时实算（python -I -X utf8 + hashlib）；6. `timestamp` 为填时实生成；7. 填用过程零改动既有件；8. 回件含绑定行（§6.2 格式）；9. `reviewerRole` 与 PERF:151 内部三角色逐字不同（签发方≠被派方）；10. **多处同步**：同一值已在 N-4 任务书签署动作复用（§5.4），只填登记件不满足 NEXT:119。
[L110] ### 5.4 多处同步排查表（哪件/哪行/需什么字段/是否已填）
[L112] | # | 件 | 行 | 需什么字段 | 是否已填 |
[L120-a / L120-b 同一行] | 7 | `a_residual_n1_20261108/ACCEPTANCE_RECORDS.json`（先例件，非 C07 落点） | 7 条 `sourceTaskId` 全 = `N-1`（计划号）；`reviewerSessionId` 已填 | 其自身任务的签发身份（非 C07 主体） | 部分（session 已填、任务号仍计划号——先例与反例） |
[T L151] - 处置：已填 → 见证同为声明、非密码学证明，但其价值在独立性（记账方 ≠ 值的主张方，满足 NEXT:23「验收者与作者不得相同」）与可交叉检索性——伪造从「单方改文本」变成「两方合谋 + 两处可互查痕迹」；未填且缺席声明如实 → 通过档不可达，登记最高 PARTIAL + unresolved「运行标识无独立见证/独立记载」。
[T L228] | G 见证与两处落笔 | 3 | 见证槽已填（见证人≠来源会话≠核验者）；见证缺席处置；两处落笔同值复用 | 代填见证→**拒绝**；N-4 同值复用失败→**拒绝** |
[T L240] | **通过** | A-G 全部可核项 PASS、无未验残留、（G1 见证已填 或 S1 有 ≥1 处先于补登的外部独立记载）、无存疑项 | C07 行政登记完成（Q6 补登动作闭合）；不升格技术结论、不构成 APPROVE_SCOPE 签署或 N-5 放行 |
```

### 2.3 防漏判说明（整文其他完成类字样）

整文子串层面另含 `登记完成`（`C07_IDENTITY_SLOT.md:95` 字段取值语义定义；`C07_TRUTH_SELF_PROOF.md:240` 通过档效力列）与 `已签`（`C07_TRUTH_SELF_PROOF.md:207`「已签｜未签」选言状态槽），逐行出处 `_v12_gate_compare_out.txt:20-23`。三者均非「断言本件已完成」，且不是禁用词命中。本轮重跑 `_v12_gate_compare.py`（`_v12w_gate_rerun.txt`）§G 证明 **9 处命中的分析单元 U 内 `U内V2_OVERRIDE=[]` 9/9 全空**：这些词都不在命中词所在的子句/单元格内。如实记录，不藏。

---

## 3 V1/V2 分界规则

### 3.1 定义

- **V1 身份陈述**：完成词（已填 / 已补登 / 已代填 / 已提交 …）在句中充当**待核条件、字段名/列名、疑问、引述占位、定语、被禁止或被规制的情形名、条件选言分支**，句子的语力是「规定 / 询问 / 枚举 / 拒绝」，不是「宣称某事已完成」。应放过。
- **V2 完成断言**：完成词充当**断言谓语**，句子的语力是「本件/本会话已经把三值填好、已交付、登记闭合」。应抓住。
- **判不了**：机器凭 U / pre / post 给不出确定结构标记时，如实输出「判不了」，走 §3.5 默认取向，不编规则假装能判。

### 3.2 候选四级判据（设计稿；**可执行性 unconfirmed**）

★ 本节如实记录编排方【设计】的候选**可执行判据**文本（实装于写域 `_v12_rule.py:13-20,108-170`），但按【复核】verdict = partial 标 **unconfirmed**：该判据在分布外 9 条新句上被证伪（§4.4），**不得作为可执行门禁判据上线**。记录判据 ≠ 宣称判据可执行。

先切分析单元 U（`_v12_rule.py:78-98`）：表格行取命中所在单元格（`|…|` 之间）；散文取命中所在子句（边界 `。！？；\n`）；`pre` = U 内命中之前，`post` = U 内命中之后。四级顺序不可调换（`_v12_rule.py:13-20`）：

| 级 | 名称 | 判据 | 输出 |
|---|---|---|---|
| S0 | HARD_V1 | 命中落在 H1–H6 任一结构内（§3.3） | V1（无条件放过，`review_flag=False`） |
| S1 | V2_OVERRIDE | U 内含硬性完成宣称词族 `_v12_rule.py:32-38`（现已/已实算/已复算/已交付/已闭合/补登完成/登记闭合/填毕/已填完/已提交完/已填且/已签/已落盘/已入账 等）且未被紧邻否定/禁止管辖 | V2（抓住） |
| S2 | WEAK_V1 | 规定式/清单待核标记（应/须/必须/不得/填用流程/自检清单/规格/校验/复制/替换/编号项 `^\s*\d+\.`）**只认 pre 前缀支配** | V1 |
| S3 | DEFAULT | 以上全不命中 | **V2 + `review_flag=True` + 判不了**，须人工复核或改写为显式规定式 |

### 3.3 逐形态规则（8 形态，任务点名形态全覆盖）

| 形态 | 标记 | 判据（词表见 `_v12_rule.py:45-60`） | 判定 |
|---|---|---|---|
| ① **规定式** | W1 / H5 | pre 前缀含 应/须/必须/不得/填用流程/自检清单/规格/校验/复制/替换，或 U 为编号清单项 | V1。例：`1. 三个身份字段已填、全件无 < 占位残留`（slot:103） |
| ② **疑问式** | H1 | U/pre 含 是否/哪件/需什么/核什么/与否，或 post 含 `?`/`？`；且与表格/问句同单元 | V1。例：`### 5.4 多处同步排查表（…是否已填）`（slot:110）、`| # | … | 是否已填 |`（slot:112） |
| ③ **否定式** | H5 | pre 末 2 字符紧邻否定（`不/未/无/非/勿/没/禁/别`），或 U 剥去 `「…」`/`` `…` `` 引文后含 不得/不许/禁止/严禁/不代填/未代填 | V1。例：`不得视为已填`。（设计口径：不用 24 字符窗计数） |
| ④ **引述式** | H2 | 命中在 `「…」`/`` `…` ``/`<…>` 引证或占位跨度内，或 U/同行含 占位符/示例/样例/先例/反例/负测/合成/原文/逐字/要求「 | V1。例：`<已填件路径>`（slot:79） |
| ⑤ **表格单元格** | H3 | 表格行且 U/同行含 是否已填/需什么字段/核什么/判定条件，或 U 含 未填/部分（/不适用/先例/反例/计划号/非 C07 主体/拒绝/通过/存疑 | V1。例：slot:112 列头、slot:120 先例与反例、truth:228 核什么列、truth:240 判定条件列 |
| ⑥ 完成词做定语 | H4 | `post` 以 `件/路径/字段/值/状态/槽/模板/记录/声明/清单/项/的` 开头，且 U/同行含 `<`/占位/命令/参数/复制/替换/路径/须/按 | V1。例：`<已填件路径>` |
| ⑦ 条件/选言/配对分支 | H6 | U/同行含 `→`/若…则/或/≠/≥/≤/判定条件/处置：/拒绝项，且为表格或含 处置/判定/拒绝/条件/清单 | V1。例：truth:151 `已填 → …；未填 → …`、truth:240 `（G1 见证已填 或 S1 有 ≥1 处…）` |
| ⑧ 硬性完成宣称 | S1 | U 内含 §3.2 S1 词族 | **V2**，除非该 U 同时被 H5 管辖 |

### 3.4 同句混用处理（设计口径 + 实装偏差，如实记）

设计口径（编排方【设计】(c)、`_v12_REPORT.md:149-164`）：① 同一句/同一表格行内每处命中独立分类；② **句子级聚合：任一命中 V2 ⇒ 整句 V2**；③ 单处内部 HARD_V1 与 V2_OVERRIDE 同触时按优先级取一条，但**两标记一并回报**供人工审计。

实装偏差（【复核】§3、本轮 `_v12w_fair_rerun.txt`）：

- 「两标记一并回报」**不实**：对 `现已填三值并过门禁，不得再改值。`，U 内实际含 V2_OVERRIDE 词族 `['现已','已填三值']`，但 `classify_v12` 回报 `override=''`、`hard=['H5_否定禁止管辖']`，`『两标记一并回报』= False`（`_v12v_fair_out.txt:19-23`）。根因 `_v12_rule.py:143-146`：命中 HARD_V1 立即 return，`override` 永远为空。
- 「只用 U/pre/post、不跨单元」**不实**：`_v12_rule.py:127,129,133,137` 在 H2/H3/H4/H6 判定里用了整行 `line`；`_v12v_fair_out.txt:25-32` 行为证据——`三值已填；另附先例件一份供比对。` 的 U = `'三值已填；'`，同行另一子句的「先例」仍触发 `H2_引述占位` ⇒ 判 V1。

故 §3.2–§3.4 的判据文本与其实现并不一致，二者都记为 **unconfirmed**，不得据此宣称门禁已可修好。

### 3.5 默认取向与理由

**默认取向 = fail-closed：判不了 ⇒ 默认 V2 + `review_flag=True` + 人工复核 / 改写为显式规定式（加 须/应/是否/若…则）。**

理由（后果不对称，编排方【设计】(d)）：误拦只产生一条待复核项 / 一次「请改写为显式规定式」的编辑，成本有界可追溯；放过会让真 V2 完成断言进入已验收件，而这两域的全部意义就是「不许代填身份、不许冒充完成」，漏一条即绕过整套身份补登 / 真值自证防线。

★ **但本轮必须如实写两处冲突（【复核】part (3)、本轮 `_v12w_adv_rerun.txt`）**：

1. S0 是「无条件 V1 且 `review_flag=False`」，优先级高于 S3；带禁令词的真 V2 句连兜底都到不了——`现已填三值并过门禁，不得再改值。` 等 5 条应 V2 实得 **V1 / review=False**（`_v12v_adv_out.txt:46-81`）。即默认取向方向自洽、实装上却失效。
2. 7 条 plain-V2 句中 5 条靠 S3 兜底（`_v12v_adv_out.txt:166-174` `[D] … = 5 / 7`），`14/14` 的「抓住」数字掩盖了 S1 覆盖率不足。

因此「判不了就拦」在本实现里**没有兑现**；在本轮文档口径下，凡 §4.4 反证句与 §5.2 边界写法一律写「判不了」，并要求 fail-closed 拦截，**不许为了让门禁通过而放宽判据**——本件不删任何 V2 样本、不放宽任何 V1 放过条件，只把失效事实登记为 unconfirmed。

---

## 4 正负样本集与回归

### 4.1 样本集（V1 ≥ 12 / V2 ≥ 12）

实装于写域 `_v12_verify.py`，输出 `_v12_verify_out.txt:60-176`：

- **V1 正样本 22 条（≥12）**：9 条逐字取自两域真实行文（= 全部 9 处禁用词命中，行号 79/103/110/112/120×2、151/228/240），4 条取真实行骨架并补入命中词（样本 ID 明标 `[改写]`，不冒充逐字），9 条构造（逐形态覆盖 §3.3 的 8 形态）。
- **V2 负样本 14 条（≥12）**：全部构造（两域真实行文中确实没有真 V2），逐条注明「现实中什么样会出现」：来源会话补登完成后的回件自述、核验者复述、台账归档行、越权代填见证后的自述、把门禁 PASS 误写成已完成动作等。
- **混合样本 4 条**：MIX-01 `['V1','V2']→V2`、MIX-02 `['V2']→V2`、MIX-03 `['V1','V2']→V2`、MIX-04 `['V1','V1']→V1`（`_v12_verify_out.txt:171-175`）。

### 4.2 回归实跑（本撰写轮）

命令：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_v1v2_20261109/_v12_verify.py > D:/Project/ra2-campaign-forge/lead/gate_v1v2_20261109/_v12w_verify_rerun.txt 2>&1; echo "EXIT=$?"; grep -E "REGRESSION|\[DOMAIN\]" D:/Project/ra2-campaign-forge/lead/gate_v1v2_20261109/_v12w_verify_rerun.txt
```

逐字输出 `EXIT=0` 且（`_v12w_verify_rerun.txt`；与 `_v12_verify_out.txt:178-189` 一致）：

```
[REGRESSION] V1 22/22 PASS ; V2 14/14 PASS ; MIXED 4/4 PASS
[DOMAIN] c07_slot_20261109 : R10 problems=5 warnings=1 ; 命中 6 处 => V1=6 V2=0 (改判后残留 V2=0)
[DOMAIN] c07_truth_protocol_20261109 : R10 problems=2 warnings=1 ; 命中 3 处 => V1=3 V2=0 (改判后残留 V2=0)
```

两域跑数：**slot V1=6 / V2=0，truth V1=3 / V2=0，合计 V1=9 / V2=0，改判后残留 V2=0**。生产门禁真 import 对照（`_v12_gate_compare.py`，本轮 `_v12w_gate_rerun.txt`；`_v12_gate_compare_out.txt:2-7`）：两域 `verdict=FAIL`，slot `problems=5 exempted=1`，truth `problems=2 exempted=1`，`R12(double_neg_hits=0)`。

### 4.3 MIX-02 复现口径差异（如实记）

`_v12_verify.py:151` 的 `MIXED_SAMPLES` 数组句 = `填用流程规定应按模板核对，但三值已实算已交付。`（token 标 `已填`），而 `:184-187` 的 `run_mixed` 实句 = `填用流程规定应按模板核对，但三值已实算，绑定行已交付。`（token 取 `已交付`）——撰写人自己也不一致。复核方按 `run_mixed` 实句 + `token=已交付` 复现 `PASS`（`_v12v_fair_out.txt:1-5`、本轮 `_v12w_fair_rerun.txt` 的 `[MIX-02] … = PASS`）；按数组复现为 `MIXED 3/4`（`_v12v_adv_out.txt:144-150`、本轮 `_v12w_adv_rerun.txt` 的 `[REGRESSION-REPRO] … MIXED 3/4`）。两个数字都如实登记，不挑好看的报。

### 4.4 ★ 反证集合：分布外新句证伪「抓住 V2 完成断言」（本件最关键的一段）

命令：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_v1v2_20261109/_v12v_adv.py > D:/Project/ra2-campaign-forge/lead/gate_v1v2_20261109/_v12w_adv_rerun.txt 2>&1; echo "EXIT=$?"; grep -E "MISMATCH|REGRESSION-REPRO|\[D\]|C-TOTAL" D:/Project/ra2-campaign-forge/lead/gate_v1v2_20261109/_v12w_adv_rerun.txt
```

逐字输出 `EXIT=0` 且 9 行 `**MISMATCH**`（`_v12v_adv_out.txt:45-101` 同）。复核方证明 9/9 句确不在撰写人样本集（`_v12v_fair_out.txt:7-17` `[UNSEEN] 9/9 …`，本轮 `_v12w_fair_rerun.txt` 同）。

A3 否定语境判反（应 V2 实得 **V1 / review=False / H5_否定禁止管辖**）：

| 句 | expect | got |
|---|---|---|
| 现已填三值并过门禁，不得再改值。 | V2 | V1 MISMATCH |
| 核验者不得代填，但三值现已填并已交付。 | V2 | V1 MISMATCH |
| 本件三值已填，不代填见证槽。 | V2 | V1 MISMATCH |
| 三值已填毕，不许事后改值。 | V2 | V1 MISMATCH |
| 三值并非不已填，回件照录即可。 | V2 | V1 MISMATCH |

A4 无关行内词漏判（应 V2 实得 **V1 / review=False / H2 或 H6**）：

| 句 | expect | got |
|---|---|---|
| 三值已填，且 reviewerRole 与 PERF:151 内部三角色逐字不同。 | V2 | V1 MISMATCH（H2_引述占位） |
| 三值已填；另附先例件一份供比对。 | V2 | V1 MISMATCH（H2_引述占位） |
| 三值已填，或按判定条件走 PARTIAL 档。 | V2 | V1 MISMATCH（H6_条件选言分支） |
| 三值已填 → 登记闭合，本件留存。 | V2 | V1 MISMATCH（H6_条件选言分支） |

对照正确项：A1 六条纯 V1（疑问/禁止/紧邻否定/占位定语/条件分支/表格列头）全 V1；A2 四条纯 V2 全 V2；A3 的 NT-5/6/7/8、A4 的 LT-3 亦正确（`_v12v_adv_out.txt:4-44,62-77,91-94`）。根因（【复核】whatBreaksIt (2)）：`_v12_rule.py:116,135,143` 把同单元任何无关禁令当管辖、HARD_V1 无条件优先于 V2_OVERRIDE；`:127,129,133,137` 让整行无关词穿透 U。

**结论（不许含糊）**：`22/22、14/14、4/4` 只在撰写人样本集内成立；在 9 条未见过的新句上，「抓住 V2 完成断言」这一边失效（9 处真 V2 被放过且无复核标记）。铁律「两边都要有样本证明」的**第二边不通过** ⇒ 候选判据 **unconfirmed / 不可执行 / 可绕过**，本件**不放宽任何判据来掩盖它**，也不把它并入生产门禁。这些写法在本轮一律写「**判不了**」（见 §5.2），并要求 fail-closed 拦截。

### 4.5 R10 误判逐条对照

| 编排方编号 | 域 / 行 | R10 判 | 实际（复核确认） | 结论 |
|---|---|---|---|---|
| 1 | slot L79 | assertion | V1 身份陈述 | **R10 误报** |
| 2 | slot L103 | assertion | V1 身份陈述 | **R10 误报** |
| 3 | slot L110 | assertion | V1 身份陈述 | **R10 误报** |
| 4 | slot L112 | assertion | V1 身份陈述 | **R10 误报** |
| 5 | slot L120（第 1 处） | assertion | V1 身份陈述 | **R10 误报** |
| 6 | truth L151 | assertion | V1 身份陈述 | **R10 误报** |
| 7 | truth L228 | assertion | V1 身份陈述 | **R10 误报** |

- R10 判 `assertion` 实际 V1 的 = **7 条全部**；R10 判 `negation` 实际 V2 的 = **0 条**；R10 判 `negation` 实际 V1 的 = **2 条**（slot L120 第 2 处、truth L240）——但这两处 R10 的豁免理由与完成词无关（窗内 `非` 来自「非 C07 主体」，`无/未` 来自「无未验残留」）：**理由错、结果对**（`_v12v_r10_out.txt:32-34,55-57`、本轮 `_v12w_r10_rerun.txt`）。
- R12 两域 `double_neg_hits=0`，与本分类无交叉。
- 净效果：R10 在这两域 `verdict=FAIL problems=7`；按 V1/V2 前置分类应为 `problems=0`（9 处全 V1）；**就这两域的 R10 problem 而言误报率 7/7 = 100%**。根因 = `_g7_predicates.py:78-130` 缺「完成词是否充当断言谓语」这一层前置分类。

---

## 5 7 条命中的最终判定 + 适用边界 + 并入顺序 + 改动建议

### 5.1 逐条终判（7 条，逐条给结论，不用「需进一步分析」概括）

本轮逐行实读原文：`C07_IDENTITY_SLOT.md:75-125`、`C07_TRUTH_SELF_PROOF.md:145-244`（Read 工具）。以下每条三选一给出结论；本 7 条中 **V2 真断言 = 0 条、判不了 = 0 条**。

**第 1 条 — slot `C07_IDENTITY_SLOT.md:79`（R10 problem #1）**
结论：**V1 身份陈述 / R10 误报**（非 V2 完成断言、非判不了）。
依据：`:79`「**填用流程**」第 ③ 步命令参数 `<已填件路径>` 是尖括号占位符，完成词做定语修饰「件路径」，规定的是「命令怎么跑、参数什么格式」；命中 U 内 `V2_OVERRIDE=[]`（`_v12_gate_compare_out.txt:10`）。形态 = 引述式 + 完成词做定语 + 规定式。

**第 2 条 — slot `:103`（R10 problem #2）**
结论：**V1 身份陈述 / R10 误报**。
依据：`:101-103` §5.2「人工自检清单（门禁之外，10 条）」的**编号第 1 个待核条件**，与并列项「全件无 `<` 占位残留」同为检查项，语力是「验收时须核什么」；`:103` 同句另有「非他件 ID」「若只能给计划号 → `unresolved`」等规定/分支文本。形态 = 规定式（编号 `1.`）。

**第 3 条 — slot `:110`（R10 problem #3）**
结论：**V1 身份陈述 / R10 误报**。
依据：`:110` 小节标题 `### 5.4 多处同步排查表（哪件/哪行/需什么字段/是否已填）`，「是否已填」是疑问式待查列名。形态 = 疑问式。

**第 4 条 — slot `:112`（R10 problem #4）**
结论：**V1 身份陈述 / R10 误报**。
依据：`:112` 表格列头 `| # | 件 | 行 | 需什么字段 | 是否已填 |`，「是否已填」是列名，非事实陈述。形态 = 表格单元格（列头）+ 疑问式。

**第 5 条 — slot `:120` 第 1 处（R10 problem #5）**
结论：**V1 身份陈述 / R10 误报**。
依据：`:120` §5.4 排查表第 7 行，明写「先例件，非 C07 落点」，主体是别件 `a_residual_n1_20261108/ACCEPTANCE_RECORDS.json`；同格状态列写「部分（session 已填、任务号仍计划号——先例与反例）」，且「其自身任务的签发身份（非 C07 主体）」。形态 = 表格单元格状态枚举 + 引述式（先例/反例）。同行第 2 处命中（R10 `negation` warning）亦为 V1，理由错结果对。

**第 6 条 — truth `C07_TRUTH_SELF_PROOF.md:151`（R10 problem #6）**
结论：**V1 身份陈述 / R10 误报**。
依据：`:148-151` 手段②「独立见证人」的**处置配对分支** `- 处置：已填 → …；未填且缺席声明如实 → …`，是「出现 X 情形时怎么处置」的条件规则，不是「X 已发生」；且 `:150` 明写「来源会话代填见证槽 = 拒绝项」——本件任务书本身要求不许代填身份，这里的「已填」正是被规制的情形名。形态 = 条件/选言分支（⑦）+ 否定式语境。

**第 7 条 — truth `:228`（R10 problem #7）**
结论：**V1 身份陈述 / R10 误报**。
依据：`:220-228` §5.2(丙) 核验者清单 A-G 概览表的 G 组「核什么」列，并列项「见证缺席处置」，拒绝条件「代填见证→**拒绝**」；`:218` 明写「核验者只核不填」。形态 = 表格单元格 + 条件/拒绝分支。

**合计与对照**：9 处命中全 V1、0 处 V2、0 处判不了（就两域这 9 处命中而言）。另 2 处 `negation` warning（slot `:120` 第 2 处、truth `:240` 通过档「判定条件」列的选言硬条件 `（G1 见证已填 或 S1 有 ≥1 处…）`）同为 V1，逐字见 `C07_TRUTH_SELF_PROOF.md:236-240`、`C07_IDENTITY_SLOT.md:120`。

**最终结论（三选一，不含糊）：门禁错，不是交付件错。** 7 条 R10 problem 全部是 **V1 身份陈述 / R10 误报**；两域交付件在这 7 处**没有真 V2 完成断言**，因此**不需要改交付件**。此结论由【复核】whatBreaksIt (1) 判为「核心事实结论 confirmed：7 条 V1 终判全部站得住、未判反」；但**判据本身 unconfirmed**（§4.4、§6），二者不可混为一谈。判不了 0 条（7 条命中）/ 9 条（候选判据在分布外新句，§4.4）。severity = medium。

### 5.2 适用边界（判不了的写法，如实写「判不了」及差什么）

编排方【设计】`boundary` 六条 + 【复核】反证补充，一律落 S3 **默认 V2 + `review_flag=True` + 判不了 + 人工复核/改写为显式规定式**，即「判不了就拦，不编规则假装能判」：

1. **跨行/跨段支配**：规定词在上一行、完成词在下一行。差：U 只到子句/单元格，无篇章级支配链 ⇒ **判不了**。
2. **依赖上下文的指代**：「该槽已填」。差：不做共指消解 ⇒ **判不了**。
3. **反讽 / 转述他人断言**：「复核回件声称三值已填」。差：无 `声称/据称/自述` 归属词表 ⇒ **判不了**（fail-closed 安全侧）。
4. **自由句式省略支配词的待核条件**：「三值已填、四路哈希实算、占位残留清零」无编号/须/是否/表格/分支标记 ⇒ **判不了**。
5. **跨文件状态同步**：A 件说已填、B 件是否落盘，属 R11 引用锚 / 独立核验轮，**不在本规则适用域**（差：单文件谓词无跨件视野）。
6. **未登记的等价完成宣称词族**：`V2_OVERRIDE` 是枚举词表，未登记说法（如「已由本人署讫」）⇒ **判不了**，落默认 V2（安全侧）；词表增补只加 V2 词、不加 V1 放过项。
7. **★ 复核新增（分布外，实证 9 条）**：真完成断言与无关禁令/否定词同句（A3 五条）、无关行内词触发 HARD_V1（A4 四条）。差：S0 无条件 V1 且 `review_flag=False` 与 S3 fail-closed 冲突、`line` 跨单元污染、无「硬性完成宣称压过硬性 V1 结构」的正确优先关系 ⇒ 当前实现**判不了**（且判反），必须人工复核；本件不编新规则假装能判。

### 5.3 并入顺序（设计口径；**本轮不实施**）

推荐链（编排方【设计】`boundary`）：

```
R9（包裹归一化要素） → V1/V2 前置分类（新） → R10（只处理剩余真 V2 候选） → R12 → R11
```

理由：R10 默认「命中即候选断言」（`_g7_predicates.py:113-130`），前置分类从源头摘掉规定/疑问/表格/占位/分支；不能放在 R10 之后，因为 `problems` 已丢完整单元信息且 `_g9_gate.py:141-152` 的 R12 会消费被污染的 `kind`；前置分类只在调用层标注，不改 `_g7_predicates.py` 一字，指纹零漂移。

★ **本轮纪律**：`_g9_gate.py:125` 现状仍是 `g7.r10_scan(text, forb)`，本任务**未实施到 `_g9_gate.py`**（该件只读）。且因候选判据 unconfirmed（§4.4），**按当前设计不得并入**——须先修好 9 条反证句、消除 §3.4 实装偏差、并让 S3 兜底真正可达，再谈上线。本件不为了让门禁通过而放宽判据。

### 5.4 若交付件有问题的最小改动建议（**不执行**）

本结论**不是**「交付件有问题」，故本节按纪律**不执行、也不建议改交付件**。备查：若未来某轮真出现 V2（例如来源会话补登回件写了「三值已填」），最小改动是把该句改写为显式规定式 / 如实登记式（如「三值补登动作由来源会话执行，见绑定行与门禁输出」），而不是删词或放宽门禁；且按 `C07_TRUTH_SELF_PROOF.md:173` D7 口径，登记件任何事后改动须重新补登并重出全套证据。本任务两域**零改动**。

---

## 6 复核回件 + 未改交付件声明 + 未验项

### 6.1 复核 verdict（如实记）

编排方【复核】字段：`"verdict":"partial"`，`ranCommands = 11`。按交付要求：**partial ⇒ 标 unconfirmed**（若 refuted 亦同样标 unconfirmed）。核心事实结论 confirmed，但「可执行四级判据」被 9 条撰写人没见过的新句证伪，故整体 partial / **unconfirmed**。

**复核确认面**（【复核】whatBreaksIt (1)，本轮已独立复现对应项）：9 件指纹 9/9 MATCH（`_v12w_fpcheck_out.txt:2-11`）；独立 `r10_scan` 得 slot raw=6/problems=5/warnings=1/assertion5+negation1、truth raw=3/problems=2/warnings=1/assertion2+negation1、R12=0（本轮 `_v12w_r10_rerun.txt`）；真 import `_g9_gate.check_deliverable` 一致（本轮 `_v12w_gate_rerun.txt`）；逐条实读原句核 7 条 V1 终判全部站得住、未判反；9 处命中 U 内 V2_OVERRIDE 9/9 全空；`22/22、14/14、MIXED 4/4` 可复现（MIX-02 需按 `run_mixed` 实句 + `token=已交付`，本轮 `_v12w_fair_rerun.txt`）；只读域 / 两件台账 / `_g7_predicates.py` 指纹与 mtime 均证零改动（`_v12w_fair_rerun.txt` 六行 `MATCH_BASELINE=True`）；`git log -1 = 2657458`、未 commit/push；只写 `_v12v_` 前缀到唯一写域。

**复核破坏面**（【复核】whatBreaksIt (2)(3)，本轮 `_v12w_adv_rerun.txt` / `_v12w_fair_rerun.txt` 重跑一致）：A3 五条否定语境判反、A4 四条无关行内词漏判（§4.4 逐句列出）⇒ 真 V2 被放过；`_v12v_fair_out.txt:7-17` 证 9/9 句不在撰写人样本集；`:19-23` 证「两标记一并回报」不实；`:25-32` 证「只用 U/pre/post 不跨单元」不实；`_v12v_adv_out.txt:166-174` 证 7 条 plain-V2 句 5 条靠 S3 兜底；S0 无条件 V1 与 S3 fail-closed 冲突。即铁律「放过 V1 身份陈述 + 抓住 V2 完成断言」的第二边失效，判据不可执行 / 可绕过 ⇒ **unconfirmed**。

### 6.2 复核回件绑定行（固定格式）

被核对象 SHA256 = 05ecdfca451476bb80d84281068fcd9c59d1364b2247cb5482943de6417781fc，字节数 = 20651
被核对象 SHA256 = 5102beae1ecf4952862d4ff1319283df816c53a49bdc81bae38d9709bef974e3，字节数 = 38232

两行由本轮 `python -I -X utf8 …/_v12w_fpcheck.py` 以 `hashlib.sha256(read_bytes())` 实算产出（`_v12w_fpcheck_out.txt:27-29`），与编排方【复核】`sha256Line` 逐字一致；逐行格式为「被核对象 + SHA256 + 等号」+ 一个空格 + 64 位十六进制 +「，字节数 = 」+ 一个空格 + 十进制数字，中间不插入路径、括号、星号、反引号或空格。

### 6.3 未改交付件声明

- 两域主件、其余只读件、两件台账、`_g7_predicates.py`、`_g9_gate.py`、`.zcode/workflow-runs/` 全部 mjs、历史 payload：**零改动、零追加、零覆盖**。证据：九件指纹 `ALL_BASELINE_MATCH = True`（`_v12w_fpcheck_out.txt:11`）；六件 mtime 与基线一致（`_v12w_fair_rerun.txt`）；本轮 `git status --porcelain` 与 `git log -1` 实跑：

```
cd "D:/Project/ra2-campaign-forge" && git status --porcelain -- lead/gate_v1v2_20261109 lead/c07_slot_20261109 lead/c07_truth_protocol_20261109 lead/gate_fp7_20261108/_g7_predicates.py lead/gate_r9r12_20261109/_g9_gate.py lead/gate_doc_name_fix_20261109 lead/PENDING_DECISIONS.md lead/GOAL_THREE_TARGETS_20261018.md; echo "---LOG---"; git log -1 --format="%h %s"
```

输出：`MM lead/GOAL_THREE_TARGETS_20261018.md`、`MM lead/PENDING_DECISIONS.md`（起始快照即为 MM，指纹一致判为既有状态）、`??` 各只读域与写域；`git log -1 = 2657458 GOAL-3T: 台账 §400→§508 与 D-07..D-11 裁决登记入账`，**未 commit、未 push**。
- 本撰写轮只写唯一写域 `lead/gate_v1v2_20261109/`，新增文件为本件、`_v12w_fpcheck.py` / `_v12w_fpcheck_out.txt` 与 5 份重跑输出 `_v12w_adv_rerun.txt` / `_v12w_verify_rerun.txt` / `_v12w_fair_rerun.txt` / `_v12w_r10_rerun.txt` / `_v12w_gate_rerun.txt`。未改动既有 `_v12_*` / `_v12v_*` 任何一件。

### 6.4 未验项（如实写「未验」，不补造）

1. **未验**：`.zcode/workflow-runs/` 全部 mjs 哈希未逐字核对（复核方注明 236 个 mjs 未逐一验；本轮同样未验，只读域零改动按指纹 + git 状态判定）。
2. **未验**：git 的 `MM` / `??` 以起始快照 + 指纹一致判为既有状态，**未跑 `git diff` 逐行比对**（本轮实跑的是 `git status --porcelain` 与 `git log -1`）。
3. **未验**：本轮未实施候选判据的修复版、未重跑修复版回归、未把它并入 `_g9_gate.py`（该件只读，且判据 unconfirmed）。
4. **未验**：MIX-02 的 `3/4` 与 `4/4` 差异已如实登记（§4.3），未修改 `_v12_verify.py:151` 的数组句；两数并存。
5. **未验**：9 条反证句的「正确判据」本轮未给出（按铁律「判不了就写判不了」，本轮只写文档，不编规则假装能判）。
6. **未验**：零真机 / 零采样代码为纪律声明，未通过进程列表取证；本轮未启动任何 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存。

### 6.5 本撰写轮实跑命令（逐条，均 `python -I -X utf8` + 绝对路径）

1. `ls -la lead/gate_v1v2_20261109/` 与 `ls -la lead/c07_slot_20261109/ lead/c07_truth_protocol_20261109/` → 写域/只读域清单（本轮首步）。
2. `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_v1v2_20261109/_v12w_fpcheck.py > …/_v12w_fpcheck_out.txt 2>&1; echo "EXIT=$?"` → `EXIT=0`，9/9 MATCH、两域 9 命中、两条绑定行。
3. `python -I -X utf8 …/_v12v_adv.py > …/_v12w_adv_rerun.txt 2>&1; … grep` → 9 条 MISMATCH、`V1 22/22 ; V2 14/14 ; MIXED 3/4`、`[D] 5/7`、`[C-TOTAL] hits=9`。
4. `python -I -X utf8 …/_v12_verify.py > …/_v12w_verify_rerun.txt 2>&1; … grep` → `V1 22/22 PASS ; V2 14/14 PASS ; MIXED 4/4 PASS`；slot V1=6/V2=0，truth V1=3/V2=0。
5. `python -I -X utf8 …/_v12v_fair.py > …/_v12w_fair_rerun.txt 2>&1; … grep` → MIX-02 PASS、UNSEEN 9/9、一并回报=False、跨单元词=True、6 件 MATCH_BASELINE=True、git log -1=2657458。
6. `python -I -X utf8 …/_v12v_r10.py > …/_v12w_r10_rerun.txt 2>&1; … grep` → problems 5/2、warnings 1/1、R12=0、RAW-VS-R10 IDENTICAL=True、TOTAL=7。
7. `python -I -X utf8 …/_v12_gate_compare.py > …/_v12w_gate_rerun.txt 2>&1; … grep` → 两域 verdict=FAIL、9 处 `U内V2_OVERRIDE=[]`。
8. `cd "D:/Project/ra2-campaign-forge" && git status --porcelain -- …; git log -1 …` → §6.3 输出。
9. 另以 Read 工具逐行实读：`_v12_REPORT.md`、`_v12_rule.py`、`_v12_verify.py:145-194`、`_v12_verify_out.txt`、`_v12_probe_out.txt`、`_v12_gate_compare_out.txt`、`_v12v_adv_out.txt`、`_v12v_fair_out.txt`、`_v12v_fp_out.txt`、`_v12v_r10_out.txt`、`_v12v_adv.py`、`_v12v_fair.py`、`C07_IDENTITY_SLOT.md:75-125`、`C07_TRUTH_SELF_PROOF.md:145-244`、`_g7_predicates.py:65-139`、`_g9_gate.py:118-157`（引用均按 `文件:行` 给出）。

---

**分界件结论一句话**：7 条 R10 problem 逐条终判全部是 **V1 身份陈述 / R10 误报**（confirmed），两域交付件零改动；但候选四级判据在分布外 9 句上把真 **V2 完成断言** 放过（partial ⇒ **unconfirmed**），这些写法**判不了**，必须 fail-closed 拦、人工复核，**并入顺序**暂不实施，不放宽判据，**未验**项见 §6.4。
