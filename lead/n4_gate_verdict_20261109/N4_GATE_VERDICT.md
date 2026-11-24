# N4_GATE_VERDICT.md — N4 重签件四条 FAIL 真伪 · N-5 就绪度 · 最小改动清单

- 日期：2026-11-09　角色：N4 判定件撰写员（只判不改、不代签、不宣告 N-5 可应用）
- 被核对象：`lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md`（23,129 B / 174 行）
- 唯一写域：`lead/n4_gate_verdict_20261109/`。本轮新增件前缀 `_n4g_writer_*`；本交付件按本轮交付指令点名 `N4_GATE_VERDICT.md`。
- 纪律：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；Python 一律 `python -I -X utf8` + 绝对路径，指纹用 hashlib；未 commit、未 push。

---

## 1 目的与边界

**目的**：只判 N4 重签件 `CANDIDATE_RESIGN_YES_V2.md` 在历史门禁下四条 FAIL 的真伪，写 N-5 就绪度结论，列「若真需要改」的最小改动清单（**不执行**），并把改动后指纹变化的引用面逐个排查。

**边界（本件不做、不断言）**：

1. **不改件**：`CANDIDATE_RESIGN_YES_V2.md` 一个字节不改；母本、候选、乙矩阵、裁决书、两件台账、`.zcode/workflow-runs/` 全部 mjs 全部只读。本件所有「应当改成什么」只写在纸上。
2. **不代签**：不替来源会话签发 `APPROVE_SCOPE`。该签署属来源会话签发人（`lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md:49` 实读）。
3. **不宣告 N-5 可应用**：判定性质仅限「门禁判据真伪 + 就绪度」，签了语义层 YES ≠ 可应用母本 ≠ 放行 N-5。
4. 「门禁通过」是门禁层事实，须由有权会话把该域 `GATE_CODE` 替换并实跑复判才算数；历史 payload 属铁律绝对只读，本件只给结论、不落地替换。
5. 逐条给「复现命令+输出」或「文件:行」；拿不到写「未验」，不补造。

**本轮独立实跑清单**（全部在写域内、可复跑）：

| 脚本 / 命令 | 输出件 | 用途 |
|:--|:--|:--|
| `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n4_gate_verdict_20261109/_n4g_writer_verify.py"` | `_n4g_writer_out.json` | 十件指纹、逐字门禁判据内联复跑、四条 FAIL 原句/计数/语境、R9/R10/R11/R12、改后哈希、引用面 |
| `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n4_gate_verdict_20261109/_n4g_gate_verbatim.py"` | stdout | 逐字历史 `GATE_CODE` 复跑（判定员自 payload 抽出） |
| `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n4_gate_verdict_20261109/_n4g_writer_refs41.py"` | `_n4g_writer_refs41.json` | 引用面 41 件逐个排查 + 本轮复扫差异 |
| `grep -n … "…/dwfrun-af6f3c87-…mjs"` / `find lead out -name "CANDIDATE_RESIGN*" -type f` / `git log -1` / `git status --porcelain` | stdout | payload 原文、候选集、零漂移 |

---

## 2 上游指纹（十件，母本逐位核对）与「挑错文件」判断的更正声明

### 2.1 十件指纹 · 本轮 hashlib 逐字节实算

实跑 `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n4_gate_verdict_20261109/_n4g_writer_verify.py"`，`_n4g_writer_out.json` 的 `ten_fingerprints` 输出 `ten_all_sha_bytes_match = true`。对照编排方【编排方指纹】十件基线：

| # | 路径 | SHA256（本轮实算 = 基线） | 字节 | 行 |
|--:|:--|:--|--:|--:|
| 1 | `lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md`（被核对象） | `1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b` | 23129 | 174 |
| 2 | `lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md` | `c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801` | 28897 | 211 |
| 3 | `lead/n4_yi_final_20261108/B_EXECUTION_SPEC_V2_YI.md` | `27f31bf560e9a71c5e9603d81a860233e7fc7b19e504eed4a15ea24a2077b067` | 35486 | 238 |
| 4 | `lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md` | `ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e` | 11948 | 85 |
| 5 | **`out/re_work/…/qc151_u0400_trip/qc151_trip.py`（母本）** | **`517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636`** | **399508** | **7292** |
| 6 | `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` | `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2` | 412759 | 7534 |
| 7 | `lead/b2b_design_20261106/STATE_MATRIX.json` | `1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016` | 3558 | 17 |
| 8 | `lead/direction_ruling_20261108/RULING_DIRECTION.md` | `0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653` | 16514 | 97 |
| 9 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 | 382 |
| 10 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 | 9758 |

**母本逐位核对**：本轮 `mother_sha_full = "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636"`，与编排方基线、判定员 RUN 6、复核员 `_n4gv_fp_out.json:2` 的 `all_sha_and_bytes_match: true` 逐位相同；399,508 B 一位不差。基线「行」= 换行数 + 1（`newline_plus1`），`splitlines` 恒少 1（文件以换行结尾），10 件一致，非漂移（`_n4gv_fp_out.json:9-22`）。

**末次零漂移复算**（写作完成后实跑，见 §6）：重签件 `MATCH 1950d3f3…5925b / 23129`、母本 `MATCH 517889c6…ba636 / 399508`、两件台账 `MATCH 3765eddb…f2d7 / 52419`、`MATCH 2baa0de4…8ede / 759518`。

### 2.2 ★ 对编排方先前「挑错文件」判断的更正声明

**先前判断**：门禁挑错了文件——把 28,897 B 的中稿 `_n4v2_B_EXECUTION_SPEC_V2.md` 当成被核交付件。

**更正结论：该判断不成立，编排方后续更正成立。门禁挑的就是 23,129 B 的 `CANDIDATE_RESIGN_YES_V2.md`。**

