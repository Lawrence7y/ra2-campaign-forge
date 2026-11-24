# -*- coding: utf-8 -*-
"""A01 probe 3: ScenarioClass(0x6832C0 ctor, size 0x3740) 的 +0x620/+0x628/+0x62C/+0x630 簇。
逐个 0x62C 写点解宿主函数 + this 来源。只读 gamemd.exe。"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("== coverage ==")
print("coverage: %.2f%%  insns=%d  resync=%d" % eng.coverage)

def show(lo, hi, mark=()):
    print("\n--- 0x%08X .. 0x%08X ---" % (lo, hi))
    for a, b, m, o in eng.disasm(lo, hi - lo):
        t = " <<<" if a in mark else ""
        print("0x%08X  %-22s %-8s %s%s" % (a, b, m, o, t))

# 1) 0x684180 (called by MLF at 0x55D81C right after clearing +0x630)
show(0x684120, 0x684200, {0x684174, 0x684180, 0x684186, 0x684195, 0x6841A0})

# 2) 0x6840A1 / 0x6840AF / 0x6840BC : the +0x630 setter cluster
show(0x684050, 0x684120, {0x6840A1, 0x6840AF, 0x6840BC})

# 3) 0x6836D2 : clears +0x62C and +0x630
show(0x683680, 0x683710, {0x6836D2, 0x6836D8})

# 4) ScenarioClass ctor 0x6832C0 : does it init +0x62C/+0x630?
show(0x6832C0, 0x6833C0)

# 5) callers of 0x684180 / 0x6836D2-area functions
print("\n== callers of 0x684180 ==")
for ins in eng.stream:
    if ins.mnemonic == "call" and ins.op_str == "0x684180":
        print("0x%08X  call 0x684180" % ins.address)
print("\n== callers of 0x6836C0? probe: scan for call targets in 0x6836xx ==")
for ins in eng.stream:
    if ins.mnemonic == "call" and ins.op_str.startswith("0x6836") :
        print("0x%08X  call %s" % (ins.address, ins.op_str))
