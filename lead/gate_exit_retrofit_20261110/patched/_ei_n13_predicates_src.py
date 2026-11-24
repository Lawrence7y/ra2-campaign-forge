# -*- coding: utf-8 -*-
r"""_n13_predicates.py — N13 / R13 谓词（第二轮修订，修复核 partial 的 ④ 与 ⑦）

A 检索动作 / B 小节标题·表头列名·目录清单：本件只补这两类语境。
C 否定式交既有 R10（lead/gate_fp7_20261108/_g7_predicates.py:78-130）判定，
本件只消费其 kind，另加「否定必须落在 token 自己的微段内」的局部性守卫；
双重否定交 R12（:134-148）。不重写 R10 的正则。

★ 核心判据（复核后收紧，不放宽）：语境豁免必须以【该 token 自己的微段】
为单位，不能靠整行 / 整子句里任意位置出现的 A/B/C 标记。微段边界含冒号、
斜杠、竖线、加号、逗号、括号、星号、井号，使「grep 结果：」「未验：」
「/ 此笔已入账 /」各自独立成段。逐处命中判序：
  0 行级同句混用：本行另有肯定完成断言（主语+完成词、或拆分形态）→ 全行 D
  1 微段内有直接否定（不宣告/不得/…）且 R10 同意 → C（放过）
  2 微段内 token 前有非结构性名词（主语）→ D（真断言）
  3 微段内 token 之后有 A/B 标记（grep/核查/结果/0 命中/?/…），
    或 token 之前是「有没有/是否」问句 → A 或 B（放过）
  4 其余（裸完成词、拿不准、无 R10）→ D（默认 FAIL）

零真机、零采样；纯静态文本 + 位置 + 正则；不 import 任何动态/内存/进程模块。
"""

import re

DEFAULT_TOKENS = ("已入账", "已追加", "已生效")

# 行首装饰：缩进、列表符号、数字序号、引用符。只剥前缀，不改 body 内容。
_LEAD = re.compile(r"^\s*(?:[-*+>]\s+|\d+[.)]\s+|[①-⑳]\s*)*\s*")

# 微段边界：比 R10 的 CLAUSE_BREAK（。！？；\n，:71）更细。
# 不含「」——引号连同其外的「不得写成」留在同一微段，供 C 类判定。
_SEG_BREAK = "。！？；\n，,、：:|+/（）()【】<>*#=`"

_HEADING = re.compile(r"^#{1,6}\s")
_TABLE_ROW = re.compile(r"^\|.*\|\s*$")
_TABLE_SEP = re.compile(r"^\|[\s:|-]+\|\s*$")
_B_TOC = re.compile(r"(?:§|一页纸总览|总览|1\([a-c]\)|目录|大纲|结构|五节|五章|章节)")

# A/B 标记：只允许出现在【token 之后】的同一微段内；冒号前的「grep 结果：」
# 只在上一微段，不能给本微段里的裸完成词 / 主语断言发豁免。
_A_AFTER = re.compile(
    r"grep|检索|搜索|查找|清点|核查|核对|实跑命令|核查动作|结果|=0\b|"
    r"0\s*(?:逐字)?命中|否（grep|[？?]|清单|总览|目录|结构|五节|五章|章节"
)
_A_QUESTION = re.compile(r"有没有|是否|查有无|查是否")
_ASK_TAIL = re.compile(r"[？?]|的\s*$")

# 允许的「非主语前缀」：仅结构性 / 问询性成分。剥完后若还有字，就是主语。
_STRUCT = re.compile(
    r"\s+|#{1,6}\s*|\d+\s*|[（(][a-zA-Z0-9]+[）)]\s*|[①-⑳]\s*"
    r"|[·•\-+*|/>“”‘’`_=「」『』【】\[\]{}〈〉§]+\s*"
    r"|有没有|是否|查有无|查是否|(?:一|二|三|四|五|六|七|八|九|十)、"
    r"|上游指纹|待入账清点|一页纸总览|总览|目录|大纲|结构|五节|五章|章节|清单"
)

