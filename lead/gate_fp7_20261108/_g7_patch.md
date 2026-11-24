# _g7_patch.md — 门禁误报第 5/6/7/8 类增量补丁（不改既有模板，只给四谓词与插桩位置）

撰写：门禁误报形式化员·GLM（dynamic workflow 子代理）。日期：2026-11-09。
谓词本体逐字 = `_g7_predicates.py`（被核对象 SHA256 = `02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120`，字节数 = 11743）。
反向验证实跑 = `_g7_reverse_validate.py` → `_g7_reverse_validate_out.txt`（46/46 PASS，见 §5）。
★ 本件不改 GATE_TEMPLATE_FIXED.py.txt、不改任何门禁 mjs、不改交付件与台账。

## 1 插桩位置（模板侧与门禁代码侧）

模板侧（GATE_TEMPLATE_FIXED.py.txt，r2 版）：在 §R8「替换对照」表格之后、「未验项」清单之前，新增四节 §R9/§R10/§R12/§R11（编号即谓词名；§R12 紧随 §R10，因其消费 §R10 的语境分类）。R0–R8 一字不动。

门禁代码侧（GATE_CODE 家族，三类改动点）：
1. 要素循环 `for k in [...]: if k not in t: P.append('缺要素 '+k)` → 改调 `r9_check(t, tokens)`（R9 归一化在一切字面要素检查之前执行）。
2. 绑定行两行 `B=re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?',t); if not B: P.append('缺 SHA256 绑定行')` → 改调 `r11_scan(t, doc_dir, root=ROOT)`（其内置 R3-3 回验，勿再重复比对）。
3. 若该域门禁含越权词字面扫描 → 改调 `r10_scan` 后接 `r12_scan`（顺序固定：R10 豁免在前、R12 双重否定否决在后）。

执行顺序（与既有谓词）：R0 三问 → R1–R8 既有检查 → R9 → R10 → R12 → R11 → R7 输出契约（rule_id=R9/R10/R11/R12 随 problems/warnings 输出）。

需调整的既有谓词：①绑定行紧邻正则必须替换（S2 已证其在 CANDIDATE/LEDGER 两真实件上必然误报「缺 SHA256 绑定行」）；②要素词表不得从任务书行文复制包裹符（「APPROVE_SCOPE」/`APPROVE_SCOPE` 整体入表即成第 5 类）；③不建议改用全域 `SHA256\s*=\s*`?[0-9a-fA-F]{64}`（bind_any）——S5 已证其把仅含指纹引证、无绑定行的 TV4 判 PASS（LEDGER 真实件 bind_any=10，其中仅 1 条是绑定行）。

## 2 R9（第 5 类：带反引号/引号包裹标识符判缺要素）

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

机理：N2 先拼接反引号跨度内的换行拆断，N1 把包裹字符替换为空格（成词边界，杜绝跨词假拼接）；raw 命中则不计警告。消误报不漏判：真缺要素 = raw 与归一化双缺（TV1 判 FAIL 实跑在案）；拆断形态（TV7）与包裹失配门禁字面量（TV7b）在 naive 下误报、R9 下判在场（S6）。

## 3 R10 + R12（第 6/7 类：否定式自指、否定句含完成时词）

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

机理与三道防线：
- 否定回看不跨句（子句边界 。！？；\n）：「台账无需再登记。已追加至台账」中前句的「无」不再豁免后句的「已追加」（TV2 对照：编排式 24 字符裸窗把该正面断言误豁免，R10 仍判违规，S4）。
- 短引证跨度（≤80 字符「…」）+ 自指标记检查：CANDIDATE:130 翻案条款「或回件出现「可应用/放行 N-5」断言」是条件引用而非断言 → quote_mention 警告；而「本件放行 N-5」类带自指标的跨度不豁免（TV2 判 FAIL）。
- R12 双重否定用**相邻构式**（不得不/并非不/无不/没有不/不无/不能不/不可不/并不是不/不是不/未曾不）而非否定词奇偶计数——奇偶法两个方向都错：真实件 CANDIDATE:155「**无越权断言**：…不出现「可应用母本…」」两独立否定短语会被误判肯定（新误报），TV3「并未漏看…并非不宣告…」三否定词会被误豁免（漏判）。实跑：TV3 三处已生效被编排式回看全豁（3/3），R12 恰拦两处双重否定、放过单重否定对照（S4）。

## 4 R11（第 8 类：绑定行路径隔断误判缺绑定）

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

机理：分隔段允许 ≤160 个非句末、非换行字符（覆盖「被核对象（审阅回件 `path`）SHA256 = `hex`」与「被核对象 = 核对回件文本（…存本写域 `path`）——**SHA256 = `hex`」两种真实形态）；hex 可选反引号；路径回看限同一行（防上一行无关反引号路径误绑）；绑定行必须 ≥1，且每条带路径者回验现盘（真失配/不在盘仍 FAIL）。四真实件实跑：CANDIDATE/LEDGER/C97×2 四条绑定全部 match=true，OBSERVATION 缺路径 → 警告（S1）；TV4（无绑定）/TV5（伪造）/TV6（不在盘）全 FAIL（S3）。

## 5 反向验证汇总（_g7_reverse_validate_out.txt，46/46 PASS）

| 组 | 内容 | 结果 |
|---|---|---|
| S1 | 四真实件 × R9/R10/R12/R11 | problems 全 0；R10 命中 6+3+0+0 全豁免/警告；R11 绑定 1/1/1/2 全 match |
| S2 | naive 门禁在真实件复现第 5/8 类 | CANDIDATE/LEDGER 缺绑定行 ×2 门禁正则、包裹字面缺要素 ×1 |
| S3 | TV1/TV2/TV4/TV5/TV6 真违规 | 全 FAIL（R9 缺要素、R10×5、R11 缺绑定/伪造/不在盘） |
| S4 | TV3 双重否定 + TV2 跨句污染 | 编排式回看 3/3 全豁（漏判复现）；R12 恰拦 2；R10 仍拦 TV2 |
| S5 | TV4 bind_any 对照 | bind_any=1 会 PASS；R11 FAIL |
| S6 | TV7 拆断 / TV7b 包裹失配 | naive 漏判复现 ×2；R9 均判在场 |
| S7 | 保护件 9 件指纹 | 全 MATCH（含模板/两台账/四真实件） |

## 6 残余风险与未验（如实）

1. **第 5 类原始误报件未定位（未验）**：四份指纹件上 naive 裸子串门禁不漏包裹形态（包裹符不与 token 相交；实测 CANDIDATE 裸写 2/反引号 3、LEDGER 裸写 1/反引号 5）——第 5 类漏判只在门禁字面量带包裹符（S2 已在 CANDIDATE 复现）或要素被拆断（TV7）两形态发生。机制修复已验证，原始现场未验。
2. DOUBLE_NEG_RE 构式清单非穷尽（「非…不可」跨距离等变体未覆盖）——漏检方向残余，按语料增补。
3. quote_mention 豁免残余：真越权恰写成 ≤80 字符、无自指标记的「…」短语时降为警告不 fail——靠 warnings 可见性与 R0 行为差异原则兜底。
4. NEG_RE 词表含「排除/非」等易误配词（如「能排除的假设」）——子句边界已限毒性，24 字符窗内误豁免残余（漏检方向）。
5. R11 对分隔段 >160 字符或跨句的绑定行仍漏（现网四件未见此形态，未验）。
6. 谓词未改写进任何真实工作流（本轮禁令）；S1–S7 为离线静态验证。
