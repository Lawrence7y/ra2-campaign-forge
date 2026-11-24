# GATE_FALSE_POSITIVE_5_6_7.md — 门禁误报第 5/6/7/8 类：增量补丁与反向验证

撰写：门禁补丁撰写员（dynamic workflow 子代理）。日期：2026-11-09。
本件为最终交付件，谓词本体 = `_g7_predicates.py`（SHA256 = `02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120`，字节数 = 11743），插桩说明 = `_g7_patch.md`（SHA256 = `9a7f5b9d2f7b87f8cc5baf09205322fb5507552ff3834ca28bf772d0417df849`，字节数 = 12647）。
文件名沿用编排方指定的 `GATE_FALSE_POSITIVE_5_6_7.md`；实际覆盖**四**类（第 5/6/7/8 类，fixedCount=4）——形式化回件如实报 4 而非 3：派发方回件串按 fixedCount/4 输出、其门禁要求 R9–R12 四谓词齐备。

## 1 目的与边界

**目的**：修复既有门禁在四类真实交付件形态上的误报——第 5 类（带反引号/引号包裹标识符判缺要素）、第 6 类（否定式自指被当越权断言）、第 7 类（否定句含完成时词被当越权断言）、第 8 类（绑定行路径隔断判缺绑定）。只给**增量补丁**：四个新谓词 R9/R10/R12/R11 与插桩位置，不重写模板。

**边界（本轮硬约束，全部遵守）**：
- 零真机：未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存。
- 零采样代码：全部谓词为静态文本/哈希检查，仅 `import re / hashlib / pathlib`，无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。
- **绝对只读**：`lead/gate_template_20261108/`、`lead/gate_validate_20261108/`、母本 qc151_trip.py、两件台账零改动——本轮实跑指纹核对 9/9 MATCH（见 §2 与 §5 S7）。
- 唯一写域 = `lead/gate_fp7_20261108/`；未 commit、未 push。
- 引用规范：本文每个结论均锚到「实跑命令+输出」（本轮会话内执行）或「文件:行」（本轮逐字抽查）；拿不到的写**未验**，见 §4/§6。

## 2 上游指纹

九件上游件指纹实测（命令：`python -I -X utf8 _g7_fp_check.py` → 7/7 MATCH；`python -I -X utf8 _gv_fp_check.py` → protect_ok=9 protect_bad=0；本轮两条命令均实跑，输出在案）：

| 文件 | SHA256 | 字节数 | 状态 |
|---|---|---|---|
| lead/gate_template_20261108/GATE_TEMPLATE_FIXED.py.txt | `543e79184258f9f96517fdc8d61d42e46a7cd544f11ce0ab3b78d9fd505e9abe` | 28128 | MATCH |
| lead/gate_template_20261108/GATE_FALSE_POSITIVES.md | `2011cb866e8a6e857c7c3fcd08e7270e0cc062f8eed47610fa025bf15b5f3244` | 25841 | MATCH |
| lead/gate_validate_20261108/GATE_TEMPLATE_REGRESSION.md | `c9093cab4f708d3f2bfd721095e9d8458818dd9d36019d996fd952b24e1a5a19` | 31507 | MATCH |
| lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md | `1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b` | 23129 | MATCH |
| lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md | `724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e` | 45719 | MATCH |
| lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md | `c0dfb0d17edab4d0d89c43dc48bce4b84354fd13bd89cae7277aa15e82cf65f2` | 54351 | MATCH |
| lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md | `6d88fc9241e31e0d6ed7af4988ab712c8e0f4e4caa9d3d92e4f736bf23f46395` | 21690 | MATCH |
| lead/PENDING_DECISIONS.md（台账） | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 | MATCH |
| lead/GOAL_THREE_TARGETS_20261018.md（台账） | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 | MATCH |

