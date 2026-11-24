# -*- coding: utf-8 -*-
"""P01 v5 —— 渲染单例 vtable+0x5C 定位 + 正常体/冻结体调用普查。"""
import os
import sys
import pickle
import struct

BASE = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(BASE, "..")))
from ra2tool import Engine


def out(name):
    p = os.path.normpath(os.path.join(BASE, name))
    if not p.startswith(BASE):
        raise ValueError("refuse: %s" % p)
    return p


eng = Engine()
with open(out("stream_cache.pkl"), "rb") as f:
    tup = pickle.load(f)
idx = {t[0]: k for k, t in enumerate(tup)}

# ctor 0x6D1C20 头部：找 vtable imm
print("ctor 0x6D1C20 head:", flush=True)
for t in tup:
    if 0x6D1C20 <= t[0] < 0x6D1C60:
        print("  %08X  %-18s %s %s" % (t[0], t[2], t[3], t[4]), flush=True)

vt = None
for t in tup:
    if 0x6D1C20 <= t[0] < 0x6D1C50 and t[3] == "mov":
        m = t[4].split(", ")
        if len(m) == 2 and m[0] in ("dword ptr [eax]", "dword ptr [ecx]") and m[1].startswith("0x"):
            vt = int(m[1], 16)
            break
print("vtable = %s" % (hex(vt) if vt else "?"), flush=True)
if vt:
    tgt = eng.u32(vt + 0x5C)
    print("vtable+0x5C -> %08X" % tgt, flush=True)
    print("bytes at %08X: %s" % (tgt, eng.rd(tgt, 8).hex()), flush=True)
    for t in tup:
        if tgt <= t[0] < tgt + 0x40:
            print("  %08X  %-18s %s %s" % (t[0], t[2], t[3], t[4]), flush=True)

# 正常体调用普查
from collections import Counter
calls = Counter()
for (va, sz, b, mn, ops) in tup:
    if 0x55D878 <= va < 0x55DE4F and mn == "call" and ops.startswith("0x"):
        try:
            calls[int(ops, 16)] += 1
        except ValueError:
            pass
print("normal-body unique call targets: %d" % len(calls), flush=True)
for tgt, n in sorted(calls.items()):
    print("  -> %08X x%d" % (tgt, n), flush=True)

# 冻结体调用普查
calls2 = Counter()
for (va, sz, b, mn, ops) in tup:
    if 0x55D830 <= va < 0x55D859 and mn == "call" and ops.startswith("0x"):
        try:
            calls2[int(ops, 16)] += 1
        except ValueError:
            pass
print("freeze-body targets: %s" % ["%08X" % t for t in sorted(calls2)], flush=True)
print("DONE v5", flush=True)
