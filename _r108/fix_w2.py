#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_w2.py —— 修 E-w2：上一稿 fix_w1.py 的替换命中了 R107 的 EI6 首条，不是 R108 的 EJ8

E-w2 事实（不粉饰）：
  fix_w1.py 用 '**自错 8 处，全部由断言当场抓住**' 作替换锚点，而 LEAD_LOCK 里该串
  **先出现在 R107 的 EI6**（第 4924 行），后出现在 R108 的 EJ8（第 5103 行）。
  `str.replace(..., 1)` 只替换第一处 ⇒ **R107 的 EI6 被从「8 处」改成「9 处」（错）**，
  而 R108 的 EJ8 仍是「8 处」（也错）。这正是「引用/修改前必须先核锚点唯一性」的反例。

E-w3 同时修：R108 自错条数本身也数错了。逐码清点：
  E-x1 E-x2 E-x3 E-x4（4） + E-y1 E-y2 E-y3（3） + E-z1 E-z2（2） + E-w1 E-w2（2） = **11 处**。
  此前 LEAD_LOCK 写 8、看板写 9、台账写 9（体例把 E-y2/E-y3 并成一行，按行数少算）。

本脚本：① R107 EI6 还原为「8 处」；② R108 EJ8 / 看板 / 台账 统一为「11 处」；
        ③ 每步 wx 独占备份 + 旧 CR 断言 + 回读校验，且**锚点必须全局唯一**才动。
"""
import hashlib, io, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
R14REL = 'lead/next_re_20261117_r14'
BASE = os.path.join(ROOT, R14REL, 'R17_LEAD_BASELINE')
TS = time.strftime('%Y%m%d_%H%M%S')
fails = []
def ck(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))
    if not c:
        fails.append(n)

# (path, old, new, expect_cr, min_count, max_count)
JOBS = [
    # ① 还原 R107 EI6
    ('lead/LEAD_LOCK',
     'EI6. 🐞 **自错 9 处，全部由断言当场抓住**（不隐去、不洗白）',
     'EI6. 🐞 **自错 8 处，全部由断言当场抓住**（不隐去、不洗白）', 137, 1, 1),
    # ② R108 §EJ8 → 11 处
    ('lead/LEAD_LOCK',
     'EJ8. 🐞 **自错 8 处，全部由断言当场抓住**',
     'EJ8. 🐞 **自错 11 处，全部由断言当场抓住**', 137, 1, 1),
    ('_r108/seg_lock_EJ.md',
     'EJ8. 🐞 **自错 9 处，全部由断言当场抓住**',
     'EJ8. 🐞 **自错 11 处，全部由断言当场抓住**', 0, 1, 1),
    ('lead/next_re_20261117_r14/STATUS_BOARD.md',
     '- 🐞 **自错 9 处（全部由断言抓住）**',
     '- 🐞 **自错 11 处（全部由断言抓住）**', 0, 1, 1),
    ('_r108/seg_board_108.md',
     '- 🐞 **自错 9 处（全部由断言抓住）**',
     '- 🐞 **自错 11 处（全部由断言抓住）**', 0, 1, 1),
    ('lead/GOAL_THREE_TARGETS_20261018.md',
     '**H. 自错 9 处（全部由断言当场抓住）**',
     '**H. 自错 11 处（全部由断言当场抓住）**', 337, 1, 1),
    ('_r108/seg_ledger_1162.md',
     '**H. 自错 9 处（全部由断言当场抓住）**',
     '**H. 自错 11 处（全部由断言当场抓住）**', 0, 1, 1),
]
for ji, (path, old, new, ecr, mn, mx) in enumerate(JOBS):
    t = io.open(path, encoding='utf-8', newline='').read()
    n = t.count(old)
    ck('%s 锚点 %r 出现 %d 次（要求 %d..%d，锚点必须唯一）'
       % (path.split('/')[-1], old[:28], n, mn, mx), mn <= n <= mx, n)
    if not (mn <= n <= mx):
        continue
    old_b = io.open(path, 'rb').read()
    ck('%s CR 前置 %d' % (path.split('/')[-1], ecr), old_b.count(b'\r\n') == ecr,
       old_b.count(b'\r\n'))
    newt = t.replace(old, new, 1)
    ck('%s 替换后新串出现、旧串消失' % path.split('/')[-1],
       new in newt and newt.count(old) == n - 1)
    if not path.startswith('_r108'):
        # E-w4：首稿备份名只含 basename+时间戳，同一文件的两处改动会撞名（EEXIST 崩在第二处）。
        # 备份名必须带作业序号。
        bl = os.path.join(BASE, '%s.before_R108_EW2_j%d_%s.bak'
                          % (os.path.basename(path), ji, TS))
        fd = os.open(bl, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        try:
            os.write(fd, old_b)
        finally:
            os.close(fd)
        ck('%s 备份独占且逐字节同' % path.split('/')[-1],
           hashlib.sha256(io.open(bl, 'rb').read()).digest()
           == hashlib.sha256(old_b).digest(), os.path.basename(bl))
    with io.open(path, 'wb') as f:
        f.write(newt.encode('utf-8'))
    back = io.open(path, 'rb').read()
    ck('%s 回读逐字节一致' % path.split('/')[-1], back == newt.encode('utf-8'))
    ck('%s CR 保持 %d' % (path.split('/')[-1], ecr), back.count(b'\r\n') == ecr,
       back.count(b'\r\n'))

# 终检：R107 EI6 = 8，R108 EJ8 = 11，全局无「自错 9 处」
t = io.open('lead/LEAD_LOCK', encoding='utf-8', newline='').read()
ck('R107 EI6 已还原为 8 处', 'EI6. 🐞 **自错 8 处' in t)
ck('R108 EJ8 = 11 处', 'EJ8. 🐞 **自错 11 处' in t)
ck('LEAD_LOCK 无「自错 9 处」残留', '自错 9 处' not in t)
print('FAILS', len(fails), fails)
sys.exit(1 if fails else 0)
