# -*- coding: utf-8 -*-
"""Final verification: RTTI arg2 class, draw filter, ctor +0x14 setter."""
import struct, pefile, hashlib
from capstone import *
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(EXE,"rb").read()
pe = pefile.PE(EXE, fast_load=True); BASE=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.rstrip(b"\x00").decode("latin1")
    secs.append(dict(name=nm,va=BASE+s.VirtualAddress,vsize=s.Misc_VirtualSize,raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
def sec_of(va):
    for s in secs:
        if s["va"]<=va<s["va"]+max(s["vsize"],s["rawsize"]): return s
    return None
def rd(va,n):
    s=sec_of(va)
    if s is None: return b""
    o=s["raw"]+(va-s["va"]); return data[o:o+n]
def u32(va):
    b=rd(va,4); return struct.unpack("<I",b)[0] if len(b)==4 else None
def va_of_fo(fo):
    for s in secs:
        if s["raw"]<=fo<s["raw"]+s["rawsize"]: return s["va"]+(fo-s["raw"]),s["name"]
    return None,None
def cstr(va):
    b=rd(va,80); z=b.find(b"\x00"); return b[:z].decode("latin1") if z!=-1 else b.decode("latin1")
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
def disasm(start,end):
    out=[]; va=start
    while va<end:
        got=list(md.disasm(rd(va,16),va,count=1))
        if not got: out.append((va,1,"?","")); va+=1; continue
        i=got[0]
        try: ops=i.op_str
        except: ops=""
        out.append((i.address,i.size,i.mnemonic,ops)); va+=i.size
    return out

# 1. Verify BuildingTypeClass TD string via COL 0x7FC618 -> TD -> TD+8
print("=== RTTI verification: arg2 class ===")
for col in [0x7FC618]:
    sig=u32(col); td=u32(col+0xC)
    print("COL %08X sig=%d TD=%08X TD+8 name=%r" % (col,sig,td,cstr(td+8)))
# Verify BuildingClass+0x520 gives BuildingTypeClass* via 0x45DD90's factory caller
print("\n=== BuildingTypeClass ctor 0x45DD90 evidence ===")
print("  0x6C2990 TClassFactory<BuildingTypeClass> method calls 0x45DD90 (see t1_caller_class.txt)")
# TD for TClassFactory<BuildingTypeClass>
i=data.find(b".?AV?$TClassFactory@VBuildingTypeClass@@@@")
if i>=0:
    va,_=va_of_fo(i); print("  factory RTTI name VA=%08X TD=%08X" % (va,va-8))

# 2. Draw filter at 0x48288C..0x4828A8
print("\n=== draw-list filter 0x482880..0x4828B0 ===")
for a,sz,mn,op in disasm(0x482880,0x4828B0):
    print("  %08X  %-7s %s" % (a,mn,op))

# 3. ctor chain [+0x14] writes with context
print("\n=== constructor +0x14 detailed ===")
for f,name,rng in [(0x4D31E0,"4D31E0",0x400),(0x6F2B40,"6F2B40",0x400),(0x5F3900,"5F3900",0x400),(0x410170,"410170",0x40)]:
    ins=disasm(f,f+rng)
    print("\n-- %s --" % name)
    for idx,(a,sz,mn,op) in enumerate(ins):
        if ('0x14' in op and '[' in op and 'esp' not in op) or (mn=='call' and idx<15):
            print("  %08X  %-7s %s" % (a,mn,op))

# 4. Check 0x5F3B39 context
print("\n=== 0x5F3B39 context ===")
for a,sz,mn,op in disasm(0x5F3B10,0x5F3B50):
    mark=">>>" if a==0x5F3B39 else "   "
    print(" %s %08X  %-7s %s" % (mark,a,mn,op))
