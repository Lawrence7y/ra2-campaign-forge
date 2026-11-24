#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify thiscall this-register for the 14 delta rows:
for each entry, find 'mov <reg>,ecx' in prologue (first 24 insns) and confirm
>=1 proven-field access uses that reg (or ecx directly)."""
import pefile, os, csv, json
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM
ROOT=r"D:\Project\ra2-campaign-forge"
P=os.path.join(ROOT,"ra2youli","gamemd.exe"); DELTA=os.path.join(ROOT,"lead","next_re_20261117_r14","S05-K2","coverage_delta.tsv")
pe=pefile.PE(P); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.rstrip(b"\0").decode(),s.VirtualAddress+IB,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
SM={s[0]:s for s in SECS}; T=SM[".text"]; D=open(P,"rb").read()
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.skipdata=True; MD.detail=True
PROVEN={0x10,0x20,0x74,0x80,0x81,0x94,0x21C,0x674}
def insns(va,n=200):
    o=T[3]+(va-T[1]); out=[]
    for i in MD.disasm(D[o:o+8000],va):
        out.append(i)
        if len(out)>=n: break
    return out
rows=list(csv.DictReader(open(DELTA,encoding="utf-8"),delimiter="\t"))
ok=0
for r in rows:
    va=int(r['entry'],16); ins=insns(va,200)
    thisreg='ecx'
    # find prologue mov reg,ecx within first 24 insns
    for i in ins[:24]:
        if i.mnemonic=='mov' and len(i.operands)==2:
            dst=i.operands[0]; src=i.operands[1]
            if src.type==1 and i.reg_name(src.reg)=='ecx' and dst.type==1:  # X86_OP_REG=1
                thisreg=i.reg_name(dst.reg); break
    # count proven-field accesses using thisreg
    cnt=0
    for i in ins:
        for op in i.operands:
            if op.type==X86_OP_MEM and op.mem.index==0 and int(op.mem.disp) in PROVEN:
                b=i.reg_name(op.mem.base) if op.mem.base else None
                if b==thisreg: cnt+=1
    print("%s %-28s thisreg=%-4s this-field-accesses=%d %s"%(r['entry'],r['name'][:28],thisreg,cnt,'OK' if cnt>=3 else 'CHECK'))
    if cnt>=3: ok+=1
print('verified >=3 this-field-accesses:',ok,'/',len(rows))
