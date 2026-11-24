# -*- coding: utf-8 -*-
"""P01 v4 —— 渐变启动器头/调用者、ret0x10 小方法归主、0x684240/0x684290 追帧对、指针表搜索。"""
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

# 函数头集合（与 v1 同口径）
starts = {0x55D360, 0x55E160}
for (va, sz, b, mn, ops) in tup:
    if mn.startswith("ret"):
        starts.add(va + sz)
    elif mn == "call" and ops.startswith("0x"):
        try:
            starts.add(int(ops, 16))
        except ValueError:
            pass
sstarts = sorted(starts)


def fstart(va):
    k = 0
    lo, hi = 0, len(sstarts)
    while lo < hi:
        mid = (lo + hi) // 2
        if sstarts[mid] <= va:
            k = mid
            lo = mid + 1
        else:
            hi = mid
    return sstarts[k] if sstarts and sstarts[k] <= va else None


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


def line(t):
    return "%08X  %-20s %-7s %s" % (t[0], t[2], t[3], t[4])


def dump_win(f, lo, hi):
    for t in tup:
        if lo <= t[0] < hi:
            f.write(line(t) + "\n")


TARGETS = [0x6DF6FD, 0x6E4080, 0x6E4020, 0x6E4040]
for t in TARGETS:
    fs = fstart(t)
    cs = call_sites(t)
    print("method %08X fstart~%s callsites=%s" % (t, hex(fs) if fs else "?",
          [("%08X" % x) + ":" + m for x, m in cs]), flush=True)

# 渐变启动器：包含 0x53B4EB 的函数头
fs_fade = fstart(0x53B4EB)
print("fade-starter head ~ %s" % (hex(fs_fade) if fs_fade else "?"), flush=True)
cs_fade = call_sites(fs_fade)
print("fade-starter callers: %s" % [("%08X" % x) + ":" + m for x, m in cs_fade], flush=True)

# 0x657CA0 所在函数头与调用者
fs_657 = fstart(0x657C42)
print("0x657C42 fstart~%s callers=%s" % (hex(fs_657) if fs_657 else "?",
      [("%08X" % x) + ":" + m for x, m in call_sites(fs_657)]), flush=True)

# 指针表搜索：.rdata/.data 中指向这些函数的 dword
PTR_DATA = {}
for nm, sva, vsz, rp, rsz in eng.SEC:
    if nm in (".rdata", ".data"):
        blob = eng.raw[rp:rp + rsz]
        PTR_DATA[nm] = (sva, blob)

WANT = set(TARGETS) | {fs_fade, fs_657, 0x684060, 0x684180, 0x684240, 0x684290}
for nm, (sva, blob) in PTR_DATA.items():
    for w in sorted(x for x in WANT if x):
        needle = struct.pack("<I", w)
        off = 0
        while True:
            off = blob.find(needle, off)
            if off < 0:
                break
            if off % 4 == 0:
                print("ptr %08X -> %08X in %s at %08X" % (sva + off, w, nm, sva + off), flush=True)
            off += 1

with open(out("I_final_dumps.txt"), "w", encoding="utf-8") as f:
    if fs_fade:
        f.write("\n==== fade-starter head %X..0x53B560 ====\n" % fs_fade)
        dump_win(f, fs_fade, 0x53B560)
    f.write("\n==== catchup pair 0x684240..0x684300 ====\n")
    dump_win(f, 0x684240, 0x684300)
    for t in TARGETS:
        fs = fstart(t)
        if fs:
            f.write("\n==== method %X head ====\n" % fs)
            dump_win(f, fs, fs + 0x30)
print("DONE v4", flush=True)
