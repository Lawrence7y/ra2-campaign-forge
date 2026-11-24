# -*- coding: utf-8 -*-
"""U3 focused: disassemble cell-add/remove + limbo functions; search for [reg+0x14] writes."""
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

# Known functions that add/remove objects from cell chains and limbo
FUNCS = [
 (0x47E8A0,0x47EA90,"cell chain ADD (47E8A0)"),
 (0x47EA90,0x47EC90,"cell chain REMOVE (47EA90)"),
 (0x5F4D30,0x5F4E50,"Limbo (5F4D30)"),
 (0x4824D4,0x482960,"draw-list consumer (4824D4)"),
 (0x47C3D0,0x47C4C8,"FindTechnoNearestTo (47C3D0)"),
]
for st,en,name in FUNCS:
    print("\n=== %s : [0x%X, 0x%X) ===" % (name,st,en))
    for a,sz,mn,op in disasm(st,en):
        if '0x14' in op and '[' in op:
            print("  >>> %08X  %-7s %s" % (a,mn,op))
    # also show first 20 insns for orientation
    print("  --- first 15 ---")
    for a,sz,mn,op in disasm(st,st+0x50)[:15]:
        print("      %08X  %-7s %s" % (a,mn,op))
