# -*- coding: utf-8 -*-
"""导出 BuildingClass / BuildingTypeClass 各子表内存布局与槽内容，判定什么是主虚表。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

def dump_region(va, n, label):
    print("== %s  [%08X, +%d)" % (label, va, n))
    for i in range(0, n, 4):
        v = C.u32(va + i)
        t = ""
        if v and C.in_text(v):
            ai = C.atlas_covering(v)
            t = "  <text fn %s>" % (ai[1] if ai else "?")
        print("   %08X: %08X%s" % (va + i, v, t))

print("COL 007FC2B0 (tn/small):")
for i in range(4):
    print("   %08X: %08X" % (0x7FC2B0 + i*4, C.u32(0x7FC2B0 + i*4)))
print("COL 007FC360 (main):  raw")
for i in range(8):
    print("   %08X: %08X" % (0x7FC360 + i*4, C.u32(0x7FC360 + i*4)))

dump_region(0x7E3E80, 0x50, "BuildingClass vt area before main")
dump_region(0x7E3EBC, 0x60, "main vtable 007E3EBC")

print("\n--- BuildingTypeClass ---")
for i in range(8):
    print("   %08X: %08X" % (0x7FC570 + i*4, C.u32(0x7FC570 + i*4)))
