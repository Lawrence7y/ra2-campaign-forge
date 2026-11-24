# -*- coding: utf-8 -*-
"""_ncv_taskbooks.py -- 独立解 .mjs payload 的 lowered，核「贴了≠用了」原文。

不采信 _nc_taskbook_*_hits.txt；自己 json.loads 第 9 行，按行号打印命中与上下文。
只读输入，输出仅 stdout。
"""
import io
import json
import os
import re

ROOT = r"D:\Project\ra2-campaign-forge"
TB89 = os.path.join(ROOT, ".zcode", "workflow-runs",
                    "dwfrun-89df48db-a7c0-4905-85b8-68da3f294695.mjs")
TB86 = os.path.join(ROOT, ".zcode", "workflow-runs",
                    "dwfrun-868215ce-ea87-4e41-a54b-5a0af3c441dd.mjs")


def lowered(path):
    for l in io.open(path, "r", encoding="utf-8").read().split("\n"):
        if l.startswith("export const payload"):
            body = l[len("export const payload = "):].rstrip().rstrip(";")
            return json.loads(body)["lowered"].split("\n")
    raise RuntimeError("no payload")


def dump(tag, path, needles, windows):
    L = lowered(path)
    print("=== %s : %s : n_lowered_lines=%d ===" % (tag, os.path.basename(path), len(L)))
    for needle in needles:
        hits = [(i + 1, s.strip()) for i, s in enumerate(L) if needle in s]
        print("--- needle %r : %d hits ---" % (needle, len(hits)))
        for ln, s in hits:
            print("  lowered:%d | %s" % (ln, s[:300]))
    for a, b in windows:
        print("--- context lowered:%d-%d ---" % (a, b))
        for i in range(a - 1, min(b, len(L))):
            print("  lowered:%d | %s" % (i + 1, L[i].strip()[:300]))


dump("89df", TB89,
     ["32768", "16384", "0.14013134", "0.8599", "0.14013", "vfText", "fpText", "0.86"],
     [(30, 40), (60, 70), (100, 125)])
dump("8682", TB86,
     ["rjText", "10 个域", "5 个", "十个域", "32 域双轨重判结果", "publishArtifact", "10 个", "结论"],
     [(90, 115), (128, 136), (164, 172), (212, 230)])

# 下游更正件在盘行
rj = io.open(os.path.join(ROOT, "lead", "gate_rejudge32_20261109", "GATE_REJUDGE_32.md"),
             "r", encoding="utf-8").read().split("\n")
print("=== GATE_REJUDGE_32.md cited lines ===")
for ln in (51, 53, 56, 161, 289):
    print("  :%d | %s" % (ln, rj[ln - 1].strip()[:300]))
