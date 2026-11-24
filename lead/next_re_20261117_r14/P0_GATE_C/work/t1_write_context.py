# -*- coding: utf-8 -*-
"""P0-GATE-C Task1: dump context around each write point for value-source tracing."""
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

WRITE_SITES = [
 (0x45E145,"16BF"),(0x45E13F,"16BE"),(0x45E115,"16B7"),(0x45DE5E,"E58"),
 (0x460ABA,"16BF"),(0x460AAF,"16BE"),(0x460A13,"16B7"),
 (0x465210,"E58"),(0x465531,"E58"),(0x465D18,"E58"),
 (0x523AF8,"E58"),(0x524E98,"E58"),
 (0x7471A5,"E58"),(0x747BC4,"E58"),(0x748098,"E58"),
]
for addr,tag in WRITE_SITES:
    print("\n=== WRITE %s @ %08X : context [addr-0x60, addr+0x10) ===" % (tag,addr))
    for a,sz,mn,op in disasm(addr-0x60,addr+0x10):
        mark=">>>" if a==addr else "   "
        print(" %s %08X  %-7s %s" % (mark,a,mn,op))
