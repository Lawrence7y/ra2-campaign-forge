# -*- coding: utf-8 -*-
# P12: 帧循环细节 / 0x55CFD0 四变体 / 0x4790E0 / MLF edi / 立即数隐写检查
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine, G_FRAME

eng = Engine()
by = eng.by()
stream = eng.stream

def dump(lo, hi, tag=""):
    print("  [%s %#x..%#x)" % (tag, lo, hi))
    for a in sorted(k for k in by if lo <= k < hi):
        ins = by[a]
        print("  %#08x  %-22s %s %s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print("== A. dispatcher 帧循环 [0x48CE60, 0x48CF00) ==")
dump(0x48CE60, 0x48CF00, "loop")

print("\n== B. 0x55CFD0 的四个旗标写块及条件 ==")
dump(0x55CFD0, 0x55D000, "head")
dump(0x55D100, 0x55D2A0, "variants")

print("\n== C. 0x4790E0 头 ==")
dump(0x4790E0, 0x479120, "4790e0")

print("\n== D. MLF edi 追源 [0x55DBF0,0x55DC60) ==")
dump(0x55DBF0, 0x55DC60, "edi-src")

print("\n== E. 立即数隐写检查：0xA8ED84 作为 imm / lea 目标 ==")
n_imm = 0
for ins in stream:
    try:
        ops = ins.operands
    except Exception:
        continue
    for op in ops:
        if op.type == 2 and op.imm == G_FRAME:
            print("  IMM 命中: %#08x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
            n_imm += 1
print("  imm 命中数 = %d" % n_imm)
# 原始字节计数 vs disp_hits 计数
tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
pat = bytes([0x84, 0xED, 0xA8, 0x00])
cnt, pos = 0, 0
while True:
    j = tb.find(pat, pos)
    if j < 0: break
    cnt += 1
    pos = j + 1
print("  .text 中字节序列 84 ed a8 00 出现 %d 次（disp_hits=1007）" % cnt)

print("\n== F. 0x6BB9A0 对 0x48CCC0 的两处调用上下文 ==")
dump(0x6BE020, 0x6BE080, "gamemain")
