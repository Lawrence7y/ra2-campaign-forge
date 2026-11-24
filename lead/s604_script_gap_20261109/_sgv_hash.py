# -*- coding: utf-8 -*-
# _sgv_hash.py —— 复核步骤①：独立实算编排方基线 8 件 + 上轮写域 5 件指纹（hashlib，只读）
import hashlib, os, time

BASE = r'D:\Project\ra2-campaign-forge'
FILES = [
    ('lead/GOAL_THREE_TARGETS_20261018.md', '2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede', 759518),
    ('lead/PENDING_DECISIONS.md', '3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7', 52419),
    ('lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md', '7241026122978426838d6c8ccaa8ea3335fe6213adef6bae10ab9c7aa83df2f2', 17272),
    ('lead/s604_attribution_20261108/S604_ATTRIBUTION.md', '8e9a606752ce2fd4c3d279ba5bb4a54eba99bc83f8974921f3f5601aa1008237', 27182),
    ('lead/slowframe_r3_20261108/_r3_recompute_gapdiff.py', '9e27495232301018ec8e5b4f38c101d6ab4835feef514215a821be00ca459a78', 12659),
    ('lead/slowframe_r3_20261108/_r3_recompute_out.txt', 'f1f55791f14bb13669d2fde062a1d85ffaab3c05d7379c59573692c5cb88e54b', 9494),
    ('lead/slowframe_r3_20261108/S604_GAP_RECHECK.md', '5d1b0ecc9f0e21ddecc38584c363afa0c758f40089ccc57749f237aeffbdf726', 19291),
    ('lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md', 'e7c29e06f48b2380d5bec3f99e08ac2a4ce90d94da27b48b98d5eb2113a75d60', 23707),
    # 上轮写域 5 件（对照 _sg_FINDINGS.md:8-11 自报指纹）
    ('lead/s604_script_gap_20261109/_sg_FINDINGS.md', None, None),
    ('lead/s604_script_gap_20261109/_sg_probe_compression.py', '9d178bcf60eafccb1878cb292aa714db754157c5fce157d164c7a4093f23ddd3', 12708),
    ('lead/s604_script_gap_20261109/_sg_probe_compression_out.txt', '723537dc8d9cbf6db2e71026bec8ef5ed16a6ee878bf09fd2844e28a4712e5e3', 5102),
    ('lead/s604_script_gap_20261109/_sg_probe_shift.py', '0fe4fb8f194cf082412ae90f19741c8b22276add2a0286f548dac63ed156d6fb', 10080),
    ('lead/s604_script_gap_20261109/_sg_probe_shift_out.txt', '354c974135dc58cb5c8977dbf2caa1b88eaa158b8d47b72d7cd3838e45fc6a1e', 3423),
]
for rel, exp_h, exp_b in FILES:
    p = os.path.join(BASE, rel.replace('/', os.sep))
    with open(p, 'rb') as fh:
        data = fh.read()
    h = hashlib.sha256(data).hexdigest()
    n = len(data)
    if exp_h is None:
        verdict = 'RECORDED'
    else:
        verdict = 'MATCH' if (h == exp_h and n == exp_b) else '*** MISMATCH ***'
    mt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(p)))
    print('%s  %8d B  mtime=%s  %s  %s' % (verdict, n, mt, h, rel))
