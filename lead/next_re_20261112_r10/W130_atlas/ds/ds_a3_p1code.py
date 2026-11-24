#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A3 (P1): are the 87 .text hits inside actual code?  Linear-disassemble .text
with skipdata, then check instruction coverage at each hit address."""
from __future__ import annotations
import json
from collections import Counter
import capstone
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from ds_img import BASE, IMG, SECS, sec_of, in_raw, u32, rd, secname

J = json.loads(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json",
                    encoding="utf-8").read())
vt = {int(k, 16): v for k, v in J["vt2name"].items()}
text = sorted(a for a in vt if secname(a) == ".text")

t = next(s for s in SECS if s.name == ".text")
code = IMG[t.va - BASE: t.va - BASE + t.vsize]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
md.skipdata = True          # <<< mandatory
print("skipdata enabled:", md.skipdata)

# coverage map: set of instruction START addresses; plus list of (start,size)
starts = {}
db_bytes = 0
n_insn = 0
for ins in md.disasm(code, t.va):
    starts[ins.address] = ins.size
    n_insn += 1
print(f"linear sweep: {n_insn} insn, covered bytes {sum(starts.values())}, .text vsize {t.vsize}")

print()
print("=== for each of the 87: is the address an instruction boundary? ===")
res = Counter()
detail = []
for a in text:
    if a in starts:
        kind = "INSN-START"
    else:
        # find containing instruction
        prev = [s for s in starts if s <= a < s + starts[s]]
        kind = f"inside insn @0x{prev[0]:08X}" if prev else "NO PREV"
    res[kind.split(" ")[0]] += 1
    detail.append((a, vt[a], kind, u32(a), u32(a - 4)))
for k, v in res.items():
    print(f"  {k:<12}{v}")

print()
print("=== show the disassembly context for 12 representative hits ===")
show = [0x443B24, 0x45CC44, 0x46C2D8, 0x48CA50, 0x49DCD0, 0x4AC194, 0x4CD864,
        0x5DA8A0, 0x5FE874, 0x5FF6A0, 0x659BB0, 0x7CB8A4]
for a in show:
    lo = a - 0x10
    print(f"\n--- 0x{a:08X}  {vt[a]}   [a-4]=0x{u32(a-4):08X}  [a]=0x{u32(a):08X} ---")
    n = 0
    for ins in md.disasm(IMG[lo - BASE: a + 0x10 - BASE], lo):
        mark = " <<<" if ins.address == a else ("     " if ins.address + ins.size <= a else "  ~~")
        if ins.address + ins.size > a and ins.address < a:
            mark = "  ~~ (hit is INSIDE this insn)"
        print(f"  0x{ins.address:08X} {ins.bytes.hex():<20}{ins.mnemonic:<8}{ins.op_str}{mark}")
        n += 1
        if n > 30:
            break

print()
print("=== control: pick 87 random .text addresses NOT in the map, same test ===")
import random
random.seed(1234)
pool = [v for v in starts if t.va <= v < t.va + t.vsize]
ctrl = random.sample(pool, 87)
# random non-boundary addresses
ctrl2 = [t.va + random.randrange(0, t.vsize - 4) for _ in range(87)]
c1 = sum(1 for a in ctrl if a in starts)
c2 = sum(1 for a in ctrl2 if a in starts)
print(f"  random-instr-boundary addrs that are in starts: {c1}/87 (expect 87)")
print(f"  random-arbitrary-offset addrs that are in starts: {c2}/87  (~base rate of being a boundary)")

print()
print("=== .text addresses among the 87: mod 16 alignment distribution ===")
print("  ", Counter(a & 0xF for a in text))

print()
print("=== how many .text bytes-windows contain the COL pointer pattern? ===")
# count 4-byte-aligned dwords in .text that equal the 8 distinct COL addresses
cols = sorted({u32(a - 4) for a in text})
print("  distinct COLs behind the 87:", len(cols), [f"0x{c:08X}" for c in cols])
for c in cols:
    hits = 0
    offs = []
    o = 0
    b = c.to_bytes(4, "little")
    while True:
        o = code.find(b, o)
        if o < 0:
            break
        if o % 4 == 0:
            hits += 1
            offs.append(t.va + o)
        o += 1
    print(f"  COL 0x{c:08X}: {hits} aligned occurrences in .text; first {[f'0x{x:08X}' for x in offs[:6]]}")
