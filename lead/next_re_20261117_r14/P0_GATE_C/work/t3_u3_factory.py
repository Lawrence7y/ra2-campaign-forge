# -*- coding: utf-8 -*-
"""U3: find InfantryClass/UnitClass TClassFactory Create -> constructor -> +0x14 write."""
import struct, pefile, hashlib, bisect
from capstone import *
from capstone.x86 import *
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
def u32(va):
    b=rd(va,4); return struct.unpack("<I",b)[0] if len(b)==4 else None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
TEXT=[s for s in secs if s["name"]==".text"][0]; T0,T1=TEXT["va"],TEXT["va"]+TEXT["rawsize"]; TRAW=TEXT["raw"]
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
def va_of_fo(fo):
    for s in secs:
        if s["raw"]<=fo<s["raw"]+s["rawsize"]: return s["va"]+(fo-s["raw"]),s["name"]
    return None,None
def find_td(name):
    pat=name; i=data.find(pat); out=[]
    while i!=-1:
        va,_=va_of_fo(i)
        if va: out.append(va-8)
        i=data.find(pat,i+1)
    return out

for cls in [b".?AV?$TClassFactory@VInfantryClass@@@@@", b".?AV?$TClassFactory@VUnitClass@@@@@",
            b".?AVInfantryClass@@", b".?AVUnitClass@@"]:
    print("\n=== class pattern %s ===" % cls.decode())
    tds=find_td(cls)
    print("  TD candidates: %s" % " ".join("%08X"%t for t in tds))
    for TD in tds:
        # COLs referencing this TD (COL+0xC = TD)
        pat=struct.pack("<I",TD); i=data.find(pat); cols=[]
        while i!=-1:
            va,_=va_of_fo(i)
            if va:
                cand=va-0xC
                if u32(cand) in (0,1): cols.append(cand)
            i=data.find(pat,i+1)
        print("    TD %08X COLs: %s" % (TD," ".join("%08X"%c for c in cols)))
        for col in cols:
            # vtable[-1]==col
            patc=struct.pack("<I",col); j=data.find(patc); vts=[]
            while j!=-1:
                va,_=va_of_fo(j)
                if va and j%4==0: vts.append(va+4)
                j=data.find(patc,j+1)
            print("      COL %08X vtables: %s" % (col," ".join("%08X"%v for v in vts)))
            for vt in vts[:2]:
                slots=[u32(vt+4*k) for k in range(8)]
                print("        vt %08X first 8 slots: %s" % (vt," ".join("%08X"%s for s in slots)))
# disassemble 0x4D31E0 around +0x14 write
print("\n=== fn 0x4D31E0 context around 0x4D34E0 ===")
for a,sz,mn,op in disasm(0x4D34A0,0x4D3520):
    mark=">>>" if a==0x4D34E0 else "   "
    print(" %s %08X  %-7s %s" % (mark,a,mn,op))