工作域内核心工件实测：`_g7_predicates.py` = `02c17e49…51120`/11743（与形式化回件声明一致）；`_gv_subject.json`（形式化回件逐字落盘）= `84e0a3b6894ddf1a8fb3a19f09415a482c5e2df6e1e6d36edb41a35e8c7a1b8b`/7709（与复核回件绑定一致）。命令：`python -I -X utf8 -c "import hashlib; …"`（本轮实跑）。

## 3 四类误报的机制归纳与实测发生率

### 3.1 实测发生率（命令：`python -I -X utf8 _g7_probe_repro.py`，本轮复跑，输出 `_g7_probe_repro_out.txt`；逐项与编排方派发实测一致）

探针定义逐字取自派发载荷 dwfrun-fed3c2a2 的 PROBE_CODE（`_g7_probe_repro.py:14-19`）：越权词族 BAD_BAN=['已生效','可应用母本','放行 N-5','已入账','已追加']；否定语境=命中点前 24 字符窗内 `re.search(r'(不|无|未|非|禁|勿|否决|排除|不宣告|不得)')`；三种绑定正则 bind_naive=`被核对象 SHA256\s*=\s*[0-9a-fA-F]{64}`（hex 不许反引号）/ bind_relaxed=`被核对象[^。\n]{0,160}?SHA256\s*=\s*`?…{64}` / bind_any=`SHA256\s*=\s*`?…{64}`。

| 件（字节） | 朴素计数（naiveHits） | 否定语境计数（negated） | bind_naive | bind_relaxed | bind_any | APPROVE_SCOPE 包裹形态 |
|---|---|---|---|---|---|---|
| CANDIDATE_RESIGN_YES_V2.md（23129） | 已生效 1、可应用母本 1、放行 N-5 4、已入账 0、已追加 0 | 1 / 1 / 3 / 0 / 0 | **0** | 1 | 1 | 裸写 2、反引号 3、拆断 0 |
| LEDGER_APPENDIX_DRAFT.md（45719） | 已生效 3、其余 0 | 3 / 0 / 0 / 0 / 0 | **0** | 1 | 10 | 裸写 1、反引号 5、拆断 0 |
| OBSERVATION_PROTOCOL_SPEC.md（54351） | 全 0 | 全 0 | 1 | 1 | 2 | — |
| C97_SCOPE_RECHECK.md（21690） | 全 0 | 全 0 | 2 | 2 | 2 | — |

### 3.2 逐类机制归纳（机制 → 真实件证据行，全部本轮逐字抽查）

**第 5 类（带反引号标识符判缺要素）**：机制 = 门禁字面等值匹配对包裹/拆断零容忍。关键仲裁事实：**裸子串门禁其实不漏反引号/全角包裹形态**（包裹符不与 token 相交；实测 CANDIDATE 裸写 2/反引号 3、LEDGER 裸写 1/反引号 5，两种形态都在场，naive 均命中）。真漏判只发生在两形态：①门禁字面量本身带包裹符（从任务书行文复制进词表，如既有件 `lead/gate_validate_20261108/_gv_gates/1552e9fe.py:9` 词表整体含 `'APPROVE_SCOPE'`）——S2 在 CANDIDATE 实跑复现 `['缺要素 「APPROVE_SCOPE」', …]`；②要素被 Markdown 换行拆断（TV7 实跑复现）。**第 5 类原始误报件未定位 = 未验**（机制两形态均已复现并修复，见 §4 R9 与 §5）。

**第 6 类（否定式自指被当越权断言）**：机制 = 越权词字面扫描把自指引用当断言，且单纯否定回看不完备。真实命中：CANDIDATE:150「本 YES **不签 `APPROVE_SCOPE`**…**不放行 N-5**；不断言…」（否定语境）、CANDIDATE:155「**无越权断言**：审阅/复核回件不出现「可应用母本 / 放行 N-5 / APPROVE_SCOPE 已签」类断言」（两个独立否定短语）；LEDGER:146/:194「不宣告 N-4 正式绑定已生效」（否定句）。朴素计数 9 处命中、否定语境计数后 CANDIDATE 只剩 3 处裸命中——其中 CANDIDATE:130 翻案条款「…或回件出现「可应用/放行 N-5」断言，本 confirmed 即翻。」**无否定词**，是条件引用而非断言，需引证跨度豁免补足（R10 quote_mention）。

