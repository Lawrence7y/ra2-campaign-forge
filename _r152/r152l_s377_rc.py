#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R152 L：R14_COMMON §2.157 补 S-377（上一步只改了标题的「六条」，未补条目）。"""
import hashlib, os, sys, time

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
ANCHOR = '**不是数据错、是断言取字段取错**。'
ck('S-376 段尾锚点唯一', t.count(ANCHOR) == 1, t.count(ANCHOR))
S377 = ('\n- **S-377（产物自指）**：`r152d` 首版把 `measured_at` 设成「每次运行取当前时刻」，'
        '而 `r152e` 用它生成 v5.41 ⇒ 我在终态校验里改脚本后重跑了一次，'
        '**v5.41 的 sha 与正文钉值同时漂移**（`b56f8c28…` / `20:51:21Z` 变成 `f31c8fdc…` / `20:54:16Z`）。'
        '修法：`r152d` 改成「记录文件已存在即冻结复用」，并在冻结分支断言「本次实测与冻结记录逐项相同」。'
        '⇒ 病根仍是「把一个会变的量写进产物」，但这次会变的不是被查询的值，'
        '而是**我自己产物的生成时刻**（与 S-362/S-364「脚本依赖自己刚写下的文本」同族）。')
bak = os.path.join(BAKDIR, 'R14_COMMON.md.before_r152l_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
t2 = t.replace(ANCHOR, ANCHOR + S377)
ck('内容变化', t2 != t)
open(RC, 'wb').write(t2.encode('utf-8'))
back = open(RC, 'rb').read()
ck('回读一致 / CR 1081', back == t2.encode('utf-8') and back.count(b'\r') == 1081, back.count(b'\r'))
ck('S-377 条目恰 1 条（区分标题里的区间串）',
   back.decode('utf-8').count('- **S-377（产物自指）**') == 1,
   back.decode('utf-8').count('- **S-377（产物自指）**'))
print('\nFAILS:', fails if fails else 'none')
sys.exit(1 if fails else 0)
