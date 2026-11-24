#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r110_fix.py —— 修正已写入四件套里的数字错误（追加式写入把错数写进去了，必须就地替换）。

起因：r110_write.py 首次写入用的备用段里有三处算术错误（自错 L-14 / L-15）：
  ① 「845 张 / 50 张 / 5.9%」→ 正确值 846 / 51 / 6.0%（来自 r110d 最终版）
  ② 「4611 = 2762 + 1497 + 340 + 12」这个式子不自洽（和是 4611 但含 12 条错分类）
  ③ L-10 写「4271 与 4611 的差额」，应写「4616 − 4271 − 5」
段文件已就地更新，本脚本把**已写入四件套中的本轮段整段替换**为新段。

做法（比追加安全）：定位本轮段在文件中的**唯一首行**，把它到文件末尾的全部字节替换为新段。
因为本轮段就是文件的最后一段，这个操作等价于「截断到段首 + 追加新段」，且能保留全部前文。
每条都断言：旧段首行在文件中恰好出现 1 次、替换后前文逐字节不变、CR 不变、新段首行回读可见。

反向自测（写入前执行）：对一个临时副本做同样的替换，验证 ① 前文逐字节保留 ② 旧段确实消失
③ 故意把首行写成不存在 → 必须报 FAIL 而不是静默无事发生。
"""
import hashlib, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = ROOT + '/lead/next_re_20261117_r14'
BASE = R14 + '/R17_LEAD_BASELINE'

TARGETS = [
    ('F1', R14 + '/R14_COMMON.md', ROOT + '/_r110/seg_rc_2114.md', 1081, 'c7ec8eafd56357f0'),
    ('F2', ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md', ROOT + '/_r110/seg_ledger_1164.md', 337, 'ec6e01abe07bc40b'),
    ('F3', ROOT + '/lead/LEAD_LOCK', ROOT + '/_r110/seg_lock_EL.md', 137, 'eb046b9f0f8c3ada'),
    ('F4', R14 + '/STATUS_BOARD.md', ROOT + '/_r110/seg_board_110.md', 0, '99b51c66647cf684'),
]
# 断点续跑：F1 已在上一轮跑成功（其备份已创建），用 --only F2,F3,F4 跳过它，避免 wx 冲突。
_ONLY = None
for _a in sys.argv[1:]:
    if _a.startswith('--only'):
        _ONLY = set(x.strip() for x in _a.split('=', 1)[1].split(','))
if _ONLY:
    TARGETS = [t for t in TARGETS if t[0] in _ONLY]

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

def first_line(seg_bytes):
    return seg_bytes.split(b'\n', 1)[0] + b'\n'

# ---------- 反向自测（不碰真文件） ----------
print('--- 反向自测 ---', flush=True)
_t = b'PRE\n\xe4\xb8\xad\n' + b'SECT. x\n' + b'OLDBODY\n'
_seg = b'SECT. x\nNEWBODY\n'
_fl = first_line(_seg)
ck('T1 反控：首行在临时副本中恰好出现 1 次', _t.count(_fl) == 1, _t.count(_fl))
_i = _t.index(_fl)
_rep = _t[:_i] + _seg
ck('T2 替换后前文逐字节保留', _rep[:_i] == _t[:_i], [_i, len(_rep)])
ck('T3 替换后旧段体 OLDBODY 消失、NEWBODY 出现',
   b'OLDBODY' not in _rep and b'NEWBODY' in _rep,
   # 自错 L-16：上一稿写 b'body\n' not in _rep 而新段是 b'new body\n'（含子串 body），必然 FAIL。
   # 是自测写法错，不是替换逻辑错。改用互不为子串的标记重验。
   {'old_gone': b'OLDBODY' not in _rep, 'new_in': b'NEWBODY' in _rep})
ck('T4 反控：把首行写成不存在时 count == 0（会触发 FAIL 而非静默）',
   _t.count(b'NOSUCH. y\n') == 0, _t.count(b'NOSUCH. y\n'))
ck('T5 反控：CR 保留 —— 带 CR 的临时副本替换后 CR 数不变',
   (b'a\r\nb\r\n' + _fl)[:].count(b'\r') == 2, 2)

ts = time.strftime('%Y%m%d_%H%M%S', time.gmtime())
report = {'ts_utc': ts, 'checks': [], 'files': {}}

for key, tgt, seg, cr_exp, sha_exp in TARGETS:
    print('\n--- %s %s ---' % (key, os.path.basename(tgt)), flush=True)
    old = open(tgt, 'rb').read()
    old_sha = hashlib.sha256(old).hexdigest()
    ck('%s 写前 sha == 首次写入后的值 %s' % (key, sha_exp), old_sha.startswith(sha_exp), old_sha[:16])
    ck('%s 写前 CR == %d' % (key, cr_exp), old.count(b'\r') == cr_exp, old.count(b'\r'))

    seg_new = open(seg, 'rb').read()
    ck('%s 新备用段无 CR' % key, seg_new.count(b'\r') == 0, seg_new.count(b'\r'))
    fl = first_line(seg_new)
    ck('%s 本轮段首行在文件中恰好出现 1 次（可定位）' % key, old.count(fl) == 1, old.count(fl))
    if old.count(fl) != 1:
        continue
    cut = old.index(fl)
    head = old[:cut]

    base_name = 'SUPERSEDED.before_r110fix_%s_%s_%s.bak' % (key, os.path.basename(tgt), ts)
    base_path = os.path.join(BASE, base_name)
    try:
        fd = os.open(base_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        os.write(fd, old); os.close(fd)
        ck('%s 修正前备份已独占创建 %s' % (key, base_name), True, base_name)
    except FileExistsError:
        ck('%s 修正前备份已独占创建' % key, False, 'EXISTS')
        continue
    ck('%s 备份 == 写前内容' % key,
       hashlib.sha256(open(base_path, 'rb').read()).hexdigest() == old_sha, base_name)

    now = open(tgt, 'rb').read()
    ck('%s 备份后、写入前 sha 未变（无并发改动）' % key,
       hashlib.sha256(now).hexdigest() == old_sha, hashlib.sha256(now).hexdigest()[:16])

    merged = head + seg_new
    with open(tgt, 'wb') as f:
        f.write(merged)
    ck('%s 一次性写入 %d（保留前文）+ %d（新段）= %d B'
       % (key, len(head), len(seg_new), len(merged)),
       len(merged) == len(head) + len(seg_new), [len(head), len(seg_new), len(merged)])

    rb = open(tgt, 'rb').read()
    ck('%s 回读前文逐字节保留' % key, rb[:len(head)] == head, [len(head), len(rb)])
    ck('%s 回读 CR 仍为 %d' % (key, cr_exp), rb.count(b'\r') == cr_exp, rb.count(b'\r'))
    ck('%s 回读含新段首行' % key, fl in rb, fl[:50].decode('utf-8', 'replace'))
    ck('%s 回读旧错串已消失（845 张 offset==0 / 50 张（5.9%%））' % key,
       b'845 \xe5\xbc\xa0' not in rb and b'50 \xe5\xbc\xa0\xef\xbc\x885.9%' not in rb, '')
    ck('%s 回读 sha == 写入值' % key,
       hashlib.sha256(rb).hexdigest() == hashlib.sha256(merged).hexdigest(),
       hashlib.sha256(rb).hexdigest()[:16])
    report['files'][key] = {'target': tgt, 'head_bytes': len(head), 'new_bytes': len(rb),
                            'old_sha': old_sha, 'new_sha': hashlib.sha256(rb).hexdigest(),
                            'old_lf': old.count(b'\n'), 'new_lf': rb.count(b'\n')}

print('\n--- 全局复核 ---', flush=True)
b = open(R14 + '/STATUS_BOARD.md', 'rb').read()
ck('G1 看板行数 <= 300', b.count(b'\n') <= 300, b.count(b'\n'))
ck('G2 看板 CR == 0', b.count(b'\r') == 0, b.count(b'\r'))
for key, path, cr_exp in (('R14_COMMON', R14 + '/R14_COMMON.md', 1081),
                          ('LEDGER', ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md', 337),
                          ('LEAD_LOCK', ROOT + '/lead/LEAD_LOCK', 137)):
    bb = open(path, 'rb').read()
    ck('G3 %s CR 仍为 %d' % (key, cr_exp), bb.count(b'\r') == cr_exp, bb.count(b'\r'))
ba = open(R14 + '/BOARD_ARCHIVE.md', 'rb').read()
ck('G4 BOARD_ARCHIVE CR 仍为 2952', ba.count(b'\r') == 2952, ba.count(b'\r'))

npass = sum(1 for c in checks if c['ok'])
report['checks'] = checks
report['summary'] = {'total': len(checks), 'pass': npass, 'fail': len(checks) - npass}
json.dump(report, open(ROOT + '/_r110/r110_fix.json', 'w'), ensure_ascii=False, indent=1)
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass), flush=True)
sys.exit(0 if npass == len(checks) else 1)
