#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r177a：F35 引文自指计数逐版实测（正反控成对）。"""
import csv, glob, os, re, sys

TIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(p):
    return {r[0]: r for r in csv.reader(open(p, encoding='utf-8'), delimiter='\t')}

A = '同血缘克隆'; B = '不是独立实现'
ok = 0; fail = 0
def chk(cond, msg):
    global ok, fail
    if cond: ok += 1; print('  PASS', msg)
    else: fail += 1; print('  FAIL', msg)

vers = []
for d in glob.glob(os.path.join(TIER, 'R17_R*_FACTINDEX_V5*')):
    m = re.search(r'_V(\d+)$', d)
    if m: vers.append((int(m.group(1)), d))
vers.sort()
print('versions found:', len(vers), [v for v, _ in vers])
sel = [(v, d) for v, d in vers if 553 <= v <= 559]
print('selected:', [v for v, _ in sel])
rows_prev = None
for v, d in sel:
    f = os.path.join(d, 'FACT_INDEX.tsv')
    rows = load(f)
    st, lim = rows['F35'][1], rows['F35'][4]
    print('V%d  A(st)=%d A(lim)=%d B(st)=%d B(lim)=%d  len_st=%d len_lim=%d' % (
        v, st.count(A), lim.count(A), st.count(B), lim.count(B), len(st), len(lim)))
    rows_prev = rows
print()
print('--- 断言：V559 现值 vs R174-R2 版本表（V554=1/5, V555=4/7, V556=5/8）---')
vmap = {v: load(os.path.join(d, 'FACT_INDEX.tsv')) for v, d in sel}
for v, expA, expB in ((554, 1, 5), (555, 4, 7), (556, 5, 8)):
    lim = vmap[v]['F35'][4]
    print('  V%d 实测 A=%d B=%d  表写 A=%d B=%d' % (v, lim.count(A), lim.count(B), expA, expB))
    chk(lim.count(A) == expA and lim.count(B) == expB, 'V%d 版本表条目与实测一致' % v)
print()
print('--- 反控（必须为假）---')
chk(vmap[559]['F35'][4].count(B) == 8, 'V559 B(lim)==8（R174-R2 自称的 V556 值现在仍等于 8）')
chk(vmap[559]['F35'][4].count(A) == 5,  'V559 A(lim)==5（同）')
print()
print('--- R174-R2 段本身是否随版本增长 ---')
for v in (556, 557, 558, 559):
    lim = vmap[v]['F35'][4]
    has_r174r2 = '【R174-R2 补' in lim
    print('  V%d 含 R174-R2 段=%s' % (v, has_r174r2))
chk(all('【R174-R2 补' in vmap[v]['F35'][4] for v in (556, 557, 558, 559)),
    'V556..V559 四版均含 R174-R2 段（其后各版未再追加 F35 补段）')
print()
print('RESULT: %d PASS / %d FAIL' % (ok, fail))
sys.exit(1 if fail else 0)
