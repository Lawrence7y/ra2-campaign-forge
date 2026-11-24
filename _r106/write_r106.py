#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""write_r106.py —— R106 四件套写入（独占备份 -> 断言旧 sha/CR -> 一次写 -> 回读校验）

纪律（任务卡 §3）：
  1. 每次修改前在 R17_LEAD_BASELINE/ 用 wx 模式独占创建唯一备份
  2. 断言旧 sha256 与 CR 都等于预期
  3. 一次性写入（追加，不重写整文件）
  4. 回读逐字节校验，并复核 CR 不变量
"""
import hashlib, io, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14REL = os.path.join('lead', 'next_re_20261117_r14')
BASE = os.path.join(ROOT, R14REL, 'R17_LEAD_BASELINE')
TS = time.strftime('%Y%m%d_%H%M%S')

TARGETS = {
    'R14_COMMON': (os.path.join(ROOT, R14REL, 'R14_COMMON.md'),
                   'b00ec43984c4ca85', 1081),
    'LEDGER': (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
               '5350048bd883b59c', 337),
    'LEAD_LOCK': (os.path.join(ROOT, 'lead', 'LEAD_LOCK'),
                  '66f09bc40c1cfd57', 137),
    'STATUS_BOARD': (os.path.join(ROOT, R14REL, 'STATUS_BOARD.md'),
                     '54887c7542457ec9', 0),
    'BOARD_ARCHIVE': (os.path.join(ROOT, R14REL, 'BOARD_ARCHIVE.md'),
                      '3c12191fe2016670', 2952),
}

fails = []


def ck(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))
    if not c:
        fails.append(n)


def sha16(p):
    return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()[:16]


def crcount(p):
    return io.open(p, encoding='utf-8', newline='').read().count('\r\n')


# ---- 1 断言旧状态（全部四个 + 归档的 CR）
for k, (p, sha, cr) in TARGETS.items():
    ck('pre %s sha256 %s' % (k, sha), sha16(p) == sha, sha16(p))
    ck('pre %s CR %d' % (k, cr), crcount(p) == cr, crcount(p))


# ---- 2 独占创建备份（wx 模式）
def backup(path, tag):
    os.makedirs(BASE, exist_ok=True)
    bl = os.path.join(BASE, '%s.before_R106_%s_%s.bak'
                      % (os.path.basename(path), tag, TS))
    with io.open(path, 'rb') as src:
        data = src.read()
    fd = os.open(bl, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    ck('backup exclusive %s' % tag,
       os.path.exists(bl) and os.path.getsize(bl) == len(data),
       os.path.basename(bl))
    return bl


BACKUPS = {k: backup(p, k) for k, (p, _, _) in TARGETS.items()}


# ---- 3 一次性写入（追加）
def append(path, segfile, expect_cr, label):
    seg = io.open(segfile, encoding='utf-8', newline='').read()
    ck('seg %s is LF-only' % os.path.basename(segfile), '\r' not in seg,
       seg.count('\n'))
    cur = io.open(path, encoding='utf-8', newline='').read()
    if not cur.endswith('\n'):
        seg = '\n' + seg
    new = cur + seg
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new)
    back = io.open(path, encoding='utf-8', newline='').read()
    ck('post %s 回读逐字节一致' % label, back == new, len(back))
    ck('post %s CR 保持 %d' % (label, expect_cr),
       back.count('\r\n') == expect_cr, back.count('\r\n'))
    return len(new.encode('utf-8'))


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    print('--- R106 write, ts=%s ---' % TS)

    if which in ('all', 'rc'):
        b = append(TARGETS['R14_COMMON'][0],
                   os.path.join(ROOT, '_r106', 'seg_rc_2110.md'), 1081, 'R14_COMMON')
        print('  R14_COMMON bytes ->', b)

    if which in ('all', 'led'):
        b = append(TARGETS['LEDGER'][0],
                   os.path.join(ROOT, '_r106', 'seg_ledger_1160.md'), 337, 'LEDGER')
        print('  LEDGER bytes ->', b)

    if which in ('all', 'lock'):
        b = append(TARGETS['LEAD_LOCK'][0],
                   os.path.join(ROOT, '_r106', 'seg_lock_EH.md'), 137, 'LEAD_LOCK')
        print('  LEAD_LOCK bytes ->', b)

    if which in ('all', 'board'):
        # 归档线检查：>=260 行时先归档最早两段
        bl = io.open(TARGETS['STATUS_BOARD'][0], encoding='utf-8',
                     newline='').read().count('\n')
        ck('board 写入前行数 < 260（无需归档）', bl < 260, bl)
        b = append(TARGETS['STATUS_BOARD'][0],
                   os.path.join(ROOT, '_r106', 'seg_board_106.md'), 0, 'STATUS_BOARD')
        n = io.open(TARGETS['STATUS_BOARD'][0], encoding='utf-8',
                    newline='').read().count('\n')
        ck('board lines <= 300', n <= 300, n)
        print('  STATUS_BOARD bytes ->', b, 'lines', n)

    # 归档文件必须一字未动
    ck('post BOARD_ARCHIVE sha256 未变',
       sha16(TARGETS['BOARD_ARCHIVE'][0]) == '3c12191fe2016670',
       sha16(TARGETS['BOARD_ARCHIVE'][0]))
    ck('post BOARD_ARCHIVE CR 仍 2952',
       crcount(TARGETS['BOARD_ARCHIVE'][0]) == 2952,
       crcount(TARGETS['BOARD_ARCHIVE'][0]))

    print('FAILS:', len(fails), fails)
    sys.exit(1 if fails else 0)
