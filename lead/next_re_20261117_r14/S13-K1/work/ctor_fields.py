"""S13-K1: extract all field offsets written by each class's constructor(s).
thiscall this register tracked from first `mov reg,ecx` before any call (disc #3).
Also capture pointer-walking loops (base,count,stride) like the Verses 11-double init.
"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\work")
from re_lib import *
import capstone

CTORS = {
 "WeaponTypeClass":  [0x771C70,0x771F00,0x771F50,0x7730F0],
 "WarheadTypeClass": [0x75CEC0,0x75D230,0x75E510],
 "BulletTypeClass":  [0x46BBC0,0x46BDC0,0x46C6A0,0x46C890],
 "BulletClass":      [0x466380,0x466560,0x46AE70],
}
XECX = capstone.x86.X86_REG_ECX
lines=[]
def p(x=""): lines.append(str(x))

def this_reg(ins):
    for i in ins:
        if i.mnemonic=="call": return None
        if i.mnemonic=="mov" and len(i.operands)==2:
            d,s=i.operands
            if d.type==1 and s.type==1 and s.reg==XECX: return d.reg
    return None

def fn_extent(fn):
    at=ATLAS_FN.get(fn)
    if at: return fn+at[0]
    # independent: ret+pad
    last=fn
    for i in disasm(fn,0x400):
        last=i.address+i.size
        if i.mnemonic.startswith("ret"):
            b=read(i.address+i.size,2)
            if len(b)==2 and b[0] in (0xCC,0x90) and b[1] in (0xCC,0x90): return i.address+i.size
    return last

all_ctor = {}
for cls, fns in CTORS.items():
    offs = {}   # off -> set of (width, sites)
    p(f"\n=== {cls} constructors ===")
    for fn in fns:
        end=fn_extent(fn)
        ins=disasm(fn,end-fn)
        this=this_reg(ins)
        if this is None:
            p(f"  fn {hex(fn)}: NO this reg found (skip)"); continue
        cnt=0; loopdesc=[]
        for i in ins:
            if i.mnemonic not in ("mov","fstp","fst","movsd","movss","movzx","movsx"): continue
            for op in i.operands:
                if op.type==capstone.x86.X86_OP_MEM and op.mem.base==this and op.mem.index==0 and op.mem.disp>=0 and op.mem.disp<0x800:
                    offs.setdefault(op.mem.disp,set()).add((op.size, i.address))
                    cnt+=1
            # pointer-walk loop detection: lea reg,[this+BASE]
            if i.mnemonic=="lea" and len(i.operands)==2 and i.operands[1].type==capstone.x86.X86_OP_MEM:
                m=i.operands[1].mem
                if m.base==this and m.index==0 and i.operands[0].type==1:
                    loopdesc.append((i.address, m.disp, MD.reg_name(i.operands[0].reg)))
        p(f"  fn {hex(fn)} end={hex(end)} this={MD.reg_name(this)} direct_stores={cnt} lea_bases={[(hex(a),hex(o),r) for a,o,r in loopdesc[:10]]}")
    p(f"  TOTAL distinct ctor-written offsets: {len(offs)}")
    p("  offsets: " + " ".join(hex(o) for o in sorted(offs)))
    all_ctor[cls]=offs

# write machine-readable
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\EVIDENCE\ctor_offsets.tsv","w",encoding="utf-8") as f:
    f.write("class\toff\tsites\n")
    for cls,offs in all_ctor.items():
        for o in sorted(offs):
            sites=sorted(set(s for w,s in offs[o]))
            f.write(f"{cls}\t0x{o:X}\t" + ",".join(hex(s) for s in sites[:8]) + "\n")
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\EVIDENCE\ctor_offsets.txt","w",encoding="utf-8").write("\n".join(lines))
print("\n".join(lines))
