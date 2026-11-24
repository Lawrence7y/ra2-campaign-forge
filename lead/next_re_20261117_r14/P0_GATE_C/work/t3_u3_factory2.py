# -*- coding: utf-8 -*-
"""U3: list TClassFactory RTTI names; disassemble candidate +0x14 setters."""
import struct, pefile, hashlib, re
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
# all RTTI names containing TClassFactory
print("=== RTTI names containing 'TClassFactory' (first 30) ===")
hits=[]
for m in re.finditer(rb"\.\?AV\?\$TClassFactory@V[^@]+@@@@", data):
    s=m.group().decode("latin1")
    hits.append(s)
for s in sorted(set(hits))[:30]: print("  ",s)
print("  total:",len(set(hits)))
# also Infantry/Unit factory variants
for m in re.finditer(rb"\.\?AV[^\x00]{0,60}InfantryClass[^\x00]{0,20}", data):
    s=m.group().decode("latin1")
    if "Factory" in s: print("  INF FACTORY:",s)
for m in re.finditer(rb"\.\?AV[^\x00]{0,60}UnitClass[^\x00]{0,20}", data):
    s=m.group().decode("latin1")
    if "Factory" in s: print("  UNIT FACTORY:",s)

# disassemble candidate setters
for f,name,rng in [(0x5D5B60,"5D5B60",0x40),(0x59D6AD,"59D6AD",0x60),(0x5F3900,"5F3900",0x60),
                   (0x410170,"410170",0x50),(0x588C10,"588C10",0x50),(0x6F2B40,"6F2B40",0x50)]:
    print("\n=== fn %s ===" % name)
    for a,sz,mn,op in disasm(f,f+rng):
        mark=">>>" if ('0x14' in op and '[' in op and 'esp' not in op) else "   "
        print(" %s %08X  %-7s %s" % (mark,a,mn,op))
