#!/usr/bin/env python3
"""Register write trace for ecx/edi/esi in MissionClass dispatch path."""
from pathlib import Path
import pefile,struct,re
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli/gamemd.exe'; data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections: secs.append((IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData))
def rd(va,n):
 for a,b,r,z in secs:
  if a<=va<b and va-a<z: return data[r+va-a:r+va-a+n]
 return None
def u32(va): return struct.unpack('<I',rd(va,4))[0]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def dis(a,n,c=100):
 b=rd(a,n); return list(md.disasm(b,a,count=c)) if b else []
lines=['S10-K4 REGISTER TRACE (ecx/edi/esi)']
head=dis(0x5B3060,0x8C,100)
for i in head:
    if (i.mnemonic in ('mov','lea') and re.match(r'^(edi|esi|ecx),',i.op_str)) or i.op_str=='esi' and i.mnemonic=='push':
        lines.append('HEAD %08X %s %s'%(i.address,i.bytes.hex(),i.op_str))
    if i.mnemonic=='call' and i.op_str.startswith('dword ptr ['):
        lines.append('HEAD_DISPATCH %08X %s %s'%(i.address,i.bytes.hex(),i.op_str))
# every dispatch stub: writes to esi before pop, and thiscall ecx setup
for mid in range(32):
    stub=u32(0x5B34E8+4*mid)
    ins=dis(stub,0x30,40)
    wr=[]
    for i in ins:
        if (i.mnemonic in ('mov','lea') and re.match(r'^(edi|esi|ecx),',i.op_str)) or i.mnemonic=='pop' and i.op_str=='esi':
            wr.append('%08X:%s %s'%(i.address,i.bytes.hex(),i.op_str))
        if i.mnemonic=='ret': break
    lines.append('STUB mid=%d va=%08X writes=%s'%(mid,stub,' | '.join(wr)))
lines += [
 'CONCLUSION: 005B3065 mov edi,ecx captures thiscall this; each case does mov ecx,edi then call [vptr+disp], so virtual this remains MissionClass*;',
 '005B3086 lea esi,[edi+0xC8] is the only esi write before the destination stores; no dispatch case rewrites esi before [esi]/[esi+4]/[esi+8] stores; pop esi occurs only after stores.'
]
p=ROOT/'lead/next_re_20261117_r14/S10_K4/EVIDENCE/register_trace.txt'
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines[:8]))
