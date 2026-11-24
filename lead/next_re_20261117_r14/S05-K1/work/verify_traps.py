"""Verify the two known-trap sites named in the card:
1) 0x6D98EF mov byte [esi+0x80],0  (write value = 0, NOT 1)
2) 0x636590 / 0x695BC0 mov [ebp+0x94],* where ebp=this (not stack slot)
Print exact disassembly with ecx/ebp provenance.
"""
import pefile, os
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
ROOT=os.path.join('D:',os.sep,'Project','ra2-campaign-forge')
P=os.path.join(ROOT,'ra2youli','gamemd.exe')
pe=pefile.PE(P); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.rstrip(b'\0').decode(),s.VirtualAddress+IB,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
DATA=open(P,'rb').read()
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.skipdata=True
def off(va):
    for n,vb,vs,pr,rs in SECS:
        if vb<=va<vb+max(vs,rs):
            d=va-vb
            if d<rs: return pr+d
    return None
def dis(va,n=12,label=''):
    print('--- %s @%08X ---'%(label,va))
    o=off(va)
    for ins in MD.disasm(DATA[o:o+80],va):
        print('  %08X %-20s %s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
        n-=1
        if n<=0: break
# site 1
dis(0x6D98E0,16,'trap +0x80 0x6D98EF region')
# site 2 - scan around 0x636590 and 0x695BC0 for [ebp+0x94]
for base,nm in [(0x636590,'0x636590 region'),(0x695BC0,'0x695BC0 region')]:
    dis(base-0x20,20,nm)
