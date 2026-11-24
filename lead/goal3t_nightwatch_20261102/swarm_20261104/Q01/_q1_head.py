# -*- coding: utf-8 -*-
"""Q01 步1：coverage 自证 + 已知锚点字节 A1..A6 复核（全部亲跑）。"""
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("image sha256 =", eng.sha)
print("IB =", hex(eng.IB), " .text = [%08X, %08X) size=%d" % (eng.TLO, eng.THI, eng.TSZ))
cov = eng.coverage
print("coverage  %.6f%% / %d insns / %d resync" % cov)
assert abs(cov[0] - 99.998376) < 0.001, "coverage mismatch: %r" % (cov,)
assert cov[1] == 1394120, cov[1]
assert cov[2] == 66, cov[2]
print("coverage self-test PASS")

def show(va, n, tag):
    print("\n--- %s (0x%08X, %dB) ---" % (tag, va, n))
    for a, b, m, o in eng.disasm(va, n):
        print("  %08X  %-22s %s %s" % (a, b, m, o))

# A1: 0x55CFD0 头
show(0x55CFD0, 32, "0x55CFD0 头")

# A2..A5: 四个清零块
for tag, va in [("0x55D123", 0x55D123), ("0x55D1B1", 0x55D1B1),
                ("0x55D219", 0x55D219), ("0x55D25C", 0x55D25C)]:
    show(va, 28, tag)
