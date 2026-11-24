# -*- coding: utf-8 -*-
"""领队独立核验 D-19 的反证据：0x42CC80 是否真的在同步重试路径再次推进代际戳。只读。"""
import sys

sys.path.insert(0, r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104')
from ra2tool import Engine

e = Engine()
print("coverage", e.coverage)

print("\n=== 0x42CC70..0x42CCA5 ===")
for a, b, m, o in e.disasm(0x42CC70, 0x38):
    print("%08X %-18s %s %s" % (a, b, m, o))

print("\n=== raw bytes 0x42CC80 / 0x42CC9B ===")
print("0x42CC80:", e.rd(0x42CC80, 5).hex())
print("0x42CC9B:", e.rd(0x42CC9B, 6).hex())
