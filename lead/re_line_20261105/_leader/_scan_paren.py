# -*- coding: utf-8 -*-
"""逐行扫描草稿的括号平衡，跳过字符串字面量内部。只读。"""
import io

P = r"D:/Project/ra2-campaign-forge/.zcode/workflow-drafts/W4-四VA字段规格卡.dwf.ts"
BT = chr(96)
SQ = chr(39)
DQ = chr(34)
BS = chr(92)

depth = 0
for ln, line in enumerate(io.open(P, encoding="utf-8").read().split("\n"), 1):
    before = depth
    i = 0
    in_str = None
    while i < len(line):
        c = line[i]
        if in_str:
            if c == BS:
                i += 2
                continue
            if c == in_str:
                in_str = None
        else:
            if c in (BT, SQ, DQ):
                in_str = c
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
        i += 1
    if depth != before:
        print("L%-4d depth %d -> %d   %s" % (ln, before, depth, line.strip()[:90]))
print("final depth:", depth)
