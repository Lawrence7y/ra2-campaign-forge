# -*- coding: utf-8 -*-
# 独立复核：0x414A80 / 0x414AE5 是否同一函数；PASS2 跨 C3-ret 的归属是否成立
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
d = open(EXE, 'rb').read()
def off(va): return va - 0x400000
md = Cs(CS_ARCH_X86, CS_MODE_32)

print('=== 0x414A80 .. 0x414B40 全解码 ===')
for ins in md.disasm(d[off(0x414A80):off(0x414B40)], 0x414A80):
    print('  %08x  %-8s %s' % (ins.address, ins.mnemonic, ins.op_str))

# 全 .text 中对 0x414AE5 / 0x414A80 的 E8/E9 直调者
print('\n=== 全 .text 直接引用（E8/E9 rel32）到两个候选起点 ===')
import re
text = d[off(0x401000):off(0x401000)+0x3df000]
def callers_to(target):
    out=[]
    for i in range(len(text)-5):
        if text[i] in (0xE8,0xE9):
            rel=struct.unpack_from('<i',text,i+1)[0]
            va=0x401000+i
            if (va+5+rel)&0xFFFFFFFF==target:
                out.append((va,hex(text[i])))
    return out
for t in (0x414A80,0x414AE5,0x414B24,0x416D50,0x4166C0):
    print('  target 0x%X : E8/E9 callers %s' % (t, [(hex(a),k) for a,k in callers_to(t)][:12]))

# .rdata/.data dword 引用
print('\n=== .rdata/.data 中等于候选起点的 dword 位置 ===')
for t in (0x414A80,0x414AE5,0x416D50,0x4166C0):
    pat=struct.pack('<I',t)
    pos=[]
    for sec_va,sec_sz in ((0x7E1000,0x31000),(0x812000,0x6c000)):
        base=off(sec_va)
        s=d[base:base+sec_sz]
        st=0
        while True:
            j=s.find(pat,st)
            if j<0: break
            pos.append(hex(sec_va+j)); st=j+1
    print('  0x%X -> %s' % (t,pos[:12]))

print('\n=== 0x414AE4 处字节 + 后继 ===')
print('  bytes@0x414AE0:', d[off(0x414AE0):off(0x414AF0)].hex(' '))
print('  bytes@0x414A78 (0x414A80 前置填充):', d[off(0x414A78):off(0x414A84)].hex(' '))

print('\nDONE')
