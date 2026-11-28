# -*- coding: utf-8 -*-
"""R222 m8：把 0x7c62ac 定性为「内联 delta 解码器（3 份展开副本）」，并核对三份副本的
指针步进差异与初始化函数不对称。

定性判据（全部实测）：
  D1 输入是 byte[esi]（1 B 含 2 nibble），输出是 word[edi]/byte[edi]（样本）⇒ 方向是「解包→样本」。
  D2 每次迭代用 dword[ebx+0x10] 的 bit0 在「取已缓存字的高半字节」/「读新字节、取低半字节」间切换。
  D3 全函数 0 条 0x879b30 引用；delta 由 test eax,4 / 2 / 1 + shr 3 + test eax,8 内联算出，
     与表版解码器（0x7c6808 / 0x7c7428）同一个律 D 定义（m6 C1 已证 1424/1424）。
  D4 样本计数 [ebp-8] 在 16 位模式下先 shr 1（0x7c62ce..0x7c62d5），8 位模式不除。
反控：
  R1 若为编码器，则写 [esi]、读 [edi]；实测相反。
  R2 若三份副本指针步进完全一致，则副本 2/3 的第 2 组 esi/edi 步进应与副本 1 相同 —— 实测不同。
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


COPIES = [('copy1', 0x7c62ea, 0x7c63e8), ('copy2', 0x7c63ea, 0x7c6509), ('copy3', 0x7c6509, 0x7c6609)]
print('=== 三份展开副本结构 ===')
info = {}
for nm, lo, hi in COPIES:
    s = dis(lo, hi)
    reads = [a for a, b, mn, op in s if mn == 'mov' and op == 'al, byte ptr [esi]']
    w16 = [a for a, b, mn, op in s if mn == 'mov' and op.startswith('word ptr [edi')]
    w8 = [a for a, b, mn, op in s if mn == 'mov' and op == 'byte ptr [edi], ah']
    esi_st = [(a, mn, op) for a, b, mn, op in s if ('esi' in op) and mn in ('inc', 'add', 'dec', 'sub')]
    edi_st = [(a, mn, op) for a, b, mn, op in s if ('edi' in op) and mn in ('inc', 'add', 'dec', 'sub')]
    nibsel = [a for a, b, mn, op in s if mn == 'test' and op.startswith('dword ptr [ebx + 0x10]')]
    refs879 = [a for a, b, mn, op in s if '0x879b30' in op]
    back = [(a, op) for a, b, mn, op in s if mn == 'jne' and op.startswith('0x') and int(op, 16) < a]
    info[nm] = dict(insns=len(s), reads=reads, w16=w16, w8=w8, esi=esi_st, edi=edi_st,
                    nibsel=nibsel, refs879=refs879, back=back)
    print('%s %08x..%08x insns %d' % (nm, lo, hi, len(s)))
    print('   read byte[esi] %s | word[edi] %s | byte[edi],ah %s' %
          ([hex(x) for x in reads], [hex(x) for x in w16], [hex(x) for x in w8]))
    print('   esi step %s' % [(hex(a), mn, op) for a, mn, op in esi_st])
    print('   edi step %s' % [(hex(a), mn, op) for a, mn, op in edi_st])
    print('   nibble select %s | 0x879b30 refs %s | back-edge %s' %
          ([hex(x) for x in nibsel], refs879, [(hex(a), op) for a, op in back]))

ck('D1a 三份副本各读 1 次 byte[esi]', all(len(info[k]['reads']) == 1 for k in info), {k: info[k]['reads'] for k in info})
ck('D1b 三份副本各写 1 次 word[edi] + 1 次 byte[edi],ah',
   all(len(info[k]['w16']) == 1 and len(info[k]['w8']) == 1 for k in info))
ck('D3a 三份副本 0x879b30 引用全 0', all(info[k]['refs879'] == [] for k in info),
   {k: info[k]['refs879'] for k in info})
ck('D3b copy1 有 nibble 选择 test（bit0 切换）', len(info['copy1']['nibsel']) == 1, info['copy1']['nibsel'])
ck('D3c 三份副本各有 1 条回边（jne 向前）', all(len(info[k]['back']) == 1 for k in info),
   {k: info[k]['back'] for k in info})
# 反控 R1：写 [esi] / 读 [edi] 应不存在
wr_esi = [(a, mn, op) for a, b, mn, op in dis(0x7c62ac, 0x7c6620) if mn == 'mov' and op.startswith('byte ptr [esi],')]
rd_edi = [(a, mn, op) for a, b, mn, op in dis(0x7c62ac, 0x7c6620) if mn == 'mov' and ('edi' in op and op.split(',')[0].strip() in ('al', 'ax', 'eax'))]
ck('R1 反控：全函数无 mov [esi],.. 也无把 [edi] 读进累加器', wr_esi == [] and rd_edi == [], (wr_esi, rd_edi))
# D4 16 位样本数折半
h = [(a, mn, op) for a, b, mn, op in dis(0x7c62ce, 0x7c62da)]
ck('D4a 16 位模式样本数 shr 1（cmp word[ebx+0x38],0x10 -> shr eax,1）',
   any(mn == 'cmp' and op == 'word ptr [ebx + 0x38], 0x10' for a, mn, op in h) and
   any(mn == 'shr' and op == 'eax, 1' for a, mn, op in h), h)
# 反控 R2：副本 2/3 与副本 1 的 edi 步进不同
ck('R2 反控：copy2/copy3 的 edi 步进与 copy1 不同',
   info['copy1']['edi'] != info['copy2']['edi'] and info['copy1']['edi'] != info['copy3']['edi'],
   (info['copy1']['edi'], info['copy2']['edi'], info['copy3']['edi']))

print()
print('=== 两个初始化函数的字段集 ===')
for nm, lo, hi in (('init2 0x7c6270', 0x7c6270, 0x7c62ac), ('init1 0x7c6730', 0x7c6730, 0x7c6752)):
    s = [(a, mn, op) for a, b, mn, op in dis(lo, hi) if mn == 'mov' and op.startswith(('word ptr [eax', 'dword ptr [eax'))]
    print(nm, [(op.split(',')[0].replace('word ptr ', '').replace('dword ptr ', ''), op.split(',')[1].strip()) for a, mn, op in s])
i2 = [(a, mn, op) for a, b, mn, op in dis(0x7c6270, 0x7c62ac)]
i1 = [(a, mn, op) for a, b, mn, op in dis(0x7c6730, 0x7c6752)]
ck('I1 init2 清 8 个字段（+0x22/+0x20/+0x14/+0x10/+0x36/+0x34/+0x28/+0x24）',
   len([1 for a, mn, op in i2 if mn == 'mov' and op.startswith(('word ptr [eax', 'dword ptr [eax'))]) == 8)
ck('I2 init1 只清 4 个字段（+0x22/+0x14/+0x36/+0x28）',
   len([1 for a, mn, op in i1 if mn == 'mov' and op.startswith(('word ptr [eax', 'dword ptr [eax'))]) == 4)
ck('I3 init2 设两声道 step=7（+0x20/+0x34），init1 不设',
   any(op == 'word ptr [eax + 0x20], 7' for a, mn, op in i2) and
   any(op == 'word ptr [eax + 0x34], 7' for a, mn, op in i2) and
   not any(op.endswith(', 7') for a, mn, op in i1))

print()
print('FAIL 数 =', len(fails), fails)
if fails:
    raise SystemExit(1)
