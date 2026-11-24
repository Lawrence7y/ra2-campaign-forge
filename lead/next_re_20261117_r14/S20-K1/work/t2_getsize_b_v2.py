"""T2 Channel B (v2): tie push<size>/call alloc to vtable install of same class.

For each `push <size>; call 0x7C8E17` site in .text, scan forward ~0x60 bytes
for a `mov [reg], <vt>` vtable-install of the class's main vtable, and record
the constructor function that performs it. This is a direct allocation->class
binding independent of constructor-boundary heuristics.
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Bin, md, disasm_window, insn_text, write_tsv, write_text

b = Bin()
TLO, THI = b.sec_range(".text")
text = b.section_bytes(".text")

SIZES = {
    "AnimClass":               (0x1C8, 0x7E3354),
    "ParticleClass":           (0x138, 0x7EF954),
    "ParticleSystemClass":     (0x100, 0x7EFB9C),
    "VoxelAnimClass":          (0x148, 0x7F6318),
    "AnimTypeClass":           (0x378, 0x7E3608),
    "ParticleTypeClass":       (0x318, 0x7F0188),
    "ParticleSystemTypeClass": (0x310, 0x7F00A8),
    "VoxelAnimTypeClass":      (0x308, 0x7F6548),
}
ALLOC = 0x7C8E17

rows=[]; detail=[]
for cls,(size,vt) in SIZES.items():
    pat=b"\x68"+struct.pack("<I",size)
    pos=0; sites=[]
    while True:
        j=text.find(pat,pos)
        if j<0: break
        pos=j+1; va=TLO+j
        # confirm alloc call within 8 insns
        ins=disasm_window(b,va,64,skipdata=True)
        ok=False
        for i in ins[:8]:
            if i.mnemonic=="call" and i.op_str.lower()=="0x%x"%ALLOC: ok=True; break
        if ok: sites.append(va)
    detail.append("=== %s size=0x%X vt=%08X alloc-push sites=%d ==="%(cls,size,vt,len(sites)))
    pairs=0
    for va in sites:
        # scan forward 0x80 bytes for vtable install of vt
        ins=disasm_window(b,va,0x80,skipdata=True)
        vtwrite=None; ctorcall=None
        for i in ins:
            if i.mnemonic=="mov" and ("0x%x"%vt) in i.op_str.lower() and "ptr [" in i.op_str:
                vtwrite=i.address; break
        if vtwrite:
            detail.append("  PAIR alloc-push@%08X -> vtable-install@%08X (vt=%08X size=0x%X)"%(va,vtwrite,vt,size))
            rows.append([cls,"0x%X"%size,"%08X"%vt,"%08X"%va,"%08X"%vtwrite,"alloc+vtinstall"])
            pairs+=1
    detail.append("  pairs with vtable install: %d"%pairs)

write_tsv("T2_getsize_channelB_v2.tsv","class\tsize\tvtable\tpush_site\tvt_install_site\tkind",rows)
write_text("T2_getsize_channelB_v2.txt","\n".join(detail)+"\n")
print("\n".join(detail))
