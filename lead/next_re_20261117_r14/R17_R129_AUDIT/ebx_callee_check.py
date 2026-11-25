#!/usr/bin/env python3
# R129 auditor: for each direct call target on the path 0x6bd6c2..0x6bd945,
# linear-scan from the entry until the first ret and report whether ebx is
# written, and whether it was saved first (push ebx before any write).
import re
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
IB=0x400000
pe=pefile.PE(EXE,fast_load=False)
D=bytes(pe.__data__)
def roff(va):
    rva=va-IB
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            if rva-s.VirtualAddress<s.SizeOfRawData: return s.PointerToRawData+rva-s.VirtualAddress
    return None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def body(fn,maxlen=0x800):
    data=D[roff(fn):roff(fn)+maxlen]
    for a,sz,m,op in md.disasm_lite(data,fn):
        yield a,m,op
def audit(fn):
    saved=False; writes=[]; rets=[]
    for a,m,op in body(fn):
        if m=='push' and op=='ebx': saved=True
        elif m=='pop' and op=='ebx': return saved,writes,('pop',hex(a))
        elif m=='ret': return saved,writes,('ret',hex(a))
        else:
            # destination is the first operand when it is a register
            dst=op.split(',')[0].strip()
            if m in ('mov','xor','lea','add','sub','inc','dec','and','or','shl','shr','imul','not','neg','xchg','movzx','movsx') and dst in ('ebx',):
                writes.append((hex(a),m+' '+op,'saved' if saved else 'UNSAVED'))
    return saved,writes,('no-ret',None)
targets=[0x734e60,0x734fe0,0x4068e0,0x65c250,0x535aa0,0x525a10,0x52a670,0x5256f0,0x65c2a0,0x4790b0,0x7c8e17,0x5b3c20,0x7c978a,0x7b84f0,0x7346a0,0x4a3bf0,0x4aecd0,0x7ca564,0x7cbddc]
bad=0
for fn in sorted(set(targets)):
    saved,writes,term=audit(fn)
    flag='' 
    uns=[w for w in writes if w[2]=='UNSAVED']
    if uns or not saved and writes: flag='  <-- CLOBBERS EBX UNSAVED'; bad+=1
    print('0x%08x saved=%s writes=%d %s term=%s%s'%(fn,saved,len(writes),writes[:3],term,flag))
print('callees with unsaved ebx writes:',bad)
