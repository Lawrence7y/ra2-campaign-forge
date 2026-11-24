# -*- coding: utf-8 -*-
"""A01 probe 2: [0xA8B230] 写点全解 + 字段 0x62C / 0x630 / 0x620 / 0x628 家族。
只读 gamemd.exe。"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("== coverage ==")
print("coverage: %.2f%%  insns=%d  resync=%d" % eng.coverage)

def dump_name(tag, hits):
    print("\n===== %s : %d hits =====" % (tag, len(hits)))
    for va, rw, mn, ops in hits:
        print("0x%08X %s  %-8s %s" % (va, rw, mn, ops))

def ctx(va, before=0x60, after=0x50):
    lo, hi = va - before, va + after
    print("\n--- ctx around 0x%08X ---" % va)
    for a, b, m, o in eng.disasm(lo, hi - lo):
        mark = " <<<" if a == va else ""
        print("0x%08X  %-22s %-8s %s%s" % (a, b, m, o, mark))

dump_name("[0xA8B230] ScenarioClass::Instance", eng.disp_hits(0x00A8B230))
for va, rw, mn, ops in eng.disp_hits(0x00A8B230):
    if rw == "W":
        ctx(va, 0x70, 0x40)

for fld in (0x620, 0x624, 0x628, 0x62C, 0x630, 0x634):
    dump_name("field +0x%X (any base)" % fld, eng.disp_hits_field(fld))
