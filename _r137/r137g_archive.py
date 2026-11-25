#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R137-g · 看板归档（最早两段 -> BOARD_ARCHIVE）+ 重写看板

为什么需要这一步：
  r137f 写完后看板 334 行 > 300 上限（自错 S-259：我在写之前只核了「252 < 260 不触发归档」，
  但没核「本轮正文加进去之后会不会超 300」—— 252 + 82 = 334）。
  按纪律必须先归档最早的 2 段，且归档 CR 保持 2952、看板 CR 保持 0。

纪律：
  - wx 独占备份
  - 断言归档 CR == 2952、看板 CR == 0
  - 移动文本不得含 CR（否则污染归档）
  - 回读校验
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
ARCH = os.path.join(R14, 'BOARD_ARCHIVE.md')

TS = time.strftime('%Y%m%d_%H%M%S')

BOARD_MAX = 300


def sha(b):
    return hashlib.sha256(b).hexdigest()


def backup(p, tag):
    b = io.open(p, 'rb').read()
    dst = os.path.join(BASE, '%s.before_%s_%s.bak' % (os.path.basename(p), tag, TS))
    with io.open(dst, 'xb') as f:        # exclusive create
        f.write(b)
    assert sha(io.open(dst, 'rb').read()) == sha(b)
    print('backup %s -> %s (%d B)' % (os.path.basename(p), os.path.basename(dst), len(b)))
    return dst


def main():
    bb = io.open(BOARD, 'rb').read()
    ab = io.open(ARCH, 'rb').read()
    n_board = bb.count(b'\n')
    print('before: board %d lines / CR %d ; archive %d lines / CR %d'
          % (n_board, bb.count(b'\r'), ab.count(b'\n'), ab.count(b'\r')))

    if bb.count(b'\r') != 0:
        print('ABORT board CR != 0'); return 1
    if ab.count(b'\r') != 2952:
        print('ABORT archive CR != 2952 (got %d)' % ab.count(b'\r')); return 1
    # 判据必须看「本轮正文加进去之后」的行数，不是当前行数 —— 自错 S-259 就是这么来的。
    PENDING = int(os.environ.get('R137_PENDING_LINES', '82'))
    if n_board + PENDING <= BOARD_MAX:
        print('board %d + pending %d <= %d, no archival needed'
              % (n_board, PENDING, BOARD_MAX))
        return 0
    print('board %d + pending %d > %d -> archive the two oldest rounds'
          % (n_board, PENDING, BOARD_MAX))

    backup(BOARD, 'R137_arch')
    backup(ARCH, 'R137_arch')

    bt = bb.decode('utf-8')
    idx = [m.start() for m in re.finditer(r'(?m)^## ', bt)]
    print('board round blocks: %d' % len(idx))
    if len(idx) < 3:
        print('ABORT need >=3 blocks to archive 2'); return 1

    head = bt[:idx[0]]
    blocks = [bt[idx[i]:(idx[i + 1] if i + 1 < len(idx) else len(bt))]
              for i in range(len(idx))]
    # 归档最早两段：它们绝不能被读成「本轮」的段
    moved = blocks[0] + blocks[1]
    if '\r' in moved:
        print('ABORT moved text contains CR'); return 1
    keep = head + ''.join(blocks[2:])

    with io.open(ARCH, 'ab') as f:
        f.write(moved.encode('utf-8'))
    a2 = io.open(ARCH, 'rb').read()
    assert a2.count(b'\r') == 2952, 'archive CR changed'
    assert a2.startswith(ab), 'archive not appended cleanly'

    with io.open(BOARD, 'w', encoding='utf-8', newline='') as f:
        f.write(keep)
    b2 = io.open(BOARD, 'rb').read()
    assert b2.count(b'\r') == 0, 'board CR moved'
    n_after = b2.count(b'\n')
    print('after : board %d lines / CR %d ; archive CR %d'
          % (n_after, b2.count(b'\r'), a2.count(b'\r')))
    print('moved %d B / %d lines to archive' % (len(moved.encode()), moved.count('\n')))

    # ---- 决定性断言：归档段不能是 R137 段，R137 段必须仍在看板里 ----
    assert 'R17 第 137 轮' in keep, 'R137 block vanished from board'
    assert 'R17 第 137 轮' not in moved, 'R137 block got archived (wrong direction)'
    assert n_after <= BOARD_MAX, 'board still over cap: %d' % n_after
    print('checks OK: R137 kept on board, board %d <= %d' % (n_after, BOARD_MAX))
    return 0


if __name__ == '__main__':
    sys.exit(main())
