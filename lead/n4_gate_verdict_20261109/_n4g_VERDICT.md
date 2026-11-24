# _n4g_VERDICT.md — N4 重签件四条 FAIL 真伪定论（判定员回件）

- 日期：2026-11-09　角色：N4 门禁判定员（只判不改）
- 被核对象：`lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md`
- 纪律：未改 `CANDIDATE_RESIGN_YES_V2.md` 一个字节、未改母本、未改任何历史 payload、未代签 `APPROVE_SCOPE`、未宣告 N-5 可应用；未 commit、未 push；零真机、零采样代码；Python 一律 `python -I -X utf8` + 绝对路径，指纹用 hashlib。

## 0 绑定行（严格格式）

被核对象 SHA256 = 1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b，字节数 = 23129
被核对象 SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508

（口径 = 本轮 GATE_CODE 正则 `r'被核对象 SHA256 = [0-9a-fA-F]{64}'`；两值由 `_n4g_probe.py` / RUN 6 hashlib 逐字节实算。）

## 1 更正「挑错文件」判断

历史 payload `.zcode/workflow-runs/dwfrun-af6f3c87-7d72-4587-8e0d-07c4b878337c.mjs` 的 `GATE_CODE` 原文（`lowered` 偏移 7007–9114，由 `_n4g_extract_gate.py` 逐字抽出、6 个 JS 拼接占位替换为 live hashlib 值，落 `_n4g_gate_verbatim.py`）：

```
cands=sorted([p for p in wd.glob('*.md') if p.name.startswith('CANDIDATE_RESIGN')]) if wd.is_dir() else []
...
 DOC=max(cands,key=lambda p:p.stat().st_size)
 B=re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?',t)
```

`startswith('CANDIDATE_RESIGN')` 过滤 + `wd` 限定目录，唯一候选。实跑 `ls -la lead/n4_yi_final_20261108/` 得 4 件 `.md`，仅 1 件以 `CANDIDATE_RESIGN` 开头；`find lead out -name "CANDIDATE_RESIGN*" -type f` 全库 3 件，另 2 件是 `lead/gate_doc_name_fix_20261109/_dnv_sandbox36/…` 与 `_dnw_sandbox/…` 下的沙箱副本（hashlib 实算三者同为 `1950d3f3…5925b`/23129 B），**不在门禁 wd 内，不进候选**。故 `max(st_size)` 无歧义，28,897 B 中稿 `_n4v2_B_EXECUTION_SPEC_V2.md` 根本不入门禁候选集。**编排方的更正成立。**

## 2 独立复跑：四条 FAIL 全复现

**RUN 1** — `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n4_gate_verdict_20261109/_n4g_gate_verbatim.py"`（逐字历史 GATE_CODE）：

```
{"ok": false, "problems": ["缺要素 不签 APPROVE_SCOPE", "含越权断言 可应用母本", "含越权断言 放行 N-5", "缺 SHA256 绑定行"], "bindings": 0, "docBytes": 23129, "doc": "CANDIDATE_RESIGN_YES_V2.md", "rows": 17, "hunks": 21}
```

**RUN 2** — `python -I -X utf8 ".../_n4g_probe.py"`（独立实现，输出 `_n4g_probe_out.json`）：

```
a_candidates = [{"name": "CANDIDATE_RESIGN_YES_V2.md", "bytes": 23129}]
a_fp = {"sha256": "1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b", "bytes": 23129, "lines_newline_plus1": 174, "lines_splitlines": 173}
b_naive_problems = ["缺要素 不签 APPROVE_SCOPE", "含越权断言 可应用母本", "含越权断言 放行 N-5", "缺 SHA256 绑定行"]
b_fail1_missingElements = ["不签 APPROVE_SCOPE"]
b_fail2_ban_hits = {"可应用母本": [14127], "放行 N-5": [1150, 10932, 13617, 14135]}
b_fail4_bindings = {"gate_regex": 0, "tight_literal": 0, "loose": 1}
c_struct = {"sections": 六节全 true, "rows": 17, "hunks": 21}
c_binding_lines = [[122, "**被核对象（审阅回件 …）SHA256 = `ee27…`，字节数 = 11948**…"]]
```

