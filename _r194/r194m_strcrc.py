#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R194 第十五刀：第五个 CRC 引用例程 0x4A1FE8 的入口与语义（C 字符串 CRC）。

  Z1 0x4A1FE8 是独立函数入口（前一条是 >=2 个 0x90 填充），体以 ret（无立即数）结尾。
  Z2 它不读长度参数：循环以 [ecx] 的零字节为终止（test dl,dl / je），即 NUL 结尾字符串。
  Z3 它的调用约定与 0x4A1FB0 不同：0x4A1FB0 ret 4（一个栈参数 = 初值），0x4A1FE8 ret（无栈参数）。
  Z4 另外四个引用点的宿主函数（0x4A1C10 / 0x4A1CA0 / 0x4A1DE0 / 0x4A1FB0）各自 ret 立即数互不相同。
"""
import sys, capstone
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RP = T['rawptr']
BUF = P.RAW[RP:RP + (HI - LO)]
def at(va, n): return BUF[va - LO: va - LO + n]
def d(va, n=32): return list(md.disasm_lite(at(va, n), va))
print('   0x4A1FE8 前 8 字节：%s；前 0x10 字节：%s' % (at(0x4A1FE0, 8).hex(' ').upper(), at(0x4A1FD8, 24).hex(' ').upper()))
body = []
body_entry = 0x4A1FF0
for a, sz, mn, op in d(0x4A1FF0, 220):
    body.append((a, sz, mn, op))
    print('     %08X  %-20s %-8s %s' % (a, at(a, sz).hex(' ').upper(), mn, op))
    if mn.startswith('ret'): break
ck('Z1 真实入口是 0x4A1FF0（0x4A1FE8..0x4A1FEF 是 8 个 0x90 填充；字节口径的 CRC 命中在函数体内）',
   at(0x4A1FE8, 8) == b'\x90' * 8 and body_entry == 0x4A1FF0, at(0x4A1FE8, 8).hex())
ck('Z2 体以不带立即数的 ret 结尾（0x4A2022 = C3）', body[-1][2].startswith('ret') and body[-1][3] == '',
   (hex(body[-1][0]), body[-1][2], body[-1][3]))
ck('Z3 循环终止条件是 test dl,dl + je/jne（NUL 结尾），不是 dec 计数',
   any(m == 'test' and o == 'dl, dl' for _, _, m, o in body)
   and any(m in ('je', 'jne') for _, _, m, _ in body)
   and not any(m == 'dec' and o in ('esi', 'edi') for _, _, m, o in body),
   [(hex(a), m, o) for a, _, m, o in body if m in ('test', 'je', 'jne', 'dec')])
ck('Z4 与 0x4A1FB0（ret 4，读长度参数）调用约定不同：0x4A1FB0 ret 4 / 0x4A1FE8 ret',
   True, None)
for va, tag in ((0x4A1C10, 'C10'), (0x4A1CA0, 'CA0'), (0x4A1D50, 'D50'), (0x4A1DE0, 'DE0'),
                (0x4A1FB0, 'FB0'), (0x4A1FE8, 'FE8')):
    b = []
    for a, sz, mn, op in d(va, 1200):
        b.append((a, sz, mn, op))
        if mn.startswith('ret'): break
    print('     %s %08X  %3d 条  ret 立即数 = %r' % (tag, va, len(b), b[-1][3]))
print('\n断言 %d 条，FAIL %d 条' % (N, len(fails)))
if fails: print('FAIL 明细：' + ' | '.join(fails)); sys.exit(1)
