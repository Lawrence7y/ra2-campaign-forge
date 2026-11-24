#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""write_r105.py —— R105 四件套写入（独占备份 -> 断言旧 sha/CR -> 一次写 -> 回读校验）"""
import hashlib, io, os, shutil, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14REL = os.path.join('lead', 'next_re_20261117_r14')
BASE = os.path.join(ROOT, R14REL, 'R17_LEAD_BASELINE')
TS = time.strftime('%Y%m%d_%H%M%S')

TARGETS = {
    'R14_COMMON': (os.path.join(ROOT, R14REL, 'R14_COMMON.md'),
                   'e42889b4768d99dfa21b8c1ff85d6d125f53e6c451dbef0589716711758fd697', 1081),
    'LEDGER': (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
               'bd5e34f946802758d5a83b857222242c0124f316fd7b3d6f0347d02a46155e56', 337),
    'LEAD_LOCK': (os.path.join(ROOT, 'lead', 'LEAD_LOCK'),
                  '12c4ac2f7b4c4dcd2683349bfb9f07779c4b274d7686a21b91ea19717b9b3253', 137),
    'STATUS_BOARD': (os.path.join(ROOT, R14REL, 'STATUS_BOARD.md'),
                     '0afb1fa52967e66aea28aefe451567431dc39ca62d7e25c1b811f0e212b2b7b8', 0),
}

fails = []
def ck(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))
    if not c:
        fails.append(n)

# ---- 1 断言旧状态
for k, (p, sha, cr) in TARGETS.items():
    h = hashlib.sha256(io.open(p, 'rb').read()).hexdigest()
    t = io.open(p, encoding='utf-8', newline='').read()
    ck('pre %s sha256' % k, h == sha, h[:16])
    ck('pre %s CR' % k, t.count('\r\n') == cr, t.count('\r\n'))

# ---- 2 独占创建备份（wx 模式）
def backup(path, tag):
    bl = os.path.join(BASE, '%s.before_R105_%s_%s.bak' % (os.path.basename(path), tag, TS))
    with io.open(path, 'rb') as src:
        data = src.read()
    fd = os.open(bl, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    ck('backup exclusive %s' % tag, os.path.exists(bl) and os.path.getsize(bl) == len(data),
       os.path.basename(bl))
    return bl

BACKUPS = {k: backup(p, k) for k, (p, _, _) in TARGETS.items()}

# ---- 3 一次性写入（追加）
def append(path, segfile, expect_cr):
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
    ck('post %s 回读逐字节一致' % os.path.basename(path), back == new, len(back))
    ck('post %s CR 保持 %d' % (os.path.basename(path), expect_cr),
       back.count('\r\n') == expect_cr, back.count('\r\n'))
    return len(new.encode('utf-8'))

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    print('--- R105 write, ts=%s ---' % TS)
    if which in ('all', 'rc'):
        b = append(TARGETS['R14_COMMON'][0], os.path.join(ROOT, '_r105', 'seg_rc_2109.md'), 1081)
        print('  R14_COMMON bytes ->', b)
    if which in ('all', 'led'):
        b = append(TARGETS['LEDGER'][0], os.path.join(ROOT, '_r105', 'seg_ledger_1159.md'), 337)
        print('  LEDGER bytes ->', b)
    if which in ('all', 'lock'):
        b = append(TARGETS['LEAD_LOCK'][0], os.path.join(ROOT, '_r105', 'seg_lock_EG.md'), 137)
        print('  LEAD_LOCK bytes ->', b)
    if which in ('all', 'board'):
        b = append(TARGETS['STATUS_BOARD'][0], os.path.join(ROOT, '_r105', 'seg_board_105.md'), 0)
        n = io.open(TARGETS['STATUS_BOARD'][0], encoding='utf-8', newline='').read().count('\n')
        ck('board lines <= 300', n <= 300, n)
        print('  STATUS_BOARD bytes ->', b, 'lines', n)
    print('FAILS:', len(fails))
    sys.exit(1 if fails else 0)
