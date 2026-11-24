#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_w7_final.py —— 追加 E-w7 并把自错条数改成真值 16，随后**在全部文本写入之后**再刷新收口字节数

顺序很关键（这正是 E-w7 的教训）：文本改动会改变字节数，故收口数字必须最后取。
本脚本分两阶段：
  阶段 A：把 E-w7 行插进四个文件的自错段，标题 15 -> 16。
  阶段 B：直读盘上终值，替换 §2.112.9 的字节串（等宽数字，不改变文件长度）。
  阶段 C：终检 —— R14_COMMON 里声明的字节串 == 盘上实际值。
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

W7 = ('E-w7 §2.112.9 收口的字节数是在追加 E-w1..E-w6 **之前**取的，追加后即过期 —— '
      '收口数字必须在所有写入完成之后取，不能边写边填。')
# ---------------- 阶段 A ----------------
AP = [
    ('lead/LEAD_LOCK', 137,
     'E-w6 §2.112 初稿只写 2.112.1..2.112.7，缺了 §2.111 体例里必有的「自错」「收口」两节（没先对齐上一节骨架）。',
     '\n' + W7,
     'EJ8. 🐞 **自错 15 处，全部由断言当场抓住**',
     'EJ8. 🐞 **自错 16 处，全部由断言当场抓住**'),
    ('lead/GOAL_THREE_TARGETS_20261018.md', 337,
     'E-w6 §2.112 初稿只写 2.112.1..2.112.7，缺了 §2.111 体例里必有的「自错」「收口」两节（没先对齐上一节骨架）。',
     '\n' + W7,
     '**H. 自错 15 处（全部由断言当场抓住）**',
     '**H. 自错 16 处（全部由断言当场抓住）**'),
    ('lead/next_re_20261117_r14/STATUS_BOARD.md', 0,
     '  E-w6 §2.112 初稿只写 2.112.1..2.112.7，缺了 §2.111 体例里必有的「自错」「收口」两节（没先对齐上一节骨架）。',
     '\n  ' + W7,
     '- 🐞 **自错 15 处（全部由断言抓住）**',
     '- 🐞 **自错 16 处（全部由断言抓住）**'),
    ('lead/next_re_20261117_r14/R14_COMMON.md', 1081,
     '| E-w6 | §2.112 初稿只写 2.112.1..2.112.7，缺了 §2.111 体例里必有的「自错」「收口」两节（没先对齐上一节骨架） | 收口复核对齐体例时发现 |',
     '\n| E-w7 | §2.112.9 收口的字节数在追加 E-w1..E-w6 **之前**取，追加后即过期 —— 收口数字必须在所有写入完成之后取 | 终检比对盘上实际字节数发现 |',
     '### 2.112.8 自错 15 处（全部由断言当场抓住，不隐去、不洗白）',
     '### 2.112.8 自错 16 处（全部由断言当场抓住，不隐去、不洗白）'),
]
for ji, (p, ecr, anchor, ins, oh, nh) in enumerate(AP):
    t = io.open(p, encoding='utf-8', newline='').read()
    ck('%s 锚点/标题各唯一' % p, t.count(anchor) == 1 and t.count(oh) == 1,
       (t.count(anchor), t.count(oh)))
    if t.count(anchor) != 1 or t.count(oh) != 1:
        continue
    old_b = io.open(p, 'rb').read()
    ck('%s CR 前置 %d' % (p, ecr), old_b.count(b'\r\n') == ecr, old_b.count(b'\r\n'))
    new = t.replace(anchor, anchor + ins, 1).replace(oh, nh, 1)
    ck('%s 含 E-w7 且标题 16' % p, 'E-w7' in new and nh in new)
    bl = os.path.join(BASE, '%s.before_R108_EW7F_j%d_%s.bak'
                      % (os.path.basename(p), ji, TS))
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

