"""Recheck section 4: screenshot hashing + per-pixel diff for the three trips."""
import hashlib, os
from PIL import Image
import numpy as np

ROOT = 'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/'
DIRS = ['l3_1101v4e', 'l3_1101v4f', 'l3_1101v4g']
FILES = ['frame_target_01.png', 'navsig_burst_00_g.png', 'fs_boot_probe.png',
         'frame_early_01.png', 'navsig_nav_setup_post_00_g.png']

h = {}
for d in DIRS:
    for f in FILES:
        p = ROOT + d + '/' + f
        if os.path.exists(p):
            b = open(p, 'rb').read()
            h[(d, f)] = (hashlib.sha256(b).hexdigest(), len(b), Image.open(p).size)
for f in FILES:
    print('==', f)
    for d in DIRS:
        v = h.get((d, f))
        print('   ', d, v if v else 'ABSENT')

def pixdiff(a, b):
    ia = np.asarray(Image.open(a).convert('RGB'), dtype=np.int16)
    ib = np.asarray(Image.open(b).convert('RGB'), dtype=np.int16)
    assert ia.shape == ib.shape, (ia.shape, ib.shape)
    d_ = np.abs(ia - ib)
    per_px = d_.max(axis=2)
    return ia.shape, int(d_.max()), int((per_px > 0).sum()), per_px.size

pairs = [('l3_1101v4e', 'l3_1101v4f'), ('l3_1101v4e', 'l3_1101v4g'), ('l3_1101v4f', 'l3_1101v4g')]
for f in ['frame_target_01.png', 'navsig_burst_00_g.png', 'fs_boot_probe.png']:
    print('== pixel diff', f)
    for a, b in pairs:
        pa, pb = ROOT + a + '/' + f, ROOT + b + '/' + f
        if os.path.exists(pa) and os.path.exists(pb):
            shape, maxd, ndiff, total = pixdiff(pa, pb)
            print(f'   {a} vs {b}: shape={shape} maxdiff={maxd} diff_px={ndiff}/{total} = {100.0*ndiff/total:.4f}%')
        else:
            print(f'   {a} vs {b}: MISSING FILE')

# also compare burst vs target within one trip
for d in DIRS:
    print(d, 'burst==target bytes?',
          h.get((d, 'navsig_burst_00_g.png'), (None,))[0] == h.get((d, 'frame_target_01.png'), (None,))[0])
