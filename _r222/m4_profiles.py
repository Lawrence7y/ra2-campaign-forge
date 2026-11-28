# -*- coding: utf-8 -*-
"""R222 m4: 四个解码循环体的写入位宽 / 指针步进 / 单体同构，以及编码器循环步进。

针对假设：
  H1 0x7c6808 是 16-bit mono 单展开体（edi+=0x10, esi+=4，每块写 1 word）
  H2 0x7c7428 是 0x7c7371 内的 16-bit mono 体（同上）
  H3 0x7c77f0 / 0x7c7bc0 是 16-bit stereo 双展开体（edi+=0x20, esi+=4，每块写 2 word）
  H4 编码器 0x7c62ac 内外两段展开体指针步进一致
反控：
  R1 把 stereo 体的每块写 word 数按 1 计（即假设 mono 化）时，edi 步进与块数应不自洽
  R2 把 0x7c6808 的 edi 步进读成 0x20 时不自洽
"""
import sys, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True


def dis(lo, hi):
    o = P.r2o(lo)
    buf = P.RAW[o:o + (hi - lo)]
    return [(i.address, i.bytes.hex(), i.mnemonic, i.op_str) for i in md.disasm(buf, lo)]


def profile(name, lo, hi, table_va):
    seq = dis(lo, hi)
    adds = [a for a, b, mn, op in seq if mn == 'add' and op == 'eax, dword ptr [edx*2 + 0x%x]' % table_va]
    stores = [(a, op) for a, b, mn, op in seq if mn == 'mov' and op.startswith('word ptr [edi')
              and op.rstrip().endswith(', ax')]
    adv_edi = [(a, op) for a, b, mn, op in seq if mn in ('add',) and op.startswith('edi,')]
    adv_esi = [(a, op) for a, b, mn, op in seq if mn == 'add' and op.startswith('esi,')]
    print('--- %s %08x..%08x ---' % (name, lo, hi))
    print('  add-count %d ; adds %s' % (len(adds), [hex(x) for x in adds]))
    print('  word stores to [edi..]: %d -> %s' % (len(stores), [(hex(a), o) for a, o in stores[:20]]))
    print('  add edi: %s ; add esi: %s' % ([(hex(a), o) for a, o in adv_edi], [(hex(a), o) for a, o in adv_esi]))
    print('  sub edi: %s' % [(hex(a), op) for a, b, mn, op in seq if mn == 'sub' and op.startswith('edi,')])
    print('  sub esi: %s' % [(hex(a), op) for a, b, mn, op in seq if mn == 'sub' and op.startswith('esi,')])
    return seq


print('===== H1 0x7c6808 (block1 表) =====')
profile('dec6808', 0x7c6808, 0x7c6b38, 0x8759b4)
print()
print('===== H2 0x7c7428 (block2 表, mono 体) =====')
profile('body0', 0x7c7428, 0x7c75b2, 0x879b30)
print()
print('===== H3 body1 0x7c77f0 (stereo 展开 A) =====')
profile('body1', 0x7c77f0, 0x7c797a, 0x879b30)
print()
print('===== H3 body2 0x7c7bc0 (stereo 展开 B) =====')
profile('body2', 0x7c7bc0, 0x7c7d4a, 0x879b30)
print()
print('===== H4 编码器 0x7c62ac =====')
enc = dis(0x7c62ac, 0x7c6620)
print('  insns %d' % len(enc))
print('  add esi:', [(hex(a), op) for a, b, mn, op in enc if mn in ('add', 'inc') and 'esi' in op])
print('  add edi:', [(hex(a), op) for a, b, mn, op in enc if mn in ('add', 'inc') and 'edi' in op])
print('  mov al,[esi]:', [hex(a) for a, b, mn, op in enc if mn == 'mov' and op == 'al, byte ptr [esi]'])
print('  byte[edi] writes:', [(hex(a), op) for a, b, mn, op in enc if mn == 'mov' and op.startswith('byte ptr [edi')])
print('  word[edi] writes:', [(hex(a), op) for a, b, mn, op in enc if mn == 'mov' and op.startswith('word ptr [edi')])
for a, b, mn, op in enc:
    if mn in ('je', 'jne', 'jl', 'jle', 'jg', 'jge', 'jmp') and op.startswith('0x') and int(op, 16) < a:
        print('  back-edge %08x -> %s' % (a, op))

print()
print('===== 单体同构：0x7c6808 vs 0x7c7428（归一化 mnemonic+op） =====')
HEX = re.compile(r'0x[0-9a-f]+')


def norm(lo, hi):
    out = []
    for a, b, mn, op in dis(lo, hi):
        out.append((mn, HEX.sub(lambda m: 'V' if int(m.group(0), 16) > 0x1000 else m.group(0), op)))
    return out


a1 = norm(0x7c6808, 0x7c6a60)
a2 = norm(0x7c7428, 0x7c7680)
m = min(len(a1), len(a2))
same = sum(1 for i in range(m) if a1[i] == a2[i])
d = [i for i in range(m) if a1[i] != a2[i]]
print('  长度 %d vs %d ; 相同 %d/%d ; 前 5 差异 %s' % (len(a1), len(a2), same, m, [(i, a1[i], a2[i]) for i in d[:5]]))
