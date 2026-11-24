# -*- coding: utf-8 -*-
# P01: 现场自证 + CurrentFrame 基线复核（只读 gamemd.exe）
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine, G_FRAME

eng = Engine()
print("sha256 =", eng.sha[:16], "... (期望 73201cc021497c95)")
print(".text  = [%#x, %#x)  size=%#x" % (eng.TLO, eng.THI, eng.TSZ))
cov = eng.coverage
print("coverage = %.2f%% / %d insns / resync=%d" % (cov[0], cov[1], cov[2]))

hits = eng.disp_hits(G_FRAME)
ws = [h for h in hits if h[1] == "W"]
rs = [h for h in hits if h[1] == "R"]
print("G_FRAME %#x: total=%d  W=%d  R=%d" % (G_FRAME, len(hits), len(ws), len(rs)))
print("--- 10 写点 ---")
for va, acc, mn, ops in ws:
    print("%#08x  %s  %s %s" % (va, acc, mn, ops))
print("--- 写点字节 ---")
for va, acc, mn, ops in ws:
    b = eng.rd(va, 10)
    print("%#08x  %s" % (va, b.hex()))
# 0x55DE73/7E/81 三连锚
for a in (0x55DE73, 0x55DE7E, 0x55DE81):
    print("anchor %#x: %s" % (a, eng.rd(a, 8).hex()))
