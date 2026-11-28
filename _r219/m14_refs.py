# -*- coding: utf-8 -*-
"""R219 m14：修正 m13 A2 暴露的自错 E3 ——「三 offset 引用 31 条」实际为 30 条。

m1 的输出里那个 31 是 **30 条 (0x77c/0x780/0x784) + 1 条 (0x87c488)** 的合计，
被我误读成「三 offset 的合计 = 31」，并写进了 R14 §2.227 / GOAL §1277 / LOCK QM / 看板第 219 轮。

本脚本给出定稿数字（逐 offset 逐助记符）：
  [1] 五个字段 offset 的引用全表：0x77c / 0x780 / 0x784 / 0x788 / 0x87c488
  [2] 「mov dword ptr [reg+off], imm32(.text)」写入端逐条
  [3] 反控：确认 0x87c488 只有 1 条且是 call（不是 mov 写入）
"""
import sys, re, collections, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
T = P.B['.text']; LO = T['lo']
raw = P.RAW[T['rawptr']:T['rawptr'] + T['rawsize']]
insns = []; pos = 0
while pos < len(raw):
    got = False
    for a, sz, mn, ops in md.disasm_lite(raw[pos:pos + 16], LO + pos):
        insns.append((a, mn, ops)); pos += sz; got = True; break
    if not got: pos += 1
print('[0] sweep = %d insns' % len(insns))

pat = re.compile(r'\[(eax|ebx|ecx|edx|esi|edi|ebp) \+ (0x[0-9a-f]+)\]', re.I)
TARGETS = (0x77c, 0x780, 0x784, 0x788, 0x87c488)
hits = [(a, mn, o, int(m.group(2), 16)) for a, mn, o in insns
        if (m := pat.search(o)) and int(m.group(2), 16) in TARGETS]
c = collections.Counter((off, mn) for _, mn, _, off in hits)
print('\n[1] per-offset / per-mnemonic:')
for off in TARGETS:
    tot = sum(1 for h in hits if h[3] == off)
    det = ', '.join('%s=%d' % (mn, c[(off, mn)]) for mn in sorted(set(h[1] for h in hits if h[3] == off)))
    print('    off=%#07x total=%2d   %s' % (off, tot, det))
three = sum(1 for h in hits if h[3] in (0x77c, 0x780, 0x784))
four = sum(1 for h in hits if h[3] in (0x77c, 0x780, 0x784, 0x788))
print('    三 offset (0x77c/0x780/0x784) 合计 = %d   <== 定稿数字（此前误记 31）' % three)
print('    四 offset (加 0x788) 合计 = %d' % four)
print('    再加 0x87c488 1 条 => 全五 offset = %d' % len(hits))

print('\n[2] imm32 writes into .text:')
imm = [(a, off, int(o.split(',')[-1].strip(), 16)) for a, mn, o, off in hits
       if mn == 'mov' and ', 0x' in o and P.where(int(o.split(',')[-1].strip(), 16)) == '.text']
for a, off, v in imm:
    print('    %#x  off=%#05x <- %#010x' % (a, off, v))
print('    total = %d ; 其中三 offset 内 %d 条、0x788 %d 条'
      % (len(imm), sum(1 for _, off, _ in imm if off in (0x77c, 0x780, 0x784)),
         sum(1 for _, off, _ in imm if off == 0x788)))

print('\n[3] NEG CONTROL: 0x87c488 的全部引用')
for a, mn, o, off in hits:
    if off == 0x87c488:
        print('    %#x %s %s' % (a, mn, o))
print('    含 mov 写入的条数 = %d (must be 0)'
      % sum(1 for a, mn, o, off in hits if off == 0x87c488 and mn == 'mov'))

json.dump(dict(three=three, four=four, all5=len(hits),
               imm_total=len(imm),
               imm_three=sum(1 for _, off, _ in imm if off in (0x77c, 0x780, 0x784)),
               imm_788=sum(1 for _, off, _ in imm if off == 0x788)),
          open('/home/t628/projects/ra2-campaign-forge/_r219/m14.json', 'w'), indent=1)
print('\n[done] -> _r219/m14.json')