# 段文件同步（不影响盘上正式文件长度）
SEGS = [('_r108/seg_lock_EJ.md',
         'E-w6 §2.112 初稿只写 2.112.1..2.112.7，缺了 §2.111 体例里必有的「自错」「收口」两节（没先对齐上一节骨架）。',
         '\n' + W7, 'EJ8. 🐞 **自错 15 处，全部由断言当场抓住**',
         'EJ8. 🐞 **自错 16 处，全部由断言当场抓住**'),
        ('_r108/seg_ledger_1162.md',
         'E-w6 §2.112 初稿只写 2.112.1..2.112.7，缺了 §2.111 体例里必有的「自错」「收口」两节（没先对齐上一节骨架）。',
         '\n' + W7, '**H. 自错 15 处（全部由断言当场抓住）**',
         '**H. 自错 16 处（全部由断言当场抓住）**'),
        ('_r108/seg_board_108.md',
         '  E-w6 §2.112 初稿只写 2.112.1..2.112.7，缺了 §2.111 体例里必有的「自错」「收口」两节（没先对齐上一节骨架）。',
         '\n  ' + W7, '- 🐞 **自错 15 处（全部由断言抓住）**',
         '- 🐞 **自错 16 处（全部由断言抓住）**')]
for p, anchor, ins, oh, nh in SEGS:
    t = io.open(p, encoding='utf-8', newline='').read()
    if t.count(anchor) != 1 or t.count(oh) != 1:
        ck('%s 锚点唯一' % p, False, (t.count(anchor), t.count(oh)))
        continue
    with io.open(p, 'wb') as f:
        f.write(t.replace(anchor, anchor + ins, 1).replace(oh, nh, 1).encode('utf-8'))
    ck('%s 段同步含 E-w7' % p,
       'E-w7' in io.open(p, encoding='utf-8', newline='').read())

# ---------------- 阶段 B ----------------
FILES = [('lead/next_re_20261117_r14/R14_COMMON.md', 1081),
         ('lead/LEAD_LOCK', 137),
         ('lead/GOAL_THREE_TARGETS_20261018.md', 337),
         ('lead/next_re_20261117_r14/STATUS_BOARD.md', 0),
         ('lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 2952)]
REAL = []
for p, ecr in FILES:
    b = io.open(p, 'rb').read()
    REAL.append(len(b))
    ck('%s CR %d（终值取样前）' % (p, ecr), b.count(b'\r\n') == ecr, b.count(b'\r\n'))
NEW = '字节 %s / %s / %s / %s / %s' % tuple('{:,}'.format(x) for x in REAL)
import re
P = 'lead/next_re_20261117_r14/R14_COMMON.md'
t = io.open(P, encoding='utf-8', newline='').read()
m = re.search(r'字节 [\d,]+ / [\d,]+ / [\d,]+ / [\d,]+ / [\d,]+', t)
ck('收口字节串可定位且唯一', m is not None and t.count(m.group(0)) == 1,
   m.group(0) if m else None)
if m and t.count(m.group(0)) == 1:
    ck('新串与旧串等宽（替换后长度不变）', len(NEW) == len(m.group(0)),
       (len(m.group(0)), len(NEW)))
    old_b = io.open(P, 'rb').read()
    for seg in ('_r108/seg_rc_2112.md',):
        s = io.open(seg, encoding='utf-8', newline='').read()
        if m.group(0) in s:
            with io.open(seg, 'wb') as f:
                f.write(s.replace(m.group(0), NEW, 1).encode('utf-8'))
    with io.open(P, 'wb') as f:
        f.write(t.replace(m.group(0), NEW, 1).encode('utf-8'))
    back = io.open(P, 'rb').read()
    ck('R14_COMMON 回读一致且 CR 1081',
       back.count(b'\r\n') == 1081 and len(back) == len(old_b), (len(old_b), len(back)))

# ---------------- 阶段 C ----------------
t = io.open(P, encoding='utf-8', newline='').read()
REAL2 = [len(io.open(p, 'rb').read()) for p, _ in FILES]
ck('终检：§2.112.9 声明的字节数 == 盘上实际值',
   NEW in t and NEW == '字节 %s / %s / %s / %s / %s'
   % tuple('{:,}'.format(x) for x in REAL2), NEW)
ck('四件套 CR 全绿', all(io.open(p, 'rb').read().count(b'\r\n') == e for p, e in FILES))
print('FAILS', len(fails), fails)
sys.exit(1 if fails else 0)
