# -*- coding: utf-8 -*-
"""Dump vtable clusters around slots; find COL via [vt-4]->COL; object sizes at alloc sites."""
import pefile, struct
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
def rd(va,n):
    s=sec_of(va)
    if s is None: return b""
    o=s["raw"]+(va-s["va"]); return data[o:o+n]
def u32(va):
    b=rd(va,4); return struct.unpack("<I",b)[0] if len(b)==4 else None
def cstr(va):
    b=rd(va,96); z=b.find(b"\x00"); return b[:z].decode("latin1") if z!=-1 else b.decode("latin1")
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
def dis(start,end):
    va=start
    while va<end:
        got=list(md.disasm(rd(va,16),va,count=1))
        if not got: va+=1; continue
        i=got[0]; print("    %08X %-7s %s"%(i.address,i.mnemonic,i.op_str)); va+=i.size

def try_col(vt):
    """MSVC: [vtable_base-4] -> COL; COL+0xC -> TD; TD+8 -> name"""
    p=u32(vt-4)
    if p and sec_of(p):
        sig=u32(p); td=u32(p+0xC)
        if sig==0 and td and sec_of(td):
            nm=cstr(td+8)
            if nm.startswith('.?AV'): return hex(p),hex(td),nm
    return None
print("=== vtable cluster around 0x7E8A00 (fn 4CCA20 slot) ===")
for va in range(0x7E89D0,0x7E8A40,4):
    v=u32(va)
    extra=""
    if v and 0x400000<=v<0x800000: extra=" <- dword"
    print("  %08X: %08X%s"%(va,v or 0,extra))
# scan for COL in region pointing to TD
for va in range(0x7E89C0,0x7E8A40,4):
    r=try_col(va)
    if r: print("  COL@%08X vtable_base=%08X -> %s"%(va,va,r))

print("\n=== vtable cluster around 0x7F7958 / 0x7F79C8 (fn 7B23B0 slots) ===")
for base in [0x7F7958,0x7F79C8]:
    for va in range(base-0x20,base+0x20,4):
        r=try_col(va)
        if r: print("  COL@%08X vtable_base=%08X -> %s"%(va,va,r))
    print("  [base-4]=%08X [base-8]=%08X"%(u32(base-4) or 0,u32(base-8) or 0))

print("\n=== vtable 0x7EE0F4 cluster (5C0247/5C0920) ===")
for va in range(0x7EE0D0,0x7EE120,4):
    r=try_col(va)
    if r: print("  COL@%08X vtable_base=%08X -> %s"%(va,va,r))

print("\n=== alloc 0x7B20E0 (called by 7B23B0 via ebp=eax) ===")
dis(0x7B20E0,0x7B2120)
print("\n=== callers of 0x77A700: full context at each ===")
for c in [0x786c84,0x786cfa,0x799420,0x79a469,0x7aba77]:
    print("  -- call@%08X --"%c)
    dis(c-0x30,c+0x10)