依据一（payload 原文，实跑 `grep -n -E "GATE_CODE|cands=|…" ".zcode/workflow-runs/dwfrun-af6f3c87-7d72-4587-8e0d-07c4b878337c.mjs"` 输出第 9 行，`lowered` 字段内 `const GATE_CODE = [`）：

```
cands=sorted([p for p in wd.glob('*.md') if p.name.startswith('CANDIDATE_RESIGN')]) if wd.is_dir() else []
...
 DOC=max(cands,key=lambda p:p.stat().st_size)
 B=re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?',t)
```

三行逐字落在抽出件 `_n4g_gate_verbatim.py:5`（`cands=`）、`:8`（`DOC=max`）、`:20`（`B=re.findall`）。`wd` 被 `root/'lead/n4_yi_final_20261108'` 限定（`_n4g_gate_verbatim.py:3`），且 `startswith('CANDIDATE_RESIGN')` 过滤掉了所有中稿名——`_n4v2_B_EXECUTION_SPEC_V2.md` 以下划线开头，根本不进候选集，`max(st_size)` 无歧义。

依据二（本轮实跑，`_n4g_writer_out.json` 的 `candidate_set`）：

```
"all_md_in_wd": ["B_EXECUTION_SPEC_V2_YI.md", "CANDIDATE_RESIGN_YES_V2.md",
                 "_cs_semantic_review_GLM_20261108.md", "_n4v2_B_EXECUTION_SPEC_V2.md"]
"cands_startswith": ["CANDIDATE_RESIGN_YES_V2.md"]
"picked_by_max_size": "CANDIDATE_RESIGN_YES_V2.md"
```

依据三（全库副本，实跑 `find lead out -name "CANDIDATE_RESIGN*" -type f`，stdout 3 行）：

```
lead/gate_doc_name_fix_20261109/_dnv_sandbox36/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md
lead/gate_doc_name_fix_20261109/_dnw_sandbox/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md
lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md
```

另 2 件在沙箱目录、不在门禁 `wd` 内；本轮目录限定 `python -I -X utf8 -c "…(R/'lead').rglob('CANDIDATE_RESIGN*')…"` 实算三者指纹同为 `1950d3f3…5925b / 23129`。逐字门禁复跑输出的 `"doc": "CANDIDATE_RESIGN_YES_V2.md", "docBytes": 23129` 与之自洽。复核员回件第 ② 项亦独立重建 `GATE_CODE` 并确认「候选不止一件之 refuted 条件不成立」（编排方【复核】字段）。

---

## 3 四条 FAIL 逐条判定

### 3.0 四条 FAIL 的复现（两条独立命令，逐字一致）

**RUN A — 逐字历史 `GATE_CODE`**：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n4_gate_verdict_20261109/_n4g_gate_verbatim.py"`（判定员 `_n4g_extract_gate.py` 自 payload `lowered` 偏移 7007–9114 抽出、6 个 JS 拼接占位替换为 live hashlib 值）：

```
{"ok": false, "problems": ["缺要素 不签 APPROVE_SCOPE", "含越权断言 可应用母本", "含越权断言 放行 N-5", "缺 SHA256 绑定行"], "bindings": 0, "docBytes": 23129, "doc": "CANDIDATE_RESIGN_YES_V2.md", "rows": 17, "hunks": 21}
```

**RUN B — 本轮独立实现**（`_n4g_writer_verify.py` 内联四步判据，stdout 的 `inline_naive_gate`）：

```
"problems": ["缺要素 不签 APPROVE_SCOPE", "含越权断言 可应用母本", "含越权断言 放行 N-5", "缺 SHA256 绑定行"],
"missingElements": ["不签 APPROVE_SCOPE"], "overreachHits": ["可应用母本", "放行 N-5"],
"rows": 17, "hunks": 21, "bindings": 0
```

与编排方【门禁重跑】`naive.hits=["可应用母本","放行 N-5"]`、`r12.problems=[]`、`structural.missingElements=["不签 APPROVE_SCOPE"]`、`rows:17`、`hunks:21`、`bindings_strict:0/bindings_loose:1` 逐项一致。六节全在场、逐行表 17 行 ≥14、九 hunk 21 处 ≥9，这三项门禁未报问题。

### 3.1 ① 缺要素「不签 `APPROVE_SCOPE`」= **伪 FAIL**（责任在门禁词表过严）

**复现证据**：RUN A / RUN B 均报 `缺要素 不签 APPROVE_SCOPE`；判据是 `_n4g_gate_verbatim.py:12-13` 的 `for k in [...]: if k not in t: P.append('缺要素 '+k)`——纯字面子串比较，词表项为 `不签 APPROVE_SCOPE`（7 连字，中间一个空格）。

**原句**（实读 `CANDIDATE_RESIGN_YES_V2.md:15`、`:150`）：

```
:15   1. **不签 `APPROVE_SCOPE`**——该签署属来源会话签发人（N-4 原文 `NEXT_STEPS_20261106.md:49` 验收条款：「独立审阅者签候选 YES、来源会话签发人签 APPROVE_SCOPE」，本轮实读）。
:150  **性质限定（越权断言排除声明）**：本 YES **不签 `APPROVE_SCOPE`**（属来源会话签发人）；**不应用母本**（母本指纹 517889c6…/399,508 本轮零改动）；…
```

**语境分析**：两处都是加粗的边界条目，`APPROVE_SCOPE` 被 Markdown 反引号 U+0060 包裹；`:15` 还逐字引用 N-4 验收条款（`NEXT_STEPS_20261106.md:49` 本轮实读确有「独立审阅者签候选 YES、来源会话签发人签 APPROVE_SCOPE」）。语义明确「不签」，缺的只是 7 个连续字符的字面。

**依据**（本轮 `_n4g_writer_out.json` 的 `fail1`）：`present_raw = false`、`with_backticks_count = 2`。实装 R9 包裹归一化（`lead/gate_fp7_20261108/_g7_predicates.py:31-65`，`r9_normalize` 先把反引号跨度内换行删掉、再把 `_WRAP_CHARS` 换成空格）在本轮 `improved_predicates.r9_each` 给出 `"不签 APPROVE_SCOPE": [true, "normalized"]`、`r9_problems: []`、warning「仅在包裹归一化后命中（raw 层缺字面）」。

