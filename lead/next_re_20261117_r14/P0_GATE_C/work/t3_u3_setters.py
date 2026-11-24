# -*- coding: utf-8 -*-
"""U3: fully disassemble candidate +0x14 flag setter functions."""
import struct, pefile, hashlib, bisect
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

# find callers of these functions
def callers_of(target):
    T=[s for s in secs if s["name"]==".text"][0]; T0,T1=T["va"],T["va"]+T["rawsize"]; TR=T["raw"]
    out=[]
    for va in range(T0,T1-5):
        if data[TR+(va-T0)]==0xE8:
            rel=int.from_bytes(data[TR+(va+1-T0):TR+(va+5-T0)],"little",signed=True)
            if (va+5+rel)&0xFFFFFFFF==target: out.append(va)
    return out

for f,name in [(0x4CC9A0,"4CC9A0"),(0x77A700,"77A700"),(0x5C0240,"5C0240"),(0x5C07D0,"5C07D0")]:
    print("\n=== fn %s full [0x%X,0x%X+0x80) ===" % (name,f,f))
    for a,sz,mn,op in disasm(f,f+0x90):
        mark=">>>" if ('0x14' in op and '[' in op) else "   "
        print(" %s %08X  %-7s %s" % (mark,a,mn,op))
    cs=callers_of(f)
    print("  callers (%d): %s" % (len(cs)," ".join("%08X"%c for c in cs[:20])))
