#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""定向核查：006C9890 的宿主 007BA590 与包装器 00477770；
另含 TechnoClass 低地址命中 006F450D、AircraftClass 宿主 00413D20 的完整反汇编。"""
import os, sys, io, re, json, struct, hashlib, bisect, collections
sys.dont_write_bytecode = True
import capstone
from capstone import x86 as X

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROJ = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(PROJ, "ra2youli", "gamemd.exe")

pe_raw = open(EXE, "rb").read()
pe_off = struct.unpack_from("<I", pe_raw, 0x3C)[0]
nsec = struct.unpack_from("<H", pe_raw, pe_off + 6)[0]
optsize = struct.unpack_from("<H", pe_raw, pe_off + 20)[0]
opt = pe_off + 24
BASE = struct.unpack_from("<I", pe_raw, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + optsize + i * 40
    nm = pe_raw[o:o + 8].rstrip(b"\0").decode("latin-1")
    vs, va, rs, rp = struct.unpack_from("<IIII", pe_raw, o + 8)
    secs.append((nm, BASE + va, vs, rs, rp))
buf = bytearray(BASE and (max(v + max(vs, rs) for (n, v, vs, rs, rp) in secs) - BASE + 16) or 0)
for (nm, va, vs, rs, rp) in secs:
    o = va - BASE
    n = min(rs, len(pe_raw) - rp)
    if n > 0:
        buf[o:o + n] = pe_raw[rp:rp + n]

def code(va, n):
    o = va - BASE
    return bytes(buf[o:o + n])

def u32(va):
    o = va - BASE
    return struct.unpack_from("<I", buf, o)[0] if 0 <= o and o + 4 <= len(buf) else None

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True
md.skipdata = True
mdc = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); mdc.detail = True

atlas = {}
for i, ln in enumerate(io.open(os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv"), encoding="utf-8-sig")):
    if i == 0: continue
    c = ln.rstrip("\r\n").split("\t")
    if len(c) >= 2:
        try: atlas[int(c[0].strip(), 16)] = int(c[1])
        except ValueError: pass
AS = sorted(atlas)
def fn_of(va):
    i = bisect.bisect_right(AS, va)
    for j in range(i - 1, max(-1, i - 4), -1):
        a = AS[j]
        if a <= va < a + atlas[a]: return a
    return None

H = lambda v: "%08X" % v

def dump(start, n=0x120, tag=""):
    print("\n----- %s @%s -----" % (tag, H(start)))
    for ins in md.disasm(code(start, n), start):
        print("  %08X: %-22s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    print("  (atlas fn of this addr = %s, size=%s)" % (H(fn_of(start)) if fn_of(start) else None,
                                                        atlas.get(fn_of(start)) if fn_of(start) else None))

dump(0x7BA590, 0xC0, "006C9890 声称宿主 007BA590（FileStraw 析构器？）")
dump(0x7BA420, 0xA0, "对照：007BA420（B3 审计认定 FilePipe 析构器）")
dump(0x477770, 0x80, "声称包装器 00477770")
dump(0x477790, 0x60, "对照包装器 00477790（B3 审计文件）")
print("\n=== callers of 007BA590 (linear scan of .text) ===")
tva = [s for s in secs if s[0] == ".text"][0][1]
tsz = [s for s in secs if s[0] == ".text"][0][2]
found = []
for ins in md.disasm(code(tva, tsz), tva):
    if ins.mnemonic.startswith(".") or ins.id == 0:
        continue
    try:
        ops = ins.operands
    except Exception:
        continue
    if ins.mnemonic == "call" and len(ops) == 1 and ops[0].type == X.X86_OP_IMM:
        if (ops[0].imm & 0xFFFFFFFF) == 0x7BA590:
            found.append(ins.address)
print([H(x) for x in found], "-> host fns:", [H(fn_of(x)) if fn_of(x) else None for x in found])

print("\n=== vptr stores for vt 007E4D90 (all disps) ===")
n = 0
for ins in md.disasm(code(tva, tsz), tva):
    if ins.mnemonic != "mov":
        continue
    try:
        ops = ins.operands
    except Exception:
        continue
    if len(ops) != 2: continue
    d, s = ops
    if d.type != X.X86_OP_MEM or s.type != X.X86_OP_IMM: continue
    if (s.imm & 0xFFFFFFFF) != 0x7E4D90: continue
    n += 1
    b = ins.reg_name(d.mem.base) if d.mem.base else "ABS"
    print("  %08X  %-40s base=%-4s disp=%s host=%s" % (ins.address, ins.mnemonic + " " + ins.op_str,
          b, hex(d.mem.disp), H(fn_of(ins.address)) if fn_of(ins.address) else None))
print("  total stores =", n)
