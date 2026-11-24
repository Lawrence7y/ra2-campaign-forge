# -*- coding: utf-8 -*-
"""Decode INI key strings and dump remaining E58 write contexts."""
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
def cstr(va):
    b=rd(va,128); z=b.find(b"\x00"); return b[:z].decode("latin1") if z!=-1 else b.decode("latin1")
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

print("=== INI key strings referenced in 0x45FE95 loader ===")
for a in [0x81AA30,0x81AA3C,0x81AA4C,0x81AA5C,0x81AA88,0x81AA8C,0x81AA94,0x81AAA0,0x81AA20]:
    print("  0x%08X: %r" % (a,cstr(a)))

print("\n=== start of 0x45DD90 (verify bl=0) ===")
for a,sz,mn,op in disasm(0x45DD90,0x45DDE0):
    print("  %08X  %-7s %s" % (a,mn,op))

print("\n=== full 0x45FE95 INI loader field writes (0x460800..0x460B20) ===")
for a,sz,mn,op in disasm(0x460800,0x460B20):
    if ('0x16' in op and '[' in op) or '5295f0' in op.lower() or '0x81aa' in op.lower():
        print("  %08X  %-7s %s" % (a,mn,op))

for addr,tag in [(0x465210,"E58/BuildingTypeClass"),(0x465531,"E58/465450"),(0x465D18,"E58/465CC0"),
                 (0x523AF8,"E58/5239D0"),(0x524E98,"E58/InfantryTypeClass"),(0x7471A5,"E58/7470D0"),
                 (0x747BC4,"E58/UnitTypeClass"),(0x748098,"E58/74800A")]:
    print("\n=== WRITE %s @ %08X ===" % (tag,addr))
    for a,sz,mn,op in disasm(addr-0x50,addr+0x10):
        mark=">>>" if a==addr else "   "
        print(" %s %08X  %-7s %s" % (mark,a,mn,op))
