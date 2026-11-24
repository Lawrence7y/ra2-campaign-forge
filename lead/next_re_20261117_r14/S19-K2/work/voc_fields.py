#!/usr/bin/env python3
"""Broader audio RTTI string search + VocClass field write/read scan in known audio methods."""
import os,re,struct,csv
import pefile
from capstone import *
from capstone.x86 import *
ROOT=r'D:\Project\ra2-campaign-forge'; EXE=os.path.join(ROOT,r'ra2youli\gamemd.exe')
pe=pefile.PE(EXE,fast_load=False); IB=pe.OPTIONAL_HEADER.ImageBase; data=open(EXE,'rb').read()
# broad ASCII search anywhere in image
print('=== broad ASCII audio class-name-ish strings in file ===')
for pat in [rb'\.?AV[A-Za-z0-9_@$?]*Voc[A-Za-z0-9_@$?]*@@',rb'\.?AV[A-Za-z0-9_@$?]*Audio[A-Za-z0-9_@$?]*@@',
            rb'\.?AV[A-Za-z0-9_@$?]*Wave[A-Za-z0-9_@$?]*@@',rb'\.?AV[A-Za-z0-9_@$?]*Theme[A-Za-z0-9_@$?]*@@',
            rb'\.?AV[A-Za-z0-9_@$?]*Sound[A-Za-z0-9_@$?]*@@',rb'\.?AV[A-Za-z0-9_@$?]*Vox[A-Za-z0-9_@$?]*@@',
            rb'\.?AV[A-Za-z0-9_@$?]*Music[A-Za-z0-9_@$?]*@@']:
    hits=[m.group(0).decode('ascii','replace') for m in re.finditer(pat,data)]
    print(f'  {pat.decode(errors="replace")}: {sorted(set(hits))}')

# VocClass methods (anchored by F1 audit, verified independently here by offset fingerprints)
methods={
 0x4063B0:'ctor',0x406540:'set_Limit',0x406570:'set_Control',0x4065C0:'set_Type',
 0x4065D0:'set_Priority',0x4065E0:'set_Range',0x4065F0:'set_MinVolume',0x406600:'set_Delay',
 0x4041D0:'reader1',0x405190:'VoiceAlloc',0x7514D0:'FindIndex',0x752DB0:'LoadFromINI',
}
atlas={}
with open(os.path.join(ROOT,r'lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'),encoding='utf-8') as f:
    for row in csv.DictReader(f,delimiter='\t'): atlas[int(row['entry'],16)]=int(row['size'])
md=Cs(CS_ARCH_X86,CS_MODE_32);md.skipdata=True;md.detail=True
# collect per-offset accesses
from collections import defaultdict
writes=defaultdict(list); reads=defaultdict(list)
for va,lbl in methods.items():
    sz=atlas.get(va)
    if sz is None:
        # get from next atlas entry
        continue
    raw=data[va-IB:va-IB+sz]
    for ins in md.disasm(raw,va):
        for i,op in enumerate(ins.operands):
            if op.type!=X86_OP_MEM: continue
            disp=op.mem.disp
            if 0<=disp<0x148 and op.mem.base!=0:  # [reg+disp] data access
                if ins.id in (X86_INS_MOV,X86_INS_MOVSX,X86_INS_MOVZX,X86_INS_ADD,X86_INS_SUB,X86_INS_AND,X86_INS_OR,X86_INS_INC,X86_INS_DEC) and i==0:
                    writes[disp].append((va,lbl,ins.address,ins.mnemonic,ins.op_str))
                else:
                    reads[disp].append((va,lbl,ins.address,ins.mnemonic,ins.op_str))
print()
print('=== VocClass field offsets: W=write sites, R=read sites (in anchored audio methods) ===')
print(f'{"off":>6} {"W":>3} {"R":>3}  Wsample / Rsample')
for off in sorted(set(writes)|set(reads)):
    w=writes[off];r=reads[off]
    ws='; '.join(f'{a:X}({l}) {m} {o}' for _,l,a,m,o in w[:2])
    rs='; '.join(f'{a:X}({l}) {m} {o}' for _,l,a,m,o in r[:2])
    print(f'0x{off:04X} {len(w):>3} {len(r):>3}  W[{ws}]  R[{rs}]')
