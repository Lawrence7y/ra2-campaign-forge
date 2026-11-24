"""Dump exact disassembly of allocation sites + operator new + abstract stubs."""
import pefile, struct, os
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
ROOT=os.path.join('D:',os.sep,'Project','ra2-campaign-forge')
P=os.path.join(ROOT,'ra2youli','gamemd.exe')
pe=pefile.PE(P); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in pe.sections:
    SECS.append((s.Name.rstrip(b'\0').decode(),s.VirtualAddress+IB,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData))
DATA=open(P,'rb').read()
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.skipdata=True
def off(va):
    for n,vb,vs,pr,rs in SECS:
        if vb<=va<vb+max(vs,rs):
            d=va-vb
            if d<rs: return pr+d
    return None
def dis(va,n=16):
    o=off(va)
    print('--- @%08X ---'%va)
    for ins in MD.disasm(DATA[o:o+96],va):
        print('  %08X  %-20s %s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
        n-=1
        if n<=0: break

print('=== operator new 0x7C8E17 ===')
dis(0x7C8E17,10)
print('=== abstract stub 0x4C9150 ===')
dis(0x4C9150,4)
for va,nm in [(0x44FAF8,'Building push720'),(0x449E16,'Unit push8E8'),
              (0x4430C2,'Infantry push6F0'),(0x41B1B4,'Aircraft push6D8')]:
    print('=== %s @%08X ==='%(nm,va))
    dis(va,9)
