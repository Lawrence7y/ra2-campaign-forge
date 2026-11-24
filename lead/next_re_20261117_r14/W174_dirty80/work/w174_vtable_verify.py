#!/usr/bin/env python3
"""Raw-byte verification of vtable slots (independent of symbols.json / RTTI tooling).
Reads dword at vtable_va + 4*slot directly from gamemd.exe raw bytes.
Checks:
  TeamClass vtable 0x7F4730 slot 23 -> expect 0x6E9140
  BuildingClass vtable 0x7E3EBC slot ? -> known ObjectClass-family
Also checks ObjectClass.h / TeamClass.h source text lines verbatim.
"""
import os, sys, struct, pefile
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=r"D:\Project\ra2-campaign-forge"
pe=pefile.PE(os.path.join(ROOT,"ra2youli","gamemd.exe"),fast_load=True)
IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append((IB+s.VirtualAddress,s.PointerToRawData,s.SizeOfRawData,s.Name.decode(errors="replace").rstrip("\0")))
def u32(va):
    for v,r,sz,n in secs:
        if v<=va and va+4<=v+sz:
            off=r+(va-v)
            return struct.unpack("<I",pe.__data__[off:off+4])[0]
    return None
out=[]
out.append("=== raw vtable dword reads (ImageBase %08X) ==="%IB)
tests=[("TeamClass",0x7F4730,23),("TeamClass",0x7F4730,0),("TeamClass",0x7F4730,3),
       ("BuildingClass",0x7E3EBC,73),("ObjectClass-ish",0x7E1F50,23)]
for name,vt,slot in tests:
    val=u32(vt+4*slot)
    out.append("%-16s vt=%08X slot=%d(+0x%X) -> %s"%(name,vt,slot,4*slot,("%08X"%val) if val else "??"))
# scan all dwords in .rdata for value 0x6E9140 -> which vtables reference it
target=0x6E9140
refs=[]
for v,r,sz,n in secs:
    if n not in (".rdata",):continue
    data=pe.__data__[r:r+sz]
    for i in range(0,len(data)-3,4):
        x=struct.unpack("<I",data[i:i+4])[0]
        if x==target:refs.append(v+i)
out.append("dword refs to 0x6E9140 in .rdata: %s"%(" ".join("%08X"%x for x in refs)))
for x in refs:
    out.append("  ref %08X: slot index from vtable bases:"%x)
    for name,vt,slotc in [("TeamClass",0x7F4730,24),("TeamTypeClass",0x7F47D0,27)]:
        if vt<=x<vt+4*slotc:
            out.append("    -> %s slot %d (+0x%X)"%(name,(x-vt)//4,x-vt))
# source lines
for src,marker in [("YRpp/ObjectClass.h","NeedsRedraw"),
                   ("YRpp/TeamClass.h","StepCompleted"),
                   ("YRpp/ObjectClass.h","InLimbo"),
                   ("YRpp/TeamClass.h","FirstUnit")]:
    path=os.path.join(ROOT,src)
    with open(path,"r",encoding="utf-8",errors="replace") as f:
        for ln,line in enumerate(f,1):
            if marker in line:
                out.append("%s:%d: %s"%(src,ln,line.rstrip()))
with open(os.path.join(HERE,"..","EVIDENCE","w174_vtable_raw_verify.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(out)+"\n")
print("\n".join(out))
