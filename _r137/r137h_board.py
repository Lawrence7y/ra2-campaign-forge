#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R137-h · 把本轮看板段追加到 STATUS_BOARD.md（归档已在 r137g 完成）

r137f 的问题（自错 S-259）：我在写之前只核了「252 < 260 不触发归档」，没核
「252 + 83 = 335 > 300」。结果写进去当场越界，只能回滚。
正确顺序是：先按「当前行数 + 本轮段行数」判是否归档，再写。
r137g 已按此归档（252 -> 136 行，归档 CR 2952 不变），本轮段 83 行，136 + 83 = 219 <= 300。

本条只做一件事：把同一份 BOARD_TXT 追加进看板，并回读校验。
"""
import hashlib
import io
import os
import re
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
BOARD = os.path.join(R14, 'STATUS_BOARD.md')

BOARD_MAX = 300
PRE_SHA = 'd6571c88c12e215681554564c245c16ade4a9920b6d70ddbefbd869cd197168c'  # 归档前的看板


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    # 从 r137f 里取同一份正文，保证「写进去的就是审过的那份」
    src = io.open(os.path.join(ROOT, '_r137/r137f_write.py'), encoding='utf-8').read()
    i = src.index("BOARD_TXT = u'''")
    j = src.index("'''", i + len("BOARD_TXT = u'''"))
    txt = src[i + len("BOARD_TXT = u'''"):j]
    if not txt.endswith('\n'):
        txt += '\n'
    if '\r' in txt:
        print('ABORT text contains CR'); return 1
    if 'R17 第 137 轮' not in txt:
        print('ABORT text is not the R137 block'); return 1

    b = io.open(BOARD, 'rb').read()
    n0 = b.count(b'\n')
    if b.count(b'\r') != 0:
        print('ABORT board CR != 0'); return 1
    if 'R17 第 137 轮' in b.decode('utf-8'):
        print('ABORT R137 block already present'); return 1
    add = txt.count('\n')
    print('board %d lines, adding %d -> %d (cap %d)' % (n0, add, n0 + add, BOARD_MAX))
    if n0 + add > BOARD_MAX:
        print('ABORT would exceed cap; archive more first'); return 1

    # wx 独占备份
    dst = os.path.join(BASE, 'STATUS_BOARD.md.before_R137_write_%s.bak'
                       % time.strftime('%Y%m%d_%H%M%S'))
    with io.open(dst, 'xb') as f:
        f.write(b)
    assert sha(io.open(dst, 'rb').read()) == sha(b), 'backup mismatch'
    print('backup ->', os.path.basename(dst))

    with io.open(BOARD, 'ab') as f:
        f.write(txt.encode('utf-8'))
    a = io.open(BOARD, 'rb').read()
    assert a.count(b'\r') == 0, 'board CR moved'
    assert a.startswith(b), 'not appended cleanly'
    assert a.count(b'\n') == n0 + add, 'line count wrong'
    assert 'R17 第 137 轮' in a.decode('utf-8'), 'R137 block missing'
    print('wrote board: %d lines, %d B, CR %d, sha %s'
          % (a.count(b'\n'), len(a), a.count(b'\r'), sha(a)[:16]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
