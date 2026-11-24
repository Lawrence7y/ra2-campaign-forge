# -*- coding: utf-8 -*-
"""_rs_hits.py — dump every hit line (exact 2 needles) with block membership,
quotation/negation signals, and file nature. Read-only.
"""
import os, re, hashlib

ROOT = "D:/Project/ra2-campaign-forge/lead"
N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"

# Anchored marker regexes (line must BE a marker, not merely mention one)
START = re.compile(r"^\s*(?:<!--[^>]*草案正文[^>]*逐字转录开始|#{1,6}\s*↓{2,}[^\n]*草案正文|↓{3,}\s*草案正文\s*↓{3,})")
END = re.compile(r"^\s*(?:<!--[^>]*草案正文[^>]*逐字转录结束|#{1,6}\s*↑{2,}[^\n]*草案正文|↑{3,}\s*草案正文[^\n]*↑{3,})")

NEG = ["不再成立", "过时", "已定谳", "已闭合", "已定位", "被推翻", "被超越",
       "改前", "改后", "建议改", "引文", "原句", "逐字", "grep", "命中",
       "不成立", "否证", "取代", "自本节起", "不影响", "不再计入", "不可引用",
       "误读", "瑕疵", "未验项", "复核", "验收", "错误步骤已"]
QUOTE = ["`", "「", "』", ">", "|"]

def blocks(ls):
    stack = []; out = []
    for i, L in enumerate(ls, 1):
        if START.match(L):
            stack.append(i)
        elif END.match(L):
            if stack:
                out.append((stack.pop(), i))
    return sorted(out + [(s, len(ls)) for s in stack])

def md_files():
    for dp, dn, fn in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT).replace("\\", "/")
        d = 0 if rel == "." else rel.count("/") + 1
        if d > 2:
            continue
        for f in fn:
            if f.lower().endswith(".md"):
                yield os.path.join(dp, f), os.path.relpath(os.path.join(dp, f), ROOT).replace("\\", "/")

if __name__ == "__main__":
    tot = 0
    for p, rel in sorted(md_files(), key=lambda x: x[1]):
        b = open(p, "rb").read()
        ls = b.decode("utf-8", "replace").splitlines()
        hits = [i for i, L in enumerate(ls, 1) if N1 in L or N2 in L]
        if not hits:
            continue
        bl = blocks(ls)
        print("=" * 96)
        print("FILE %s  bytes=%d lines=%d sha256=%s" %
              (rel, len(b), len(ls), hashlib.sha256(b).hexdigest()))
        print("  blocks =", bl)
        for n in hits:
            L = ls[n - 1]
            inside = [(a, z) for a, z in bl if a < n < z]
            negs = [k for k in NEG if k in L]
            tot += 1
            print("  :%-4d IN_BLOCK=%-5s %-14s needles=%s neg=%s" %
                  (n, bool(inside), str(inside) if inside else "",
                   ("N1" if N1 in L else "") + ("+N2" if N2 in L else ""),
                   ",".join(negs) if negs else "-"))
            print("        | %s" % L[:250])
    print("=" * 96)
    print("TOTAL HIT LINES (dir-depth<=2) =", tot)
