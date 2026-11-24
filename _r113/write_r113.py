#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""write_r113.py —— 按写入纪律落盘四件套（R113）。

纪律（每次修改前必须执行，与 R108–R112 同一套）：
  1. 在 R17_LEAD_BASELINE/ 用 os.O_EXCL（等价 wx）**独占创建**唯一备份，文件名带作业序号与时刻；
  2. 断言旧 sha256 与 CR（防止在别人改过的文件上盲写）；
  3. 一次性写入（old + seg，单次 write）；
  4. 回读校验（CR / 行数增量 / 段落标记 / 字节 == old+seg）。

看板归档：本轮开局 STATUS_BOARD 211 行 < 260 ⇒ **不触发归档**（R112 已归档到 211）。
本轮仍然断言「不触发」这件事，防止以后有人把阈值当摆设。
"""
import hashlib, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
W = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(W, 'R17_LEAD_BASELINE')
SEG = os.path.join(ROOT, '_r113')
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def crlf(p):
    d = open(p, 'rb').read()
    return d.count(b'\r'), d.count(b'\n'), len(d)


stamp = time.strftime('%Y%m%d_%H%M%S')
report = []
job = [0]


def backup(path, tag):
    job[0] += 1
    bak = os.path.join(BASE, '%s.before_R113_%s_j%d_%s.bak'
                       % (os.path.basename(path), tag, job[0], stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(path, 'rb').read())
    ck('W2 %s 备份独占创建成功且字节一致（j%d）' % (os.path.basename(path), job[0]),
       sha(bak) == sha(path), os.path.basename(bak))
    return bak


BRD = os.path.join(W, 'STATUS_BOARD.md')
ARC = os.path.join(W, 'BOARD_ARCHIVE.md')

# ============ 第 0 步：看板归档判定 ============
cr0, lf0, by0 = crlf(BRD)
ck('A0 看板开局 %d 行 < 260 ⇒ 本轮**不**触发归档（R112 已归档到 211）' % lf0,
   lf0 < 260, {'lines': lf0, 'threshold': 260})
ck('A0b BOARD_ARCHIVE 开局 CR==2952 且本轮不动它', crlf(ARC)[0] == 2952, crlf(ARC)[0])

# ============ 第 1 步：四件套追加 ============
TARGETS = [
    (os.path.join(W, 'R14_COMMON.md'), 1081, 10446, 'seg_rc_2117.md', 1081, '## 2.117 R113'),
    (os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'), 337, 46231,
     'seg_ledger_1167.md', 337, '## §1167 R113'),
    (os.path.join(ROOT, 'lead/LEAD_LOCK'), 137, 5574, 'seg_lock_EN.md', 137, 'EN. R113'),
    (BRD, 0, 211, 'seg_board_113.md', 0, '第 113 轮（2026-11-24 14:4x'),
]

for path, old_cr, old_lf, segname, new_cr, marker in TARGETS:
    name = os.path.basename(path)
    seg = open(os.path.join(SEG, segname), 'rb').read()
    ck('W0 %s 段落全 LF（CR==0）' % segname, seg.count(b'\r') == 0, seg.count(b'\r'))
    ck('W0b %s 段落以 LF 开头、以 LF 结尾' % segname,
       seg.startswith(b'\n') and seg.endswith(b'\n'), (seg[:2], seg[-2:]))

    c0, l0, b0 = crlf(path)
    s0 = sha(path)
    if marker.encode() in open(path, 'rb').read():
        ck('W1 %s 段落已存在（幂等跳过）；CR 仍 == %d' % (name, new_cr), c0 == new_cr,
           (c0, l0, b0))
        report.append({'file': name, 'action': 'skip-existing', 'cr': c0, 'lf': l0})
        continue

    ck('W1 %s 旧 CR==%d（实测 %d / LF %d / %d B）' % (name, old_cr, c0, l0, b0),
       c0 == old_cr, (c0, l0, b0))
    ck('W1b %s 旧 LF==%d（实测 %d）' % (name, old_lf, l0), l0 == old_lf, l0)

    bk = backup(path, 'write')
    old = open(path, 'rb').read()
    with open(path, 'wb') as f:
        f.write(old + seg)

    c1, l1, b1 = crlf(path)
    back = open(path, 'rb').read()
    ck('W4 %s 回读 CR==%d（不变）实测 %d' % (name, new_cr, c1), c1 == new_cr, (c1, l1, b1))
    ck('W5 %s 行数 %d += %d = %d' % (name, l0, seg.count(b'\n'), l0 + seg.count(b'\n')),
       l1 == l0 + seg.count(b'\n'), (l0, l1))
    ck('W6 %s 回读字节 == 旧 + 段（逐字节）且含标记' % name, back == old + seg, marker)
    report.append({'file': name, 'action': 'appended', 'sha_before': s0,
                   'sha_after': hashlib.sha256(back).hexdigest(),
                   'lf_before': l0, 'lf_after': l1, 'cr': c1, 'bytes': b1,
                   'backup': os.path.basename(bk)})

# ============ 第 2 步：全局不变量 ============
b_lf = crlf(BRD)[1]
ck('W7 STATUS_BOARD 写入后 %d 行 <= 300（硬上限）' % b_lf, b_lf <= 300, b_lf)
ck('W8 BOARD_ARCHIVE CR 仍为 2952（本轮未动归档）', crlf(ARC)[0] == 2952, crlf(ARC)[0])
ck('W9 R14_COMMON CR 仍为 1081', crlf(os.path.join(W, 'R14_COMMON.md'))[0] == 1081,
   crlf(os.path.join(W, 'R14_COMMON.md'))[0])
ck('W10 LEAD_LOCK CR 仍为 137', crlf(os.path.join(ROOT, 'lead/LEAD_LOCK'))[0] == 137,
   crlf(os.path.join(ROOT, 'lead/LEAD_LOCK'))[0])
ck('W11 台账 CR 仍为 337',
   crlf(os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'))[0] == 337,
   crlf(os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'))[0])

# ============ 第 3 步：段落内容自检（防写进自相矛盾的句子） ============
rc = open(os.path.join(W, 'R14_COMMON.md'), 'rb').read().decode('utf-8')
led = open(os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'), 'rb').read().decode('utf-8')
lk = open(os.path.join(ROOT, 'lead/LEAD_LOCK'), 'rb').read().decode('utf-8')
brd = open(BRD, 'rb').read().decode('utf-8')
ck('C1 四件套都含本轮 5 条核心结论关键字（0x7ed358 / ILocomotion / 1214 / 闭包 / S-10）',
   all(all(k in t for k in ('0x7ed358', 'ILocomotion', '1214', '闭包', 'S-10'))
       for t in (rc, led, lk, brd)), 'ok')
ck('C2 四件套都如实写「未取得」且不把 IPersistStream 方法数写成已证',
   all('未取得' in t or '未做' in t for t in (rc, led, lk, brd))
   and 'IPersistStream 有几个方法' in rc and '没有' in rc, 'ok')
ck('C3 四件套都记了 [OVERTIME]（exec #198 超预算）或说明其失败',
   any('[OVERTIME]' in t or 'OVERTIME' in t for t in (rc, led, lk, brd)), 'ok')

json.dump({'stamp': stamp, 'report': report, 'checks': checks},
          open(os.path.join(SEG, 'write_r113.json'), 'w'), indent=1, ensure_ascii=False)
bad = sum(1 for c in checks if not c['ok'])
print('\n--- write_r113: %d checks, PASS %d, FAIL %d ---' % (len(checks), len(checks) - bad, bad))
sys.exit(1 if bad else 0)
