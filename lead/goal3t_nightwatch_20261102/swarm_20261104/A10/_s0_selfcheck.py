# -*- coding: utf-8 -*-
# A10 现场自证：覆盖率 + 回边复钉 + 全函数窗口落盘
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
cov = eng.coverage
print("coverage = %.2f%% / %d insns / %d resync" % (cov[0], cov[1], cov[2]))

LO, HI = 0x55D360, 0x55DEE0
bes = eng.loop_backedges(LO, HI)
print("backedges in [0x55D360,0x55DEE0):")
for va, t, mn in bes:
    print("  0x%06X -> 0x%06X  %s" % (va, t, mn))

rets, succ = eng.func_rets(LO, HI)
print("rets:", ["0x%06X" % i.address for i in rets])

# 全函数窗口落盘
out = open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/A10/_mlf_full.txt", "w", encoding="utf-8")
seq = [i for i in eng.stream if LO <= i.address < HI]
out.write("# MainLogicFrame 0x55D360..0x55DEE0  insns=%d\n" % len(seq))
for i in seq:
    out.write("0x%06X  %-22s %s %s\n" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
out.close()
print("dumped _mlf_full.txt insns=%d" % len(seq))
