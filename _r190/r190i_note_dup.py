#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R190 I：把本轮「重复追加」这一自错如实补记进 LEAD_LOCK 与看板（各追加一次，fail-closed）。"""
import hashlib, os, sys, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE')
stamp = time.strftime('%Y%m%d_%H%M%S')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

PT10 = '''

**PT10. 📌 R190 自错 g4（最重的一处，写进记录）：四件套被追加了两遍，靠备份去重恢复.** `r190g_fourpiece.py` 首版把看板正文赋给名为 `BOARD` 的变量，而 `BOARD` 本来已是**路径**常量；执行到第 4 份时 `open(BOARD,'rb')` 拿到的是一段正文当文件名 ⇒ `OSError: File name too long`。**更重的是前 3 份已经在同一次运行里写盘成功**，我改掉变量名后**原样重跑整个脚本**，于是 R14_COMMON / GOAL_THREE_TARGETS / LEAD_LOCK 三份各被追加 **2 遍**（现盘标记各出现 2 次）。发现方式是追加后直接 `grep -c` 三份标记（不是靠"应该没问题"）。修复 `_r190/r190h_fix_dup.py`（**30 断言 0 FAIL**）：从**首版运行前**的 `*_194548.bak` 恢复，断言「现盘尾部 = 单份 + 单份逐字节相同」后只加单份，三份回到 1,669,308 / 5,342,907 / 1,330,484 B、CR 分别为 1081 / 337 / 137、标记各 1 次。**这一处的教训不是"变量名写错"，而是：写盘脚本重跑前必须先检查目标状态是否已被上一次运行修改过**（本轮脚本只对 `os.O_EXCL` 备份做了幂等保护，对目标文件本身没有）。
'''
BOARDADD = '''
**自错补记 S-190g4（最重的一处）.** `r190g_fourpiece.py` 把看板正文赋给已用作**路径**的变量名 `BOARD`，第 4 份 `open()` 抛 `OSError: File name too long`；前 3 份**已在同一次运行里写盘成功**，改变量名后**原样重跑**导致 R14_COMMON / 台账 / LEAD_LOCK 各被追加 **2 遍**。靠追加后 `grep -c` 三份标记发现，`_r190/r190h_fix_dup.py`（**30 断言 0 FAIL**）从首版运行前的备份恢复并只加单份，三份回到 **1,669,308 / 5,342,907 / 1,330,484 B**，CR **1081 / 337 / 137**、标记各 **1** 次。教训：**写盘脚本重跑前必须先断言目标文件尚未被上一次运行修改**（本轮只对备份做了 O_EXCL 幂等保护）。
'''
def app(path, add, tag, cr, mk, exp_cnt):
    raw = open(path, 'rb').read()
    ck('%s 改前 CR == %d' % (tag, cr), raw.count(b'\r') == cr, raw.count(b'\r'))
    ck('%s 改前标记出现 %d 次（幂等闸）' % (tag, exp_cnt), raw.count(mk.encode()) == exp_cnt, raw.count(mk.encode()))
    ck('%s 新段无 tab/CR' % tag, '\t' not in add and '\r' not in add)
    new = raw + add.encode()
    ck('%s 新 CR == %d' % (tag, cr), new.count(b'\r') == cr, new.count(b'\r'))
    ck('%s 体量闭合' % tag, len(new) == len(raw) + len(add.encode()))
    bak = os.path.join(BL, '%s.before_r190_note_%s.bak' % (os.path.basename(path), stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(raw)
    ck('%s 备份 sha 一致' % tag,
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == hashlib.sha256(raw).hexdigest())
    assert open(path, 'rb').read() == raw
    open(path, 'wb').write(new)
    ck('%s 回读一致' % tag,
       hashlib.sha256(open(path, 'rb').read()).hexdigest() == hashlib.sha256(new).hexdigest())
    return len(raw), len(new)
a = app(os.path.join(ROOT, 'lead/LEAD_LOCK'), PT10, 'LEAD_LOCK', 137, '**PT10.', 0)
b = app(os.path.join(TIER, 'STATUS_BOARD.md'), BOARDADD, 'STATUS_BOARD', 0, 'S-190g4', 0)
bb = open(os.path.join(TIER, 'STATUS_BOARD.md'), 'rb').read()
ck('Z1 看板总行数 %d <= 300' % bb.count(b'\n'), bb.count(b'\n') <= 300, bb.count(b'\n'))
ck('Z2 看板 CR == 0', bb.count(b'\r') == 0)
print('\nLEAD_LOCK %d -> %d / BOARD %d -> %d' % (a[0], a[1], b[0], b[1]))
print('断言 %d 条，FAIL %d 条' % (n, len(fails)))
sys.exit(1 if fails else 0)