# 直接否定：必须在 token 自己的微段内才算 C。「未验：」在上一微段，不算。
# 只收【显式否定短语】，不收裸「不/未/非/无」单字——「有没有」里含「没」、
# 「无非」「非常」等都会误触；单字否定的形（不清点：本笔已入账）由 ③ 主语守卫
# 与行级肯定守卫兜底，仍判 D，不产生放过。
_DIRECT_NEG = re.compile(
    r"不宣告|不得不|并非不|并不是不|不是不|不得|不能|不可|并未|亦非|"
    r"未见|未验|未核|未确认|否决|排除|禁止|请勿|无越权|没有不"
)
_QUOTE_SPAN = re.compile(r"「[^」]{0,120}」|“[^”]{0,120}”|\"[^\"]{0,120}\"")
_BAN = re.compile(r"不得|不能|不可|禁止|请勿")

# 整行肯定守卫：完成词 + 可应用/放行/无需…，或「但/且 … 已入账」转折肯定。
_POS_TAIL = re.compile(
    r"(?:已|现|正式)(?:生效|入账|追加)\s*[，,、；;]?\s*"
    r"(?:可应用|可改|放行|具备|无需|照此|即)"
)
_CONTRAST_POS = re.compile(
    r"(?:但|但是|然而|而|且|另外|另|同时|并)\s*[^，。；\n]{0,24}?(?:已入账|已追加|已生效)"
)

# 词表拆分裂缝：「本笔已于 §605 入账」不含字面三词，用主语 + 完成动词补 D。
# 第二轮：不再跳过 A/B/C 豁免行（复核 :344-346 指出的豁免外溢）。
_SPLIT_SUBJ = (
    r"(?:本笔|本件|该笔|该件|此笔|此件|该条|本条|此条|本节|母本|台账|"
    r"本候选|本回件|本交付件|本项|该项|此项|本草案|该草案|"
    r"第\s*[一二三四五六七八九十\d]+\s*笔|笔\s*\d+|N-?\d+)"
)
_SPLIT_ASSERT = re.compile(
    r"(?:" + _SPLIT_SUBJ + r")\s*(?:已|现|正式|业已|现已|现正式)\s*"
    r"(?:于\s*§\s*\d+\s*|至\s*台账\S{0,8}\s*|经\s*)?(?:入账|追加|生效)"
)


def _body(line):
    """剥掉行首缩进/列表符号/引用符，返回 (body, offset)。"""
    m = _LEAD.match(line)
    off = m.end() if m else 0
    return line[off:], off


def _seg_bounds(text, pos, breaks=_SEG_BREAK):
    """pos 所在微段在 text 中的 [start, end)（不跨 breaks）。"""
    s, e = 0, len(text)
    for ch in breaks:
        j = text.rfind(ch, 0, pos)
        if j + 1 > s:
            s = j + 1
        j = text.find(ch, pos)
        if j != -1 and j < e:
            e = j
    return s, e


def _is_heading(body):
    return bool(_HEADING.match(body))


def _is_table_header(lines, idx):
    """(|...| 行且下一行是 |:--| 分隔行) 或含 ? / 是否 的问询列名 → 表头。
    返回 (is_header, is_table_row)；数据行不是表头。"""
    body, _ = _body(lines[idx])
    if not _TABLE_ROW.match(body):
        return False, False
    nbody, _ = _body(lines[idx + 1]) if idx + 1 < len(lines) else ("", 0)
    if _TABLE_SEP.match(nbody):
        return True, True
    if re.search(r"[?？]|是否", body):
        return True, True
    return False, True


def _is_toc_enum(body):
    """目录 / 一页纸总览 / 结构枚举行：§ 或章节序号，名词短语串，非完整句。"""
    if not _B_TOC.search(body):
        return False
    if "。" in body or "；" in body:
        return False
    return bool(re.search(r"§\d+|/\s|\+\s|\|\s|[（(][a-zA-Z0-9]+[）)]", body)
                or "总览" in body)


