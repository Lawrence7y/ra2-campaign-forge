#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R187 B：看板归档（271 >= 260 ⇒ 搬最早两段 R175 + R176 到 BOARD_ARCHIVE.md）。"""
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
ck('B0 看板 CR == 0', b0.count(b'\r') == 0, b0.count(b'\r'))
ck('B1 归档 CR == 2952', a0.count(b'\r') == 2952, a0.count(b'\r'))
ck('B2 看板 271 行 >= 260 ⇒ 必须归档', b0.count(b'\n') == 271, b0.count(b'\n'))

T = b0.decode('utf-8'); L = T.split('\n')
idx = [i for i, l in enumerate(L) if l.startswith('## ')]
ck('B3 看板首段 == R175、次段 == R176', 'R17 第 175 轮' in L[idx[0]] and 'R17 第 176 轮' in L[idx[1]],
   (L[idx[0]][:40], L[idx[1]][:40]))
cut = idx[2]
moved = '\n'.join(L[idx[0]:cut])
keep = '\n'.join(L[cut:])
ck('B4 搬走两段共 %d 行、留下 %d 行' % (cut - idx[0], len(L) - cut),
   cut - idx[0] > 0 and len(L) - cut > 0, (cut - idx[0], len(L) - cut))
ck('B5 搬走的段标题恰两个', moved.count('\n## ') + (1 if moved.startswith('## ') else 0) == 2,
   moved.count('\n## '))

A = a0.decode('utf-8')
na = A.rstrip('\n') + '\n\n' + moved + '\n'
nb = keep
nb_b = nb.encode()
ck('B6 归档新体量按构造逐项闭合：旧（尾 1 换行）− rstrip 1 + 两空行 2 + 搬走段 + 段尾 1 = 旧 + 段 + 2',
   len(na.encode()) == len(a0) - 1 + 2 + len(moved.encode()) + 1,
   (len(na.encode()), len(a0) - 1 + 2 + len(moved.encode()) + 1,
    len(na.encode()) - len(a0) - len(moved.encode())))
ck('B7 归档 CR 保持 2952（搬走段无 CR）', na.count('\r') == 2952, na.count('\r'))
ck('B8 看板 CR 保持 0', nb.count('\r') == 0, nb.count('\r'))
ck('B9 看板剩余行数 < 271 且 >= 200', 200 <= nb.count('\n') < 271, nb.count('\n'))
ck('B10 看板不再含 R175 / R176 段', 'R17 第 175 轮' not in nb and 'R17 第 176 轮' not in nb)
ck('B11 归档含 R175 / R176 段', 'R17 第 175 轮' in na and 'R17 第 176 轮' in na)
ck('B12 看板仍以 R186 段结尾', 'R17 第 186 轮' in nb.split('## ')[-1], nb.split('## ')[-1][:40])

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
print('== 写盘 ==')
for path, oldraw, newtxt in ((ARC, a0, na), (BRD, b0, nb)):
    bak = os.path.join(BL, '%s.before_r187_arch_%s.bak' % (os.path.basename(path), stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(oldraw)
    ck('W1 %s 备份独占' % os.path.basename(path),
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == hashlib.sha256(oldraw).hexdigest())
    assert open(path, 'rb').read() == oldraw, '母本被外部改动'
    io.open(path, 'w', encoding='utf-8', newline='').write(newtxt)
    back = open(path, 'rb').read()
    ck('W2 %s 回读一致' % os.path.basename(path),
       hashlib.sha256(back).hexdigest() == hashlib.sha256(newtxt.encode()).hexdigest())
    print('   %-20s %d -> %d B / %d 行' % (os.path.basename(path), len(oldraw), len(back), newtxt.count('\n')))
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
sys.exit(1 if fails else 0)
