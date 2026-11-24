from capstone import Cs,CS_ARCH_X86,CS_MODE_32
P='ra2bench/gamemd.exe'; d=open(P,'rb').read(); IB=0x400000
md=Cs(CS_ARCH_X86,CS_MODE_32)
def show(va,n,label=''):
    o=0x1000+(va-IB-0x1000)
    print('==== %s @ %08x'%(label,va))
    for i in md.disasm(d[o:o+n],va):
        print('  %08x  %-20s %s'%(i.address,i.bytes.hex(),i.mnemonic+' '+i.op_str))
show(0x4af530,0x60,'Q3 site1 fn head 0x4af540')
show(0x4af770,0x30,'C2 wrong boundary 0x4af77d')
show(0x4af7c0,0x60,'Q3 site1 body')
