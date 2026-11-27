#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r158b1_backup.py — 写入纪律第一步：wx 模式独占创建唯一备份 + 断言旧 sha256 与 CR。
幂等：备份已存在且 sha 吻合则跳过创建（不覆盖已有备份）。
"""
import hashlib, io, os, sys, time

R = '/home/t628/projects/ra2-campaign-forge'
BD = R + '/lead/next_re_20261117_r14/R17_LEAD_BASELINE'
STAMP = time.strftime('%Y%m%d_%H%M%S')

TARGETS = [
    ('rc',     R + '/lead/next_re_20261117_r14/R14_COMMON.md',            '281bc45c29afdf8d3752', 1081),
    ('ledger', R + '/lead/GOAL_THREE_TARGETS_20261018.md',                '589367588e6f96fe61e4', 337),
    ('lock',   R + '/lead/LEAD_LOCK',                                     '91210621bceb902cc501', 137),
    ('board',  R + '/lead/next_re_20261117_r14/STATUS_BOARD.md',          'dab4303753f44f19f241', 0),
    ('arch',   R + '/lead/next_re_20261117_r14/BOARD_ARCHIVE.md',         'ca712524789f963c3971', 2952),
]

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok

import glob
for tag, p, sha8, cr in TARGETS:
    raw = io.open(p, encoding='utf-8', newline='').read()
    now8 = hashlib.sha256(open(p, 'rb').read()).hexdigest()[:20]
    ck('%s 旧 sha 前缀吻合' % tag, now8 == sha8, '%s vs %s' % (now8, sha8))
    ck('%s 旧 CR 计数吻合' % tag, raw.count('\r') == cr, '%d vs %d' % (raw.count('\r'), cr))
    ext = '.md' if p.endswith('.md') else '.bak'
    # 幂等：本 tag 若已有 before_r158_* 备份且 sha 与当前一致，则复用
    prior = sorted(glob.glob(os.path.join(BD, '*before_r158_%s_*' % tag)))
    if prior:
        ph = hashlib.sha256(open(prior[-1], 'rb').read()).hexdigest()[:20]
        if ph == now8:
            ck('%s 复用已有备份（sha 吻合）' % tag, True, os.path.basename(prior[-1]))
            continue
        else:
            ck('%s 已有备份但 sha 不吻合（说明已写过，须人工判）' % tag, False,
               '%s vs %s' % (ph, now8))
            continue
    dst = os.path.join(BD, 'before_r158_%s_%s%s' % (tag, STAMP, ext))
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)   # wx 独占
    with io.open(fd, 'w', encoding='utf-8', newline='') as f:
        f.write(raw)
    back = io.open(dst, encoding='utf-8', newline='').read()
    ck('%s 备份逐字节回读一致' % tag, back == raw, os.path.basename(dst))

print('\nFAILS=%d' % len(fails))
sys.exit(0 if not fails else 1)
