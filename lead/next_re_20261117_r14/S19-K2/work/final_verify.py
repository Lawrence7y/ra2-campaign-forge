#!/usr/bin/env python3
"""Final verification: WaveClass push-0x240, PlayGlobal callees, BinkMovieLoop back-edges."""
import os,struct,re,csv
import pefile
from capstone import *
from capstone.x86 import *
ROOT=r'D:\Project\ra2-campaign-forge'; EXE=os.path.join(ROOT,r'ra2youli\gamemd.exe')
pe=pefile.PE(EXE,fast_load=False); IB=pe.OPTIONAL_HEADER.ImageBase; d=open(EXE,'rb').read()
def u32(va): return struct.unpack_from('<I',d,va-IB)[0]
# 1. push 0x240 (68 40 02 00 00) anywhere in .text
pat=bytes.fromhex('6840020000')
hits=[]; i=0
while True:
    j=d.find(pat,i,0x7E038D-IB)
    if j<0:break
    hits.append(IB+j); i=j+1
print('push 0x240 sites:',[hex(x) for x in hits])
# push 0x148 sites
pat2=bytes.fromhex('6848010000');h=[];i=0
while True:
    j=d.find(pat2,i,0x7E038D-IB)
    if j<0:break
    h.append(IB+j);i=j+1
print('push 0x148 sites:',[hex(x) for x in h])
# 2. PlayGlobal atlas size
import csv as c
with open(os.path.join(ROOT,r'lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'),encoding='utf-8') as f:
    for row in c.DictReader(f,delimiter='\t'):
        if int(row['entry'],16)==0x750920:
            print('PlayGlobal atlas:',row);break
# 3. BinkMovieLoop 0x432C70 back-edges to 0x432CB8
md=Cs(CS_ARCH_X86,CS_MODE_32);md.skipdata=True
raw=d[0x432C70-IB:0x432C70-IB+458]
back=[]
for ins in md.disasm(raw,0x432C70):
    o=ins.op_str.strip()
    m=re.fullmatch(r'0x([0-9a-fA-F]+)',o)
    if m and (ins.mnemonic in ('jmp','je','jne','jg','jge','jl','jle','ja','jae','jb','jbe','jz','jnz')):
        if int(m.group(1),16)==0x432CB8:
            back.append((ins.address,ins.mnemonic))
print('back-edges to 0x432CB8:',[(hex(a),m) for a,m in back])
