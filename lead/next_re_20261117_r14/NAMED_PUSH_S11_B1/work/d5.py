import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from core import *
for i in dis(0x004B62C0, read_va(0x004B62C0, 0xDA)):
    if i.id==0: break
    print('%s  %-14s %-40s' % (hx(i.address), i.bytes.hex(), i.mnemonic+' '+i.op_str))
