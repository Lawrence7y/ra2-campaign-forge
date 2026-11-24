#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R100 四件套写入器：备份(wx) -> 断言旧 sha/CR -> 一次性写入 -> 回读校验。
--dry 只读不写。所有待写文本来自 _r100/text/*.md（先自测文本本身无 CR）。
"""
import io, os, sys, hashlib, time, re

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
TXT = os.path.join(ROOT, '_r100', 'text')

FILES = {
    'RC': (os.path.join(R14, 'R14_COMMON.md'), 1081, 'r14_common_2_104.md'),
    'LED': (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), 337, 'ledger_1154.md'),
    'LCK': (os.path.join(ROOT, 'lead', 'LEAD_LOCK'), 137, 'lead_lock_eb.md'),
    'BRD': (os.path.join(R14, 'STATUS_BOARD.md'), 0, 'board_r100.md'),
}

def read(p):
    return io.open(p, encoding='utf-8', newline='').read()

def sha(p):
    return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()

def main(dry):
    f = 0
    for tag, (p, exp_cr, tf) in FILES.items():
        tp = os.path.join(TXT, tf)
        if not os.path.isfile(tp):
            print('  SKIP %s : %s missing' % (tag, tf)); f += 1; continue
        blob = read(tp)
        if '\r' in blob:
            print('  FAIL %s text has CR' % tag); f += 1
        # 反引号禁令只针对 _cards/ 调度卡面；四件套正文历来使用反引号（见 EA 段/看板）
        cur = read(p)
        ncr = cur.count('\r\n')
        if ncr != exp_cr:
            print('  FAIL %s live CR %d != expected %d' % (tag, ncr, exp_cr)); f += 1
        print('  OK   %s live CR %d ; new text %d B' % (tag, ncr, len(blob.encode())))
    print('precheck FAIL = %d' % f)
    if dry or f:
        return 1 if f else 0

    stamp = time.strftime('%Y%m%d_%H%M%S')
    old_sha = {}
    for tag, (p, exp_cr, tf) in FILES.items():
        b = os.path.join(BASE, 'R100%s_%s.bak' % (tag, stamp))
        with open(b, 'xb') as fh:
            fh.write(io.open(p, 'rb').read())
        assert sha(b) == sha(p), 'backup sha mismatch %s' % b
        old_sha[tag] = sha(p)
    assert len(set(old_sha.values())) == len(old_sha), 'two files had same sha?'
    print('backups written with stamp %s' % stamp)

    for tag, (p, exp_cr, tf) in FILES.items():
        assert sha(p) == old_sha[tag], 'file changed since backup %s' % tag
        assert read(p).count('\r\n') == exp_cr
        blob = read(os.path.join(TXT, tf))
        cur = read(p)
        if tag == 'BRD':
            new = cur.rstrip('\n') + '\n\n' + blob.rstrip('\n') + '\n'
        else:
            new = cur.rstrip('\n') + '\n\n' + blob.rstrip('\n') + '\n'
        with io.open(p, 'w', encoding='utf-8', newline='') as fh:
            fh.write(new)
        back = read(p)
        ok = (back.count('\r\n') == exp_cr)
        tail = blob.rstrip('\n').split('\n')[-1]
        tail_ok = back.rstrip('\n').endswith(tail)
        print('  WRITE %s : CR %d (expect %d) %s ; tail-match %s ; %d -> %d B'
              % (tag, back.count('\r\n'), exp_cr, 'OK' if ok else 'FAIL',
                 tail_ok, len(cur.encode()), len(back.encode())))
        if not (ok and tail_ok):
            return 1
    for tag, (p, exp_cr, tf) in FILES.items():
        print('  FINAL %s lines=%d CR=%d sha=%s'
              % (tag, read(p).count('\n'), read(p).count('\r\n'), sha(p)[:16]))
    return 0

if __name__ == '__main__':
    sys.exit(main('--dry' in sys.argv))