**真伪与责任**：伪 FAIL。要素语义在场，门禁词表未做包裹归一化。**交付件不该改**。

### 3.2 ② 含越权断言「可应用母本」= **伪 FAIL**（并更正编排方背景一处）

**★ 独立复核更正**：编排方背景称「可应用母本」出现在「性质限定里的『**不应用母本**』」——**不成立**。本轮 `_n4g_writer_out.json` 的 `fail2_fail3` 实跑：

```
"count_可应用母本": 1,  "count_不应用母本": 2,  "可应用母本_in_不应用母本": false
```

「不应用母本」是 4 字词，不含 5 字词「可应用母本」。全文「可应用母本」**恰好 1 处**，在 `:155`（byte pos 14127）。复核员 `_n4gv_text.py` 独立复现同一更正（编排方【复核】⑤）。

**原句**（`CANDIDATE_RESIGN_YES_V2.md:155`）：

```
3. **无越权断言**：审阅/复核回件不出现「可应用母本 / 放行 N-5 / APPROVE_SCOPE 已签」类断言；
```

**语境分析**：这是 §6「附条件全文」第 3 条，列举「不许出现的断言」——**排除性声明 / 排除清单**，不是断言。整句带「无越权断言」「不出现」「「」引证跨度」「类断言」四重标记。复核员独立极性分类器 `_n4gv_polarity_out.json:9-16` 逐处给整句：`"my_polarity_verdict": "EXCLUSION / NEGATION / QUOTE (not an assertion)"`、`in_「」quote: true`、`negation_before_token_in_sentence: true`、`self_assert_marker: false`；全件 `total_hits: 5, assertion_count: 0`（`:74-75`）。

**依据**：本轮 `improved_predicates` 实跑 `r10_problems: []`、`r12_problems: []`、`r10_kinds = {negation: 4, quote_mention: 1, assertion: 0, double_neg: 0}`。编排方【门禁重跑】`r10.problems=[]`、warnings 5 条（negation×4 + quote_mention×1）、`r12.problems=[]` 一致。

**真伪**：伪 FAIL。门禁把「附条件排除清单」里的词当成越权断言，忽略了断言极性。**真断言**在本件中零处；唯一正面判定是 `:148`「**resign 判定：YES——仅限「候选语义层」**」，自带「仅限」限定。

### 3.3 ③ 含越权断言「放行 N-5」= **伪 FAIL**

**复现证据**：RUN A / RUN B 均报该条；`_n4g_writer_out.json` 的 `ban_token_line_map` 给 `"放行 N-5": [17, 130, 150, 155]`、`count_放行N5 = 4`、`count_不放行N5 = 2`。

**四处原句与语境**（逐字实读）：

| 行 | 原句 | 语境 |
|--:|:--|:--|
| :17 | `3. **不放行 N-5**——N-5 需有权来源会话派发新任务书（N-4 原文 :53-58，本轮实读）。` | 边界否定声明（§1 第 3 条） |
| :130 | `- **翻案条款（复核回件原文）**：若…或回件出现「可应用/放行 N-5」断言，本 confirmed 即翻。` | 引证（翻案条款，条件句「若…即翻」） |
| :150 | `**不放行 N-5**；不断言运行时行为、整趟行为或崩溃修复效果；不签真机验收。` | 性质限定·越权断言排除声明 |
| :155 | `3. **无越权断言**：…不出现「可应用母本 / 放行 N-5 / APPROVE_SCOPE 已签」类断言；` | 附条件排除清单 |

`_n4gv_polarity_out.json:17-72` 逐处给 `my_polarity_verdict = "EXCLUSION / NEGATION / QUOTE (not an assertion)"`，四处 `self_assert_marker: false`。

**依据**：实装 R10（`_g7_predicates.py:78-130`）逐处分类 `negation×3 + quote_mention×1`、`assertion = 0`、`r10_problems: []`；R12 双重否定守卫（`_g7_predicates.py:133-148`）`r12_problems: []`、`hits: []`。RUN 3 汇总（判定员 `_n4g_predicates_out.json:103-109`）：`naive_gate_problems` 4 条 vs `improved_gate_problems: []`；本轮 `_n4g_writer_out.json` 复现 `improved_gate_problems: []`。`lead/gate_r9r12_20261109/GATE_R9R12_REGRESSION.md:159` 已把本件登记为 **PASS**：`| …CANDIDATE_RESIGN_YES_V2.md | 23129 | PASS | 6(6)=5 negation+1 quote_mention | 0 | ee27b4ca… match=True | 4 | 旧 4 条朴素越权全为否定/引证语境；绑定真锚 |`（本轮实读）。

**真伪**：伪 FAIL。四处全为否定 / 引证 / 排除清单，无一处**真断言**。

### 3.4 ④ 缺 SHA256 绑定行（严格 0）= **伪 FAIL（语义层）＋ 附带格式合同错配**（如实登记，不掩盖）

**复现证据**：RUN A `"bindings": 0`；RUN B `"bindings": 0`；编排方【门禁重跑】`bindings_strict: 0 / bindings_loose: 1`。

**原句**（`CANDIDATE_RESIGN_YES_V2.md:122` 逐字）：

```
**被核对象（审阅回件 `lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md`）SHA256 = `ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e`，字节数 = 11948**——复核回件绑定值，撰写员本轮 hashlib 实算相符（`_rw_fpcheck` MATCH 行）。
```

**逐字符断点**（本轮 `_n4g_writer_out.json` 的 `fail4` + 判定员 `_n4g_exact_out.json`）：