**第 7 类（否定句含完成时词被当越权断言）**：与第 6 类同机制，词形为「不宣告…已生效」（LEDGER:146/:194），naive 计数 3 处、否定语境计数后仍 3 处在窗内——既有编排式回看能豁免这三处，但豁免机制过度（见第 6 类 TV2 跨句污染与 §4 R12 反例）。

**第 8 类（绑定行路径隔断判缺绑定）**：机制 = 既有绑定行正则要求「被核对象 SHA256 =」紧邻（`_gv_gates/858e5e0b.py:11-12`：`B=re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?',t); if not B: P.append('缺 SHA256 绑定行')`），交付件真实绑定行被括注路径或长说明段隔断即漏。真实形态三种：CANDIDATE:122「**被核对象（审阅回件 `lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md`）SHA256 = `ee27b4ca…`」（路径隔断 → bind_naive=0，S2 实跑复现误报）；LEDGER:186「被核对象 = 核对回件文本（…存本写域 `_lv_subject_reply.txt`）——**SHA256 = `6888379a…`」（长分隔段，仅 bind_relaxed 命中）；C97:68/:69 与 OBS:366（紧邻形态，naive 本就命中）。反向陷阱：改全域 bind_any 会把指纹引证误当绑定——LEDGER bind_any=10 中仅 1 条是绑定行；TV4（仅指纹引证无绑定行）bind_any=1 会 PASS（S5 实跑）。

## 4 四个修正谓词（R9/R10/R12/R11）

谓词本体逐字在 `_g7_predicates.py`（hash 见 §2）；以下片段与该模块经 AST 级等价验证（命令：`python -I -X utf8 _gv_ast_equiv.py` → 唯一差异 r11_scan 首部 import 合并行写法；`python -I -X utf8 _doc_ast_align_check.py` → import 归一化 + docstring 剥离后六函数与常量全 ALIGNED_EQUAL，本轮实跑）。

### 4.1 R9 — 包裹归一化要素匹配（第 5 类）

```python
_WRAP_CHARS = "`\u00b4\u201c\u201d\u2018\u2019\u300c\u300d\u300e\u300f"
def r9_normalize(text):
    out, pos = [], 0
    for m in re.finditer(r"`([^`]*)`", text):
        out.append(text[pos:m.start()])
        out.append(m.group(1).replace("\n", "").replace("\r", ""))
        pos = m.end()
    out.append(text[pos:])
    n2 = "".join(out)
    return "".join(" " if ch in _WRAP_CHARS else ch for ch in n2)
def r9_element_present(text, token):
    if token in text: return True, "raw"
    if token in r9_normalize(text): return True, "normalized"
    return False, ""
def r9_check(text, tokens):
    problems, warnings = [], []
    for k in tokens:
        ok, layer = r9_element_present(text, k)
        if not ok: problems.append("缺要素 " + k + "（R9：raw 与包裹归一化文本双缺）")
        elif layer == "normalized":
            warnings.append("要素 %s 仅在包裹归一化后命中（raw 层缺字面）" % k)
    return problems, warnings
