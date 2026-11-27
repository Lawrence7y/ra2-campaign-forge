#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R152 O：补 R14_COMMON §2.157 的 S-378 条目（r152n 的锚点差一个「是」字，未插入；标题已改）。

幂等：目标串已存在则跳过插入。
"""
import os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC = os.path.join(D, 'R14_COMMON.md')
BAKDIR = os.path.join(D, 'R17_LEAD_BASELINE')
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


raw = open(RC, 'rb').read()
ck('pre CR 1081', raw.count(b'\r') == 1081, raw.count(b'\r'))
t = raw.decode('utf-8')
MARK = '- **S-378**：'
ANCHOR = '- **S-377（产物自指）**'
i = t.find(ANCHOR)
ck('S-377 条目存在', i >= 0, i)
j = t.find('\n', i)
ck('S-377 条目为单行', j > i, (i, j))
S378 = ('\n- **S-378**：`r152l` 本身**非幂等** —— 我为了修「S-377 条目出现 2 次」这条断言而重跑一次，'
        '结果它又把同一条插了第二遍（`r152m` 才去重成功）。⇒ 连续两次同族错：'
        'S-377 是「产物里写了会变的量」，S-378 是「修数据用的脚本不能重复运行」。'
        '修法：所有落盘脚本先判「目标串是否已存在」，存在则跳过而不是再插一遍。')
if MARK in t:
    print('  SKIP 已存在 S-378 条目，不重复插入，直接退出（不写盘、不备份）')
    ck('S-378 条目恰 1 条', t.count(MARK) == 1, t.count(MARK))
    print('\nFAILS:', fails if fails else 'none')
    sys.exit(1 if fails else 0)
t = t[:j] + S378 + t[j:]
ck('插入后 S-378 条目恰 1 条', t.count(MARK) == 1, t.count(MARK))
ck('S-377 条目仍恰 1 条', t.count(ANCHOR) == 1, t.count(ANCHOR))
bak = os.path.join(BAKDIR, 'R14_COMMON.md.before_r152o_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
open(RC, 'wb').write(t.encode('utf-8'))
back = open(RC, 'rb').read()
ck('回读一致 / CR 1081', back == t.encode('utf-8') and back.count(b'\r') == 1081, back.count(b'\r'))
print('\nFAILS:', fails if fails else 'none')
sys.exit(1 if fails else 0)