**计数对账**：行数 174（编排方 174，一致；`splitlines` 口径 173）、rows 17（一致）、hunks 21（一致，`hunks_raw` 21 项）、绑定行 严格 0 / 宽松 1（一致）、字节 23129（一致）。**RUN 6** 十件指纹 sha/bytes/lines 逐项对照编排方基线，`all_match = true`（含母本 `517889c6…`/399,508/7292）。

## 3 逐条判 ① / ④（缺要素类）

### ① 缺要素「不签 APPROVE_SCOPE」= 伪 FAIL，责任在门禁词表

原句（`CANDIDATE_RESIGN_YES_V2.md:15`、`:150`）：

```
1. **不签 `APPROVE_SCOPE`**——该签署属来源会话签发人（N-4 原文 `NEXT_STEPS_20261106.md:49` 验收条款：「独立审阅者签候选 YES、来源会话签发人签 APPROVE_SCOPE」，本轮实读）。
**性质限定（越权断言排除声明）**：本 YES **不签 `APPROVE_SCOPE`**（属来源会话签发人）；…
```

RUN 2 `b_fail1_literal_reason`：`present_raw = false`、`不签 \`APPROVE_SCOPE\`` = true、`不签署 APPROVE_SCOPE` = false。即**字面不含七个连续字符，语义明确在场**（反引号包裹 `APPROVE_SCOPE`，是 Markdown 代码标记，且连续两处、一处还引 N-4 验收条款）。

**判断：词表过严，交付件不该改。** 实装 R9（`lead/gate_fp7_20261108/_g7_predicates.py:31-65`，包裹字符归一化）在 RUN 3 给出 `problems: []`、warning「要素 不签 APPROVE_SCOPE 仅在包裹归一化后命中（raw 层缺字面）」、`each_element` = `(true, "normalized")`。语义层要素存在性已满足，缺的只是字面 7 连字。

### ④ 缺 SHA256 绑定行 = 伪 FAIL（语义），但**格式与后加铁律不符**须如实登记

`CANDIDATE_RESIGN_YES_V2.md:122` 逐字：

```
**被核对象（审阅回件 `lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md`）SHA256 = `ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e`，字节数 = 11948**——复核回件绑定值，撰写员本轮 hashlib 实算相符（`_rw_fpcheck` MATCH 行）。
```

RUN 4 / RUN 7（`_n4g_exact_out.json`）逐字符结论：

| 项 | 实值 | 后果 |
|:--|:--|:--|
| 「被核对象」与「SHA256 =」之间 | 插 70 字符 infix `（审阅回件 \`lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md\`）`，且无空格 | 历史正则 `被核对象 SHA256\s*=` 失配 → **严格 0** |
| 64 位 hex 前后 | 各一个反引号 U+0060 | 本轮铁律「中间不得插入…反引号」明确禁止；历史正则 `` `? `` 容许 |
| 「，字节数 = 11948」 | 在场 | 绑定要素完整 |
| 宽松口径 `被核对象[^。\n]{0,160}?SHA256…` | 命中 1 条 | **宽松 1** |

**差在哪个字符**：主要断点是那 70 字符括注 infix 顶掉了「被核对象 」后的紧邻空格；次要断点是 hex 前后的反引号。RUN 7 变体实测：`v1_only_drop_infix` 严格仍 false（连空格都没了）、`v2_only_drop_hex_backticks` 严格仍 false、`v3_drop_infix_insert_space` 严格 **true** 但铁律 tight 仍 false（反引号还在）、`v4_canonical_full_line` 严格与 tight 均 true。

**绑定是否真实**：RUN 3 用实装 R11（`_g7_predicates.py:157-219`）实测 `bindings: 1`、`recomputed = ee27b4ca…3102e`、`bytes: 11948`、`match: true`、`problems: []`；`lead/gate_r9r12_20261109/GATE_R9R12_REGRESSION.md:159` 已把本件登记为 PASS「ee27b4ca… match=True | 旧 4 条朴素越权全为否定/引证语境；绑定真锚」。即**绑定语义完全成立，只是书写与合同不一致**。

**谁该让步（正面回答）**：这是合同版本错配。2026-11-08 产出件的历史门禁正则自带 `` `? ``（容许反引号），说明当时合同只要求「被核对象」与「SHA256」紧邻；本轮（2026-11-09）铁律把格式收紧到禁一切 infix/反引号，是**后加的更严合同**。用后加合同判先前交付件，等价于追溯改判。`lead/gate_postmortem_20261109/GATE_LITERAL_MATCH_POSTMORTEM.md:73` 亦把它归为「合同-门禁不一致（现行铁律禁 infix），修法=合同参数显式化」。

