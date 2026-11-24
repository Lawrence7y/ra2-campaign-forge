# -*- coding: utf-8 -*-
"""P01 v2 —— 0x684060/0x684180/0x683610 全函数 + 渐变机/时钟/显示对象身份。"""
import os
import sys
import re
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
print("coverage = %.2f%% / %d" % eng.coverage[:2], flush=True)

with open(out("stream_cache.pkl"), "rb") as f:
    import pickle
    tup = pickle.load(f)
print("cache insns=%d (cache-only run)" % len(tup), flush=True)

idx = {t[0]: k for k, t in enumerate(tup)}


def line(t):
    return "%08X  %-20s %-7s %s" % (t[0], t[2], t[3], t[4])


def dump_win(f, lo, hi):
    for t in tup:
        if lo <= t[0] < hi:
            f.write(line(t) + "\n")


def call_sites(target):
    res = []
    for (va, sz, b, mn, ops) in tup:
        if mn in ("call", "jmp") and ops.startswith("0x"):
            try:
                if int(ops, 16) == target:
                    res.append((va, mn))
            except ValueError:
                pass
    return res


def disp_hits_fast(va):
    """cache-based 等价 eng.disp_hits（detail 已含在 mnemonic/op_str，写判按助记符+操作数序）。"""
    res = []
    pat = re.compile(r"0x%x\b" % va)
    for (va2, sz, b, mn, ops) in tup:
        if mn in ("mov", "movzx", "movsx", "lea", "cmp", "test", "add", "sub",
                  "inc", "dec", "or", "and", "xor", "push", "imul", "add"):
            parts = ops.split(", ")
            for i, p in enumerate(parts):
                if pat.search(p) and ("[" in p):
                    # W 判：dst(=第一操作数)为内存
                    w = (i == 0)
                    res.append((va2, "W" if w else "R", mn, ops))
                    break
    return res


with open(out("F_hold_funcs.txt"), "w", encoding="utf-8") as f:
    for nm, lo, hi in [("hold_inc_0x684060", 0x684060, 0x684180),
                       ("hold_dec_0x684180", 0x684180, 0x684244),
                       ("zero_writer_0x683610", 0x6835A0, 0x683720),
                       ("fade_caller_ctx_0x53A747", 0x53A5C0, 0x53A7C0),
                       ("clock_0x6C8C40", 0x6C8C40, 0x6C8C90),
                       ("mlf_pre_freeze_0x55D3C0", 0x55D3C0, 0x55D7C2),
                       ("normal_body_calls", 0x55D878, 0x55DE50)]:
        f.write("\n==== %s [%X,%X) ====\n" % (nm, lo, hi))
        dump_win(f, lo, hi)

# 函数尾验证：0x684060 与 0x684180 的 ret/边界
for nm, lo, hi in [("0x684060", 0x684060, 0x684200), ("0x684180", 0x684180, 0x684300),
                   ("0x683610", 0x683610, 0x683800)]:
    rs = [t[0] for t in tup if lo <= t[0] < hi and t[3].startswith("ret")]
    print("rets in [%s]: %s" % (nm, [hex(x) for x in rs]), flush=True)

# XREF
for tgt in (0x684060, 0x684180, 0x53B560, 0x683610, 0x6C8C40, 0x53BBA0, 0x4A4830):
    cs = call_sites(tgt)
    print("xrefs->%08X: %d %s" % (tgt, len(cs), [("%08X" % x) + ":" + m for x, m in cs][:30]), flush=True)

# 渐变状态机全局
for g in (0xA9FAB0, 0xA9FA98, 0x887324, 0x887640, 0x88731C, 0xA8ED9C, 0xABCD58,
          0x87F7E8, 0x87F770, 0x887350, 0x887348, 0xB07784, 0x887640):
    hs = disp_hits_fast(g)
    ws = [h for h in hs if h[1] == "W"]
    print("g %08X refs=%d W=%d %s" % (g, len(hs), len(ws), [hex(w[0]) for w in ws][:12]), flush=True)

# [0x887324] 对象 vtable：找写点上下文里的 imm vtable
hs = disp_hits_fast(0x887324)
with open(out("G_887324.txt"), "w", encoding="utf-8") as f:
    for (va, rw, mn, ops) in hs:
        f.write("%08X %s %s %s\n" % (va, rw, mn, ops))
        if rw == "W":
            k = idx[va]
            f.write("".join("  ctx " + line(tup[j]) + "\n" for j in range(max(0, k - 8), min(len(tup), k + 4))))

# 字符串（新窗口）
def cstr(va, n=96):
    raw = eng.rd(va, n)
    z = raw.find(b"\0")
    if z < 0:
        z = n
    s = raw[:z]
    if len(s) >= 4 and all(32 <= c < 127 for c in s):
        return s.decode("ascii")
    return None


DATA = [(nm, sva, sva + vsz) for (nm, sva, vsz, rp, rsz) in eng.SEC]


def strings_in(lo, hi, acc):
    for (va, sz, b, mn, ops) in tup:
        if lo <= va < hi and ops.startswith("0x"):
            try:
                imm = int(ops, 16)
            except ValueError:
                continue
            for nm, a, bb in DATA:
                if nm != ".text" and a <= imm < bb:
                    s = cstr(imm)
                    if s:
                        acc.append((va, imm, s))
                    break


with open(out("S2_strings.txt"), "w", encoding="utf-8") as f:
    for nm, lo, hi in [("hold_inc", 0x684060, 0x684180), ("hold_dec", 0x684180, 0x684244),
                       ("zero_writer", 0x6835A0, 0x683720), ("fade_machine", 0x53B560, 0x53B960),
                       ("fade_caller", 0x53A5C0, 0x53A7C0), ("mlf_pre_freeze", 0x55D3C0, 0x55D7C2),
                       ("normal_body", 0x55D878, 0x55DE50)]:
        acc = []
        strings_in(lo, hi, acc)
        f.write("\n==== %s ====\n" % nm)
        for (va, imm, s) in acc:
            f.write("%08X -> %08X \"%s\"\n" % (va, imm, s))
        print("strings %s: %d" % (nm, len(acc)), flush=True)

# IAT 常量
for slot in (0x7E14F4, 0x7E14F8, 0x7E14BC, 0x7E1530, 0x7E11F0):
    print("iat %08X = %s" % (slot, eng.resolve_iat(slot)), flush=True)

# 0x6C8C40 内部是否走 IAT
print("clock head bytes:", eng.rd(0x6C8C40, 16).hex(), flush=True)
print("DONE v2", flush=True)
