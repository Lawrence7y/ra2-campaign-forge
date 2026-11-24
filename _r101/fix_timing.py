#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R101 修正：四件套里子代理用时登记的措辞（写入纪律同样执行：wx 独占备份 -> 断言 -> 替换 -> 回读）"""
import os, re, json, hashlib, datetime
ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
BASE = 'lead/next_re_20261117_r14/R17_LEAD_BASELINE'
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
TARGETS = {
 'lead/next_re_20261117_r14/R14_COMMON.md': ('R14_COMMON', 1081,
   '它自报**超时**：卡面预算 10 分钟，实际约 **45 分钟 ⇒ `[OVERTIME]` 如实记**。',
   '它以「3 段各 1.5-3.7 分钟的 140 万行线性扫描」自报用时约 **45 分钟（它自己的估计，含重跑）**；\n按磁盘产物时刻（派发约 03:37、报告落盘 04:02）实测约 **25 分钟 vs 预算 10 ⇒ `[OVERTIME]` 如实记**。'),
 'lead/LEAD_LOCK': ('LEAD_LOCK', 137,
   '它自报\n**预算 10 分钟、实际约 45 分钟 ⇒ `[OVERTIME]` 如实记**；',
   '它自报约 45 分钟（含重跑）、按落盘时刻实测约 **25 分钟 vs 预算 10 ⇒ `[OVERTIME]` 如实记**；'),
 'lead/next_re_20261117_r14/STATUS_BOARD.md': ('STATUS_BOARD', 0,
   '自报 **45 分钟 vs 预算 10 ⇒ [OVERTIME]**',
   '自报约 45 分钟（含重跑）、落盘时刻实测约 25 分钟 vs 预算 10 ⇒ **`[OVERTIME]`**'),
 'lead/next_re_20261117_r14/R14_COMMON.md': None,
}
HY4_OLD = '它与卡面 13 项背景事实**全部一致**'
HY4_NEW = '派发约 03:37、报告落盘 **03:41**（约 5 分钟，预算 10，**无 OVERTIME**）。它与卡面 13 项背景事实**全部一致**'

def sha(b): return hashlib.sha256(b).hexdigest()

done = []
for path, spec in TARGETS.items():
    if spec is None: continue
    tag, creq, old, new = spec
    b = open(path, 'rb').read()
    cr = b.count(b'\r')
    assert cr == creq, 'CR 不符 %s %d!=%d' % (path, cr, creq)
    oldb = old.encode('utf-8'); newb = new.encode('utf-8')
    assert b.count(oldb) == 1, '旧串命中 %d 次（须恰 1 次）: %s' % (b.count(oldb), path)
    dst = '%s/SUPERSEDED.before_r101fix_%s_%s.md' % (BASE, tag, TS)
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(b)
    assert sha(open(dst, 'rb').read()) == sha(b)
    nb = b.replace(oldb, newb, 1)
    assert nb.count(b'\r') == cr, 'CR 会变'
    open(path, 'wb').write(nb)
    back = open(path, 'rb').read()
    assert back == nb
    assert back.count(b'\r') == creq
    print('FIXED %s  %d -> %d B (CR %d 保持)' % (path, len(b), len(nb), cr))
    done.append(path)

# hy4 timing 追加到 R14 与看板
for path, tag, creq in [('lead/next_re_20261117_r14/R14_COMMON.md', 'R14_COMMON', 1081),
                        ('lead/next_re_20261117_r14/STATUS_BOARD.md', 'STATUS_BOARD', 0)]:
    b = open(path, 'rb').read()
    cr = b.count(b'\r'); assert cr == creq
    if HY4_OLD.encode() in b:
        dst = '%s/SUPERSEDED.before_r101fix2_%s_%s.md' % (BASE, tag, TS)
        fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, 'wb') as f: f.write(b)
        assert sha(open(dst, 'rb').read()) == sha(b)
        nb = b.replace(HY4_OLD.encode(), HY4_NEW.encode(), 1)
        assert nb.count(b'\r') == cr
        open(path, 'wb').write(nb)
        assert open(path, 'rb').read() == nb
        print('FIXED-HY4 %s  %d -> %d B' % (path, len(b), len(nb)))
    else:
        print('SKIP-HY4 %s（未命中旧串）' % path)
print('done', done)
