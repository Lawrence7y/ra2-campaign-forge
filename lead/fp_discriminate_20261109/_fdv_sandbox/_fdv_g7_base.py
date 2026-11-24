# -*- coding: utf-8 -*-
r"""_g7_predicates.py — 门禁误报第 5/6/7/8 类修正谓词（R9/R10/R11/R12）+ 朴素门禁对照。
设计稿与可粘贴实现一体：本文件即增量补丁谓词本体，供 _g7_reverse_validate.py 实跑。
零真机、零采样；只做静态文本/哈希检查。hashlib 用于引用锚回验。

插桩位置（见 _g7_patch 说明）：接在既有 GATE_CODE 的绑定行检查之后、print 之前，
problems/warnings 双列表口径与模板 R7 输出契约一致（rule_id 必填）。
"""

import re

# ============ 朴素门禁对照（既有门禁家族现状，用于对照演示，非补丁） ============
NAIVE_BIND = re.compile(r"被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?")

def naive_gate(text, tokens, bind_re=NAIVE_BIND):
    """既有门禁家族的四步现状：缺小节(略)/缺要素子串/越权词子串/绑定行紧邻正则。
    返回 problems 列表——四类误报在此全数复现。"""
    problems = []
    for k in tokens:
        if k not in text:
            problems.append("缺要素 " + k)
    if not bind_re.search(text):
        problems.append("缺 SHA256 绑定行")
    return problems


# ============ R9 反引号/引号包裹归一化的要素匹配（第 5 类） ============
_WRAP_CHARS = "`\u00b4\u201c\u201d\u2018\u2019\u300c\u300d\u300e\u300f"
_WRAP_SPAN = re.compile(r"([^`\n]{1,200})")

def r9_normalize(text):
    """两遍归一化（顺序敏感：先 N2 后 N1）：
    N2 反引号跨行拆断修复：每个 `…` 跨度内若含换行，把跨度内换行删除
       （仅限反引号跨度，字面标识符被 Markdown 换行拆断的形态）；
    N1 包裹字符 → 空格（` ´ “ ” ‘ ’ 「 」 『 』），防跨词假拼接（拼接处成词边界）。
    返回归一化文本。"""
    out, pos = [], 0
    for m in re.finditer(r"`([^`]*)`", text):
        out.append(text[pos:m.start()])
        out.append(m.group(1).replace("\n", "").replace("\r", ""))
        pos = m.end()
    out.append(text[pos:])
    n2 = "".join(out)
    return "".join(" " if ch in _WRAP_CHARS else ch for ch in n2)

def r9_element_present(text, token):
    """要素在场的包裹鲁棒判定：先原文匹配，再对归一化文本匹配。
    返回 (present, where)：where 命中所在的文本层（raw|normalized）。"""
    if token in text:
        return True, "raw"
    if token in r9_normalize(text):
        return True, "normalized"
    return False, ""

def r9_check(text, tokens):
    """R9 谓词：对每个必现要素做包裹鲁棒匹配。
    返回 (problems, warnings)：缺要素才 fail（真缺：raw 与 normalized 双缺）。"""
    problems, warnings = [], []
    for k in tokens:
        ok, layer = r9_element_present(text, k)
        if not ok:
            problems.append("缺要素 " + k + "（R9：raw 与包裹归一化文本双缺）")
        elif layer == "normalized":
            warnings.append("要素 %s 仅在包裹归一化后命中（raw 层缺字面）" % k)
    return problems, warnings


# ============ R10 否定语境/引证语境豁免的越权断言扫描（第 6/7 类） ============
NEG_RE = re.compile(r"(不|无|未|非|禁|勿|否决|排除|不宣告|不得)")  # 与编排方探针同词表
NEG_WINDOW = 24  # 回看窗宽：沿用编排方实测口径，保证数字可对账
CLAUSE_BREAK = "。！？；\n"  # 子句边界：否定回看不跨句（防「无需…」的「无」污染下一 token）
SPAN_RE = re.compile(r"「([^」\n]{0,80})」")  # 短引证跨度（≤80 字符，非整段引文）
SELF_MARKERS = ("本件", "本文", "本候选", "本 YES", "本域", "本回件", "特此", "现宣告", "现批准", "本节")
# 双重否定构式（相邻两个否定词构成肯定）：不用「否定词奇偶计数」——两个独立否定短语
# （如「无越权断言…不出现」）会被奇偶法误判成肯定，「并未…并非不…」三否定词会被误豁免。
DOUBLE_NEG_RE = re.compile(r"(不得不|并非不|并不是不|不是不|无不|没有不|不无|不能不|不可不|未曾不)")

