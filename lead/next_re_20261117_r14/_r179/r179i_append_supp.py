# -*- coding: utf-8 -*-
"""r179i：把「收口补」四段追加到四件套（C16 重钉后补写，因为 C16 下界要用本节实测字节）。"""
import hashlib, io, os, sys

TIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
NEW = os.path.join(TIER, '_r179', '_new')
TARGETS = [
    (os.path.join(TIER, 'R14_COMMON.md'), 'c_2_184_supp.md', 1081, 'R179b_R14_COMMON.before_supp.bak'),
    (os.path.join(TIER, '..', 'GOAL_THREE_TARGETS_20261018.md'), 'ledger_1234_supp.md', 337, 'R179b_LEDGER.before_supp.bak'),
    (os.path.join(TIER, '..', 'LEAD_LOCK'), 'lock_pj_supp.md', 137, 'R179b_LEAD_LOCK.before_supp.bak'),
    (os.path.join(TIER, 'STATUS_BOARD.md'), 'board_179_supp.md', 0, 'R179b_STATUS_BOARD.before_supp.bak'),
]
PASS = FAIL = 0


def ck(n, c, d=''):
    global PASS, FAIL
    if c:
        PASS += 1; print('PASS %s  %s' % (n, d))
    else:
        FAIL += 1; print('FAIL %s  %s' % (n, d))


def sha(b): return hashlib.sha256(b).hexdigest()


segs = {}
for p, s, cr, tag in TARGETS:
    b = open(os.path.join(NEW, s), 'rb').read()
    ck('段 %s 无 CR' % s, b.count(b'\r') == 0)
    ck('段 %s 以空行开头' % s, b.startswith(b'\n'))
    segs[p] = b

for p, s, cr, tag in TARGETS:
    raw = open(p, 'rb').read()
    ck('改前 CR=%d %s' % (cr, os.path.basename(p)), raw.count(b'\r') == cr, raw.count(b'\r'))
    bp = os.path.join(BASE, tag)
    if not os.path.exists(bp):
        fd = os.open(bp, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        with os.fdopen(fd, 'wb') as f: f.write(raw)
    ck('备份可复算 %s' % tag, sha(open(bp, 'rb').read()) == sha(raw))

if FAIL:
    print('ABORT 未写盘'); sys.exit(1)
if '--dry' in sys.argv:
    print('--dry 通过'); sys.exit(0)

for p, s, cr, tag in TARGETS:
    old = open(p, 'rb').read(); sh0 = sha(old)
    new = old + segs[p]
    ck('%s CR 不变 = %d' % (os.path.basename(p), cr), new.count(b'\r') == cr, new.count(b'\r'))
    ck('%s sha 变化' % os.path.basename(p), sha(new) != sh0)
    open(p, 'wb').write(new)
    rb = open(p, 'rb').read()
    ck('%s 回读一致' % os.path.basename(p), rb == new)
    print('  %s: %d -> %d B (+%d)' % (os.path.basename(p), len(old), len(rb), len(rb) - len(old)))
    if p.endswith('STATUS_BOARD.md'):
        ck('看板 <= 300 行', rb.count(b'\n') <= 300, rb.count(b'\n'))
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
