# -*- coding: utf-8 -*-
"""段清单 + 分隔符约定核对。"""
import io, re, sys
sys.dont_write_bytecode = True
import pefile

R14 = r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14"
EXE = r"D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe"
COV = R14 + "/COVERAGE/coverage.tsv"
B4 = R14 + "/R16_F1_B4/delta.tsv"
W = '④ 活表槽位见证'

pe = pefile.PE(EXE, fast_load=True)
print('sections:')
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    print('  %-10s va=%08X vsize=%08X rsize=%08X  ch=%08X'
          % (nm, 0x400000 + s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData,
             s.Characteristics))

# 并表行/先例：witness 前面紧跟的字符
rows = {}
for ln in io.open(COV, encoding='utf-8-sig'):
    c = ln.rstrip('\r\n').split('\t')
    if len(c) < 8:
        continue
    rows[c[0].strip().upper()] = c

print()
print('preceding char before witness (merged rows):')
from collections import Counter
cnt = Counter()
for e, c in rows.items():
    c4 = c[3]
    i = c4.find(W)
    if i > 0:
        cnt[c4[i - 1]] += 1
print(cnt)

print()
print('B4 appended separator:')
for n, ln in enumerate(io.open(B4, encoding='utf-8-sig')):
    if n == 0:
        continue
    c = ln.rstrip('\r\n').split('\t')
    old = rows[c[0].strip().upper()][3]
    app = c[3][len(old):]
    print('  %s app[:3]=%r  endswith=%r' % (c[0], app[:3], app[-3:]))