def _prefix_is_subject(prefix):
    """剥掉结构性/问询性成分后仍有文字 → 视为主语（真断言）。"""
    return bool(_STRUCT.sub("", prefix).strip())


def _seg_of(line, start, end):
    s, e = _seg_bounds(line, start)
    return line[s:e], start - s, end - s


def _split_assert_lines(text):
    """逐行找「主语 + 完成动词」拆分形态；返回 {行号: [命中原文]}。
    守卫：命中所在微段不含直接否定，且命中不落在引证跨度内。"""
    out = {}
    for li, line in enumerate(text.splitlines(), 1):
        for m in _SPLIT_ASSERT.finditer(line):
            seg, _, _ = _seg_of(line, m.start(), m.end())
            if _DIRECT_NEG.search(seg):
                continue
            if any(q.start() <= m.start() and m.end() <= q.end()
                   for q in _QUOTE_SPAN.finditer(line)):
                continue
            out.setdefault(li, []).append(m.group(0).strip())
    return out


def _line_positive(line, occurrences, split_hits):
    """同句混用：本行是否存在【另一处】肯定完成断言 → 全行豁免作废。"""
    for tok, bs, be in occurrences:
        seg, rs, re_ = _seg_of(line, bs, be)
        if _DIRECT_NEG.search(seg[:rs]):
            continue
        if _prefix_is_subject(seg[:rs]) or _CONTRAST_POS.search(seg):
            return True, "主语+完成词 / 转折肯定：" + tok
    for m in _POS_TAIL.finditer(line):
        seg, _, _ = _seg_of(line, m.start(), m.end())
        if not _DIRECT_NEG.search(seg):
            return True, "完成词+可应用/放行：" + m.group(0)
    if split_hits:
        return True, "词表拆分裂缝：" + split_hits[0]
    return False, ""


