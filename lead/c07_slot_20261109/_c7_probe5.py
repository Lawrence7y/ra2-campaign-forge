# -*- coding: utf-8 -*-
# _c7_probe5.py — 草案任务书身份槽位检索 + 台账 N-10/N-11 登记面检索（只读）
import os, re

ROOT = r"D:\Project\ra2-campaign-forge"

def grep(rel, pat, maxlen=200):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    with open(p, "rb") as f:
        raw = f.read().decode("utf-8", errors="replace")
    lines = raw.splitlines()
    print("== %s (总行数=%d) pattern=%r ==" % (rel, len(lines), pat))
    n = 0
    for i, ln in enumerate(lines, 1):
        if re.search(pat, ln):
            n += 1
            s = ln.strip()
            if len(s) > maxlen:
                s = s[:maxlen] + "…"
            print("  :%d: %s" % (i, s))
    if n == 0:
        print("  （无命中）")
    print()

grep("lead/bexec_n4_20261108/B_EXECUTION_SPEC.md", r"APPROVE_SCOPE|session|run ID|签发|身份|任务书编号|SPEC_DRAFT|不生效")
grep("lead/PENDING_DECISIONS.md", r"N-10|N-11|PERF_REPAIR|D13D14|DECISION_QUESTIONS|问题卡")
grep("lead/GOAL_THREE_TARGETS_20261018.md", r"N-10|N-11|PERF_REPAIR_HANDOFF|D13D14|DECISION_QUESTIONS")
