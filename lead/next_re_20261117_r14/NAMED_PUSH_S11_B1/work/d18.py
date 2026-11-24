import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from core import *
def body(ea,cap=300):
    out=[]
    for i in dis(ea, read_va(ea,cap)):
        if i.id==0: break
        out.append(i)
        if i.id==X86_INS_RET:
            nx=read_va(i.address+i.size,1)
            if nx[:1] in (b'\xcc',b'\x90',b''): break
    return out
for ea,lbl in ((0x004AF610,'ROW1 Drive slot6'),(0x004CCB40,'ROW8 Fly slot16'),(0x006622C0,'ROW18 Rocket slot16')):
    print('\n===== %s %s =====' % (lbl,hx(ea)))
    for i in body(ea):
        print('   %s %-14s %s' % (hx(i.address), i.bytes.hex(), i.mnemonic+' '+i.op_str))
