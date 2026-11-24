# -*- coding: utf-8 -*-
"""Trace callers of 0x45DD90 / 0x45FE95 and identify class via caller vtable RTTI."""
import struct, pefile, hashlib, bisect
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
TEXT=[s for s in secs if s["name"]==".text"][0]; T0,T1=TEXT["va"],TEXT["va"]+TEXT["rawsize"]
TRAW=TEXT["raw"]
def callers_of(target):
    out=[]
    for va in range(T0,T1-5):
        if data[TRAW+(va-T0)]==0xE8:
            rel=int.from_bytes(data[TRAW+(va+1-T0):TRAW+(va+5-T0)],"little",signed=True)
            if (va+5+rel)&0xFFFFFFFF==target: out.append(va)
    return out
pad=set([T0]); e8s=set()
for va in range(T0,T1-5):
    b=data[TRAW+(va-T0)]
    if b==0xC3 or b==0xC2:
        n=1 if b==0xC3 else 3; p,k=va+n,0
        while p<T1 and data[TRAW+(p-T0)]==0x90 and k<16: k+=1;p+=1
        if k>=2: pad.add(p)
    if b==0xE8:
        rel=int.from_bytes(data[TRAW+(va+1-T0):TRAW+(va+5-T0)],"little",signed=True)
        t=(va+5+rel)&0xFFFFFFFF
        if T0<=t<T1: e8s.add(t)
ents=sorted(pad|e8s)
def fn(a):
    i=bisect.bisect_right(ents,a)-1; return ents[i] if i>=0 else T0
def col_class(colva):
    if u32(colva) not in (0,1): return None
    td=u32(colva+0xC)
    if td is None: return None
    b=rd(td+8,64); z=b.find(b"\x00")
    if z==-1: return None
    nm=b[:z].decode("latin1")
    return nm if nm.startswith(".?A") else None
def class_of_fn(f):
    pat=struct.pack("<I",f); out=[]
    for s in secs:
        if s["name"] not in (".rdata",".data"): continue
        blob=data[s["raw"]:s["raw"]+s["rawsize"]]; i=blob.find(pat)
        while i!=-1:
            if i%4==0:
                slot=s["va"]+i
                for back in range(0,0x200,4):
                    vb=slot-back; col=u32(vb-4)
                    if col is None: continue
                    nm=col_class(col)
                    if nm: out.append((slot,vb,col,nm,back//4)); break
            i=blob.find(pat,i+1)
    return out
for tgt in [0x45DD90,0x45FE95]:
    cs=callers_of(tgt)
    print("\n=== callers of %08X : %d ===" % (tgt,len(cs)))
    for c in cs:
        f=fn(c); ci=class_of_fn(f)
        print("  call@%08X in fn %08X class=%s" % (c,f,ci[:3] if ci else "UNRESOLVED"))
    print("  TARGET %08X vtable class: %s" % (tgt,class_of_fn(tgt) or "UNRESOLVED"))
