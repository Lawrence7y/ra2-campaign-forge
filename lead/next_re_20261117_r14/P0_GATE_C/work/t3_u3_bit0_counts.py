# -*- coding: utf-8 -*-
"""Final precise count: [reg+0x14] byte writes excluding stack slot, by value class."""
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
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
rows=[]
va=T0
while va<T1:
    got=list(md.disasm(data[TRAW+(va-T0):TRAW+(va-T0)+16],va,count=1))
    if not got: va+=1;continue
    i=got[0]
    try: ops=i.operands
    except: ops=[]
    for k,o in enumerate(ops):
        if o.type==X86_OP_MEM and o.mem.disp==0x14 and o.size==1 and (o.access & CS_AC_WRITE):
            base=o.mem.base
            # skip stack base ESP (X86_REG_ESP=4) ; note ebp frame we keep but mark
            is_stack=(base==X86_REG_ESP)
            valtype="reg"
            bit0=None
            if len(ops)>=2:
                s=ops[1]
                if s.type==X86_OP_IMM:
                    valtype="imm:%d"%s.imm; bit0=s.imm&1
                elif s.type==X86_OP_MEM: valtype="mem"
                else: valtype="reg"
            rows.append(dict(addr=i.address,mn=i.mnemonic,opstr=i.op_str,base=base,
                             stack=is_stack,valtype=valtype,bit0=bit0))
    va+=i.size
print("=== [reg+0x14] byte WRITE points (capstone op.access, size=1) ===")
print("total:",len(rows))
nonstack=[r for r in rows if not r["stack"]]
print("non-ESP-base:",len(nonstack))
imm0=[r for r in nonstack if r["bit0"]==0]
imm1=[r for r in nonstack if r["bit0"]==1]
regv=[r for r in nonstack if r["bit0"] is None]
print("  imm with bit0=0 (direct clear):",len(imm0))
for r in imm0: print("    %08X %s %s"%(r["addr"],r["mn"],r["opstr"]))
print("  imm with bit0=1 (direct set):",len(imm1))
for r in imm1: print("    %08X %s %s"%(r["addr"],r["mn"],r["opstr"]))
print("  register/mem value writes (bit0 traced separately):",len(regv))
# find OR 1 pattern anywhere (op0 mem, mnemonic or)
print("\n=== 'or byte [reg+0x14],1' explicit pattern ===")
va=T0
orcnt=0
while va<T1:
    got=list(md.disasm(data[TRAW+(va-T0):TRAW+(va-T0)+16],va,count=1))
    if not got: va+=1;continue
    i=got[0]
    if i.mnemonic=='or':
        try: ops=i.operands
        except: ops=[]
        if len(ops)>=2 and ops[0].type==X86_OP_MEM and ops[0].mem.disp==0x14 and ops[0].size==1 and ops[1].type==X86_OP_IMM and ops[1].imm==1:
            print("  %08X %s %s"%(i.address,i.mnemonic,i.op_str)); orcnt+=1
    va+=i.size
print("count:",orcnt)
