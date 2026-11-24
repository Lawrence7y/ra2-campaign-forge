"""S13-K1: BulletClass has no INI loader. Derive field semantics from
constructor defaults + method read/write sites across its own vtable functions.
"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\work")
from re_lib import *
import capstone, struct

# BulletClass own methods from vtable (measured earlier)
SLOTS = [0x410260,0x46AFD0,0x46AFF0,0x46B560,0x410450,0x46AE70,0x46AFB0,0x4103E0,
 0x46B5C0,0x410470,0x4684E0,0x46B550,0x46B540,0x5F6250,0x410490,0x4104A0,0x4104B0,
 0x5F6690]
# plus clue methods: 0x468090 (Draw), 0x46B5A0, 0x466660 (Detonate?), 0x468000, 0x468670
METHODS=[("ctor",0x466380),("ctor2",0x466560),("ctor3?",0x46AE70),
 ("slot3_Update",0x46B560),("slot5",0x46AE70),("slot6",0x46AFB0),("slot8",0x46B5C0),
 ("slot10",0x4684E0),("slot11_WhatAmI",0x46B550),("slot12_GetSize",0x46B540),
 ("Draw_468090",0x468090),("m_46B5A0",0x46B5A0),("m_466660",0x466660),
 ("m_468000",0x468000),("m_468670",0x468670),("m_4686? ",0x468670)]

lines=[]
def p(x=""): lines.append(str(x))

def this_reg(ins):
    for i in ins:
        if i.mnemonic=="call": return None
        if i.mnemonic=="mov" and len(i.operands)==2:
            d,s=i.operands
            if d.type==1 and s.type==capstone.x86.X86_REG_ECX: return d.reg
    return None

# Dump full ctor 0x466380 with byte-precise stores
p("=== BulletClass ctor 0x466380 (full) ===")
at=ATLAS_FN.get(0x466380); end=0x466380+at[0] if at else 0x4664bf
for i in disasm(0x466380,end-0x466380):
    p("  "+fmt_insn(i))
p("\n=== BulletClass methods: field accesses [reg+off] with this-register ===")
access={}  # off -> list of (method, addr, mnemonic, size)
for name,fn in METHODS:
    at=ATLAS_FN.get(fn); end=fn+(at[0] if at else 0x180)
    ins=disasm(fn,min(end-fn,0x900))
    this=this_reg(ins)
    for i in ins:
        if this is None: break
        for op in i.operands:
            if op.type==capstone.x86.X86_OP_MEM and op.mem.base==this and op.mem.index==0:
                if 0x40<=op.mem.disp<0x160:
                    access.setdefault(op.mem.disp,[]).append((name,i.address,i.mnemonic,op.size))
for off in sorted(access):
    p(f"  +0x{off:03X}: " + " | ".join(f"{n}@{hex(a)} {m}.{s}" for n,a,m,s in access[off][:8]))
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\EVIDENCE\bulletclass_methods.txt","w",encoding="utf-8").write("\n".join(lines))
print("wrote", len(lines), "lines")
print("\n".join(lines[-80:]))