# ---------------------------------------------------------------------------
# R13 主入口 (a)：单个文本 → (是否含 A/B 类语境命中, 命中明细)
# ---------------------------------------------------------------------------
def r13_scan(text, tokens=DEFAULT_TOKENS, r10_scan=None, r12_scan=None):
    """R13 谓词（A/B 两类）。返回 (has_ab, details)。

    details 逐处命中：token/pos/line/quote/kind∈{A,B,C,D}/exempt/rule/
    r10_kind/degraded。只有 kind == 'D' 应当 FAIL。
    默认 FAIL：无法归类、拿不准、或未提供 r10_scan 时非 A/B 一律 D。
    r10_scan / r12_scan 来自 _g7_predicates.py；生产用法必须同时加载。
    """
    L = text.splitlines(keepends=False)
    table_flags = [_is_table_header(L, i) for i in range(len(L))]

    r10_map, r12_pos = {}, set()
    if r10_scan is not None:
        _, _, rhits = r10_scan(text, list(tokens))
        for h in rhits:
            r10_map[(h["token"], h["pos"])] = h["kind"]
    if r12_scan is not None:
        _, dhits = r12_scan(text, list(tokens))
        for h in dhits:
            r12_pos.add((h["token"], h["pos"]))

    split_lines = _split_assert_lines(text)

    details = []
    abs_base = 0
    for li, line in enumerate(L):
        body, off = _body(line)
        occ = []
        for tok in tokens:
            for m in re.finditer(re.escape(tok), body):
                occ.append((tok, m.start(), m.start() + len(tok)))
        if not occ and li + 1 not in split_lines:
            abs_base += len(line) + 1
            continue

        mixed, mixed_why = _line_positive(body, occ, split_lines.get(li + 1, []))
        is_head = _is_heading(body)
        is_thdr, is_trow = table_flags[li]
        is_toc = _is_toc_enum(body)
        b_struct = is_head or is_thdr or (is_toc and not is_trow)

        for tok, bs, be in occ:
            gpos = abs_base + off + bs
            seg, rs, re_ = _seg_of(body, bs, be)
            prefix, suffix = seg[:rs], seg[re_:]
            quote = line.strip()
            rec = {"token": tok, "pos": gpos, "line": li + 1, "quote": quote,
                   "kind": "D", "exempt": False, "rule": "", "degraded": False,
                   "r10_kind": r10_map.get((tok, gpos))}

            # ⓪ 同句混用 / 行级肯定段：整行作废
            if mixed:
                rec.update(kind="D", exempt=False,
                           rule="同句混用：行内另有肯定断言（" + mixed_why + "）",
                           quote=quote + " | " + mixed_why)
                details.append(rec)
                continue

            # ① R12 双重否定构式 = 肯定
            if (tok, gpos) in r12_pos:
                rec.update(kind="D", exempt=False, rule="R12 双重否定构式=肯定")
                details.append(rec)
                continue

            # ② 微段内直接否定 → C（必须 R10 同意；无 R10 则降级默认 FAIL）
            direct_neg = bool(_DIRECT_NEG.search(prefix))
            in_quote = any(q.start() <= bs and be <= q.end()
                           for q in _QUOTE_SPAN.finditer(body))
            if direct_neg or (in_quote and _BAN.search(_QUOTE_SPAN.sub(" ", body))):
                k = rec["r10_kind"]
                if r10_scan is not None and k in ("negation", "quote_mention"):
                    rec.update(kind="C", exempt=True,
                               rule="C 否定式（R10 " + k + " 已覆盖，微段内直接否定）",
                               r10_kind=k)
                elif r10_scan is None:
                    rec.update(kind="D", exempt=False, degraded=True,
                               rule="降级：无 R10，C 类不自行豁免 → 默认 FAIL")
                else:
                    rec.update(kind="D", exempt=False,
                               rule="R10 " + str(k) + "：微段否定不采纳 → 默认 FAIL")
                details.append(rec)
                continue

            # ③ 微段内主语 + 完成词 → D（真断言，主语词表不再是唯一依据）
            if _prefix_is_subject(prefix):
                rec.update(kind="D", exempt=False,
                           rule="D 真断言：微段内 token 前有非结构性名词（主语）")
                details.append(rec)
                continue

            # ④ A / B：标记必须在 token 之后的同一微段内，或问句在 token 之前
            a_after = _A_AFTER.search(suffix)
            a_ask = _A_QUESTION.search(prefix) and _ASK_TAIL.search(seg)
            if a_after or a_ask:
                if b_struct:
                    rec.update(kind="B", exempt=True,
                               rule="B 小节标题/表头列名/目录清单：微段内标记 "
                                    + repr((a_after or _A_QUESTION.search(prefix)).group(0)))
                else:
                    rec.update(kind="A", exempt=True,
                               rule="A 检索动作：微段内标记 "
                                    + repr((a_after or _A_QUESTION.search(prefix)).group(0)))
                details.append(rec)
                continue

            # ⑤ 拿不准 / 裸完成词 → 默认 FAIL
            rec.update(kind="D", exempt=False,
                       rule="默认 FAIL：微段内无 A/B 标记，且无直接否定",
                       degraded=(r10_scan is None))
            details.append(rec)
        abs_base += len(line) + 1

    # 词表拆分裂缝：逐行补 D，不再跳过 A/B/C 豁免行
    for li, hits in split_lines.items():
        for h in hits:
            details.append({"token": h, "pos": -1, "line": li,
                            "quote": L[li - 1].strip(), "kind": "D", "exempt": False,
                            "rule": "词表拆分裂缝：主语+完成动词（非字面三词）",
                            "degraded": False, "r10_kind": None})

    has_ab = any(d["kind"] in ("A", "B") for d in details)
    return has_ab, details


def r13_assertions(text, tokens=DEFAULT_TOKENS, r10_scan=None, r12_scan=None):
    """便捷入口：返回 (problems, details)。problems 只含 D 类（应当 FAIL）。
    接口与 r10_scan 的前两项对齐，便于迁移配方直接替换。"""
    _, details = r13_scan(text, tokens, r10_scan=r10_scan, r12_scan=r12_scan)
    problems = ["越权断言 %s（N13 D 类，L%d：%s）" % (d["token"], d["line"], d["rule"])
                for d in details if d["kind"] == "D"]
    return problems, details


