# -*- coding: utf-8 -*-
"""领队独立核验 W3 两条最反直觉的断言：
  (a) SelectAutoTarget 0x6FB010 实为 UpdateReload（弹药装填），Ammo==-1 时早退；
  (b) DrawIfVisible 0x5F4B10 裁剪失败时直接 ret，跳过整个 Draw。

只读 gamemd.exe，零真机。
"""
import sys

sys.path.insert(0, r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104')
from ra2tool import Engine

e = Engine()
print("coverage", e.coverage)

print("\n=== A. 0x6FB010 (claimed SelectAutoTarget = UpdateReload) ===")
for a, b, m, o in e.disasm(0x6FB010, 0x80):
    print("%08X %-18s %s %s" % (a, b, m, o))

print("\n=== B. 0x5F4B10 DrawIfVisible head..exit ===")
for a, b, m, o in e.disasm(0x5F4B10, 0x80):
    print("%08X %-18s %s %s" % (a, b, m, o))
