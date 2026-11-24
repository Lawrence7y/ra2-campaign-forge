# -*- coding: utf-8 -*-
# R13 谓词完整可粘贴片段（A 检索动作 / B 小节标题·表头·目录 / C 交 R10 / D 默认 FAIL）
# 用法：把本段整段粘进门禁脚本，按 §3 的迁移配方调用 r13_assertions(t, WORDS, r10_scan, r12_scan)
import re

WORDS = ('已入账', '已追加', '已生效')
_LEAD = re.compile(r"^\s*(?:[-*+>]\s+|\d+[.)]\s+|[①-⑳]\s*)*\s*")
_SEG = "。！？；\n，,、：:|+/（）()【】<>*#=`"   # 微段边界（含冒号/斜杠/竖线）
_HEAD = re.compile(r"^#{1,6}\s")
_TROW = re.compile(r"^\|.*\|\s*$")
_TSEP = re.compile(r"^\|[\s:|-]+\|\s*$")
_TOC = re.compile(r"(?:§|一页纸总览|总览|1\([a-c]\)|目录|大纲|结构|五节|五章|章节)")
# A/B 标记只允许在 token 之后的同一微段内（或「有没有/是否」在 token 之前）
_AFTER = re.compile(r"grep|检索|搜索|查找|清点|核查|核对|实跑命令|核查动作|结果|=0\b|"
                    r"0\s*(?:逐字)?命中|否（grep|[？?]|清单|总览|目录|结构|五节|五章|章节")
_ASK = re.compile(r"有没有|是否|查有无|查是否")
_ASKTAIL = re.compile(r"[？?]|的\s*$")
# 结构性前缀（剥净后仍有字 = 主语 ⇒ D）
_STRUCT = re.compile(r"\s+|#{1,6}\s*|\d+\s*|[（(][a-zA-Z0-9]+[）)]\s*|[①-⑳]\s*"
                     r"|[·•\-+*|/>“”‘’`_=「」『』【】\[\]{}〈〉§]+\s*"
                     r"|有没有|是否|查有无|查是否|(?:一|二|三|四|五|六|七|八|九|十)、"
                     r"|上游指纹|待入账清点|一页纸总览|总览|目录|大纲|结构|五节|五章|章节|清单")
_NEG = re.compile(r"不宣告|不得不|并非不|并不是不|不是不|不得|不能|不可|并未|亦非|"
                  r"未见|未验|未核|未确认|否决|排除|禁止|请勿|无越权|没有不")
_QUOTE = re.compile(r"「[^」]{0,120}」|“[^”]{0,120}”|\"[^\"]{0,120}\"")
_BAN = re.compile(r"不得|不能|不可|禁止|请勿")
_POSTAIL = re.compile(r"(?:已|现|正式)(?:生效|入账|追加)\s*[，,、；;]?\s*"
                      r"(?:可应用|可改|放行|具备|无需|照此|即)")
_CONTRAST = re.compile(r"(?:但|但是|然而|而|且|另外|另|同时|并)\s*[^，。；\n]{0,24}?(?:已入账|已追加|已生效)")
_SUBJ = (r"(?:本笔|本件|该笔|该件|此笔|此件|该条|本条|此条|本节|母本|台账|本候选|本回件|"
         r"本交付件|本项|该项|此项|本草案|该草案|第\s*[一二三四五六七八九十\d]+\s*笔|笔\s*\d+|N-?\d+)")
_SPLIT = re.compile(r"(?:" + _SUBJ + r")\s*(?:已|现|正式|业已|现已|现正式)\s*"
                    r"(?:于\s*§\s*\d+\s*|至\s*台账\S{0,8}\s*|经\s*)?(?:入账|追加|生效)")


def _body(line):
    m = _LEAD.match(line)
    return (line[m.end():], m.end()) if m else (line, 0)


def _seg_of(s, a, b):
    lo, hi = 0, len(s)
    for ch in _SEG:
        j = s.rfind(ch, 0, a)
        if j + 1 > lo:
            lo = j + 1
        j = s.find(ch, a)
        if j != -1 and j < hi:
            hi = j
    return s[lo:hi], a - lo, b - lo


def _subject(pre):
    return bool(_STRUCT.sub("", pre).strip())


def _header(lines, i):
    body, _ = _body(lines[i])
    if not _TROW.match(body):
        return False, False
    nxt, _ = _body(lines[i + 1]) if i + 1 < len(lines) else ("", 0)
    if _TSEP.match(nxt) or re.search(r"[?？]|是否", body):
        return True, True
    return False, True


