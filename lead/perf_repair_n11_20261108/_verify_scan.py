# -*- coding: utf-8 -*-
"""Independent reviewer: prohibited-term scan + grade/branch-language scan over write domain."""
import os, re

WD = r"D:/Project/ra2-campaign-forge/lead/perf_repair_n11_20261108"

# Sampling / injection / live-process / dynamic-resolution prohibitions
BAD = [
    "gamemd.exe", "ra2loader", "YURI.exe", "taskkill",
    "MiniDump", "SuspendThread", "StackWalk", "OpenProcess", "ReadProcessMemory",
    "WriteProcessMemory", "VirtualAllocEx", "CreateRemoteThread", "SetWindowsHookEx",
    "ctypes", "windll", "kernel32", "GetProcAddress", "LoadLibrary",
    "探针注入", "hook", "HOOK", "采样代码", "注入",
    "import ctypes", "from ctypes",
]
# Terms that indicate CAUSAL_READY / collection-release / guess values (should be negated)
SENSITIVE = ["CAUSAL_READY", "放行采集", "修复候选", "修复完成", "猜值", "签发人"]

def scan(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()

for name in sorted(os.listdir(WD)):
    p = os.path.join(WD, name)
    if not os.path.isfile(p) or not name.endswith((".py", ".md", ".txt")):
        continue
    L = scan(p)
    hits = []
    for i, t in enumerate(L, 1):
        for b in BAD:
            if b in t:
                hits.append((i, b, t.strip()[:140]))
    print("=== %s : %d lines ===" % (name, len(L)))
    if hits:
        for i, b, t in hits:
            print("  HIT %s L%d [%s]: %s" % (name, i, b, t))
    else:
        print("  no prohibited-term hits")

print()
print("=== grade / branch / boundary language in main deliverable ===")
H = os.path.join(WD, "_n11_PERF_REPAIR_HANDOFF.md")
L = scan(H)
for i, t in enumerate(L, 1):
    for s in SENSITIVE:
        if s in t:
            print("  L%d: %s" % (i, t.strip()[:260]))
            break

print()
print("=== '待裁' / '未验' / 'BLOCKED' counts ===")
for kw in ["待裁", "未验", "BLOCKED", "不放行", "不自动扩大", "未真机", "不填猜值", "HANDOFF_COMPLETE"]:
    c = sum(1 for t in L if kw in t)
    print("  %s : %d lines" % (kw, c))
