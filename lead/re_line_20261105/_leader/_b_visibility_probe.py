# -*- coding: utf-8 -*-
"""D-20 步骤 B：从 DrawIfVisible 0x5F4B10 追踪可视性判定与「可见单位数」的可能载体。

目标：区分三种结果
  (i)  存在「现成计数」VA（可直接读）
  (ii) 需要遍历推导（没有单一计数，但有可遍历的容器）
  (iii) 未定位

只读 gamemd.exe。零真机、零采样实现。
"""
import sys

sys.path.insert(0, r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104')
from ra2tool import Engine

e = Engine()
print("coverage", e.coverage)
print("SHA 73201cc0... assumed by Engine")

print("\n=== 1. DrawIfVisible 0x5F4B10 完整函数（到 ret 0xC 为止）===")
n = 0
for a, b, m, o in e.disasm(0x5F4B10, 0x120):
    print("%08X %-20s %s %s" % (a, b, m, o))
    n += 1
    if m.startswith("ret") and n > 10:
        break

print("\n=== 2. TacticalClass::IsVisible 0x6D2140 头部（视口判定）===")
for a, b, m, o in e.disasm(0x6D2140, 0x80):
    print("%08X %-20s %s %s" % (a, b, m, o))

print("\n=== 3. 对象主渲染簇 0x6D8DB0 头部（遍历 5 层，逐单位调 DrawIfVisible）===")
for a, b, m, o in e.disasm(0x6D8DB0, 0xA0):
    print("%08X %-20s %s %s" % (a, b, m, o))
