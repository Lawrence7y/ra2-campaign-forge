#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""小工具：按地址范围 dump 反汇编（只读）"""
import os, sys, io, struct, bisect, capstone
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE); PROJ = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(PROJ, "ra2youli", "gamemd.exe")
raw = open(EXE, "rb").read()
po = struct.unpack_from("<I", raw, 0x3C)[0]
ns = struct.unpack_from("<H", raw, po + 6)[0]
os_ = struct.unpack_from("<H", raw, po + 20)[0]
opt = po + 24
BASE = struct.unpack_from("<I", raw, opt + 28)[0]
secs = []
for i in range(ns):
    o = opt + os_ + i * 40
    nm = raw[o:o + 8].rstrip(b"\0").decode("latin-1")
    vs, va, rs, rp = struct.unpack_from("<IIII", raw, o + 8)
    secs.append((nm, BASE + va, vs, rs, rp))
buf = bytearray(max(v + max(vs, rs) for (n, v, vs, rs, rp) in secs) - BASE + 16)
for (nm, va, vs, rs, rp) in secs:
    o = va - BASE
    buf[o:o + min(rs, len(raw) - rp)] = raw[rp:rp + min(rs, len(raw) - rp)]
def code(va, n): return bytes(buf[va - BASE:va - BASE + n])
atlas = {}
for i, ln in enumerate(io.open(os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv"), encoding="utf-8-sig")):
    if i == 0: continue
    c = ln.rstrip("\r\n").split("\t")
    if len(c) >= 2:
        try: atlas[int(c[0].strip(), 16)] = int(c[1])
        except ValueError: pass
AS = sorted(atlas)
def fn_of(v):
    i = bisect.bisect_right(AS, v)
    for j in range(i - 1, max(-1, i - 4), -1):
        a = AS[j]
        if a <= v < a + atlas[a]: return a
    return None
H = lambda v: "%08X" % v
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True
for arg in sys.argv[1:]:
    st = int(arg, 16)
    f = fn_of(st)
    print("\n=== %s  (atlas fn=%s size=%s) ===" % (H(st), H(f) if f else None, atlas.get(f) if f else None))
    for ins in md.disasm(code(st, 0x100), st):
        print("  %08X: %-20s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
