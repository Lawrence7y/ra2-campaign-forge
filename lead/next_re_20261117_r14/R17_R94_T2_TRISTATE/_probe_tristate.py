# -*- coding: utf-8 -*-
"""read-only probe: run recheck_verify on the 5 landable rows, print status."""
import io, os, sys
R14 = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ROOT = os.path.abspath(os.path.join(R14, '..', '..'))
sys.path.insert(0, R14)
import recheck_verify as v
with io.open(os.path.join(R14, 'DISC_RECHECK.tsv'), encoding='utf-8', newline='') as f:
    lines = [l for l in f.read().split('\n') if l]
rows = [l.split('\t') for l in lines[1:]]
for r in rows:
    if r[0] in ('3', '4', '22', '27', '28'):
        ok, detail = v.verify_recheck_line(ROOT, r)
        print('disc %s product=%s ok=%s :: %s' % (r[0], os.path.basename(r[4]), ok, detail[:120]))
