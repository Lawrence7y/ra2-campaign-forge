#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_w5.py —— 补 E-w5 并把自错条数改成真值 14

E-w5：上一稿 fix_w34.py 的 JOBS 表给 lock/台账 两支只挂了 W2 一条插入文本，
     而同一脚本的断言要求 E-w2/W3/W4 三条都在 ⇒ 该断言 FAIL 4；
     断言本身是对的（它抓住了我表里少挂的两条），缺的是文本。

逐码终值：
  E-x1 E-x2 E-x3 E-x4（4）
  E-y1 E-y2 E-y3（3）
  E-z1 E-z2（2）
  E-w1 E-w2 E-w3 E-w4 E-w5（5）
  ⇒ **14 条**。
"""
import hashlib, io, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
BASE = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_LEAD_BASELINE')
TS = time.strftime('%Y%m%d_%H%M%S')
fails = []
def ck(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))
    if not c:
        fails.append(n)

W5 = ('E-w5 上一稿 JOBS 表给 lock/台账 两支只挂了 E-w2 一条插入文本，而同脚本断言要求三条齐备 ⇒ FAIL 4；'
      '断言是对的（它抓住了表里少挂的两条），缺的是文本。')

JOBS = [
    # path, CR, 插入锚点(全串唯一), 插入体, 旧标题, 新标题
    ('lead/LEAD_LOCK', 137,
     'E-w4 备份文件名只含 basename + 时间戳，同一文件的两处改动落在同一秒 ⇒ `O_EXCL` 第二次直接 EEXIST 崩掉半个作业；备份名必须带作业序号。',
     'EJ8. 🐞 **自错 13 处，全部由断言当场抓住**',
     'EJ8. 🐞 **自错 14 处，全部由断言当场抓住**'),
    ('_r108/seg_lock_EJ.md', 0,
     'E-w4 备份文件名只含 basename + 时间戳，同一文件的两处改动落在同一秒 ⇒ `O_EXCL` 第二次直接 EEXIST 崩掉半个作业；备份名必须带作业序号。',
     'EJ8. 🐞 **自错 13 处，全部由断言当场抓住**',
     'EJ8. 🐞 **自错 14 处，全部由断言当场抓住**'),
    ('lead/next_re_20261117_r14/STATUS_BOARD.md', 0,
     '  E-w4 备份文件名只含 basename + 时间戳，同一文件的两处改动落在同一秒 ⇒ `O_EXCL` 第二次直接 EEXIST 崩掉半个作业；备份名必须带作业序号。',
     '- 🐞 **自错 13 处（全部由断言抓住）**',
     '- 🐞 **自错 14 处（全部由断言抓住）**'),
    ('_r108/seg_board_108.md', 0,
     '  E-w4 备份文件名只含 basename + 时间戳，同一文件的两处改动落在同一秒 ⇒ `O_EXCL` 第二次直接 EEXIST 崩掉半个作业；备份名必须带作业序号。',
     '- 🐞 **自错 13 处（全部由断言抓住）**',
     '- 🐞 **自错 14 处（全部由断言抓住）**'),
    ('lead/GOAL_THREE_TARGETS_20261018.md', 337,
     'E-w4 备份文件名只含 basename + 时间戳，同一文件的两处改动落在同一秒 ⇒ `O_EXCL` 第二次直接 EEXIST 崩掉半个作业；备份名必须带作业序号。',
     '**H. 自错 13 处（全部由断言当场抓住）**',
     '**H. 自错 14 处（全部由断言当场抓住）**'),
    ('_r108/seg_ledger_1162.md', 0,
     'E-w4 备份文件名只含 basename + 时间戳，同一文件的两处改动落在同一秒 ⇒ `O_EXCL` 第二次直接 EEXIST 崩掉半个作业；备份名必须带作业序号。',
     '**H. 自错 13 处（全部由断言当场抓住）**',
     '**H. 自错 14 处（全部由断言当场抓住）**'),
]
for ji, (path, ecr, anchor, oldh, newh) in enumerate(JOBS):
    t = io.open(path, encoding='utf-8', newline='').read()
    ck('%s W4 行唯一' % path, t.count(anchor) == 1, t.count(anchor))
    ck('%s 标题 13 唯一' % path, t.count(oldh) == 1, t.count(oldh))
    ck('%s 尚无 W5' % path, 'E-w5 ' not in t)
    old_b = io.open(path, 'rb').read()
    ck('%s CR 前置 %d' % (path, ecr), old_b.count(b'\r\n') == ecr, old_b.count(b'\r\n'))
    ins = ('\n  ' + W5) if path.endswith('.md') and 'STATUS_BOARD' in path or path.endswith('seg_board_108.md') else ('\n' + W5)
    new = t.replace(anchor, anchor + ins, 1).replace(oldh, newh, 1)
    ck('%s W1..W5 齐备且标题 14' % path,
       all(('E-w%d ' % k) in new for k in range(1, 6)) and newh in new)
    if not path.startswith('_r108'):
        bl = os.path.join(BASE, '%s.before_R108_EW5_j%d_%s.bak'
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
# 终检
t = io.open('lead/LEAD_LOCK', encoding='utf-8', newline='').read()
ck('R107 EI6 仍为 8 处', 'EI6. 🐞 **自错 8 处' in t)
ck('R108 EJ8 为 14 处', 'EJ8. 🐞 **自错 14 处' in t)
ck('LEAD_LOCK 无 9/11/13 残留', not any(('自错 %d 处' % x) in t for x in (9, 11, 13)))
print('FAILS', len(fails), fails)
sys.exit(1 if fails else 0)