def r10_context(text, start, end):
    """对一处越权词命中分类。返回 dict：
    neg_count 回看窗内否定词个数（仅作信息）；dbl 是否存在相邻双重否定构式；
    回看窗 = min(24 字符, 当前子句)，子句起点 = 窗口内最后一个句界符（。！？；\\n）
    之后——否定词只对其子句负责。
    in_span/span 是否落在短引证跨度内；marked 跨度内或跨度前紧邻是否有自指宣告词。
    分类：dbl → double_neg（交 R12 判违规）；neg_count≥1 → negation（R10 豁免+警告）；
    plain+span(无自指) → quote_mention（R10 警告）；plain+无span → assertion（R10 违规）。"""
    s = max(0, start - NEG_WINDOW)
    boundary = max(text.rfind(ch, 0, start) for ch in CLAUSE_BREAK)
    if boundary > s:
        s = boundary
    pre = text[s:start]
    neg_count = len(NEG_RE.findall(pre))
    dbl = bool(DOUBLE_NEG_RE.search(pre))
    in_span, span = False, ""
    for m in SPAN_RE.finditer(text):
        if m.start() <= start and end <= m.end():
            in_span, span = True, m.group(1)
            break
    marked = in_span and any(mk in span for mk in SELF_MARKERS)
    if not in_span:
        head = text[max(0, start - 12):start]
        marked = any(mk in head for mk in SELF_MARKERS)
    if dbl:
        kind = "double_neg"
    elif neg_count >= 1:
        kind = "negation"
    elif in_span and not marked:
        kind = "quote_mention"
    else:
        kind = "assertion"
    return {"neg_count": neg_count, "dbl": dbl, "in_span": in_span, "marked": marked,
            "span": span[:40], "kind": kind}

def r10_scan(text, assert_tokens):
    """R10 谓词：越权断言词族逐处语境分类。
    返回 (problems, warnings, hits)。第 6/7 类误报全部降为 warnings；
    正面断言（无否定、无引证语境）仍 fail；双重否定构式交 R12 裁决。"""
    problems, warnings, hits = [], [], []
    for tok in assert_tokens:
        for m in re.finditer(re.escape(tok), text):
            ctx = r10_context(text, m.start(), m.end())
            hits.append({"token": tok, "pos": m.start(), "kind": ctx["kind"],
                         "neg_count": ctx["neg_count"], "in_span": ctx["in_span"]})
            if ctx["kind"] == "assertion":
                problems.append("越权断言 %s（R10：无否定、无引证语境）" % tok)
            elif ctx["kind"] == "negation":
                warnings.append("%s 处于否定语境（R10 豁免，窗内否定词 %d）"
                                % (tok, ctx["neg_count"]))
            elif ctx["kind"] == "quote_mention":
                warnings.append("%s 为短引证跨度内提及（R10 豁免）" % tok)
    return problems, warnings, hits


# ============ R12 双重否定守卫（第 6/7 类反例防线，接在 R10 之后） ============
def r12_scan(text, assert_tokens):
    """R12 谓词：回看窗内存在相邻双重否定构式（不得不/并非不/无不/没有不/不无/不能不
    /不可不/并不是不/不是不/未曾不）的越权词命中重新判违规。
    依据：双重否定=肯定（「并非不宣告已生效」＝宣告了）；注意不用否定词奇偶计数——
    两个独立否定短语（「无越权断言…不出现」）并非双重否定，「并未…并非不…」三个
    否定词也不豁免（奇偶法在此两例分别误报与漏判）。
    返回 (problems, hits)。"""
    problems, hits = [], []
    for tok in assert_tokens:
        for m in re.finditer(re.escape(tok), text):
            ctx = r10_context(text, m.start(), m.end())
            if ctx["kind"] == "double_neg":
                problems.append("越权断言 %s（R12：回看窗含双重否定构式=肯定）" % tok)
                hits.append({"token": tok, "pos": m.start()})
    return problems, hits


