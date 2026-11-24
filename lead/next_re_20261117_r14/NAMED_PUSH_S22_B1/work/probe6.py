# -*- coding: utf-8 -*-
import os,sys,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

def contain(va):
    return C.find_containing_atlas_func(va)

# 工厂 ctor 调用者所在函数
for c in ['006BC5D6','006BC613','006BC650','006BC68D','006BC6CA','006BC707','006BC744','006BC781','006BC7BE','006BC7FB','006BC838','006BC875','006BC8B2','006BC8EF','006BC92C','006BC969']:
    f=contain(int(c,16))
    print("caller",c,"in_func",f, "atexit", C.is_atexit_registered(int(f[1],16)) if f else None)

print("\n### 调用者所在函数体 (0x6BC5xx 附近) ###")
f=contain(0x6BC5D6)
fv=int(f[1],16); fs=f[2]
for ins in R.disasm_body(fv,fs):
    if ins.id==0: continue
    print("  %08X %-22s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic+' '+ins.op_str))
