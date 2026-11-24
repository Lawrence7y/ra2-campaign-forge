# -*- coding: utf-8 -*-
"""检查工作流草稿里未配对的反引号（模板字符串定界符）。只读。"""
import io

P = r"D:/Project/ra2-campaign-forge/.zcode/workflow-drafts/D-17D-18-裁决GPT-6.1-Sol-medium.dwf.ts"
BT = chr(96)
BS = chr(92)

lines = io.open(P, encoding="utf-8").read().split("\n")
bad = 0
for i, line in enumerate(lines, 1):
    n = 0
    j = 0
    while j < len(line):
        if line[j] == BT and (j == 0 or line[j - 1] != BS):
            n += 1
        j += 1
    if n % 2 == 1:
        bad += 1
        print("ODD line %d (count=%d): %s" % (i, n, line.strip()[:150]))
print("total odd lines:", bad)
