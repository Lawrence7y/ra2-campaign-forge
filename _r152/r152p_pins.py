#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R152 P：终态钉值汇总（只读，写 _r152/r152p_pins.json 供压缩摘要引用）。"""
import hashlib, json, os, subprocess, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
F = {
    'R14_COMMON': os.path.join(D, 'R14_COMMON.md'),
    'LEDGER': os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'),
    'LEAD_LOCK': os.path.join(ROOT, 'lead/LEAD_LOCK'),
    'STATUS_BOARD': os.path.join(D, 'STATUS_BOARD.md'),
    'BOARD_ARCHIVE': os.path.join(D, 'BOARD_ARCHIVE.md'),
    'check_disc': os.path.join(D, 'check_disc.py'),
    'DISC_RECHECK': os.path.join(D, 'DISC_RECHECK.tsv'),
    'DISC_UNVERIFIABLE': os.path.join(D, 'DISC_UNVERIFIABLE.tsv'),
    'FACT_INDEX_V541': os.path.join(D, 'R17_R113_FACTINDEX_V541/FACT_INDEX.tsv'),
    'FACT_INDEX_V540': os.path.join(D, 'R17_R112_FACTINDEX_V540/FACT_INDEX.tsv'),
}
out = {}
for k, p in F.items():
    b = open(p, 'rb').read()
    out[k] = {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(),
              'cr': b.count(b'\r'), 'lf': b.count(b'\n')}
r = subprocess.run([sys.executable, 'check_disc.py'], cwd=D, capture_output=True, text=True, timeout=600)
out['gate'] = {'exit': r.returncode,
               'lines': [l for l in r.stdout.split('\n')
                         if any(x in l for x in ('C10 self', 'C16 per-section', 'C16d', 'C7d', 'C12 ', 'C12b'))]}
json.dump(out, open(os.path.join(ROOT, '_r152/r152p_pins.json'), 'w'), ensure_ascii=False, indent=1)
for k, v in out.items():
    if k == 'gate':
        print('gate exit', v['exit'])
        for l in v['lines']:
            print('   ', l.strip())
    else:
        print('%-18s %9d B  CR=%-5d sha=%s' % (k, v['bytes'], v['cr'], v['sha256'][:16]))
