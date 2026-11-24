#!/usr/bin/env python3
"""S10-K1: full disasm of FootClass::AI 0x4DA530; mark mission-field and indirect-call sites."""
import pefile, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE=r"ra2youli\gamemd.exe"
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
data=open(EXE,'rb').read()
secs=[]
for s in pe.sections:
    secs.append((s.Name.decode(errors='replace').rstrip('\x00'), IB+s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
def va2off(va):
    for n,v,vs,r,rs in secs:
        if v<=va<v+max(vs,rs): return r+(va-v)
    return None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
start=0x4DA530
o=va2off(start)
code=data[o:o+0x1100]
lines=[]
for ins in md.disasm(code,start):
    mark=''
    if re.search(r'\[\w+\s*\+\s*0xAC\]',ins.op_str): mark+=' <== MISSION'
    if re.search(r'\[\w+\s*\+\s*0xB4\]',ins.op_str): mark+=' <== QUEUED'
    if ins.mnemonic in ('call','jmp') and 'dword ptr [' in ins.op_str:
        m=re.search(r'\+\s*(0x[0-9a-f]+)',ins.op_str)
        if m:
            off=int(m.group(1),16)
            mark+=' <== INDIR +0x%X slot %d'%(off,off//4)
    lines.append("0x%08X: %-26s %s %s%s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str,mark))
    if ins.mnemonic.startswith('ret') and ins.address>start+0x800: break
print('\n'.join(lines))
print("TOTAL LINES:",len(lines))
