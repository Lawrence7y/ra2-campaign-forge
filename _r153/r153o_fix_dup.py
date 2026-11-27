#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R153 O：修 S-386（r153n 把锚点行又抄了一遍，致 S-382 条目重复两次）。

根因：r153n 的 A_RC 块**以锚点行本身开头**，而写法是 anchor + add ⇒ 锚点行出现两次。
同时我把幂等判据写成 `add[:32] not in t`，它**确实 FAIL 了却没中止**（只记录），于是写下去了。
⇒ 两条教训：① 幂等断言失败必须 `sys.exit`，不能只登记；
          ② 「插入块」不得以锚点行开头（应写成「锚点行 + \n + 纯新增内容」）。

本脚本：只删重复的那一份（保留第一份），并断言删后 S-382 条目恰 1 条。
"""
import hashlib
import os
import re
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC = os.path.join(D, 'R14_COMMON.md')
BAKDIR = os.path.join(D, 'R17_LEAD_BASELINE')

fail = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fail.append(n)
    return ok


DUP = ('- **S-382**：`r153h` 里把 `extra = set()` 当字典用，直接 `TypeError`；改 `dict` 后通过。\n'
       '  与前族同：断言里写进了本该被查询的量。\n')

raw = open(RC, 'rb').read()
ck('R14_COMMON CR == 1081', raw.count(b'\r') == 1081, raw.count(b'\r'))
t = raw.decode('utf-8')
n_dup = t.count(DUP)
print('重复块出现次数 = %d' % n_dup)
ck('重复块恰 2 次（可修）', n_dup == 2, n_dup)

# 只删第二次出现
i1 = t.find(DUP)
i2 = t.find(DUP, i1 + len(DUP))
ck('两次出现位置递增', 0 <= i1 < i2, (i1, i2))
t2 = t[:i2] + t[i2 + len(DUP):]
ck('删后重复块恰 1 次', t2.count(DUP) == 1, t2.count(DUP))

# 反控：只删了 DUP 长度那么多字节
ck('反控：字节数恰减 %d' % len(DUP.encode('utf-8')),
   len(t.encode('utf-8')) - len(t2.encode('utf-8')) == len(DUP.encode('utf-8')),
   len(t.encode('utf-8')) - len(t2.encode('utf-8')))
ck('反控：其它内容未动（把 DUP 补回可逐字节还原）',
   (t2[:i2] + DUP + t2[i2:]) == t)

bak = os.path.join(BAKDIR, 'R14_COMMON.md.before_r153o_%s.bak'
                   % time.strftime('%Y%m%d_%H%M%S'))
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
ck('备份 wx 创建', os.path.exists(bak))

open(RC, 'wb').write(t2.encode('utf-8'))
back = open(RC, 'rb').read()
ck('回读一致', back == t2.encode('utf-8'))
ck('回读 CR == 1081', back.count(b'\r') == 1081, back.count(b'\r'))

# 逐节复核：§2.158 仍在且末节仍是 158
tt = back.decode('utf-8')
ns = [int(x) for x in re.findall(r'(?m)^##\s+2\.(\d+)\b', tt)]
ck('节数 152 / 末节 158', len(ns) == 152 and max(ns) == 158, (len(ns), max(ns)))
ck('§2.158 内含 S-383..S-385 三条', all(('S-%d' % k) in tt for k in (383, 384, 385)))
ck('§2.158 内含 S-379..S-382 四条', all(('S-%d' % k) in tt for k in (379, 380, 381, 382)))
print('  §2.158 内「S-382」出现次数 = %d' % tt[tt.find('## 2.158'):].count('S-382'))

print('\nR14_COMMON 终态 %d B / sha %s'
      % (len(back), hashlib.sha256(back).hexdigest()[:16]))
print('\nFAIL %d：%s' % (len(fail), fail))
sys.exit(1 if fail else 0)