| 项 | 实值 | 后果 |
|:--|:--|:--|
| 「被核对象」与「SHA256 =」之间 | 插 70 字符括注 infix `（审阅回件 \`lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md\`）`，且 `space_between_被核对象_and_SHA256 = false` | 历史正则 `被核对象 SHA256\s*=`（`_n4g_gate_verbatim.py:20`）失配 → **严格 0** |
| 64 位 hex 前后 | 各一个反引号 U+0060（`hex_backticks: true`） | 本轮铁律「中间不得插入…反引号」明禁；历史正则自带 `` `? `` 容许 |
| 「，字节数 = 11948」 | 在场 | 绑定要素完整 |
| 宽松口径 `被核对象[^。\n]{0,160}?SHA256…` | `loose_count: 1` | **宽松 1** |
| `iron_tight_count`（本轮铁律 `被核对象 SHA256 = [0-9a-fA-F]{64}`） | 0 | 按本轮字面格式不合 |

判定员 RUN 7（`_n4g_exact_out.json:10-33`）四个变体实测：只删 infix → 严格仍 false（连空格都没了）；只去 hex 反引号 → 严格仍 false；删 infix 并补空格 → 严格 true 但 tight 仍 false；规范整行 → 严格与 tight 均 true。

**绑定是否真实（决定性）**：实装 R11（`_g7_predicates.py:151-222`，容忍 ≤160 字符路径隔断 + 引用锚现盘重算）在本轮 `improved_predicates.r11` 给出 `r11_problems: []`、1 条 binding：`declared = ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e`、`path = lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md`、`match: true`、`recomputed` 同值、`bytes: 11948`。判定员 `_n4g_predicates_out.json:90-101` 同值。本轮另实算该引用锚文件 sha256 亦为 `ee27b4ca…3102e` / 11948 B（`_n4g_writer_out.json.fail4`）。**绑定语义完全成立，只是书写与格式合同不一致**。`lead/gate_postmortem_20261109/GATE_LITERAL_MATCH_POSTMORTEM.md:73` 实读：「真件 …:122（路径括注+反引号 hex+加粗）：本会话紧邻正则解析 **False（FP 现场复现）**、宽容解析 True、路径抽出后现盘重算 ee27b4caf4fa…/11948 **MATCH=True** … 口径分歧属合同-门禁不一致（现行铁律禁 infix），修法=合同参数显式化」。

**谁让步**：历史 `GATE_CODE` 正则自带 `` `? ``（容许反引号），说明 2026-11-08 合同只要求「被核对象」与「SHA256」紧邻；本轮（2026-11-09）铁律把格式收紧到禁一切 infix / 反引号，是**后加的更严合同**。用后加合同追溯判先前交付件属合同版本错配。

- **主判**：应门禁让步——采用已实装的 R11 宽容匹配 + 引用锚回验，交付件零改动（`GATE_R9R12_REGRESSION.md:159` 已判 PASS）。据此 ④ 在语义层是伪 FAIL，四条 FAIL 全为门禁判据误报。
- **不掩盖另半边**：若来源会话坚持按本轮铁律**字面**追溯执行，则 ④ 不是纯词表问题，`:122` 确实不合规，须按 §5 改一行；此时 N-5 就绪度总结论由 (b) 转 (c)。两种口径的后果都登记在此，不两边讨好。

### 3.5 四条 FAIL 汇总

| # | FAIL 原文 | 真伪 | 定性 | 责任 / 依据 |
|:--|:--|:--|:--|:--|
| ① | 缺要素 不签 APPROVE_SCOPE | **伪** | 语义在场两处，反引号使 7 连字缺字面 | 门禁词表过严 → R9 归一化（`_g7_predicates.py:31-65`） |
| ② | 含越权断言 可应用母本 | **伪** | 全文恰 1 处，在 `:155` 排除清单，非断言 | 门禁忽略断言极性 → R10+R12；更正编排方背景 |
| ③ | 含越权断言 放行 N-5 | **伪** | 4 处全为否定 / 引证 / 排除清单，非断言 | 同 ②；`_n4gv_polarity_out.json` assertion_count=0 |
| ④ | 缺 SHA256 绑定行（严格 0） | **伪（语义）**／**格式真不合后加铁律** | 绑定真实、R11 回验 `match: true`；70 字符 infix + hex 反引号使紧邻正则失配 | 主判：门禁紧邻正则 → R11；条件分支见上 |

RUN 3 与本轮 `_n4g_writer_out.json` 同值：`naive_gate_problems` = 4 条，`improved_gate_problems = p9+p10+p12+p11 = []`。已实装谓词在同一文件上四条全消。

---

## 4 「声明不做 X 必然要提到 X」张力的正面处理与谓词层影响

### 4.1 张力（门禁自相矛盾，正面回答，不两面讨好）

本件的核心内容就是「声明我不做 X」：

- 历史 payload IRON 第 8 条（实跑 `grep -n` 输出 `.zcode/workflow-runs/dwfrun-af6f3c87-…mjs:9` 内字面）：`"★ 本任务不签 APPROVE_SCOPE（属来源会话签发人）、不应用母本、不放行 N-5。签署性质仅限「候选语义层YES」。"`
- 同一 payload 的撰写交付指令要求 §6 写「越权断言排除声明」，REVIEW_RULES 第 ⑥ 项要求「检查 resign 结论有没有被拔高…有没有出现「可应用」「放行 N-5」这类越权断言」。

要表达「不做 X」，**必然要提到 X 这个词**（`不签 APPROVE_SCOPE`、`不应用母本`、`不放行 N-5`、`:155` 的排除清单）。而朴素门禁 `_n4g_gate_verbatim.py:14-15`：

```
for bad in ['可应用母本','放行 N-5','已应用','已签 APPROVE_SCOPE']:
 if bad in t: P.append('含越权断言 '+bad)
```

用全文子串判违规，等价于要求文件一次都不出现禁词——**也就是要求它无法表达被强制要求的声明**。一边要求写排除声明，一边把排除声明里的词判成越权：门禁此处自相矛盾。

