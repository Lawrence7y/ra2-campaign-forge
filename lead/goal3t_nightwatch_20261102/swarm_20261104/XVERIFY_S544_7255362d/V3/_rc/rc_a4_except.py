"""Recheck A4 + section 4: hash every except_post_*.txt, and hash + pixel-diff the screenshots."""
import hashlib, os, glob, collections, sys

CAND = []
for root in ['D:/Project/ra2-campaign-forge/lead',
             'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip']:
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.startswith('except_post_') and fn.endswith('.txt'):
                CAND.append(os.path.join(dirpath, fn).replace('\\', '/'))
print('except_post files found =', len(CAND))
h = collections.Counter()
lines = collections.Counter()
for p in CAND:
    b = open(p, 'rb').read()
    h[hashlib.sha256(b).hexdigest()] += 1
    lines[b.count(b'\n') + 1] += 1
print('distinct sha256 =', len(h))
for k, v in h.most_common():
    print('  ', k, v)
print('line-count distribution (by newline+1):', dict(lines))

# targeted files
ROOT = 'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/'
for d, f in [('l3_1101v4e', 'except_post_20261103T112149364551.txt'),
             ('l3_1101v4f', 'except_post_20261104T172914049535.txt'),
             ('l3_1101v4g', 'except_post_20261104T173316775436.txt')]:
    p = ROOT + d + '/' + f
    b = open(p, 'rb').read()
    txt = b.decode('utf-8', 'replace')
    print(d, 'size', len(b), 'sha256', hashlib.sha256(b).hexdigest(),
          'lines(newline-split)', len(txt.splitlines()),
          '007CFC9F count', txt.count('007CFC9F'),
          'EXCEPTION_SINGLE_STEP count', txt.count('EXCEPTION_SINGLE_STEP'))
