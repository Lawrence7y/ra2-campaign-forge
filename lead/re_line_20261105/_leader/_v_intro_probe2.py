# -*- coding: utf-8 -*-
"""领队裁决 Q1 vs Q3 冲突（精简版）：只做反汇编，不做全镜像普查。"""
import sys

sys.path.insert(0, r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104')
from ra2tool import Engine

e = Engine()

print("=== 0x5BF260 ===")
for a, b, m, o in e.disasm(0x5BF260, 0x50):
    print("%08X %-18s %s %s" % (a, b, m, o))
    if m.startswith("ret"):
        break

print("\n=== 0x5BF2B0 ===")
n = 0
for a, b, m, o in e.disasm(0x5BF2B0, 0x120):
    print("%08X %-18s %s %s" % (a, b, m, o))
    n += 1
    if m.startswith("ret") and n > 4:
        break

print("\n=== 0x5BED40 (head) ===")
for a, b, m, o in e.disasm(0x5BED40, 0x60):
    print("%08X %-18s %s %s" % (a, b, m, o))
