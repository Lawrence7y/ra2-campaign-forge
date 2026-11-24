# -*- coding: utf-8 -*-
"""U3: disassemble InfantryClass ctor 0x517A50 and base ctor chain for +0x14 writes."""
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

def dump_ctor(f,name,limit=0x180):
    print("\n=== %s ctor %08X ===" % (name,f))
    for a,sz,mn,op in disasm(f,f+limit):
        mark=""
        if '0x14' in op and '[' in op and 'esp' not in op: mark=">>>"
        if mn in ('call',) and (a-f)<0x40: mark="@@ "
        print(" %s %08X  %-7s %s" % (mark,a,mn,op))

dump_ctor(0x517A50,"InfantryClass",0x200)
# also find base ctor calls within first 0x40 and dump first called ctor candidates
for f,name in [(0x517A50,"Inf")]:
    print("\n--- calls in first 0x80 of %s ctor ---" % name)
    for a,sz,mn,op in disasm(f,f+0x80):
        if mn=='call': print("  %08X call %s" % (a,op))
