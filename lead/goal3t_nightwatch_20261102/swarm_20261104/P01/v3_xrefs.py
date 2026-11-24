# -*- coding: utf-8 -*-
"""P01 v3 —— inc/dec 其余调用点上下文 + 渐变启动器 + 渐变机全态 + 0x887324 vtable。"""
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


def line(t):
    return "%08X  %-20s %-7s %s" % (t[0], t[2], t[3], t[4])


def dump_win(f, lo, hi):
    for t in tup:
        if lo <= t[0] < hi:
            f.write(line(t) + "\n")


with open(out("H_xref_ctx.txt"), "w", encoding="utf-8") as f:
    for nm, lo, hi in [
        ("inc_caller_657CA0", 0x657C40, 0x657D20),
        ("dec_caller_657CC8_same", 0x657C40, 0x657D20),
        ("inc_caller_6DF703", 0x6DF680, 0x6DF780),
        ("inc_caller_6E4086", 0x6E3FC0, 0x6E40D0),
        ("fade_starter_539875", 0x539820, 0x5398C0),
        ("fade_pre_block_53B4C0", 0x53B4C0, 0x53B560),
        ("fade_machine_rest", 0x53B617, 0x53B790),
        ("helpers_406F00_406F40", 0x406F00, 0x406F80),
        ("helper_54F720", 0x54F720, 0x54F770),
        ("mlf_caller_48CE8A", 0x48CE40, 0x48CEB0),
        ("timer_writers_mlf_pace", 0x55D760, 0x55D7C2),
    ]:
        f.write("\n==== %s [%X,%X) ====\n" % (nm, lo, hi))
        dump_win(f, lo, hi)

# 0x887324 的 vtable 抽取：写点上下文中找 mov [reg],imm 的 vtable imm
hs = [(va, ops) for (va, rw, mn, ops) in
      [(v, r, m, o) for (v, r, m, o) in
       [(t[0], None, t[3], t[4]) for t in tup] ] if False]
# 直接扫写 0x887324 的指令上下文
for (va, sz, b, mn, ops) in tup:
    if ops.startswith("[0x887324]") or ", [0x887324]" in ops:
        k = idx[va]
        ctx = tup[max(0, k - 6):k + 2]
        if mn == "mov" and ops.startswith("[0x887324]"):
            # mov [0x887324], reg 或 imm
            print("W %08X %s %s" % (va, mn, ops), flush=True)
            for c in ctx:
                # 找相邻的 mov eax,imm / push imm vtable 模式
                if "0x7e" in c[4] or "0x8" in c[4][:8] or c[3] == "mov":
                    print("   ctx %08X %s %s" % (c[0], c[3], c[4]), flush=True)

print("DONE v3", flush=True)
