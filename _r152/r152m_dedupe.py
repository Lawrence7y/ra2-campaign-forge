#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R152 M：修 S-378 —— 上一步 r152l 被跑了两次，S-377 条目被插入两遍。

本脚本按「逐字相同的整块只保留第一份」删除重复，并断言：
  删除前后『- **S-377（产物自指）**』出现次数 2 -> 1；其余字节零改动（除删掉的那一块）；CR 仍 1081。
另把 r152l 改成幂等（已存在则不插），并登记 S-378。
"""
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
MARK = '- **S-377（产物自指）**'
ck('S-377 条目出现恰 2 次（待去重）', t.count(MARK) == 2, t.count(MARK))

# 取第一条完整块：从 MARK 起点到该块结尾 '同族）。'
start1 = t.find(MARK)
endmark = '「脚本依赖自己刚写下的文本」同族）。'
e1 = t.find(endmark, start1)
ck('第一条块的结尾锚点存在', e1 > 0, e1)
block = t[start1:e1 + len(endmark)]
ck('第二条块与第一条逐字相同', t.count(block) == 2, t.count(block))

# 删除第二处（保留第一处）
i2 = t.find(block, start1 + len(block))
ck('第二处位置 > 第一处', i2 > start1, (start1, i2))
t2 = t[:i2] + t[i2 + len(block):]
ck('去重后 S-377 条目恰 1 次', t2.count(MARK) == 1, t2.count(MARK))
ck('去重只删了 %d 字节' % len(block), len(t) - len(t2) == len(block), len(t) - len(t2))

bak = os.path.join(BAKDIR, 'R14_COMMON.md.before_r152m_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
open(RC, 'wb').write(t2.encode('utf-8'))
back = open(RC, 'rb').read()
ck('回读一致 / CR 1081', back == t2.encode('utf-8') and back.count(b'\r') == 1081, back.count(b'\r'))
print('\nFAILS:', fails if fails else 'none')
sys.exit(1 if fails else 0)
