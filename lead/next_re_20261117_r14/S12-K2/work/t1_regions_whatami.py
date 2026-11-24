"""T1/T2: aligned region dumps for 0x43F180 (two can-place sites + failure
branches), wrappers 0x5683C0/0x5687F0, and WhatAmI vtable-slot-11 constants.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from re_helper import Bin, disasm_range, fmt_insn, load_atlas, EVID

b = Bin()
L = []

def dump(a, n, title):
    L.append("="*88); L.append(title); L.append("="*88)
    for ins in disasm_range(b, a, a+n, skipdata=True):
        L.append(fmt_insn(ins))

# aligned whole 0x43F180 split into chunks to avoid any truncation issues
rows,_ = load_atlas()
f = next(r for r in rows if r["_va"]==0x43F180)
L.append("0x43F180 full disasm, size=%d, in %d chunks" % (f["_size"], (f["_size"]+399)//400))
for off in range(0, f["_size"], 400):
    dump(0x43F180+off, min(400, f["_size"]-off), "0x43F180 +%04X" % off)

dump(0x5683C0, 1068, "T2 wrapper 0x5683C0 (attach, atlas size 1068)")
dump(0x5687F0, 945,  "T2 wrapper 0x5687F0 (detach, atlas size 945)")

# WhatAmI map: read vtable slot 11 (offset 0x2C) for known class vtables.
# BuildingClass vt = 0x7E3EBC per R14_COMMON. Also scan ALL vftables in .rdata:
# for each 4B-aligned addr whose slot11 points to a tiny 'mov eax,imm; ret' fn.
L.append("="*88); L.append("WhatAmI (vtable slot 11 @ +0x2C) constant map via tiny-fn pattern"); L.append("="*88)
m = b.sec(".rdata")
rdata = b.pe.__data__[m["raw"]:m["raw"]+m["rawsize"]]
base = m["va"]
seen = {}
for i in range(0, len(rdata)-4, 4):
    vt = base + i
    slot = int.from_bytes(rdata[i+0x2C:i+0x30], "little") if i+0x30 <= len(rdata) else 0
    if not (0x400000 <= slot < 0x900000): continue
    try:
        code = b.read(slot, 8)
    except Exception:
        continue
    # B8 imm32 C3  (mov eax,imm; ret) within first 8 bytes
    if code[0]==0xB8 and code[5]==0xC3:
        imm = int.from_bytes(code[1:5],"little")
        seen.setdefault((slot,imm), []).append(vt)
for (slot,imm),vts in sorted(seen.items(), key=lambda kv:(kv[0][1],kv[0][0])):
    L.append("WhatAmI=%-5d(0x%-3X) slotfn=%08X  nvtable=%d  sample_vt=%08X" %
             (imm, imm, slot, len(vts), vts[0]))

out = os.path.join(EVID,"t1_43F180_and_wrappers_and_whatami.txt")
with open(out,"w",encoding="utf-8") as fp: fp.write("\n".join(L)+"\n")
print("wrote",out,"lines",len(L))
print("distinct WhatAmI constants:", sorted(set(k[1] for k in seen)))