```

- **消误报理由**：N2 先拼接反引号跨度内的换行拆断（仅反引号跨度，防误拼接）；N1 把包裹字符（`` ` ´ “ ” ‘ ’ 「 」 『 』 ``）替换为**空格**（成词边界，杜绝跨词假拼接）。真缺要素 = raw 与归一化双缺，字面标准不放松。
- **会否漏判分析**：不会比现状更松——raw 命中在先；归一化只增加命中层不减少。真缺要素样本 TV1 实跑仍判 FAIL（S3）；包裹形态 TV7/TV7b 在 R9 下判在场且带 normalized 警告可见。**已知残余（未验修复）**：未包裹的裸拆断形态（「APPROVE_\nSCOPE」）N2 不覆盖——复核员 GV-K2 实跑 `problems=['缺要素 APPROVE_SCOPE（R9：raw 与包裹归一化文本双缺）']`，属第 5 类家族内残余；四真实件拆断形态实测 0 处（probe split=0），现网无影响。
- **实跑输出**（`_g7_reverse_validate_out.txt` S1/S6，本轮复跑）：`[S1] CANDIDATE R9 got=[]`、`[S1] LEDGER R9 got=[]`、`[S6] TV7 R9 判要素在场 got=[]`、`[S6] TV7b R9 判要素在场 got=[]`、`[S6] CANDIDATE R9 要素在场（raw 层）got=(True, 'raw')`。

### 4.2 R10 — 否定语境/引证语境豁免的越权断言扫描（第 6/7 类）

```python
NEG_RE = re.compile(r"(不|无|未|非|禁|勿|否决|排除|不宣告|不得)")
NEG_WINDOW = 24
CLAUSE_BREAK = "。！？；\n"
SPAN_RE = re.compile(r"「([^」\n]{0,80})」")
SELF_MARKERS = ("本件","本文","本候选","本 YES","本域","本回件","特此","现宣告","现批准","本节")
DOUBLE_NEG_RE = re.compile(r"(不得不|并非不|并不是不|不是不|无不|没有不|不无|不能不|不可不|未曾不)")
def r10_context(text, start, end):
    s = max(0, start - NEG_WINDOW)
    boundary = max(text.rfind(ch, 0, start) for ch in CLAUSE_BREAK)
    if boundary > s: s = boundary
    pre = text[s:start]
    neg_count = len(NEG_RE.findall(pre))
    dbl = bool(DOUBLE_NEG_RE.search(pre))
    in_span, span = False, ""
    for m in SPAN_RE.finditer(text):
        if m.start() <= start and end <= m.end():
            in_span, span = True, m.group(1); break
    marked = in_span and any(mk in span for mk in SELF_MARKERS)
    if not in_span:
        head = text[max(0, start - 12):start]
        marked = any(mk in head for mk in SELF_MARKERS)
    if dbl: kind = "double_neg"
    elif neg_count >= 1: kind = "negation"
    elif in_span and not marked: kind = "quote_mention"
    else: kind = "assertion"
    return {"neg_count": neg_count, "dbl": dbl, "in_span": in_span,
            "marked": marked, "span": span[:40], "kind": kind}
def r10_scan(text, assert_tokens):   # 消误报主谓词
    problems, warnings, hits = [], [], []
    for tok in assert_tokens:
        for m in re.finditer(re.escape(tok), text):
            ctx = r10_context(text, m.start(), m.end())
            hits.append({"token": tok, "pos": m.start(), "kind": ctx["kind"],
                         "neg_count": ctx["neg_count"], "in_span": ctx["in_span"]})
            if ctx["kind"] == "assertion":
                problems.append("越权断言 %s（R10：无否定、无引证语境）" % tok)
            elif ctx["kind"] == "negation":
                warnings.append("%s 处于否定语境（R10 豁免，窗内否定词 %d）" % (tok, ctx["neg_count"]))
            elif ctx["kind"] == "quote_mention":
                warnings.append("%s 为短引证跨度内提及（R10 豁免）" % tok)
    return problems, warnings, hits
```

