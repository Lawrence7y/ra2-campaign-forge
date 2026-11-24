# -*- coding: utf-8 -*-
# P02 probe1: 场景自证 + MainLogicFrame 头部逐字节 + 回边
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("== scene ==")
print("sha256:", eng.sha)
print("coverage:", eng.coverage)

print("\n== MainLogicFrame prologue 0x55D360..0x55D3D0 ==")
for a, b, m, o in eng.disasm(0x55D360, 0x70):
    print("%08X  %-22s %s %s" % (a, b, m, o))

print("\n== raw bytes 0x55D377-0x55D390 ==")
print(eng.rd(0x55D377, 0x19).hex())

print("\n== loop backedges in MainLogicFrame ==")
for be in eng.loop_backedges(0x55D360, 0x55DEE0):
    print("backedge: %08X -> %08X  %s" % be)

print("\n== IAT sanity ==")
for slot in (0x7E11F0, 0x7E1530):
    print("%08X -> %s" % (slot, eng.resolve_iat(slot)))
