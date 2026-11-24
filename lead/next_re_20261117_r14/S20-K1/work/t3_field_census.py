"""T3: field-access census per class.

Method set = all main-vtable slot impls (dedup) + ctor ranges (vtable-writer funcs).
Track registers holding `this` (ecx at entry) via simple mov propagation; for
each [reg+disp] within object size, record read/write with capstone operand
access flags. Aggregate per offset. Byte-level, no atlas dependency.
"""
import sys, os, struct
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Bin, md, insn_text, write_tsv, write_text
import capstone

b = Bin()
m = md(detail=True, skipdata=True)
CLASSES = [
    ("AnimClass",           0x7E3354, 124, 0x1C8),
    ("ParticleClass",       0x7EF954, 123, 0x138),
    ("ParticleSystemClass", 0x7EFB9C, 122, 0x100),
    ("VoxelAnimClass",      0x7F6318, 122, 0x148),
]
VTWR = {
    "AnimClass":[0x42201C], "ParticleClass":[0x62B767],
    "ParticleSystemClass":[0x62DD16], "VoxelAnimClass":[0x749434],
}

def fn_start(w, back=0x600):
    st=max(0x401000,w-back); ins=list(m.disasm(b.read(st,w-st+32),st)); c=[]
    for k,i in enumerate(ins):
        if i.address>w: break
        if i.mnemonic in ("ret","jmp") or i.mnemonic.startswith("int"):
            if k+1<len(ins): c.append(ins[k+1].address)
        if i.mnemonic=="push" and i.op_str=="ebp" and k+1<len(ins) and ins[k+1].mnemonic=="mov" and "ebp, esp" in ins[k+1].op_str:
            c.append(i.address)
    cs=[x for x in c if x<=w]
    return max(cs) if cs else w

def fn_end(start, maxb=0x3000):
    """first ret/jmp after some instructions"""
    try:
        for i in m.disasm(b.read(start,maxb),start):
            if i.id==0: continue
            if i.mnemonic=="ret" and i.address>start+8:
                return i.address+i.size
    except Exception: pass
    return start+0x100

def analyze_fn(cls, fn, size):
    """Return list of (off, kind, addr, text)."""
    acc=[]
    try:
        ins=list(m.disasm(b.read(fn,0x1000),fn))
    except Exception:
        return acc
    thisregs={'ecx'}
    for i in ins:
        if i.id==0: continue
        # propagate this through mov reg,reg
        if i.mnemonic=="mov" and len(i.operands)==2:
            a,bop=i.operands
            if a.type==capstone.x86.X86_OP_REG and bop.type==capstone.x86.X86_OP_REG:
                an=i.reg_name(a.reg); bn=i.reg_name(bop.reg)
                if bn in thisregs and an!=bn: thisregs.add(an)
                elif bn not in thisregs and an in thisregs: thisregs.discard(an)
        # memory operands
        for op in i.operands:
            if op.type!=capstone.x86.X86_OP_MEM: continue
            mem=op.mem
            if mem.base==0: continue
            basename=i.reg_name(mem.base)
            if basename not in thisregs: continue
            disp=mem.disp & 0xFFFFFFFF
            if disp>=size: continue
            access=op.access
            kind='W' if access & capstone.CS_AC_WRITE else ('R' if access & capstone.CS_AC_READ else '?')
            acc.append((disp,kind,i.address,insn_text(i)))
        # terminate at ret
        if i.mnemonic=="ret": break
    return acc

allaccess=defaultdict(list)  # (cls,off)-> list of (kind,addr,text,fn)
summary=[]
for cls, vt, nslot, size in CLASSES:
    methods=set()
    for s in range(nslot):
        fn=b.u32(vt+4*s)
        if 0x401000<=fn<0x7E1000: methods.add(fn)
    for w in VTWR[cls]:
        fs=fn_start(w); fe=fn_end(fs)
        methods.add(fs)
    summary.append("%s vt=%08X slots=%d size=0x%X methods=%d"%(cls,vt,nslot,size,len(methods)))
    for fn in sorted(methods):
        for off,kind,addr,txt in analyze_fn(cls,fn,size):
            allaccess[(cls,off)].append((kind,addr,txt,fn))

# emit per-offset census
rows=[]
for (cls,off),lst in sorted(allaccess.items()):
    w=[x for x in lst if x[0]=='W']; r=[x for x in lst if x[0]=='R']
    rows.append([cls,"0x%X"%off,len(w),len(r),
                 ",".join("%08X"%x[1] for x in w[:12]),
                 ",".join("%08X"%x[1] for x in r[:12]),
                 "; ".join(x[2] for x in (w+r)[:4])])
write_tsv("T3_field_census.tsv","class\toffset\twriters\treaders\twriter_addrs\treader_addrs\tsample_insns",rows)

# detail text
detail=[]
for cls,_,_,size in CLASSES:
    detail.append("=== %s size=0x%X field census (offsets with >=1 writer) ==="%(cls,size))
    for (c,off),lst in sorted(allaccess.items()):
        if c!=cls: continue
        w=[x for x in lst if x[0]=='W']; r=[x for x in lst if x[0]=='R']
        if not w: continue
        detail.append("  +0x%03X W=%d R=%d"%(off,len(w),len(r)))
        for kind,addr,txt,fn in lst[:10]:
            detail.append("      %08X W=%s fn=%08X  %s"%(addr,kind,fn,txt[:80]))
write_text("T3_field_census.txt","\n".join(summary)+"\n\n"+"\n".join(detail)+"\n")
print("\n".join(summary))
print("offset rows:",len(rows))
