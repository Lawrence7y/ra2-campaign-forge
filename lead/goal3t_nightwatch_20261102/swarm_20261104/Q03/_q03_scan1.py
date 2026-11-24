# -*- coding: utf-8 -*-
"""Q03 综合扫描：IID、IStream 来源、上层调用链。一次性跑完避免重复全镜像遍历。"""
import sys, struct
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
out = []

def p(s=""):
    print(s)
    out.append(s)

# 1) IID @ 0x81FC50
b = eng.rd(0x81FC50, 16)
d1, d2, d3 = struct.unpack_from("<IHH", b, 0)
p(f"[IID @ 0x81FC50] {d1:08X}-{d2:04X}-{d3:04X}-{b[8:10].hex().upper()}-{b[10:16].hex().upper()}")
p(f"  raw: {b.hex()}")

# 2) 全镜像直接调用 xref（一次遍历，多目标）
TARGETS = {0x67CEF0: "SAVE-upper 0x67CEF0", 0x67E440: "LOAD-upper 0x67E440",
           0x67D300: "SAVE-driver", 0x67E730: "LOAD-driver",
           0x67F7E0: "SAVE-host", 0x67F9C0: "LOAD-host",
           0x6CF240: "post-load-cb 0x6CF240"}
xr = {t: [] for t in TARGETS}
heads = set()
for ins in eng.stream:
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == 2:
        t = ins.operands[0].imm
        heads.add(t)
        if t in xr:
            xr[t].append(ins.address)
for t, tag in TARGETS.items():
    p(f"=== direct callers of {tag} ===")
    for a in xr[t]:
        p(f"  0x{a:08X}")
    if not xr[t]:
        p("  (none)")

# 3) 上层函数头 prologue
for h, tag in ((0x67CEF0, "SAVE-upper"), (0x67E440, "LOAD-upper")):
    p(f"=== prologue {tag} 0x{h:X} ===")
    for va, bh, mn, ops in eng.disasm(h, 0xA0):
        p(f"{va:08X}  {bh:<18} {mn} {ops}")
    p()

with open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/Q03/_q03_scan1_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("DONE")
