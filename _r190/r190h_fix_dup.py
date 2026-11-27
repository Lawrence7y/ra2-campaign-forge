#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R190 H：修 r190g 的重复追加（首版在我把 BOARDTXT 变量名与路径变量写混之前，
已对 R14_COMMON / LEDGER / LEAD_LOCK 各追加过一次，随后在 BOARD 处抛异常；
第二次运行又追加一次 ⇒ 三份文件各出现 2 份本轮正文）。

做法：从**第一次运行前**的备份（*_194548.bak）恢复，再追加一次。全程断言。
"""
import hashlib, os, re, sys, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE')
stamp = time.strftime('%Y%m%d_%H%M%S')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
JOBS = [
    (os.path.join(TIER, 'R14_COMMON.md'), os.path.join(BL, 'R14_COMMON.md.before_r190_20261127_194548.bak'),
     '### 2.195 R190', 1081, 1664425),
    (os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'),
     os.path.join(BL, 'GOAL_THREE_TARGETS_20261018.md.before_r190_20261127_194548.bak'),
     '## §1245 R190', 337, 5339767),
    (os.path.join(ROOT, 'lead/LEAD_LOCK'), os.path.join(BL, 'LEAD_LOCK.before_r190_20261127_194548.bak'),
     '**PT1. 📌 R190 交付一', 137, 1324735),
]
for path, bak, marker, cr, size in JOBS:
    cur = open(path, 'rb').read(); b0 = open(bak, 'rb').read()
    ck('%s 备份 = 首版前原始（%d B / CR %d）' % (os.path.basename(path), size, cr),
       len(b0) == size and b0.count(b'\r') == cr, (len(b0), b0.count(b'\r')))
    ck('%s 备份里本轮标记出现 0 次' % os.path.basename(path), b0.count(marker.encode()) == 0,
       b0.count(marker.encode()))
    ck('%s 现盘里本轮标记出现 2 次（重复）' % os.path.basename(path), cur.count(marker.encode()) == 2,
       cur.count(marker.encode()))
    # 抽取单份正文：从现盘里取「标记起点到下一个本轮标记起点或文件尾」的最长公共部分
    txt = cur.decode('utf-8'); bt = b0.decode('utf-8')
    tail = txt[len(bt):]           # 两次追加的全部内容
    half = len(tail) // 2
    add = tail[:half]
    ck('%s 两次追加内容逐字节相同（前一半 == 后一半）' % os.path.basename(path), tail == add + add,
       (len(tail), len(add)))
    ck('%s 单份正文以换行开头、以换行结尾' % os.path.basename(path),
       add.startswith('\n') and add.endswith('\n'), (repr(add[:3]), repr(add[-3:])))
    new = b0 + add.encode()
    ck('%s 新体量 = 备份 + 单份（%d）' % (os.path.basename(path), len(new)),
       len(new) == len(b0) + len(add.encode()), (len(new), len(b0) + len(add.encode())))
    ck('%s 新 CR == %d' % (os.path.basename(path), cr), new.count(b'\r') == cr, new.count(b'\r'))
    ck('%s 新体里标记恰 1 次' % os.path.basename(path), new.count(marker.encode()) == 1,
       new.count(marker.encode()))
    if fails: continue
    rbak = os.path.join(BL, '%s.before_r190_dedup_%s.bak' % (os.path.basename(path), stamp))
    fd = os.open(rbak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(cur)
    ck('%s 去重前状态已备份' % os.path.basename(path),
       hashlib.sha256(open(rbak, 'rb').read()).hexdigest() == hashlib.sha256(cur).hexdigest())
    assert open(path, 'rb').read() == cur
    open(path, 'wb').write(new)
    ck('%s 回读一致' % os.path.basename(path),
       hashlib.sha256(open(path, 'rb').read()).hexdigest() == hashlib.sha256(new).hexdigest())
    print('   %s %d -> %d B' % (os.path.basename(path), len(cur), len(new)))
if fails:
    print('★ fail-closed：%d 条未过，未写盘' % len(fails)); sys.exit(1)
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
sys.exit(0)
