#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r182j_c20_v3_neutral.py —— 把 C20 边界注释里最后一处可陈旧版本号（V564）改成版本中性。

理由不是审美：该行是「建 V564 目录但不改指针 ⇒ 三门全绿」的实测记录，
但写成具体版本号后，下一次升到 V564 时它会**静默变成事实错误**（那时 V564 已是当前版）。
与审计 B4 指出的 1179 行同族。改为「建一个更高版本号的目录」。
"""
import hashlib, io, os, shutil, sys, tempfile
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(TIER, 'check_disc.py')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE')
OLD_SHA = 'b266a97fa703bb84728e73aa6e7f3b196be90e9c1824767f9dd021859eed9afc'
OLD_BYTES = 75262
fails = []
def ck(n, c, d=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)
    return c
def sha(b): return hashlib.sha256(b).hexdigest()

raw = open(GATE, 'rb').read()
ck('A0 旧 sha 命中', sha(raw) == OLD_SHA, sha(raw)[:16])
ck('A1 旧字节命中', len(raw) == OLD_BYTES, len(raw))
if fails: sys.exit(1)
src = raw.decode('utf-8')
O = '# 建 V564 目录但不改任何指针'
N = '# 建一个更高版本号的目录（复制现版台账）但不改任何指针'
ck('B1 锚点唯一', src.count(O) == 1, src.count(O))
new = src.replace(O, N, 1)
nb = new.encode('utf-8')
ck('B2 CR 0', nb.count(b'\r') == 0)
import re
blk = new[new.index('# ---- C20 [R182 新增]'):new.index('# ---- C5 CR 抽查 ----')]
ck('B3 C20 块内 V<数字> 归零（版本中性）', len(re.findall(r'V\d+', blk)) == 0,
   re.findall(r'V\d+', blk))
tmpd = tempfile.mkdtemp(prefix='r182j_')
try:
    sp = os.path.join(tmpd, 'c.py')
    io.open(sp, 'w', encoding='utf-8', newline='').write(new)
    import py_compile
    try:
        py_compile.compile(sp, doraise=True, cfile=os.path.join(tmpd, 'x.pyc'))
        ck('C1 语法通过', True)
    except Exception as e:
        ck('C1 语法通过', False, e)
finally:
    shutil.rmtree(tmpd, ignore_errors=True)
if fails: sys.exit(1)
bak = os.path.join(BL, 'check_disc.py.before_r182_C20v3_%s.bak' % sha(raw)[:12])
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
ck('D1 独占备份', os.path.exists(bak), os.path.basename(bak))
with open(GATE, 'wb') as f:
    f.write(nb)
back = open(GATE, 'rb').read()
ck('D2 回读一致', sha(back) == sha(nb))
print('NEW_SHA=%s' % sha(back)); print('NEW_BYTES=%d' % len(back))
print('[exit 0]' if not fails else 'FAILED %r' % (fails,))
