# -*- coding: utf-8 -*-
"""V-P03 探针 8（最终）：10 宿主写点前 [g] 读点审计 + [0xABCD58] 写者 + MLF 头 INGAME 早退"""
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
P = print
S = eng.stream
P("[coverage] %.2f%% / %d / %d" % eng.coverage)

hits = eng.disp_hits(0xA8ED84)
HOSTS = [
    ("W1", 0x52DA08, 0x52D9A0, 0x52F3F0), ("W2", 0x55DE81, 0x55D360, 0x55DEE0),
    ("W3", 0x5B7329, 0x5B7090, 0x5B7360), ("W4", 0x5BB20C, 0x5BAC60, 0x5BB290),
    ("W5", 0x5E550F, 0x5E3D10, 0x5E5F10), ("W6", 0x5E747C, 0x5E7460, 0x5E74E0),
    ("W7", 0x68466B, 0x684620, 0x684C30), ("W8", 0x686765, 0x686730, 0x686890),
    ("W9", 0x795234, 0x794BA0, 0x795650), ("W10", 0x79758C, 0x7970D0, 0x7975AC),
]
P("===== 宿主内 [0xA8ED84] 读点审计（报告称：除 MLF 外 9 宿主写点前 0 读） =====")
for tag, wva, lo, hi in HOSTS:
    rs = [(hex(a), m) for a, d, m, _ in hits if lo <= a < hi and d == "R"]
    P("[%s] host=[0x%x,0x%x) reads=%d %s" % (tag, lo, hi, len(rs), rs))

P("")
P("===== [0xABCD58] 写者清单 =====")
for a, d, m, o in eng.disp_hits(0xABCD58):
    if d == "W":
        P("   W 0x%08x %s %s  (in 0x55CFD0 func? %s)" % (a, m, o, 0x55CFD0 <= a < 0x55D360))

P("")
P("===== MLF 头 INGAME 早退 0x55D360..0x55D380 =====")
for a, b, m, o in eng.disasm(0x55D360, 0x24):
    P("    0x%08x  %-18s %s %s" % (a, b, m, o))
P("DONE8")
