# -*- coding: utf-8 -*-
"""_nnv_gate_limits.py — 核自动发现器自身窗口边界：>4 字间隙 / >2 字后缀的新类能否被发现。"""
import os, re
from collections import Counter
ROOT = r"D:/Project/ra2-campaign-forge/lead"
files = {}
for dp, dn, fn in os.walk(ROOT):
    rel = os.path.relpath(dp, ROOT).replace("\\", "/")
    d = 0 if rel == "." else rel.count("/") + 1
    if d > 2:
        dn[:] = []
        continue
    for f in sorted(fn):
        if not f.lower().endswith(".md"):
            continue
        p = os.path.join(dp, f)
        r = os.path.relpath(p, ROOT).replace("\\", "/")
        if r.startswith("needle_norm_20261109/"):
            continue
        b = open(p, "rb").read()
        if b"\x00" in b:
            continue
        files[r] = b.decode("utf-8", "replace").splitlines()

DISCOVER = re.compile(r"只能判(.{0,4}?)不可复现(.{0,2})")
W4 = re.compile(r"只能判.{0,3}不可复现")
SUPP = re.compile(r"只能判[「『“(]?不可复现[」』”)]?")

def discover(fs):
    c = Counter()
    for ls in fs.values():
        for L in ls:
            for m in DISCOVER.finditer(L):
                c[(m.group(1), m.group(2))] += 1
    return set(c)

base = discover(files)
print("baseline discovered classes =", len(base))
probes = [
    "只能判 —— 不可复现",              # pre 4 字，窗口内
    "只能判  －－－－  不可复现",      # pre >4 字，超窗口
    "只能判「不可复现」＋＋＋",         # post >2 字
    "只能判【不可复现】",               # 新包裹符，窗口内
]
for L in probes:
    fs2 = dict(files)
    fs2["__INJECTED__.md"] = [L]
    diff = discover(fs2) - base
    print("-- %r --" % L)
    print("   自动发现新增类 = %d %s ; 门禁 FAIL? %s" % (len(diff), sorted(diff), bool(diff)))
    print("   W4 召回? %s ; 补充轨召回? %s" % (bool(W4.search(L)), bool(SUPP.search(L))))
print("")
print("注：自动发现器正则 (.{0,4}?) / (.{0,2}) 本身有窗口；超窗口的新变体既不被发现也不被召回，")
print("    门禁不会报警 —— 这是「保证漏了哪类自己不知道」的残余盲区，须如实登记。")
