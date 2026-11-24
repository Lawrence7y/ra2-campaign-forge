import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from core import *
def show(va,cap,lbl):
    print('\n== %s %s ==' % (lbl, hx(va)))
    for i in dis(va, read_va(va,cap)):
        if i.id==0: break
        print('   %s %-14s %s' % (hx(i.address), i.bytes.hex(), i.mnemonic+' '+i.op_str))
        if i.id==X86_INS_RET:
            nx=read_va(i.address+i.size,1)
            if nx[:1] in (b'\xcc',b'\x90',b''): break
show(0x0045AEA0, 0x90, 'callee of row1/7/16 site1')
show(0x004D0490, 0x90, 'callee of row9 site1')
show(0x0065AD30, 0x100, 'callee of row12 site2')
