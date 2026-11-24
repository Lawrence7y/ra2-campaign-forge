"""T1 v2：逐表走槽——从 vtable 起读 dword，只要值落在 .text 代码区就算一槽，
遇到非 .text 值即停。叠加"下一 COL 位置"作为硬上界。对账审计基线 14,044 槽/1,214 表。"""
import struct
import re_lib as R

b = R.Bin()
rtti = R.RTTI(b)
colset = set(rtti.cols.keys())
text = b.sec(".text")
t_lo, t_hi = text["va"], text["va"] + text["rawsize"]

s = b.sec(".rdata")
buf = b.pe.__data__[s["raw"]:s["raw"] + s["rawsize"]]
base = s["va"]
vpos = []
for i in range(0, len(buf) - 4, 4):
    if struct.unpack_from("<I", buf, i)[0] in colset:
        vpos.append((base + i, struct.unpack_from("<I", buf, i)[0]))
vpos.sort()

def walk_slots(vt, hard_end):
    slots = []
    va = vt
    while va < hard_end:
        fv = b.u32(va)
        if t_lo <= fv < t_hi:
            slots.append((va, fv))
        else:
            break
        va += 4
    return slots

rows = []
total = 0
for k, (pos, col) in enumerate(vpos):
    vt = pos + 4
    hard_end = vpos[k + 1][0] if k + 1 < len(vpos) else base + len(buf)
    slots = walk_slots(vt, hard_end)
    total += len(slots)
    rows.append(dict(vt=vt, col=col, name=rtti.cols[col]["name"],
                     n=len(slots), slots=slots))

print("tables:", len(rows), "total slots (walk .text):", total)
# 分布
from collections import Counter
dist = Counter(r["n"] for r in rows)
print("slot-count dist top20:", sorted(dist.items(), key=lambda x: -x[1])[:20])
print("zero-slot tables:", dist.get(0, 0))

with open("rdata_vtables_walk.tsv", "w", encoding="utf-8") as f:
    f.write("vtable\tcol\tname\tslots\n")
    for r in rows:
        f.write("%08X\t%08X\t%s\t%d\n" % (r["vt"], r["col"], r["name"], r["n"]))

# 线索虚表
for kv in [0x7F3058, 0x7F2FCC, 0x7E6114, 0x7E1964, 0x7EBE3C, 0x7F7B2C, 0x7F2F44, 0x7F4348]:
    for r in rows:
        if r["vt"] == kv:
            print("CLUE vt=%08X %-55s slots=%d" % (kv, r["name"], r["n"]))
            break
