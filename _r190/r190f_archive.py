#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R190 F：看板归档（269 >= 260 ⇒ 搬最早两段 R179 + R180 到 BOARD_ARCHIVE.md）。"""
import hashlib, io, os, sys, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BRD = os.path.join(TIER, 'STATUS_BOARD.md')
ARC = os.path.join(TIER, 'BOARD_ARCHIVE.md')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE')
stamp = time.strftime('%Y%m%d_%H%M%S')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
b0 = open(BRD, 'rb').read(); a0 = open(ARC, 'rb').read()
ck('A0 看板 CR == 0', b0.count(b'\r') == 0, b0.count(b'\r'))
ck('A1 归档 CR == 2952', a0.count(b'\r') == 2952, a0.count(b'\r'))
ck('A2 看板 %d 行 >= 260 ⇒ 必须归档' % b0.count(b'\n'), b0.count(b'\n') == 269, b0.count(b'\n'))
T = b0.decode('utf-8'); L = T.split('\n')
idx = [i for i, l in enumerate(L) if l.startswith('## ')]
ck('A3 段数 == 10', len(idx) == 10, len(idx))
ck('A4 首段 == R179、次段 == R180',
   'R17 第 179 轮' in L[idx[0]] and 'R17 第 180 轮' in L[idx[1]],
   (L[idx[0]][:34], L[idx[1]][:34]))
cut = idx[2]
moved = '\n'.join(L[idx[0]:cut]); keep = '\n'.join(L[cut:])
ck('A5 搬走两段共 %d 行、留下 %d 行' % (cut - idx[0], len(L) - cut),
   cut - idx[0] > 0 and len(L) - cut > 0, (cut - idx[0], len(L) - cut))
ck('A6 搬走的段标题恰两个', moved.count('\n## ') + (1 if moved.startswith('## ') else 0) == 2,
   moved.count('\n## '))
A = a0.decode('utf-8')
tn = len(a0) - len(a0.rstrip(b'\n'))
ck('A7a 归档尾部换行数实测 == 1', tn == 1, tn)
na = A.rstrip('\n') + '\n\n' + moved + '\n'
nb = keep
ck('A7 归档新体量按构造闭合', len(na.encode()) == len(a0) - tn + 2 + len(moved.encode()) + 1,
   (len(na.encode()), len(a0) - tn + 2 + len(moved.encode()) + 1))
ck('A8 归档 CR 保持 2952', na.count('\r') == 2952, na.count('\r'))
ck('A9 看板 CR 保持 0', nb.count('\r') == 0, nb.count('\r'))
ck('A10 看板剩余行数 150..259', 150 <= nb.count('\n') < 260, nb.count('\n'))
ck('A11 看板不再含 R179 / R180 段', 'R17 第 179 轮' not in nb and 'R17 第 180 轮' not in nb)
ck('A12 归档含 R179 / R180 段', 'R17 第 179 轮' in na and 'R17 第 180 轮' in na)
ck('A13 看板仍以 R189 段结尾', 'R17 第 189 轮' in nb.split('\n## ')[-1], nb.split('\n## ')[-1][:40])
ck('N1 反控：若 cut 取 idx[1] 则搬走行数 != 本次', (idx[1] - idx[0]) != (cut - idx[0]))
ck('N2 反控：keep 首行 == R182 段头', keep.startswith('## ') and 'R17 第 182 轮' in keep.split('\n')[0],
   keep.split('\n')[0][:40])
if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
print('== 写盘 ==')
for path, oldraw, newtxt in ((ARC, a0, na.encode()), (BRD, b0, nb.encode())):
    bak = os.path.join(BL, '%s.before_r190_arch_%s.bak' % (os.path.basename(path), stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(oldraw)
    ck('W1 %s 备份 sha 一致' % os.path.basename(path),
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == hashlib.sha256(oldraw).hexdigest())
    assert open(path, 'rb').read() == oldraw
    open(path, 'wb').write(newtxt)
    ck('W2 %s 回读一致' % os.path.basename(path),
       hashlib.sha256(open(path, 'rb').read()).hexdigest() == hashlib.sha256(newtxt).hexdigest())
print('归档 %d B / 看板 %d B / %d 行' % (len(na.encode()), len(nb.encode()), nb.count('\n')))
print('断言 %d 条，FAIL %d 条' % (n, len(fails)))
sys.exit(1 if fails else 0)
