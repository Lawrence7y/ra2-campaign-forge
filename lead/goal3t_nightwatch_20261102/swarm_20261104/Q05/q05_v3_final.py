# -*- coding: utf-8 -*-
"""Q05 v3：收尾验证（死 test 原始字节 / GameMainLoop prologue / inc helper 头 /
timeEnd 配对 / LogicUpdate 单机等待环与执行块延续 / 0x55CFD0 快速旁路）。"""
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("coverage: %.6f%% / %d insns / %d resync" % eng.coverage)
by = eng.by()
stream = eng.stream

def disby(lo, hi, tag):
    print("-- %s [0x%X,0x%X) --" % (tag, lo, hi))
    a = lo
    while a < hi:
        i = by.get(a)
        if i is None:
            a += 1
            continue
        print("  0x%08X: %-22s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
        a += i.size

print("\n== T1 dead-test raw bytes ==")
print("  0x55CFD0:", eng.rd(0x55CFD0, 16).hex(" "))
print("  0x55D059:", eng.rd(0x55D059, 10).hex(" "))

print("\n== T2 GameMainLoop prologue [0x52D9A0,0x52DA10) ==")
disby(0x52D9A0, 0x52DA0E, "gml_head")

print("\n== T3 inc-helper head zone [0x684110,0x684155) ==")
disby(0x684110, 0x684156, "inc_helper_head")
calls = {}
for ins in stream:
    if ins.mnemonic not in ("call", "jmp"):
        continue
    if not ins.operands or ins.operands[0].type != 2:
        continue
    calls.setdefault(ins.operands[0].imm, []).append(ins.address)
for t in sorted(set(k for k in calls if 0x684000 <= k < 0x684200)):
    print("  calltarget 0x%08X n=%d sites=%s" % (t, len(calls[t]), [hex(a) for a in calls[t]][:8]))

print("\n== T4 timeBegin/timeEnd 全镜像配对 ==")
for t, nm in [(0x5D5870, "begin"), (0x5D5880, "end")]:
    print("  %s: %s" % (nm, [hex(a) for a in sorted(calls.get(t, []))]))

print("\n== T5 LogicUpdate 单机 idle 环 [0x55E2C0,0x55E33B) ==")
disby(0x55E2C0, 0x55E33B, "lu_idle")

print("\n== T6 LogicUpdate 执行块延续 [0x55E3DE,0x55E4C0) ==")
disby(0x55E3DE, 0x55E4C0, "lu_exec2")

print("\n== T7 0x55CFD0 快速旁路落点 [0x55D330,0x55D365) ==")
disby(0x55D330, 0x55D365, "cfd0_fastpath")
