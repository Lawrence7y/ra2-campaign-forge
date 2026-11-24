# -*- coding: utf-8 -*-
"""只读探针：dump 先例 ④ 行 + 本批 4 行的现盘原值（A 项要用的实值）。"""
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')

ENTRIES = ['00763200', '00763D90', '00772CD0', '00772EB0']
PREC = ['00464AC0', '004DE630', '004F42F0']

rows = {}
with open(COV, encoding='utf-8-sig') as f:
    for i, ln in enumerate(f):
        if i == 0:
            continue
        c = ln.rstrip('\r\n').split('\t')
        if len(c) < 8:
            continue
        e = c[0].strip().upper()
        rows.setdefault(e, []).append(c)

print('=== 本批 entry 在现盘的 col4 原值 ===')
for e in ENTRIES:
    r = rows.get(e)
    print('\n--- %s  occurrences=%d' % (e, len(r) if r else 0))
    if r:
        c = r[0]
        print('  grade=%r  n_sources=%r conflict=%r' % (c[4], c[6], c[7]))
        print('  col4=', c[3])

print('\n=== 先例行 ★④ 活表槽位见证 骨架 ===')
for e in PREC:
    r = rows.get(e)
    if not r:
        print('--- %s NOT FOUND' % e); continue
    print('\n--- %s' % e)
    print(r[0][3])
