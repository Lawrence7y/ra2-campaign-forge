from capstone import Cs,CS_ARCH_X86,CS_MODE_32
P='ra2bench/gamemd.exe'; d=open(P,'rb').read(); IB=0x400000
md=Cs(CS_ARCH_X86,CS_MODE_32)
def show(va,n,label=''):
    o=0x1000+(va-IB-0x1000)
    print('==== %s @ %08x..%08x'%(label,va,va+n))
    for i in md.disasm(d[o:o+n],va):
        print('  %08x  %-24s %s'%(i.address,i.bytes.hex(),i.mnemonic+' '+i.op_str))
show(0x67fdf0,0x120,'0x67fe31 stride region head')
