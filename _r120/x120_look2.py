from capstone import Cs,CS_ARCH_X86,CS_MODE_32
P='ra2bench/gamemd.exe'; d=open(P,'rb').read(); IB=0x400000
md=Cs(CS_ARCH_X86,CS_MODE_32)
def show(va,n=0x80,label=''):
    o=0x1000+(va-IB-0x1000)
    print('==== %s @ %08x'%(label,va))
    for i in md.disasm(d[o:o+n],va):
        print('  %08x  %-24s %s'%(i.address,i.bytes.hex(),i.mnemonic+' '+i.op_str))
show(0x67d2a0,0xa0,'pre 0x67d36e')