### 4.2 立场：禁词检查须靠「断言极性」，不靠「零出现」

1. 「不 X」与「X」真值相反；把二者同罪，门禁丧失最基本的区分能力。
2. 这不等于放松：R10（否定 / 短引证豁免）+ R12（双重否定构式守卫）组合既豁免排除性声明，又拦双重否定与裸断言。RUN 5 合成样本（判定员 `_n4g_r10gap_out.json`，本轮实读）：S6「本 YES 已获批准，可应用母本，放行 N-5。」→ 两词正确判 `assertion` 被拦住；`GATE_R9R12_REGRESSION.md:153` 实读「TV1-TV6 全 FAIL…六种真违规形态零放走」。
3. 修法应补「清单 / 词表 / 排除项」语境识别与反引号代码跨度识别，而不是把「不 X」改写成不写。
4. **真断言**一旦出现（如「本 YES 已获批准，可应用母本」）必须仍被拦。

### 4.3 谓词层影响（如实登记 R10 仍有漏类，不夸大）

RUN 5（`_n4g_r10gap_out.json`，本轮实读）显示 R10 只认两个豁免触发（`_g7_predicates.py:69-111`：24 字符子句窗内否定词、「」≤80 字符短引证跨度），缺「显式清单 / 词表」与「反引号代码跨度」两类数据语境：

- S3「…凡出现任一表述则本 YES 立即作废：可应用母本 / 放行 N-5。」→ 两词误报 `assertion`（否定词出 24 字窗）；
- S5「- 越权词表：可应用母本；放行 N-5；APPROVE_SCOPE 已签。」→ 两词误报 `assertion`；
- S4「门禁 BAN 清单为 \`可应用母本\`、\`放行 N-5\`、\`已签 APPROVE_SCOPE\`，均不得出现。」→ 第三词误报 `assertion`（反引号代码跨度不视为数据语境）。

即本件 R10 的 0 problems 是**脆弱的正确**：`:155` 恰好同时带「无…不出现」与「」两个触发条件才全豁免。`GATE_R9R12_REGRESSION.md:207` 实读已登记「R10 对本登记报告的自指误报 12 条…机制 = R10 引证豁免只认「…」短跨度，反引号代码跨度内的词表声明被当断言」；`:226` 建议「反引号代码跨度视为数据语境豁免越权词扫描；并把 24 字符窗邻近否定词误豁免改为子句内同短语判定」。

**本件自身的活体自指（本轮实跑，如实登记）**：`python -I -X utf8 -c "…import _g7_predicates as g7; t=…N4_GATE_VERDICT.md…; g7.r10_scan(t,['可应用母本','放行 N-5','已应用','已签 APPROVE_SCOPE']); g7.r12_scan(…)"` 输出 `R10 problems = 22 R12 problems = 0`、`kinds = {negation: 16, quote_mention: 9, assertion: 22, double_neg: 0}`、总命中 47。逐处打印上下文确认 22 条 `assertion` 全部落在：① 门禁复现输出的 JSON / 代码块（如 `"problems": ["…含越权断言 可应用母本…"]`）、② 本件 §1 的「**不宣告 N-5 可应用**：…签了语义层 YES ≠ 可应用母本 ≠ 放行 N-5」（排除性声明）、③ 引述 `:155` 排除清单与 COUNT 对账、④ §4 引用的朴素门禁 `for bad in ['可应用母本','放行 N-5',…]` 词表、⑤ RUN 5 合成样本 S3/S6 转述。无一为**真断言**——全部是数据语境 / 代码跨度 / 排除清单 / 引证，正是 §4.2 与 `GATE_R9R12_REGRESSION.md:207` 登记的 R10 漏类在本判定件自身复现。本件不是 `CANDIDATE_RESIGN*` 交付件、不在门禁 `wd.glob('*.md')` 候选集内，故此自指结果不影响四条 FAIL 的结论；但它是「零出现判据不可用」的又一活体证据，故如实登记而不隐藏。

**结论**：四条 FAIL 的修法在谓词层是把该域 `GATE_CODE` 的四个朴素判据替换为 R9（要素包裹归一化）/ R10（极性豁免）/ R12（双重否定守卫）/ R11（绑定行路径隔断容忍 + 引用锚回验）的组合，并补上述两类语境。RUN 3 已在同一文件上实装验证 `improved_gate_problems: []`；但**替换进该域门禁并实跑复判**不属本任务（历史 payload 绝对只读），须由有权会话另派。本节只给谓词层影响，不宣告门禁已通过。

---

## 5 N-5 就绪度结论 · 未满足前置 · 最小改动清单 · 引用面排查

### 5.1 N-5 就绪度：三选一 → **判 (b) 不能，但只需改门禁**

三选一定义：**(a)** 可以进入 N-5 应用；**(b)** 不能，但只需改门禁（交付件语义无缺陷）；**(c)** 不能，且交付件本身需要改。

**判 (b)**：

- 四条 FAIL 全是门禁判据误报（§3）；本轮与判定员 RUN 3 的改进谓词在同一文件上 `improved_gate_problems: []`；`GATE_R9R12_REGRESSION.md:159` 已把本件登记为 PASS。交付件语义无缺陷。
- 但「门禁通过」是**门禁层**事实，必须把该域 `GATE_CODE` 换成 R9/R10/R11/R12 并实跑复判才能算数，不能由本判定件口头宣布；历史 payload 属铁律绝对只读、本任务不得改，故本任务只给结论、不落地替换 → **不是 (a)**。
- **(c) 只在一种条件下成立**：来源会话坚持用 2026-11-09 后加铁律的**字面格式**去追溯判 2026-11-08 交付件，则 ④ 需改 `:122`（改法见 §5.3，不执行），总结论转 (c)。

### 5.2 与本件无关、仍未满足的 N-5 前置条件（签了 YES ≠ 可以改母本）

逐条给依据行，不用「已核对」概括：

1. **来源会话签发人签发 `APPROVE_SCOPE`**：`lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md:49` 实读「独立审阅者签候选 YES、来源会话签发人签 APPROVE_SCOPE，均以 N-1 记录格式绑定任务书与基线／候选哈希；身份、任一规则或版本缺失则任务书不生效」；交付件 `:159-160` 自列「来源会话签发人签发 `APPROVE_SCOPE`…本文不代签」。本件只是那个 YES，不含此签。
2. **有权签发人对甲/乙方向正式确认并补登**：`lead/direction_ruling_20261108/RULING_DIRECTION.md:23` 实读「仅保留为**待有权签发人确认的方向意见**，不宣告 N-4 正式绑定已经生效」；`:25`「本次不补登、不签署、不应用」；`:66`「技术方向乙；正式替代和绑定待有权签发，未生效」。交付件 `:161` 同列。
3. **有权来源会话派发 N-5 新任务书 + 正式写域**：`NEXT_STEPS_20261106.md:53-58` 实读（`:55`「持 N-4 有效新任务书的执行者…」、`:58`「仅限有权来源会话签发的新任务书之正式写域…缺任务书是任务派发阻塞」）、`:119`「身份未落实是派发阻塞，不是让用户再次授权的一般权限阻塞」；交付件 `:162`。
4. **实施侧用户当轮明示**：`RULING_DIRECTION.md:7` 实读「N-5 正式应用、N-10 实施采集…均不得由裁决代替用户当轮明示」、`:25`「N-5 实施另待用户当轮明示」、`:66`；`NEXT_STEPS_20261106.md:98`「任何依赖 E3／MiniDump／SuspendThread／StackWalk／真机或活进程的实施须用户当轮明示」。与「一般授权已具备、无需再次索取同一一般授权」（`:50`、`:58`）不矛盾——缺的是具体实施明示与任务书，不是一般权限。
5. **签发人身份 / 任务书编号 / 版本绑定入 N-1 记录**：`:49`、`:119`（「该会话派任务时须把自己的实际 session/run ID、任务 ID、签发角色写入 N-1 记录及 N-4 任务书」）。
6. **运行时与真机验证 9 项未验**：交付件 `:142`（T1/T2/T5、整趟行为、母本 6 包装函数运行时行为、RULING D24/D25 复读、补登件定位、复核回件落盘件）、`:163-168`（V2:91 措辞等）自列。零真机约束下的固有未验。
7. **门禁层本身**：该域 `GATE_CODE` 现仍报 4 FAIL（RUN A stdout `"ok": false`），修正谓词已实装但未替换进该域门禁。

### 5.3 重签件若需改的最小改动清单（**只列，一个字节未执行**）

> 前提：仅在来源会话坚持按本轮铁律字面、或坚持「零出现」口径时才需要。以下均为「应当改成什么」。

**改动点 A（针对 ①，可选）**：`:15`、`:150` 的 `不签 \`APPROVE_SCOPE\`` → `不签 APPROVE_SCOPE`（去反引号）。改后字面 7 连字在场，语义无损，与 `NEXT_STEPS_20261106.md:49` 书写一致。

