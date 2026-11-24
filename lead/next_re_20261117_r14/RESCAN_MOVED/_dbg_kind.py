# -*- coding: utf-8 -*-
"""按比较种类拆分 M1 站点（test r,r 空值检测 vs cmp r,imm 状态码比较），
并统计各自涉及的**行**数 —— 决定"可伪证增量"的关键口径。
"""
import csv
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import *

pe = pefile.PE(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe')
IB = pe.OPTIONAL_HEADER.ImageBase
sec = next(s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text')
VA = IB + sec.VirtualAddress
D = sec.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True

sites = list(csv.DictReader(open('_m1m2_sites.tsv', encoding='utf-8'), delimiter='\t'))
rows = {r['entry']: r for r in csv.DictReader(open('_rows.tsv', encoding='utf-8'), delimiter='\t')}

import collections
bykind = collections.defaultdict(lambda: [0, set()])
detail = []
for s in sites:
    ea = int(s['cmp_at'], 16)
    off = ea - VA
    ins = next(md.disasm(D[off:off + 16], ea))
    if ins.id == X86_INS_TEST:
        kind = 'test_r_r'
    elif ins.id == X86_INS_CMP:
        kind = 'cmp_r_imm'
    elif ins.id in (X86_INS_CMP, X86_INS_TEST):
        kind = 'cmp_mem'
    else:
        kind = 'other:%s' % ins.mnemonic
    key = (s['form'], kind)
    bykind[key][0] += 1
    bykind[key][1].add(s['entry'])
    if ins.id == X86_INS_CMP:
        detail.append((s['entry'], s['subsystem'], s['name'], s['form'],
                       s['call_at'], s['cmp_at'], ins.op_str, rows[s['entry']]['m0_sites']))

print('%-4s %-12s %8s %10s' % ('form', 'cmp_kind', 'sites', 'rows'))
for k in sorted(bykind):
    print('%-4s %-12s %8d %10d' % (k[0], k[1], bykind[k][0], len(bykind[k][1])))

print('\n== M1 的 cmp r,imm 站点（状态码比较，最接近 ③b② 的形态）共 %d ==' % len(detail))
for t in detail[:40]:
    print('%s %s %-32s call@%s cmp@%s  %s  (m0=%s)' % (
        t[0], t[1], t[2][:32], t[4], t[5], t[6], t[7]))
