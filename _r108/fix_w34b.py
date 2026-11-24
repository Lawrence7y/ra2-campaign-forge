#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_w34b.py —— 补上 lock/台账 里漏掉的 E-w3 / E-w4 两条（E-w5：上一稿 JOBS 表里
这两处只挂了 W2 一条，断言却要求三条都在，故 FAIL 4 —— 断言抓到了，不是运气）。

四个文件（LEAD_LOCK / seg_lock_EJ / 台账 / seg_ledger_1162）在 E-w2 行后各追加 E-w3、E-w4。
"""
import hashlib, io, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
BASE = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_LEAD_BASELINE')
TS = time.strftime('%Y%m%d_%H%M%S')
W3 = ('E-w3 「自错几处」本身数错了两次（先写 8、后写 9），根因是按**行**数而不是按**条**数 '
      '（台账体例把 E-y2/E-y3 并成一行）⇒ 逐码清点后真值是 **13 条**。')
W4 = ('E-w4 备份文件名只含 basename + 时间戳，同一文件的两处改动落在同一秒 ⇒ '
      '`O_EXCL` 第二次直接 EEXIST 崩掉半个作业；备份名必须带作业序号。')

fails = []
def ck(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))
    if not c:
        fails.append(n)

W2MARK = '已用带段号的全串锚点改回（R107 EI6 还原 8 处、R108 EJ8 改为真值）。'
JOBS = [('lead/LEAD_LOCK', 137), ('_r108/seg_lock_EJ.md', 0),
        ('lead/GOAL_THREE_TARGETS_20261018.md', 337), ('_r108/seg_ledger_1162.md', 0)]
for ji, (path, ecr) in enumerate(JOBS):
    t = io.open(path, encoding='utf-8', newline='').read()
    ck('%s W2 标记唯一' % path, t.count(W2MARK) == 1, t.count(W2MARK))
    ck('%s 尚无 W3' % path, 'E-w3 ' not in t)
    old_b = io.open(path, 'rb').read()
    ck('%s CR 前置 %d' % (path, ecr), old_b.count(b'\r\n') == ecr, old_b.count(b'\r\n'))
    new = t.replace(W2MARK, W2MARK + '\n' + W3 + '\n' + W4, 1)
    ck('%s 三条齐备' % path, all(k in new for k in ('E-w2 ', 'E-w3 ', 'E-w4 ')))
    if not path.startswith('_r108'):
        bl = os.path.join(BASE, '%s.before_R108_EW34b_j%d_%s.bak'
                          % (os.path.basename(path), ji, TS))
        fd = os.open(bl, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        try:
            os.write(fd, old_b)
        finally:
            os.close(fd)
        ck('%s 备份独占同哈希' % path,
           hashlib.sha256(io.open(bl, 'rb').read()).digest()
           == hashlib.sha256(old_b).digest(), os.path.basename(bl))
    with io.open(path, 'wb') as f:
        f.write(new.encode('utf-8'))
    back = io.open(path, 'rb').read()
    ck('%s 回读一致 CR %d' % (path, ecr),
       back == new.encode('utf-8') and back.count(b'\r\n') == ecr, back.count(b'\r\n'))
print('FAILS', len(fails), fails)
sys.exit(1 if fails else 0)