我的判定：**应门禁让步**（采用已实装的 R11 宽容匹配 + 引用锚回验，交付件零改动），`lead/gate_r9r12_20261109/GATE_R9R12_REGRESSION.md:159` 已给出该答案。但**不掩盖另半边**：若来源会话坚持按本轮铁律字面执行，则 ④ 不是纯词表问题，L122 确实不合规，需按 §6 改一行——此时结论转为 (c)。两种口径的后果都写在这里，不两边讨好。

## 4 逐条判 ② / ③（越权断言类）

### 原句与出现位置（RUN 2 `d_occurrences`）

**★ 独立复核出的一处背景更正**：编排方背景称「可应用母本」出现在「性质限定里的『**不应用母本**』」——**不成立**。实跑 `t.count('可应用母本')=1`、`t.count('不应用母本')=2`、`'可应用母本' in '不应用母本' = False`。「不应用母本」是 4 字词，不含 5 字词「可应用母本」。全文「可应用母本」**恰好 1 处**，在 L155 的排除清单里。

| 词 | 次数 | 位置 | 原句（节选） | 语境 |
|:--|--:|:--|:--|:--|
| 可应用母本 | 1 | L155 (pos 14127) | `3. **无越权断言**：审阅/复核回件不出现「可应用母本 / 放行 N-5 / APPROVE_SCOPE 已签」类断言；` | **排除清单**（附条件第 3 条，列举不许出现的断言） |
| 放行 N-5 | 4 | L17 (1150) | `3. **不放行 N-5**——N-5 需有权来源会话派发新任务书（N-4 原文 :53-58，本轮实读）。` | 边界否定声明 |
| | | L130 (10932) | `或回件出现「可应用/放行 N-5」断言，本 confirmed 即翻。` | 引证（翻案条款） |
| | | L150 (13617) | `**不放行 N-5**；不断言运行时行为…` | 性质限定·越权断言排除声明 |
| | | L155 (14135) | `不出现「可应用母本 / 放行 N-5 / …」类断言` | 排除清单 |

本件唯一的正面判定在 L148：`**resign 判定：YES——仅限「候选语义层」**`，自带「仅限」限定，且不断言可应用/放行。**结论：②③ 五处命中全部是在排除/否定/引证，无一处是在断言；两条 FAIL 均为误报。**

### R10/R12 谓词实测（RUN 3，与语义判断一致）

```
r10.problems = []      r10.warnings = 5 条
kind_counts = {"negation": 4, "quote_mention": 1}   assertion = 0
r12.problems = []      r12.hits = []
```

谓词**没有**把任何一处判成 assertion，与我的语义判断一致，故不存在「谓词判 assertion 而语义是排除」的情形，如实登记。注：本域 GATE_CODE 的 BAN 是 4 项（不含「已生效」），故命中 5 处；回归语料用 5 项 BAN，命中 6 处——数字差异来自词表，非矛盾。

### 谓词漏了哪一类语境（RUN 5 `_n4g_r10gap_out.json`，构造样本实测）

`_g7_predicates.py:78-111` 的 R10 只认两个豁免触发：① 24 字符子句窗内出现否定词；② 「」≤80 字符短引证跨度且无自指标记。缺**第三类：显式「清单/词表/排除项」语境**。实测：

