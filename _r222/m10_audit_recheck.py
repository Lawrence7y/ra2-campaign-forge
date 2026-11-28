# -*- coding: utf-8 -*-
"""R222 m10：复算审计员 #582 的 4 条修正/口径（§2.12 规则 D，主会话亲自复算）。

A1 复核：0x7c6000..0x7c7000 内 mov ax, word ptr [esi] 与 lodsw 的条数（审计称皆 0）。
A2 复核：副本 2/3 的第二路径复用字段（审计称 0x7c62f5 / 0x7c63f5 / 0x7c6514 读 word[ebx+0x1c]/[ebx+0x30]）。
A3 复核：0x7c75cc 7 字节 = 5a 59 5b 5f 5e c9 c3（纯尾声）。
A4 复核：cx 既不 8 也不 0x10 时落点 0x7c73a8 -> 0x7c75cc；且该路径 eax 未被置值。
A5 复核：0x7c635b..0x7c635d 是否切在指令中间（审计称卡面终止地址有误）。
A6 复核：8 项表 0x7c7758 与 4 项表 0x7c7778 零间隙相邻；4 项表后 4 个 dword 是代码。
"""
import sys, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
fails = []


def ck(n, c, d=''):
    if not c:
        fails.append(n)
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))


def dis(lo, hi):
    o = P.r2o(lo)
    b = P.RAW[o:o + (hi - lo)]
    return [(i.address, i.bytes.hex(), i.mnemonic, i.op_str) for i in md.disasm(b, lo)]


s = dis(0x7c6000, 0x7c7000)
w16 = [(a, op) for a, b, mn, op in s if mn == 'mov' and op == 'ax, word ptr [esi]']
lod = [(a, mn) for a, b, mn, op in s if mn == 'lodsw']
ck('A1a 0x7c6000..0x7c7000 内 mov ax,word[esi] 0 条（审计 #582 修正成立）', w16 == [], w16)
ck('A1b 同区间 lodsw 0 条', lod == [], lod)

f1 = [(a, mn, op) for a, b, mn, op in s if mn == 'mov' and op in ('ax, word ptr [ebx + 0x1c]', 'ax, word ptr [ebx + 0x30]')]
ck('A2a 副本 2/3 复用字段 mov ax,word[ebx+0x1c]/[ebx+0x30] 至少 3 处',
   len(f1) >= 3, [(hex(a), op) for a, mn, op in f1])

tail = dis(0x7c75cc, 0x7c75d3)
ck('A3 0x7c75cc = 5a 59 5b 5f 5e c9 c3（pop edx/ecx/ebx/edi/esi; leave; ret）',
   ''.join(b for a, b, mn, op in tail) == '5a595b5f5ec9c3', ''.join(b for a, b, mn, op in tail))

d = [(a, mn, op) for a, b, mn, op in dis(0x7c73a0, 0x7c73c3)]
ck('A4a cx!=8 且 cx!=0x10 -> 0x7c73a8 jne 0x7c75cc',
   any(a == 0x7c73a8 and mn == 'jne' and op == '0x7c75cc' for a, mn, op in d), d[:4])
# 该路径上 eax 是否被置值：从 0x7c7371 到 0x7c73a8 之间有无写 eax
pre = [(a, mn, op) for a, b, mn, op in dis(0x7c7371, 0x7c73a9)]
wr = [(a, mn, op) for a, mn, op in pre if mn in ('mov', 'xor', 'lea', 'add', 'sub') and op.startswith('eax')]
ck('A4b 直达尾声中 eax 未被置值（返回值为调用方残留）', wr == [], wr)

mid = [(a, len(b) // 2, mn, op) for a, b, mn, op in dis(0x7c6356, 0x7c6360)]
ck('A5 0x7c635b mov eax,[ebx+0x14] 长 3 B，卡片终止地址 0x7c635d 确实切在指令中间',
   any(a == 0x7c635b and ln == 3 and mn == 'mov' for a, ln, mn, op in mid), mid)

ck('A6a 两表零间隙：0x7c7778 == 0x7c7758 + 0x20', 0x7c7778 == 0x7c7758 + 0x20)
head4 = [P.RAW[P.r2o(t):P.r2o(t) + 16].hex() for t in (0x7c7788, 0x7c77f0, 0x7c7f20)]
ck('A6b 4 项表后紧跟代码：0x7c7788=555333d2 / 0x7c77f0=03045530 / 0x7c7f20=558bec',
   head4[0].startswith('555333d2') and head4[1].startswith('03045530') and head4[2].startswith('558bec'), head4)

print()
print('FAIL 数 =', len(fails), fails)
if fails:
    raise SystemExit(1)
