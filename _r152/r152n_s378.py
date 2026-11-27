#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R152 N：登记第 7 条自错 S-378（r152l 非幂等，重跑把 S-377 条目插了两遍；已由 r152m 去重）。"""
import os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC = os.path.join(D, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(D, 'STATUS_BOARD.md')
BAKDIR = os.path.join(D, 'R17_LEAD_BASELINE')
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


def rw(p, cr, pairs):
    raw = open(p, 'rb').read()
    ck('%s pre CR %d' % (os.path.basename(p), cr), raw.count(b'\r') == cr, raw.count(b'\r'))
    t = raw.decode('utf-8')
    for a, b in pairs:
        ck('%s 锚点唯一 %.30s' % (os.path.basename(p), a), t.count(a) == 1, t.count(a))
    bak = os.path.join(BAKDIR, os.path.basename(p) + '.before_r152n_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    for a, b in pairs:
        t = t.replace(a, b)
    open(p, 'wb').write(t.encode('utf-8'))
    back = open(p, 'rb').read()
    ck('%s 回读一致 / CR %d' % (os.path.basename(p), cr),
       back == t.encode('utf-8') and back.count(b'\r') == cr, back.count(b'\r'))


S378_RC = ('\n- **S-378**：`r152l` 本身**非幂等** —— 我为了修「S-377 条目出现 2 次」这个断言而重跑了一次，'
           '结果它又把同一条插了第二遍（`r152m` 才去重成功）。⇒ 这是**连续两次同族错**：'
           'S-377 是「产物里写了会变的量」，S-378 是「修数据用的脚本不能重复运行」。'
           '修法：所有落盘脚本都要先判「目标串是否已存在」，存在则跳过而不是再插一遍。')

rw(RC, 1081, [('而**我自己产物的生成时刻**（与 S-362/S-364「脚本依赖自己刚写下的文本」同族）。',
               '而**我自己产物的生成时刻**（与 S-362/S-364「脚本依赖自己刚写下的文本」同族）。' + S378_RC),
              ('### 九 · 自错 S-372..S-377（六条，两条方向错）',
               '### 九 · 自错 S-372..S-378（七条，两条方向错）')])

rw(LOCK, 137, [('**六条全是判据/口径缺陷，无一条数据错。**',
                '**S-378**：`r152l` **非幂等** —— 我为修「S-377 条目出现 2 次」这条断言而重跑，'
                '它又把同一条插了第二遍（`r152m` 才去重）。⇒ 连续两次同族：S-377 是「产物里写了会变的量」，'
                'S-378 是「修数据用的脚本不能重复运行」。修法：落盘脚本一律先判目标串是否已存在。'
                '**七条全是判据/口径缺陷，无一条数据错。**'),
               ('OJ9. 🔴 **自错 S-372..S-377（六条，两条方向错，无一条数据错）.**',
                'OJ9. 🔴 **自错 S-372..S-378（七条，两条方向错，无一条数据错）.**')])

rw(LED, 337, [('**六条无一条是数据错。**',
               '**S-378**（`r152l` **非幂等**：为修「S-377 条目出现 2 次」而重跑，结果又插了第二遍，'
               '`r152m` 才去重；落盘脚本一律先判目标串是否已存在）。**七条无一条是数据错。**'),
              ('### 八 · 自错六条', '### 八 · 自错七条')])

rw(BRD, 0, [('`r152d` 改成「记录已存在即冻结」+ 冻结分支断言本次实测与记录逐项相同。',
             '`r152d` 改成「记录已存在即冻结」+ 冻结分支断言本次实测与记录逐项相同。'
             '**S-378** `r152l` **非幂等** —— 为修「S-377 条目出现 2 次」而重跑，结果又插了一遍'
             '（`r152m` 去重成功）⇒ 连续两次同族：S-377 是「产物里写了会变的量」，S-378 是'
             '「修数据的脚本不能重复运行」；落盘脚本一律先判目标串是否已存在。'),
            ('### 十 · 自错 S-372..S-377（六条，两条方向错，无一条数据错）',
             '### 十 · 自错 S-372..S-378（七条，两条方向错，无一条数据错）')])

print('\nFAILS:', fails if fails else 'none')
sys.exit(1 if fails else 0)
