# -*- coding: utf-8 -*-
"""R216 m4：①170DAC82 的符号/字符串归属；②0x410230 尾部分支 0x410246 起；
③0x7c8b3d 是否 operator delete；④四个 IID GUID 字符串在 .rdata 是否另有 text 形式。"""
import sys,struct,json,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import *
mdl=Cs(CS_ARCH_X86,CS_MODE_32)
def o(va): return P.r2o(va)
print('=== 0x410230 完整（含尾部）0x410230..0x410260 ===')
for i in mdl.disasm(P.RAW[o(0x410230):o(0x410230)+0x30],0x410230):
    print('  %08x  %-8s %s'%(i.address,i.mnemonic,i.op_str))
print('  raw=%s'%P.RAW[o(0x410230):o(0x410230)+0x30].hex())
print('=== 0x7c8b3d 起 40 字节 ===')
for i in mdl.disasm(P.RAW[o(0x7c8b3d):o(0x7c8b3d)+0x40],0x7c8b3d):
    print('  %08x  %-8s %s'%(i.address,i.mnemonic,i.op_str))
    if i.mnemonic.startswith('ret'): break
print('=== 0x7f7c70/persist 视图交叉：0x7f7c60..0x7f7ca0 字节 ===')
print(P.RAW[o(0x7f7c60):o(0x7f7ca0)].hex())
print('=== 符号表中 170DAC82 相关 ===')
import subprocess
raw=open('out/reverse/symbols.json','rb').read()
print('symbols.json bytes=%d'%len(raw))
for pat in (b'170DAC82',b'170dac82',b'PersistStream',b'IPersist',b'AbstractClass',b'IUnknown',b'QueryInterface'):
    print('  %-16s 出现=%d'%(pat.decode(),raw.count(pat)))