# ============ R11 绑定行路径隔断容忍 + 引用锚回验（第 8 类） ============
BIND_RE = re.compile(r"被核对象[^。\n]{0,160}?SHA256\s*=\s*`?([0-9a-fA-F]{64})`?")
BIND_BYTES_RE = re.compile(r"字节数\s*=\s*([\d,]+)")
BIND_PATH_BACK = re.compile(r"`([^`\n]{1,200})`")
_COMMA = re.compile(r",")

def r11_scan(text, doc_dir, root=None, recompute=None):
    """R11 谓词：绑定行匹配放宽 + 引用锚回验。
    匹配：「被核对象」与「SHA256 =」之间允许 ≤160 个非句末（。）、非换行字符
    （括注路径、破折号、加粗标记均可）；hex 允许可选反引号包裹。
    要求 ≥1 条绑定行，否则 fail（缺绑定行）。
    回验（R3-3 精神，堵假阴性）：路径取自「被核对象…SHA256 =」分隔段内的反引号
    路径；分隔段无路径时，回看【同一行】内最后一个反引号路径（限同一行，防止
    把上一行的无关路径误绑到本行绑定）。相对路径解析顺序 = 被扫文档所在目录 →
    仓库根 → 原样。现盘重算失配/对象不在盘 → fail（真问题，R3-3a/R3-3c）；
    找不到显式路径 → warning（R3-3b 需人工锚定）。字节数声明在同行为可解析时
    一并比对（先剥千分位逗号，兼容 R3-4）。
    recompute=None 时用内置 hashlib。返回 (problems, warnings, bindings)。"""
    import hashlib as _h
    import pathlib as _pl
    if recompute is None:
        def recompute(p):
            b = p.read_bytes()
            return _h.sha256(b).hexdigest(), len(b)
    problems, warnings, bindings = [], [], []
    for m in BIND_RE.finditer(text):
        declared = m.group(1)
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        if line_end == -1:
            line_end = len(text)
        tail = text[m.end():min(line_end, m.end() + 120)]
        sep = text[m.start() + 4:m.start() + m.group(0).find("SHA256")]
        path = None
        sep_paths = BIND_PATH_BACK.findall(sep)
        if sep_paths:
            path = sep_paths[-1]
        else:
            back_paths = BIND_PATH_BACK.findall(text[line_start:m.start()])
            if back_paths:
                path = back_paths[-1]
        rec = {"declared": declared, "path": path, "match": None}
        if path:
            p = _pl.Path(path.strip())
            cand = []
            if not p.is_absolute():
                cand.append(doc_dir / p)
                if root is not None:
                    cand.append(root / p)
            cand.append(p)
            hit = next((c for c in cand if c.is_file()), None)
            if hit is None:
                problems.append("引用锚指向不在盘对象 %s（R11/R3-3c）" % path)
                rec["match"] = False
            else:
                sha, size = recompute(hit)
                bm = BIND_BYTES_RE.search(tail)
                ok_sha = sha == declared.lower()
                ok_len = True
                if bm:
                    ok_len = int(_COMMA.sub("", bm.group(1))) == size
                rec.update({"match": ok_sha and ok_len, "recomputed": sha, "bytes": size})
                if not (ok_sha and ok_len):
                    problems.append("引用锚失配 %s：现盘 %s/%d ≠ 声明（R11/R3-3a）"
                                    % (path, sha[:12], size))
        else:
            warnings.append("绑定行缺显式路径，需人工锚定（R11/R3-3b）")
        bindings.append(rec)
    if not bindings:
        problems.append("缺 SHA256 绑定行（R11：被核对象…SHA256 = hex 全域无匹配，"
                        "已容忍 ≤160 字符路径隔断与可选反引号）")
    return problems, warnings, bindings
