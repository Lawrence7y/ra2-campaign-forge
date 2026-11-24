import struct,sys
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
P='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
d=open(P,'rb').read()
IB=0x400000; TRAW=0x1000
md=Cs(CS_ARCH_X86,CS_MODE_32)
def show(va,n=0x60,label=''):
    o=TRAW+(va-IB-0x1000)
    print('==== %s @ %08x'%(label,va))
    for i in md.disasm(d[o:o+n],va):
        print('  %08x  %-22s %s'%(i.address,i.bytes.hex(),i.mnemonic+' '+i.op_str))
show(0x67d320,0x90,'around first site 0x67d36e')
show(0x67ddf0,0x60,'last of 0x7f block 0x67ddf5')
show(0x4af7d0,0x50,'0x4af7df site')
