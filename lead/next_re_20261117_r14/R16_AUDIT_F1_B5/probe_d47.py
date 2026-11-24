# -*- coding: utf-8 -*-
"""只读探针：核 D-47 披露指针在本批与既有 76 行族里的措辞一致性 + §12.4/§12.6 分布。"""
import os, sys, re, collections
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
DELTA = os.path.join(R14, 'R16_F1_B5', 'delta.tsv')

pat = re.compile(r'（D-47\(A\) 裁决：[^）]*）')
forms = collections.Counter()
rows_with = []
with open(COV, encoding='utf-8-sig') as f:
    for i, ln in enumerate(f):
        if i == 0:
            continue
        c = ln.rstrip('\r\n').split('\t')
        if len(c) < 8:
            continue
        m = pat.findall(c[3])
        if m:
            rows_with.append(c[0])
            for x in m:
                forms[x] += 1
print('coverage rows with D-47 disclosure:', len(rows_with))
print('distinct disclosure forms:', len(forms))
for k, v in forms.most_common():
    print('  x%-3d %s' % (v, k))
print('rows:', ' '.join(rows_with[:90]))
print()
print('§12.4 occurrences in coverage col4:',
      sum(1 for i, ln in enumerate(open(COV, encoding='utf-8-sig'))
          if i and '§12.4' in ln))
print('§12.6 occurrences in coverage col4:',
      sum(1 for i, ln in enumerate(open(COV, encoding='utf-8-sig'))
          if i and '§12.6' in ln))

print('\n=== delta.tsv appended parts: §12.4/§12.6 + disclosure form ===')
with open(DELTA, encoding='utf-8') as f:
    dl = [x for x in f.read().split('\n') if x.strip()][1:]
for ln in dl:
    c = ln.split('\t')
    body = c[3]
    print(c[0], '§12.4=%s §12.6=%s' % ('§12.4' in body, '§12.6' in body),
          'disc=', pat.findall(body))