- S3「本件附条件第 3 条要求：…凡出现任一表述则本 YES 立即作废：可应用母本 / 放行 N-5。」→ 两词判 `assertion`（**误报**，否定词落在 24 字窗外）。
- S5「- 越权词表：可应用母本；放行 N-5；APPROVE_SCOPE 已签。」→ 两词判 `assertion`（**误报**，无「」、无邻近否定词）。
- S4「门禁 BAN 清单为 \`可应用母本\`、\`放行 N-5\`、\`已签 APPROVE_SCOPE\`，均不得出现。」→ 前两词因邻近否定词侥幸豁免，第三词判 `assertion`（**误报**，反引号代码跨度不视为数据语境）。
- S6「本 YES 已获批准，可应用母本，放行 N-5。」→ 正确判 `assertion` 拦住（真断言零放松）。

即本件 R10 的 0 problems 是**脆弱的正确**：L155 恰好同时带「无…不出现」和「」两个触发条件才全豁免。`GATE_R9R12_REGRESSION.md:207` 已登记 R10 对报告自身自指误报 12 条，`:226` 建议补「反引号代码跨度视为数据语境豁免」并把 24 字窗邻近否定改子句内同短语判定。

### ★ 张力正面处理

本件的核心内容就是「声明我不做 X」：历史 payload IRON 第 8 条明文要求「本任务不签 APPROVE_SCOPE、不应用母本、不放行 N-5」，撰写指令又要求 §6 写「越权断言排除声明」。要表达「不做 X」，**必然要提到 X 这个词**。朴素门禁 `for bad in [...]: if bad in t: P.append('含越权断言 '+bad)` 用全文子串判违规，等价于要求文件一次都不出现禁词——**也就是要求它无法表达这个被强制要求的声明**。门禁此处自相矛盾：一边要求写排除声明，一边把排除声明里的词判成越权。

**我的立场（不选两边讨好）**：禁词检查不能靠「零出现」，必须靠**断言极性**。理由链：①「不 X」与「X」真值相反，把二者同罪，门禁丧失最基本的区分能力；② 这不等于放松——R10+R12 组合既豁免否定/引证/清单，又拦双重否定与裸断言（S6 真断言实测拦住，回归报告 `:153` TV1–TV6 全 FAIL 零放走）；③ 修法应补「清单/词表/排除项」语境识别与代码跨度识别，而不是把「不 X」改写成不写；④ 真断言一旦出现（如「本 YES 已获批准，可应用母本」）必须仍被拦。

因此 **②③ 判伪 FAIL，责任在门禁判据，交付件不改一个字**。

### 四条 FAIL 汇总

| # | FAIL | 真伪 | 定性 | 责任 |
|:--|:--|:--|:--|:--|
| ① | 缺要素 不签 APPROVE_SCOPE | **伪** | 语义在场，仅反引号使 7 连字缺字面 | 门禁词表过严 → R9 归一化 |
| ② | 含越权断言 可应用母本 | **伪** | 1 处全在排除清单，非断言 | 门禁忽略断言极性 → R10+R12 |
| ③ | 含越权断言 放行 N-5 | **伪** | 4 处全为否定/引证/排除清单，非断言 | 同 ② |
| ④ | 缺 SHA256 绑定行（严格 0） | **伪**（语义）／**格式真不合后加铁律** | 绑定真实且 R11 回验 MATCH=True；70 字符 infix + hex 反引号使紧邻正则失配 | 主判：门禁紧邻正则 → R11；条件分支见上 |

RUN 3 汇总：`naive_gate_problems` = 4 条，`improved_gate_problems` = `p9 + p10 + p12 + p11` = **[]**。已实装谓词在同一文件上四条全消。

## 5 N-5 就绪度：选 (b) 不能，但只需改门禁

**判 (b)**：四条 FAIL 全是门禁判据问题，交付件本身语义无缺陷（RUN 3 改进谓词零 problems；`GATE_R9R12_REGRESSION.md:159` 已判 PASS）。但「门禁通过」是 N-5 应用链在**门禁层**的事实，必须把该域 `GATE_CODE` 换成 R9/R10/R11/R12 并实跑复判才能算数，不能由本判定件口头宣布；而历史 payload 属铁律绝对只读、本任务不得改，故本任务只给结论、不落地替换。因此不是 (a)。**(c) 只在一种条件下成立**：来源会话坚持用 2026-11-09 后加铁律的字面格式去追溯判 2026-11-08 的交付件，则 ④ 需改 L122（改法见 §6）。

### 与本件无关的、仍未满足的 N-5 前置条件（签了 YES ≠ 可以改母本）

1. **来源会话签发人签 `APPROVE_SCOPE`**：`lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md:49`「独立审阅者签候选 YES、来源会话签发人签 APPROVE_SCOPE，均以 N-1 记录格式绑定任务书与基线／候选哈希；身份、任一规则或版本缺失则任务书不生效」；交付件 `:159-160` 自列「本文不代签」。本件只是那个 YES，不含此签。
2. **有权签发人对甲/乙方向正式确认并补登**：`lead/direction_ruling_20261108/RULING_DIRECTION.md:23` Q1 仅「待有权签发人确认的方向意见」，`:25`「本次不补登、不签署、不应用」，`:66`「正式替代和绑定待有权签发，未生效」；交付件 `:161` 同列。
3. **有权来源会话派发 N-5 新任务书（正式写域）**：`NEXT_STEPS_20261106.md:53-58`、`:119`「身份未落实是派发阻塞」；交付件 `:162`。
4. **用户当轮明示**（实施侧）：`RULING_DIRECTION.md:7`「N-5 正式应用…不得由裁决代替用户当轮明示」、`:25`「N-5 实施另待用户当轮明示」、`:66`；`NEXT_STEPS_20261106.md:98`（依赖 E3／真机／活进程的实施须当轮明示）。与「一般授权已具备、无需再次索取同一一般授权」（`:50`、`:58`）不矛盾。
5. **签发人身份／任务书编号／版本绑定入 N-1 记录**：`:49`、`:119`。
6. **运行时与真机验证**：交付件 `:142`、`:163-168` 自列 9 项未验（T1/T2/T5、整趟行为、母本 6 包装函数运行时行为、RULING D24/D25 复读、补登件定位、复核回件落盘件、V2:91 措辞）。
7. **门禁层本身**：该域 `GATE_CODE` 现仍报 4 FAIL（RUN 1），修正谓词已实装但未替换进该域门禁。

## 6 「若真需要改」最小改动清单（只列，不执行）

> 前提：仅在来源会话坚持按本轮铁律字面、或坚持「零出现」口径时才需要。以下均为「应当改成什么」，**一个字节也未执行**。

**改动点 A（针对 ①，可选）**：`:15`、`:150` 的 `不签 \`APPROVE_SCOPE\`` → `不签 APPROVE_SCOPE`（去反引号）。改后字面 7 连字在场，语义无损，且与 N-4 `:49` 书写一致。

