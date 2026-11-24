"""T2 Channel B (v3): push<size>/call alloc site whose window contains call to a
function that installs this class's main vtable (constructor range)."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Bin, md, disasm_window, insn_text, write_tsv, write_text

b = Bin(); TLO, THI = b.sec_range(".text"); text=b.section_bytes(".text")
m = md(detail=True, skipdata=True)

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
VTWR = {
    "AnimClass":               [0x42201C, 0x422847, 0x4228EB, 0x4252BB],
    "ParticleClass":           [0x62B767, 0x62BC4A, 0x62D7C4, 0x62D9A4],
    "ParticleSystemClass":     [0x62DD16, 0x62DFA6, 0x62E077, 0x62FF6D],
    "VoxelAnimClass":          [0x749434],
    "AnimTypeClass":           [0x428E80],
    "ParticleTypeClass":       [0x645930],
    "ParticleSystemTypeClass": [0x644940],
    "VoxelAnimTypeClass":      [0x74BA20],
}
ALLOC=0x7C8E17

def find_fn_start(write_va, max_back=0x600):
    st=max(TLO,write_va-max_back)
    ins=list(m.disasm(b.read(st,write_va-st+32),st))
    cands=[]
    for k,i in enumerate(ins):
        if i.address>write_va: break
        if i.mnemonic in ("ret","jmp") or i.mnemonic.startswith("int"):
            if k+1<len(ins): cands.append(ins[k+1].address)
        if i.mnemonic=="push" and i.op_str=="ebp" and k+1<len(ins) and ins[k+1].mnemonic=="mov" and "ebp, esp" in ins[k+1].op_str:
            cands.append(i.address)
    cs=[c for c in cands if c<=write_va]
    return max(cs) if cs else None

rows=[]; detail=[]
for cls,(size,vt) in SIZES.items():
    ranges=[]
    for w in VTWR.get(cls,[]):
        fs=find_fn_start(w)
        if fs: ranges.append((fs,w))
    detail.append("=== %s size=0x%X vt=%08X ctor_ranges=%s ==="%
                  (cls,size,vt,",".join("%08X-%08X"%r for r in ranges)))
    pat=b"\x68"+struct.pack("<I",size); pos=0; sites=[]
    while True:
        j=text.find(pat,pos)
        if j<0: break
        pos=j+1; va=TLO+j
        ins=disasm_window(b,va,48,skipdata=True)
        if any(i.mnemonic=="call" and i.op_str.lower()=="0x%x"%ALLOC for i in ins[:8]):
            sites.append(va)
    pairs=0
    for va in sites:
        lo=max(TLO,va-0x40); hi=min(THI,va+0x80)
        ins=disasm_window(b,lo,hi-lo,skipdata=True)
        for i in ins:
            if i.mnemonic=="call" and i.op_str.startswith("0x"):
                tgt=int(i.op_str,16)
                for fs,we in ranges:
                    if fs<=tgt<=we:
                        detail.append("  PAIR push@%08X alloccall-> ctorcall@%08X target=%08X range=%08X-%08X"%
                                      (va,i.address,tgt,fs,we))
                        rows.append([cls,"0x%X"%size,"%08X"%vt,"%08X"%va,
                                     "%08X"%i.address,"%08X"%tgt])
                        pairs+=1
                        break
    detail.append("  pairs: %d (alloc sites=%d)"%(pairs,len(sites)))

write_tsv("T2_getsize_channelB_v3.tsv","class\tsize\tvtable\tpush_site\tctor_call_site\tctor_target",rows)
write_text("T2_getsize_channelB_v3.txt","\n".join(detail)+"\n")
print("\n".join(detail))
