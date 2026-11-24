#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_w7.py —— E-w7：§2.112.9 收口里写的字节数已过期（那是写入 E-w1..E-w6 之前的值）

E-w7 事实：我先写完 §2.112.9 的收口字节数（896,329 / 680,774 / 4,901,826 / 35,327），
随后又追加了 E-w1..E-w6 六条，字节数随之变化；收口段落里的数字就成了**当时值**而非**终值**。
根因：收口数字必须在**所有写入完成之后**取，不能边写边填。

本脚本：直读盘上终值 -> 精确替换 §2.112.9 里的字节串 -> 回读校验。
"""
import hashlib, io, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
BASE = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_LEAD_BASELINE')
TS = time.strftime('%Y%m%d_%H%M%S')
FILES = [('lead/next_re_20261117_r14/R14_COMMON.md', 1081),
         ('lead/LEAD_LOCK', 137),
         ('lead/GOAL_THREE_TARGETS_20261018.md', 337),
         ('lead/next_re_20261117_r14/STATUS_BOARD.md', 0),
         ('lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 2952)]
REAL = []
for p, ecr in FILES:
    b = io.open(p, 'rb').read()
    REAL.append(len(b))
    assert b.count(b'\r\n') == ecr, p
print('终值字节', REAL)

OLD = '字节 896,329 / 680,774 / 4,901,826 / 35,327 / 863,251'
NEW = '字节 %s / %s / %s / %s / %s' % tuple('{:,}'.format(x) for x in REAL)
print('替换为', NEW)

fails = []
def ck(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))
    if not c:
        fails.append(n)

JOBS = [('lead/next_re_20261117_r14/R14_COMMON.md', 1081),
        ('_r108/seg_rc_2112.md', 0)]
for ji, (p, ecr) in enumerate(JOBS):
    t = io.open(p, encoding='utf-8', newline='').read()
    ck('%s 旧字节串唯一' % p, t.count(OLD) == 1, t.count(OLD))
    if t.count(OLD) != 1:
        continue
    old_b = io.open(p, 'rb').read()
    ck('%s CR 前置 %d' % (p, ecr), old_b.count(b'\r\n') == ecr, old_b.count(b'\r\n'))
    new = t.replace(OLD, NEW, 1)
    if not p.startswith('_r108'):
        bl = os.path.join(BASE, '%s.before_R108_EW7_%s.bak'
                          % (os.path.basename(p), TS))
        fd = os.open(bl, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        try:
            os.write(fd, old_b)
        finally:
            os.close(fd)
        ck('%s 备份独占同哈希' % p,
           hashlib.sha256(io.open(bl, 'rb').read()).digest()
           == hashlib.sha256(old_b).digest(), os.path.basename(bl))
    with io.open(p, 'wb') as f:
        f.write(new.encode('utf-8'))
    back = io.open(p, 'rb').read()
    ck('%s 回读一致 CR %d' % (p, ecr),
       back == new.encode('utf-8') and back.count(b'\r\n') == ecr, back.count(b'\r\n'))

# 终检：R14_COMMON §2.112.9 里的字节串与盘上一致
t = io.open('lead/next_re_20261117_r14/R14_COMMON.md', encoding='utf-8', newline='').read()
ck('R14_COMMON §2.112.9 字节串 == 盘上终值', NEW in t)
ck('旧字节串已无残留（全局）', all(OLD not in io.open(p, encoding='utf-8', newline='').read()
                              for p, _ in JOBS))
print('FAILS', len(fails), fails)
sys.exit(1 if fails else 0)
