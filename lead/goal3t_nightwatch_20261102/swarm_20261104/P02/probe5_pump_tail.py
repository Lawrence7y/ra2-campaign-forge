# -*- coding: utf-8 -*-
# P02 probe5: 泵包装 0x53E770 尾段（返回语义）+ 补 IAT + LogicUpdate/MLF体 的旗标读点上下文
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()

print("== wrapper 0x53E770 tail 0x53E8CA..0x53EC60 ==")
for a, b, m, o in eng.disasm(0x53E8CA, 0x396):
    print("%08X  %-18s %s %s" % (a, b, m, o))

print("\n== IAT 补解 ==")
for slot in (0x7E11E8, 0x7E11EC, 0x7E13C0, 0x7E1244, 0x7E1484, 0x7E14D4, 0x7E14D8, 0x7E11D4, 0x7E11D8):
    print("  %08X -> %s" % (slot, eng.resolve_iat(slot)))

def dump(title, va, n):
    print("\n== %s ==" % title)
    for a, b, m, o in eng.disasm(va, n):
        print("%08X  %-18s %s %s" % (a, b, m, o))

dump("LogicUpdate 旗标读点 0x55E204 上下文", 0x55E1E8, 0x40)
dump("MLF 体旗标读点 0x55D88E 上下文", 0x55D870, 0x40)
