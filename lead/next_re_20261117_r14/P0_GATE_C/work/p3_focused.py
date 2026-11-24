# -*- coding: utf-8 -*-
"""Focused: prologue of 7CCFFC (ebp frame?), RTTI of vtable 7EE0F4, 55A710, callers of 4CCA20, FindTechnoNearestTo."""
import pefile, struct
from capstone import *
from capstone.x86 import *
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
def rd(va,n):
    s=sec_of(va)
    if s is None: return b""
    o=s["raw"]+(va-s["va"]); return data[o:o+n]
def u32(va):
    b=rd(va,4); return struct.unpack("<I",b)[0] if len(b)==4 else None
TEXT=[s for s in secs if s["name"]==".text"][0]; T0,T1=TEXT["va"],TEXT["va"]+TEXT["rawsize"]; TRAW=TEXT["raw"]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
def dis(start,end,marks=None):
    marks=marks or {}
    va=start
    while va<end:
        got=list(md.disasm(rd(va,16),va,count=1))
        if not got: print("  %08X  ???"%va); va+=1; continue
        i=got[0]
        mk=">>>" if i.address in marks else "   "
        print("  %s %08X  %-7s %s"%(mk,i.address,i.mnemonic,i.op_str))
        va+=i.size

print("=== prologue 0x7CCFFC ===")
dis(0x7CCFFC,0x7CD020)
print("\n=== RTTI via vtable 0x7EE0F4 (5C0247/5C0920 object vtable) ===")
# find COL referencing vtable, TD+8 name
for s in secs:
    if s["name"]==".text": continue
    for off in range(0,s["rawsize"]-3,4):
        v=struct.unpack_from("<I",data,s["raw"]+off)[0]
        if v==0x7EE0F4:
            colva=s["va"]+off
            td=u32(colva+0xC)
            if td:
                b=rd(td+8,80); z=b.find(b"\x00")
                print("  col=%08X td=%08X name=%r"%(colva,td,b[:z].decode('latin1') if z!=-1 else b.decode('latin1')))
print("\n=== 0x55A710 (called by 4CCA20) ===")
dis(0x55A710,0x55A770)
print("\n=== callers of 0x4CCA20 (E8 scan) ===")
for va in range(T0,T1-4):
    if data[TRAW+(va-T0)]==0xE8:
        rel=int.from_bytes(data[TRAW+(va+1-T0):TRAW+(va+5-T0)],"little",signed=True)
        if (va+5+rel)&0xFFFFFFFF==0x4CCA20: print("  call@%08X"%va)
print("\n=== FindTechnoNearestTo 0x47C3D0..0x47C4D0 ===")
dis(0x47C3D0,0x47C4D0,{0x47C3E3,0x47C427,0x47C430,0x47C440,0x47C491,0x47C4A7})
