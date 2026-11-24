# -*- coding: utf-8 -*-
"""U3: check Infantry/Unit slot73 UnLimbo 0x4D3780 and ObjectClass base for bit0 setter."""
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
# 0x4D3780..0x4D3BF0 (slot73 unit/infantry)
print("=== 0x4D3780 slot73 full: [reg+0x14] writes ===")
for a,sz,mn,op in disasm(0x4D3780,0x4D3C00):
    if ('0x14' in op and '[' in op and 'esp' not in op):
        print("  >>> %08X  %-7s %s" % (a,mn,op))
# show all calls
print("  calls:")
for a,sz,mn,op in disasm(0x4D3780,0x4D3C00):
    if mn=='call': print("    %08X %s" % (a,op))
# broader search: functions that write byte [reg+0x14] with reg source, list context of al/dl value
print("\n=== candidate bit0 setters: mov [reg+0x14], reg where reg likely or'd with 1 ===")
import re
for a,sz,mn,op in disasm(0x400000,0x7E1000):
    pass  # too slow; skip
# Just check 0x6F3237 context (in ObjectClass ctor)
print("\n=== 0x6F3237 context ===")
for a,sz,mn,op in disasm(0x6F3210,0x6F3250):
    mark=">>>" if a==0x6F3237 else "   "
    print(" %s %08X  %-7s %s" % (mark,a,mn,op))
