#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""write_r107.py —— R107 四件套写入（独占备份 -> 断言旧 sha/CR -> 一次写 -> 回读校验）"""
import hashlib, io, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14REL = os.path.join('lead', 'next_re_20261117_r14')
BASE = os.path.join(ROOT, R14REL, 'R17_LEAD_BASELINE')
TS = time.strftime('%Y%m%d_%H%M%S')

def sha16(p):
    return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()[:16]

def crcount(p):
    return io.open(p, encoding='utf-8', newline='').read().count('\r\n')

TARGETS = {
    'R14_COMMON': (os.path.join(ROOT, R14REL, 'R14_COMMON.md'),
                   '822076dfb60db606', 1081),
    'LEDGER': (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
               'c8f3dd14910143cb', 337),
    'LEAD_LOCK': (os.path.join(ROOT, 'lead', 'LEAD_LOCK'),
                  '6dfbce31d014fb32', 137),
    'STATUS_BOARD': (os.path.join(ROOT, R14REL, 'STATUS_BOARD.md'),
                     '36c69fffbad606ab', 0),
    'BOARD_ARCHIVE': (os.path.join(ROOT, R14REL, 'BOARD_ARCHIVE.md'),
                      '3c12191fe2016670', 2952),
}
fails = []

def ck(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))
    if not c:
        fails.append(n)

for k, (p, sha, cr) in TARGETS.items():
    ck('pre %s sha256 %s' % (k, sha), sha16(p) == sha, sha16(p))
    ck('pre %s CR %d' % (k, cr), crcount(p) == cr, crcount(p))

def backup(path, tag):
    os.makedirs(BASE, exist_ok=True)
    bl = os.path.join(BASE, '%s.before_R107_%s_%s.bak'
                      % (os.path.basename(path), tag, TS))
    with io.open(path, 'rb') as src:
        data = src.read()
    fd = os.open(bl, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    ck('backup exclusive %s' % tag,
       os.path.exists(bl) and os.path.getsize(bl) == len(data), os.path.basename(bl))
    return bl

BACKUPS = {k: backup(p, k) for k, (p, _, _) in TARGETS.items()}

def append(path, segfile, expect_cr, label):
    seg = io.open(segfile, encoding='utf-8', newline='').read()
    ck('seg %s is LF-only' % os.path.basename(segfile), '\r' not in seg, seg.count('\n'))
    cur = io.open(path, encoding='utf-8', newline='').read()
    if not cur.endswith('\n'):
        seg = '\n' + seg
    new = cur + seg
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new)
    back = io.open(path, encoding='utf-8', newline='').read()
    ck('post %s 回读逐字节一致' % label, back == new, len(back))
    ck('post %s CR 保持 %d' % (label, expect_cr), back.count('\r\n') == expect_cr,
       back.count('\r\n'))
    return len(new.encode('utf-8'))

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    print('--- R107 write, ts=%s ---' % TS)
    if which in ('all', 'rc'):
        print('  R14_COMMON bytes ->', append(TARGETS['R14_COMMON'][0],
              os.path.join(ROOT, '_r107', 'seg_rc_2111.md'), 1081, 'R14_COMMON'))
    if which in ('all', 'led'):
        print('  LEDGER bytes ->', append(TARGETS['LEDGER'][0],
              os.path.join(ROOT, '_r107', 'seg_ledger_1161.md'), 337, 'LEDGER'))
    if which in ('all', 'lock'):
        print('  LEAD_LOCK bytes ->', append(TARGETS['LEAD_LOCK'][0],
              os.path.join(ROOT, '_r107', 'seg_lock_EI.md'), 137, 'LEAD_LOCK'))
    if which in ('all', 'board'):
        bl = io.open(TARGETS['STATUS_BOARD'][0], encoding='utf-8',
                     newline='').read().count('\n')
        ck('board 写入前行数 < 260（无需归档）', bl < 260, bl)
        b = append(TARGETS['STATUS_BOARD'][0],
                   os.path.join(ROOT, '_r107', 'seg_board_107.md'), 0, 'STATUS_BOARD')
        n = io.open(TARGETS['STATUS_BOARD'][0], encoding='utf-8',
                    newline='').read().count('\n')
        ck('board lines <= 300', n <= 300, n)
        print('  STATUS_BOARD bytes ->', b, 'lines', n)
    ck('post BOARD_ARCHIVE sha256 未变', sha16(TARGETS['BOARD_ARCHIVE'][0]) == '3c12191fe2016670',
       sha16(TARGETS['BOARD_ARCHIVE'][0]))
    ck('post BOARD_ARCHIVE CR 仍 2952', crcount(TARGETS['BOARD_ARCHIVE'][0]) == 2952,
       crcount(TARGETS['BOARD_ARCHIVE'][0]))
    print('FAILS:', len(fails), fails)
    sys.exit(1 if fails else 0)
