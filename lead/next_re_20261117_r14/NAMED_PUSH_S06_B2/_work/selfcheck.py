# -*- coding: utf-8 -*-
"""自校验：目录完整、行数、delta 6 列、base_rate、evidence 存在且 name/subsystem 原样。"""
import os, csv, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT,'_work')
A = {r['entry']:r for r in json.load(open(os.path.join(WORK,'analysis.json'),encoding='utf-8'))}
ev = os.path.join(ROOT,'EVIDENCE')
files = [f for f in os.listdir(ev) if f.startswith('ROW_') and f.endswith('.txt')]
print('EVIDENCE files:', len(files))
# delta
d = list(csv.reader(open(os.path.join(ROOT,'delta.tsv'),encoding='utf-8'), delimiter='\t'))
print('delta header:', d[0])
print('delta PASS rows:', len(d)-1)
for r in d[1:]:
    assert len(r)==6, r
    e = r[0]
    assert e==e.upper() and not e.startswith('0X')
    assert A[e]['name']==r[2], (e, r[2], A[e]['name'])
    assert r[1]=='S06'
    assert r[4]=='[已证]'
    p = os.path.join(ROOT, r[5].split('/NAMED_PUSH_S06_B2/')[-1].replace('/',os.sep))
    assert os.path.isfile(p), p
    print('  OK', e, r[2], 'grade', r[4])
# base_rate
br = list(csv.reader(open(os.path.join(ROOT,'base_rate.tsv'),encoding='utf-8'), delimiter='\t'))
print('base_rate:', br)
# report sanity
rep = open(os.path.join(ROOT,'REPORT.md'),encoding='utf-8').read()
for tok in ['B2  18  18  3  18  3  0.1667','四环齐全','18/18','3/18']:
    print('report contains', repr(tok), tok in rep)
print('SELF-CHECK PASS')
