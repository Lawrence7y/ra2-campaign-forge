#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W29 recon3: targeted closure. Read-only."""
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE=r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe"; IB=0x400000
pe=pefile.PE(EXE,fast_load=True); data=open(EXE,"rb").read()
secs=[(s.Name.rstrip(b"\x00").decode("latin1"),s.VirtualAddress,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
def va2off(va):
    rva=va-IB
    for n,srva,vsz,raw,rsz in secs:
        if srva<=rva<srva+max(vsz,rsz):
            o=raw+(rva-srva)
            if o<raw+rsz:return o
    return None
def off2va(off):
    for n,rva,vsz,raw,rsz in secs:
        if raw<=off<raw+rsz:return IB+rva+(off-raw)
    return None
md=Cs(CS_ARCH_X86,CS_MODE_32)
def disasm(va,n,label=""):
    off=va2off(va)
    print("\n---- DISASM %s VA=0x%08X RVA=0x%08X FOFF=0x%08X (n=%d) ----"%(label,va,va-IB,off if off is not None else -1,n))
    if off is None:print(" !! unmapped");return
    c=0
    for i in md.disasm(data[off:off+n*8],va):
        o=va2off(i.address)
        print("  VA=0x%08X RVA=0x%08X FOFF=0x%08X  %-22s  %-7s %s"%(i.address,i.address-IB,o if o is not None else -1," ".join("%02X"%x for x in i.bytes),i.mnemonic,i.op_str))
        c+=1
        if c>=n:break
def d32(va):
    o=va2off(va);return struct.unpack_from("<I",data,o)[0] if o is not None else None
def find_all(h,n):
    o=[];s=0
    while True:
        p=h.find(n,s)
        if p<0:break
        o.append(p);s=p+1
    return o

print("==== CCFileClass vtable 0x7E16B0 (first 20 slots) ====")
for k in range(20):
    va=0x7E16B0+4*k
    v=d32(va)
    print("  +0x%02X [0x%08X]=0x%08X  %s"%(4*k,va,v if v is not None else -1,"-> .text" if (v and 0x401000<=v<0x7E0000) else ""))
print("\n==== MixFileClass vtable 0x7EDF50 / List 0x7EDF38 sanity (is code?) ====")
for va in [0x7EDF38,0x7EDF50,0x7E1A44,0x7E1AF4,0x7E4A28]:
    print("  [0x%08X]=0x%08X"%(va,d32(va)))

print("\n==== GetFileName helper (vtable +4 target) & strupr ====")
gf=d32(0x7E16B0+4)
print("  CCFileClass vtable +4 = 0x%08X"%gf)
disasm(gf,30,"CCFileClass vtable+4 (GetFileName?)")
disasm(0x7DCFC4,20,"0x7DCFC4 (assert strupr / name normalization)")
disasm(0x7CAF30,24,"0x7CAF30 (assert strrchr(buf,'.'))")
disasm(0x473B10,24,"0x473B10 (CCFileClass::Read)")
disasm(0x47AAB0,24,"0x47AAB0 (disk read path target)")

print("\n==== CSF loader: second stage / failure branch ====")
disasm(0x734900,55,"0x734900 (between 1st and 2nd Get_File)")
disasm(0x73491A,12,"0x73491A (Open/Get_File failure branch)")
disasm(0x7349A0,16,"0x7349A0 (2nd CCFileClass ctor before 0x7349C2)")

print("\n==== MIX header magic / flags (MixFileClass ctor 0x5B3C20) ====")
disasm(0x5B3CD0,60,"MixFileClass ctor header parse")

print("\n==== CWD establishment: xref IAT slots ====")
for slot,api in [(0x7E11A8,"GetModuleFileNameA"),(0x7E1148,"SetCurrentDirectoryA"),(0x7E11BC,"CreateFileA"),(0x7E1208,"FindFirstFileA")]:
    pat=struct.pack("<I",slot);hits=find_all(data,pat)
    print("\n  IAT slot 0x%08X (%s): %d imm32 occurrence(s)"%(slot,api,len(hits)))
    for h in hits[:20]:
        sec="?"
        for n,rva,vsz,raw,rsz in secs:
            if raw<=h<raw+rsz:sec=n
        p2=data[h-2] if h>=2 else 0;p1=data[h-1] if h>=1 else 0
        hint="call [imm32]" if (p2==0xFF and p1==0x15) else ("mov r32,[imm32]" if p2==0x8B else "?")
        print("    FOFF=0x%08X VA=0x%08X sec=%-6s prev=%02X %02X %s"%(h,off2va(h) or -1,sec,p2,p1,hint))
# disasm around GetModuleFileNameA/SetCurrentDirectoryA call sites
for va,lab in [(0x6BBFD0,"0x6BBFD0 GetModuleFileNameA region"),(0x6BC060,"0x6BC060 SetCurrentDirectoryA region")]:
    disasm(va,24,lab)

print("\n==== extension-literal inventory (Q3: any per-extension priority table?) ====")
for lit in [b".csf",b".CSF",b".ini",b".INI",b".mix",b".MIX",b".str",b".STR",b".CSF\0"]:
    hs=find_all(data,lit)
    print("  %-8r : %d hit(s) %s"%(lit,len(hs),", ".join("VA=0x%X"%(off2va(h) or -1) for h in hs[:10])))
# xref .csf literal VA explicitly
print("\n  xrefs to 0x8457EC ('.csf'):")
for h in find_all(data,struct.pack("<I",0x8457EC)):
    print("    FOFF=0x%08X VA=0x%08X sec prev=%02X %02X"%(h,off2va(h) or -1,data[h-2] if h>=2 else 0,data[h-1] if h>=1 else 0))
print("\n  xrefs to 0x840D40 ('ra2md.str'):")
for h in find_all(data,struct.pack("<I",0x840D40)):
    print("    FOFF=0x%08X VA=0x%08X prev=%02X"%(h,off2va(h) or -1,data[h-1] if h>=1 else 0))

print("\nDONE recon3")
