# -*- coding: utf-8 -*-
"""U3: find all bit-0-setting writes to [reg+0x14] and trace ctor chain of InfantryClass."""
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
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
# scan for byte writes to [base+0x14] where value sets bit0
bit0_writes=[]
va=T0
while va<T1:
    got=list(md.disasm(data[TRAW+(va-T0):TRAW+(va-T0)+16],va,count=1))
    if not got: va+=1;continue
    i=got[0]
    try: ops=i.operands
    except: ops=[]
    if ops and ops[0].type==X86_OP_MEM and ops[0].mem.disp==0x14 and ops[0].access & CS_AC_WRITE and ops[0].size==1 and ops[0].mem.base!=0:
        # check if this instr sets bit0: mov ...,1 / or ...,1 / (any reg val to be checked later)
        sets_bit0=False
        if i.mnemonic in ('mov','or') and len(ops)>=2 and ops[1].type==X86_OP_IMM and (ops[1].imm & 1):
            sets_bit0=True
        if sets_bit0:
            bit0_writes.append((i.address,i.mnemonic,i.op_str,fn(i.address)))
    va+=i.size
print("=== direct byte writes setting bit0 of [reg+0x14] (mov/or with imm&1) ===")
for a,mn,op,f in bit0_writes:
    print("  %08X  %-6s %-34s fn=%08X" % (a,mn,op,f))
print("count:",len(bit0_writes))

# recursive constructor chain from 0x517A50: first call in first 0x20 bytes
def first_calls(f,span=0x30):
    out=[]
    va=f
    while va<f+span:
        got=list(md.disasm(rd(va,16),va,count=1))
        if not got: va+=1;continue
        i=got[0]
        if i.mnemonic=='call' and i.op_str.startswith('0x'):
            try: out.append(int(i.op_str,16))
            except: pass
        va+=i.size
    return out
print("\n=== constructor chain BFS from InfantryClass 0x517A50 (first 0x30 calls) ===")
seen=set(); stack=[0x517A50]; depth={0x517A50:0}
while stack and len(seen)<30:
    f=stack.pop(0)
    if f in seen: continue
    seen.add(f)
    calls=[c for c in first_calls(f) if T0<=c<T1]
    print("  ctor %08X d=%d -> first calls: %s" % (f,depth[f]," ".join("%08X"%c for c in calls)))
    for c in calls:
        if c not in seen and depth[f]<4:
            depth[c]=depth[f]+1; stack.append(c)
# which of these functions write bit0
print("\n=== which ctor-chain fns are in bit0_writes ===")
for a,mn,op,f in bit0_writes:
    if f in seen: print("  HIT: %08X %s in fn %08X d=%d" % (a,mn,op,f,depth[f]))
