#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W29 recon4: final targeted closure. Read-only."""
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
def find_all(h,n):
    o=[];s=0
    while True:
        p=h.find(n,s)
        if p<0:break
        o.append(p);s=p+1
    return o
def cstr(va,maxlen=120):
    o=va2off(va)
    if o is None:return "<unmapped>"
    b=data[o:o+maxlen];z=b.find(b"\x00")
    return repr(b if z<0 else b[:z])

print("==== E8 raw call sites to 0x734990 / 0x7346A0 / 0x734952 ====")
trva=traw=trsz=None
for n,rva,vsz,raw,rsz in secs:
    if n==".text":trva,traw,trsz=rva,raw,rsz
for tgt in [0x7346A0,0x734990,0x734952,0x734D30]:
    sites=[]
    for off in range(traw,traw+trsz-5):
        if data[off]!=0xE8:continue
        rel=struct.unpack_from("<i",data,off+1)[0]
        cv=IB+trva+(off-traw)
        if cv+5+rel==tgt:sites.append(cv)
    print("  target 0x%08X : %d site(s) %s"%(tgt,len(sites),", ".join("0x%X"%x for x in sites)))

print("\n==== 0x7346A0 tail (0x7348A0 -> 0x734952) ====")
disasm(0x7348A0,60,"0x7348A0 (after 1st Get_File / CSF body)")
disasm(0x73491A,12,"0x73491A failure exit")

print("\n==== 0x734990 header / name source ====")
disasm(0x734990,40,"0x734990 (2nd CSF reader, from entry)")
print("  cstr(0x8457C8) =",cstr(0x8457C8))
print("  cstr(0x816210) =",cstr(0x816210))

print("\n==== CWD: SetCurrentDirectoryA at 0x6BC07E, synced from 0x6BC070 ====")
disasm(0x6BC070,20,"0x6BC070 (SetCurrentDirectoryA call site)")

print("\n==== ra2bench MIX headers (first 12 bytes; format+flags) ====")
import os
base=r"D:\Project\ra2-campaign-forge\ra2bench"
for fn in ["langmd.mix","language.mix","ra2md.mix","ra2.mix","expandmd01.mix"]:
    p=os.path.join(base,fn)
    try:
        with open(p,"rb") as f:h=f.read(12)
        w0,w1=struct.unpack_from("<HH",h,0)
        print("  %-18s size=%-10d first4=%s  word0=0x%04X word1(flags)=0x%04X  flags&2(encrypted)=%s"%(fn,os.path.getsize(p),h[:4].hex(),w0,w1,bool(w1&2)))
    except Exception as e:
        print("  %-18s ERROR %s"%(fn,e))

print("\n==== crc32 of CSF-ish names (engine normalizes to UPPER) ====")
import zlib
for nm in ["ra2md.csf","RA2MD.CSF","ra2.csf","RA2.CSF","ra2md.str","RA2MD.STR"]:
    print("  %-12s -> 0x%08X"%(nm,zlib.crc32(nm.encode("ascii"))&0xffffffff))

print("\nDONE recon4")
