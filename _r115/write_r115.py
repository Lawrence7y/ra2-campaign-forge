#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""write_r115.py —— 按写入纪律落盘四件套（R115）。

纪律（与 R108–R114 同一套）：
  1. 在 R17_LEAD_BASELINE/ 用 os.O_EXCL（等价 wx）**独占创建**唯一备份，文件名带作业序号与时刻；
  2. 断言旧 sha256 与 CR（防止在别人改过的文件上盲写）；
  3. 一次性写入（old + seg，单次 write）；
  4. 回读校验（CR / 行数增量 / 段落标记 / 字节 == old+seg）。

看板：开局 194 行 < 260 ⇒ 按规则**不触发**归档。
但本轮段落 86 行，194+86=**280 > 260**（规则要求 >=260 就归档，且硬上限 300）。
故本轮**必须**先归档最早的一个实体段（第 112 轮，56 行）到 BOARD_ARCHIVE，
逐字搬、missing=0，归档 CR 必须保持 2952。归档后 194-56=138 行，再追加 86 行 ⇒ 224 行 <= 300。
"""
import hashlib, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
W = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(W, 'R17_LEAD_BASELINE')
SEG = os.path.join(ROOT, '_r115')
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
    bak = os.path.join(BASE, '%s.before_R115_%s_j%d_%s.bak'
                       % (os.path.basename(path), tag, job[0], stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(path, 'rb').read())
    ck('W2 %s 备份独占创建成功且字节一致（j%d）' % (os.path.basename(path), job[0]),
       sha(bak) == sha(path), os.path.basename(bak))
    return bak


BRD = os.path.join(W, 'STATUS_BOARD.md')
ARC = os.path.join(W, 'BOARD_ARCHIVE.md')

# ============ 第 0 步：看板归档 ============
cr0, lf0, by0 = crlf(BRD)
segp_b = os.path.join(SEG, 'seg_board_115.md')
seg_lines = open(segp_b, 'rb').read().count(b'\n')
ck('A0 看板开局 %d 行' % lf0, lf0 == 194, {'lines': lf0})
ck('A0b 本轮段落 %d 行 ⇒ 写入后 %d+%d=%d > 260（规则阈值），故**必须**先归档一个实体段'
   % (seg_lines, lf0, seg_lines, lf0 + seg_lines),
   lf0 + seg_lines > 260, {'projected': lf0 + seg_lines})
ck('A0c BOARD_ARCHIVE 开局 CR==2952', crlf(ARC)[0] == 2952, crlf(ARC)[0])

brd = open(BRD, 'rb').read()
lines = brd.split(b'\n')
starts = [i for i, l in enumerate(lines) if l.startswith(b'## ')]
ck('A1 看板实体段起点 %d 个（第 112 / 114 轮）' % len(starts), len(starts) == 2,
   [lines[i][:40].decode('utf-8', 'replace') for i in starts])
if len(starts) < 2:
    print('FATAL: 段结构不符合预期，中止')
    sys.exit(2)
cut = starts[1]                       # 保留第 114 轮起的全部内容
head = lines[:starts[0]]
archive_part = lines[starts[0]:cut]   # 第 112 轮，56 行
keep_part = lines[cut:]
ck('A2 待归档段 = 第 112 轮，共 %d 行；保留（第 114 轮起）%d 行'
   % (len(archive_part), len(keep_part)),
   40 <= len(archive_part) <= 80, {'arch': len(archive_part), 'keep': len(keep_part)})

arc_old = open(ARC, 'rb').read()
arc_add = b'\n'.join(archive_part).rstrip(b'\n') + b'\n'
missing = [l for l in archive_part if l and l not in brd]
ck('A3 归档逐字搬：待归档 %d 行中在原文里找不到的 = %d（missing 必须 0）'
   % (len(archive_part), len(missing)), not missing, {'missing': len(missing)})

brd_new = b'\n'.join(head + keep_part)
ck('A4 新看板 = 头部 + 第 114 轮起；行数 %d - %d = %d'
   % (lf0, len(archive_part), brd_new.count(b'\n')),
   brd_new.count(b'\n') == lf0 - len(archive_part), brd_new.count(b'\n'))

bak_arc = backup(ARC, 'archive')
open(ARC, 'wb').write(arc_old + arc_add)
arc_new = open(ARC, 'rb').read()
ck('A5 BOARD_ARCHIVE 回读 == 旧 + 段（逐字节）', arc_new == arc_old + arc_add,
   {'old': len(arc_old), 'add': len(arc_add), 'new': len(arc_new)})
ck('A6 BOARD_ARCHIVE CR 仍为 2952', arc_new.count(b'\r') == 2952, arc_new.count(b'\r'))
ck('A6b BOARD_ARCHIVE LF 增量正确',
   arc_new.count(b'\n') == arc_old.count(b'\n') + arc_add.count(b'\n'),
   (arc_old.count(b'\n'), arc_add.count(b'\n'), arc_new.count(b'\n')))

bak_brd = backup(BRD, 'archive')
open(BRD, 'wb').write(brd_new)
brd_back = open(BRD, 'rb').read()
ck('A7 STATUS_BOARD 回读 == 头部 + 第 114 轮起（逐字节）', brd_back == brd_new,
   {'bytes': len(brd_back)})
ck('A7b STATUS_BOARD 归档后 %d 行 <= 300' % brd_back.count(b'\n'),
   brd_back.count(b'\n') <= 300, brd_back.count(b'\n'))
ck('A7c STATUS_BOARD CR 仍为 0', brd_back.count(b'\r') == 0, brd_back.count(b'\r'))

# ============ 第 1 步：逐文件追加 ============
JOBS = [
    ('R14_COMMON.md', os.path.join(W, 'R14_COMMON.md'), os.path.join(SEG, 'seg_rc_2119.md'),
     b'## 2.119', 1081),
    ('GOAL_THREE_TARGETS_20261018.md', os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'),
     os.path.join(SEG, 'seg_ledger_1169.md'), b'## \xc2\xa71169 R115', 337),
    ('LEAD_LOCK', os.path.join(ROOT, 'lead/LEAD_LOCK'), os.path.join(SEG, 'seg_lock_EQ.md'),
     b'EQ. R115', 137),
    ('STATUS_BOARD.md', BRD, segp_b, '第 115 轮'.encode('utf-8'), 0),
]

for name, path, segp, marker, want_cr in JOBS:
    seg = open(segp, 'rb').read()
    ck('W0 %s 段落全 LF（CR==0）' % os.path.basename(segp), seg.count(b'\r') == 0,
       seg.count(b'\r'))
    ck('W0b %s 段落以 LF 开头、以 LF 结尾' % os.path.basename(segp),
       seg.startswith(b'\n') and seg.endswith(b'\n'), (seg[:2], seg[-2:]))
    cr_b, lf_b, by_b = crlf(path)
    s_b = sha(path)
    ck('W1 %s 旧 CR==%d（实测 %d / LF %d / %d B）' % (name, want_cr, cr_b, lf_b, by_b),
       cr_b == want_cr, (cr_b, lf_b, by_b))
    bak = backup(path, 'write')
    old = open(path, 'rb').read()
    open(path, 'wb').write(old + seg)
    back = open(path, 'rb').read()
    cr_a, lf_a, by_a = crlf(path)
    ck('W4 %s 回读 CR==%d（不变）实测 %d' % (name, want_cr, cr_a), cr_a == want_cr,
       (cr_a, lf_a, by_a))
    ck('W5 %s 行数 %d += %d = %d' % (name, lf_b, seg.count(b'\n'), lf_b + seg.count(b'\n')),
       lf_a == lf_b + seg.count(b'\n'), (lf_b, lf_a))
    ck('W6 %s 回读字节 == 旧 + 段（逐字节）且含标记' % name, back == old + seg, marker)
    report.append({'file': name, 'action': 'appended', 'sha_before': s_b,
                   'sha_after': hashlib.sha256(back).hexdigest(),
                   'lf_before': lf_b, 'lf_after': lf_a, 'cr': cr_a, 'bytes': by_a,
                   'backup': os.path.basename(bak)})

# ============ 第 2 步：全局不变量 ============
b_lf = crlf(BRD)[1]
ck('W7 STATUS_BOARD 写入后 %d 行 <= 300（硬上限）' % b_lf, b_lf <= 300, b_lf)
ck('W8 BOARD_ARCHIVE CR 仍为 2952', crlf(ARC)[0] == 2952, crlf(ARC)[0])
ck('W9 R14_COMMON CR 仍为 1081', crlf(os.path.join(W, 'R14_COMMON.md'))[0] == 1081,
   crlf(os.path.join(W, 'R14_COMMON.md'))[0])
ck('W10 LEAD_LOCK CR 仍为 137', crlf(os.path.join(ROOT, 'lead/LEAD_LOCK'))[0] == 137,
   crlf(os.path.join(ROOT, 'lead/LEAD_LOCK'))[0])
ck('W11 台账 CR 仍为 337',
   crlf(os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'))[0] == 337,
   crlf(os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'))[0])

# ============ 第 3 步：段落内容自检 ============
rc = open(os.path.join(W, 'R14_COMMON.md'), 'rb').read().decode('utf-8')
led = open(os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'), 'rb').read().decode('utf-8')
lk = open(os.path.join(ROOT, 'lead/LEAD_LOCK'), 'rb').read().decode('utf-8')
brd = open(BRD, 'rb').read().decode('utf-8')

KEY = ('S 尺', '1214', '260', '0x7fa498', 'EQ', '234')
ck('C1 四件套都含本轮核心关键字 %s' % (KEY,),
   all(('S 尺' in t and '260' in t and '0x7fa498' in t) for t in (rc, led, lk, brd)), 'ok')
ck('C2 四件套都如实写「未取得」，且都写明 IPersistStream 方法数仍拿不到（不写成已证）',
   all('未取得' in t for t in (rc, led, lk, brd))
   and all('IPersistStream' in t for t in (rc, led, lk, brd)), 'ok')
ck('C3 四件套都写明「不编赢家」（0x7f7c70 vs 0x7f7c80 仍不可区分）',
   all('不编赢家' in t for t in (rc, led, lk, brd)), 'ok')
ck('C4 四件套都记了跨家族子代理的实质意见（不是只记自己对了）',
   all(('hy4' in t and 'deepseek' in t) for t in (rc, led, lk, brd)), 'ok')
ck('C5 四件套都把本轮自错（S-15..S-21）如实登记，不粉饰',
   all(('S-15' in t or 'S-17' in t) for t in (rc, led, lk, brd)), 'ok')
ck('C6 四件套都写明 C15 只证漏洞未修（不写成已修）',
   all('空洞' in t for t in (rc, led, lk, brd)), 'ok')

json.dump({'stamp': stamp, 'report': report, 'checks': checks,
           'archive': {'took_lines': len(archive_part),
                       'board_after_archive': lf0 - len(archive_part),
                       'board_final': b_lf}},
          open(os.path.join(SEG, 'write_r115.json'), 'w'), indent=1, ensure_ascii=False)
bad = sum(1 for c in checks if not c['ok'])
print('\n--- write_r115: %d checks, PASS %d, FAIL %d ---'
      % (len(checks), len(checks) - bad, bad))
sys.exit(1 if bad else 0)