**改动点 B（针对 ④，核心）**：`:122` 整行替换为规范格式，逐字：

```
被核对象 SHA256 = ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e，字节数 = 11948
```

即删 70 字符括注 infix、删 hex 前后反引号、删外层 `**`，保留「，字节数 = 」与数字。判定员 `_n4g_exact_out.json:28-33` 实测该行 `gate_strict: true`、`iron_tight: true`。**更低侵入替代**：`:122` 原行不动，其后新增一行上述规范行；实测整文件 `gate_strict: 1`、`iron_tight: 1`，且保留原括注路径信息（推荐此式，若必须改件）。

**改动点 C（针对 ②③，不推荐，仅登记备选）**：不要删「可应用母本 / 放行 N-5 / 不放行 N-5 / 不应用母本」这些词——删了就无法表达排除声明，恰是 IRON 与 §6 的必写内容。若来源会话坚持「零出现」，唯一自洽做法是把排除声明换成不含禁词的等价表述（如 `:155` 改为「审阅/复核回件不得出现任何超出语义层 YES 的断言」、`:17` 改为「N-5 仍待有权来源会话派发新任务书」），但这会削弱可核验性，**不推荐**。

**改动后 SHA256 / 字节（本轮 `_n4g_writer_verify.py` 内存实算，均未落盘到被核件；与判定员 `_n4g_exact_out.json`、复核员回件逐项对账）**：

| 落地方式 | SHA256 | 字节 | 出处一致 |
|:--|:--|--:|:--|
| 原件（未改） | `1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b` | 23129 | 三方一致 |
| 仅替换 `:122`（B） | `abf90ca74dc886ef315beeb9306019120b7884fe10b667723db77e67e17e47ec` | 22944 | 判定员/复核员/本轮一致 |
| `:122` 后插入一行（B 替代式） | `50925ee9d183213831d9fd26b7d07007a8f6d7ba65867e19805efcf6814f1dce` | 23236 | 判定员/复核员/本轮一致 |
| 文件尾追加（判定员口径 `t+'\n'+CANON+'\n'`） | `23c264830de6f5177d1ba732037941deec730bec9623c33479fffea237f3e675` | 23237 | 判定员 `_n4g_exact.py:41`，本轮一致 |
| 文件尾追加（复核员口径，尾空元素前插 / `t+CANON+'\n'`） | `cf14fe84952b4ef81c136fbcdf93bff0dee3b7648d1b2b92325c6d2a148631e7` | 23236 | 复核员回件，本轮独立实跑复现 |
| 倒数第一行前插入（本轮另一口径） | `6caa6c75becbb7c270724da368843c522dfc8e7175773105d9d05b8b7cfa11cc` | 23236 | 本轮新算，仅登记口径差 |
| **A+B 同时改**（判定员标「未验」） | `194a43c29a31ebfee69ca4760d0326a8d20d2fbe1948ba00a6f1503d8abc7159` | 22940 | 复核员内存算 + 本轮实算一致，补上「未验」 |

