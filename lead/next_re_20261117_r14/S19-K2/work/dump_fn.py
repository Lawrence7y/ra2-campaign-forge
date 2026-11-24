#!/usr/bin/env python3
"""Focused annotated disassembly for evidence verification."""
import os,re,sys,json,struct,csv
import pefile
from capstone import *
from capstone.x86 import *
ROOT=r'D:\Project\ra2-campaign-forge'; EXE=os.path.join(ROOT,r'ra2youli\gamemd.exe')
pe=pefile.PE(EXE,fast_load=False); IB=pe.OPTIONAL_HEADER.ImageBase; data=open(EXE,'rb').read()
iat={}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    dll=e.dll.decode('ascii','replace')
    for imp in e.imports:
        iat[imp.address]=dll+'!'+(imp.name.decode('ascii','replace') if imp.name else '#'+str(imp.ordinal))
if hasattr(pe,'DIRECTORY_ENTRY_DELAY_IMPORT'):
    for e in pe.DIRECTORY_ENTRY_DELAY_IMPORT:
        dll=e.dll.decode('ascii','replace')
        for imp in e.imports:
            iat[imp.address]=dll+'!'+(imp.name.decode('ascii','replace') if imp.name else '#'+str(imp.ordinal))
# name map from coverage
cov={}
with open(os.path.join(ROOT,r'lead\next_re_20261117_r14\COVERAGE\coverage.tsv'),encoding='utf-8') as f:
    for row in csv.DictReader(f,delimiter='\t'):
        cov[int(row['entry'],16)]=row['name']
def cstr(va,maxn=96):
    off=va-IB
    if off<0 or off>=len(data):return None
    b=data[off:off+maxn]; z=b.find(b'\0')
    if z<0:z=maxn
    s=b[:z]
    return s.decode('ascii','replace') if len(s)>=3 and all(32<=c<127 for c in s) else None
md=Cs(CS_ARCH_X86,CS_MODE_32);md.skipdata=True;md.detail=True
def dump(va,size=None):
    if size is None:
        # derive from atlas
        import bisect
        with open(os.path.join(ROOT,r'lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'),encoding='utf-8') as f:
            for row in csv.DictReader(f,delimiter='\t'):
                if int(row['entry'],16)==va: size=int(row['size']);break
    raw=data[va-IB:va-IB+size]
    print(f'\n===== fn 0x{va:X} size={size} name={cov.get(va,"?")} =====')
    for ins in md.disasm(raw,va):
        ann=''
        o=ins.op_str.strip()
        m=re.fullmatch(r'0x([0-9a-fA-F]+)',o)
        if ins.id in (X86_INS_CALL,X86_INS_JMP) and m:
            t=int(m.group(1),16)
            ann='; -> '+cov.get(t,'sub_%X'%t)
        m2=re.fullmatch(r'dword ptr \[0x([0-9a-fA-F]+)\]',o)
        if m2 and int(m2.group(1),16) in iat:
            ann='; IAT '+iat[int(m2.group(1),16)]
        for op in ins.operands if ins.id in (X86_INS_PUSH,X86_INS_MOV,X86_INS_LEA) else []:
            if op.type==X86_OP_IMM:
                s=cstr(op.imm&0xFFFFFFFF)
                if s: ann+=' ; STR "'+s+'" @0x%X'%(op.imm&0xFFFFFFFF)
        print(f'  {ins.address:08X}  {ins.bytes.hex():<20} {ins.mnemonic:<7} {o}{ann}')
if __name__=='__main__':
    args=sys.argv[1:]
    # parse pairs va:size or just va
    i=0
    while i<len(args):
        a=args[i]
        if ':' in a:
            va,sz=a.split(':'); dump(int(va,16),int(sz))
        else:
            dump(int(a,16))
        i+=1
