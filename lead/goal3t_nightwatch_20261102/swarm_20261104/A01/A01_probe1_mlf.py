# -*- coding: utf-8 -*-
"""A01 probe 1: MainLogicFrame 0x55D360 全函数反汇编 + 出口/守卫链。
只读 gamemd.exe。"""
import sys, io
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("== coverage ==")
print("coverage: %.2f%%  insns=%d  resync=%d" % eng.coverage)

print("\n== raw bytes 0x55D360..0x55DEE0 ==")
ins = eng.disasm(0x55D360, 0x55DEE0 - 0x55D360)
for a, b, m, o in ins:
    print("0x%08X  %-24s %-8s %s" % (a, b, m, o))

print("\n== func_rets ==")
rets, succ = eng.func_rets(0x55D360, 0x55DEE0)
for r in rets:
    print("ret @ 0x%08X  %s %s" % (r.address, r.mnemonic, r.op_str))

print("\n== reach without inc block [0x55DE73,0x55DE84) ==")
seen = eng.reach_without(0x55D360, 0x55DEE0, 0x55DE73, 0x55DE84)
by = eng.by()
bad = [a for a in sorted(seen) if by.get(a) and by[a].mnemonic.startswith("ret")]
print("rets reachable w/o inc:", ["0x%08X" % a for a in bad])

print("\n== loop backedges in MLF ==")
for a, t, mn in eng.loop_backedges(0x55D360, 0x55DEE0):
    print("0x%08X -> 0x%08X  %s" % (a, t, mn))