# ---------------------------------------------------------------------------
# (b) 迁移配方：朴素字面门禁 → 谓词化门禁（调用方接口不变）
# ---------------------------------------------------------------------------
# 改前 3 行（既有门禁，_dnv_gate.py:14-15 / dwfrun-614dbceb GATE_CODE）：
#     for bad in ['已入账','已追加','已生效']:
#      if bad in t: P.append('含越权断言 '+bad)
#
# 改后 5 条语句（粘贴块 10 行；except 必须同时抓 ImportError 与 OSError，
# 否则真删文件时 spec.loader.exec_module 抛 FileNotFoundError 会让门禁崩溃）：
#     try:
#      import importlib.util as _u, pathlib as _p
#      if not (_p.Path(N13).is_file() and _p.Path(G7).is_file()): raise ImportError('谓词模块缺失')
#      _s=_u.spec_from_file_location('_n13',str(N13));_m=_u.module_from_spec(_s);_s.loader.exec_module(_m)
#      _g=_u.spec_from_file_location('_g7',str(G7));_g7=_u.module_from_spec(_g);_g.loader.exec_module(_g7)
#      for _p in _m.r13_assertions(t,['已入账','已追加','已生效'],r10_scan=_g7.r10_scan,r12_scan=_g7.r12_scan)[0]: P.append(_p)
#     except (ImportError, OSError, AttributeError):
#      for bad in ['已入账','已追加','已生效']:
#       if bad in t: P.append('含越权断言 '+bad)   # 降级：字面全拦，绝不静默 PASS
#
# 判别顺序：N13(A/B 微段过滤) → R10(C/D) → R12(双重否定) → R9/R11（其余项）。
# 谓词本体只读加载，不修改 _g7_predicates.py 一字（铁律绝对只读）。


if __name__ == "__main__":
    # 最小自检：降级形态（不依赖任何外部件）
    for s in ("### 1(c) 有没有已入账的？", "本笔已于 §605 入账",
              "grep 结果：已入账", "未验：本笔已入账"):
        p, d = r13_assertions(s)
        print(repr(s), "=>", "FAIL" if p else "PASS",
              [(x["kind"], x["rule"][:30]) for x in d])

    # ---------- 出口追加（仅追加；库本体与上面 4 行自检 print 一字未改）----------
    # 本脚本的判定 = 「最小自检」的 4 个降级形态样本是否仍给出 docstring :12-18
    # 判序所决定的结果。3 个样本按设计本就应 FAIL（D 类），故不能用 not p 聚合
    # （那样原件恒为 1，是假出口）；这里逐项对照应有结果，任一漂移即置假。
    # 期望值逐条取自原件未改动时的实测输出（本会话 python -I 实跑捕获）：
    #   B(放过) / D(拆分) / D(默认 FAIL) / D+D(同句混用+拆分)
    _EXPECTED = (
        ("### 1(c) 有没有已入账的？", False, ("B",)),
        ("本笔已于 §605 入账", True, ("D",)),
        ("grep 结果：已入账", True, ("D",)),
        ("未验：本笔已入账", True, ("D", "D")),
    )

    ok = True

    def check(name, cond, detail=""):
        global ok
        ok = ok and bool(cond)          # 合取聚合：全部检查通过才真
        print(("  [PASS] " if cond else "  [FAIL] ") + name
              + ((" | " + detail) if detail else ""))

    for s, want_p, want_kinds in _EXPECTED:
        p, d = r13_assertions(s)
        got = (bool(p), tuple(x["kind"] for x in d))
        want = (want_p, want_kinds)
        check("降级形态自检与判序期望一致 " + repr(s), got == want,
              "" if got == want else "got=" + repr(got) + " want=" + repr(want))

    print("核验结论: " + ("ALL PASS" if ok else "FAIL"))
    raise SystemExit(0 if ok else 1)
