# -*- coding: utf-8 -*-
"""U2/Task3: trace 10 call sites of 0x47C620, dump arg setup context."""
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
TEXT=[s for s in secs if s["name"]==".text"][0]; T0,T1=TEXT["va"],TEXT["va"]+TEXT["rawsize"]; TRAW=TEXT["raw"]
# find E8 call sites to 0x47C620
TARGET=0x47C620
sites=[]
for va in range(T0,T1-5):
    if data[TRAW+(va-T0)]==0xE8:
        rel=int.from_bytes(data[TRAW+(va+1-T0):TRAW+(va+5-T0)],"little",signed=True)
        if (va+5+rel)&0xFFFFFFFF==TARGET: sites.append(va)
print("=== call sites of 0x47C620 : %d ===" % len(sites))
# fn boundary
pad=set([T0]);e8s=set()
for va in range(T0,T1-5):
    b=data[TRAW+(va-T0)]
    if b in (0xC3,0xC2):
        n=1 if b==0xC3 else 3;p,k=va+n,0
        while p<T1 and data[TRAW+(p-T0)]==0x90 and k<16:k+=1;p+=1
        if k>=2:pad.add(p)
    if b==0xE8:
        rel=int.from_bytes(data[TRAW+(va+1-T0):TRAW+(va+5-T0)],"little",signed=True)
        t=(va+5+rel)&0xFFFFFFFF
        if T0<=t<T1:e8s.add(t)
ents=sorted(pad|e8s)
def fn(a):
    i=bisect.bisect_right(ents,a)-1;return ents[i] if i>=0 else T0
for s in sites:
    print("\n=== call @%08X in fn %08X: context [addr-0x40, addr+0x8) ===" % (s,fn(s)))
    for a,sz,mn,op in disasm(s-0x40,s+8):
        mark=">>>" if a==s else "   "
        print(" %s %08X  %-7s %s"%(mark,a,mn,op))
