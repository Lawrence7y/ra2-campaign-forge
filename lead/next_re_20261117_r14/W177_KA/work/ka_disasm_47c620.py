#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-KA 独立静态反汇编 0x47C620 —— 不依赖 branch_recompute.py / P0_GATE_B 文本。
用 pefile 定位 .text，capstone(skipdata=True) 从函数入口顺序解码，打印全量。
"""
import os, pefile, capstone, hashlib

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177_KA\EVIDENCE\ka_47c620_disasm.txt"
P = []
def p(s=''):
    P.append(str(s)); print(s)
p('EXE=' + EXE)
p('SHA256=' + hashlib.sha256(open(EXE,'rb').read()).hexdigest().upper())
pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
p('ImageBase=0x%X' % IB)
sec = None
for s in pe.sections:
    va = IB + s.VirtualAddress
    if va <= 0x47C620 < va + s.Misc_VirtualSize:
        sec = s; break
assert sec is not None
base = IB + sec.VirtualAddress
off = sec.PointerToRawData + (0x47C620 - base)
data = open(EXE,'rb').read()[off: off + 0x700]
p('.text VA=0x%X raw_off=0x%X slice=0x47C620..0x47CD20 (%d bytes)' % (base, off, len(data)))
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
md.detail = True
for ins in md.disasm(data, 0x47C620):
    p('  0x%08X  %-24s %s %s' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    if ins.address >= 0x47CD10: break
# call site slices
for start, end, label in [(0x43F2A0,0x43F2C0,'callsite 0x43F2AE (place loop)'), (0x449470,0x449490,'callsite 0x449482 (canplace query)'), (0x47C3F0,0x47C420,'0x47C3D0 selector')]:
    off2 = sec.PointerToRawData + (start - base)
    d2 = open(EXE,'rb').read()[off2: off2 + (end-start)]
    p('\n===== %s =====' % label)
    for ins in md.disasm(d2, start):
        p('  0x%08X  %-24s %s %s' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT,'w',encoding='utf-8').write('\n'.join(P)+'\n')
print('saved', OUT)
