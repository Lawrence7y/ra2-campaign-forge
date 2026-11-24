# -*- coding: utf-8 -*-
"""领队独立核验 W3 的 C1 关键断言：
  (a) 0x4CBBA0 (CallFindPath) 是否丢弃 0x7D0、改传 -1；
  (b) 0x429A90 (SearchCore) 是否把 <0 的预算重写为 0xFFF7 (65527)。

只读 gamemd.exe，零真机。
"""
import sys

sys.path.insert(0, r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104')
from ra2tool import Engine

e = Engine()

print("=== A. 0x4D3E37.. call 0x4CBBA0 (caller pushes 0x7D0) ===")
for a, b, m, o in e.disasm(0x4D3E37, 0x18):
    print("%08X %-18s %s %s" % (a, b, m, o))

print("\n=== B. 0x4CBBA0..0x4CBC3B (CallFindPath body) ===")
for a, b, m, o in e.disasm(0x4CBBA0, 0xA0):
    print("%08X %-18s %s %s" % (a, b, m, o))
    if m.startswith("ret"):
        break

print("\n=== C. 0x429D51..0x429D65 (SearchCore budget rewrite) ===")
for a, b, m, o in e.disasm(0x429D51, 0x18):
    print("%08X %-18s %s %s" % (a, b, m, o))

print("\n=== D. raw bytes check ===")
print("0x429D59..0x429D60 =", e.rd(0x429D59, 10).hex())
print("0x4CBC1B..0x4CBC22 =", e.rd(0x4CBC1B, 10).hex())
