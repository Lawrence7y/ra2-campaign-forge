#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Focused confirmation of 0x431B80 = BufferIOFileClass::~BufferIOFileClass."""
import sys, struct, io, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work")
import pe_util as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
out=[]

def dis(va,n):
    b=P.read(va,n)
    r=[]
    for ins in md.disasm(b,va):
        r.append(f"{ins.address:08X}: {ins.bytes.hex():<16s} {ins.mnemonic} {ins.op_str}")
    return r

def class_of_vtable(vb):
    col=P.u32(vb-4)
    if col is None or P.u32(col)!=0: return None
    td=P.u32(col+0xC)
    if td is None: return None
    off=P.va2off(td+8)
    if off is None: return None
    with open(P.EXE,'rb') as f:f.seek(off);b=f.read(80)
    z=b.find(b'\x00');s=b[:z if z>=0 else 80]
    try:return s.decode('latin1')
    except:return None

# build vtable->class map for slots_of
sections=P.sections();rd=[s for s in sections if s[0]=='.rdata'][0]
_,rv,rs,pr,raw,_=rd
with open(P.EXE,'rb') as f:f.seek(pr);rdata=f.read(raw)
text=[s for s in sections if s[0]=='.text'][0];tlo,thi=text[1],text[1]+text[4]
_vbc={}
for i in range(0,len(rdata)-4,4):
    p=struct.unpack_from('<I',rdata,i)[0]
    if not(rv<=p<rv+rs):continue
    if P.u32(p)!=0:continue
    td=P.u32(p+0xC)
    if td is None:continue
    o=P.va2off(td+8)
    if o is None:continue
    with open(P.EXE,'rb') as f:f.seek(o);b=f.read(80)
    z=b.find(b'\x00');s=b[:z if z>=0 else 80]
    if s.startswith(b'.?AV') and b'@@' in s:
        _vbc[rv+i+4]=s.decode('latin1','replace')
def slots_of(f):
    r=[]
    for vb,cls in _vbc.items():
        for k in range(0,600):
            sv=P.u32(vb+4*k)
            if sv is None or not(tlo<=sv<thi):break
            if sv==f:r.append((hex(vb),cls,k));break
    return r

# 1. BufferIOFileClass vtable slots 0/1 (deleting dtor thunks)
vt=0x7E3A2C
out.append(f"BufferIOFileClass vtable base = {vt:08X}, class = {class_of_vtable(vt)}")
for k in range(0,4):
    s=P.u32(vt+4*k)
    out.append(f"  slot{k} (+0x{4*k:X}) = {s:08X}")
    out.append("\n".join("    "+l for l in dis(s,64)))

# 2. Is 0x431B80 called by slot0/slot1 thunks?
out.append("\n=== scan E8 calls to 0x431B80 within slot0 (0x432610) and slot1 (0x401940) ===")
for name,va in [("slot0_thunk",0x432610),("slot1_thunk",0x401940)]:
    calls=P.scan_rel32_calls(0x431B80,start_va=va,end_va=va+0x80)
    out.append(f"  {name} @ {va:08X}: {[hex(c[0]) for c in calls]}")

# 3. RTTI class of 0x7E1668 (what callers store before calling 0x431B80)
out.append(f"\n0x7E1668 vtable class = {class_of_vtable(0x7E1668)}")
col=P.u32(0x7E1664)
out.append(f"  0x7E1664 (vtable[-1]) = {col:08X}; sig={P.u32(col) if col else None}")
if col:
    td=P.u32(col+0xC)
    out.append(f"  TD={td:08X}")
    off=P.va2off(td+8) if td else None
    if off:
        with open(P.EXE,'rb') as f:f.seek(off);b=f.read(80)
        z=b.find(b'\x00')
        out.append(f"  name bytes = {b[:z if z>=0 else 60]!r}")

# 4. 0x65CA00 disasm (base destructor)
out.append("\n=== 0x65CA00 (tail-called base dtor) ===")
out.append("\n".join(dis(0x65CA00,96)))
# its vtable class if any
out.append(f"  0x65CA00 vtable slots: {slots_of(0x65CA00)}")
# 5. IAT name for free thunk 0x7C8B3D - disassemble it
out.append("\n=== 0x7C8B3D (called with buffer) ===")
out.append("\n".join(dis(0x7C8B3D,32)))

txt="\n".join(out)+"\n"
CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-K3"
with io.open(os.path.join(CARD,"EVIDENCE","dtor_431B80_focus.txt"),"w",encoding="utf-8") as f:f.write(txt)
sys.stdout.write(txt)
