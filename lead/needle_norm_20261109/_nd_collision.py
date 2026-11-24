# -*- coding: utf-8 -*-
"""_nd_collision.py — 验证哨兵冲突行及旧 L1 在该行上的行为。"""
import re
p = r"D:/Project/ra2-campaign-forge/lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
L = open(p, encoding="utf-8").read().splitlines()[3464]
print("line 3465 repr prefix:", repr(L[:260]))
print("contains 只能判 / 不可复现 :", ("只能判" in L), ("不可复现" in L))
print("sentinel \\x01 positions:", [i for i, c in enumerate(L) if ord(c) == 1])
print("has raw 只能判「不可复现」 :", "只能判「不可复现」" in L)
print("has raw 只能判『不可复现』 :", "只能判『不可复现』" in L)
print("W4 regex hit :", bool(re.search("只能判.{0,3}不可复现", L)))

QO, QC, SYM = "「『“‘", "」』”’", "`\"'"
def norm(s):
    out = []
    for c in s:
        if c in QO: out.append("\x01")
        elif c in QC: out.append("\x02")
        elif c in SYM: out.append("\x03")
        else: out.append(c)
    return "".join(out)
kN = norm("只能判「不可复现」")
print("old-L1 norm(line).find(canon_key) =", norm(L).find(kN))