三种「追加一行」口径（23237 / 23236 / 23236）差异来自空行与插入位置，非伪造；核心三种落地方式的哈希三方完全一致。

### 5.4 改动后指纹变化的引用面排查（**41 件逐个排查**）

判定员 `_n4g_refs.py` 基线圈定 41 件 = 39 件完整 hash（19 硬绑定 + 20 审计/文字快照，含判定写域 4 件）+ 2 件短哈希截断。本轮 `_n4g_writer_refs41.py` 实跑输出 `_n4g_writer_refs41.json`：`baseline_41_count: 41`、`all_41_hash_refs_still_present: true`、`live: 19`、`audit: 20`、`short: 2`。**逐件**（`文件:行` = 首个 hash 命中行；完整清单落 `_n4g_writer_refs41.json` 的 `baseline_41.rows`）：

**A. 硬绑定候选 19 件**（把该 hash 当期望值比对，改后必然 MISMATCH，须同步改期望值；是否真在运行时读取**未逐件验**）。逐件：

| # | 文件:行 | # | 文件:行 |
|--:|:--|--:|:--|
| 1 | `lead/counterpart_fix_20261109/_cf_fp_check.py:24` | 11 | `lead/gate_rejudge32_20261109/_rj_orchestrator_replay_out.json:1` |
| 2 | `lead/counterpart_fix_20261109/_cfv_fp_check.py:52` | 12 | `lead/matrix_ab_ruling_20261109/_rv_decision_model_20261109.py:31` |
| 3 | `lead/gate_doc_name_fix_20261109/_dn_regate_out.json:532` | 13 | `lead/matrix_row5_20261109/_r5c_fingerprint.py:20` |
| 4 | `lead/gate_fp7_20261108/_g7_fp_check.py:12` | 14 | `lead/matrix_row5_20261109/_r5v_fingerprint.py:23` |
| 5 | `lead/gate_fp7_20261108/_g7_reverse_validate.py:163` | 15 | `lead/oldwording_sweep_20261109/_ow_raw_hits.json:12391` |
| 6 | `lead/gate_fp7_20261108/_gv_fp_check.py:20` | 16 | `lead/n4_gate_verdict_20261109/_n4g_binding_out.json:430` |
| 7 | `lead/gate_r9r12_20261109/_g9_regression_out.json:3896` | 17 | `lead/n4_gate_verdict_20261109/_n4g_exact_out.json:53` |
| 8 | `lead/gate_r9r12_20261109/_g9v_regress_out.json:1299` | 18 | `lead/n4_gate_verdict_20261109/_n4g_probe_out.json:17` |
| 9 | `lead/gate_rejudge32_20261109/_rj_baseline_rerun.json:532` | 19 | `lead/n4_gate_verdict_20261109/_n4g_refs.py:5` |
| 10 | `lead/gate_rejudge32_20261109/_rj_double_track_out.json:931` | | |

（19 件唯一、无重复；`_n4g_writer_refs41.json` 的 `baseline_41.rows` 中 `role=硬绑定候选(live)` 逐件同此表。）

**B. 审计 / 文字快照 20 件（改后陈述与现盘不符，须登记或重跑，非必须改字节）**

`lead/counterpart_fix_20261109/COUNTERPART_FIX.md:42`、`_cf_counterpart_vs_tighten_20261109.md:34`、`lead/gate_doc_name_fix_20261109/_dnv_regate_rerun.txt:532`、`_dnw_regate_rerun.txt:532`、`lead/gate_fp7_20261108/GATE_FALSE_POSITIVE_5_6_7.md:27`、`_g7_reverse_validate_out.txt:70`、`lead/gate_postmortem_20261109/GATE_LITERAL_MATCH_POSTMORTEM.md:23`、`_pm_hash_verify_out.txt:1`、`_pm_postmortem_20261109.md:12`、`_pml_hash_out.txt:1`、`_pmv_hash_check_out.txt:1`、`lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md:28`、`_ab_RULING_MATRIX_AB_20261109.md:16`、`lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md:30`、`_r5_row5_linkage_assessment.md:14`、`_r5c_fingerprint_out.txt:11`、`_r5v_fingerprint_out.txt:10`、`lead/text_fix_unified_20261109/UNIFIED_TEXT_FIX.md:50`、`_uf_UNIFIED_FIX_LIST_20261109.md:21`、`lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md:31`。

**C. 短哈希截断 2 件**：`lead/gate_doc_name_fix_20261109/_dnv_patch36_run_out.json:522`（`docSha256_head "1950d3f31048b9a0"`）、`lead/gate_doc_name_fix_20261109/_dnw_template_out.json:970`（`sha_head "1950d3f31048"`）。

**D. 不受影响（本轮实跑）**：两件台账全文 grep 无 `1950d3f3`、无 `CANDIDATE_RESIGN`（`_n4g_writer_out.json.refs.ledgers` 三项全 false；末次零漂移复算 MATCH）；`.zcode/workflow-runs/` 全部 mjs 中完整 hash = **0 件**（`grep -l "1950d3f3…5925b" .zcode/workflow-runs/*.mjs` 无输出），仅 **7 件**按文件名引用（`_n4g_writer_refs41.json.mjs.name_only`，文件名不变即不受影响，且历史 payload 绝对只读；原始产出 payload 的 `FP_CODE` 是 live hashlib 计算、未硬编码）；2 件沙箱同名副本（`_dnv_sandbox36/`、`_dnw_sandbox/`）是历史快照、同指纹 `1950d3f3…5925b / 23129`，不应跟着改（改了反破坏可复现性）。

