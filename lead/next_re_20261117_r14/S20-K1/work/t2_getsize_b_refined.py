"""T2 Channel B (refined): tie push<size>/call alloc to class constructor calls.

For each class:
  1. vtable-install sites (from T2_vtable_writes) identify constructor bodies.
  2. Find the enclosing function entry by linear scan backward to prologue.
  3. Find direct `call <ctorEntry>` sites; in a window around each, look for
     `push <GetSize>; call 0x7C8E17` (operator new wrapper).
  4. Report pairs with both channels.
"""
import struct, sys, os, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Bin, md, disasm_window, insn_text, write_tsv, write_text

b = Bin()
TLO, THI = b.sec_range(".text")
text = b.section_bytes(".text")
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

# vtable write sites (function containing these = ctor/init)
VTWR = {
    "AnimClass":               [0x42201C, 0x422847, 0x4228EB, 0x4252BB],
    "ParticleClass":           [0x62B767, 0x62BC4A, 0x62D7C4, 0x62D9A4],
    "ParticleSystemClass":     [0x62DD16, 0x62DFA6, 0x62E077, 0x62FF6D],
    "VoxelAnimClass":          [0x749434],
    "AnimTypeClass":           [],
    "ParticleTypeClass":       [],
    "ParticleSystemTypeClass": [],
    "VoxelAnimTypeClass":      [],
}

ALLOC = 0x7C8E17

def find_fn_start(write_va, max_back=0x600):
    """Scan backwards for function entry: a ret/int3 then a prologue-like insn."""
    st = write_va - max_back
    if st < TLO: st = TLO
    ins = list(m.disasm(b.read(st, write_va - st + 32), st))
    # find candidate starts: after a ret/jmp/int3, or push ebp/sub esp
    cands = []
    for k, i in enumerate(ins):
        if i.address > write_va: break
        if i.mnemonic in ("ret", "jmp") or i.mnemonic.startswith("int"):
            if k+1 < len(ins): cands.append(ins[k+1].address)
        if i.mnemonic == "push" and i.op_str == "ebp" and k+1 < len(ins):
            if ins[k+1].mnemonic == "mov" and "ebp, esp" in ins[k+1].op_str:
                cands.append(i.address)
    # the latest candidate <= write_va
    cs = [c for c in cands if c <= write_va]
    return max(cs) if cs else None

def find_call_sites(target, max_scan=0x400000):
    """linear scan .text for E8 rel32 -> target."""
    out=[]
    pos=0
    while True:
        j=text.find(b"\xE8", pos)
        if j<0: break
        pos=j+1
        va=TLO+j
        if va+5>THI: break
        rel=struct.unpack_from("<i",text,j+1)[0]
        tgt=va+5+rel
        if tgt==target: out.append(va)
    return out

rows=[]; detail=[]
for cls,(size,vt) in SIZES.items():
    detail.append("=== %s size=0x%X vt=%08X ==="%(cls,size,vt))
    ctor_starts=set()
    for w in VTWR.get(cls,[]):
        fs=find_fn_start(w)
        detail.append("  vtwrite@%08X -> fn_start=%s"%(w,("%08X"%fs) if fs else "?"))
        if fs: ctor_starts.add(fs)
    # channel B: for each ctor start, find callers, then look for push<size>;call ALLOC in window
    found=False
    for ctor in sorted(ctor_starts):
        callers=find_call_sites(ctor)
        detail.append("  ctor=%08X direct callers=%d: %s"%(ctor,len(callers),",".join("%08X"%c for c in callers[:12])))
        for csite in callers:
            lo=csite-0x80; hi=csite+0x80
            lo=max(lo,TLO); hi=min(hi,THI)
            ins=disasm_window(b,lo,hi-lo,skipdata=True)
            # look for push size followed (within 6 insns) by call ALLOC
            for k,i in enumerate(ins):
                if i.mnemonic=="push" and i.op_str.lower()=="0x%x"%size:
                    for j2 in range(k+1,min(k+7,len(ins))):
                        if ins[j2].mnemonic=="call" and ins[j2].op_str.lower()=="0x%x"%ALLOC:
                            detail.append("    PAIR: push@%08X callalloc@%08X near ctorcall@%08X (ctor %08X)"%
                                          (i.address,ins[j2].address,csite,ctor))
                            rows.append([cls,"0x%X"%size,"%08X"%vt,"%08X"%i.address,
                                         "%08X"%ins[j2].address,"%08X"%csite,"%08X"%ctor])
                            found=True
                            break
    if not found:
        detail.append("  NO PAIR FOUND (channel B unresolved via direct ctor callers)")

write_tsv("T2_getsize_channelB_refined.tsv","class\tsize\tvtable\tpush_site\tcall_alloc\tcall_ctor_site\tctor",rows)
write_text("T2_getsize_channelB_refined.txt","\n".join(detail)+"\n")
print("\n".join(detail[:140]))