**改动点 B（针对 ④，核心）**：`:122` 整行替换为规范格式，逐字：

```
被核对象 SHA256 = ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e，字节数 = 11948
```

即删 70 字符括注 infix、删 hex 前后反引号、删外层 `**`，保留「，字节数 = 」与数字。RUN 7 实测该行 `gate_strict=true`、`iron_tight=true`。**更低侵入替代**：`:122` 原行不动，其后**新增一行**上述规范行；RUN 7 实测整文件 `gate_strict=1`、`iron_tight=1`，且保留原括注路径信息（推荐此式，若必须改件）。

**改动点 C（针对 ②③，不推荐，仅登记备选）**：不要删「可应用母本 / 放行 N-5 / 不放行 N-5 / 不应用母本」这些词——删了就无法表达排除声明，恰是本件 IRON 与 §6 的必写内容。若来源会话坚持「零出现」，唯一自洽做法是把排除声明换成不含禁词的等价表述（如 `:155` 改为「审阅/复核回件不得出现任何超出语义层 YES 的断言」、`:17` 改为「N-5 仍待有权来源会话派发新任务书」），但这会削弱可核验性，我不推荐。

**改动后 SHA256（RUN 7 `_n4g_exact_out.json`，均未落盘）**：

| 落地方式 | SHA256 | 字节 |
|:--|:--|--:|
| 原件 | `1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b` | 23129 |
| 仅替换 :122（B） | `abf90ca74dc886ef315beeb9306019120b7884fe10b667723db77e67e17e47ec` | 22944 |
| :122 后插入一行（B 替代式） | `50925ee9d183213831d9fd26b7d07007a8f6d7ba65867e19805efcf6814f1dce` | 23236 |
| 文件尾追加一行 | `23c264830de6f5177d1ba732037941deec730bec9623c33479fffea237f3e675` | 23237 |
| A+B 同时改 | 未验（未实算） | 未验 |

### 引用面排查（谁引用了它的指纹）

`_n4g_refs.py` 全量扫描落 `_n4g_refs_out.json` / `_n4g_refs_full.txt`。逐个查出：

