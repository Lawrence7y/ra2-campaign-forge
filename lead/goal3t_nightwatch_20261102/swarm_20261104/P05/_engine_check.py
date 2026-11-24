# -*- coding: utf-8 -*-
"""P05 后台引擎复核：MainLogicFrame 冻结出口字节级验证（只读，零真机）。
基线（任务给定，已定谳）：MainLogicFrame 0x55D360，3 ret（0x55D877/0x55DEC7/0x55DEDB），
其中 0x55D877 与 0x55DEDB 不经 inc 即可达；唯一定常 inc 0x55DE7E + 写回 0x55DE81。
本脚本只做复证，不重推边界（边界引自基线，hi=0x55DF00 仅作扫描窗）。
"""
import sys, bisect

sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("coverage:", eng.coverage)
by = eng.by()
addrs = sorted(by)


def ctx(va, before=5, after=3):
    i = bisect.bisect_left(addrs, va)
    lo, hi = max(0, i - before), min(len(addrs), i + after + 1)
    for a in addrs[lo:hi]:
        ins = by[a]
        mark = "  <<<" if a == va else ""
        print(f"{a:08X}  {ins.bytes.hex():<22} {ins.mnemonic} {ins.op_str}{mark}")


print("== inc 站点 0x55DE7E 邻域 ==")
ctx(0x55DE7E, 3, 5)
for va in (0x55D877, 0x55DEC7, 0x55DEDB):
    print(f"== ret {va:06X} 邻域 ==")
    ctx(va, 5, 1)

rets, _succ = eng.func_rets(0x55D360, 0x55DF00)
print("func_rets(0x55D360,0x55DF00) =", [hex(i.address) for i in rets])

# cut 块 = inc(0x55DE7E) 起、写回指令（0x55DE81 起）止；cut_hi 取块末字节（含），
# 使块后正常 fall-through 不被误剪。
ins7e = by.get(0x55DE7E)
ins81 = by.get(0x55DE81)
if ins7e is None or ins81 is None:
    print("!! 0x55DE7E/0x55DE81 不是流内指令起点，cut 块需人工核定")
    cut_lo, cut_hi = 0x55DE7E, 0x55DE85
else:
    cut_lo = 0x55DE7E
    cut_hi = 0x55DE81 + ins81.size - 1
    print(f"inc insn: {ins7e.bytes.hex} {ins7e.mnemonic} {ins7e.op_str}")
    print(f"写回 insn: {ins81.bytes.hex} {ins81.mnemonic} {ins81.op_str}")
print("cut block = [%s, %s]" % (hex(cut_lo), hex(cut_hi)))
r = eng.reach_without(0x55D360, 0x55DF00, cut_lo, cut_hi)
for va in (0x55D877, 0x55DEC7, 0x55DEDB):
    print(f"{va:06X} reachable_without_inc_block = {va in r}")
print("reach set size:", len(r), "(下近似：间接跳转未跟踪)")
