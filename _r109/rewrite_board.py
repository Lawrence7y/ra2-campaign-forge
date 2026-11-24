#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rewrite_board.py —— 重做 R109 看板段（上一次写入在 19 秒后被外部回退，如实记录为事故，不追查根源）。

事实（只记现象，不查守护进程源码 —— 元审计红线）：
  j4 备份 12:40:15 取到 256 行（无 R109）；写入后回读断言 305 行含 R109（PASS）；
  j5 备份 12:40:34 再取，**又是 35651 B / 256 行 / 无 R109** ⇒ 两次取证之间文件被回退。
  archive 脚本随后按 256 行版本归档 R105/R106，故现看板 108 行、只剩 R108 + 两条指针。
本脚本把 R109 段重新追加，并**二次回读 + 延时再回读**，确认是否再次被回退。
"""
import hashlib, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
BASE = 'lead/next_re_20261117_r14/R17_LEAD_BASELINE'
BOARD = 'lead/next_re_20261117_r14/STATUS_BOARD.md'
SEG = '_r109/seg_board_109.md'
STAMP = time.strftime('%Y%m%d_%H%M%S')
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

raw = open(BOARD, 'rb').read()
ck('当前看板 %d 行 / CR %d / 无 R109' % (raw.count(b'\n'), raw.count(b'\r')),
   raw.count(b'\r') == 0 and '第 109 轮' not in raw.decode('utf-8'), raw.count(b'\n'))
ck('当前看板含两条归档指针（R105 / R106）',
   raw.count('已归档至 BOARD_ARCHIVE.md（2026-11-24 12:4x'.encode('utf-8')) == 2, True)
ck('当前看板保留 R108 段', '第 108 轮' in raw.decode('utf-8'), True)

b = os.path.join(BASE, 'SUPERSEDED.before_r109_j7_%s_%s.bak' % (os.path.basename(BOARD), STAMP))
fd = os.open(b, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
ck('独占备份 j7', hashlib.sha256(open(b, 'rb').read()).hexdigest() == hashlib.sha256(raw).hexdigest(), b)

seg = open(SEG, 'rb').read()
ck('段文件无 CR', seg.count(b'\r') == 0, seg.count(b'\r'))
new = raw + (b'' if raw.endswith(b'\n') else b'\n') + seg
open(BOARD, 'wb').write(new)
r1 = open(BOARD, 'rb').read()
ck('回读 1：前缀一致 + CR 0 + 含 R109 + 行数 %d <= 300' % r1.count(b'\n'),
   r1[:len(raw)] == raw and r1.count(b'\r') == 0 and '第 109 轮' in r1.decode('utf-8')
   and r1.count(b'\n') <= 300, (len(raw), len(r1), r1.count(b'\n')))
time.sleep(20)
r2 = open(BOARD, 'rb').read()
ck('延时 20 s 回读 2：内容仍在（若再次消失即为外部回退事故）',
   r2 == r1 and '第 109 轮' in r2.decode('utf-8'), (len(r2), r2 == r1))
json.dump({'checks': checks, 'len': [len(raw), len(r1), len(r2)]},
          open('_r109/rewrite_board.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
sys.exit(0 if npass == len(checks) else 1)
