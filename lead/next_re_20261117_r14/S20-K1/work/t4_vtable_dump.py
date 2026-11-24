"""T4: Dump all main-vtable slots with implementation addresses and a short
signature (first insns, ret form, approx size). Byte-level, no atlas dependency."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Bin, md, disasm_window, insn_text, write_tsv, write_text

b = Bin()
m = md(detail=True, skipdata=True)
CLASSES = [
    ("AnimClass",               0x7E3354, 124),
    ("ParticleClass",           0x7EF954, 123),
    ("ParticleSystemClass",     0x7EFB9C, 122),
    ("VoxelAnimClass",          0x7F6318, 122),
]
rows=[]; detail=[]
for cls, vt, nslot in CLASSES:
    detail.append("=== %s main vtable %08X slots=%d ==="%(cls,vt,nslot))
    for s in range(nslot):
        fn = b.u32(vt+4*s)
        # signature: first 4 real insns
        try:
            ins = [i for i in m.disasm(b.read(fn,48),fn) if i.id!=0][:5]
            sig = "; ".join(insn_text(i) for i in ins)
        except Exception:
            sig="?"
        # ret form: scan up to 512 bytes for first ret
        retform=""
        try:
            for i in m.disasm(b.read(fn,512),fn):
                if i.id==0: continue
                if i.mnemonic=="ret":
                    retform = "ret" + ((" "+i.op_str) if i.op_str else "")
                    break
        except Exception: pass
        # immediate-value slots (GetSize/WhatAmI are mov eax,imm;ret)
        rows.append([cls, "%08X"%vt, s, "0x%X"%(4*s), "%08X"%fn, retform, sig])
        detail.append("  v[%3d] +0x%03X = %08X  %-10s | %s"%(s,4*s,fn,retform,sig[:90]))
write_tsv("T4_vtable_slots.tsv","class\tvtable\tslot\toffset\timpl\tretform\tfirst_insns",rows)
write_text("T4_vtable_slots.txt","\n".join(detail)+"\n")
print("wrote %d slot rows"%len(rows))
