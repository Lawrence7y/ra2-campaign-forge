#!/usr/bin/env python3
# R129 auditor: relaxed-criterion counts.
#  (a) raw byte pattern c7 05 occurrences in .text vs decoded instruction starts
#  (b) every decoded instruction in .text whose imm32 operand lands on a validated
#      MSVC RTTI vtable head, grouped by mnemonic
# Streaming disasm_lite only, skipdata=True.
import re, struct, json
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
_cache={}
def is_vthead(imm):
    if imm in _cache: return _cache[imm]
    r=False
    if 0x7e1000<=imm<0x812000:
        col=None
        o=roff(imm-4)
        if o is not None: col=struct.unpack_from('<I',D,o)[0]
        if col is not None:
            oc=roff(col)
            if oc is not None:
                sig,offc,cd,ptd,pchd=struct.unpack_from('<IIIII',D,oc)
                if sig==0 and offc==0 and cd==0:
                    op=roff(ptd+8)
                    if op is not None:
                        z=D.index(b'\0',op)
                        r=D[op:z].startswith(b'.?A')
    _cache[imm]=r
    return r

s=[x for x in pe.sections if x.Name.rstrip(b'\0')==b'.text'][0]
data=D[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]
base=IB+s.VirtualAddress
# (a)
raws=[]; i=0
while True:
    i=data.find(b'\xc7\x05',i)
    if i<0: break
    tg=struct.unpack_from('<I',data,i+2)[0]; imm=struct.unpack_from('<I',data,i+6)[0]
    raws.append((base+i,tg,imm)); i+=1
# (b)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
movabs=[]; anyimm=[]
for a,sz,m,op in md.disasm_lite(data,base):
    for tok in re.findall(r'0x[0-9a-f]{5,8}',op):
        v=int(tok,16)
        if is_vthead(v):
            anyimm.append((a,m,op,v)); break
    if m=='mov' and op.startswith('dword ptr ['):
        mm=re.match(r'^dword ptr \[(0x[0-9a-f]+)\], (0x[0-9a-f]+)$',op)
        if mm: movabs.append((a,int(mm.group(1),16),int(mm.group(2),16)))
print('(a) raw byte c7 05 in .text:',len(raws))
dec_starts={a for a,t,mm in movabs}
print('    of which are real decoded instruction starts (mov [abs],imm32):',sum(1 for a,t,mm in raws if a in dec_starts))
print('    of which are mid-instruction byte coincidences:',len(raws)-sum(1 for a,t,mm in raws if a in dec_starts))
print('    raw hits whose imm is a validated vtable head:',sum(1 for a,t,mm in raws if is_vthead(mm)))
print('    raw hits whose imm is a validated vtable head AND target==0xa8e8c8:',
      [('0x%08x'%a,'imm 0x%08x'%mm) for a,t,mm in raws if t==0xa8e8c8])
print()
print('(b) decoded instructions in .text with an imm32 equal to any validated vtable head:',len(anyimm))
from collections import Counter
print('    by mnemonic:',dict(Counter(m for a,m,op,v in anyimm)))
print('    of which are the mov-dword-ptr-abs form:',sum(1 for a,m,op,v in anyimm if m=='mov' and op.startswith('dword ptr [')))
print('    distinct vtable heads referenced:',len(set(v for a,m,op,v in anyimm)))
print('    extreme restatement: distinct mov [abs],imm32 sites regardless of imm:',len(movabs))
print('    distinct target addresses among those:',len(set(t for a,t,mm in movabs)))
json.dump([(a,m,op,v) for a,m,op,v in anyimm],open('/tmp/r129_anyimm.json','w'))
