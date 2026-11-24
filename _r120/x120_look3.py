from capstone import Cs,CS_ARCH_X86,CS_MODE_32
import re
P='ra2bench/gamemd.exe'; d=open(P,'rb').read(); IB=0x400000; TRAW=0x1000
md=Cs(CS_ARCH_X86,CS_MODE_32)
def show(va,n,label=''):
    o=0x1000+(va-IB-0x1000)
    print('==== %s @ %08x..%08x'%(label,va,va+n))
    for i in md.disasm(d[o:o+n],va):
        print('  %08x  %-26s %s'%(i.address,i.bytes.hex(),i.mnemonic+' '+i.op_str))
show(0x67d360,0x1a0,'sites 1-4 region')
text=d[TRAW:TRAW+0x3df38d]
# ret positions in region 0x67d300..0x681000
for m in re.finditer(rb'\xc3|\xc2..', text[0x67d300-0x401000:0x681000-0x401000]):
    pass
