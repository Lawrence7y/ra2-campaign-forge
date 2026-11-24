#!/usr/bin/env python3
"""Generate all remaining byte-level evidence files for S18-K2."""
import sys, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-K2\work")
import peutil as p

EV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-K2\EVIDENCE"

def dump_to(fn, va, count, maxbytes):
    lines = []
    for ins in p.disasm(va, count, maxbytes):
        lines.append(p.fmt(ins))
    with open(os.path.join(EV, fn), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(fn, len(lines), "insns")

dump_to("fillevent_place.txt", 0x4C6AE0, 42, 0xD0)
dump_to("fillevent_sellcell.txt", 0x4C6650, 34, 0xA0)
dump_to("fillevent_animation.txt", 0x4C6800, 40, 0xC0)
dump_to("dispatch_entry.txt", 0x4C6CB0, 30, 0xC0)
dump_to("crc_init.txt", 0x64DAB0, 22, 0x60)
