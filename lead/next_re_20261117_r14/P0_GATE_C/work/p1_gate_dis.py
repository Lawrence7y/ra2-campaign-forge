# -*- coding: utf-8 -*-
"""Disassemble gate path 0x47C620..0x47C8A0 with full bytes for path condition analysis."""
import pefile
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
    s=sec_of(va); o=s["raw"]+(va-s["va"]); return data[o:o+n]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
def dis(start,end):
    va=start
    while va<end:
        got=list(md.disasm(rd(va,16),va,count=1))
        if not got: print("  %08X  ???"%va); va+=1; continue
        i=got[0]
        b=rd(i.address,i.size).hex()
        print("  %08X  %-20s %-7s %s" % (i.address,b,i.mnemonic,i.op_str))
        va+=i.size
for lo,hi,label in [(0x47C620,0x47C760,"GateCheck 47C620"),(0x47C760,0x47C8A0,"tail 47C760")]:
    print("\n=== %s ===" % label)
    dis(lo,hi)
