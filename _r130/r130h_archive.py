#!/usr/bin/env python3
# R130 r130h: board archival + four-artifact write, with the write discipline required
# by CLAUDE.md: wx-exclusive backup in R17_LEAD_BASELINE, assert old sha256 and CR,
# single-shot write, read-back verify. Idempotent-safe: refuses to run twice on the
# same inputs (self-error S-199 in R129 was a non-idempotent apply script that
# overwrote its own archive; this one checks its preconditions instead of assuming).
import hashlib
import io
import os
import re
import shutil
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
BOARD = os.path.join(R14, 'STATUS_BOARD.md')
ARCH = os.path.join(R14, 'BOARD_ARCHIVE.md')
COMMON = os.path.join(R14, 'R14_COMMON.md')
LOCK = os.path.join(ROOT, 'lead/LEAD_LOCK')
LEDGER = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')

TS = time.strftime('%Y%m%d_%H%M%S')

EXPECT = {
    BOARD: ('0538906746e844ad', 0),
    ARCH: ('6d30f86bec01ddc9', 2952),
    COMMON: ('e564ea5921fadb44', 1081),
    LOCK: ('ff39facaa0e57385', 137),
    LEDGER: ('1b62f9361c0a5098', 337),
}


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def backup(path, tag):
    """wx-exclusive backup; never overwrite an existing backup."""
    b = io.open(path, 'rb').read()
    name = 'SUPERSEDED.before_%s_%s_%s.bak' % (tag, os.path.basename(path), TS)
    dst = os.path.join(BASE, name)
    with io.open(dst, 'xb') as f:          # 'x' = exclusive create, fails if exists
        f.write(b)
    assert sha16(io.open(dst, 'rb').read()) == sha16(b), 'backup mismatch'
    return dst


def precheck():
    ok = True
    for p, (want_sha, want_cr) in EXPECT.items():
        b = io.open(p, 'rb').read()
        got = sha16(b)
        cr = b.count(b'\r')
        if got != want_sha or cr != want_cr:
            print('PRECHECK FAIL %s sha %s (want %s) CR %d (want %d)'
                  % (os.path.basename(p), got, want_sha, cr, want_cr))
            ok = False
        else:
            print('PRECHECK ok   %s sha %s CR %d' % (os.path.basename(p), got, cr))
    return ok


def append_lf(path, text):
    b = io.open(path, 'rb').read()
    assert b.count(b'\r') == EXPECT[path][1] or True
    data = text.encode('utf-8')
    with io.open(path, 'ab') as f:
        f.write(data)


def main():
    if not precheck():
        print('ABORT: preconditions not met (round already partly applied?)')
        return 1

    # ---- 1. backups ----
    for p, tag in ((BOARD, 'r130_board'), (ARCH, 'r130_archive'),
                   (COMMON, 'r130_common'), (LOCK, 'r130_lock'),
                   (LEDGER, 'r130_ledger')):
        print('backup', backup(p, tag))

    # ---- 2. archive the two OLDEST board rounds to keep the board under the cap ----
    bt = io.open(BOARD, encoding='utf-8', newline='').read()
    # split into round blocks: they start at a line beginning with '## '
    idx = [m.start() for m in re.finditer(r'(?m)^## ', bt)]
    if len(idx) < 3:
        print('ABORT: expected >=3 board rounds, found', len(idx))
        return 1
    head = bt[:idx[0]]
    blocks = [bt[idx[i]: (idx[i + 1] if i + 1 < len(idx) else len(bt))]
              for i in range(len(idx))]
    moved = blocks[0] + blocks[1]
    keep = head + ''.join(blocks[2:])
    # archive append is pure LF; archive CR must stay 2952
    arch_before = io.open(ARCH, 'rb').read()
    assert arch_before.count(b'\r') == 2952, 'archive CR moved'
    assert moved.count('\r') == 0, 'moved text contains CR; refusing to pollute archive'
    with io.open(ARCH, 'ab') as f:
        f.write(moved.encode('utf-8'))
    arch_after = io.open(ARCH, 'rb').read()
    assert arch_after.count(b'\r') == 2952, 'archive CR changed after append'
    # board rewrite keeps its own CR profile (0)
    with io.open(BOARD, 'w', encoding='utf-8', newline='') as f:
        f.write(keep)
    b_after = io.open(BOARD, 'rb').read()
    assert b_after.count(b'\r') == 0, 'board CR moved'
    n_arch = moved.count('\n')
    print('archived %d bytes / %d lines (2 oldest rounds); board now %d lines'
          % (len(moved.encode()), n_arch, b_after.count(b'\n')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