- **消误报理由（三道防线）**：①回看窗 = min(24 字符, 当前子句)（句界 。！？；\n 截断）——前句否定词不再豁免后句正面断言（TV2 跨句污染复现后 R10 仍拦）；②短引证跨度（≤80 字符「…」）+ 自指标记检查——CANDIDATE:130 翻案条款是条件引用 → quote_mention 警告，带自指标的跨度（「本件放行 N-5」）不豁免；③双重否定构式不在 R10 豁免（交 R12 裁决）。
- **会否漏判分析**：真违规正面断言仍逐处判 FAIL（TV2 五处 got=5，S3；GV-A/B/C 三件新样本全 FAIL）。**残余**：真越权恰写成 ≤80 字符、无自指标的「…」短语时降为警告不 fail；NEG_RE 词表「排除/非」在 24 字符窗内可能误豁免（漏检方向，见 §6）。
- **实跑输出**：S1 detail CANDIDATE 六处命中 = 5×negation + 1×quote_mention（pos 10932，引证跨度），problems=[]；LEDGER 三处全 negation，problems=[]；`[S3] TV2 正面越权断言 ×5 → R10 fail got=5`；`[S4] TV2 编排式回看误豁免 ≥1（复现跨句污染漏判）got=True`（R10 子句边界修正后仍判违规）。

### 4.3 R12 — 双重否定守卫（第 6/7 类反例防线，接 R10 之后）

```python
def r12_scan(text, assert_tokens):   # 双重否定守卫，接在 R10 之后
    problems, hits = [], []
    for tok in assert_tokens:
        for m in re.finditer(re.escape(tok), text):
            ctx = r10_context(text, m.start(), m.end())
            if ctx["kind"] == "double_neg":
                problems.append("越权断言 %s（R12：回看窗含双重否定构式=肯定）" % tok)
                hits.append({"token": tok, "pos": m.start()})
    return problems, hits
```

- **双重否定反例（为何弃用否定词奇偶计数）**——两个方向都错，全部实跑：
  - **奇偶法制造新误报**：真实件 CANDIDATE:155「**无越权断言**：…不出现「可应用母本…」」命中点窗内恰 2 个否定词（两个独立否定短语，非双重否定）→ 奇偶法判肯定 → 判违规（复核员 `_gv_pred_check.py` D 组实跑：`CANDIDATE: 奇偶法判违规 2 处 ['可应用母本', '放行 N-5']；R10 判违规 0 处`）。
  - **奇偶法漏判**：TV3「复核方并未漏看：本件并非不宣告 N-4 正式绑定**已生效**。」命中 1（pos=245）窗内 3 个否定词（未/非/不）→ 奇偶数误豁免 → 漏判（复核员 D 组同轮实跑确认作者原话针对命中 1 逐字成立；其对 pos=299「不得不」两「不」隔「得」凑偶数会碰巧判违规，恰说明奇偶法不可靠）。
  - R12 改用**相邻构式表**（不得不|并非不|并不是不|不是不|无不|没有不|不无|不能不|不可不|未曾不）：TV3 实跑 `R12 拦下双重否定 ×2（单重否定对照不拦）got=2`；单重否定对照句「上一轮回件不宣告…」两谓词均不拦（GV-J `got=([], [])`）。
- **会否漏判分析**：构式表非穷尽——分离型「亦非不宣告…」（否定词不相邻）R10/R12 全 0 漏检（复核员 GV-L 实跑实证，与 §6.2 自报相符）；按语料增补构式。
- **实跑输出**：`[S4] TV3 编排式回看全部豁免（复现漏判）got=3`、`[S4] TV3 R12 拦下双重否定 ×2 got=2`；`[C] GV-D/E/F 三种双重否定 → R12 fail` 且 R10 不误报。

### 4.4 R11 — 绑定行路径隔断容忍 + 引用锚回验（第 8 类）

