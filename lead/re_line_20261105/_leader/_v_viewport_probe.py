# -*- coding: utf-8 -*-
"""D-17 静态补证：核实 0x887308 指向的 DSurface 对象 +0x1C 是否可能是视口尺寸/坐标。

只读 gamemd.exe。零真机、零采样代码。
"""
import sys

sys.path.insert(0, r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104')
from ra2tool import Engine

e = Engine()
print("coverage", e.coverage)

print("\n=== A. 0x432A35 附近（读 [0x887308] 后 +0x1C）===")
for a, b, m, o in e.disasm(0x432A20, 0x40):
    print("%08X %-18s %s %s" % (a, b, m, o))

print("\n=== B. 0x4328DE 附近（读 [0x88730C] 当 this）===")
for a, b, m, o in e.disasm(0x4328D0, 0x30):
    print("%08X %-18s %s %s" % (a, b, m, o))

print("\n=== C. 谁写 DSurface 对象 +0x1C（间接，无法直接查；先看 0x432A35 所在函数头部）===")
for a, b, m, o in e.disasm(0x4329F0, 0x40):
    print("%08X %-18s %s %s" % (a, b, m, o))