def _toc(body):
    if not _TOC.search(body) or "。" in body or "；" in body:
        return False
    return bool(re.search(r"§\d+|/\s|\+\s|\|\s|[（(][a-zA-Z0-9]+[）)]", body) or "总览" in body)


def _split_lines(text):
    out = {}
    for li, line in enumerate(text.splitlines(), 1):
        for m in _SPLIT.finditer(line):
            seg, _, _ = _seg_of(line, m.start(), m.end())
            if _NEG.search(seg):
                continue
            if any(q.start() <= m.start() and m.end() <= q.end()
                   for q in _QUOTE.finditer(line)):
                continue
            out.setdefault(li, []).append(m.group(0).strip())
    return out


def _line_positive(body, occ, splits):
    for tok, a, b in occ:
        seg, ra, _ = _seg_of(body, a, b)
        if _NEG.search(seg[:ra]):
            continue
        if _subject(seg[:ra]) or _CONTRAST.search(seg):
            return True
    for m in _POSTAIL.finditer(body):
        seg, _, _ = _seg_of(body, m.start(), m.end())
        if not _NEG.search(seg):
            return True
    return bool(splits)


def r13_assertions(t, tokens=WORDS, r10_scan=None, r12_scan=None):
    """返回 (problems, details)；problems 只含 D 类。C 类必须 R10 同意才豁免。"""
    L = t.splitlines()
    hdr = [_header(L, i) for i in range(len(L))]
    r10, r12 = {}, set()
    if r10_scan:
        for h in r10_scan(t, list(tokens))[2]:
            r10[(h["token"], h["pos"])] = h["kind"]
    if r12_scan:
        for h in r12_scan(t, list(tokens))[1]:
            r12.add((h["token"], h["pos"]))
    splits = _split_lines(t)
    problems, details, base = [], [], 0
    for li, line in enumerate(L):
        body, off = _body(line)
        occ = [(tok, m.start(), m.end()) for tok in tokens
               for m in re.finditer(re.escape(tok), body)]
        if not occ and li + 1 not in splits:
            base += len(line) + 1
            continue
        mixed = _line_positive(body, occ, splits.get(li + 1, []))
        bstruct = _HEAD.match(body) or hdr[li][0] or (_toc(body) and not hdr[li][1])
        for tok, a, b in occ:
            pos = base + off + a
            seg, ra, rb = _seg_of(body, a, b)
            pre, suf = seg[:ra], seg[rb:]
            kind, rule, degraded = "D", "", False
            if mixed:
                rule = "同句混用：行内另有肯定断言"
            elif (tok, pos) in r12:
                rule = "R12 双重否定构式=肯定"
            else:
                neg = bool(_NEG.search(pre)) or bool(
                    any(q.start() <= a and b <= q.end() for q in _QUOTE.finditer(body))
                    and _BAN.search(_QUOTE.sub(" ", body)))
                k = r10.get((tok, pos)) if r10_scan else None
                if neg and k in ("negation", "quote_mention"):
                    kind, rule = "C", "C 否定式（R10 " + k + " 已覆盖）"
                elif neg and r10_scan is None:
                    rule, degraded = "降级：无 R10，C 类不自行豁免 → 默认 FAIL", True
                elif neg:
                    rule = "R10 " + str(k) + "：微段否定不采纳 → 默认 FAIL"
                elif _subject(pre):
                    rule = "D 真断言：微段内 token 前有主语"
                else:
                    hit = _AFTER.search(suf)
                    ask = _ASK.search(pre) and _ASKTAIL.search(seg)
                    if hit or ask:
                        kind, rule = ("B" if bstruct else "A"), (
                            ("B 小节标题/表头/目录：" if bstruct else "A 检索动作：")
                            + repr((hit or _ASK.search(pre)).group(0)))
                    else:
                        rule, degraded = "默认 FAIL：微段内无 A/B 标记且无直接否定", (r10_scan is None)
            details.append({"token": tok, "pos": pos, "line": li + 1,
                            "quote": line.strip(), "kind": kind, "exempt": kind in ("A", "B", "C"),
                            "rule": rule, "r10_kind": r10.get((tok, pos)), "degraded": degraded})
            if kind == "D":
                problems.append("越权断言 %s（N13 D 类，L%d：%s）" % (tok, li + 1, rule))
        base += len(line) + 1
    for li, hits in splits.items():
        for h in hits:
            details.append({"token": h, "pos": -1, "line": li, "quote": L[li - 1].strip(),
                            "kind": "D", "exempt": False, "rule": "词表拆分裂缝：主语+完成动词",
                            "r10_kind": None, "degraded": False})
            problems.append("越权断言 %s（N13 D 类·词表拆分裂缝，L%d：主语+完成动词）" % (h, li))
    return problems, details
