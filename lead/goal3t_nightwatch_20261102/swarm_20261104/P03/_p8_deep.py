# -*- coding: utf-8 -*-
# P08: W2 深挖（守卫/出口/另一读点去向） + W4 ebp 追源 + 0x5E7460 真尾 + 基线 reach_without
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine, G_FRAME

eng = Engine()
by = eng.by()

def dump(lo, hi, tag=""):
    print("  [%s %#x..%#x)" % (tag, lo, hi))
    for a in sorted(k for k in by if lo <= k < hi):
        ins = by[a]
        print("  %#08x  %-22s %s %s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print("== A. MLF 尾部 0x55DEC0..0x55DEE0（两个 ret 的角色） ==")
dump(0x55DEC0, 0x55DEE0)

print("\n== B. reach_without 复核（绕开 [0x55DE73,0x55DE84] inc 块仍可达的 ret） ==")
seen = eng.reach_without(0x55D360, 0x55DEE0, 0x55DE73, 0x55DE84)
rets = sorted(k for k in seen if by[k].mnemonic.startswith("ret"))
print("  绕开 inc 块可达的 ret: %s" % ["%#x" % r for r in rets])

print("\n== C. MLF 另外两处读点去向（非 RMW 验证） ==")
dump(0x55D3BB, 0x55D3E0, "读@0x55D3BB")
dump(0x55D8C9, 0x55D8F0, "读@0x55D8C9")

print("\n== D. W4 宿主 [0x5BAC60,0x5BB20C) 内全部 ebp 相关指令 ==")
for a in sorted(k for k in by if 0x5BAC60 <= k < 0x5BB20C):
    ins = by[a]
    if "ebp" in ins.op_str or ins.mnemonic in ("push", "pop"):
        print("  %#08x  %-22s %s %s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print("\n== E. W4 函数头 0x5BAC60..0x5BAD20 ==")
dump(0x5BAC60, 0x5BAD20, "W4 head")

print("\n== F. 0x5E7460 真尾扫描：向后找首个 ret / jmp ==")
seq = sorted(k for k in by if 0x5E7460 <= k < 0x5E8000)
tail = None
for a in seq:
    ins = by[a]
    if ins.mnemonic.startswith("ret"):
        tail = a
        break
print("  首个 ret: %#x" % tail if tail else "  0x8000 前无 ret")
dump(0x5E74E0, 0x5E7560, "0x5E74E0 后续")
