#!/usr/bin/env python3
"""Dump full disassembly for the 7 entries using atlas size as window (column 2).
Independent verification: linear disasm of exactly `size` bytes must end at/with a ret
(allow trailing int3/nop padding). This is a bounded linear channel; the direct-call
site scan (scan_sites.py) is a whole-.text channel independent of atlas entry+size."""
import json, os
from common import disasm_n, insn_str

ENTRIES = [0x0065CAC0, 0x004324B0, 0x00552490, 0x006C9890,
           0x00631CC0, 0x0065D150, 0x00431E80]
SIZE = {0x0065CAC0:111, 0x004324B0:234, 0x00552490:346, 0x006C9890:67,
        0x00631CC0:75, 0x0065D150:56, 0x00431E80:131}

lines = []
out = {}
for va in ENTRIES:
    sz = SIZE[va]
    insns = disasm_n(va, sz + 16)
    # linear: keep insns whose start < va+sz
    body = [i for i in insns if i.address < va + sz]
    last = body[-1] if body else None
    lines.append(f"\n===== {va:08X} atlas_size={sz} last_insn={insn_str(last) if last else 'NA'} =====")
    for i in insns:
        tag = 'BODY' if i.address < va+sz else 'AFTER'
        lines.append(f"[{tag}] {insn_str(i)}")
    out[f"{va:08X}"] = {'size': sz, 'last': insn_str(last) if last else None}

base = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C4"
with open(base + r"\EVIDENCE\dis_full.txt", 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))
with open(base + r"\EVIDENCE\dis_extent.json", 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2)
print("wrote dis_full.txt lines:", len(lines))
for k,v in out.items(): print(k, v['size'], v['last'])