```python
BIND_RE = re.compile(r"被核对象[^。\n]{0,160}?SHA256\s*=\s*`?([0-9a-fA-F]{64})`?")
BIND_BYTES_RE = re.compile(r"字节数\s*=\s*([\d,]+)")
BIND_PATH_BACK = re.compile(r"`([^`\n]{1,200})`")
_COMMA = re.compile(r",")
def r11_scan(text, doc_dir, root=None, recompute=None):
    import hashlib as _h, pathlib as _pl
    if recompute is None:
        def recompute(p):
            b = p.read_bytes(); return _h.sha256(b).hexdigest(), len(b)
    problems, warnings, bindings = [], [], []
    for m in BIND_RE.finditer(text):
        declared = m.group(1)
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        if line_end == -1: line_end = len(text)
        tail = text[m.end():min(line_end, m.end() + 120)]
        sep = text[m.start() + 4:m.start() + m.group(0).find("SHA256")]
        path = None
        sep_paths = BIND_PATH_BACK.findall(sep)
        if sep_paths: path = sep_paths[-1]
        else:
            back_paths = BIND_PATH_BACK.findall(text[line_start:m.start()])
            if back_paths: path = back_paths[-1]
        rec = {"declared": declared, "path": path, "match": None}
        if path:
            p = _pl.Path(path.strip()); cand = []
            if not p.is_absolute():
                cand.append(doc_dir / p)
                if root is not None: cand.append(root / p)
            cand.append(p)
            hit = next((c for c in cand if c.is_file()), None)
            if hit is None:
                problems.append("引用锚指向不在盘对象 %s（R11/R3-3c）" % path); rec["match"] = False
            else:
                sha, size = recompute(hit)
                bm = BIND_BYTES_RE.search(tail)
                ok_sha = sha == declared.lower()
                ok_len = True
                if bm: ok_len = int(_COMMA.sub("", bm.group(1))) == size
                rec.update({"match": ok_sha and ok_len, "recomputed": sha, "bytes": size})
                if not (ok_sha and ok_len):
                    problems.append("引用锚失配 %s：现盘 %s/%d ≠ 声明（R11/R3-3a）" % (path, sha[:12], size))
        else:
            warnings.append("绑定行缺显式路径，需人工锚定（R11/R3-3b）")
        bindings.append(rec)
    if not bindings:
        problems.append("缺 SHA256 绑定行（R11：被核对象…SHA256 = hex 全域无匹配，已容忍 ≤160 字符路径隔断与可选反引号）")
    return problems, warnings, bindings
```

- **消误报理由**：「被核对象」与「SHA256 =」间允许 ≤160 个非句末、非换行字符（覆盖 CANDIDATE:122 括注路径与 LEDGER:186 长分隔段两种真实形态）；hex 可选反引号；路径回看**限同一行**（防上一行无关路径误绑）。不采用全域 bind_any（TV4 漏判实证，S5）。
- **会否漏判分析**：绑定行必须 ≥1 才 PASS；每条带路径者现盘重算回验（失配/不在盘仍 FAIL：TV5 伪造、TV6 不在盘、GV-G 真盘+错哈希全 FAIL）——放宽匹配不放松校验。**残余**：分隔段 >160 字符或跨句的绑定行仍漏（四真实件未见此形态，未验）。
- **实跑输出**：S1 四件 R11 problems 全 []，绑定回验 match=true×4（C97 两条 `_review_reply_transcript.json`/`_verify_reply.json` 经同一行回看路径均在盘且哈希字节数相符；OBS:366 无路径 → 仅警告 warn=1）；复核员 B 组绕开 R11 自算 hashlib 独立复证：ee27b4ca…/11948、6888379a…/5592、91d1317f…/4481、1fe6b1b6…/4034 全 match=true；`[S3] TV4 无绑定行 → R11 fail`、`[S5] TV4 bind_any 命中 ≥1（若只查全域会 PASS）got=True` + `[S5] TV4 R11 仍 FAIL got=True`。

## 5 反向验证与复核回件

### 5.1 反向验证实跑（命令：`python -I -X utf8 _g7_reverse_validate.py` → `_g7_reverse_validate_out.txt`，本轮复跑，exit=0，**verdict: total=46 pass=46 fail=0**）

**A. 四真实件不再误报（S1）**——problems 全 []：
```
PASS  [S1] CANDIDATE_RESIGN_YES_V2.md R9(APPROVE_SCOPE)  got=[]
PASS  [S1] CANDIDATE_RESIGN_YES_V2.md R10  got=[]   | R11 bindings=[{"path": "lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md", "match": true}] R10warn=6
PASS  [S1] LEDGER_APPENDIX_DRAFT.md R11  got=[]     | bindings=[{"path": "_lv_subject_reply.txt", "match": true}] R10warn=3
PASS  [S1] OBSERVATION_PROTOCOL_SPEC.md R11 got=[]  | bindings=[{"path": null, ...}] warn=1（无路径仅警告）
PASS  [S1] C97_SCOPE_RECHECK.md R11 got=[]          | bindings=[{"path": "_review_reply_transcript.json", "match": true}, {"path": "_verify_reply.json", "match": true}]
```

**B. 真违规样本逐个 FAIL（S3/S5 + 复核员 C 组新样本）**：
```
PASS  [S3] TV1 缺要素 → R9 fail
PASS  [S3] TV2 正面越权断言 ×5 → R10 fail  got=5
PASS  [S3] TV5 伪造绑定（hex≠现盘）→ R11 fail
PASS  [S3] TV6 绑定指向不在盘 → R11 fail
PASS  [S3] TV4 无绑定行（仅指纹引证）→ R11 fail
PASS  [S5] TV4 bind_any 命中 ≥1（若只查全域会 PASS）  got=True   ← bind_any 漏判实证
PASS  [C] GV-D/E/F 双重否定(不得不/并非不/不能不) → R12 fail 且 R10 不误报
PASS  [C] GV-J 对照:单重否定 → R10 豁免且 R12 不拦  got=([], [])
PASS  [C] GV-G 伪造绑定(真盘+错哈希) → R11 失配 / [C] GV-H 指向不在盘 → R11 / [C] GV-I 真缺要素 → R9 fail
```

**C. 漏判形态对照复现（S2/S4/S6）**：
```
PASS  [S2] CANDIDATE 858e5e0b正则复现缺绑定行  got=True   （第 8 类误报在真实件复现）
PASS  [S2] LEDGER bind_naive复现缺绑定行  got=True
PASS  [S2] CANDIDATE 包裹字面量复现缺要素  got=True        （第 5 类误报在真实件复现）
PASS  [S4] TV3 编排式回看全部豁免（复现漏判）  got=3 → R12 恰拦 2、单重否定对照不拦
PASS  [S4] TV2 编排式回看误豁免 ≥1（复现跨句污染漏判）→ R10 仍拦
PASS  [S6] TV7/TV7b naive 漏判复现 ×2 → R9 均判在场
```

**D. 保护件零漂移（S7）**：九件指纹全 MATCH（清单见 §2）。

### 5.2 复核回件（如实转录，verdict = **confirmed**）

> 复核结论：回件成立（confirmed），六项检查全过，另报 1 项作者未申报的轻微残余。被核对象=ask 所载形式化回件全文（逐字落盘 lead/gate_fp7_20261108/_gv_subject.json，7709B）。
> 被核对象 SHA256 = `84e0a3b6894ddf1a8fb3a19f09415a482c5e2df6e1e6d36edb41a35e8c7a1b8b`，字节数 = 7709

复核六项全过（①三类误报独立复算逐项一致；②谓词消误报独立验证 A 组四真实件 problems 全 []、B 组绑定回验 match=true×4；③反向验证 46/46 复跑成立、七个 TV 样本均为真实构造、另建 8 个新真违规样本全 FAIL；④双重否定反例实跑复证——奇偶法对 CANDIDATE:155 制造 2 处新误报、对 TV3 命中 1 误豁免，作者原话逐字成立；⑤无整模板重写、插入锚点真实存在（GATE_TEMPLATE_FIXED.py.txt:325 §R8 替换对照、:339 未验项）；⑥零越界、9 件保护件零漂移、谓词仅 import re/hashlib/pathlib）。

复核另报两项残余（不推翻 confirmed，本文如实收录）：**GV-K2** 未包裹裸拆断形态 R9 仍判缺要素（作者 §6 残余清单未申报的一例，第 5 类家族内，四真实件实测 0 处现网无影响）；**GV-L** 分离型「亦非不宣告已生效」R10/R12 全 0 漏检（与作者 §6.2 自报相符）。复核员自校一笔：其 D 组初版断言「奇偶法对 TV3 全豁免」过强——奇偶法对 pos=299「不得不」凑偶数会碰巧判违规；作者原话「三否定词会被误豁免」针对命中 1（pos=245），逐字成立。

本轮补写员对复核件两条脚本级 FAIL 的独立裁定：`_gv_pred_check.py` 的 `[E] 三代码块归一化后逐行含于模块 got=False` 系**逐行包含式比对的口径问题**（patch 侧紧凑写法与模块侧 docstring/import 排版差异），非语义分歧——补写员独立复验 `python -I -X utf8 _doc_ast_align_check.py`（本轮实跑）：import 归一化 + docstring 剥离后 r11_scan 全等 True、六同名函数全等、模块级常量逐名比对 True（ALIGNED_EQUAL），与复核回件「唯一差异=r11_scan 首部 import 合并行写法」一致。`[D] 奇偶法对 TV3 全豁免 got=1 want=0` 即上述复核员自校项，如实记录。

## 6 结论

- **增量插入位置**：模板侧 `GATE_TEMPLATE_FIXED.py.txt` 在 §R8「替换对照」（:325）之后、「未验项」（:339）之前新增四节 §R9/§R10/§R12/§R11（§R12 紧随 §R10，因其消费 R10 的语境分类）；R0–R8 一字不动。门禁代码侧三处替换点：①要素循环 `for k in [...]: if k not in t: P.append('缺要素 '+k)` → `r9_check(t, tokens)`；②绑定行两行（`_gv_gates/858e5e0b.py:11-12` 形态）→ `r11_scan(t, doc_dir, root=ROOT)`；③越权词字面扫描 → `r10_scan` 后接 `r12_scan`。
- **与既有谓词执行顺序**：R0 三问 → R1–R8 既有检查 → R9 → R10 → R12 → R11 → R7 输出契约（rule_id=R9/R10/R11/R12 随 problems/warnings 输出）。
- **是否需调整既有谓词**：需要，三处——①紧邻绑定行正则**必须替换**（S2 已证其在 CANDIDATE/LEDGER 两真实件必然误报「缺 SHA256 绑定行」）；②要素词表**不得**从任务书行文复制包裹符（「APPROVE_SCOPE」整体入表即成第 5 类，`1552e9fe.py:9` 现状在案）；③**不得**改用全域 bind_any（S5 已证其放走 TV4；LEDGER bind_any=10 仅 1 条是绑定行）。
- **fixedCount = 4**（第 5/6/7/8 类四类、R9/R10/R11/R12 四谓词；severity=medium）。
- **未验项（如实）**：
  1. 第 5 类**原始误报件未定位**（机制两形态已在 CANDIDATE/TV7/TV7b 复现并修复，原始现场未验）。
  2. DOUBLE_NEG_RE 构式表非穷尽——分离型「非…不宣告」变体漏检（GV-L 实跑实证），按语料增补。
  3. quote_mention 豁免残余：真越权写成 ≤80 字符、无自指标的「…」短语时降为警告不 fail（靠 warnings 可见性与 R0 兜底）。
  4. NEG_RE 词表「排除/非」易误配，24 字符窗内误豁免残余（漏检方向）。
  5. R9 对未包裹裸拆断形态不覆盖（复核员 GV-K2 实证；四真实件实测 0 处）。
  6. R11 对 >160 字符或跨句分隔的绑定行未验（现网四件未见此形态）。
  7. 谓词未改写进任何真实工作流/门禁 mjs（本轮禁令）；S1–S7 及复核 A–E 组均为离线静态验证，本件亦未 commit。
