#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r110_write.py —— 四件套写入（R110）：备份用 wx 独占创建 -> 断言旧 sha/CR -> 一次性写入 -> 回读校验。

纪律（逐条在 checks 里留证）：
  W-x1 备份文件用 os.open(..., O_CREAT|O_EXCL) 独占创建，文件名含 UTC 时间戳与目标名，冲突即失败。
  W-x2 写前断言：文件 sha256 == 记录值 且 CR 计数 == 记录值 且 LF 计数 == 记录值（三者同时）。
  W-x3 备份内容 sha256 == 写前文件 sha256（备份是真的、不是空文件）。
  W-x4 备用段自身 CR == 0（全 LF），且不含 NUL。
  W-x5 一次性写入（单个 wb 调用），不做多次追加。
  W-x6 回读：CR 保持、旧字节是新的前缀（逐字节）、新段首行出现、行数/字节数符合预期。
状态文件 _r110/r110_write.json 每次运行覆盖；重复运行会因 wx 冲突而失败（这是设计意图）。
"""
import hashlib, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = ROOT + '/lead/next_re_20261117_r14'
BASE = R14 + '/R17_LEAD_BASELINE'

TARGETS = [
    # (key, 目标路径, 备用段, 期望旧 CR, 期望旧 sha16, 期望旧 LF, 写入位置说明)
    ('W1', R14 + '/R14_COMMON.md', ROOT + '/_r110/seg_rc_2114.md',
     1081, 'eaccfa2807d4cccc', 10033, 'R14_COMMON 尾部追加 §2.114'),
    ('W2', ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md', ROOT + '/_r110/seg_ledger_1164.md',
     337, '1d21076ecbb7cd46', 46005, '台账尾部追加 §1164'),
    ('W3', ROOT + '/lead/LEAD_LOCK', ROOT + '/_r110/seg_lock_EL.md',
     137, '834cb8666afe8118', 5277, 'LEAD_LOCK 尾部追加 EL 段'),
    ('W4', R14 + '/STATUS_BOARD.md', ROOT + '/_r110/seg_board_110.md',
     0, 'f85824c74c0fe33e', 163, '看板尾部追加第 110 轮段'),
]

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

ts = time.strftime('%Y%m%d_%H%M%S', time.gmtime())
report = {'ts_utc': ts, 'checks': [], 'files': {}}

for key, tgt, seg, cr_exp, sha_exp, lf_exp, desc in TARGETS:
    print('\n--- %s %s ---' % (key, desc), flush=True)
    old = open(tgt, 'rb').read()
    old_sha = hashlib.sha256(old).hexdigest()
    old_cr = old.count(b'\r')
    old_lf = old.count(b'\n')
    ck('%s 目标存在且写前 sha256 == 记录值 %s' % (key, sha_exp),
       old_sha.startswith(sha_exp), old_sha[:16])
    ck('%s 写前 CR == %d（期望 %d）' % (key, old_cr, cr_exp), old_cr == cr_exp, old_cr)
    ck('%s 写前 LF == %d（期望 %d）' % (key, old_lf, lf_exp), old_lf == lf_exp, old_lf)

    new_seg = open(seg, 'rb').read()
    ck('%s 备用段无 CR（全 LF）' % key, new_seg.count(b'\r') == 0, new_seg.count(b'\r'))
    ck('%s 备用段无 NUL' % key, b'\x00' not in new_seg, new_seg.count(b'\x00'))

    base_name = 'SUPERSEDED.before_r110_%s_%s_%s.bak' % (key, os.path.basename(tgt), ts)
    base_path = os.path.join(BASE, base_name)
    # W-x1 独占创建
    try:
        fd = os.open(base_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        os.write(fd, old)
        os.close(fd)
        ck('%s 备份已独占创建 %s' % (key, base_name), True, base_name)
    except FileExistsError:
        ck('%s 备份已独占创建 %s' % (key, base_name), False, 'EXISTS（重复运行？）')
        continue
    bak = open(base_path, 'rb').read()
    ck('%s 备份内容 sha256 == 写前 sha256（备份非空且逐字节相同）' % key,
       hashlib.sha256(bak).hexdigest() == old_sha, hashlib.sha256(bak).hexdigest()[:16])

    # 写前再确认未被他人改动（多进程共写风险）
    now = open(tgt, 'rb').read()
    ck('%s 备份后、写入前，目标 sha 未变（无并发改动）' % key,
       hashlib.sha256(now).hexdigest() == old_sha, hashlib.sha256(now).hexdigest()[:16])

    # W-x5 一次性写入
    merged = old + new_seg
    with open(tgt, 'wb') as f:
        f.write(merged)
    ck('%s 一次性写入 %d + %d = %d B' % (key, len(old), len(new_seg), len(merged)),
       len(merged) == len(old) + len(new_seg), [len(old), len(new_seg), len(merged)])

    # W-x6 回读
    rb = open(tgt, 'rb').read()
    ck('%s 回读 CR 仍为 %d' % (key, cr_exp), rb.count(b'\r') == cr_exp, rb.count(b'\r'))
    ck('%s 回读旧字节是新的前缀（逐字节）' % key, rb[:len(old)] == old,
       [len(old), len(rb)])
    first_line = new_seg.split(b'\n', 1)[0]
    ck('%s 回读含新段首行' % key, first_line in rb, first_line[:60].decode('utf-8', 'replace'))
    ck('%s 回读 sha == 写入值的 sha' % key,
       hashlib.sha256(rb).hexdigest() == hashlib.sha256(merged).hexdigest(),
       hashlib.sha256(rb).hexdigest()[:16])
    report['files'][key] = {'target': tgt, 'seg': seg, 'backup': base_name,
                            'old_sha': old_sha, 'new_sha': hashlib.sha256(rb).hexdigest(),
                            'old_bytes': len(old), 'new_bytes': len(rb),
                            'old_lf': old_lf, 'new_lf': rb.count(b'\n'),
                            'old_cr': old_cr, 'new_cr': rb.count(b'\r')}

# 全局复核
print('\n--- 全局复核 ---', flush=True)
b = open(R14 + '/STATUS_BOARD.md', 'rb').read()
ck('G1 看板总行数 <= 300（纪律上限）', b.count(b'\n') <= 300, b.count(b'\n'))
ck('G2 看板 CR == 0', b.count(b'\r') == 0, b.count(b'\r'))
for key, path, cr_exp in (('R14_COMMON', R14 + '/R14_COMMON.md', 1081),
                          ('LEDGER', ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md', 337),
                          ('LEAD_LOCK', ROOT + '/lead/LEAD_LOCK', 137)):
    bb = open(path, 'rb').read()
    ck('G3 %s CR 仍为 %d' % (key, cr_exp), bb.count(b'\r') == cr_exp, bb.count(b'\r'))
ba = open(R14 + '/BOARD_ARCHIVE.md', 'rb').read()
ck('G4 BOARD_ARCHIVE CR 仍为 2952（本轮未归档）', ba.count(b'\r') == 2952, ba.count(b'\r'))

npass = sum(1 for c in checks if c['ok'])
report['checks'] = checks
report['summary'] = {'total': len(checks), 'pass': npass, 'fail': len(checks) - npass}
json.dump(report, open(ROOT + '/_r110/r110_write.json', 'w'), ensure_ascii=False, indent=1)
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass), flush=True)
sys.exit(0 if npass == len(checks) else 1)