**① 硬绑定（把该 hash 当期望值实算比对，改后必然 MISMATCH，需同步改期望值）**
- `lead/counterpart_fix_20261109/_cf_fp_check.py:24`（`EXPECTED` 字典，输出 `MISMATCH`）、`_cfv_fp_check.py`
- `lead/gate_fp7_20261108/_g7_fp_check.py:12`（`EXPECT`，输出 `ALL_MATCH`/`MISMATCH_COUNT`）、`_gv_fp_check.py`、`_g7_reverse_validate.py`
- `lead/matrix_row5_20261109/_r5c_fingerprint.py:20`、`_r5v_fingerprint.py`（`FINGERPRINT_MATCH n/10`）
- `lead/matrix_ab_ruling_20261109/_rv_decision_model_20261109.py:31`（`BASELINE_…=11/11_MATCH`）
- `lead/gate_doc_name_fix_20261109/_dn_regate_out.json`、`_dnv_regate_rerun.txt`、`_dnw_regate_rerun.txt`（门禁重跑输出）
- `lead/gate_r9r12_20261109/_g9_regression_out.json`（`appendix_real4` 的 `sha256` 字段）、`_g9v_regress_out.json`
- `lead/gate_rejudge32_20261109/_rj_baseline_rerun.json`、`_rj_double_track_out.json`、`_rj_orchestrator_replay_out.json`
- `lead/oldwording_sweep_20261109/_ow_raw_hits.json`
- 短哈希截断 2 件：`lead/gate_doc_name_fix_20261109/_dnv_patch36_run_out.json:522`（`docSha256_head "1950d3f31048b9a0"`）、`_dnw_template_out.json:970`（`sha_head "1950d3f31048"`）

**② 审计/文字快照（改后陈述与现盘不符，须登记或重跑，非必须改字节）**：20 件，含 `lead/text_fix_unified_20261109/UNIFIED_TEXT_FIX.md:50`（规范格式绑定行）、`_uf_UNIFIED_FIX_LIST_20261109.md`、`lead/counterpart_fix_20261109/COUNTERPART_FIX.md:42`、`lead/gate_postmortem_20261109/GATE_LITERAL_MATCH_POSTMORTEM.md:23`、`lead/gate_fp7_20261108/GATE_FALSE_POSITIVE_5_6_7.md`、`lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md`、`lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md`、`lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md`、`lead/gate_r9r12_20261109/GATE_R9R12_REGRESSION.md:159`（表格 23129 B + PASS 结论）、各 `*_out.txt` 的 MATCH 行。完整清单见 `_n4g_refs_out.json` 的 `audit_snapshot_refs.files`。

**③ 不受影响**：两件台账 `lead/PENDING_DECISIONS.md` / `lead/GOAL_THREE_TARGETS_20261018.md` 全文 grep 无 `1950d3f3`、无 `CANDIDATE_RESIGN`（RUN 6 亦证零漂移）；`.zcode/workflow-runs/` 全部 mjs 中 **0 件**含完整或短 hash（原始产出 payload `dwfrun-af6f3c87…` 的 `FP_CODE` 是 live hashlib 计算，未硬编码），**7 件**仅按文件名引用（文件名不变即不受影响，且历史 payload 绝对只读）；两件沙箱同名副本（`_dnv_sandbox36/`、`_dnw_sandbox/`）是历史快照，同指纹，不应跟着改（改了反破坏可复现性）。

## 7 未验项与纪律声明

- 未验：`live_binding_candidates` 19 件是否**全部**在运行时真读取该期望值——只按扩展名 + 比对语义键初筛，未逐件执行（写入 `_n4g_refs_out.json` 的 note）；A+B 同时改后的整文件 SHA256 未实算；Git 历史（历史 commit 中的引用）未查。
- 未跑：任何真机程序、任何采样/注入/动态内存解析；未读取活进程内存。
- 未改：`CANDIDATE_RESIGN_YES_V2.md`（RUN 6 指纹 `1950d3f3…5925b`/23129 零漂移）、母本（`517889c6…`/399,508 零漂移）、`lead/n4_yi_final_20261108/` 全部件、`lead/b2b_candidate_lf_20261107/`、`lead/b2b_design_20261106/STATE_MATRIX.json`、`lead/direction_ruling_20261108/`、`.zcode/workflow-runs/` 全部 mjs、两件台账。
- 未代签 `APPROVE_SCOPE`、未宣告 N-5 可应用、未宣告母本可改。未 commit、未 push。
- 全部写入仅落在 `lead/n4_gate_verdict_20261109/`，前缀 `_n4g_`。
