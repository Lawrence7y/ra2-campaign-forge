#!/usr/bin/env python3
# R131 r131u: write-discipline backup. Pure-LF files, wx exclusive create, sha+CR asserted
# BEFORE and AFTER, read-back verified. Nothing is modified here.
import hashlib
import io
import json
import os
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
STAMP = time.strftime('%Y%m%d_%H%M%S')
TAG = 'R131'
OUT = '/home/t628/projects/ra2-campaign-forge/_r131/r131u_backup.json'

TARGETS = [
    os.path.join(R14, 'check_disc.py'),
    os.path.join(R14, 'DISC_RECHECK.tsv'),
    os.path.join(R14, 'R14_COMMON.md'),
    os.path.join(R14, 'STATUS_BOARD.md'),
    os.path.join(R14, 'BOARD_ARCHIVE.md'),
    os.path.join(ROOT, 'lead', 'LEAD_LOCK'),
    os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
]
EXPECT_CR = {
    'R14_COMMON.md': 1081,
    'LEAD_LOCK': 137,
    'GOAL_THREE_TARGETS_20261018.md': 337,
    'STATUS_BOARD.md': 0,
    'BOARD_ARCHIVE.md': 2952,
}

os.makedirs(BASE, exist_ok=True)
rec = {'stamp': STAMP, 'files': []}
for p in TARGETS:
    b = io.open(p, 'rb').read()
    name = os.path.basename(p)
    sha = hashlib.sha256(b).hexdigest()
    cr = b.count(b'\r\n')
    exp = EXPECT_CR.get(name)
    entry = {'path': p, 'name': name, 'sha256': sha, 'bytes': len(b), 'cr': cr,
             'expected_cr': exp, 'cr_ok': (exp is None or cr == exp)}
    print('%-34s %s bytes=%-8d CR=%-5s %s'
          % (name, sha[:16], len(b), cr, 'OK' if entry['cr_ok'] else 'CR-MISMATCH'))
    if not entry['cr_ok']:
        rec['files'].append(entry)
        continue
    dst = os.path.join(BASE, '%s.before_%s_%s.bak' % (name, TAG, STAMP))
    # wx: exclusive create. If the name somehow exists, do NOT overwrite.
    with io.open(dst, 'xb') as f:
        f.write(b)
    back = io.open(dst, 'rb').read()
    entry['backup'] = dst
    entry['readback_sha256'] = hashlib.sha256(back).hexdigest()
    entry['readback_ok'] = entry['readback_sha256'] == sha and back == b
    src_after = hashlib.sha256(io.open(p, 'rb').read()).hexdigest()
    entry['source_unchanged'] = src_after == sha
    print('     -> %s  readback=%s source_unchanged=%s'
          % (os.path.basename(dst), entry['readback_ok'], entry['source_unchanged']))
    rec['files'].append(entry)

bad = [e for e in rec['files'] if not (e.get('cr_ok') and e.get('readback_ok')
                                      and e.get('source_unchanged'))]
rec['all_ok'] = not bad
print('\nbackups ok: %d / %d' % (len(rec['files']) - len(bad), len(rec['files'])))
json.dump(rec, open(OUT, 'w'), ensure_ascii=False, indent=1)
raise SystemExit(0 if rec['all_ok'] else 1)