**E. 本轮复扫差异（如实登记，计数随并发写入动态增长）**：`_n4g_writer_refs41.json.rescan_now` = 完整 hash 55 件、短 hash 3 件。相对 41 件基线新增完整 hash 16 件（`lead/gate_rejudge32_20261109/_rjv_regate_fresh.json`、`_rjv_step2_out.json` 两件为其他会话新写；其余 14 件均在本判定写域 `lead/n4_gate_verdict_20261109/`，含判定员 `_n4g_*`、复核员 `_n4gv_*` 与本轮 `_n4g_writer_*` 输出件——它们引用的是**原件**指纹、自身被自己扫到，不构成新的外部绑定）；新增短 hash 1 件 `lead/gate_rejudge32_20261109/_rjv_step2_stdout.txt:242`（本轮实读该行 `…bytes=23129 sha=1950d3f31048`）。`out/` 全树 `rglob` 两次在本机挂起（判定员与复核员均记此坑），本轮改做 `find out/ct out/re_work out/forge1_verify -maxdepth 6 -type f … | xargs grep -l -E "1950d3f3|CANDIDATE_RESIGN_YES_V2"`，三段均 **0 命中**——`out/` 覆盖不穷尽，如实记为未验。

---

## 6 复核回件 · 绑定行 · 纪律声明 · 未验项

### 6.1 复核 verdict 如实登记

- **交付件自身的复核 verdict = `confirmed`**（`CANDIDATE_RESIGN_YES_V2.md:124` 实读：「**复核 verdict = confirmed**（非 refuted / partial，故记 confirmed，不标 unconfirmed）」；其被核对象是审阅回件 `_cs_semantic_review_GLM_20261108.md`）。
- **编排方【复核】回件对判定员工作的复核 verdict = `confirmed`**，`ranCommands: 32`，「8 项复核点全部通过，无 refuted 触发条件」，含绑定行 `被核对象 SHA256 = 1950d3f3…5925b，字节数 = 23129`。
- 两条均非 refuted / partial，**均不标 unconfirmed**。本判定件（`N4_GATE_VERDICT.md`）是本轮新撰写、尚未经独立复核，此点记入 §6.4 未验。

### 6.2 本判定件的复核回件绑定行（严格格式）

被核对象 SHA256 = 1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b，字节数 = 23129

（=`CANDIDATE_RESIGN_YES_V2.md` 现盘 hashlib 实算；末次零漂移复跑 `MATCH 1950d3f3…5925b / 23129`。格式 = 「被核对象 SHA256 = 」+ 64 位 hex + 「，字节数 = 」+ 数字，中间无路径 / 括号 / 星号 / 反引号 / 额外空格。）

母本逐位核对绑定行（同格式，供 §2 校验）：

被核对象 SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508

### 6.3 纪律声明

- **未改重签件**：`CANDIDATE_RESIGN_YES_V2.md` 全程只读。末次复算 `MATCH 1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b / 23129`（写作完成后实跑 `python -I -X utf8 -c "…hashlib…"`，stdout 四行 MATCH）。§5.3 全部改法只在内存算哈希，未落盘到该件。
- **未改母本**：`MATCH 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636 / 399508`。
- **未改受保护只读件**：`lead/n4_yi_final_20261108/` 全部件、`lead/b2b_candidate_lf_20261107/`、`lead/b2b_design_20261106/STATE_MATRIX.json`、`lead/direction_ruling_20261108/`、`.zcode/workflow-runs/` 全部 mjs、两件台账（`MATCH 3765eddb… / 52419`、`MATCH 2baa0de4… / 759518`）。`git status --porcelain -- <受保护路径>` 实跑输出仅初始快照的 `MM lead/GOAL_THREE_TARGETS_20261018.md`、`MM lead/PENDING_DECISIONS.md` 与 4 条 `??` 目录，`git log -1 --oneline HEAD` = `2657458`（与会话起始一致）。
- **未代签 `APPROVE_SCOPE`、未宣告 N-5 可应用、未宣告母本可改**；未替来源会话签发任何东西。
- 未跑任何真机 / 采样 / 注入 / 动态内存解析；未 commit、未 push。全部写入仅落 `lead/n4_gate_verdict_20261109/`，辅助件前缀 `_n4g_writer_*`，写域内 `find … -name "__pycache__" -o -name "*.pyc"` 无输出（脚本设 `sys.dont_write_bytecode = True`）。

### 6.4 未验项（如实，不补造）

1. 19 件 `live_binding_candidates` 是否**全部**在运行时真读取该期望值——只按扩展名 + 比对语义键初筛，未逐件执行（`_n4g_refs_out.json:69` note 已登记，本轮未补）。
2. `out/` 全树引用覆盖不穷尽（`rglob` 挂起坑，只做三目录 maxdepth-6 定向扫描 0 命中）；Git 历史（历史 commit 中的引用）未查。
3. Git 历史引用未查；本轮未跑 `git log --all -S` 类全史检索。
4. 本判定件 `N4_GATE_VERDICT.md` 自身尚未经独立复核（编排方【复核】复核对象是判定员 `_n4g_VERDICT.md` 与本轮上游材料，非本件）。
5. R10 漏类（清单 / 词表 / 反引号代码跨度）的正式修法未落地（§4.3）；该域 `GATE_CODE` 未被替换、未在替换后实跑复判——故不宣告门禁已通过。
6. 一次 Bash 组合命令因 `out/` 大树 `rglob` / `find out` 在 120 s 内未完成而被移入后台并 `TaskStop` 终止；其前半段（逐字门禁复跑 + `find lead out -name "CANDIDATE_RESIGN*"` 三行）已从 stdout 日志实读取得，三副本指纹改用目录限定 `python -I -X utf8 -c "…(R/'lead').rglob(…)…"` 补跑成功。不影响任何结论。

---

*本文由 N4 判定件撰写员于 2026-11-09 撰写；全部断言可追至本轮实跑命令输出或「文件:行」实读；拿不到者已记「未验」。判定性质仅限「门禁判据真伪 + N-5 就绪度 + 不执行的最小改动清单」；未改重签件、未改母本、未代签、未宣告 N-5 可应用。*
