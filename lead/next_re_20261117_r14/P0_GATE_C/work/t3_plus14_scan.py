# -*- coding: utf-8 -*-
"""U3: scan all [reg+0x14] byte accesses (write/read) across .text.
Classify by op.access; group by containing function; report write values."""
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
TEXT=[s for s in secs if s["name"]==".text"][0]; T0,T1=TEXT["va"],TEXT["va"]+TEXT["rawsize"]; TRAW=TEXT["raw"]
# fn boundaries
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
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
import capstone.x86_const as XC
# scan all [base+0x14] mem operands (disp exactly 0x14)
rows=[]
va=T0
while va<T1:
    got=list(md.disasm(data[TRAW+(va-T0):TRAW+(va-T0)+16],va,count=1))
    if not got: va+=1;continue
    i=got[0]
    try: ops=i.operands
    except: ops=[]
    for k,o in enumerate(ops):
        if o.type==X86_OP_MEM and o.mem.disp==0x14 and o.mem.base!=0:
            is_wr=bool(o.access & CS_AC_WRITE)
            rows.append(dict(addr=i.address,mn=i.mnemonic,opstr=i.op_str,
                rw="WRITE" if is_wr else "read",access=o.access,size=o.size,opidx=k,fn=fn(i.address),
                base=o.mem.base, index=o.mem.index))
    va+=i.size
print("total [reg+0x14] mem-operand refs: %d" % len(rows))
wr=[r for r in rows if r["rw"]=="WRITE"]; rd_=[r for r in rows if r["rw"]=="read"]
print("writes=%d reads=%d" % (len(wr),len(rd_)))
# byte writes only
print("\n=== BYTE writes to [reg+0x14] (size=1) ===")
bw=[r for r in wr if r["size"]==1]
for r in bw:
    print("  %08X  %-7s %-30s fn=%08X" % (r["addr"],r["mn"],r["opstr"],r["fn"]))
print("byte write count: %d" % len(bw))
print("\n=== OTHER writes (size!=1) ===")
for r in wr:
    if r["size"]!=1:
        print("  %08X  %-7s %-30s sz=%d fn=%08X" % (r["addr"],r["mn"],r["opstr"],r["size"],r["fn"]))
print("\n=== byte READS count and by function (top 30) ===")
br=[r for r in rd_ if r["size"]==1]
print("byte reads: %d" % len(br))
from collections import Counter
fc=Counter(r["fn"] for r in br)
for f,c in fc.most_common(30): print("  fn %08X: %d" % (f,c))
print("\n=== all byte reads with 'and' nearby (the filter pattern) ===")
for r in br:
    if r["mn"] in ("and","test","cmp","movzx"):
        print("  %08X  %-7s %-30s fn=%08X" % (r["addr"],r["mn"],r["opstr"],r["fn"]))
