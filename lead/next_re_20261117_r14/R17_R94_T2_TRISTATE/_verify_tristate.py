# -*- coding: utf-8 -*-
"""read-only verification for R55-T2: Q1 rule on 28 rows + in-memory selfcheck + fraud test.
不调用 migrate()，不落盘 DISC_RECHECK.tristate.tsv。"""
import io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(R14, '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, R14)
import migrate_tristate as m
import recheck_verify as v

s, out, changes = m.build_output()
print('=== Q1: 判别式逐行结果（28 行）===')
print('id\told7\tnew7\tclass')
for i in range(1, len(out)):
    a = s[i].split('\t')
    b = out[i].split('\t')
    old = a[6].strip()
    new = b[6].strip()
    print('%s\t%s\t%s\t%s' % (a[0], old, new,
          ('有·可核' if new == m.NEW_V else '有·无自产出机制' if new == m.NEW_N else '无')))

print('\n=== changes count by target ===')
from collections import Counter
print(Counter(x[2] for x in changes))
print('total col7 changes:', len(changes))

print('\n=== Q3 selfcheck (in-memory, 不落盘) ===')
ok, counts = m.selfcheck()
print('PASS?', ok)

print('\n=== Q4 fraud construction: 无 -> 有·可核 还能被抓吗 ===')
# 取纪律 11（现 col7=无），复制行仅改 col7 为 有·可核，走 recheck_verify
rows = [l.split('\t') for l in s[1:] if l]
for r in rows:
    if r[0] == '11':
        fake = list(r)
        print('before col7:', fake[6])
        fake[6] = m.NEW_V
        fakeok, detail = v.verify_recheck_line(ROOT, fake)
        print('after  col7:', fake[6], '-> recheck_verify ok=%s :: %s' % (fakeok, detail[:100]))
        break
