# -*- coding: utf-8 -*-
"""R72 · 从备份回滚四件套到写入前状态（一次性，带前/后断言）。

事故：write_r72.py 的旧 sha 断言只记录 FAIL 但不中止，导致同一轮内容被追加了两次
（四件套各出现 2 份 §2.77 / §1126 / CZ / 第 72 轮段）。本脚本用 _224929 批次备份
（= 写入前原始态，sha 与开局实测一致）回滚，并在回滚前后双向断言。

纪律：回滚前先把当前（双份）状态另存一份取证，便于事后核对。
"""
import io, os, sys, hashlib, time

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')

T = {
    'R14_COMMON':   (os.path.join(R14, 'R14_COMMON.md'), 1081, '67ddce048049ee1b'),
    'LEDGER':       (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), 337, '37370734cfe151f9'),
    'LEAD_LOCK':    (os.path.join(ROOT, 'lead', 'LEAD_LOCK'), 137, '65a79be10e182013'),
    'STATUS_BOARD': (os.path.join(R14, 'STATUS_BOARD.md'), 0, 'b51b5f95df59e7b3'),
}
MARK = {'R14_COMMON': '## 2.77 ', 'LEDGER': '## §1126 ',
        'LEAD_LOCK': '## CZ ·', 'STATUS_BOARD': 'R17 第 72 轮'}

P = print
fails = []
def ck(n, c, d=''):
    P(('  PASS ' if c else '  FAIL ') + n + (('  ' + d) if d else ''))
    if not c: fails.append(n)

P('=== S1 · 当前状态 ===')
for k, (p, cr, sh) in T.items():
    b = io.open(p, 'rb').read()
    n = b.decode('utf-8').count(MARK[k])
    P('  %-14s %9d B CR=%-5d 段出现 %d 次' % (k, len(b), b.count(b'\r'), n))
    # 允许 1（单份，待从备份重写）或 2（双份事故态），两种都要能回滚
    ck('%s 当前段出现次数 ∈ {1,2}' % k, n in (1, 2), '%d 次' % n)

P('')
P('=== S2 · 取证：把双份状态另存 ===')
ts = time.strftime('%Y%m%d_%H%M%S')
for k, (p, cr, sh) in T.items():
    dst = os.path.join(BASE, 'INCIDENT.r72_double_append_%s_%s.md' % (k, ts))
    with open(dst, 'xb') as f:
        f.write(io.open(p, 'rb').read())
    ck('取证副本 %s 已建立' % os.path.basename(dst), os.path.isfile(dst))

P('')
P('=== S3 · 回滚（用 _224929 备份 = 写入前原始态）===')
for k, (p, cr, sh) in T.items():
    src = os.path.join(BASE, 'SUPERSEDED.before_r72_write_%s_20261122_224929.md' % k)
    ck('%s 备份存在' % k, os.path.isfile(src))
    b = io.open(src, 'rb').read()
    ck('%s 备份 sha 前16 = 开局值 %s' % (k, sh), hashlib.sha256(b).hexdigest()[:16] == sh)
    ck('%s 备份 CR = %d' % (k, cr), b.count(b'\r') == cr, '%d' % b.count(b'\r'))
    ck('%s 备份不含本轮段（确为写入前）' % k, MARK[k] not in b.decode('utf-8'))
    io.open(p, 'wb').write(b)

P('')
P('=== S4 · 回滚后双向断言 ===')
for k, (p, cr, sh) in T.items():
    b = io.open(p, 'rb').read()
    h = hashlib.sha256(b).hexdigest()
    P('  %-14s %9d B CR=%-5d sha=%s' % (k, len(b), b.count(b'\r'), h[:16]))
    ck('%s sha 完全等于开局值' % k, h[:16] == sh, h[:16])
    ck('%s CR 恢复为 %d' % (k, cr), b.count(b'\r') == cr, '%d' % b.count(b'\r'))
    ck('%s 已不含本轮段' % k, MARK[k] not in b.decode('utf-8'))
bd = io.open(T['STATUS_BOARD'][0], 'rb').read().decode('utf-8')
ck('看板已回到写入前（不含第 72 轮段）', 'R17 第 72 轮' not in bd, 'ok')

P('')
P('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
sys.exit(0 if not fails else 1)
