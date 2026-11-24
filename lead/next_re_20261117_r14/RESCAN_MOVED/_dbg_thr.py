# -*- coding: utf-8 -*-
"""报告用最终数字：门槛对照 + 命名口径敏感性。只读 _rows.tsv / _falsifiable_layer.tsv / survey.tsv。"""
import csv
import math
import re

rows = list(csv.DictReader(open('_rows.tsv', encoding='utf-8'), delimiter='\t'))
layer = {r['subsystem']: r for r in
         csv.DictReader(open('_falsifiable_layer.tsv', encoding='utf-8'), delimiter='\t')}
ref = {}
with open(r'..\SURVEY_3B2\survey.tsv', encoding='utf-8') as f:
    rd = csv.reader(f, delimiter='\t')
    next(rd)
    for r in rd:
        ref[r[0]] = dict(n=int(r[1]), proved=int(r[3]), p3b2=int(r[5]))
SUBS = ['S%02d' % i for i in range(1, 23)]
PSEUDO_SURVEY = re.compile(r'^(sub_|.*::sub_)')

hdr = ('S', 'n', 'proved', 'thr50', 'm0', 'new', 'new_named', 'new_named_loose',
       'vd_new', 'vd_named', 'A', 'A>=thr', 'B', 'B>=thr')
print('\t'.join(hdr))
tot = dict(n=0, proved=0, m0=0, new=0, nn=0, nns=0, vd=0, vdn=0)
changed = []
for s in SUBS:
    rs = [r for r in rows if r['subsystem'] == s]
    m0 = sum(1 for r in rs if int(r['m0_sites'])>0)
    new = [r for r in rs if int(r['m0_sites'])==0 and (int(r['m1_sites'])>0 or int(r['m2_sites'])>0)]
    nn = sum(1 for r in new if r['named'] == '1')
    nns = sum(1 for r in new if r['name'] and not PSEUDO_SURVEY.match(r['name']))
    vd = int(layer[s]['new_value_dispatch'])
    vdn = int(layer[s]['new_vd_named'])
    n, pr = ref[s]['n'], ref[s]['proved']
    thr = math.ceil(0.5 * n)
    A = pr + m0 + nn
    B = pr + m0 + vd
    base = pr + m0          # 不含任何新增（=SURVEY_3B2 的 best_proved）
    print('\t'.join(str(x) for x in (s, n, pr, thr, m0, len(new), nn, nns, vd, vdn,
                                     A, A >= thr, B, B >= thr)))
    if (base < thr) and (A >= thr or B >= thr):
        changed.append(s)
    for k, v in (('n', n), ('proved', pr), ('m0', m0), ('new', len(new)),
                 ('nn', nn), ('nns', nns), ('vd', vd), ('vdn', vdn)):
        tot[k] += v
print('TOTAL\tn=%d proved=%d m0=%d new=%d new_named=%d new_named_loose=%d vd_new=%d vd_named=%d'
      % (tot['n'], tot['proved'], tot['m0'], tot['new'], tot['nn'], tot['nns'],
         tot['vd'], tot['vdn']))
print('因新增而跨过 proved 门槛的子系统:', changed or '无')
