# -*- coding: utf-8 -*-
"""并发并表的 18 行在派生 76 集合里的位置；B5 规模。"""
import io, os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify as V

base76, stages, raw = V.derive_76()
pos = {r['entry'].upper(): i + 1 for i, r in enumerate(base76)}
changed = ("005FEAF0 00629FD0 0062D7A0 0062D9A0 0062FE90 00630090 00644960 006457A0 "
           "00645950 006B5850 006C2B10 006C2C90 006C2E10 006C2F90 006C3110 006C3290 "
           "006C3410 006C3590").split()
print('changed entries -> derived position:')
for e in changed:
    print('  %s -> %s' % (e, pos.get(e, 'NOT IN 76')))
print()
for b in ('B1', 'B2', 'B3', 'B4', 'B5'):
    p = os.path.join(V.R14, 'R16_F1_%s' % b, 'fields.tsv')
    if os.path.isfile(p):
        n = sum(1 for i, ln in enumerate(io.open(p, encoding='utf-8-sig')) if i)
        ent = [ln.split('\t')[0] for i, ln in enumerate(io.open(p, encoding='utf-8-sig')) if i]
        ps = [pos.get(x.upper(), '?') for x in ent]
        print('%s fields rows=%d  derived_positions=%s..%s' % (b, n, ps[0], ps[-1]))
