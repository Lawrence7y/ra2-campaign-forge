# -*- coding: utf-8 -*-
# _c7_probe4.py — 台账 C07/Q6/身份落实登记面检索（只读）+ NEXT:23/:119 原文行号核验
import os, re

ROOT = r"D:\Project\ra2-campaign-forge"
PAT = re.compile(r"C07|Q6|责任身份|身份补登|补登.*身份|身份.*落实|reviewerSessionId|sourceTaskId|签发角色")

targets = [
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
]
for rel in targets:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    with open(p, "rb") as f:
        raw = f.read().decode("utf-8", errors="replace")
    lines = raw.splitlines()
    print("== %s (总行数=%d) ==" % (rel, len(lines)))
    n = 0
    for i, ln in enumerate(lines, 1):
        if PAT.search(ln):
            n += 1
            s = ln.strip()
            if len(s) > 200:
                s = s[:200] + "…"
            print("  :%d: %s" % (i, s))
    if n == 0:
        print("  （无命中）")
    print()
