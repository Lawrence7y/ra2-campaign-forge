# -*- coding: utf-8 -*-
# A06 probe1: 现场自证 + 0x55E160 LogicUpdate 整函数窗口 + 关键全局引用普查
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

eng = Engine()
cov = eng.coverage
print("coverage = %.2f%% / %d insns / resync %d" % cov)
print("sha256 =", eng.sha[:16], "...", eng.sha[-16:])

LU = 0x55E160
print("\n===== disasm 0x55E160 .. +0x900 =====")
for va, hx, mn, ops in eng.disasm(LU, 0x900):
    print("%08X  %-22s %s %s" % (va, hx, mn, ops))

print("\n===== key globals: disp_hits across whole .text =====")
for name, va in [("[0x887328] TICKLAST", 0x00887328),
                 ("[0x887330] TICKTGT", 0x00887330),
                 ("[0xA8EDA0]", 0x00A8EDA0),
                 ("[0xA8ED80] FOCUS", 0x00A8ED80),
                 ("[0xA8B558] GAMESPEED", 0x00A8B558)]:
    hits = eng.disp_hits(va)
    print("\n%s : %d hits" % (name, len(hits)))
    for h in hits:
        print("   %08X %s %s %s" % h)

print("\n===== all call sites targeting 0x55E160 (whole .text) =====")
n = 0
for ins in eng.stream:
    if ins.mnemonic in ("call",) :
        try:
            t = ins.operands[0]
            if t.type == 2 and t.imm == LU:
                print("   %08X  call 0x55E160" % ins.address)
                n += 1
        except Exception:
            pass
print("total call sites:", n)
