# -*- coding: utf-8 -*-
import io, os, sys
import capstone
HERE=os.path.dirname(os.path.abspath(__file__)); R14=os.path.dirname(HERE)
ROOT=os.path.dirname(os.path.dirname(R14)); EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
PROBE=os.path.join(R14,"R16_PROBE_4FINAL"); sys.path.insert(0,PROBE); sys.dont_write_bytecode=True
import final as F
IB=F.IMAGE_BASE; img=F.Image(EXE); buf=img.buf
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
out=[]
for tag,va,n in [("004741F0 host(decisive stacktemp)",0x004741F0,0x60),
                 ("00477760 wrapper(call 007BA590?)",0x00477760,0x45),
                 ("006CF0A8 (mov_abs region)",0x006CF0A8,0x40)]:
    out.append('=== %s @%08X ==='%(tag,va))
    o=va-IB
    for x in md.disasm(bytes(buf[o:o+n]),va):
        mk=''
        lo=x.op_str.lower()
        if '0x7c8b3d' in lo: mk+=' [DELETE]'
        if 'test' in x.mnemonic and '[esp' in lo: mk+=' [testesp]'
        if '0x7e4d90' in lo: mk+=' [VPTR]'
        if x.mnemonic in ('ret','retf'): mk+=' [RET]'
        out.append('  %08X: %-18s %s %s'%(x.address,x.bytes.hex(),'%s %s'%(x.mnemonic,x.op_str),mk))
    out.append('')
io.open(os.path.join(HERE,'verify_tricky.txt'),'w',encoding='utf-8').write('\n'.join(out))
print('ok')
